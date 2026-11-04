"""Estandarización de series: el LLM NUNCA recibe series crudas, solo resúmenes."""
import statistics
from typing import Any
 
from orquestador.config import settings
 
Punto = tuple[float, float]
 
 
def extraer_series(dato: Any) -> list[dict]:
    """Extrae series de respuestas de Grafana (frames) o Prometheus/VictoriaMetrics (matrix).
    TODO(ulises): validar contra una respuesta real de run_panel_query."""
    series: list[dict] = []
 
    def visitar(nodo: Any, nombre: str = "serie"):
        if isinstance(nodo, dict):
            # Grafana data frame: {"schema": {...}, "data": {"values": [[ts...], [v...]]}}
            vals = nodo.get("data", {}).get("values") if isinstance(nodo.get("data"), dict) else None
            if isinstance(vals, list) and len(vals) >= 2:
                nom = (nodo.get("schema") or {}).get("name") or nombre
                for i, col in enumerate(vals[1:], start=1):
                    pts = [(float(t), float(v)) for t, v in zip(vals[0], col) if _num(t) and _num(v)]
                    if pts:
                        series.append({"nombre": f"{nom}#{i}" if len(vals) > 2 else nom, "puntos": pts})
                return
            # Prometheus matrix: {"metric": {...}, "values": [[ts, "v"], ...]}
            if isinstance(nodo.get("values"), list) and "metric" in nodo:
                pts = [(float(t), float(v)) for t, v in nodo["values"] if _num(t) and _num(v)]
                if pts:
                    series.append({"nombre": str(nodo["metric"]), "puntos": pts})
                return
            for k, v in nodo.items():
                visitar(v, str(k))
        elif isinstance(nodo, list):
            for v in nodo:
                visitar(v, nombre)
 
    visitar(dato)
    return series
 
 
def _num(x) -> bool:
    try:
        float(x)
        return True
    except (TypeError, ValueError):
        return False
 
 
def muestrear(puntos: list[Punto], n: int) -> list[Punto]:
    if len(puntos) <= n:
        return puntos
    paso = len(puntos) / n
    return [puntos[int(i * paso)] for i in range(n)]
 
 
def resumir(puntos: list[Punto]) -> dict:
    valores = [v for _, v in puntos]
    if not valores:
        return {"vacia": True}
    ordenados = sorted(valores)
    p95 = ordenados[min(len(ordenados) - 1, int(0.95 * len(ordenados)))]
    media = statistics.fmean(valores)
    desv = statistics.pstdev(valores) if len(valores) > 1 else 0.0
    mitad = len(valores) // 2 or 1
    m1, m2 = statistics.fmean(valores[:mitad]), statistics.fmean(valores[mitad:] or valores)
    tendencia = "estable"
    if m1 and abs(m2 - m1) / abs(m1) > 0.1:
        tendencia = "al alza" if m2 > m1 else "a la baja"
    anomalias = []
    if desv > 0:
        candidatos = sorted(puntos, key=lambda p: abs(p[1] - media), reverse=True)
        anomalias = [{"ts": t, "valor": v} for t, v in candidatos[: settings.serie_max_anomalias]
                     if abs(v - media) / desv >= 3]
    return {"puntos": len(valores), "min": min(valores), "max": max(valores), "promedio": round(media, 4),
            "p95": p95, "ultimo": valores[-1], "tendencia": tendencia, "anomalias": anomalias}