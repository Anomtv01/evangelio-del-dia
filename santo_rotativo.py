# -*- coding: utf-8 -*-
"""
En vez de buscar el santo litúrgico EXACTO de una fecha (que es donde
veníamos trabando por falta de fotos verificadas para cada día puntual),
este módulo rota por el "banco de santos" que ya armamos con
descargar_fotos_wikitolica.py (data/pool_santos.json) -- cada día del año
le toca un santo distinto del banco, en un orden fijo y determinístico
(mismo día siempre da el mismo santo, para que no se repita si corrés el
script dos veces el mismo día).

Cuando el banco crezca (agregás más meses/santos), la rotación se
reparte mejor sola; no hace falta tocar nada.
"""

import json
import os
from datetime import date

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
POOL_PATH = os.path.join(DATA_DIR, "pool_santos.json")


def cargar_pool():
    with open(POOL_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def santo_rotativo(fecha_iso):
    """Devuelve {"nombre_en": ..., "nombre_es": ..., "nombre_limpio_en": ...,
    "foto": ...} para el santo que le toca a esta fecha, rotando por el
    banco disponible. Nunca devuelve None si el banco tiene al menos 1
    santo (a diferencia del enfoque litúrgico anterior)."""
    pool = cargar_pool()
    if not pool:
        return None

    claves_ordenadas = sorted(pool.keys())
    y, m, d = (int(x) for x in fecha_iso.split("-"))
    dia_del_anio = date(y, m, d).timetuple().tm_yday

    idx = dia_del_anio % len(claves_ordenadas)
    clave = claves_ordenadas[idx]
    entrada = pool[clave]

    return {
        "nombre_en": clave,
        "nombre_limpio_en": clave,
        "nombre_es": entrada["nombre_es"],
        "foto": entrada["foto"],
        "grado_texto": None,
    }
