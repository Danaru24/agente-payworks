"""Script CLI ligero para probar RAG en vivo contra payworks_rag_1024 y calibrar RAG_UMBRAL (Outcome O2)."""
import asyncio
import sys
from pathlib import Path

from dotenv import load_dotenv

# Carga .env antes de importar config/rag
ENV_PATH = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(dotenv_path=ENV_PATH, override=False)

from orquestador.config import settings  # noqa: E402
from orquestador.tools.rag import buscar_contexto  # noqa: E402

PREGUNTAS_DEFAULT = [
    "¿Qué es Payworks y cuáles son sus componentes principales?",
    "¿Cómo funciona el flujo de autorización de una transacción en Payworks?",
    "¿Qué significa un código de rechazo o error de comunicación con el autorizador?",
]


def _recortar(texto: str, max_len: int = 120) -> str:
    limpio = " ".join(texto.split())
    return limpio if len(limpio) <= max_len else limpio[: max_len - 3] + "..."


async def _probar_pregunta(pregunta: str) -> None:
    print(f"\n=== Pregunta: {pregunta} ===")
    print(
        f"Tabla: {settings.rag_tabla} | top_k: {settings.rag_top_k} | "
        f"umbral: {settings.rag_umbral} | exp_id: '{settings.rag_experimento_id or '*'}'"
    )
    chunks, baja_confianza = await buscar_contexto([pregunta])
    print(f"Baja confianza: {baja_confianza} | Chunks devueltos: {len(chunks)}")
    if not chunks:
        print("(Sin resultados)")
        return

    encabezado = f"{'ID':>6} | {'Similitud':>9} | {'Sección H1 / H2':<38} | {'Contenido (120 chars)'}"
    print(encabezado)
    print("-" * len(encabezado))
    for c in chunks:
        cid = str(c.get("id", ""))
        sim = float(c.get("similitud", 0.0))
        h1 = str(c.get("seccion_h1") or "").strip()
        h2 = str(c.get("seccion_h2") or "").strip()
        seccion = " > ".join(p for p in (h1, h2) if p) or "-"
        seccion_col = _recortar(seccion, 38)
        extracto = _recortar(str(c.get("contenido", "")), 120)
        print(f"{cid:>6} | {sim:>9.4f} | {seccion_col:<38} | {extracto}")


async def main() -> None:
    preguntas = [" ".join(sys.argv[1:])] if len(sys.argv) > 1 else PREGUNTAS_DEFAULT
    for p in preguntas:
        await _probar_pregunta(p)


if __name__ == "__main__":
    asyncio.run(main())
