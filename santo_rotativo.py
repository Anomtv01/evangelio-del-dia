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

NUEVO: además del santo, devuelve la VOZ que narra hoy (rotación de voces
gratuitas de edge-tts). Misma lógica de fecha ancla, así que es igual de
determinística: mismo día -> misma voz.
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

# ---------------------------------------------------------------------------
# ROTACIÓN DE VOCES (edge-tts, gratis)
# ---------------------------------------------------------------------------
# Se intenta importar desde voces_edge para tener una sola fuente de verdad.
# Si voces_edge no está disponible, se usa esta copia de respaldo.
ROTACION_NARRACION_FALLBACK = [
    "narrador",      # es-MX-JorgeNeural   (masculina, seria)
    "narradora",     # es-MX-DaliaNeural   (femenina, neutra)
    "narrador_us",   # es-US-AlonsoNeural  (masculina, español EE.UU.)
    "narradora_us",  # es-US-PalomaNeural  (femenina, español EE.UU.)
]

try:
    from voces_edge import ROTACION_NARRACION, VOCES as _VOCES_EDGE
except Exception:                                                # noqa: BLE001
    ROTACION_NARRACION = ROTACION_NARRACION_FALLBACK
    _VOCES_EDGE = {}


def cargar_pool():
    with open(POOL_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _dias_desde_ancla(fecha_iso=None):
    """Días transcurridos desde la fecha ancla. Acepta 'YYYY-MM-DD' o None."""
    if fecha_iso is None:
        hoy = date.today()
    else:
        y, m, d = (int(x) for x in fecha_iso.split("-"))
        hoy = date(y, m, d)
    return (hoy - FECHA_ANCLA).days


def voz_del_dia(fecha_iso=None):
    """
    Perfil de voz que narra hoy. Rota secuencialmente igual que el santo,
    así que nunca se repite la misma voz dos días seguidos.
    Devuelve p.ej. 'narrador' -> úsalo con voces_edge.generar_voz(...).
    """
    return ROTACION_NARRACION[_dias_desde_ancla(fecha_iso) % len(ROTACION_NARRACION)]


def nombre_voz_real(perfil):
    """Traduce el perfil al nombre real de la voz ('es-MX-JorgeNeural')."""
    return _VOCES_EDGE.get(perfil, perfil)


def santo_rotativo(fecha_iso):
    pool = cargar_pool()
    if not pool:
        return None
    claves_ordenadas = sorted(pool.keys())
    n = len(claves_ordenadas)

    dias_transcurridos = _dias_desde_ancla(fecha_iso)
    idx = dias_transcurridos % n

    clave = claves_ordenadas[idx]
    entrada = pool[clave]

    perfil_voz = voz_del_dia(fecha_iso)

    return {
        "nombre_en": clave,
        "nombre_limpio_en": clave,
        "nombre_es": entrada["nombre_es"],
        "foto": entrada["foto"],
        "grado_texto": None,
        # --- nuevo: voz que narra hoy ---
        "voz": perfil_voz,                       # perfil para voces_edge
        "voz_nombre": nombre_voz_real(perfil_voz),  # nombre real de la voz
    }


# ---------------------------------------------------------------------------
# Prueba rápida:  python santo_rotativo.py
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    from datetime import timedelta

    hoy = date.today()
    print(f"Fecha ancla: {FECHA_ANCLA}\n")
    print(f"{'FECHA':<12} {'SANTO':<32} {'VOZ':<14} VOZ REAL")
    print("-" * 88)
    for i in range(10):
        f = (hoy + timedelta(days=i)).isoformat()
        try:
            s = santo_rotativo(f)
            if s:
                print(f"{f:<12} {s['nombre_es'][:31]:<32} "
                      f"{s['voz']:<14} {s['voz_nombre']}")
            else:
                print(f"{f:<12} (banco vacío)")
        except FileNotFoundError:
            print(f"{f:<12} voz={voz_del_dia(f):<14} "
                  f"({nombre_voz_real(voz_del_dia(f))})  [pool no encontrado]")
