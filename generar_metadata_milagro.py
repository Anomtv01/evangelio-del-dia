# -*- coding: utf-8 -*-
"""
Genera titulo, descripcion y tags de YouTube para el video del Jueves
Eucaristico, a partir del JSON de milagro_del_dia.py, y los guarda en el
MISMO JSON.

DIFERENCIA CLAVE con la version del santo: la descripcion NO vuelca el guion
completo (que con 13 min pasa de los 5.000 caracteres que permite YouTube y
hace fallar la subida). En su lugar arma una descripcion CORTA y atractiva:
introduccion + que veras + credito obligatorio de las imagenes + hashtags,
siempre por debajo del limite.

Uso:
    python generar_metadata_milagro.py output_milagro/milagro_2026-08-06.json
"""

import json
import re
import sys
import unicodedata

LIMITE_TITULO = 100
LIMITE_DESC = 4800          # margen bajo los 5.000 de YouTube
LIMITE_TAGS = 480           # YouTube: 500 en total

MESES_ES = ["", "enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
            "agosto", "septiembre", "octubre", "noviembre", "diciembre"]

TAGS_BASE = [
    "milagro eucaristico", "milagros eucaristicos", "jueves eucaristico",
    "eucaristia", "adoracion al santisimo", "presencia real",
    "iglesia catolica", "fe catolica", "viva la fe catolica tv",
    "carlo acutis", "santisimo sacramento",
]

RECORDATORIO = (
    "🙏 Hoy es Jueves Eucarístico, día de la Adoración al Santísimo. "
    "Suscríbete a Viva la Fe Católica TV y activa la campanita para no "
    "perderte un nuevo milagro cada semana."
)

INTENCION = ("Deja en los comentarios tu intención de oración: nos unimos "
             "como comunidad para encomendarla ante el Santísimo.")


def limpiar(t):
    return t.replace("<", "").replace(">", "")


def sin_acentos(s):
    s = s.replace("ª", "a").replace("º", "")
    return "".join(c for c in unicodedata.normalize("NFD", s)
                   if unicodedata.category(c) != "Mn")


def fecha_es(iso):
    y, m, d = iso.split("-")
    return "%d de %s de %s" % (int(d), MESES_ES[int(m)], y)


def generar_titulo(data):
    lugar = data["titulo_milagro"].replace("Milagro Eucarístico de ", "")
    sub = data.get("subtitulo", "").strip()
    # Titulo con gancho de busqueda
    base = "Milagro Eucarístico de %s" % lugar
    if data.get("anio"):
        base += " (%s)" % data["anio"]
    base = limpiar(base)
    return base[:LIMITE_TITULO]


def _resumen_desde_guion(data, max_frases=4):
    """Toma las primeras frases del guion como resumen, sin volcarlo entero."""
    segs = data.get("segmentos") or []
    texto = " ".join(s["texto"] for s in segs
                     if s.get("seccion") in ("introduccion", "gancho", "relato"))
    if not texto:
        texto = data.get("biografia", "")
    frases = re.split(r"(?<=[.!?])\s+", texto.strip())
    resumen = " ".join(frases[:max_frases]).strip()
    # recorte de seguridad
    if len(resumen) > 700:
        resumen = resumen[:700].rsplit(". ", 1)[0] + "."
    return resumen


def generar_descripcion(data):
    lugar = data["titulo_milagro"].replace("Milagro Eucarístico de ", "")
    fecha_larga = fecha_es(data["fecha"])
    pais = data.get("pais") or ""
    anio = data.get("anio") or ""

    p = []
    p.append("✝️ Jueves Eucarístico · %s" % fecha_larga)
    ubic = ", ".join(x for x in (lugar, pais) if x)
    if anio:
        ubic += " (%s)" % anio
    p.append("📿 %s\n" % ubic)

    p.append(_resumen_desde_guion(data) + "\n")

    p.append("En este video verás:")
    p.append("• Cómo ocurrió el milagro")
    p.append("• Qué determinaron los estudios y qué reconoció la Iglesia")
    p.append("• Dónde se venera hoy la reliquia")
    p.append("• Qué nos dice sobre la Presencia Real de Cristo en la Eucaristía\n")

    p.append(RECORDATORIO + "\n")
    p.append(INTENCION + "\n")

    # Credito obligatorio de las imagenes
    credito = data.get("credito_imagenes")
    if credito:
        p.append(credito + "\n")

    hashtags = ("#MilagroEucaristico #JuevesEucaristico #Eucaristia "
                "#AdoracionAlSantisimo #FeCatolica #IglesiaCatolica")
    p.append(hashtags)

    desc = limpiar("\n".join(p))
    if len(desc) > LIMITE_DESC:
        desc = desc[:LIMITE_DESC].rsplit("\n", 1)[0]
    return desc


def generar_tags(data):
    tags = list(TAGS_BASE)
    lugar = data["titulo_milagro"].replace("Milagro Eucarístico de ", "")
    tags.append(sin_acentos("milagro eucaristico de %s" % lugar).lower())
    if data.get("pais"):
        tags.append(sin_acentos(data["pais"]).lower())

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
        print("Uso: python generar_metadata_milagro.py output_milagro/milagro_<fecha>.json")
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
