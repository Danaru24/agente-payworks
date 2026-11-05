# Arquitectura
 
## Comunicación
OpenWebUI (pipe) ⇄ `POST /chat/stream` (SSE). Eventos: `status`, `token`, `error`, `done`.
Dentro de LangGraph: `stream_mode=["custom","messages","updates"]`.
 
## Dueño de cada campo del state
| Nodo | Escribe |
|---|---|
| API | session_id, user_id, mensaje_actual, ventana_conversacion |
| Centinela | categoria, es_malicioso, interpretacion, pregunta_aclaracion, rango_tiempo, usar_*, pendientes (inicial), paneles_objetivo (si el usuario da UIDs) |
| Estratega | instruccion_*, replanear, pendientes, tools_exitosas, observaciones `[Estratega]` |
| Bibliotecario | contexto_rag, rag_baja_confianza |
| Catalogador | paneles_recuperados, paneles_objetivo |
| Observador | recuperacion_mcp, graficas |
| Auditor | validacion_final, intentos, observaciones `[Auditor]`, pendientes (a repetir) |
| Redactor / respuesta fija | mensaje_final |
 
Campos con reducer (escritura paralela): `completadas`, `errores_tools`, `observaciones`.
 
## Reglas de ruteo
- Centinela: `valido` → Estratega; otro → respuesta fija.
- Estratega: C y D en paralelo; E solo cuando D terminó (o con UIDs del usuario).
- Ciclo único con tope `MAX_INTENTOS=3` (incluye reintentos técnicos del Estratega y del Auditor).
- Sin tools planeadas (p. ej. saludo): Estratega y Auditor pasan de forma determinista, sin LLM (`validacion_final=True`), y el Redactor responde.
- Al agotarse: el Redactor responde con lo disponible y declara faltantes.
 
## Presupuesto de contexto (max_model_len = 32k)
| Bloque | Tokens aprox. |
|---|---|
| System prompt (base + agente + skills) | 1.5k |
| Historial (10 mensajes) | 3k |
| RAG (≤5 chunks) | 3k |
| Catálogo (≤20 filas) | 2k |
| Métricas resumidas (≤5 paneles) | 3k |
| Salida | ≤1.2k |
| **Total peor caso** | **~14k** |