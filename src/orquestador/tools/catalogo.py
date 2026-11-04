"""Consulta del catálogo de paneles. El LLM propone SQL; aquí se VALIDA antes de ejecutar."""
import psycopg
import sqlglot
from psycopg.rows import dict_row
from sqlglot import exp
 
from orquestador.config import settings
 
_PROHIBIDOS = tuple(getattr(exp, n) for n in
                    ("Insert", "Update", "Delete", "Drop", "Create", "Alter", "Command", "Merge")
                    if hasattr(exp, n))
 
 
class SQLRechazado(ValueError):
    pass
 
 
def validar_sql(consulta: str) -> str:
    arboles = [a for a in sqlglot.parse(consulta, read="postgres") if a is not None]
    if len(arboles) != 1:
        raise SQLRechazado("se permite exactamente una sentencia")
    arbol = arboles[0]
    if not isinstance(arbol, exp.Select):
        raise SQLRechazado("solo se permite SELECT")
    if any(arbol.find_all(*_PROHIBIDOS)):
        raise SQLRechazado("sentencia prohibida")
    tablas = {t.name for t in arbol.find_all(exp.Table)}
    if tablas != {settings.catalogo_tabla}:
        raise SQLRechazado(f"solo se permite la tabla {settings.catalogo_tabla}")
    limite = arbol.args.get("limit")
    try:
        actual = int(limite.expression.name) if limite else None
    except (AttributeError, ValueError):
        actual = None
    if actual is None or actual > settings.catalogo_limite:
        arbol = arbol.limit(settings.catalogo_limite)
    return arbol.sql(dialect="postgres")
 
 
async def ejecutar(consulta_validada: str) -> list[dict]:
    async with await psycopg.AsyncConnection.connect(settings.pg_dsn_catalogo, row_factory=dict_row) as conn:
        await conn.execute(f"SET statement_timeout = {int(settings.catalogo_timeout_ms)}")
        await conn.execute("SET SESSION CHARACTERISTICS AS TRANSACTION READ ONLY")
        cur = await conn.execute(consulta_validada)
        return await cur.fetchall()