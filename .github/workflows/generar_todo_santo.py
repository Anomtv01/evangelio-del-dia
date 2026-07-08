# -*- coding: utf-8 -*-
"""
Ejecuta el pipeline completo del Santo del Día:
    1) santo_del_dia.py           -> elige el santo (rotativo) + biografía (Claude API)
    2) generar_metadata_santo.py  -> título, descripción, tags de YouTube
    3) generar_video_santo.py     -> thumbnail + narración (ElevenLabs) + video MP4
    4) subir_youtube_santo.py     -> sube a YouTube, a la playlist "Santo del Día"

Uso:
    python generar_todo_santo.py                # santo de hoy
    python generar_todo_santo.py 2026-08-11      # una fecha específica
"""

import os
import subprocess
import sys
from datetime import date

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output_santo")


def correr(cmd):
    print(f"\n$ {' '.join(cmd)}")
    resultado = subprocess.run(cmd, cwd=BASE_DIR)
    if resultado.returncode != 0:
        print(f"[AVISO] El paso '{cmd[1]}' terminó con error (código {resultado.returncode}).")
        return False
    return True


def main():
    fecha_str = sys.argv[1] if len(sys.argv) > 1 else date.today().isoformat()
    py = sys.executable

    print(f"=== Generando paquete completo del Santo del Día para {fecha_str} ===")

    if not correr([py, "santo_del_dia.py", fecha_str]):
        print("No se pudo determinar/generar el santo del día. Deteniendo el pipeline.")
        sys.exit(1)

    santo_json = os.path.join(OUTPUT_DIR, f"santo_{fecha_str}.json")
    if not os.path.exists(santo_json):
        print(f"[ERROR] No se encontró {santo_json} tras correr santo_del_dia.py.")
        sys.exit(1)

    if not correr([py, "generar_metadata_santo.py", santo_json]):
        print("Seguimos sin metadata de YouTube (se puede completar a mano si hace falta).")

    video_ok = correr([py, "generar_video_santo.py", santo_json])

    subida_ok = False
    if video_ok:
        subida_ok = correr([py, "subir_youtube_santo.py", santo_json])
    else:
        print("Sin video no se sube nada a YouTube.")

    print(f"\n=== Listo. Archivo principal: {santo_json} ===")
    if subida_ok:
        print(f"  - Subido a YouTube (estado: público, playlist 'Santo del Día')")
    else:
        print("  - NO se subió a YouTube (revisar el error de arriba)")


if __name__ == "__main__":
    main()
