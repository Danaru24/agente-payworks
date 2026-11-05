"""Humo O1 (walking skeleton): contrato SSE de POST /chat/stream SIN servicios externos.

El LLM se simula con `GenericFakeChatModel` (streaming palabra por palabra) y la memoria
en RAM. Verifica: status por subagente -> tokens progresivos -> done.
Correr: pytest -q tests/test_o1_humo.py
"""
import json

import pytest
from fastapi.testclient import TestClient
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage

from orquestador.api import main
from orquestador.graph.nodes import auditor, centinela, estratega, redactor
from orquestador.memory import repo

SALUDO = "¡Hola! Soy el Agente Payworks, ¿en qué te ayudo?"


class _FakeEstructurado:
    def __init__(self, salida):
        self.salida = salida

    async def ainvoke(self, _mensajes):
        return self.salida


def _no_llamar(*_a, **_k):
    raise AssertionError("Sin tools planeadas no se debe llamar al LLM")


@pytest.fixture
def memoria(monkeypatch):
    guardados: list[tuple] = []

    async def obtener_ventana(_sid, _n):
        return []

    async def guardar(sid, uid, rol, contenido):
        guardados.append((sid, uid, rol, contenido))

    monkeypatch.setattr(repo, "obtener_ventana", obtener_ventana)
    monkeypatch.setattr(repo, "guardar", guardar)
    return guardados


def _centinela(monkeypatch, categoria: str):
    salida = centinela.SalidaCentinela(categoria=categoria, interpretacion="Saludo sintético",
                                       usar_rag=False, usar_catalogo=False, usar_mcp=False)
    monkeypatch.setattr(centinela, "estructurado", lambda *_a, **_k: _FakeEstructurado(salida))


def _eventos(mensaje: str = "hola") -> list[dict]:
    r = TestClient(main.app).post("/chat/stream", json={"mensaje": mensaje, "session_id": "humo-o1"})
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/event-stream")
    return [json.loads(b[6:]) for b in r.text.split("\n\n") if b.startswith("data: ")]


def test_hola_status_tokens_done(monkeypatch, memoria):
    _centinela(monkeypatch, "valido")
    monkeypatch.setattr(estratega, "estructurado", _no_llamar)
    monkeypatch.setattr(auditor, "estructurado", _no_llamar)
    monkeypatch.setattr(redactor, "llm_para", lambda *_a, **_k: GenericFakeChatModel(
        messages=iter([AIMessage(content=SALUDO)])))

    evs = _eventos()
    tipos = [e["tipo"] for e in evs]
    nodos = [e["nodo"] for e in evs if e["tipo"] == "status"]
    tokens = [e["texto"] for e in evs if e["tipo"] == "token"]

    assert "error" not in tipos, evs
    assert nodos == ["centinela", "estratega", "auditor", "redactor"]
    assert len(tokens) > 1, "los tokens deben llegar de forma progresiva"
    assert "".join(tokens) == SALUDO
    assert tipos[-1] == "done" and tipos.index("token") > tipos.index("status")
    assert [g[2] for g in memoria] == ["user", "assistant"]


def test_fuera_tema_respuesta_fija(monkeypatch, memoria):
    _centinela(monkeypatch, "fuera_tema")
    evs = _eventos("¿quién ganó el partido?")
    assert [e["tipo"] for e in evs] == ["status", "token", "done"]
    assert evs[1]["texto"] == main.settings.mensaje_redireccion


def test_memoria_caida_no_tumba_el_chat(monkeypatch, memoria):
    async def falla(*_a, **_k):
        raise ConnectionError("memoria no disponible")

    monkeypatch.setattr(repo, "obtener_ventana", falla)
    _centinela(monkeypatch, "fuera_tema")
    tipos = [e["tipo"] for e in _eventos()]
    assert "error" not in tipos and tipos[-1] == "done"

