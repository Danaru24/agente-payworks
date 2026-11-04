# AGENTS.md – Reglas para agentes de código (Antigravity)
 
## Contexto
Orquestador LangGraph del Agente Payworks. Lee SOLO lo necesario para la tarea:
- Qué y por qué: `docs/00-vision.md`
- Cómo: `docs/01-arquitectura.md` (dueño de cada campo del state, aristas)
- Decisiones cerradas: `docs/adr/` — NO las contradigas sin proponer un ADR nuevo
- Pendientes: `docs/PENDIENTES.md` · Bitácora: `PROGRESS.md`
 
## Reglas duras
1. Datos sintéticos únicamente. Nunca agregues datos reales, credenciales ni hostnames internos.
2. Toda conexión, límite o parámetro va en `config.py` + `.env.example`. Nada hardcodeado.
3. Cada campo del state tiene UN nodo dueño. No escribas campos de otro nodo.
4. Las series crudas nunca llegan al LLM: pasan por `tools/series.py`.
5. SQL del Catalogador siempre pasa por `validar_sql`.
6. Solo el Redactor emite tokens al usuario; los demás nodos emiten `eventos.estado`.
7. Prompts en `prompts/*.md`, conocimiento procedimental en `skills/*/SKILL.md`. No prompts en código.
8. Dependencias: `psycopg` sin extra `[binary]` (índice RHOAI).
 
## Forma de trabajo
- Trabaja por **outcome** (ver `docs/00-vision.md`), no por lista de tareas.
- Si algo contradice la spec: DETENTE y propone el cambio al documento antes de codificar.
- Al terminar: actualiza `PROGRESS.md` y, si cambió algo visible, el `README.md` (tono educativo, conciso).
- Marca lo que necesites del humano como `TODO(ulises)` y agrégalo a `docs/PENDIENTES.md`.