# -*- coding: utf-8 -*-
"""
Sistema de paletas de color rotativas para los thumbnails del Evangelio del
Día, en el mismo espíritu del sistema de 37 paletas de santo.py: cada día
usa una paleta distinta (elegida de forma determinística según la fecha,
así el mismo día siempre da la misma paleta, pero se ve variado a lo largo
de la semana/mes).

Si más adelante querés sincronizar esto exactamente con las paletas de
santo.py, pasame ese archivo de colores y las reemplazo acá by una lista
idéntica.
"""

import hashlib

# Cada paleta: (nombre, color_acento, color_acento_claro, tinte_fondo_extra)
# tinte_fondo_extra se usa para variar levemente el degradado de fondo.
PALETAS = [
    ("Oro clásico",     (212, 175, 55),  (245, 222, 150), (22, 16, 10)),
    ("Bronce cálido",   (184, 115, 51),  (230, 170, 120), (20, 12, 8)),
    ("Rojo sangre",     (167, 35, 35),   (224, 120, 100), (18, 8, 8)),
    ("Plata celestial", (176, 184, 196), (230, 235, 240), (10, 12, 16)),
    ("Púrpura real",    (117, 58, 136),  (200, 160, 220), (14, 8, 18)),
    ("Verde esperanza", (74, 124, 89),   (170, 210, 160), (8, 14, 10)),
    ("Ámbar dorado",    (222, 158, 54),  (250, 210, 140), (20, 14, 6)),
    ("Azul noche",      (74, 98, 156),   (160, 180, 220), (8, 10, 18)),
    ("Rosa amanecer",   (196, 120, 110), (235, 190, 175), (16, 10, 10)),
    ("Cobre antiguo",   (169, 113, 66),  (220, 175, 130), (16, 11, 7)),
    ("Esmeralda",       (58, 122, 106),  (150, 210, 190), (7, 14, 12)),
    ("Marfil dorado",   (200, 178, 115), (240, 230, 200), (18, 16, 10)),
]


def paleta_del_dia(fecha_iso):
    """Elige una paleta de forma determinística según la fecha (mismo día
    siempre da la misma paleta)."""
    hash_val = int(hashlib.md5(fecha_iso.encode()).hexdigest(), 16)
    idx = hash_val % len(PALETAS)
    return PALETAS[idx]
