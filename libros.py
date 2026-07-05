# -*- coding: utf-8 -*-
"""
Mapeo de nombres de libros bíblicos: inglés (usado internamente por la cita
de USCCB y por el JSON de la Biblia Platense) -> español (para mostrar en
pantalla, título, descripción, etc.)
"""

LIBRO_EN_A_ES = {
    "Genesis": "Génesis",
    "Exodus": "Éxodo",
    "Leviticus": "Levítico",
    "Numbers": "Números",
    "Deuteronomy": "Deuteronomio",
    "Joshua": "Josué",
    "Judges": "Jueces",
    "Ruth": "Rut",
    "I Samuel": "1 Samuel",
    "II Samuel": "2 Samuel",
    "I Kings": "1 Reyes",
    "II Kings": "2 Reyes",
    "I Chronicles": "1 Crónicas",
    "II Chronicles": "2 Crónicas",
    "Ezra": "Esdras",
    "Nehemiah": "Nehemías",
    "Tobit": "Tobías",
    "Judith": "Judit",
    "Esther": "Ester",
    "Job": "Job",
    "Psalms": "Salmos",
    "Proverbs": "Proverbios",
    "Ecclesiastes": "Eclesiastés",
    "Song of Solomon": "Cantar de los Cantares",
    "Wisdom": "Sabiduría",
    "Sirach": "Eclesiástico (Sirácida)",
    "Isaiah": "Isaías",
    "Jeremiah": "Jeremías",
    "Lamentations": "Lamentaciones",
    "Baruch": "Baruc",
    "Ezekiel": "Ezequiel",
    "Daniel": "Daniel",
    "Hosea": "Oseas",
    "Joel": "Joel",
    "Amos": "Amós",
    "Obadiah": "Abdías",
    "Jonah": "Jonás",
    "Micah": "Miqueas",
    "Nahum": "Nahúm",
    "Habakkuk": "Habacuc",
    "Zephaniah": "Sofonías",
    "Haggai": "Ageo",
    "Zechariah": "Zacarías",
    "Malachi": "Malaquías",
    "I Maccabees": "1 Macabeos",
    "II Maccabees": "2 Macabeos",
    "Matthew": "Mateo",
    "Mark": "Marcos",
    "Luke": "Lucas",
    "John": "Juan",
    "Acts": "Hechos de los Apóstoles",
    "Romans": "Romanos",
    "I Corinthians": "1 Corintios",
    "II Corinthians": "2 Corintios",
    "Galatians": "Gálatas",
    "Ephesians": "Efesios",
    "Philippians": "Filipenses",
    "Colossians": "Colosenses",
    "I Thessalonians": "1 Tesalonicenses",
    "II Thessalonians": "2 Tesalonicenses",
    "I Timothy": "1 Timoteo",
    "II Timothy": "2 Timoteo",
    "Titus": "Tito",
    "Philemon": "Filemón",
    "Hebrews": "Hebreos",
    "James": "Santiago",
    "I Peter": "1 Pedro",
    "II Peter": "2 Pedro",
    "I John": "1 Juan",
    "II John": "2 Juan",
    "III John": "3 Juan",
    "Jude": "Judas",
    "Revelation of John": "Apocalipsis",
}

# La cita de USCCB usa nombres en inglés abreviados (ej. "Matthew 9:14-17",
# "1 Cor 12:31-13:13", "Ps 85"). Este mapa cubre las abreviaturas más
# comunes que aparecen en el Evangelio (los 4 evangelistas cubren ~95% de
# los casos de uso de este script).
ABREV_A_LIBRO_EN = {
    "Matthew": "Matthew", "Matt": "Matthew", "Mt": "Matthew",
    "Mark": "Mark", "Mk": "Mark",
    "Luke": "Luke", "Lk": "Luke",
    "John": "John", "Jn": "John",
}


def normalizar_libro(nombre_citacion):
    """Convierte el nombre de libro tal como aparece en la cita (ej. 'Matthew')
    al nombre exacto usado como key en el JSON de la Biblia Platense."""
    return ABREV_A_LIBRO_EN.get(nombre_citacion.strip(), nombre_citacion.strip())


def nombre_espanol(nombre_libro_en):
    return LIBRO_EN_A_ES.get(nombre_libro_en, nombre_libro_en)
