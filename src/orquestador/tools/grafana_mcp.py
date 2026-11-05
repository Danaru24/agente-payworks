"""Cliente MCP de Grafana (StreamableHTTP) con ALLOWLIST del lado del cliente:
el servidor puede exponer muchas tools, el orquestador solo carga las permitidas.

Usa el SDK oficial `mcp` (disponible en el índice RHOAI 3.5) en lugar de
langchain-mcp-adapters, que no existe en ese índice."""
import json
import re
from contextlib import asynccontextmanager
from datetime import datetime, timezone

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


_UNIDADES_S = {"s": 1, "m": 60, "h": 3600, "d": 86400, "w": 604800}
_RELATIVO = re.compile(r"^now(?:-(\d+)([smhdw]))?$")


def _a_tiempo_mcp(valor) -> str:
    """Normaliza un extremo del rango al formato que acepta query_prometheus:
    RFC3339 o relativo de Grafana (`now`, `now-1h`). Epoch (s o ms) -> RFC3339 UTC."""
    if isinstance(valor, datetime):
        dt = valor if valor.tzinfo else valor.replace(tzinfo=timezone.utc)
        return dt.isoformat()
    if isinstance(valor, (int, float)) or (isinstance(valor, str) and valor.strip().isdigit()):
        n = float(valor)
        n = n / 1000 if n > 1e11 else n  # epoch en ms
        return datetime.fromtimestamp(n, tz=timezone.utc).isoformat()
    return str(valor)


def _a_epoch(valor: str, ahora: datetime) -> float | None:
    """Epoch en segundos de un extremo ya normalizado; None si no se reconoce."""
    m = _RELATIVO.match(valor.strip())
    if m:
        delta = int(m.group(1)) * _UNIDADES_S[m.group(2)] if m.group(1) else 0
        return ahora.timestamp() - delta
    try:
        dt = datetime.fromisoformat(valor.replace("Z", "+00:00"))
    except ValueError:
        return None
    return (dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)).timestamp()


def _step_seconds(desde: str, hasta: str) -> int:
    """~100 puntos por serie, nunca menos de 60 s entre puntos."""
    ahora = datetime.now(timezone.utc)
    t0, t1 = _a_epoch(desde, ahora), _a_epoch(hasta, ahora)
    if t0 is None or t1 is None or t1 <= t0:
        return 60
    return max(60, int((t1 - t0) // 100))


def _uid_datasource(ds) -> str:
    """Extrae el uid de un datasource (`{"uid": ...}` o string). Ignora variables `${...}`."""
    uid = ds.get("uid", "") if isinstance(ds, dict) else (ds if isinstance(ds, str) else "")
    return "" if not uid or uid.startswith("$") else uid


def _extraer_query(nodo) -> tuple[str, str]:
    """Busca la primera (expr, datasourceUid) en la respuesta de get_dashboard_panel_queries.
    Tolera variantes: lista de {title, query, datasource{uid}} o {queries: [{expr, datasource}]}."""
    if isinstance(nodo, dict):
        expr = nodo.get("expr") or nodo.get("query")
        if isinstance(expr, str) and expr.strip():
            ds = nodo.get("datasourceUid") or _uid_datasource(nodo.get("datasource"))
            return expr, ds or ""
        for v in nodo.values():
            expr, ds = _extraer_query(v)
            if expr:
                # Si la query interna no trae datasource, hereda el del panel.
                return expr, ds or _uid_datasource(nodo.get("datasource"))
    elif isinstance(nodo, list):
        for v in nodo:
            expr, ds = _extraer_query(v)
            if expr:
                return expr, ds
    return "", ""


async def consultar_panel(uid_panel: str, rango: dict, panel: dict | None = None) -> dict:
    """Consulta un panel con la Ruta 2 (una sola ClientSession):
    get_dashboard_panel_queries (si el catálogo no trae expr/datasource) -> query_prometheus
    -> generate_deeplink (opcional). `panel` es la fila del catálogo, si el llamador la tiene."""
    panel = panel or {}
    panel_id = panel_uid_a_int(uid_panel)
    desde, hasta = _a_tiempo_mcp(rango["desde"]), _a_tiempo_mcp(rango["hasta"])
    expr = panel.get("expr") or panel.get("query") or ""
    datasource_uid = panel.get("datasource_uid") or panel.get("datasourceUid") or ""

    async with _sesion() as session:
        tools = await _cargar_tools(session)
        if not expr or not datasource_uid:
            respuesta = await _invocar(session, tools, "get_dashboard_panel_queries", {
                "uid": settings.grafana_dashboard_uid, "panelId": panel_id})
            expr_mcp, ds_mcp = _extraer_query(respuesta)
            expr = expr or expr_mcp
            datasource_uid = datasource_uid or ds_mcp
        datasource_uid = datasource_uid or settings.grafana_datasource_uid
        if not expr:
            raise ValueError(f"El panel {panel_id} no expone una query (expr)")
        if not datasource_uid:
            raise ValueError(f"El panel {panel_id} no trae datasourceUid y GRAFANA_DATASOURCE_UID está vacío")

        datos = await _invocar(session, tools, "query_prometheus", {
            "datasourceUid": datasource_uid, "expr": expr, "queryType": "range",
            "startTime": desde, "endTime": hasta, "stepSeconds": _step_seconds(desde, hasta)})

        deeplink = None
        if "generate_deeplink" in tools:
            try:
                deeplink = await _invocar(session, tools, "generate_deeplink", {
                    "resourceType": "panel", "dashboardUid": settings.grafana_dashboard_uid,
                    "panelId": panel_id, "timeRange": {"from": desde, "to": hasta}})
            except Exception:  # noqa: BLE001 – el deeplink es opcional
                deeplink = None
    return {"datos": datos, "deeplink": deeplink}


def panel_uid_a_int(uid_panel) -> int:
    """El catálogo guarda el panel como texto; Grafana espera panelId entero."""
    try:
        return int(str(uid_panel).strip())
    except ValueError as e:
        raise ValueError(f"panel_uid no numérico: {uid_panel!r}") from e
