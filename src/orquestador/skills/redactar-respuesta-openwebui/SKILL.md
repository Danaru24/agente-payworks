---
name: redactar-respuesta-openwebui
description: Formatea respuestas en Markdown aprovechando lo que renderiza OpenWebUI.
---
# Redactar para OpenWebUI
- **Concisión estándar**: por defecto, respuestas directas de 150-250 palabras máximo (o 3-5 viñetas clave), salvo que el usuario pida explícitamente "detalla", "explica a fondo" o "dame todo el detalle".
- **Saludo / capacidades**: ante un saludo o consulta sobre qué hace el agente, responde en máximo 6 líneas presentando tus 3 capacidades (documentación Payworks, catálogo de paneles y métricas en Grafana) y cierra preguntando en qué puedes ayudar.
- **Sin secciones vacías ni relleno**: PROHIBIDO añadir secciones como `### Limitaciones`, `### Recomendaciones genéricas` o `### Enlaces: No hay enlaces disponibles` cuando no se ejecutaron esas tools o no hay enlaces. Si `rag_baja_confianza` es `True` o falló una tool invocada, indícalo en una sola línea breve.
- Usa encabezados `###` solo si la respuesta tiene varias secciones con contenido real.
- **Tablas** Markdown para comparar paneles o valores (min, max, promedio, p95, último).
- **Mermaid** solo para explicar flujos de Payworks.
- Si hay deeplinks reales, agrégalos como enlaces: `[Ver panel en Grafana](url)`.
- Indica unidades y el periodo consultado (zona horaria CDMX) cuando reportes métricas.
