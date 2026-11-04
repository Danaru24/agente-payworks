"""Fábrica de clientes LLM. Mismo modelo para todos, parámetros distintos por agente."""
from functools import lru_cache
 
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
 
from orquestador.config import settings
 
 
def llm_para(agente: str, streaming: bool = False) -> ChatOpenAI:
    p = settings.params[agente]
    return ChatOpenAI(
        base_url=settings.llm_base_url, api_key=settings.llm_api_key, model=settings.llm_model,
        temperature=p.temperature, max_tokens=p.max_tokens, timeout=settings.llm_timeout_s,
        streaming=streaming,
    )
 
 
def estructurado(agente: str, schema):
    """Salida JSON garantizada vía guided decoding de vLLM (response_format json_schema)."""
    return llm_para(agente).with_structured_output(schema, method="json_schema")
 
 
@lru_cache
def embeddings() -> OpenAIEmbeddings:
    # check_embedding_ctx_length=False: vLLM no usa tiktoken de OpenAI
    return OpenAIEmbeddings(base_url=settings.emb_base_url, api_key=settings.llm_api_key,
                            model=settings.emb_model, check_embedding_ctx_length=False)