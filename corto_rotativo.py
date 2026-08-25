# -*- coding: utf-8 -*-
"""
corto_rotativo.py — Viva la Fe Católica TV
============================================
Elige la historia del Evangelio del Short diario. La serie se publica TODOS
LOS DÍAS (a diferencia del Jueves Eucarístico, que es semanal).

Rotación por DÍAS desde una fecha ancla, mismo criterio determinista que
milagro_rotativo.py y santo_rotativo.py: mismo día -> misma historia. El pool
tiene 50 pasajes (los encuentros, milagros y parábolas más conocidos y con
más fuerza narrativa de los cuatro Evangelios), ordenados por prioridad para
arrancar con los más queridos (la samaritana, el hijo pródigo, el buen
samaritano...).

También rota la VOZ del narrador día a día, reutilizando voces_edge.voz_del_dia()
(la misma rotación que usan las otras series).

Extrae el texto EXACTO de la Biblia Platense (data/biblia_platense.json),
igual que evangelio_del_dia.py, para que el guion se apoye siempre en el
texto real y no en la memoria del modelo.
"""

import json
import os
from datetime import date

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
POOL_PATH = os.path.join(DATA_DIR, "pool_historias_evangelio.json")
BIBLIA_PATH = os.path.join(DATA_DIR, "biblia_platense.json")

# Primer día de emisión del Short diario. La rotación arranca AQUÍ.
# No lo cambies después de publicar el primero, o se correrá todo el orden.
FECHA_ANCLA = date(2026, 8, 25)

try:
    from voces_edge import voz_del_dia, VOCES as _VOCES_EDGE
except Exception:                                                # noqa: BLE001
    def voz_del_dia(fecha=None):
        return "narrador"
    _VOCES_EDGE = {}


def cargar_pool():
    with open(POOL_PATH, encoding="utf-8") as f:
        return json.load(f)


def cargar_biblia():
    with open(BIBLIA_PATH, encoding="utf-8") as f:
        data = json.load(f)
    return {libro["name"]: libro for libro in data["books"]}


def _orden(entrada):
    """Clave de orden: prioridad, luego alfabético por título."""
    return (entrada[1].get("prioridad", 2), entrada[1].get("titulo", ""))


def _lista_ordenada(pool):
    return [k for k, _ in sorted(pool.items(), key=_orden)]


def _dias_desde_ancla(fecha=None):
    return ((fecha or date.today()) - FECHA_ANCLA).days


def extraer_texto(entrada, biblia_idx):
    libro_data = biblia_idx.get(entrada["libro"])
    if not libro_data:
        raise ValueError("Libro no encontrado en la Biblia: %s" % entrada["libro"])
    cap = next((c for c in libro_data["chapters"]
                if c["chapter"] == entrada["capitulo"]), None)
    if not cap:
        raise ValueError("Capítulo no encontrado: %s %d"
                         % (entrada["libro"], entrada["capitulo"]))
    versos = {v["verse"]: v["text"].strip() for v in cap["verses"]}
    fragmentos = [versos[n] for n in
                 range(entrada["verso_inicio"], entrada["verso_fin"] + 1)
                 if n in versos]
    if not fragmentos:
        raise ValueError("No se encontraron versos para %s" % entrada.get("clave"))
    return " ".join(fragmentos)


def historia_del_dia(fecha=None):
    pool = cargar_pool()
    if not pool:
        return None
    orden = _lista_ordenada(pool)
    idx = _dias_desde_ancla(fecha) % len(orden)
    clave = orden[idx]
    entrada = dict(pool[clave])
    entrada["clave"] = clave

    biblia_idx = cargar_biblia()
    entrada["texto_biblico"] = extraer_texto(entrada, biblia_idx)

    if entrada["verso_inicio"] == entrada["verso_fin"]:
        entrada["cita_es"] = "%s %d,%d" % (
            entrada["libro"], entrada["capitulo"], entrada["verso_inicio"])
    else:
        entrada["cita_es"] = "%s %d,%d-%d" % (
            entrada["libro"], entrada["capitulo"],
            entrada["verso_inicio"], entrada["verso_fin"])

    perfil = voz_del_dia(fecha)
    entrada["voz"] = perfil
    entrada["voz_nombre"] = _VOCES_EDGE.get(perfil, perfil)
    return entrada


if __name__ == "__main__":
    from datetime import timedelta
    from libros import nombre_espanol

    print("Fecha ancla: %s\n" % FECHA_ANCLA)
    print("%-12s %-45s %-25s %s" % ("FECHA", "HISTORIA", "CITA", "VOZ"))
    print("-" * 100)
    hoy = date.today()
    for i in range(14):
        f = hoy + timedelta(days=i)
        h = historia_del_dia(f)
        cita_es = "%s %d,%d-%d" % (nombre_espanol(h["libro"]), h["capitulo"],
                                   h["verso_inicio"], h["verso_fin"])
        print("%-12s %-45s %-25s %s" % (f.isoformat(), h["titulo"][:44],
                                        cita_es, h["voz"]))
