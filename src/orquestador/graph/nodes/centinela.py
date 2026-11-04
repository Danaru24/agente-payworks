"""Nodo A – Centinela: filtra, interpreta y planea. Se ejecuta UNA sola vez por mensaje."""
from typing import Literal
 
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field
 
from orquestador.llm.cliente import estructurado
from orquestador.llm.prompts import cargar_prompt
from orquestador.utils import eventos, formato
from orquestador.utils.tiempo import RangoSolicitado, ahora, resolver_rango
 
 
class SalidaCentinela(BaseModel):
    categoria: Literal["valido", "malicioso", "fuera_tema", "ambiguo"]
    interpretacion: str = Field(description="Máximo un párrafo: qué pide el usuario + plan de acción")
    pregunta_aclaracion: str | None = Field(None, description="Solo si categoria == ambiguo")
    usar_rag: bool
    usar_catalogo: bool
    usar_mcp: bool
    rango: RangoSolicitado | None = None
    uids_panel: list[str] = Field(default_factory=list, description="UIDs que el usuario dio explícitamente")
 
 
async def centinela(state: dict) -> dict:
    eventos.estado("centinela")
    sistema = cargar_prompt("centinela", ("filtrar-mensaje", "interpretar-mensaje"))
    humano = (f"Fecha y hora actual: {ahora().isoformat()}\n\n"
              f"Historial:\n{formato.historial(state.get('ventana_conversacion', []))}\n\n"
              f"Mensaje actual:\n{state['mensaje_actual']}")
    r: SalidaCentinela = await estructurado("centinela", SalidaCentinela).ainvoke(
        [SystemMessage(sistema), HumanMessage(humano)])
 
    usar_catalogo = r.usar_catalogo
    # Dependencia dura: sin UIDs explícitos, MCP necesita al Catalogador
    if r.usar_mcp and not r.uids_panel:
        usar_catalogo = True
    plan = [t for t, activo in (("rag", r.usar_rag), ("catalogo", usar_catalogo), ("mcp", r.usar_mcp)) if activo]
 
    return {
        "categoria": r.categoria,
        "es_malicioso": r.categoria == "malicioso",
        "interpretacion": r.interpretacion,
        "pregunta_aclaracion": r.pregunta_aclaracion,
        "rango_tiempo": resolver_rango(r.rango) if r.usar_mcp else None,
        "usar_rag": r.usar_rag, "usar_catalogo": usar_catalogo, "usar_mcp": r.usar_mcp,
        "paneles_objetivo": r.uids_panel,
        "pendientes": plan,
        "replanear": True,
        "intentos": 0,
    }