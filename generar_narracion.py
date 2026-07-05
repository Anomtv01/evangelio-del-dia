# -*- coding: utf-8 -*-
"""
Genera la narración en audio (MP3) del Evangelio del Día, usando la API de
ElevenLabs. Narra el Evangelio completo + la reflexión (si existe), con una
voz distinta rotando por día (ver voces.py).

Requiere la variable de entorno:
    ELEVENLABS_API_KEY

Uso:
    python generar_narracion.py output/evangelio_2026-07-05.json [reflexion.txt]

Salida: output/narracion_<fecha>.mp3
"""

import json
import os
import sys

import requests

from voces import voz_del_dia, nombre_voz

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

ELEVENLABS_URL = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"

# Mismos rangos que ya usás en santo.py (Stability 60-65, Similarity 75-85,
# Style 25-30, Speaker Boost ON)
VOICE_SETTINGS = {
    "stability": 0.62,
    "similarity_boost": 0.80,
    "style": 0.27,
    "use_speaker_boost": True,
}
MODEL_ID = "eleven_multilingual_v2"


RECORDATORIO_SUSCRIPCION = (
    "Si esta palabra te hizo bien, suscribite al canal Viva la Fe Católica TV "
    "y activá la campanita, para que no te pierdas el Evangelio de cada día."
)

DOXOLOGIA = (
    "Gloria al Padre, al Hijo y al Espíritu Santo. "
    "Como era en el principio, ahora y siempre, por los siglos de los siglos. Amén."
)


def construir_guion(data, reflexion_texto=None):
    partes = []
    partes.append("Evangelio del día.")
    partes.append(f"Lectura del Santo Evangelio según San {data['libro']}.")
    partes.append(data["texto_evangelio"])
    partes.append("Palabra del Señor.")
    if reflexion_texto:
        partes.append(reflexion_texto)
    partes.append(RECORDATORIO_SUSCRIPCION)
    partes.append(DOXOLOGIA)
    return " ".join(partes)


def generar_narracion(data, reflexion_texto=None):
    api_key = os.environ.get("ELEVENLABS_API_KEY")
    if not api_key:
        raise RuntimeError(
            "No se encontró la variable de entorno ELEVENLABS_API_KEY. "
            "Configurala igual que hiciste con ANTHROPIC_API_KEY."
        )

    voice_id = voz_del_dia(data["fecha"])
    guion = construir_guion(data, reflexion_texto)

    url = ELEVENLABS_URL.format(voice_id=voice_id)
    headers = {
        "xi-api-key": api_key,
        "Content-Type": "application/json",
        "Accept": "audio/mpeg",
    }
    payload = {
        "text": guion,
        "model_id": MODEL_ID,
        "voice_settings": VOICE_SETTINGS,
    }

    resp = requests.post(url, headers=headers, json=payload, timeout=120)
    if resp.status_code != 200:
        raise RuntimeError(
            f"ElevenLabs devolvió error {resp.status_code}: {resp.text[:300]}"
        )

    return resp.content, voice_id


def main():
    if len(sys.argv) < 2:
        print("Uso: python generar_narracion.py output/evangelio_<fecha>.json [reflexion.txt]")
        sys.exit(1)

    json_path = sys.argv[1]
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    reflexion_texto = None
    if len(sys.argv) > 2 and os.path.exists(sys.argv[2]):
        with open(sys.argv[2], "r", encoding="utf-8") as f:
            reflexion_texto = f.read().strip()

    try:
        audio_bytes, voice_id = generar_narracion(data, reflexion_texto)
    except RuntimeError as e:
        print(f"[ERROR] {e}")
        sys.exit(1)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_path = os.path.join(OUTPUT_DIR, f"narracion_{data['fecha']}.mp3")
    with open(out_path, "wb") as f:
        f.write(audio_bytes)

    print(f"Narración generada con {nombre_voz(voice_id)} (ID: {voice_id})")
    print(f"Guardado en: {out_path}")


if __name__ == "__main__":
    main()
