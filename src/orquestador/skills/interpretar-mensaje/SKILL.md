---
name: interpretar-mensaje
description: Convierte el mensaje y el historial en una interpretación de un párrafo con plan de acción.
---
# Interpretar mensaje
Plantilla: "El usuario quiere <objetivo> sobre <tema/panel> en <periodo>. Para resolverlo:
<herramientas y orden>."
 
| Tipo de pregunta | Herramientas |
|---|---|
| Concepto o funcionamiento de Payworks | rag |
| Qué paneles existen / cuál mide X | catalogo |
| Estado o valores en un periodo | catalogo + mcp |
| "¿Por qué subió X?" | rag + catalogo + mcp |