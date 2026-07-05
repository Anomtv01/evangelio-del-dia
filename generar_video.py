# -*- coding: utf-8 -*-
"""
Arma el video final (MP4) uniendo la imagen (thumbnail) con la narración
de audio, usando FFmpeg. Video simple: imagen fija durante toda la
duración del audio (después podemos sumarle más movimiento/efectos).

Requiere tener FFmpeg instalado y accesible en el PATH.

Uso:
    python generar_video.py output/evangelio_2026-07-05.json

Salida: output/video_<fecha>.mp4
"""

import json
import os
import subprocess
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")


def verificar_ffmpeg():
    try:
        subprocess.run(
            ["ffmpeg", "-version"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True,
        )
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False


def generar_video(fecha_str, imagen_path, audio_path, out_path):
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", imagen_path,
        "-i", audio_path,
        "-c:v", "libx264",
        "-tune", "stillimage",
        "-c:a", "aac",
        "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-shortest",
        "-vf", "scale=1280:720",
        out_path,
    ]
    resultado = subprocess.run(cmd, capture_output=True, text=True)
    if resultado.returncode != 0:
        raise RuntimeError(f"FFmpeg falló:\n{resultado.stderr[-1500:]}")


def main():
    if len(sys.argv) < 2:
        print("Uso: python generar_video.py output/evangelio_<fecha>.json")
        sys.exit(1)

    if not verificar_ffmpeg():
        print("[ERROR] No se encontró FFmpeg instalado / en el PATH.")
        sys.exit(1)

    json_path = sys.argv[1]
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    fecha = data["fecha"]
    imagen_path = os.path.join(OUTPUT_DIR, f"thumbnail_{fecha}.png")
    audio_path = os.path.join(OUTPUT_DIR, f"narracion_{fecha}.mp3")
    out_path = os.path.join(OUTPUT_DIR, f"video_{fecha}.mp4")

    if not os.path.exists(imagen_path):
        print(f"[ERROR] No se encontró el thumbnail: {imagen_path}")
        sys.exit(1)
    if not os.path.exists(audio_path):
        print(f"[ERROR] No se encontró la narración: {audio_path}")
        sys.exit(1)

    generar_video(fecha, imagen_path, audio_path, out_path)
    print(f"Video generado: {out_path}")


if __name__ == "__main__":
    main()
