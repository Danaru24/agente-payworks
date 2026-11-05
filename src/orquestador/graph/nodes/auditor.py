"""Nodo F1 – Auditor: ¿la evidencia alcanza para responder sin inventar?
Solo marca QUÉ repetir y POR QUÉ; las nuevas instrucciones las escribe el Estratega."""
from typing import Literal
 
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel
 
from orquestador.config import settings
from orquestador.llm.cliente import estructurado
from orquestador.llm.prompts import cargar_prompt
from orquestador.utils import eventos, formato
 
 
class Veredicto(BaseModel):
    suficiente: bool
    justificacion: str
    tools_a_repetir: list[Literal["rag", "catalogo", "mcp"]] = []
 
 
def _evidencia(state: dict) -> str:
    mcp = [{k: v for k, v in r.items() if k != "series"} | {
        "series": [{"nombre": s["nombre"], "resumen": s["resumen"]} for s in r.get("series", [])]}
        for r in state.get("recuperacion_mcp", [])]
    return "\n\n".join([
        formato.bloque("Mensaje actual", state["mensaje_actual"]),
        formato.bloque("Interpretación", state.get("interpretacion")),
        formato.bloque("Contexto RAG", [c.get("contenido") for c in state.get("contexto_rag", [])]),
        formato.bloque("RAG baja confianza", state.get("rag_baja_confianza", False)),
        formato.bloque("Paneles del catálogo", state.get("paneles_recuperados")),
        formato.bloque("Métricas (resumen)", mcp),
        formato.bloque("Errores técnicos", state.get("errores_tools")),
        formato.bloque("Diálogo previo Estratega/Auditor", state.get("observaciones")),
    ])
 
 
async def auditor(state: dict) -> dict:
    eventos.estado("auditor")
    if not (state.get("usar_rag") or state.get("usar_catalogo") or state.get("usar_mcp")):
        # Atajo determinista: sin tools planeadas (p. ej. saludo) no hay evidencia que auditar
        return {"validacion_final": True, "intentos": state.get("intentos", 0) + 1,
                "observaciones": ["[Auditor] Sin tools planeadas: respuesta conversacional."]}
    r: Veredicto = await estructurado("auditor", Veredicto).ainvoke(
        [SystemMessage(cargar_prompt("auditor", ("auditar-evidencia",))), HumanMessage(_evidencia(state))])
    intentos = state.get("intentos", 0) + 1
    obs = [f"[Auditor #{intentos}] {r.justificacion}"]
    if r.suficiente:
        return {"validacion_final": True, "intentos": intentos, "observaciones": obs}
    if intentos >= settings.max_intentos or not r.tools_a_repetir:
        return {"validacion_final": False, "intentos": intentos,
                "observaciones": obs + ["[Auditor] Sin más intentos: responder con lo disponible y declarar faltantes."]}
    return {"validacion_final": False, "intentos": intentos, "observaciones": obs,
            "replanear": True, "pendientes": list(r.tools_a_repetir)}