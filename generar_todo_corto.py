# -*- coding: utf-8 -*-
"""
Ejecuta el pipeline completo del Short diario del Evangelio:
    1) guion_corto.py            -> elige la historia del día + guion (Claude API)
    2) generar_metadata_corto.py -> titulo, descripcion, tags de YouTube
    3) generar_video_corto.py    -> miniatura vertical + narracion + video MP4
    4) subir_youtube_corto.py    -> sube a YouTube, a la playlist "Evangelio en 2 Minutos"

Uso:
    python generar_todo_corto.py               # short de hoy
    python generar_todo_corto.py 2026-08-25    # una fecha concreta
"""

import os
import subprocess
import sys
from datetime import date, datetime

try:
    from zoneinfo import ZoneInfo
    _ZONA_NY = ZoneInfo("America/New_York")
except Exception:                                                # noqa: BLE001
    _ZONA_NY = None

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output_corto")


def fecha_hoy_ny():
    if _ZONA_NY is not None:
        return datetime.now(_ZONA_NY).date()
    return date.today()


def correr(cmd):
    print("\n$ %s" % " ".join(cmd))
    r = subprocess.run(cmd, cwd=BASE_DIR)
    if r.returncode != 0:
        print("[AVISO] El paso '%s' termino con error (codigo %d)."
              % (cmd[1], r.returncode))
        return False
    return True


def main():
    fecha_str = sys.argv[1] if len(sys.argv) > 1 else fecha_hoy_ny().isoformat()

    py = sys.executable
    print("=== Short diario del Evangelio para %s ===" % fecha_str)

    if not correr([py, "guion_corto.py", fecha_str]):
        print("No se pudo generar el guion. Deteniendo el pipeline.")
        sys.exit(1)

    corto_json = os.path.join(OUTPUT_DIR, "corto_%s.json" % fecha_str)
    if not os.path.exists(corto_json):
        print("[ERROR] No se encontro %s." % corto_json)
        sys.exit(1)

    if not correr([py, "generar_metadata_corto.py", corto_json]):
        print("Seguimos sin metadata (se puede completar a mano).")

    video_ok = correr([py, "generar_video_corto.py", corto_json])

    subida_ok = False
    if video_ok:
        subida_ok = correr([py, "subir_youtube_corto.py", corto_json])
    else:
        print("Sin video no se sube nada a YouTube.")

    print("\n=== Listo. Archivo principal: %s ===" % corto_json)
    if subida_ok:
        print("  - Subido a YouTube (playlist 'Evangelio en 2 Minutos')")
    else:
        print("  - NO se subio a YouTube (revisar el error de arriba)")


if __name__ == "__main__":
    main()
