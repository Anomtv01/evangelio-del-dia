# -*- coding: utf-8 -*-
"""
Ejecuta el pipeline completo del Evangelio del Día:
    1) evangelio_del_dia.py   -> texto del Evangelio (JSON)
    2) generar_reflexion.py   -> reflexión original (Claude API)
    3) generar_thumbnail.py   -> imagen 1280x720
    4) generar_metadata.py    -> título, descripción, tags de YouTube

Uso:
    python generar_todo.py                # hoy
    python generar_todo.py 2026-12-25      # una fecha específica
"""

import os
import subprocess
import sys
from datetime import date, datetime

try:
    from zoneinfo import ZoneInfo
    _ZONA_NY = ZoneInfo("America/New_York")
except Exception:
    _ZONA_NY = None


def fecha_hoy_ny():
    """Fecha de 'hoy' según la hora de Nueva York, no la del servidor
    (importante porque GitHub Actions corre en UTC; sin esto, correr el
    workflow manualmente de noche en NY podía generar el Evangelio de
    'mañana' en vez de 'hoy')."""
    if _ZONA_NY is not None:
        return datetime.now(_ZONA_NY).date()
    return date.today()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")


def correr(cmd):
    print(f"\n$ {' '.join(cmd)}")
    resultado = subprocess.run(cmd, cwd=BASE_DIR)
    if resultado.returncode != 0:
        print(f"[AVISO] El paso '{cmd[1]}' terminó con error (código {resultado.returncode}).")
        return False
    return True


def main():
    fecha_str = sys.argv[1] if len(sys.argv) > 1 else fecha_hoy_ny().isoformat()
    py = sys.executable

    print(f"=== Generando paquete completo del Evangelio para {fecha_str} ===")

    if not correr([py, "evangelio_del_dia.py", fecha_str]):
        print("No se pudo obtener el Evangelio del día. Deteniendo el pipeline.")
        sys.exit(1)

    evangelio_json = os.path.join(OUTPUT_DIR, f"evangelio_{fecha_str}.json")

    reflexion_ok = correr([py, "generar_reflexion.py", evangelio_json])
    reflexion_txt = os.path.join(OUTPUT_DIR, f"reflexion_{fecha_str}.txt")
    if not reflexion_ok or not os.path.exists(reflexion_txt):
        print("Seguimos sin reflexión (podés agregarla después a mano).")
        reflexion_txt = None

    correr([py, "generar_thumbnail.py", evangelio_json])

    metadata_cmd = [py, "generar_metadata.py", evangelio_json]
    if reflexion_txt:
        metadata_cmd.append(reflexion_txt)
    correr(metadata_cmd)

    narracion_cmd = [py, "generar_narracion.py", evangelio_json]
    if reflexion_txt:
        narracion_cmd.append(reflexion_txt)
    narracion_ok = correr(narracion_cmd)

    video_ok = False
    if narracion_ok:
        video_ok = correr([py, "generar_video.py", evangelio_json])
    else:
        print("Sin narración no se puede armar el video. Deteniendo antes de YouTube.")

    subida_ok = False
    if video_ok:
        subida_ok = correr([py, "subir_youtube.py", evangelio_json])
    else:
        print("Sin video no se sube nada a YouTube.")

    print(f"\n=== Listo. Archivos en {OUTPUT_DIR} ===")
    print(f"  - evangelio_{fecha_str}.json")
    print(f"  - reflexion_{fecha_str}.txt")
    print(f"  - thumbnail_{fecha_str}.png")
    print(f"  - metadata_{fecha_str}.json")
    print(f"  - narracion_{fecha_str}.mp3")
    print(f"  - video_{fecha_str}.mp4")
    if subida_ok:
        print("  - Subido a YouTube como PRIVADO (revisalo antes de publicar)")
    else:
        print("  - NO se subió a YouTube (revisar el error de arriba)")


if __name__ == "__main__":
    main()
