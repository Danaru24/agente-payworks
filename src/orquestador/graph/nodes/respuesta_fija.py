"""Salidas tempranas: malicioso (genérico), fuera de tema (redirección amable), ambiguo (aclaración)."""
from orquestador.config import settings
from orquestador.utils import eventos
 
 
async def respuesta_fija(state: dict) -> dict:
    cat = state.get("categoria")
    if cat == "malicioso":
        texto = settings.mensaje_malicioso
    elif cat == "ambiguo":
        texto = state.get("pregunta_aclaracion") or "¿Podrías darme más detalle (periodo, panel o tema)?"
    else:
        texto = settings.mensaje_redireccion
    eventos.token(texto)
    return {"mensaje_final": texto}