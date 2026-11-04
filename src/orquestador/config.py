"""Configuración central. TODO valor se puede sobrescribir por variable de entorno.
 
Los valores marcados con TODO(ulises) son placeholders que debes completar
(ver docs/PENDIENTES.md y .env.example).
"""
import os
from dataclasses import dataclass, field
 
 
def _s(n: str, d: str = "") -> str:
    return os.getenv(n, d)
 
 
def _i(n: str, d: int) -> int:
    return int(os.getenv(n, str(d)))
 
 
def _f(n: str, d: float) -> float:
    return float(os.getenv(n, str(d)))
 
 
def _lista(n: str, d: str) -> list[str]:
    return [x.strip() for x in os.getenv(n, d).split(",") if x.strip()]
 
 
@dataclass(frozen=True)
class ParamsLLM:
    temperature: float
    max_tokens: int
 
 
def _params(agente: str, temp: float, tokens: int) -> ParamsLLM:
    p = agente.upper()
    return ParamsLLM(_f(f"{p}_TEMPERATURE", temp), _i(f"{p}_MAX_TOKENS", tokens))
 
 
@dataclass(frozen=True)
class Settings:
    # --- LLM (vLLM, API compatible con OpenAI) ---
    llm_base_url: str = _s("LLM_BASE_URL", "http://vllm-llm:8000/v1")  # TODO(ulises)
    llm_api_key: str = _s("LLM_API_KEY", "EMPTY")
    llm_model: str = _s("LLM_MODEL", "qwen2.5-7b-instruct")  # TODO(ulises)
    llm_timeout_s: int = _i("LLM_TIMEOUT_S", 45)
    llm_max_model_len: int = _i("LLM_MAX_MODEL_LEN", 32768)
 
    # --- Embeddings (vLLM en CPU) ---
    emb_base_url: str = _s("EMB_BASE_URL", "http://vllm-embeddings:8000/v1")  # TODO(ulises)
    emb_model: str = _s("EMB_MODEL", "text-embedding")  # TODO(ulises)
 
    # --- PostgreSQL ---
    pg_dsn_rag: str = _s("PG_DSN_RAG", "postgresql://lector@postgres:5432/payworks")  # TODO(ulises)
    pg_dsn_catalogo: str = _s("PG_DSN_CATALOGO", "postgresql://lector@postgres:5432/payworks")  # TODO(ulises)
    pg_dsn_memoria: str = _s("PG_DSN_MEMORIA", "postgresql://memoria@postgres:5432/payworks")  # TODO(ulises)
    memoria_schema: str = _s("MEMORIA_SCHEMA", "agente_memoria")
 
    # --- RAG (pgvector) ---
    rag_tabla: str = _s("RAG_TABLA", "documentos_payworks")  # TODO(ulises)
    rag_col_id: str = _s("RAG_COL_ID", "id")
    rag_col_contenido: str = _s("RAG_COL_CONTENIDO", "text")  # TODO(ulises)
    rag_col_metadata: str = _s("RAG_COL_METADATA", "metadata")  # TODO(ulises)
    rag_col_embedding: str = _s("RAG_COL_EMBEDDING", "embedding")  # TODO(ulises)
    rag_top_k: int = _i("RAG_TOP_K", 3)
    rag_umbral: float = _f("RAG_UMBRAL", 0.75)  # calibrar con el golden dataset
    rag_max_chunks: int = _i("RAG_MAX_CHUNKS", 5)
 
    # --- Catálogo de paneles ---
    catalogo_tabla: str = _s("CATALOGO_TABLA", "paneles_dashboard")  # TODO(ulises)
    catalogo_col_uid: str = _s("CATALOGO_COL_UID", "panel_uid")  # TODO(ulises)
    catalogo_limite: int = _i("CATALOGO_LIMITE", 20)
    catalogo_timeout_ms: int = _i("CATALOGO_TIMEOUT_MS", 5000)
    max_paneles: int = _i("MAX_PANELES_POR_CONSULTA", 5)
 
    # --- MCP Grafana ---
    mcp_url: str = _s("MCP_GRAFANA_URL", "http://mcp-grafana:8000/mcp")  # TODO(ulises)
    mcp_token: str = _s("MCP_GRAFANA_TOKEN", "")
    mcp_tools_permitidas: list[str] = field(default_factory=lambda: _lista(
        "MCP_TOOLS_PERMITIDAS", "get_dashboard_panel_queries,run_panel_query,generate_deeplink"))
    grafana_dashboard_uid: str = _s("GRAFANA_DASHBOARD_UID", "")  # TODO(ulises)
    grafana_url_publica: str = _s("GRAFANA_URL_PUBLICA", "")  # TODO(ulises)
    mcp_timeout_s: int = _i("MCP_TIMEOUT_S", 15)
 
    # --- Series y gráficas ---
    rango_max_dias: int = _i("RANGO_MAX_DIAS", 7)
    rango_default_horas: int = _i("RANGO_DEFAULT_HORAS", 1)
    zona_horaria: str = _s("ZONA_HORARIA", "America/Mexico_City")
    serie_puntos_muestra: int = _i("SERIE_PUNTOS_MUESTRA", 50)
    serie_max_anomalias: int = _i("SERIE_MAX_ANOMALIAS", 5)
    modo_graficas: str = _s("MODO_GRAFICAS", "ambos")  # deeplink | png | ambos
 
    # --- Flujo ---
    history_window: int = _i("HISTORY_WINDOW", 10)
    max_intentos: int = _i("MAX_INTENTOS", 3)
    recursion_limit: int = _i("RECURSION_LIMIT", 40)
 
    # --- Textos fijos ---
    mensaje_malicioso: str = _s(
        "MENSAJE_MALICIOSO",
        "No puedo ayudarte con esa solicitud. Estoy diseñado para responder sobre Payworks.")  # TODO(ulises)
    mensaje_redireccion: str = _s(
        "MENSAJE_REDIRECCION",
        "Parece que eso está fuera de lo que puedo ver. Puedo ayudarte con el estado de Payworks, "
        "sus paneles de monitoreo o conceptos de la aplicación. ¿Qué te gustaría consultar?")  # TODO(ulises)
 
    # --- Parámetros por agente (mismo modelo, distinto request) ---
    params: dict[str, ParamsLLM] = field(default_factory=lambda: {
        "centinela": _params("centinela", 0.0, 400),
        "estratega": _params("estratega", 0.1, 500),
        "catalogador": _params("catalogador", 0.0, 300),
        "auditor": _params("auditor", 0.0, 400),
        "redactor": _params("redactor", 0.3, 1200),
    })
 
 
settings = Settings()