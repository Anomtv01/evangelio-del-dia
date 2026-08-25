# -*- coding: utf-8 -*-
"""
Genera título, descripción y tags de YouTube para el Short diario del
Evangelio, a partir del JSON de guion_corto.py, y los guarda en el MISMO
JSON.

Uso:
    python generar_metadata_corto.py output_corto/corto_2026-08-25.json
"""

import json
import re
import sys
import unicodedata

LIMITE_TITULO = 100
LIMITE_DESC = 4800
LIMITE_TAGS = 480

TAGS_BASE = [
    "evangelio de hoy", "evangelio del dia", "biblia catolica",
    "historias de la biblia", "shorts catolicos", "fe catolica",
    "iglesia catolica", "viva la fe catolica tv", "palabra de dios",
    "shorts",
]

RECORDATORIO = ("🙏 Suscríbete a Viva la Fe Católica TV y activa la "
                "campanita para no perderte el Evangelio de cada día en "
                "dos minutos.")

# ---------------------------------------------------------------------------
# ENLACES DE AFILIADO DE AMAZON (mismo bloque que el resto del canal).
# Para agregar un producto nuevo: añade una línea (emoji + nombre, enlace).
# Para quitar uno: borra su línea. Nada más que editar.
# ---------------------------------------------------------------------------
DIVULGACION_AFILIADOS = (
    "📿 Algunos enlaces son de afiliado. Como afiliado de Amazon, gano por "
    "compras que califiquen, sin costo extra para ti. Tu apoyo ayuda a "
    "sostener este ministerio. 🙏"
)
ENLACES_AFILIADOS = [
    ("📖 Biblia Católica (Virgen de Guadalupe)",
     "https://www.amazon.com/dp/1644732475?tag=vivalafecatol-20"),
    ("📿 Santo Rosario",
     "https://amzn.to/4we4xBf"),
    ("📕 Diario de Santa Faustina (Divina Misericordia)",
     "https://www.amazon.com/dp/0944203264?tag=vivalafecatol-20"),
    ("🙏 Libro de 50 Novenas Poderosas",
     "https://www.amazon.com/dp/B0F7HQ1LTD?tag=vivalafecatol-20"),
    ("🕯️ Veladora Virgen de Guadalupe",
     "https://www.amazon.com/dp/B0GTZTQS57?tag=vivalafecatol-20"),
    ("✝️ Llavero de San Benito (protección)",
     "https://www.amazon.com/dp/B0GJCS7CSJ?tag=vivalafecatol-20"),
    ("📿 Rosario de madera San Benito (pack de 2)",
     "https://amzn.to/4fs9Qb3"),
]

# ---------------------------------------------------------------------------
# ENLACE DE AFILIADO DE WALMART (Walmart Creator). Enlace de seguimiento a
# la colección "Catholic Faith & Religious Gifts" del storefront del canal
# (biblias, rosarios, imágenes y decoración religiosa). Para agregar mas
# colecciones o enlaces de producto individuales, añade una tupla mas a
# ENLACES_AFILIADOS_WALMART.
# ---------------------------------------------------------------------------
DIVULGACION_AFILIADOS_WALMART = (
    "🛒 También soy creador de Walmart Creator: algunos enlaces de Walmart "
    "son de afiliado y puedo ganar una comisión por compras que califiquen, "
    "sin costo extra para ti."
)
ENLACES_AFILIADOS_WALMART = [
    ("✝️ Artículos de Fe Católica en Walmart (biblias, rosarios y más)",
     "https://walmrt.us/4hzq4k6"),
]


def bloque_afiliados():
    lineas = [DIVULGACION_AFILIADOS, "", "🛍️ ARTÍCULOS DE FE RECOMENDADOS:"]
    for nombre, enlace in ENLACES_AFILIADOS:
        lineas.append("%s: %s" % (nombre, enlace))
    lineas.append("")
    lineas.append(DIVULGACION_AFILIADOS_WALMART)
    for nombre, enlace in ENLACES_AFILIADOS_WALMART:
        lineas.append("%s: %s" % (nombre, enlace))
    return "\n".join(lineas)


def limpiar(t):
    return t.replace("<", "").replace(">", "")


def sin_acentos(s):
    s = s.replace("ª", "a").replace("º", "")
    return "".join(c for c in unicodedata.normalize("NFD", s)
                   if unicodedata.category(c) != "Mn")


def generar_titulo(data):
    # El gancho va en 2 lineas para la miniatura (pantalla); para el TITULO
    # del video las unimos en una sola frase completa, si no queda vacio.
    gancho = " ".join(l.strip() for l in
                      (data.get("gancho_pantalla") or "").split("\n") if l.strip())
    base = gancho if gancho else data["titulo_historia"]
    base = limpiar(base)
    titulo = "%s #Shorts" % base
    if len(titulo) > LIMITE_TITULO:
        margen = LIMITE_TITULO - len(" #Shorts") - 1
        titulo = "%s… #Shorts" % base[:margen]
    return titulo


def generar_descripcion(data):
    p = []
    p.append("✝️ %s (%s)\n" % (data["titulo_historia"], data["cita_es"]))

    texto_relato = " ".join(s["texto"] for s in data["segmentos"]
                            if s.get("seccion") in ("gancho", "relato"))
    frases = re.split(r"(?<=[.!?])\s+", texto_relato.strip())
    resumen = " ".join(frases[:3]).strip()
    if len(resumen) > 500:
        resumen = resumen[:500].rsplit(". ", 1)[0] + "."
    p.append(resumen + "\n")

    p.append(bloque_afiliados() + "\n")
    p.append(RECORDATORIO + "\n")

    hashtags = "#Shorts #Evangelio #Biblia #FeCatolica #IglesiaCatolica"
    p.append(hashtags)

    desc = limpiar("\n".join(p))
    if len(desc) > LIMITE_DESC:
        desc = desc[:LIMITE_DESC].rsplit("\n", 1)[0]
    return desc


def generar_tags(data):
    tags = list(TAGS_BASE)
    tags.append(sin_acentos(data["titulo_historia"]).lower())
    if data.get("categoria"):
        tags.append(sin_acentos(data["categoria"]).lower())

    salida, total = [], 0
    for t in tags:
        t = sin_acentos(t.lower()).strip()
        if total + len(t) + 2 > LIMITE_TAGS:
            break
        salida.append(t)
        total += len(t) + 2
    return salida


def main():
    if len(sys.argv) < 2:
        print("Uso: python generar_metadata_corto.py output_corto/corto_<fecha>.json")
        sys.exit(1)

    ruta = sys.argv[1]
    with open(ruta, encoding="utf-8") as f:
        data = json.load(f)

    data["titulo"] = generar_titulo(data)
    data["descripcion"] = generar_descripcion(data)
    tags = generar_tags(data)
    data["tags"] = tags
    data["tags_string"] = ", ".join(tags)

    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print("TITULO (%d/%d):\n%s\n" % (len(data["titulo"]), LIMITE_TITULO, data["titulo"]))
    print("DESCRIPCION (%d/5000 caracteres):\n%s\n" % (len(data["descripcion"]), data["descripcion"]))
    print("TAGS (%d/500):\n%s" % (len(data["tags_string"]), data["tags_string"]))


if __name__ == "__main__":
    main()
