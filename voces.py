# -*- coding: utf-8 -*-
"""
Sistema de rotación de voces de ElevenLabs.

CAMBIO IMPORTANTE: antes se elegía la voz con un hash MD5 de la fecha, lo
que era determinístico pero ALEATORIO -- con 8 voces, había 1 probabilidad
en 8 de que dos días seguidos usaran la misma voz (y eso pasaba).

Ahora la rotación es SECUENCIAL: cuenta los días desde una fecha ancla fija
y avanza +1 en la lista cada día. Así dos días seguidos NUNCA usan la misma
voz, y sigue siendo determinístico (mismo día -> misma voz).
"""

from datetime import date

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
NOMBRES = {}

# Fecha ancla fija para la rotación (no cambiar en producción).
FECHA_ANCLA = date(2026, 1, 1)


def nombre_voz(voice_id):
    idx = VOICE_IDS.index(voice_id) + 1 if voice_id in VOICE_IDS else "?"
    return NOMBRES.get(voice_id, f"Voz {idx}")


def voz_del_dia(fecha_iso):
    """Elige la voz rotando secuencialmente: cada día avanza +1 en la lista,
    así nunca se repite la voz dos días seguidos."""
    y, m, d = (int(x) for x in fecha_iso.split("-"))
    dias = (date(y, m, d) - FECHA_ANCLA).days
    return VOICE_IDS[dias % len(VOICE_IDS)]
