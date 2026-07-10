# -*- coding: utf-8 -*-
"""
Ejecuta el pipeline completo del Salmo del Día:
    1) salmo_del_dia.py           -> elige el salmo + reflexión (Claude API)
    2) generar_metadata_salmo.py  -> título, descripción, tags de YouTube
    3) generar_video_salmo.py     -> thumbnail + narración (ElevenLabs) + video
    4) subir_youtube_salmo.py     -> sube a YouTube, playlist "Salmo del Día"

Uso:
    python generar_todo_salmo.py                # salmo de hoy
    python generar_todo_salmo.py 2026-08-11      # una fecha específica
"""

import os
import subprocess
import sys
from datetime import date

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output_salmo")


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

    print(f"=== Generando paquete completo del Salmo del Día para {fecha_str} ===")

    if not correr([py, "salmo_del_dia.py", fecha_str]):
        print("No se pudo determinar/generar el salmo del día. Deteniendo.")
        sys.exit(1)

    salmo_json = os.path.join(OUTPUT_DIR, f"salmo_{fecha_str}.json")
    if not os.path.exists(salmo_json):
        print(f"[ERROR] No se encontró {salmo_json}.")
        sys.exit(1)

    if not correr([py, "generar_metadata_salmo.py", salmo_json]):
        print("Seguimos sin metadata (se puede completar a mano si hace falta).")

    video_ok = correr([py, "generar_video_salmo.py", salmo_json])

    subida_ok = False
    if video_ok:
        subida_ok = correr([py, "subir_youtube_salmo.py", salmo_json])
    else:
        print("Sin video no se sube nada a YouTube.")

    print(f"\n=== Listo. Archivo principal: {salmo_json} ===")
    if subida_ok:
        print("  - Subido a YouTube (playlist 'Salmo del Día')")
    else:
        print("  - NO se subió a YouTube (revisar el error de arriba)")


if __name__ == "__main__":
    main()
