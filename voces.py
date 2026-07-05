# -*- coding: utf-8 -*-
"""
Sistema de rotación de voces de ElevenLabs para la narración del Evangelio
del Día. Mismo criterio que paletas.py: cada fecha usa una voz distinta,
elegida de forma determinística (mismo día siempre da la misma voz).

Si en algún momento identificás el nombre de cada voz (ElevenLabs -> Voice
Library / My Voices), agregalo en el diccionario NOMBRES para que quede
más prolijo en los logs.
"""

import hashlib

VOICE_IDS = [
    "Nh2zY9kknu6z4pZy6FhD",
    "sKgg4MPUDBy69X7iv3fA",
    "RyfjEHnKbtma4Srae2za",
    "HJAIwgFDzw3Kk9aW7RYr",
    "q2XMPZ6icuVDBj7rgCxQ",
    "7UB6WMKyZDj19XRGC8Sb",
    "x6LHvMgpXmty838MUqHh",
    "hpp4J3VqNfWAUOO0d1Us",
]

# Opcional: nombres reales de cada voz, si los identificás en ElevenLabs.
# Por defecto usamos "Voz 1", "Voz 2", etc.
NOMBRES = {}


def nombre_voz(voice_id):
    idx = VOICE_IDS.index(voice_id) + 1 if voice_id in VOICE_IDS else "?"
    return NOMBRES.get(voice_id, f"Voz {idx}")


def voz_del_dia(fecha_iso):
    """Elige un voice_id de forma determinística según la fecha."""
    hash_val = int(hashlib.md5((fecha_iso + "-voz").encode()).hexdigest(), 16)
    idx = hash_val % len(VOICE_IDS)
    return VOICE_IDS[idx]
