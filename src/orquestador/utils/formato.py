import json
 
 
def historial(ventana: list[dict]) -> str:
    if not ventana:
        return "(sin historial)"
    return "\n".join(f"{m['role'].upper()}: {m['content']}" for m in ventana)
 
 
def bloque(titulo: str, dato) -> str:
    if not dato:
        return f"### {titulo}\n(vacío)"
    if not isinstance(dato, str):
        dato = json.dumps(dato, ensure_ascii=False, default=str)
    return f"### {titulo}\n{dato}"