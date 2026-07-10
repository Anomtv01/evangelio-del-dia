# -*- coding: utf-8 -*-
"""
Toma el JSON de salmo_del_dia.py y arma el thumbnail, la narración
(ElevenLabs, voz rotativa) y el video final, reutilizando las mismas
funciones que el Santo del Día (santo_utils.py).

Uso:
    python generar_video_salmo.py output_salmo/salmo_2026-08-11.json
"""

import json
import os
import sys

from santo_utils import crear_thumbnail, generar_audio, crear_video

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output_salmo")
# Las ilustraciones de salmos están directamente en assets/ (salmo_N.png).
CARPETA_ILUSTRACIONES = os.path.join(BASE_DIR, "assets")
# Respaldo por si un salmo no tuviera ilustración generada aún:
CARPETA_FOTOS_SALMOS = os.path.join(BASE_DIR, "fotos_salmos")

DOXOLOGIA = (
    "Gloria al Padre, al Hijo y al Espíritu Santo. "
    "Como era en el principio, ahora y siempre, por los siglos de los siglos. Amén."
)
RECORDATORIO = (
    "Si este salmo te bendijo, suscribite al canal Viva la Fe Católica TV "
    "y activá la campanita, para orar juntos cada día."
)


def construir_guion(data):
    partes = [
        f"Salmo {data['num_catolico']}.",
        data.get("texto_salmo", ""),
        data.get("reflexion", ""),
        RECORDATORIO,
        DOXOLOGIA,
    ]
    return " ".join(p for p in partes if p)


def buscar_ilustracion(num_cat):
    """Busca la ilustración del salmo. Primero en assets/ilustraciones_salmos/,
    después en fotos_salmos/. Devuelve la ruta o None."""
    candidatos = [
        os.path.join(CARPETA_ILUSTRACIONES, f"salmo_{num_cat}.png"),
        os.path.join(CARPETA_FOTOS_SALMOS, f"salmo_{num_cat}.png"),
        os.path.join(CARPETA_FOTOS_SALMOS, f"salmo_{num_cat}.jpg"),
    ]
    for c in candidatos:
        if os.path.exists(c):
            return c
    return None


def main():
    if len(sys.argv) < 2:
        print("Uso: python generar_video_salmo.py output_salmo/salmo_<fecha>.json")
        sys.exit(1)

    json_path = sys.argv[1]
    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)

    api_key = os.environ.get("ELEVENLABS_API_KEY")
    if not api_key:
        print("[ERROR] Falta la variable de entorno ELEVENLABS_API_KEY.")
        sys.exit(1)

    carpeta = os.path.join(OUTPUT_DIR, data["fecha"])
    os.makedirs(carpeta, exist_ok=True)

    num_cat = data["num_catolico"]
    foto_path = buscar_ilustracion(num_cat)
    if foto_path:
        print(f"Ilustración encontrada: {foto_path}")
    else:
        print(f"[AVISO] No se encontró ilustración para el Salmo {num_cat}, "
              f"se usa fondo genérico.")

    titulo_grande = f"Salmo {num_cat}"

    print("Creando thumbnail...")
    thumbnail = crear_thumbnail(
        titulo_grande, carpeta,
        subtitulo=data.get("subtitulo", ""),
        gancho=data.get("gancho", ""),
        foto_path=foto_path,
    )

    print("Generando audio con ElevenLabs...")
    guion = construir_guion(data)
    audio, voice_id = generar_audio(guion, carpeta, data["fecha"], api_key)
    print(f"Narración generada con voz: {voice_id}")

    print("Creando video MP4...")
    video = crear_video(thumbnail, audio, carpeta, f"salmo_{data['fecha']}")
    print(f"Video generado: {video}")

    data["_thumbnail_path"] = thumbnail
    data["_video_path"] = video
    data["_voice_id"] = voice_id
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
