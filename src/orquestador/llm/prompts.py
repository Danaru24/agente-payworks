"""System prompt = base de Payworks + prompt del agente + cuerpo de sus skills.
 
En la POC las skills se cargan de forma FIJA por nodo (sin descubrimiento dinámico),
pero se escriben en formato Agent Skills (SKILL.md) para reutilizarlas a futuro.
"""
from functools import lru_cache
from pathlib import Path
 
RAIZ = Path(__file__).resolve().parent.parent
 
 
def _cuerpo_skill(ruta: Path) -> str:
    texto = ruta.read_text(encoding="utf-8")
    if texto.startswith("---"):
        texto = texto.split("---", 2)[2]
    return texto.strip()
 
 
@lru_cache
def cargar_prompt(agente: str, skills: tuple[str, ...] = ()) -> str:
    partes = [
        (RAIZ / "prompts" / "base_payworks.md").read_text(encoding="utf-8"),
        (RAIZ / "prompts" / f"{agente}.md").read_text(encoding="utf-8"),
    ]
    partes += [_cuerpo_skill(RAIZ / "skills" / s / "SKILL.md") for s in skills]
    return "\n\n---\n\n".join(partes)
 
 
@lru_cache
def leer(nombre: str) -> str:
    return (RAIZ / "prompts" / nombre).read_text(encoding="utf-8")