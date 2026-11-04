"""Cliente MCP de Grafana (StreamableHTTP) con ALLOWLIST del lado del cliente:
el servidor puede exponer muchas tools, el orquestador solo carga las permitidas."""
import json
 
from langchain_mcp_adapters.client import MultiServerMCPClient
 
from orquestador.config import settings
 
_tools: dict | None = None
 
 
async def tools_permitidas() -> dict:
    global _tools
    if _tools is None:
        headers = {"Authorization": f"Bearer {settings.mcp_token}"} if settings.mcp_token else {}
        cliente = MultiServerMCPClient({"grafana": {
            "transport": "streamable_http", "url": settings.mcp_url, "headers": headers}})
        _tools = {t.name: t for t in await cliente.get_tools() if t.name in settings.mcp_tools_permitidas}
    return _tools
 
 
def _parsear(resultado):
    if isinstance(resultado, tuple):          # (contenido, artefacto)
        resultado = resultado[0]
    if isinstance(resultado, list):            # bloques de contenido MCP
        resultado = "".join(b.get("text", "") if isinstance(b, dict) else str(b) for b in resultado)
    try:
        return json.loads(resultado)
    except (TypeError, json.JSONDecodeError):
        return resultado
 
 
async def consultar_panel(uid_panel: str, rango: dict) -> dict:
    """TODO(ulises): confirmar nombres de argumentos con scripts/listar_tools_mcp.py.
    run_panel_query viene apagada por defecto en el server: habilitarla con --enabled-tools."""
    tools = await tools_permitidas()
    args = {"dashboardUid": settings.grafana_dashboard_uid, "panelId": uid_panel,
            "start": rango["desde"], "end": rango["hasta"]}
    datos = _parsear(await tools["run_panel_query"].ainvoke(args))
    deeplink = None
    if "generate_deeplink" in tools:
        try:
            deeplink = _parsear(await tools["generate_deeplink"].ainvoke({
                "resourceType": "panel", "dashboardUid": settings.grafana_dashboard_uid,
                "panelId": uid_panel, "timeRange": {"from": rango["desde"], "to": rango["hasta"]}}))
        except Exception:  # el deeplink es opcional
            deeplink = None
    return {"datos": datos, "deeplink": deeplink}