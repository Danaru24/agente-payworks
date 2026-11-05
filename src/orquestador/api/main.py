"""API del orquestador. POST /chat/stream devuelve Server-Sent Events tipados:
  {"tipo": "status", "nodo", "mensaje"}  progreso por subagente
  {"tipo": "token",  "texto"}            texto de la respuesta (streaming)
  {"tipo": "error",  "mensaje"} / {"tipo": "done"}
"""
import json
import logging
from contextlib import asynccontextmanager
 
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
 
from orquestador.config import settings
from orquestador.graph.builder import construir_grafo
from orquestador.memory import filters, repo
 
log = logging.getLogger("orquestador")
grafo = construir_grafo()
 
 
@asynccontextmanager
async def lifespan(_: FastAPI):
    await repo.abrir()
    yield
    await repo.cerrar()
 
 
app = FastAPI(title="Orquestador Agente Payworks", lifespan=lifespan)
 
 
class ChatRequest(BaseModel):
    mensaje: str
    session_id: str
    user_id: str | None = None
 
 
def _sse(evento: dict) -> str:
    return f"data: {json.dumps(evento, ensure_ascii=False)}\n\n"
 
 
@app.get("/health")
async def health():
    return {"status": "ok"}
 
 
@app.post("/chat/stream")
async def chat_stream(req: ChatRequest):
    async def eventos():
        respuesta: list[str] = []
        categoria = None
        try:
            try:
                ventana = await repo.obtener_ventana(req.session_id, settings.history_window)
            except Exception:  # noqa: BLE001  la memoria no debe tumbar el chat
                log.exception("No se pudo leer la memoria; se continúa sin historial")
                ventana = []
            inicial = {"session_id": req.session_id, "user_id": req.user_id,
                       "mensaje_actual": req.mensaje, "ventana_conversacion": ventana,
                       "observaciones": [], "intentos": 0}
            async for modo, dato in grafo.astream(inicial, config={"recursion_limit": settings.recursion_limit},
                                                  stream_mode=["custom", "messages", "updates"]):
                if modo == "custom":
                    if dato.get("tipo") == "token":
                        respuesta.append(dato["texto"])
                    yield _sse(dato)
                elif modo == "messages":
                    msg, meta = dato
                    if meta.get("langgraph_node") == "redactor" and isinstance(msg.content, str) and msg.content:
                        respuesta.append(msg.content)
                        yield _sse({"tipo": "token", "texto": msg.content})
                elif modo == "updates" and "centinela" in dato:
                    categoria = (dato["centinela"] or {}).get("categoria")
        except Exception as e:  # noqa: BLE001
            log.exception("Error en el flujo")
            yield _sse({"tipo": "error", "mensaje": f"Ocurrió un error procesando tu mensaje: {e}"})
        texto = filters.limpiar_para_memoria("".join(respuesta))
        try:
            for rol, contenido in (("user", req.mensaje), ("assistant", texto)):
                if filters.debe_guardar(rol, contenido, categoria):
                    await repo.guardar(req.session_id, req.user_id, rol, contenido)
        except Exception:  # noqa: BLE001
            log.exception("No se pudo guardar la memoria")
        yield _sse({"tipo": "done"})
 
    return StreamingResponse(eventos(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})