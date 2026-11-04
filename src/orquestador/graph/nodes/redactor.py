"""Nodo F2 – Redactor: único nodo que emite tokens al usuario (streaming)."""
from langchain_core.messages import HumanMessage, SystemMessage
 
from orquestador.config import settings
from orquestador.graph.nodes.auditor import _evidencia
from orquestador.llm.cliente import llm_para
from orquestador.llm.prompts import cargar_prompt
from orquestador.utils import eventos, formato
 
 
async def redactor(state: dict) -> dict:
    eventos.estado("redactor")
    extra = []
    if not state.get("validacion_final"):
        extra.append(formato.bloque("AVISO", "La evidencia es incompleta: responde solo con lo "
                                    "disponible y explica claramente qué faltó."))
    if settings.modo_graficas in ("deeplink", "ambos"):
        extra.append(formato.bloque("Deeplinks", [r.get("deeplink") for r in state.get("recuperacion_mcp", [])]))
    humano = _evidencia(state) + "\n\n" + "\n\n".join(extra)
 
    partes = []
    async for chunk in llm_para("redactor", streaming=True).astream(
            [SystemMessage(cargar_prompt("redactor", ("redactar-respuesta-openwebui",))), HumanMessage(humano)]):
        if chunk.content:
            partes.append(chunk.content)  # el token viaja por stream_mode="messages"
 
    # Gráficas PNG embebidas (experimento modo png|ambos). TODO(ulises): validar render en OpenWebUI
    anexos = "".join(f"\n\n![{g['titulo']}](data:image/png;base64,{g['png_b64']})"
                     for g in state.get("graficas", []))
    if anexos:
        eventos.token(anexos)
    return {"mensaje_final": "".join(partes) + anexos}