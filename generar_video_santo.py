# -*- coding: utf-8 -*-
"""
Toma el JSON generado por santo_del_dia.py y arma el thumbnail, la
narración (ElevenLabs, voz rotativa) y el video final.

Uso:
    python generar_video_santo.py output_santo/santo_2026-08-11.json
"""

import json
import os
import sys

from santo_utils import crear_thumbnail, generar_audio, crear_video, buscar_foto

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output_santo")

DOXOLOGIA = (
    "Gloria al Padre, al Hijo y al Espíritu Santo. "
    "Como era en el principio, ahora y siempre, por los siglos de los siglos. Amén."
)
RECORDATORIO_SUSCRIPCION = (
    "Si esta historia te bendijo, suscribite al canal Viva la Fe Católica TV "
    "y activá la campanita, para no perderte las historias de cada día."
)


def construir_guion(data):
    partes = [
        f"{data['nombre_es']}.",
        data["biografia"],
        RECORDATORIO_SUSCRIPCION,
        DOXOLOGIA,
    ]
    return " ".join(partes)


def main():
    if len(sys.argv) < 2:
        print("Uso: python generar_video_santo.py output_santo/santo_<fecha>.json")
        sys.exit(1)

    json_path = sys.argv[1]
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    api_key = os.environ.get("ELEVENLABS_API_KEY")
    if not api_key:
        print("[ERROR] Falta la variable de entorno ELEVENLABS_API_KEY.")
        sys.exit(1)

    carpeta = os.path.join(OUTPUT_DIR, data["fecha"])
    os.makedirs(carpeta, exist_ok=True)

    fotos_dir_local = os.path.join(BASE_DIR, "fotos")
    foto_path = None
    if data.get("foto"):
        candidato_local = os.path.join(fotos_dir_local, data["foto"])
        candidato_win = os.path.join("C:\\VivaLaFe\\fotos", data["foto"])
        if os.path.exists(candidato_local):
            foto_path = candidato_local
        elif os.path.exists(candidato_win):
            foto_path = candidato_win

    if not foto_path:
        foto_path = buscar_foto(data["nombre_limpio_en"])

    if foto_path:
        print(f"Foto encontrada: {foto_path}")
    else:
        print(f"[AVISO] No se encontró foto para '{data['nombre_es']}', "
              f"se usa fondo genérico.")

    print("Creando thumbnail...")
    thumbnail = crear_thumbnail(
        data["nombre_es"], carpeta,
        subtitulo=data.get("subtitulo", ""),
        gancho=data.get("gancho", ""),
        foto_path=foto_path,
    )

    print("Generando audio con ElevenLabs...")
    guion = construir_guion(data)
    audio, voice_id = generar_audio(guion, carpeta, data["fecha"], api_key)
    print(f"Narración generada con voz: {voice_id}")

    print("Creando video MP4...")
    video = crear_video(thumbnail, audio, carpeta, f"santo_{data['fecha']}")

    print(f"Video generado: {video}")

    # Guardamos las rutas en el mismo JSON, para el paso de subida
    data["_thumbnail_path"] = thumbnail
    data["_video_path"] = video
    data["_voice_id"] = voice_id
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
