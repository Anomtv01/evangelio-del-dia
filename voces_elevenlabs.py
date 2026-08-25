# -*- coding: utf-8 -*-
"""
voces_elevenlabs.py — Motor de voz ElevenLabs (PAGO) para el Short diario
del Evangelio — Viva la Fe Catolica TV
============================================================================
Usa la API REST de ElevenLabs directamente (sin SDK) porque este modulo
corre en GitHub Actions, un entorno headless sin sesion de navegador.

Requiere la variable de entorno ELEVENLABS_API_KEY (configurada como
secreto del repo en GitHub Actions).

Misma interfaz publica que voces_edge.py (generar_voz, generar_dialogo,
VOCES) para poder enchufarlo en generar_video_corto.py sin tocar el resto
del pipeline. IMPORTANTE: este motor de voz se usa SOLO para el Short
diario del Evangelio (corto_rotativo / guion_corto / generar_video_corto).
El resto de las series (santo_del_dia, milagro_del_dia, salmo_del_dia)
siguen usando voces_edge.py (gratis) — no se tocaron.

    generar_voz("texto...", "salida.mp3", "narrador")

    guion = [("narrador", "..."), ("jesus", "...")]
    generar_dialogo(guion, "audio.mp3", pausa=0.7)
"""

import os
import time

import requests

# Reutilizamos el ensamblado con ffmpeg (concatenar + silencios) de
# voces_edge.py: es generico, no depende de edge-tts.
from voces_edge import _silencio, _unir

API_URL = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"

# eleven_multilingual_v2 = mejor prosodia en espanol (recomendado para
# contenido publico). eleven_turbo_v2_5 = la mitad de creditos, calidad
# algo menor. Se puede cambiar sin tocar codigo con la variable de entorno
# ELEVENLABS_MODEL.
MODELO = os.environ.get("ELEVENLABS_MODEL", "eleven_multilingual_v2")

# ---------------------------------------------------------------------------
# CATALOGO DE VOCES (voice_id de la libreria de voces de ElevenLabs,
# elegidas en espanol para que combinen con el tono del canal)
# ---------------------------------------------------------------------------
VOCES = {
    # --- Narracion (misma rotacion por dia que voces_edge.ROTACION_NARRACION) ---
    "narrador":     "NNyuU2PGU4uwmrHysPYW",   # SANDMOR | Latin Spanish Narrator (M)
    "narradora":    "Bh4tkGuEEIADxUACafG5",   # Lucy | Warm Latin Spanish Female
    "narrador_us":  "sNINh5RgHLFf8rFhu1bI",   # Jaime | Mexican Spanish Narrator (M)
    "narradora_us": "34EkeMY6ezBFj41NQj1f",   # Nelly | Warm Peruvian Spanish Voice

    # --- Personajes del Short (guion_corto.py: VOCES_PERSONAJE) ---
    "jesus":   "hyKxCTlAqtnW188CgltM",        # Salva | grave, calida, con autoridad
    "testigo": "1CeqBeXMOqCleeQjfYfO",        # Cristina | femenina, expresiva
}

# stability/similarity_boost por perfil (equivalente a rate/pitch de edge-tts).
# Menos "stability" = mas expresivo; mas "stability" = mas parejo/solemne.
AJUSTES = {
    "narrador":     {"stability": 0.55, "similarity_boost": 0.8},
    "narradora":    {"stability": 0.55, "similarity_boost": 0.8},
    "narrador_us":  {"stability": 0.55, "similarity_boost": 0.8},
    "narradora_us": {"stability": 0.55, "similarity_boost": 0.8},
    "jesus":        {"stability": 0.65, "similarity_boost": 0.85, "style": 0.35},
    "testigo":      {"stability": 0.45, "similarity_boost": 0.8,  "style": 0.4},
}

REINTENTOS = 3
ESPERA = 4


def _api_key():
    key = os.environ.get("ELEVENLABS_API_KEY")
    if not key:
        raise RuntimeError(
            "Falta la variable de entorno ELEVENLABS_API_KEY "
            "(configurala como secreto del repo en GitHub Actions).")
    return key


def generar_voz(texto, salida, perfil="narrador"):
    """Genera un MP3 con la voz de ElevenLabs correspondiente a 'perfil'."""
    if not texto or not texto.strip():
        raise ValueError("El texto esta vacio.")

    voice_id = VOCES.get(perfil)
    if voice_id is None:
        print("   [aviso] Perfil de voz '%s' desconocido en ElevenLabs; "
              "se usa 'narrador'." % perfil)
        voice_id = VOCES["narrador"]
        perfil = "narrador"

    carpeta = os.path.dirname(os.path.abspath(salida))
    if carpeta:
        os.makedirs(carpeta, exist_ok=True)

    body = {
        "text": texto,
        "model_id": MODELO,
        "voice_settings": AJUSTES.get(perfil, {"stability": 0.55, "similarity_boost": 0.8}),
    }
    headers = {
        "xi-api-key": _api_key(),
        "Content-Type": "application/json",
        "Accept": "audio/mpeg",
    }

    ultimo = None
    for intento in range(1, REINTENTOS + 1):
        try:
            resp = requests.post(
                API_URL.format(voice_id=voice_id), json=body, headers=headers,
                timeout=120)
            if resp.status_code != 200:
                raise RuntimeError(
                    "ElevenLabs devolvio %d: %s" % (resp.status_code, resp.text[:300]))
            with open(salida, "wb") as f:
                f.write(resp.content)
            if os.path.getsize(salida) < 1024:
                raise RuntimeError("Audio vacio o corrupto.")
            return salida
        except Exception as e:                                      # noqa: BLE001
            ultimo = e
            print("   [intento %d/%d] %s" % (intento, REINTENTOS, e))
            if intento < REINTENTOS:
                time.sleep(ESPERA)
    raise RuntimeError("No se pudo generar '%s': %s" % (salida, ultimo))


def generar_dialogo(guion, salida, pausa=0.7):
    """
    Varias voces alternadas en un solo MP3 (mismo formato que
    voces_edge.generar_dialogo): guion = [(perfil, texto), ...]
    """
    import shutil
    import tempfile

    tmp = tempfile.mkdtemp(prefix="dialogo_11_")
    try:
        partes = []
        print("  Generando %d intervenciones con ElevenLabs..." % len(guion))
        for i, (perfil, texto) in enumerate(guion):
            a = os.path.join(tmp, "p%03d.mp3" % i)
            generar_voz(texto, a, perfil)
            partes.append(a)

        if pausa > 0:
            sil = os.path.join(tmp, "sil.mp3")
            _silencio(sil, pausa)
            inter = []
            for i, p in enumerate(partes):
                inter.append(p)
                if i < len(partes) - 1:
                    inter.append(sil)
            partes = inter

        _unir(partes, salida)
        print("  -> %s" % salida)
        return salida
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
