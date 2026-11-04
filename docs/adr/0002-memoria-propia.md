# ADR-0002 · Memoria propia en PostgreSQL (no PostgresSaver)
**Decisión:** tabla `agente_memoria.conversaciones` con solo mensajes del usuario y respuestas finales.
**Por qué:** el checkpointer guarda todo el state (salidas de tools); solo interesan los turnos visibles.
**Consecuencia:** `user_id` ya existe para habilitar memoria por usuario sin migración.