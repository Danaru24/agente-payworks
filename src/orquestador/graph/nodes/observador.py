"""Nodo E – Observador (MCP Grafana). En la POC la invocación es DETERMINISTA:
por cada UID objetivo se ejecuta la consulta del panel (ver ADR-0004)."""
from orquestador.config import settings
from orquestador.tools import series as S
from orquestador.tools.grafana_mcp import consultar_panel
from orquestador.tools.graficas import png_base64
from orquestador.utils import eventos
 
 
async def observador(state: dict) -> dict:
    eventos.estado("observador")
    uids = state.get("paneles_objetivo", [])[: settings.max_paneles]
    rango = state.get("rango_tiempo")
    if not uids or not rango:
        return {"recuperacion_mcp": [], "completadas": ["mcp"],
                "errores_tools": ["mcp: sin paneles objetivo o sin rango de tiempo"]}
 
    resultados, graficas, errores = [], [], []
    for uid in uids:
        eventos.estado("observador", f"📈 Observador: panel {uid}…")
        try:
            r = await consultar_panel(uid, rango)
        except Exception as e:  # noqa: BLE001
            errores.append(f"mcp: panel {uid}: {e}")
            continue
        series = S.extraer_series(r["datos"])
        resultados.append({
            "panel": uid, "rango": rango, "deeplink": r["deeplink"],
            "series": [{"nombre": s["nombre"], "resumen": S.resumir(s["puntos"]),
                        "muestra": S.muestrear(s["puntos"], settings.serie_puntos_muestra)} for s in series],
        })
        if series and settings.modo_graficas in ("png", "ambos"):
            graficas.append({"titulo": f"Panel {uid}", "png_b64": png_base64(f"Panel {uid}", series)})
 
    upd = {"recuperacion_mcp": resultados, "graficas": graficas, "completadas": ["mcp"]}
    if errores:
        upd["errores_tools"] = errores
    return upd