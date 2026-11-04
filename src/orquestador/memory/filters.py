"""Qué entra a la memoria. POC: solo mensajes del humano y respuestas finales.
Los mensajes intermedios entre agentes se observan con LangSmith, no se guardan aquí."""
 
ROLES_PERMITIDOS = {"user", "assistant"}
 
 
def debe_guardar(rol: str, contenido: str, categoria: str | None = None) -> bool:
    if rol not in ROLES_PERMITIDOS or not contenido.strip():
        return False
    # TODO(ulises): reglas futuras (p. ej. registro de auditoría para mensajes maliciosos)
    return True
 
 
def limpiar_para_memoria(contenido: str) -> str:
    """Quita imágenes base64 para no inflar la ventana de conversación."""
    import re
    return re.sub(r"!\[[^\]]*\]\(data:image/[^)]+\)", "[gráfica]", contenido)