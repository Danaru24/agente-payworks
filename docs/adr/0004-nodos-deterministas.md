# ADR-0004 · Bibliotecario y Observador sin LLM en la POC
**Decisión:** RAG y consulta de paneles se ejecutan con código; el LLM no elige tools del MCP.
**Por qué:** un modelo de 7B es poco confiable en tool calling encadenado y cada llamada suma latencia.
**Consecuencia:** al migrar a modelos mayores, el Observador puede pasar a tool calling con la misma allowlist.