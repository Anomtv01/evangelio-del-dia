# -*- coding: utf-8 -*-
"""
Toma el JSON de guion_corto.py y arma la portada VERTICAL (rayos dorados y
cruz radiante, ver portada_corto.py), la narración (ElevenLabs, con la voz
de Jesús o del personaje cuando corresponde) y el video VERTICAL 1080x1920
(formato Short), reutilizando crear_video_vertical de santo_utils.py.

Uso:
    python generar_video_corto.py output_corto/corto_2026-08-25.json
"""

import json
import os
import subprocess
import sys

from portada_corto import crear_portada_corto
from santo_utils import crear_video_vertical
import voces_elevenlabs

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output_corto")

RECORDATORIO = ("Si esta historia te tocó el corazón, suscribite a Viva la "
                "Fe Católica TV y activa la campanita para no perderte el "
                "Evangelio de cada día.")


def construir_guion(data):
    voz_nar = data.get("voz_narracion", "narrador")
    segmentos = data["segmentos"]
    pares = []
    for s in segmentos:
        voz = s.get("voz", "NARRACION")
        perfil = voz_nar if voz == "NARRACION" else voz
        pares.append((perfil, s["texto"]))
    pares.append((voz_nar, RECORDATORIO))
    return pares


def generar_audio(guion, carpeta, fecha_iso, perfil="narrador"):
    """
    Narracion con ElevenLabs (voz paga) para el Short diario del Evangelio.
    Misma firma que santo_utils.generar_audio para no tocar el resto del
    pipeline. 'guion' es una lista de (perfil, texto).
    """
    os.makedirs(carpeta, exist_ok=True)
    path = os.path.join(carpeta, "audio.mp3")
    voces_elevenlabs.generar_dialogo(list(guion), path, pausa=0.7)
    usadas = sorted({p for p, _ in guion})
    return path, "+".join(usadas)


def duracion_min(ruta):
    try:
        out = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=nw=1:nk=1", ruta],
            capture_output=True, text=True, check=True).stdout.strip()
        return float(out) / 60.0
    except Exception:                                            # noqa: BLE001
        return None


def main():
    if len(sys.argv) < 2:
        print("Uso: python generar_video_corto.py output_corto/corto_<fecha>.json")
        sys.exit(1)

    with open(sys.argv[1], encoding="utf-8") as f:
        data = json.load(f)

    carpeta = os.path.join(OUTPUT_DIR, data["fecha"])
    os.makedirs(carpeta, exist_ok=True)

    print("Creando portada vertical (1080x1920, rayos dorados + cruz)...")
    thumbnail = crear_portada_corto(
        cita_es=data.get("cita_es", ""),
        fiesta_liturgica=data.get("fiesta_liturgica", ""),
        gancho_pantalla=data.get("gancho_pantalla", ""),
        subtitulo=data.get("subtitulo", ""),
        carpeta=carpeta,
        fecha_iso=data["fecha"])

    guion = construir_guion(data)
    print("Generando audio con ElevenLabs (%d intervenciones)..." % len(guion))
    audio, voces = generar_audio(guion, carpeta, data["fecha"],
                                 perfil=data.get("voz_narracion", "narrador"))
    print("Narración generada. Voces: %s" % voces)

    dur = duracion_min(audio)
    if dur:
        print("Duración del audio: %d:%02d min" % (int(dur), int((dur - int(dur)) * 60)))
        if dur > 3.0:
            print("[AVISO] Más de 3 minutos: YouTube ya no lo clasificaría como Short.")

    print("Creando video MP4 (1080x1920 vertical)...")
    video = crear_video_vertical(thumbnail, audio, carpeta,
                                 "corto_%s" % data["fecha"])
    print("Video generado: %s" % video)

    data["_thumbnail_path"] = thumbnail
    data["_video_path"] = video
    data["_voice_id"] = voces
    data["_duracion_min"] = round(dur, 2) if dur else None
    with open(sys.argv[1], "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
