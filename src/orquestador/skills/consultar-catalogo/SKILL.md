---
name: consultar-catalogo
description: Genera SQL SELECT seguro sobre la tabla del catálogo de paneles.
---
# Consultar catálogo
Ejemplos:
- Paneles de errores: `SELECT panel_uid, nombre, descripcion FROM paneles_dashboard WHERE descripcion ILIKE '%error%' OR nombre ILIKE '%error%'`
- Total: `SELECT count(*) AS total FROM paneles_dashboard`
- Por datasource: `SELECT datasource, count(*) FROM paneles_dashboard GROUP BY datasource`