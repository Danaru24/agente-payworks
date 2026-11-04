"""Búsqueda vectorial en pgvector. Sin LLM: rápido y determinista."""
import psycopg
from psycopg import sql
from psycopg.rows import dict_row
 
from orquestador.config import settings
from orquestador.llm.cliente import embeddings
 
 
def _vec(v: list[float]) -> str:
    return "[" + ",".join(f"{x:.7f}" for x in v) + "]"
 
 
async def buscar_contexto(consultas: list[str]) -> tuple[list[dict], bool]:
    """Top-k por consulta, deduplica, filtra por umbral. Devuelve (chunks, baja_confianza)."""
    vectores = await embeddings().aembed_documents(consultas)
    s = settings
    query = sql.SQL(
        "SELECT {id} AS id, {txt} AS contenido, {meta} AS metadata, "
        "1 - ({emb} <=> %(v)s::vector) AS similitud "
        "FROM {tabla} ORDER BY {emb} <=> %(v)s::vector LIMIT %(k)s"
    ).format(id=sql.Identifier(s.rag_col_id), txt=sql.Identifier(s.rag_col_contenido),
             meta=sql.Identifier(s.rag_col_metadata), emb=sql.Identifier(s.rag_col_embedding),
             tabla=sql.Identifier(s.rag_tabla))
 
    mejores: dict = {}
    async with await psycopg.AsyncConnection.connect(s.pg_dsn_rag, row_factory=dict_row) as conn:
        for v in vectores:
            cur = await conn.execute(query, {"v": _vec(v), "k": s.rag_top_k})
            for fila in await cur.fetchall():
                previo = mejores.get(fila["id"])
                if previo is None or fila["similitud"] > previo["similitud"]:
                    mejores[fila["id"]] = fila
 
    ordenados = sorted(mejores.values(), key=lambda f: f["similitud"], reverse=True)
    aprobados = [f for f in ordenados if f["similitud"] >= s.rag_umbral][: s.rag_max_chunks]
    if aprobados:
        return aprobados, False
    return ordenados[:1], True  # mejor esfuerzo, marcado como baja confianza
 