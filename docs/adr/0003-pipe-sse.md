# ADR-0003 · Pipe de OpenWebUI + SSE tipado
**Decisión:** el orquestador expone `/chat/stream` (SSE); un pipe delgado traduce a eventos de OpenWebUI.
**Por qué:** el protocolo OpenAI no transporta estados de progreso por subagente.
**Consecuencia:** el orquestador es testeable con `curl` sin OpenWebUI.