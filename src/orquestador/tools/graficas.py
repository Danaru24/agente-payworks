"""Gráficas PNG embebidas (modo png|ambos). Experimento: comparar contra el deeplink."""
import base64
import io
from datetime import datetime
 
import matplotlib
 
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
 
 
def png_base64(titulo: str, series: list[dict]) -> str:
    fig, ax = plt.subplots(figsize=(8, 3), dpi=100)
    for s in series:
        ts = [datetime.fromtimestamp(t / 1000 if t > 1e11 else t) for t, _ in s["puntos"]]
        ax.plot(ts, [v for _, v in s["puntos"]], label=s["nombre"][:40])
    ax.set_title(titulo)
    ax.grid(alpha=0.3)
    if 1 < len(series) <= 6:
        ax.legend(fontsize=7)
    fig.autofmt_xdate()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode()