"""Búsqueda vectorial en pgvector. Sin LLM: rápido y determinista."""
import psycopg
from psycopg import sql
from psycopg.rows import dict_row

from orquestador.config import settings
from orquestador.llm.cliente import embeddings


def _vec(v: list[float]) -> str:
    return "[" + ",".join(f"{x:.7f}" for x in v) + "]"


def _formatear_contenido(fila: dict) -> str:
    partes = [
        str(fila.get(col) or "").strip()
        for col in ("seccion_h1", "seccion_h2", "seccion_h3")
    ]
    encabezado = " > ".join(p for p in partes if p)
    contenido = str(fila.get("contenido") or "")
    if encabezado:
        return f"[Sección: {encabezado}]\n{contenido}"
    return contenido


async def buscar_contexto(consultas: list[str]) -> tuple[list[dict], bool]:
    """Top-k por consulta, deduplica, filtra por umbral. Devuelve (chunks, baja_confianza)."""
    vectores = await embeddings().aembed_documents(consultas)
    s = settings
    where_clause = (
        sql.SQL("WHERE experimento_id = %(exp)s ")
        if s.rag_experimento_id
        else sql.SQL("")
    )
    query = sql.SQL(
        "SELECT {id} AS id, "
        "COALESCE(seccion_h1, '') AS seccion_h1, "
        "COALESCE(seccion_h2, '') AS seccion_h2, "
        "COALESCE(seccion_h3, '') AS seccion_h3, "
        "{txt} AS contenido, {meta} AS metadata, "
        "1 - ({emb} <=> %(v)s::vector) AS similitud "
        "FROM {tabla} "
        "{where}"
        "ORDER BY {emb} <=> %(v)s::vector LIMIT %(k)s"
    ).format(
        id=sql.Identifier(s.rag_col_id),
        txt=sql.Identifier(s.rag_col_contenido),
        meta=sql.Identifier(s.rag_col_metadata),
        emb=sql.Identifier(s.rag_col_embedding),
        tabla=sql.Identifier(s.rag_tabla),
        where=where_clause,
    )

    mejores: dict = {}
    async with await psycopg.AsyncConnection.connect(s.pg_dsn_rag, row_factory=dict_row) as conn:
        for v in vectores:
            params: dict = {"v": _vec(v), "k": s.rag_top_k}
            if s.rag_experimento_id:
                params["exp"] = s.rag_experimento_id
            cur = await conn.execute(query, params)
            for fila in await cur.fetchall():
                fila["contenido"] = _formatear_contenido(fila)
                previo = mejores.get(fila["id"])
                if previo is None or fila["similitud"] > previo["similitud"]:
                    mejores[fila["id"]] = fila

    ordenados = sorted(mejores.values(), key=lambda f: f["similitud"], reverse=True)
    aprobados = [f for f in ordenados if f["similitud"] >= s.rag_umbral][: s.rag_max_chunks]
    if aprobados:
        return aprobados, False
    return ordenados[:1], True  # mejor esfuerzo, marcado como baja confianza
