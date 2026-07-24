# -*- coding: utf-8 -*-
"""
Toma el JSON de milagro_del_dia.py y arma miniatura, narracion (edge-tts,
gratis, con voces alternadas) y video HORIZONTAL 1920x1080, reutilizando
santo_utils.py.

IMAGENES: busca en data/imagenes_milagros/<clave>.jpg (los paneles de la
exposicion que descargues). Si no hay, usa fondo generico. Como el credito de
la exposicion es obligatorio, se deja anotado en el JSON para que
generar_metadata_milagro.py lo incluya en la descripcion.

Uso:
    python generar_video_milagro.py output_milagro/milagro_2026-08-06.json
"""

import json
import os
import subprocess
import sys

from santo_utils import crear_thumbnail, generar_audio, crear_video

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output_milagro")
IMG_DIR = os.path.join(BASE_DIR, "data", "imagenes_milagros")

MINUTOS_MINIMOS = 8.0

DOXOLOGIA = ("Gloria al Padre, al Hijo y al Espiritu Santo. Como era en el "
             "principio, ahora y siempre, por los siglos de los siglos. Amen.")
RECORDATORIO = ("Hoy es Jueves Eucaristico, dia de la Adoracion al Santisimo. "
                "Si este testimonio fortalecio tu fe, suscribite a Viva la Fe "
                "Catolica TV y activa la campanita.")


def construir_guion(data):
    voz_nar = data.get("voz_narracion", "narrador")
    segmentos = data.get("segmentos")
    if segmentos:
        pares = [(voz_nar, data["titulo_milagro"] + ".")]
        for s in segmentos:
            pares.append((s.get("voz", voz_nar), s["texto"]))
        pares.append((voz_nar, RECORDATORIO))
        pares.append((voz_nar, DOXOLOGIA))
        return pares
    partes = [data["titulo_milagro"] + ".", data.get("biografia", ""),
              RECORDATORIO, DOXOLOGIA]
    return " ".join(p for p in partes if p)


def buscar_imagen(clave):
    for ext in (".jpg", ".jpeg", ".png"):
        ruta = os.path.join(IMG_DIR, clave + ext)
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
        print("Uso: python generar_video_milagro.py output_milagro/milagro_<fecha>.json")
        sys.exit(1)

    with open(sys.argv[1], encoding="utf-8") as f:
        data = json.load(f)

    carpeta = os.path.join(OUTPUT_DIR, data["fecha"])
    os.makedirs(carpeta, exist_ok=True)

    foto = buscar_imagen(data["clave"])
    print("Imagen: %s" % foto if foto else
          "[AVISO] Sin imagen para '%s'; se usa fondo generico. "
          "Descarga el panel a data/imagenes_milagros/%s.jpg"
          % (data["titulo_milagro"], data["clave"]))

    # Titulo de la miniatura: el nombre del lugar destaca mas que "Milagro de..."
    titulo_thumb = data["titulo_milagro"].replace("Milagro Eucarístico de ", "")

    print("Creando miniatura (1280x720) y fondo de video (1920x1080)...")
    thumbnail = crear_thumbnail(
        titulo_thumb, carpeta,
        subtitulo=data.get("subtitulo", ""),
        gancho=data.get("gancho", ""),
        foto_path=foto)

    guion = construir_guion(data)
    if isinstance(guion, list):
        print("Generando audio con voces alternadas (%d intervenciones)..." % len(guion))
    else:
        print("Generando audio (una sola voz)...")
    audio, voces = generar_audio(guion, carpeta, data["fecha"],
                                 perfil=data.get("voz_narracion", "narrador"))
    print("Narracion generada. Voces: %s" % voces)

    dur = duracion_min(audio)
    if dur:
        print("Duracion del audio: %d:%02d min" % (int(dur), int((dur - int(dur)) * 60)))
        print("OK: apto para anuncios a mitad de video." if dur >= MINUTOS_MINIMOS
              else "[AVISO] Menos de %s min: sin mid-roll." % MINUTOS_MINIMOS)

    print("Creando video MP4 (1920x1080 horizontal)...")
    video = crear_video(thumbnail, audio, carpeta, "milagro_%s" % data["fecha"])
    print("Video generado: %s" % video)

    data["_thumbnail_path"] = thumbnail
    data["_video_path"] = video
    data["_voice_id"] = voces
    data["_duracion_min"] = round(dur, 2) if dur else None
    data["_apto_midroll"] = bool(dur and dur >= MINUTOS_MINIMOS)
    with open(sys.argv[1], "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
