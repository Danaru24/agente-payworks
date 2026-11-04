# Pendientes para Ulises
 
## Datos y conexiones (`.env.example`, `01-configmap.yaml`, `02-secret.yaml`)
- [ ] URLs y nombres de modelo de vLLM (LLM y embeddings)
- [ ] DSNs de PostgreSQL: usuario solo lectura (RAG + catálogo) y usuario de memoria
- [ ] Tabla y columnas de pgvector (contenido, metadata, embedding)
- [ ] Tabla del catálogo, columna UID y descripción de columnas (`prompts/catalogo_esquema.md`)
- [ ] URL y token del MCP; dashboard UID; URL pública de Grafana
- [ ] Imagen del contenedor en el registro
 
## Contenido
- [ ] Glosario base de Payworks sintético (`prompts/base_payworks.md`)
- [ ] Textos fijos: mensaje malicioso y redirección (`config.py`)
- [ ] YAML de recursos externos (`deploy/recursos/`)
- [ ] Diagrama principal (`docs/assets/arquitectura.svg`) y GIF demo (`docs/assets/demo.gif`)
 
## Verificaciones técnicas
- [ ] `python scripts/listar_tools_mcp.py` → confirmar argumentos de `run_panel_query` y `generate_deeplink`
- [ ] ¿`run_panel_query` funciona con paneles Elasticsearch en Grafana 10.4? Si no: POC solo VictoriaMetrics
- [ ] Forma real de la respuesta de `run_panel_query` → ajustar `tools/series.py::extraer_series`
- [ ] Calibrar `RAG_UMBRAL` con el golden dataset
- [ ] ¿OpenWebUI renderiza imágenes `data:image/png;base64` en Markdown? (experimento de gráficas)
- [ ] Verificar que tu versión de vLLM soporta `response_format` json_schema
- [ ] Explicación del criterio de las 3 inferencias (prometido)
 
## Por discutir
- [ ] Registro de auditoría para mensajes maliciosos (fase futura)
- [ ] LangSmith vs. alternativa autohospedada (solo exploración en POC)