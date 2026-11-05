"""Consulta del catálogo de paneles. El LLM propone SQL; aquí se VALIDA antes de ejecutar.

Política fail-closed con `sqlparse` + `re` (sqlglot no existe en el índice RHOAI 3.5):
ante cualquier duda se rechaza. Solo se acepta un SELECT plano sobre la tabla del catálogo.
"""
import re

import psycopg
import sqlparse
from psycopg.rows import dict_row
from sqlparse import tokens as T

from orquestador.config import settings

# Palabras que no pueden aparecer en un SELECT plano de una sola tabla.
# FETCH se agrega para que `FETCH FIRST n ROWS` no eluda el control de LIMIT.
_PROHIBIDAS = (
    "INSERT", "UPDATE", "DELETE", "DROP", "CREATE", "ALTER", "TRUNCATE", "GRANT", "REVOKE",
    "COPY", "CALL", "DO", "MERGE", "WITH", "UNION", "INTERSECT", "EXCEPT", "JOIN", "INTO",
    "FOR", "PG_SLEEP", "SET", "SHOW", "EXECUTE", "FETCH",
)
_RE_PROHIBIDAS = re.compile(r"\b(" + "|".join(_PROHIBIDAS) + r")\b", re.IGNORECASE)
# Funciones peligrosas (lectura de archivos, sesiones remotas, config del servidor).
_RE_FUNCIONES = re.compile(
    r"\b(pg_\w+|lo_\w+|dblink\w*|set_config|current_setting|query_to_xml\w*)\s*\(", re.IGNORECASE)
_RE_LITERAL = re.compile(r"'(?:[^']|'')*'")
_RE_SELECT = re.compile(r"\bSELECT\b", re.IGNORECASE)
_RE_FROM = re.compile(r"\bFROM\b", re.IGNORECASE)
_CLAUSULAS_TRAS_FROM = r"WHERE|GROUP|ORDER|LIMIT|HAVING|OFFSET"
_RE_FROM_TABLA = re.compile(
    r"\bFROM\s+([A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)?)"      # tabla o esquema.tabla
    r"(?:\s+(?:AS\s+)?(?!(?:" + _CLAUSULAS_TRAS_FROM + r")\b)[A-Za-z_][A-Za-z0-9_]*)?"  # alias opcional
    r"\s*(?=$|\b(?:" + _CLAUSULAS_TRAS_FROM + r")\b)",
    re.IGNORECASE)
_RE_LIMIT = re.compile(r"\bLIMIT\b", re.IGNORECASE)
_RE_LIMIT_FINAL = re.compile(r"\bLIMIT\s+(\S+)((?:\s+OFFSET\s+\d+)?)\s*$", re.IGNORECASE)


class SQLRechazado(ValueError):
    pass


def _sin_literales(texto: str) -> str:
    """Sustituye los literales '...' por '' para que su contenido no dispare reglas."""
    return _RE_LITERAL.sub("''", texto)


def validar_sql(consulta: str) -> str:
    if not isinstance(consulta, str) or not consulta.strip():
        raise SQLRechazado("consulta vacía")
    texto = consulta.strip()
    if texto.endswith(";"):  # solo se tolera un ';' final
        texto = texto[:-1].rstrip()
    plano = _sin_literales(texto)

    # a) comentarios, ';' intermedios, literales raros y una única sentencia SELECT
    if "--" in plano or "/*" in plano or "*/" in plano:
        raise SQLRechazado("no se permiten comentarios SQL")
    if ";" in plano:
        raise SQLRechazado("se permite exactamente una sentencia")
    if plano.count("'") % 2 or "$" in plano or "\\" in plano or re.search(r"\bE''", plano, re.I):
        raise SQLRechazado("literales no soportados")
    sentencias = [s for s in sqlparse.parse(texto) if str(s).strip()]
    if len(sentencias) != 1:
        raise SQLRechazado("se permite exactamente una sentencia")
    sentencia = sentencias[0]
    if sentencia.get_type() != "SELECT":
        raise SQLRechazado("solo se permite SELECT")
    if any(tok.ttype in T.Comment for tok in sentencia.flatten()):
        raise SQLRechazado("no se permiten comentarios SQL")

    # b) palabras reservadas y funciones prohibidas (fuera de literales)
    m = _RE_PROHIBIDAS.search(plano)
    if m:
        raise SQLRechazado(f"palabra prohibida: {m.group(1).upper()}")
    m = _RE_FUNCIONES.search(plano)
    if m:
        raise SQLRechazado(f"función prohibida: {m.group(1)}")

    # c) sin subconsultas: un único SELECT y al inicio
    if len(_RE_SELECT.findall(plano)) != 1 or not re.match(r"\s*SELECT\b", plano, re.I):
        raise SQLRechazado("no se permiten subconsultas")

    # d) exactamente una tabla en FROM y debe ser la del catálogo
    if len(_RE_FROM.findall(plano)) != 1:
        raise SQLRechazado("se requiere exactamente un FROM")
    m = _RE_FROM_TABLA.search(plano)
    if not m:
        raise SQLRechazado("FROM inválido (¿varias tablas o sintaxis no soportada?)")
    if m.group(1).lower() != settings.catalogo_tabla.lower():
        raise SQLRechazado(f"solo se permite la tabla {settings.catalogo_tabla}")

    # e) LIMIT al final, numérico y acotado
    limite = int(settings.catalogo_limite)
    n_limits = len(_RE_LIMIT.findall(plano))
    if n_limits == 0:
        return f"{texto} LIMIT {limite}"
    if n_limits > 1:
        raise SQLRechazado("LIMIT duplicado")
    m = _RE_LIMIT_FINAL.search(texto)
    if not m:
        raise SQLRechazado("LIMIT debe ir al final de la sentencia")
    valor = m.group(1)
    n = int(valor) if valor.isdigit() and 0 < int(valor) <= limite else limite
    return f"{texto[:m.start()]}LIMIT {n}{m.group(2)}"


async def ejecutar(consulta_validada: str) -> list[dict]:
    async with await psycopg.AsyncConnection.connect(settings.pg_dsn_catalogo, row_factory=dict_row) as conn:
        await conn.execute(f"SET statement_timeout = {int(settings.catalogo_timeout_ms)}")
        await conn.execute("SET SESSION CHARACTERISTICS AS TRANSACTION READ ONLY")
        cur = await conn.execute(consulta_validada)
        return await cur.fetchall()
