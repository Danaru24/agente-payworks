# Esquema del catálogo de paneles
 
<!-- TODO(ulises): describir la tabla real (con nombres sintéticos si aplica) -->
Tabla: `paneles_dashboard`
 
| Columna | Tipo | Significado |
|---|---|---|
| panel_uid | text | Identificador del panel en Grafana |
| nombre | text | Título del panel |
| descripcion | text | Qué mide el panel y para qué sirve |
| query | text | Query original del panel |
| datasource | text | VictoriaMetrics / Elasticsearch |