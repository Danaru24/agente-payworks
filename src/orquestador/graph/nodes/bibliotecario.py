"""Nodo C – Bibliotecario (RAG). Sin LLM."""
from orquestador.tools.rag import buscar_contexto
from orquestador.utils import eventos
 
 
async def bibliotecario(state: dict) -> dict:
    eventos.estado("bibliotecario")
    consultas = [q for q in (state["mensaje_actual"], state.get("interpretacion"),
                             state.get("instruccion_rag")) if q]
    try:
        chunks, baja = await buscar_contexto(consultas)
    except Exception as e:  # noqa: BLE001
        return {"contexto_rag": [], "completadas": ["rag"], "errores_tools": [f"rag: {e}"]}
    upd = {"contexto_rag": chunks, "rag_baja_confianza": baja, "completadas": ["rag"]}
    if not chunks:
        upd["errores_tools"] = ["rag: sin resultados"]
    return upd