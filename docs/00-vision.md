# Visión y outcomes
 
**Usuarios:** equipo Command (principal) y gerencia (vista panorámica del potencial).
**No-objetivos de la POC:** escritura en sistemas, PromQL libre, logs, varios dashboards, memoria por usuario.
 
## Outcomes (cada uno con su verificación)
| ID | Outcome | Se verifica cuando… |
|---|---|---|
| O1 | Walking skeleton: OpenWebUI → orquestador → respuesta en streaming con estados | Un "hola" muestra estados y texto progresivo |
| O2 | Preguntas conceptuales respondidas desde la documentación | 5 preguntas del golden dataset con respuesta fundamentada |
| O3 | Localizar paneles por tema | "¿Qué panel mide X?" devuelve el panel correcto |
| O4 | Estado de un panel en un periodo | Valores coinciden con Grafana; incluye deeplink |
| O5 | Cadena completa RAG → catálogo → MCP | Pregunta compuesta resuelta en < 60 s |
| O6 | Filtro y memoria | Malicioso, fuera de tema y ambiguo se manejan; "¿y ayer?" usa el historial |
 
## Metas de latencia
Primer estado < 2 s · timeout por tool 15 s · respuesta completa < 60 s.