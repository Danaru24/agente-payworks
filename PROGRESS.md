# Bitácora
 
## 2026-11-03 – Andamiaje inicial
- Hecho: estructura, state, grafo de 7 nodos + respuesta fija, tools, memoria, API SSE, pipe OpenWebUI, YAML del orquestador, docs.
- Sin probar: nada se ha ejecutado contra servicios reales.
- Siguiente: completar `docs/PENDIENTES.md` → outcome O1 (walking skeleton).

## 2026-11-03 – Flujo PC → Workbench → Pod inmutable
- `.gitignore` reforzado (Workbench/Jupyter, uv/pip, cachés) + `.gitattributes` (LF) para `git pull` sin conflictos.
- `AGENTS.md`: sección "Flujo de Desarrollo y Release".
- `deploy/orquestador/buildconfig-imagestream.yaml` + `RELEASE.md`: build binario en el namespace y tags `vX.Y.Z-oN`; `03-deployment.yaml` apunta a ImageStreamTag local.
