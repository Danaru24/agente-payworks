# Bitácora
 
## 2026-11-03 – Andamiaje inicial
- Hecho: estructura, state, grafo de 7 nodos + respuesta fija, tools, memoria, API SSE, pipe OpenWebUI, YAML del orquestador, docs.
- Sin probar: nada se ha ejecutado contra servicios reales.
- Siguiente: completar `docs/PENDIENTES.md` → outcome O1 (walking skeleton).

## 2026-11-03 – Flujo PC → Workbench → Pod inmutable
- `.gitignore` reforzado (Workbench/Jupyter, uv/pip, cachés) + `.gitattributes` (LF) para `git pull` sin conflictos.
- `AGENTS.md`: sección "Flujo de Desarrollo y Release".
- `deploy/orquestador/buildconfig-imagestream.yaml` + `RELEASE.md`: build binario en el namespace y tags `vX.Y.Z-oN`; `03-deployment.yaml` apunta a ImageStreamTag local.

## 2026-11-04 – O1 walking skeleton (revisión + ajustes)
- Revisado contrato SSE `api/main.py` ↔ `deploy/openwebui/pipe_agente_payworks.py`: consistente (`status`/`token`/`error`/`done`).
- Estratega y Auditor: atajo determinista sin LLM cuando no hay tools planeadas ("hola" no depende de RAG/catálogo/MCP ni recibe AVISO de evidencia incompleta).
- Memoria tolerante a fallos: si no se puede leer, se sigue sin historial; nuevo `PG_POOL_TIMEOUT_S` (5 s) en `config.py`, `.env.example` y ConfigMap.
- Nuevo `tests/test_o1_humo.py` (LLM simulado, memoria en RAM) + extra `dev` con pytest.
- Sin probar: no hay Python local en la PC; verificar en el Workbench (pytest + `curl -N`).
- Siguiente: superar O1 en vivo → O2.


## 2026-11-05 – Compatibilidad con índice RHOAI 3.5
- Dependencias: fuera `langchain-mcp-adapters`, `psycopg-pool`, `sqlglot`; dentro `mcp>=1.26,<2` y `sqlparse>=0.5.5,<1`.
- `memory/repo.py`: conexiones bajo demanda con `psycopg.AsyncConnection.connect` (`abrir`/`cerrar` quedan como no-op por compatibilidad).
- `tools/catalogo.py`: `validar_sql` reimplementado fail-closed con `sqlparse` + `re` (1 sentencia SELECT, sin comentarios, sin subconsultas/JOIN/UNION/WITH, tabla única = `CATALOGO_TABLA`, `LIMIT` acotado a `CATALOGO_LIMITE`).
- `tools/grafana_mcp.py` y `scripts/listar_tools_mcp.py` ya usaban el SDK `mcp` (sin cambios).
- Nuevo `scripts/test_validador_sql.py` (casos positivos/negativos sin BD).


## 2026-11-05 – Observador: migración de `run_panel_query` a Ruta 2 MCP
- `run_panel_query` no existe en el MCP de Grafana del clúster. `consultar_panel()` ahora usa una sola
  `ClientSession`: `get_dashboard_panel_queries` (si el catálogo no trae `expr`/`datasource_uid`) →
  `query_prometheus` (range, `stepSeconds` ≈ 100 puntos, mínimo 60 s) → `generate_deeplink` (opcional).
- Allowlist por defecto: `get_dashboard_panel_queries, query_prometheus, generate_deeplink, get_panel_image, list_datasources`.
- Nuevo `GRAFANA_DATASOURCE_UID` (fallback opcional del datasource).
- `extraer_series()` soporta matrix/vector de Prometheus (incluido el envoltorio `data.result`) y nombra series como PromQL.
- TODO(ulises): validar contra una respuesta real de `query_prometheus` y pasar la fila del catálogo (`panel=`) desde el Observador cuando el state la tenga.
