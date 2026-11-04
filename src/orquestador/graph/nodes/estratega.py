"""Nodo B – Estratega: escribe instrucciones por tool, coordina rondas y revisa errores técnicos.
La revisión técnica es DETERMINISTA (sin LLM); el juicio semántico lo hace el Auditor."""
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field
 
from orquestador.config import settings
from orquestador.graph.state import RESET
from orquestador.llm.cliente import estructurado
from orquestador.llm.prompts import cargar_prompt
from orquestador.utils import eventos, formato
 
 
class Instrucciones(BaseModel):
    instruccion_rag: str | None = None
    instruccion_catalogo: str | None = None
    instruccion_mcp: str | None = None
    justificacion: str | None = Field(None, description="Solo si hubo observaciones: cómo las atendiste")
 
 
async def _planear(state: dict, pendientes: list[str]) -> dict:
    eventos.estado("estratega")
    humano = "\n\n".join([
        formato.bloque("Mensaje actual", state["mensaje_actual"]),
        formato.bloque("Interpretación", state.get("interpretacion")),
        formato.bloque("Tools a instruir", pendientes),
        formato.bloque("Rango de tiempo", state.get("rango_tiempo")),
        formato.bloque("Observaciones previas", state.get("observaciones")),
    ])
    r: Instrucciones = await estructurado("estratega", Instrucciones).ainvoke(
        [SystemMessage(cargar_prompt("estratega", ("planear-recuperacion",))), HumanMessage(humano)])
    upd = {"replanear": False, "pendientes": pendientes,
           "completadas": [RESET], "errores_tools": [RESET]}
    for tool in ("rag", "catalogo", "mcp"):
        valor = getattr(r, f"instruccion_{tool}")
        if tool in pendientes and valor:
            upd[f"instruccion_{tool}"] = valor
    if r.justificacion and state.get("observaciones"):
        upd["observaciones"] = [f"[Estratega] {r.justificacion}"]
    return upd
 
 
async def estratega(state: dict) -> dict:
    if state.get("replanear"):
        return await _planear(state, state.get("pendientes", []))
 
    restantes = [t for t in state.get("pendientes", []) if t not in state.get("completadas", [])]
    if restantes:
        return {}  # la arista decide el siguiente lote (p. ej. Observador después del Catalogador)
 
    errores = state.get("errores_tools", [])
    intentos = state.get("intentos", 0)
    if errores and intentos < settings.max_intentos:
        fallidas = sorted({e.split(":", 1)[0] for e in errores})
        obs = [f"[Estratega] Errores técnicos, reintento de {fallidas}: {'; '.join(errores)}"]
        upd = await _planear({**state, "observaciones": state.get("observaciones", []) + obs}, fallidas)
        upd["observaciones"] = obs + upd.get("observaciones", [])
        upd["intentos"] = intentos + 1
        return upd
    return {"tools_exitosas": not errores}