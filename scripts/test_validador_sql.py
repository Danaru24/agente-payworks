"""Verificación rápida (sin BD) de la política fail-closed de `validar_sql`.
    python scripts/test_validador_sql.py
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

try:  # validar_sql no toca la BD; si no hay libpq local (p. ej. en la PC), usa un stub.
    import psycopg  # noqa: F401
except ImportError:
    import types
    _stub = types.ModuleType("psycopg")
    _stub.rows = types.ModuleType("psycopg.rows")
    _stub.rows.dict_row = None
    sys.modules["psycopg"], sys.modules["psycopg.rows"] = _stub, _stub.rows

from orquestador.config import settings  # noqa: E402
from orquestador.tools.catalogo import SQLRechazado, validar_sql  # noqa: E402

TB = settings.catalogo_tabla
LIM = int(settings.catalogo_limite)

POSITIVOS = [
    (f"SELECT uid, title FROM {TB} WHERE title ILIKE '%error%' LIMIT 1", f"LIMIT 1"),
    (f"SELECT uid, title FROM {TB} WHERE title ILIKE '%error%'", f"LIMIT {LIM}"),
    (f"SELECT uid FROM {TB} WHERE title ILIKE '%drop; --%' LIMIT {LIM + 1000};", f"LIMIT {LIM}"),
    (f"SELECT count(*) FROM {TB} LIMIT ALL", f"LIMIT {LIM}"),
    (f"SELECT tipo, count(*) FROM {TB} c GROUP BY tipo ORDER BY 2 DESC", f"LIMIT {LIM}"),
]

NEGATIVOS = [
    f"DELETE FROM {TB}",
    f"DROP TABLE {TB}",
    "SELECT * FROM otra_tabla",
    f"SELECT * FROM {TB}, otra_tabla",
    f"SELECT * FROM {TB}; DROP TABLE {TB}",
    f"SELECT * FROM {TB}; SELECT 1",
    f"SELECT pg_sleep(10) FROM {TB}",
    f"SELECT * FROM {TB} a JOIN otra_tabla b ON a.uid = b.uid",
    f"SELECT * FROM {TB} WHERE uid IN (SELECT uid FROM otra_tabla)",
    f"SELECT * FROM (SELECT * FROM {TB}) t",
    f"SELECT * FROM {TB} -- comentario",
    f"SELECT * FROM {TB} /* x */",
    f"WITH x AS (SELECT 1) SELECT * FROM {TB}",
    f"SELECT * FROM {TB} UNION SELECT * FROM otra_tabla",
    f"SELECT * INTO copia FROM {TB}",
    f"SELECT * FROM {TB} FOR UPDATE",
    f"SELECT pg_read_file('/etc/passwd') FROM {TB}",
    f"SELECT * FROM {TB} LIMIT 5 OFFSET 0 LIMIT 3",
    f"SELECT * FROM {TB} FETCH FIRST 5000 ROWS ONLY",
    "",
]


def main() -> int:
    fallos = 0
    for consulta, esperado in POSITIVOS:
        try:
            r = validar_sql(consulta)
            ok = r.rstrip().endswith(esperado) or esperado in r
            print(("OK  " if ok else "FAIL"), "+", r)
            fallos += not ok
        except SQLRechazado as e:
            print("FAIL + rechazado:", consulta, "->", e)
            fallos += 1
    for consulta in NEGATIVOS:
        try:
            r = validar_sql(consulta)
            print("FAIL - aceptado:", consulta, "->", r)
            fallos += 1
        except SQLRechazado as e:
            print("OK   -", repr(consulta[:60]), "->", e)
    print(f"\n{len(POSITIVOS) + len(NEGATIVOS) - fallos}/{len(POSITIVOS) + len(NEGATIVOS)} casos OK")
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main())

