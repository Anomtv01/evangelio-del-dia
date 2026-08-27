# -*- coding: utf-8 -*-
"""
corto_rotativo.py — Viva la Fe Católica TV
============================================
Elige el pasaje del Short diario del Evangelio: el EVANGELIO LITÚRGICO REAL
de hoy, exactamente como marca el calendario de la Iglesia — misma fuente y
misma lógica que usa evangelio_del_dia.py (el video largo del Evangelio):

  1) Primero busca en data/citas_diarias.json (leccionario, scrapeado de
     USCCB).
  2) Si esa fuente no tiene la lectura completa de hoy (pasa en ~11% de los
     días, sobre todo en solemnidades grandes), cae a
     data/fiestas_especiales.json (respaldo manual verificado contra las
     tablas de Felix Just, S.J.).

En ambos casos arma el texto exacto con la Biblia Platense
(data/biblia_platense.json), igual que el resto del canal.

CAMBIO (26/08/2026): antes este script rotaba por un POOL FIJO de 50
historias "más queridas" del Evangelio (la samaritana, el hijo pródigo...),
sin relación con la lectura litúrgica del día -- data/pool_historias_evangelio.json
quedó sin uso. Se cambió a pedido: el Short tiene que ser el Evangelio de
HOY, el mismo que se lee en misa, no una selección aparte.

También rota la VOZ del narrador día a día, reutilizando
voces_edge.voz_del_dia() (la misma rotación que usan las otras series).
"""

import json
import os
from datetime import date

from citas import CitaNoReconocida
from evangelio_del_dia import (
    CITAS_PATH,
    FIESTAS_PATH,
    cargar_biblia,
    extraer_texto_evangelio,
    obtener_registro_de_fiesta,
    obtener_registro_del_dia,
)
from libros import nombre_espanol

try:
    from voces_edge import voz_del_dia, VOCES as _VOCES_EDGE
except Exception:                                                # noqa: BLE001
    def voz_del_dia(fecha=None):
        return "narrador"
    _VOCES_EDGE = {}


def _cargar_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _clave_desde_cita(libro_en, capitulo, v_ini, v_fin):
    """Identificador estable para el pasaje del día (nombre de archivo,
    búsqueda de portada propia si algún día se agrega una)."""
    base = libro_en.lower().replace(" ", "_")
    return "%s_%d_%d-%d" % (base, capitulo, v_ini, v_fin)


def historia_del_dia(fecha=None):
    """
    Devuelve el Evangelio litúrgico real de la fecha dada (hoy si None),
    con el mismo formato que ya consumía guion_corto.py:
        clave, titulo, cita_es, categoria, texto_biblico, voz, voz_nombre
    Devuelve None si no se encuentra lectura para esa fecha (ni en la fuente
    automática ni en el respaldo de fiestas) o si la cita no se pudo parsear.
    """
    fecha_obj = fecha if isinstance(fecha, date) else date.today()
    fecha_str = fecha_obj.isoformat()

    citas = _cargar_json(CITAS_PATH)
    fiestas = _cargar_json(FIESTAS_PATH)

    resultado = obtener_registro_del_dia(citas, fecha_str)
    if not resultado:
        resultado = obtener_registro_de_fiesta(fiestas, fecha_str)
    if not resultado:
        return None

    cita_texto, feast, _lectionary_number = resultado
    biblia_idx = cargar_biblia()

    try:
        libro_en, capitulo, v_ini, v_fin, texto = extraer_texto_evangelio(
            biblia_idx, cita_texto)
    except CitaNoReconocida:
        return None

    libro_es = nombre_espanol(libro_en)
    cita_es = ("%s %d,%d" % (libro_es, capitulo, v_ini) if v_ini == v_fin else
               "%s %d,%d-%d" % (libro_es, capitulo, v_ini, v_fin))

    feast = (feast or "").strip()
    perfil = voz_del_dia(fecha_obj)

    return {
        "clave": _clave_desde_cita(libro_en, capitulo, v_ini, v_fin),
        "titulo": feast if feast else cita_es,
        "fiesta_liturgica": feast,
        "cita_es": cita_es,
        "categoria": None,
        "libro": libro_es,
        "capitulo": capitulo,
        "verso_inicio": v_ini,
        "verso_fin": v_fin,
        "texto_biblico": texto,
        "voz": perfil,
        "voz_nombre": _VOCES_EDGE.get(perfil, perfil),
    }


if __name__ == "__main__":
    from datetime import timedelta

    print("%-12s %-45s %-25s %s" % ("FECHA", "FIESTA / HISTORIA", "CITA", "VOZ"))
    print("-" * 100)
    hoy = date.today()
    for i in range(14):
        f = hoy + timedelta(days=i)
        h = historia_del_dia(f)
        if not h:
            print("%-12s (sin lectura para esta fecha)" % f.isoformat())
            continue
        print("%-12s %-45s %-25s %s" % (f.isoformat(), h["titulo"][:44],
                                        h["cita_es"], h["voz"]))
