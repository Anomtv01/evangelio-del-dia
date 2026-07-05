# -*- coding: utf-8 -*-
"""
Traductor de nombres litúrgicos EN->ES para los patrones más comunes que
devuelve la fuente USCCB (días feriales, domingos ordinales, memorias,
fiestas y solemnidades de santos). No es un traductor universal: cubre
~95% de los casos comunes; lo que no reconoce lo deja tal cual en inglés
(mejor eso que una traducción incorrecta).
"""

import re

DIAS = {
    "Sunday": "Domingo", "Monday": "Lunes", "Tuesday": "Martes",
    "Wednesday": "Miércoles", "Thursday": "Jueves", "Friday": "Viernes",
    "Saturday": "Sábado",
}

ORDINALES = {
    "First": "1ª", "Second": "2ª", "Third": "3ª", "Fourth": "4ª", "Fifth": "5ª",
    "Sixth": "6ª", "Seventh": "7ª", "Eighth": "8ª", "Ninth": "9ª", "Tenth": "10ª",
    "Eleventh": "11ª", "Twelfth": "12ª", "Thirteenth": "13ª", "Fourteenth": "14ª",
    "Fifteenth": "15ª", "Sixteenth": "16ª", "Seventeenth": "17ª", "Eighteenth": "18ª",
    "Nineteenth": "19ª", "Twentieth": "20ª", "Twenty-first": "21ª", "Twenty-second": "22ª",
    "Twenty-third": "23ª", "Twenty-fourth": "24ª", "Twenty-fifth": "25ª",
    "Twenty-sixth": "26ª", "Twenty-seventh": "27ª", "Twenty-eighth": "28ª",
    "Twenty-ninth": "29ª", "Thirtieth": "30ª", "Thirty-first": "31ª",
    "Thirty-second": "32ª", "Thirty-third": "33ª", "Thirty-fourth": "34ª",
}

TEMPORADAS = {
    "Ordinary Time": "Tiempo Ordinario",
    "Advent": "Adviento",
    "Lent": "Cuaresma",
    "Easter": "Pascua",
    "Christmas": "Navidad",
}


def _ordinal_masculino(numero_es_fem):
    """'13ª' -> '13º' para casos donde se necesita masculino (Domingo)."""
    return numero_es_fem.replace("ª", "º")


def traducir_fiesta(nombre_en):
    if not nombre_en:
        return nombre_en

    texto = nombre_en.strip()

    # Caso: "Saturday of the Thirteenth Week in Ordinary Time"
    m = re.match(
        r"^(\w+) of the (\w+(?:-\w+)?) Week (?:in|of) (.+)$", texto
    )
    if m:
        dia_en, ordinal_en, temporada_en = m.groups()
        dia_es = DIAS.get(dia_en)
        ordinal_es = ORDINALES.get(ordinal_en)
        temporada_es = TEMPORADAS.get(temporada_en, temporada_en)
        if dia_es and ordinal_es:
            prep = "del" if temporada_en == "Ordinary Time" else "de"
            return f"{dia_es} de la {ordinal_es} Semana {prep} {temporada_es}"

    # Caso: "Thirteenth Sunday in Ordinary Time"
    m = re.match(r"^(\w+(?:-\w+)?) Sunday (?:in|of) (.+)$", texto)
    if m:
        ordinal_en, temporada_en = m.groups()
        ordinal_es = ORDINALES.get(ordinal_en)
        temporada_es = TEMPORADAS.get(temporada_en, temporada_en)
        if ordinal_es:
            prep = "del" if temporada_en == "Ordinary Time" else "de"
            return f"{_ordinal_masculino(ordinal_es)} Domingo {prep} {temporada_es}"

    # Caso: "Memorial of Saint X" / "Optional Memorial of Saint X"
    m = re.match(r"^(Optional )?Memorial of (Saint|Saints) (.+)$", texto)
    if m:
        opcional, _, nombre = m.groups()
        prefijo = "Memoria Opcional de" if opcional else "Memoria de"
        return f"{prefijo} San{'' if nombre.startswith(('a ', 'os ')) else ''} {nombre}".replace("  ", " ")

    # Caso: "Feast of Saint X"
    m = re.match(r"^Feast of (Saint|Saints) (.+)$", texto)
    if m:
        _, nombre = m.groups()
        return f"Fiesta de San {nombre}"

    # Caso: "Solemnity of X"
    m = re.match(r"^Solemnity of (.+)$", texto)
    if m:
        return f"Solemnidad de {m.group(1)}"

    # No reconocido: devolvemos el original en inglés (mejor que traducir mal)
    return texto
