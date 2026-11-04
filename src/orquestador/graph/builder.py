"""Ensamble del grafo: nodos + aristas. Ver docs/01-arquitectura.md para el diagrama."""
from langgraph.graph import END, START, StateGraph
 
from orquestador.graph.nodes.auditor import auditor
from orquestador.graph.nodes.bibliotecario import bibliotecario
from orquestador.graph.nodes.catalogador import catalogador
from orquestador.graph.nodes.centinela import centinela
from orquestador.graph.nodes.estratega import estratega
from orquestador.graph.nodes.observador import observador
from orquestador.graph.nodes.redactor import redactor
from orquestador.graph.nodes.respuesta_fija import respuesta_fija
from orquestador.graph.state import AgentState
 
 
def ruta_centinela(state: dict) -> str:
    return "estratega" if state.get("categoria") == "valido" else "respuesta_fija"
 
 
def ruta_estratega(state: dict) -> list[str] | str:
    restantes = [t for t in state.get("pendientes", []) if t not in state.get("completadas", [])]
    if not restantes:
        return "auditor"
    lote = []
    if "rag" in restantes:
        lote.append("bibliotecario")
    if "catalogo" in restantes:
        lote.append("catalogador")
    if "mcp" in restantes and "catalogo" not in restantes:  # E espera a D
        lote.append("observador")
    return lote  # varios nodos => corren en paralelo
 
 
def ruta_auditor(state: dict) -> str:
    return "estratega" if state.get("replanear") else "redactor"
 
 
def construir_grafo():
    g = StateGraph(AgentState)
    for nombre, fn in [("centinela", centinela), ("respuesta_fija", respuesta_fija),
                       ("estratega", estratega), ("bibliotecario", bibliotecario),
                       ("catalogador", catalogador), ("observador", observador),
                       ("auditor", auditor), ("redactor", redactor)]:
        g.add_node(nombre, fn)
    g.add_edge(START, "centinela")
    g.add_conditional_edges("centinela", ruta_centinela, ["estratega", "respuesta_fija"])
    g.add_conditional_edges("estratega", ruta_estratega,
                            ["bibliotecario", "catalogador", "observador", "auditor"])
    for n in ("bibliotecario", "catalogador", "observador"):
        g.add_edge(n, "estratega")
    g.add_conditional_edges("auditor", ruta_auditor, ["estratega", "redactor"])
    g.add_edge("redactor", END)
    g.add_edge("respuesta_fija", END)
    return g.compile()