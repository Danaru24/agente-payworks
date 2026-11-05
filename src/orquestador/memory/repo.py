"""Memoria conversacional en PostgreSQL (schema propio). Fuente de verdad del historial.

Conexiones bajo demanda (mismo patrón que rag.py y catalogo.py): psycopg-pool no existe
en el índice RHOAI 3.5.
"""
import psycopg
from psycopg import sql
from psycopg.rows import dict_row

from orquestador.config import settings


async def abrir() -> None:
    """Se conserva por compatibilidad con el ciclo de vida de la API: ya no hay pool que abrir."""
    return None


async def cerrar() -> None:
    """Se conserva por compatibilidad con el ciclo de vida de la API: ya no hay pool que cerrar."""
    return None


def _tabla():
    return sql.Identifier(settings.memoria_schema, "conversaciones")


async def _conectar() -> psycopg.AsyncConnection:
    return await psycopg.AsyncConnection.connect(
        settings.pg_dsn_memoria, row_factory=dict_row,
        connect_timeout=max(1, int(settings.pg_pool_timeout_s)))


async def obtener_ventana(session_id: str, n: int) -> list[dict]:
    q = sql.SQL("SELECT role, content FROM {} WHERE session_id = %s "
                "ORDER BY created_at DESC, id DESC LIMIT %s").format(_tabla())
    async with await _conectar() as conn:
        filas = await (await conn.execute(q, (session_id, n))).fetchall()
    return list(reversed(filas))


async def guardar(session_id: str, user_id: str | None, role: str, content: str) -> None:
    q = sql.SQL("INSERT INTO {} (session_id, user_id, role, content) VALUES (%s, %s, %s, %s)").format(_tabla())
    # Al salir del `async with` sin excepción, psycopg hace COMMIT automáticamente.
    async with await _conectar() as conn:
        await conn.execute(q, (session_id, user_id, role, content))
