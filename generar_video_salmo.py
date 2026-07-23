# -*- coding: utf-8 -*-
"""
Toma el JSON de salmo_del_dia.py y arma la miniatura, la narracion
(edge-tts, GRATIS, con voces alternadas) y el video HORIZONTAL 1920x1080,
reutilizando las funciones de santo_utils.py.

CAMBIOS:
  - Ya NO requiere ELEVENLABS_API_KEY (antes salia con error si faltaba,
    que era justo lo que impedia que se generara el Salmo).
  - Si el JSON trae "segmentos", usa voces alternadas: una proclama la
    Escritura y otra medita. Si no, usa el texto plano (compatibilidad).
  - Video horizontal, apto para anuncios a mitad (mid-roll).

Uso:
    python generar_video_salmo.py output_salmo/salmo_2026-08-11.json
"""

import json
import os
import subprocess
import sys

from santo_utils import crear_thumbnail, generar_audio, crear_video

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output_salmo")

MINUTOS_MINIMOS = 8.0

CARPETAS_ILUSTRACIONES = [
    os.path.join(BASE_DIR, "assets"),
    BASE_DIR,
    os.path.join(BASE_DIR, "assets", "ilustraciones_salmos"),
    os.path.join(BASE_DIR, "fotos_salmos"),
]

DOXOLOGIA = (
    "Gloria al Padre, al Hijo y al Espiritu Santo. "
    "Como era en el principio, ahora y siempre, por los siglos de los siglos. Amen."
)
RECORDATORIO = (
    "Si este salmo te bendijo, suscribite al canal Viva la Fe Catolica TV "
    "y activa la campanita, para orar juntos cada dia."
)


def construir_guion(data):
    """Lista de (perfil_voz, texto) si hay segmentos; si no, texto plano."""
    voz_med = data.get("voz_meditacion", "narrador")
    segmentos = data.get("segmentos")

    if segmentos:
        pares = [(voz_med, "Salmo %s." % data["num_catolico"])]
        for s in segmentos:
            pares.append((s.get("voz", voz_med), s["texto"]))
        pares.append((voz_med, RECORDATORIO))
        pares.append((voz_med, DOXOLOGIA))
        return pares

    partes = ["Salmo %s." % data["num_catolico"],
              data.get("texto_salmo", ""), data.get("reflexion", ""),
              RECORDATORIO, DOXOLOGIA]
    return " ".join(p for p in partes if p)


def buscar_ilustracion(num_cat):
    for carpeta in CARPETAS_ILUSTRACIONES:
        for ext in (".png", ".jpg"):
            ruta = os.path.join(carpeta, "salmo_%s%s" % (num_cat, ext))
            if os.path.exists(ruta):
                return ruta
    return None


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
        print("Uso: python generar_video_salmo.py output_salmo/salmo_<fecha>.json")
        sys.exit(1)

    json_path = sys.argv[1]
    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)

    carpeta = os.path.join(OUTPUT_DIR, data["fecha"])
    os.makedirs(carpeta, exist_ok=True)

    num_cat = data["num_catolico"]
    foto_path = buscar_ilustracion(num_cat)
    if foto_path:
        print("Ilustracion encontrada: %s" % foto_path)
    else:
        print("[AVISO] Sin ilustracion para el Salmo %s, se usa fondo generico."
              % num_cat)

    print("Creando miniatura (1280x720) y fondo de video (1920x1080)...")
    thumbnail = crear_thumbnail(
        "Salmo %s" % num_cat, carpeta,
        subtitulo=data.get("subtitulo", ""),
        gancho=data.get("gancho", ""),
        foto_path=foto_path)

    guion = construir_guion(data)
    if isinstance(guion, list):
        print("Generando audio con voces alternadas (%d intervenciones)..."
              % len(guion))
    else:
        print("Generando audio (una sola voz, formato antiguo)...")
    audio, voces = generar_audio(guion, carpeta, data["fecha"],
                                 perfil=data.get("voz_meditacion", "narrador"))
    print("Narracion generada. Voces: %s" % voces)

    dur = duracion_min(audio)
    if dur:
        print("Duracion del audio: %d:%02d min" % (int(dur), int((dur - int(dur)) * 60)))
        if dur < MINUTOS_MINIMOS:
            print("[AVISO] Menos de %s min: este video NO podra llevar anuncios "
                  "a mitad. Sube MINUTOS_OBJETIVO en salmo_del_dia.py."
                  % MINUTOS_MINIMOS)
        else:
            print("OK: apto para anuncios a mitad de video.")

    print("Creando video MP4 (1920x1080 horizontal)...")
    video = crear_video(thumbnail, audio, carpeta, "salmo_%s" % data["fecha"])
    print("Video generado: %s" % video)

    data["_thumbnail_path"] = thumbnail
    data["_video_path"] = video
    data["_voice_id"] = voces
    data["_duracion_min"] = round(dur, 2) if dur else None
    data["_apto_midroll"] = bool(dur and dur >= MINUTOS_MINIMOS)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
