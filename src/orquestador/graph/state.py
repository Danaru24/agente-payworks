"""State compartido por todos los nodos del grafo.
 
Regla de oro: cada campo tiene UN nodo dueño que lo escribe (ver docs/01-arquitectura.md).
Los campos con `Annotated[..., reducer]` pueden recibir escrituras de nodos que corren en
paralelo (Bibliotecario y Catalogador) sin pisarse.
"""
import operator
from typing import Annotated, Literal, TypedDict
 
RESET = "__reset__"
 
 
def acumular_o_reiniciar(actual: list | None, nuevo: list | None) -> list:
    """Suma listas; si el primer elemento es RESET, reinicia la lista."""
    nuevo = nuevo or []
    if nuevo and nuevo[0] == RESET:
        return list(nuevo[1:])
    return (actual or []) + nuevo
 
 
Tool = Literal["rag", "catalogo", "mcp"]
 
 
class AgentState(TypedDict, total=False):
    # Entrada
    session_id: str
    user_id: str | None
    mensaje_actual: str
    ventana_conversacion: list[dict]          # [{"role": "user|assistant", "content": str}]
 
    # Centinela (A)
    categoria: Literal["valido", "malicioso", "fuera_tema", "ambiguo"]
    es_malicioso: bool
    interpretacion: str
    pregunta_aclaracion: str | None
    rango_tiempo: dict | None                 # {"desde": iso, "hasta": iso}
    usar_rag: bool
    usar_catalogo: bool
    usar_mcp: bool
 
    # Estratega (B)
    instruccion_rag: str
    instruccion_catalogo: str
    instruccion_mcp: str
    replanear: bool
    pendientes: list[str]                     # tools de la ronda actual
    completadas: Annotated[list[str], acumular_o_reiniciar]
    errores_tools: Annotated[list[str], acumular_o_reiniciar]
    tools_exitosas: bool
 
    # Bibliotecario (C)
    contexto_rag: list[dict]
    rag_baja_confianza: bool
 
    # Catalogador (D)
    paneles_recuperados: list[dict]
    paneles_objetivo: list[str]               # UIDs
 
    # Observador (E)
    recuperacion_mcp: list[dict]
    graficas: list[dict]
 
    # Auditor (F1) / diálogo B <-> F1
    validacion_final: bool
    observaciones: Annotated[list[str], operator.add]
    intentos: int
 
    # Redactor (F2)
    mensaje_final: str