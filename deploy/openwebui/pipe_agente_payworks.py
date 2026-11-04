"""
title: Agente Payworks
description: Pipe delgado que conecta OpenWebUI con el orquestador LangGraph (SSE).
version: 0.1.0
requirements: httpx
"""
# Instalar en OpenWebUI: Admin Panel > Functions > + > pegar este archivo > habilitar.
# Este pipe NO tiene lógica: traduce eventos del orquestador a eventos de OpenWebUI.
import json
 
import httpx
from pydantic import BaseModel, Field
 
 
class Pipe:
    class Valves(BaseModel):
        ORQUESTADOR_URL: str = Field(default="http://orquestador-payworks:8080/chat/stream")  # TODO(ulises)
        TIMEOUT_S: int = Field(default=120)
 
    def __init__(self):
        self.valves = self.Valves()
 
    @staticmethod
    def _texto(contenido) -> str:
        if isinstance(contenido, list):  # mensajes multimodales
            return " ".join(p.get("text", "") for p in contenido if p.get("type") == "text")
        return contenido or ""
 
    async def pipe(self, body: dict, __user__: dict | None = None,
                   __metadata__: dict | None = None, __event_emitter__=None):
        mensajes = body.get("messages", [])
        payload = {
            "mensaje": self._texto(mensajes[-1]["content"]) if mensajes else "",
            "session_id": (__metadata__ or {}).get("chat_id") or "sin-sesion",
            "user_id": (__user__ or {}).get("id"),
        }
 
        async def estado(desc: str, done: bool = False):
            if __event_emitter__:
                await __event_emitter__({"type": "status", "data": {"description": desc, "done": done}})
 
        try:
            async with httpx.AsyncClient(timeout=self.valves.TIMEOUT_S) as cli:
                async with cli.stream("POST", self.valves.ORQUESTADOR_URL, json=payload) as r:
                    r.raise_for_status()
                    async for linea in r.aiter_lines():
                        if not linea.startswith("data: "):
                            continue
                        ev = json.loads(linea[6:])
                        if ev["tipo"] == "status":
                            await estado(ev["mensaje"])
                        elif ev["tipo"] == "token":
                            yield ev["texto"]
                        elif ev["tipo"] == "error":
                            yield f"\n\n> ⚠️ {ev['mensaje']}"
                        elif ev["tipo"] == "done":
                            await estado("Listo", done=True)
        except httpx.HTTPError as e:
            await estado("Error de conexión", done=True)
            yield f"> ⚠️ No pude contactar al orquestador: {e}"
 