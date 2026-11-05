"""Nodo D – Catalogador: text-to-SQL acotado a UNA tabla, validado fail-closed (sqlparse + re)."""
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel
 
from orquestador.config import settings
from orquestador.llm.cliente import estructurado
from orquestador.llm.prompts import cargar_prompt, leer
from orquestador.tools.catalogo import SQLRechazado, ejecutar, validar_sql
from orquestador.utils import eventos, formato
 
 
class SalidaSQL(BaseModel):
    sql: str
    razon: str
 
 
async def catalogador(state: dict) -> dict:
    eventos.estado("catalogador")
    sistema = cargar_prompt("catalogador", ("consultar-catalogo",)) + "\n\n" + leer("catalogo_esquema.md")
    humano = "\n\n".join([
        formato.bloque("Instrucción", state.get("instruccion_catalogo")),
        formato.bloque("Interpretación", state.get("interpretacion")),
        formato.bloque("Observaciones previas", state.get("observaciones")),
    ])
    try:
        r: SalidaSQL = await estructurado("catalogador", SalidaSQL).ainvoke(
            [SystemMessage(sistema), HumanMessage(humano)])
        filas = await ejecutar(validar_sql(r.sql))
    except SQLRechazado as e:
        return {"paneles_recuperados": [], "completadas": ["catalogo"],
                "errores_tools": [f"catalogo: SQL rechazado ({e})"]}
    except Exception as e:  # noqa: BLE001
        return {"paneles_recuperados": [], "completadas": ["catalogo"], "errores_tools": [f"catalogo: {e}"]}
 
    uids = [str(f[settings.catalogo_col_uid]) for f in filas if f.get(settings.catalogo_col_uid)]
    upd = {"paneles_recuperados": filas, "completadas": ["catalogo"]}
    if state.get("usar_mcp"):
        upd["paneles_objetivo"] = uids[: settings.max_paneles]
    if not filas:
        upd["errores_tools"] = ["catalogo: sin resultados"]
    return upd