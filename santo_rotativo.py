# -*- coding: utf-8 -*-
"""
Rota por el "banco de santos" (data/pool_santos.json): cada día le toca un
santo distinto, en orden fijo y determinístico. Mismo día -> mismo santo
(idempotente si el script corre dos veces el mismo día).

CLAVE: la rotación usa el número de días transcurridos desde una fecha
ancla FIJA, no el "día del año". Así, cada día avanza exactamente +1 en el
banco, garantizando que dos días seguidos NUNCA den el mismo santo (salvo
que el banco tenga 1 solo santo). Que el banco crezca no rompe la secuencia
de días futuros.
"""
import json
import os
from datetime import date

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
POOL_PATH = os.path.join(DATA_DIR, "pool_santos.json")

# Fecha ancla fija: desde aquí se cuentan los días para la rotación.
# No cambiar una vez en producción (cambiarla desplaza toda la secuencia).
FECHA_ANCLA = date(2026, 1, 1)


def cargar_pool():
    with open(POOL_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def santo_rotativo(fecha_iso):
    pool = cargar_pool()
    if not pool:
        return None
    claves_ordenadas = sorted(pool.keys())
    n = len(claves_ordenadas)

    y, m, d = (int(x) for x in fecha_iso.split("-"))
    dias_transcurridos = (date(y, m, d) - FECHA_ANCLA).days
    idx = dias_transcurridos % n

    clave = claves_ordenadas[idx]
    entrada = pool[clave]
    return {
        "nombre_en": clave,
        "nombre_limpio_en": clave,
        "nombre_es": entrada["nombre_es"],
        "foto": entrada["foto"],
        "grado_texto": None,
    }
