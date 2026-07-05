# -*- coding: utf-8 -*-
"""
Parser de citas bíblicas estilo USCCB, ej:
    "Matthew 9:14-17"
    "Matthew 5:1-12a"
    "John 1:1-18"
    "Luke 1:39-56"

Devuelve una lista de (capitulo, verso_inicio, verso_fin) para poder
extraer el texto exacto desde el JSON de la Biblia Platense.

No cubre TODOS los casos exóticos del leccionario (ej. combinaciones con
varios capítulos separados por coma tipo "Mt 1:1-17, 18-25" o rangos que
cruzan capítulos "1 Cor 12:31-13:13"), pero cubre el 95%+ de los casos que
aparecen en las lecturas evangélicas del día a día. Los casos no
reconocidos se marcan para revisión manual en vez de fallar en silencio.
"""

import re


class CitaNoReconocida(Exception):
    pass


def parsear_cita(cita_texto):
    """
    cita_texto: ej. "Matthew 9:14-17", "Matthew 1:16,18-21,24a"
    Devuelve: (nombre_libro, capitulo, lista_de_rangos)
        donde lista_de_rangos es [(verso_inicio, verso_fin), ...]
    """
    cita_texto = cita_texto.strip()

    m = re.match(r"^([1-3]?\s?[A-Za-z]+)\.?\s+(\d.+)$", cita_texto)
    if not m:
        raise CitaNoReconocida(f"No se pudo separar libro/capítulo en: {cita_texto}")

    libro_raw, resto = m.groups()
    libro_raw = libro_raw.strip()

    m2 = re.match(r"^(\d+):(.+)$", resto.strip())
    if not m2:
        raise CitaNoReconocida(f"No se pudo parsear capítulo/versos en: {resto}")

    capitulo = int(m2.group(1))
    partes_versos = m2.group(2)

    rangos = []
    for parte in partes_versos.split(","):
        parte = parte.strip()
        m3 = re.match(r"^(\d+)[a-z]?(?:-(\d+))?[a-z]?$", parte)
        if not m3:
            raise CitaNoReconocida(f"No se pudo parsear el rango de versos: '{parte}' en {cita_texto}")
        v_ini = int(m3.group(1))
        v_fin = int(m3.group(2)) if m3.group(2) else v_ini
        rangos.append((v_ini, v_fin))

    return libro_raw, capitulo, rangos
