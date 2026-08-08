# -*- coding: utf-8 -*-
"""
Genera título, descripción y tags de YouTube para el video del Santo del
Día, a partir del JSON producido por santo_del_dia.py, y los guarda de
vuelta EN EL MISMO JSON (a diferencia del Evangelio, acá no usamos un
archivo de metadata separado, para mantener todo el paquete del santo en
un solo lugar: output_santo/santo_<fecha>.json).

Uso:
    python generar_metadata_santo.py output_santo/santo_2026-08-11.json

Después de correr esto, el JSON queda con las claves nuevas:
    "titulo", "descripcion", "tags", "tags_string"
"""

import json
import os
import sys
import unicodedata

MESES_ES = [
    "", "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
]

TAGS_BASE = [
    "santo del dia", "vidas de santos", "biografia de santos",
    "iglesia catolica", "fe catolica", "viva la fe catolica tv",
    "santoral catolico", "historia de un santo",
]

RECORDATORIO_SUSCRIPCION = (
    "🙏 Si esta historia te bendijo, suscríbete a Viva la Fe Católica TV "
    "para no perderte las historias de cada día."
)


def fecha_es(fecha_iso):
    y, m, d = fecha_iso.split("-")
    return f"{int(d)} de {MESES_ES[int(m)]} de {y}"


def quitar_acentos(s):
    s = s.replace("ª", "a").replace("º", "")
    return "".join(
        c for c in unicodedata.normalize("NFD", s)
        if unicodedata.category(c) != "Mn"
    )


def generar_titulo(data):
    nombre = data["nombre_es"]
    subtitulo = data.get("subtitulo", "").strip()
    if subtitulo:
        base = f"{nombre}: {subtitulo}"
    else:
        base = f"{nombre} — Historia de un Santo"
    if len(base) <= 60:
        return base
    # Si es muy largo, nos quedamos solo con el nombre
    return nombre[:60]


def generar_descripcion(data):
    fecha_larga = fecha_es(data["fecha"])
    nombre = data["nombre_es"]
    subtitulo = data.get("subtitulo", "").strip()
    biografia = data["biografia"]

    # Resumen corto en vez de la biografia completa: el guion de 11 min supera
    # los 5.000 caracteres que permite YouTube y hace fallar la subida
    # ("invalid video description"). Tomamos las primeras frases.
    import re as _re
    segs = data.get("segmentos") or []
    texto = " ".join(sg["texto"] for sg in segs
                     if sg.get("seccion") in ("gancho", "contexto", "vida")) or biografia
    frases = _re.split(r"(?<=[.!?])\s+", texto.strip())
    resumen = " ".join(frases[:4]).strip()
    if len(resumen) > 700:
        resumen = resumen[:700].rsplit(". ", 1)[0] + "."

    partes = []
    partes.append(f"✝️ Santo del día, {fecha_larga}")
    if subtitulo:
        partes.append(f"📿 {nombre} — {subtitulo}\n")
    else:
        partes.append(f"📿 {nombre}\n")
    partes.append(resumen + "\n")
    partes.append("En este video conocerás su vida, sus pruebas y su legado "
                  "para la Iglesia.\n")
    partes.append(RECORDATORIO_SUSCRIPCION + "\n")
    partes.append("Deja en los comentarios tu intención de oración: oramos "
                  "juntos como comunidad.\n")

    hashtags = " ".join(
        f"#{t.replace(' ', '')}" for t in
        ["SantoDelDia", "VidasDeSantos", "FeCatolica", "IglesiaCatolica"]
    )
    partes.append(hashtags)

    desc = "\n".join(partes).replace("<", "").replace(">", "")
    if len(desc) > 4800:
        desc = desc[:4800].rsplit("\n", 1)[0]
    return desc


def generar_tags(data):
    tags = list(TAGS_BASE)
    nombre_normalizado = quitar_acentos(data["nombre_es"].lower())
    tags.append(nombre_normalizado)
    subtitulo = data.get("subtitulo", "")
    if subtitulo:
        tags.append(quitar_acentos(subtitulo.lower()))

    tags_normalizados = [quitar_acentos(t.lower()) for t in tags]
    resultado = []
    total = 0
    for t in tags_normalizados:
        add_len = len(t) + 2  # + ", "
        if total + add_len > 490:
            break
        resultado.append(t)
        total += add_len

    return resultado


def main():
    if len(sys.argv) < 2:
        print("Uso: python generar_metadata_santo.py output_santo/santo_<fecha>.json")
        sys.exit(1)

    json_path = sys.argv[1]
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    data["titulo"] = generar_titulo(data)
    data["descripcion"] = generar_descripcion(data)
    tags = generar_tags(data)
    data["tags"] = tags
    data["tags_string"] = ", ".join(tags)

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"TÍTULO ({len(data['titulo'])} caracteres):\n{data['titulo']}\n")
    print(f"DESCRIPCIÓN:\n{data['descripcion']}\n")
    print(f"TAGS ({len(data['tags_string'])} caracteres):\n{data['tags_string']}\n")
    print(f"Guardado (agregado) en: {json_path}")


if __name__ == "__main__":
    main()
