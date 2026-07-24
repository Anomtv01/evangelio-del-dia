# -*- coding: utf-8 -*-
"""
Ejecuta el pipeline completo del Jueves Eucaristico:
    1) milagro_del_dia.py           -> elige el milagro de la semana + guion (Claude API)
    2) generar_metadata_milagro.py  -> titulo, descripcion, tags de YouTube
    3) generar_video_milagro.py     -> miniatura + narracion (edge-tts) + video MP4
    4) subir_youtube_milagro.py     -> sube a YouTube, a la playlist "Jueves Eucaristico"

Uso:
    python generar_todo_milagro.py                # milagro del proximo jueves
    python generar_todo_milagro.py 2026-08-06     # una fecha concreta
"""

import os
import re
import subprocess
import sys
from datetime import date, datetime, timedelta

try:
    from zoneinfo import ZoneInfo
    _ZONA_NY = ZoneInfo("America/New_York")
except Exception:                                                # noqa: BLE001
    _ZONA_NY = None

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output_milagro")


def proximo_jueves(fecha):
    d = fecha
    while d.weekday() != 3:
        d += timedelta(days=1)
    return d


def correr(cmd):
    print("\n$ %s" % " ".join(cmd))
    r = subprocess.run(cmd, cwd=BASE_DIR)
    if r.returncode != 0:
        print("[AVISO] El paso '%s' termino con error (codigo %d)."
              % (cmd[1], r.returncode))
        return False
    return True


def main():
    if len(sys.argv) > 1:
        fecha_str = sys.argv[1]
    else:
        hoy = datetime.now(_ZONA_NY).date() if _ZONA_NY else date.today()
        fecha_str = proximo_jueves(hoy).isoformat()

    py = sys.executable
    print("=== Jueves Eucaristico para %s ===" % fecha_str)

    if not correr([py, "milagro_del_dia.py", fecha_str]):
        print("No se pudo generar el milagro. Deteniendo el pipeline.")
        sys.exit(1)

    milagro_json = os.path.join(OUTPUT_DIR, "milagro_%s.json" % fecha_str)
    if not os.path.exists(milagro_json):
        print("[ERROR] No se encontro %s." % milagro_json)
        sys.exit(1)

    if not correr([py, "generar_metadata_milagro.py", milagro_json]):
        print("Seguimos sin metadata (se puede completar a mano).")

    video_ok = correr([py, "generar_video_milagro.py", milagro_json])

    subida_ok = False
    if video_ok:
        subida_ok = correr([py, "subir_youtube_milagro.py", milagro_json])
    else:
        print("Sin video no se sube nada a YouTube.")

    print("\n=== Listo. Archivo principal: %s ===" % milagro_json)
    if subida_ok:
        print("  - Subido a YouTube (playlist 'Jueves Eucaristico')")
    else:
        print("  - NO se subio a YouTube (revisar el error de arriba)")


if __name__ == "__main__":
    main()
