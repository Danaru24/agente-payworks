"""Cliente MCP de Grafana (StreamableHTTP) con ALLOWLIST del lado del cliente:
el servidor puede exponer muchas tools, el orquestador solo carga las permitidas.

Usa el SDK oficial `mcp` (disponible en el índice RHOAI 3.5) en lugar de
langchain-mcp-adapters, que no existe en ese índice."""
import json
from contextlib import asynccontextmanager

import httpx
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

from orquestador.config import settings

_tools: dict | None = None


def _headers() -> dict:
    return {"Authorization": f"Bearer {settings.mcp_token}"} if settings.mcp_token else {}


@asynccontextmanager
async def _sesion():
    """Abre una sesión MCP inicializada contra settings.mcp_url."""
    # TODO(ulises): mover el timeout a config.py + .env.example (MCP_TIMEOUT_S).
    timeout = getattr(settings, "mcp_timeout_s", 30.0)
    async with httpx.AsyncClient(headers=_headers(), timeout=timeout) as http_client:
        async with streamable_http_client(settings.mcp_url, http_client=http_client) as (
            read_stream, write_stream, _,
        ):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                yield session


async def _cargar_tools(session: ClientSession) -> dict:
    global _tools
    if _tools is None:
        respuesta = await session.list_tools()
        _tools = {t.name: t for t in respuesta.tools if t.name in settings.mcp_tools_permitidas}
    return _tools


async def tools_permitidas() -> dict:
    if _tools is None:
        async with _sesion() as session:
            await _cargar_tools(session)
    return _tools


async def _invocar(session: ClientSession, tools: dict, nombre_tool: str, argumentos: dict):
    if nombre_tool not in settings.mcp_tools_permitidas or nombre_tool not in tools:
        raise PermissionError(f"Tool MCP no permitida o no expuesta: {nombre_tool}")
    resultado = await session.call_tool(nombre_tool, arguments=argumentos)
    return _parsear(resultado)


def _parsear(resultado):
    """Convierte un CallToolResult en dict/list (si es JSON) o texto."""
    bloques = getattr(resultado, "content", None) or []
    texto = "".join(getattr(b, "text", "") or "" for b in bloques if getattr(b, "type", None) == "text")
    if getattr(resultado, "isError", False):
        raise RuntimeError(f"Error de la tool MCP: {texto or 'sin detalle'}")
    if not texto and getattr(resultado, "structuredContent", None) is not None:
        return resultado.structuredContent
    try:
        return json.loads(texto)
    except (TypeError, json.JSONDecodeError):
        return texto


async def consultar_panel(uid_panel: str, rango: dict) -> dict:
    """TODO(ulises): confirmar nombres de argumentos con scripts/listar_tools_mcp.py.
    run_panel_query viene apagada por defecto en el server: habilitarla con --enabled-tools."""
    async with _sesion() as session:
        tools = await _cargar_tools(session)
        args = {"dashboardUid": settings.grafana_dashboard_uid, "panelId": uid_panel,
                "start": rango["desde"], "end": rango["hasta"]}
        datos = await _invocar(session, tools, "run_panel_query", args)
        deeplink = None
        if "generate_deeplink" in tools:
            try:
                deeplink = await _invocar(session, tools, "generate_deeplink", {
                    "resourceType": "panel", "dashboardUid": settings.grafana_dashboard_uid,
                    "panelId": uid_panel, "timeRange": {"from": rango["desde"], "to": rango["hasta"]}})
            except Exception:  # el deeplink es opcional
                deeplink = None
    return {"datos": datos, "deeplink": deeplink}
