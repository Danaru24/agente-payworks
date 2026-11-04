"""Memoria conversacional en PostgreSQL (schema propio). Fuente de verdad del historial."""
from psycopg import sql
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool
 
from orquestador.config import settings
 
_pool: AsyncConnectionPool | None = None
 
 
async def abrir() -> None:
    global _pool
    _pool = AsyncConnectionPool(settings.pg_dsn_memoria, min_size=1, max_size=5, open=False,
                                kwargs={"row_factory": dict_row})
    await _pool.open()
 
 
async def cerrar() -> None:
    if _pool:
        await _pool.close()
 
 
def _tabla():
    return sql.Identifier(settings.memoria_schema, "conversaciones")
 
 
async def obtener_ventana(session_id: str, n: int) -> list[dict]:
    q = sql.SQL("SELECT role, content FROM {} WHERE session_id = %s "
                "ORDER BY created_at DESC, id DESC LIMIT %s").format(_tabla())
    async with _pool.connection() as conn:
        filas = await (await conn.execute(q, (session_id, n))).fetchall()
    return list(reversed(filas))
 
 
async def guardar(session_id: str, user_id: str | None, role: str, content: str) -> None:
    q = sql.SQL("INSERT INTO {} (session_id, user_id, role, content) VALUES (%s, %s, %s, %s)").format(_tabla())
    async with _pool.connection() as conn:
        await conn.execute(q, (session_id, user_id, role, content))