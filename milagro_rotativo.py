# -*- coding: utf-8 -*-
"""
milagro_rotativo.py — Viva la Fe Catolica TV
=============================================
Elige el Milagro Eucaristico de la semana. La serie se publica los JUEVES,
dia dedicado a la Adoracion al Santisimo.

Rotacion por SEMANAS desde una fecha ancla (un jueves), con el mismo criterio
determinista de santo_rotativo.py: misma semana -> mismo milagro.

ORDEN DE APARICION (para enganchar desde el principio):
  1. Primero los DESTACADOS (Lanciano, Bolsena, Santarem, Siena...) y los
     HISPANOS (Espana, Colombia, Peru), que son los que mas conectan.
  2. Luego el resto de milagros.
  3. Al final, los santos eucaristicos (Sagrado Corazon, etc.).

Ademas rota la VOZ del narrador, igual que en el santo.
"""

import json
import os
from datetime import date

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
POOL_PATH = os.path.join(DATA_DIR, "pool_milagros.json")
TEXTOS_PATH = os.path.join(DATA_DIR, "textos_milagros.json")

# Primer JUEVES de emision de la serie. La rotacion arranca AQUI, asi que el
# primer video sera el primero de la lista ordenada (Lanciano y los grandes).
# Ponlo en el jueves en que publicaras el primer milagro. No lo cambies despues.
FECHA_ANCLA = date(2026, 8, 6)   # primer jueves de emision

ROTACION_NARRACION = ["narrador", "narradora", "narrador_us", "narradora_us"]

try:
    from voces_edge import VOCES as _VOCES_EDGE
except Exception:                                                # noqa: BLE001
    _VOCES_EDGE = {}


def cargar_pool():
    with open(POOL_PATH, encoding="utf-8") as f:
        return json.load(f)


def cargar_textos():
    if os.path.exists(TEXTOS_PATH):
        with open(TEXTOS_PATH, encoding="utf-8") as f:
            return json.load(f)
    return {}


def _orden(entrada):
    """Clave de orden: prioridad, luego hispano, luego alfabetico."""
    return (entrada[1].get("prioridad", 2),
            0 if entrada[1].get("hispano") else 1,
            entrada[1].get("titulo", ""))


def _lista_ordenada(pool):
    return [k for k, _ in sorted(pool.items(), key=_orden)]


def _semanas_desde_ancla(fecha=None):
    return ((fecha or date.today()) - FECHA_ANCLA).days // 7


def voz_de_la_semana(fecha=None):
    return ROTACION_NARRACION[_semanas_desde_ancla(fecha) % len(ROTACION_NARRACION)]


def _slug(s):
    import re
    import unicodedata
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")


def buscar_texto_fuente(entrada, textos):
    """Devuelve el texto del PDF para ese milagro, si existe."""
    if not entrada.get("lugar"):
        return None
    ls = _slug(entrada["lugar"])
    for k, v in textos.items():
        ks = _slug(k)
        if ls and (ls in ks or ks in ls):
            return v
    return None


def milagro_de_la_semana(fecha=None):
    pool = cargar_pool()
    if not pool:
        return None
    orden = _lista_ordenada(pool)
    idx = _semanas_desde_ancla(fecha) % len(orden)
    clave = orden[idx]
    entrada = dict(pool[clave])

    textos = cargar_textos()
    texto_fuente = buscar_texto_fuente(entrada, textos)

    perfil = voz_de_la_semana(fecha)
    entrada.update({
        "clave": clave,
        "voz": perfil,
        "voz_nombre": _VOCES_EDGE.get(perfil, perfil),
        "texto_fuente": texto_fuente,
        "tiene_fuente": bool(texto_fuente),
    })
    return entrada


if __name__ == "__main__":
    from datetime import timedelta

    print(f"Fecha ancla (jueves): {FECHA_ANCLA}\n")
    print(f"{'SEMANA':<12} {'MILAGRO':<40} {'PAIS':<12} {'VOZ':<12} FUENTE")
    print("-" * 90)
    base = date.today()
    # Alinear al proximo jueves
    while base.weekday() != 3:
        base += timedelta(days=1)
    for i in range(12):
        f = base + timedelta(weeks=i)
        m = milagro_de_la_semana(f)
        if m:
            print(f"{f.isoformat():<12} {m['titulo'][:39]:<40} "
                  f"{str(m['pais'] or '-'):<12} {m['voz']:<12} "
                  f"{'si' if m['tiene_fuente'] else 'NO'}")
