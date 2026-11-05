"""Estandarización de series: el LLM NUNCA recibe series crudas, solo resúmenes."""
import statistics
from typing import Any
 
from orquestador.config import settings
 
Punto = tuple[float, float]
 
 
def extraer_series(dato: Any) -> list[dict]:
    """Extrae series de respuestas de Grafana (data frames) o Prometheus vía `query_prometheus`
    del MCP de Grafana: matrix (`metric` + `values: [[ts, "v"], ...]`, posiblemente envuelta en
    `{"data": {"result": [...]}}`) o vector instantáneo (`metric` + `value: [ts, "v"]`)."""
    # TODO(ulises): validar contra una respuesta real de query_prometheus en el clúster.
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
            # Prometheus vector: {"metric": {...}, "value": [ts, "v"]}
            if "metric" in nodo and (isinstance(nodo.get("values"), list) or isinstance(nodo.get("value"), list)):
                crudos = nodo["values"] if isinstance(nodo.get("values"), list) else [nodo["value"]]
                pts = [(float(p[0]), float(p[1])) for p in crudos
                       if isinstance(p, (list, tuple)) and len(p) >= 2 and _num(p[0]) and _num(p[1])]
                # Puntos malformados (no par [ts, v] o no numéricos) se descartan sin romper.
                if pts:
                    series.append({"nombre": _nombre_metrica(nodo["metric"], nombre), "puntos": pts})
                return
            for k, v in nodo.items():
                visitar(v, str(k))
        elif isinstance(nodo, list):
            for v in nodo:
                visitar(v, nombre)
 
    visitar(dato)
    return series
 
 
def _nombre_metrica(metric: Any, defecto: str) -> str:
    """`{"__name__": "x", "pod": "a"}` -> `x{pod="a"}` (formato PromQL legible)."""
    if not isinstance(metric, dict) or not metric:
        return str(metric) if metric else defecto
    base = metric.get("__name__", "")
    etiquetas = ",".join(f'{k}="{v}"' for k, v in sorted(metric.items()) if k != "__name__")
    return f"{base}{{{etiquetas}}}" if etiquetas else (base or defecto)


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