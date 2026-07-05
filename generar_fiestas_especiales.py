# -*- coding: utf-8 -*-
"""
Genera data/fiestas_especiales.json: un archivo de "excepciones" con la cita
correcta del Evangelio para las solemnidades/fiestas grandes que la fuente
automática (USCCB scraper) no tiene completas (revisado y confirmado contra
Felix Just S.J. - catholic-resources.org/Lectionary, tablas 1998 USA Edition).

Cubre 2023-2027 (mismo rango que nuestra fuente de citas diarias).
Solo se usa como respaldo cuando data/citas_diarias.json no tiene la lectura.
"""

import json
from datetime import date, timedelta

# Domingo de Pascua de cada año (fuente: calendario litúrgico oficial)
PASCUA = {
    2023: date(2023, 4, 9),
    2024: date(2024, 3, 31),
    2025: date(2025, 4, 20),
    2026: date(2026, 4, 5),
    2027: date(2027, 3, 28),
}

# Ciclo dominical (A/B/C) para el Tiempo Ordinario de cada año calendario
# (el ciclo cambia el 1er domingo de Adviento, pero para fechas dentro del
# mismo año antes de Adviento, corresponde el ciclo indicado)
CICLO = {2023: "A", 2024: "B", 2025: "C", 2026: "A", 2027: "B"}

GOSPEL_CICLO = {
    # Ascensión (Jueves de la 6ta semana de Pascua Y/O 7mo Domingo de Pascua)
    "Ascension": {
        "A": ("Matthew", "28:16-20"),
        "B": ("Mark", "16:15-20"),
        "C": ("Luke", "24:46-53"),
    },
    # Pentecostés (Misa del Día)
    "Pentecost": {
        "A": ("John", "20:19-23"),
        "B": ("John", "20:19-23"),
        "C": ("John", "20:19-23"),
    },
    # Santísima Trinidad
    "Trinity": {
        "A": ("John", "3:16-18"),
        "B": ("Matthew", "28:16-20"),
        "C": ("John", "16:12-15"),
    },
    # Corpus Christi
    "CorpusChristi": {
        "A": ("John", "6:51-58"),
        "B": ("Mark", "14:12-16,22-26"),
        "C": ("Luke", "9:11b-17"),
    },
    # Sagrado Corazón
    "SacredHeart": {
        "A": ("Matthew", "11:25-30"),
        "B": ("John", "19:31-37"),
        "C": ("Luke", "15:3-7"),
    },
    # Transfiguración (6 de agosto - usa el ciclo del año en curso)
    "Transfiguration": {
        "A": ("Matthew", "17:1-9"),
        "B": ("Mark", "9:2-10"),
        "C": ("Luke", "9:28b-36"),
    },
    # Cristo Rey (últ. domingo del Tiempo Ordinario) - ciclo del año que TERMINA
    # (ej. nov 2023 usa ciclo A, que es el ciclo de 2023)
    "ChristKing": {
        "A": ("Matthew", "25:31-46"),
        "B": ("John", "18:33b-37"),
        "C": ("Luke", "23:35-43"),
    },
}

# Domingos de Cuaresma 3/4/5 (forma "restaurada" de Año A, disponible
# también en B y C; aquí usamos la lectura estándar de cada ciclo)
LENT_SUNDAYS = {
    3: {"A": ("John", "4:5-42"), "B": ("John", "2:13-25"), "C": ("Luke", "13:1-9")},
    4: {"A": ("John", "9:1-41"), "B": ("John", "3:14-21"), "C": ("Luke", "15:1-3,11-32")},
    5: {"A": ("John", "11:1-45"), "B": ("John", "12:20-33"), "C": ("John", "8:1-11")},
}


def cita_str(libro, ref):
    return f"{libro} {ref}"


fiestas = {}


def agregar(fecha, feast, libro, ref):
    key = fecha.isoformat()
    fiestas.setdefault(key, []).append({
        "feast": feast,
        "citation": cita_str(libro, ref),
    })


for year, pascua in PASCUA.items():
    ciclo = CICLO[year]

    # --- Movibles basados en Pascua ---
    jueves_santo = pascua - timedelta(days=3)
    viernes_santo = pascua - timedelta(days=2)
    ascension_jue = pascua + timedelta(days=39)
    ascension_dom = pascua + timedelta(days=42)
    pentecostes = pascua + timedelta(days=49)
    trinidad = pascua + timedelta(days=56)
    corpus_jue = pascua + timedelta(days=60)
    corpus_dom = pascua + timedelta(days=63)
    sagrado_corazon = pascua + timedelta(days=68)

    agregar(pascua, "Domingo de Pascua (Misa del Día)", "John", "20:1-9")
    agregar(jueves_santo, "Jueves Santo - Misa de la Cena del Señor", "John", "13:1-15")
    agregar(viernes_santo, "Viernes Santo - Pasión del Señor", "John", "18:1-19:42")

    libro, ref = GOSPEL_CICLO["Ascension"][ciclo]
    agregar(ascension_jue, "Ascensión del Señor", libro, ref)
    agregar(ascension_dom, "Ascensión del Señor (7mo Domingo de Pascua)", libro, ref)

    libro, ref = GOSPEL_CICLO["Pentecost"][ciclo]
    agregar(pentecostes, "Pentecostés (Misa del Día)", libro, ref)

    libro, ref = GOSPEL_CICLO["Trinity"][ciclo]
    agregar(trinidad, "Santísima Trinidad", libro, ref)

    libro, ref = GOSPEL_CICLO["CorpusChristi"][ciclo]
    agregar(corpus_jue, "Santísimo Cuerpo y Sangre de Cristo", libro, ref)
    agregar(corpus_dom, "Santísimo Cuerpo y Sangre de Cristo (Domingo)", libro, ref)

    libro, ref = GOSPEL_CICLO["SacredHeart"][ciclo]
    agregar(sagrado_corazon, "Sagrado Corazón de Jesús", libro, ref)

    # --- Fijas por fecha calendario ---
    agregar(date(year, 1, 1), "Santa María, Madre de Dios", "Luke", "2:16-21")
    agregar(date(year, 2, 2), "Presentación del Señor", "Luke", "2:22-40")
    agregar(date(year, 3, 19), "San José, Esposo de la Virgen María", "Matthew", "1:16,18-21,24a")
    agregar(date(year, 3, 25), "Anunciación del Señor", "Luke", "1:26-38")
    agregar(date(year, 6, 24), "Natividad de San Juan Bautista", "Luke", "1:57-66,80")
    agregar(date(year, 6, 29), "San Pedro y San Pablo, Apóstoles", "Matthew", "16:13-19")

    libro, ref = GOSPEL_CICLO["Transfiguration"][ciclo]
    agregar(date(year, 8, 6), "Transfiguración del Señor", libro, ref)

    agregar(date(year, 8, 15), "Asunción de la Santísima Virgen María", "Luke", "1:39-56")
    agregar(date(year, 9, 14), "Exaltación de la Santa Cruz", "John", "3:13-17")
    agregar(date(year, 11, 1), "Todos los Santos", "Matthew", "5:1-12a")
    agregar(date(year, 11, 2), "Conmemoración de los Fieles Difuntos", "John", "11:17-27")
    agregar(date(year, 11, 9), "Dedicación de la Basílica de Letrán", "John", "2:13-22")
    agregar(date(year, 12, 8), "Inmaculada Concepción de la Virgen María", "Luke", "1:26-38")
    agregar(date(year, 12, 25), "Natividad del Señor (Misa del Día)", "John", "1:1-18")

    # --- Domingos de Cuaresma 3/4/5 (por si la fuente solo trae la opción de
    # Escrutinios y deja vacía la lectura estándar del ciclo) ---
    # Domingo de Ramos = Pascua - 7. Los Domingos de Cuaresma 5,4,3 van
    # contando hacia atrás desde ahí: 5to = Pascua-14, 4to = Pascua-21, 3ro = Pascua-28
    cuaresma3 = pascua - timedelta(days=28)
    cuaresma4 = pascua - timedelta(days=21)
    cuaresma5 = pascua - timedelta(days=14)
    nombres_domingo = {3: "3er", 4: "4to", 5: "5to"}
    for n, fecha in [(3, cuaresma3), (4, cuaresma4), (5, cuaresma5)]:
        libro, ref = LENT_SUNDAYS[n][ciclo]
        agregar(fecha, f"{nombres_domingo[n]} Domingo de Cuaresma", libro, ref)

with open("/home/claude/mensajes_virgen/data/fiestas_especiales.json", "w", encoding="utf-8") as f:
    json.dump(fiestas, f, ensure_ascii=False, indent=2, sort_keys=True)

print(f"Generadas {len(fiestas)} fechas de excepción (2023-2027).")
