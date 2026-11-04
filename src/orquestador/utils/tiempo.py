"""Resolución DETERMINISTA de rangos de tiempo. El LLM solo clasifica la expresión;
el cálculo de fechas lo hace código (los LLM se equivocan con fechas)."""
from datetime import datetime, timedelta
from typing import Literal
from zoneinfo import ZoneInfo
 
from pydantic import BaseModel
 
from orquestador.config import settings
 
 
class RangoSolicitado(BaseModel):
    tipo: Literal["ultimos", "hoy", "ayer", "absoluto", "ninguno"]
    cantidad: int | None = None
    unidad: Literal["minutos", "horas", "dias"] | None = None
    desde: str | None = None   # ISO 8601, solo si tipo == "absoluto"
    hasta: str | None = None
 
 
def ahora() -> datetime:
    return datetime.now(ZoneInfo(settings.zona_horaria))
 
 
def resolver_rango(r: RangoSolicitado | None) -> dict:
    tz = ZoneInfo(settings.zona_horaria)
    fin = ahora()
    if r is None or r.tipo == "ninguno":
        inicio = fin - timedelta(hours=settings.rango_default_horas)
    elif r.tipo == "ultimos":
        delta = {"minutos": timedelta(minutes=1), "horas": timedelta(hours=1),
                 "dias": timedelta(days=1)}[r.unidad or "horas"]
        inicio = fin - delta * max(1, r.cantidad or 1)
    elif r.tipo == "hoy":
        inicio = fin.replace(hour=0, minute=0, second=0, microsecond=0)
    elif r.tipo == "ayer":
        hoy0 = fin.replace(hour=0, minute=0, second=0, microsecond=0)
        inicio, fin = hoy0 - timedelta(days=1), hoy0
    else:
        inicio = datetime.fromisoformat(r.desde).astimezone(tz) if r.desde else fin - timedelta(hours=1)
        fin = datetime.fromisoformat(r.hasta).astimezone(tz) if r.hasta else fin
    # Límite duro para no reventar el contexto
    if fin - inicio > timedelta(days=settings.rango_max_dias):
        inicio = fin - timedelta(days=settings.rango_max_dias)
    return {"desde": inicio.isoformat(), "hasta": fin.isoformat()}