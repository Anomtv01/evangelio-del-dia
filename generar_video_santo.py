# -*- coding: utf-8 -*-
"""
Toma el JSON de santo_del_dia.py y arma la miniatura, la narracion
(edge-tts, GRATIS, con voces alternadas) y el video HORIZONTAL 1920x1080.

CAMBIOS:
  - Ya no requiere ELEVENLABS_API_KEY.
  - Si el JSON trae "segmentos", genera el audio con voces alternadas
    (narrador + el santo en primera persona). Si no, usa el texto plano
    de "biografia" con una sola voz (compatibilidad hacia atras).
  - El video sale horizontal, apto para mid-roll.

Uso:
    python generar_video_santo.py output_santo/santo_2026-08-11.json
"""

import json
import os
import subprocess
import sys

from santo_utils import crear_thumbnail, generar_audio, crear_video, buscar_foto

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output_santo")

MINUTOS_MINIMOS = 8.0   # umbral de YouTube para anuncios a mitad (mid-roll)

DOXOLOGIA = (
    "Gloria al Padre, al Hijo y al Espiritu Santo. "
    "Como era en el principio, ahora y siempre, por los siglos de los siglos. Amen."
)
RECORDATORIO_SUSCRIPCION = (
    "Si esta historia te bendijo, suscribite al canal Viva la Fe Catolica TV "
    "y activa la campanita, para no perderte las historias de cada dia."
)


def construir_guion(data):
    """
    Devuelve una LISTA de (perfil_voz, texto) si hay segmentos,
    o un string si solo hay biografia (formato antiguo).
    """
    voz_nar = data.get("voz_narracion", "narrador")
    segmentos = data.get("segmentos")

    if segmentos:
        pares = [(voz_nar, f"{data['nombre_es']}.")]
        for s in segmentos:
            pares.append((s.get("voz", voz_nar), s["texto"]))
        pares.append((voz_nar, RECORDATORIO_SUSCRIPCION))
        pares.append((voz_nar, DOXOLOGIA))
        return pares

    partes = [f"{data['nombre_es']}.", data["biografia"],
              RECORDATORIO_SUSCRIPCION, DOXOLOGIA]
    return " ".join(partes)


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
        print("Uso: python generar_video_santo.py output_santo/santo_<fecha>.json")
        sys.exit(1)

    json_path = sys.argv[1]
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    carpeta = os.path.join(OUTPUT_DIR, data["fecha"])
    os.makedirs(carpeta, exist_ok=True)

    # --- Foto ---
    fotos_dir_local = os.path.join(BASE_DIR, "fotos")
    foto_path = None
    if data.get("foto"):
        cand_local = os.path.join(fotos_dir_local, data["foto"])
        cand_win = os.path.join("C:\\VivaLaFe\\fotos", data["foto"])
        if os.path.exists(cand_local):
            foto_path = cand_local
        elif os.path.exists(cand_win):
            foto_path = cand_win
    if not foto_path:
        foto_path = buscar_foto(data["nombre_limpio_en"])

    print(f"Foto: {foto_path}" if foto_path
          else f"[AVISO] Sin foto para '{data['nombre_es']}', se usa fondo generico.")

    # --- Miniatura horizontal 16:9 ---
    print("Creando miniatura (1280x720) y fondo de video (1920x1080)...")
    thumbnail = crear_thumbnail(
        data["nombre_es"], carpeta,
        subtitulo=data.get("subtitulo", ""),
        gancho=data.get("gancho", ""),
        foto_path=foto_path)

    # --- Audio con edge-tts (gratis) ---
    guion = construir_guion(data)
    if isinstance(guion, list):
        print(f"Generando audio con voces alternadas ({len(guion)} intervenciones)...")
    else:
        print("Generando audio (una sola voz, formato antiguo)...")
    audio, voces = generar_audio(guion, carpeta, data["fecha"],
                                 perfil=data.get("voz_narracion", "narrador"))
    print(f"Narracion generada. Voces: {voces}")

    dur = duracion_min(audio)
    if dur:
        print(f"Duracion del audio: {int(dur)}:{int((dur - int(dur)) * 60):02d} min")
        if dur < MINUTOS_MINIMOS:
            print(f"[AVISO] Menos de {MINUTOS_MINIMOS} min: este video NO podra "
                  f"llevar anuncios a mitad (mid-roll). Sube MINUTOS_OBJETIVO "
                  f"en santo_del_dia.py.")
        else:
            print("OK: apto para anuncios a mitad de video.")

    # --- Video horizontal ---
    print("Creando video MP4 (1920x1080 horizontal)...")
    video = crear_video(thumbnail, audio, carpeta, f"santo_{data['fecha']}")
    print(f"Video generado: {video}")

    data["_thumbnail_path"] = thumbnail
    data["_video_path"] = video
    data["_voice_id"] = voces
    data["_duracion_min"] = round(dur, 2) if dur else None
    data["_apto_midroll"] = bool(dur and dur >= MINUTOS_MINIMOS)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
