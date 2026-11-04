"""Eventos de progreso que viajan por el stream (stream_mode="custom")."""
from langgraph.config import get_stream_writer
 
ETIQUETAS = {
    "centinela": "🛡️ Centinela: analizando tu mensaje…",
    "estratega": "🧭 Estratega: planeando la recuperación…",
    "bibliotecario": "📚 Bibliotecario: buscando en la documentación…",
    "catalogador": "🗂️ Catalogador: localizando paneles…",
    "observador": "📈 Observador: consultando métricas en Grafana…",
    "auditor": "🔎 Auditor: verificando la evidencia…",
    "redactor": "✍️ Redactor: preparando la respuesta…",
}
 
 
def estado(nodo: str, mensaje: str | None = None) -> None:
    get_stream_writer()({"tipo": "status", "nodo": nodo, "mensaje": mensaje or ETIQUETAS.get(nodo, nodo)})
 
 
def token(texto: str) -> None:
    get_stream_writer()({"tipo": "token", "texto": texto})