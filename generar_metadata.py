# -*- coding: utf-8 -*-
"""
Genera título, descripción y tags de YouTube para el video del Evangelio
del Día, a partir del JSON producido por evangelio_del_dia.py.
 
Uso:
    python generar_metadata.py output/evangelio_2026-07-04.json
 
Salida: output/metadata_<fecha>.json (+ imprime todo en pantalla)
"""
 
import json
import os
import sys
import unicodedata
 
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
 
MESES_ES = [
    "", "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
]
 
TAGS_BASE = [
    "evangelio de hoy", "evangelio del dia", "biblia catolica",
    "reflexion catolica", "iglesia catolica", "fe catolica",
    "viva la fe catolica tv", "palabra de dios", "lectura del evangelio",
]
 
# ---------------------------------------------------------------------------
# ENLACES DE AFILIADO DE AMAZON
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
]
 
 
def bloque_afiliados():
    """Arma el bloque de enlaces de afiliado con su divulgación."""
    lineas = [DIVULGACION_AFILIADOS, "", "🛍️ ARTÍCULOS DE FE RECOMENDADOS:"]
    for nombre, enlace in ENLACES_AFILIADOS:
        lineas.append(f"{nombre}: {enlace}")
    return "\n".join(lineas)
 
 
def fecha_es(fecha_iso, con_articulo=True):
    y, m, d = fecha_iso.split("-")
    txt = f"{int(d)} de {MESES_ES[int(m)]} de {y}"
    return txt
 
 
def quitar_acentos(s):
    s = s.replace("ª", "a").replace("º", "")
    return "".join(
        c for c in unicodedata.normalize("NFD", s)
        if unicodedata.category(c) != "Mn"
    )
 
 
def generar_titulo(data):
    cita = data["cita_es"]
    # Título corto, bajo 60 caracteres (según tu estándar de canal)
    base = f"Evangelio de Hoy 📖 {cita}"
    if len(base) <= 60:
        return base
    # Si es muy largo (fiestas con cita larga), recortamos el emoji/formato
    base2 = f"Evangelio de Hoy - {cita}"
    return base2[:60]
 
 
def generar_descripcion(data, reflexion_texto=None):
    fecha_larga = fecha_es(data["fecha"])
    fiesta = data.get("fiesta_liturgica", "").strip()
    cita = data["cita_es"]
    texto = data["texto_evangelio"]
 
    partes = []
    partes.append(f"📖 Evangelio de hoy, {fecha_larga}")
    if fiesta:
        partes.append(f"✝️ {fiesta}")
    partes.append(f"\nLectura del Santo Evangelio según San {data['libro']} ({cita})\n")
    partes.append(f"«{texto}»\n")
 
    if reflexion_texto:
        partes.append("💭 Reflexión:")
        partes.append(reflexion_texto + "\n")
 
    partes.append(bloque_afiliados() + "\n")
 
    partes.append(
        "🙏 Si esta palabra te bendijo, compártela y suscríbete a Viva la Fe "
        "Católica TV para no perderte el Evangelio de cada día.\n"
    )
    partes.append(
        f"Texto bíblico: {data.get('fuente_texto', 'Biblia Platense (Straubinger) - Dominio Público')}"
    )
 
    hashtags = " ".join(
        f"#{t.replace(' ', '')}" for t in
        ["EvangelioDeHoy", "PalabraDeDios", "FeCatolica", "ReflexionDiaria"]
    )
    partes.append("\n" + hashtags)
 
    return "\n".join(partes)
 
 
def generar_tags(data):
    tags = list(TAGS_BASE)
    tags.append(f"evangelio segun san {data['libro'].lower()}")
    fiesta = data.get("fiesta_liturgica", "")
    if fiesta:
        tags.append(quitar_acentos(fiesta.lower()))
 
    # Unimos y recortamos a <500 caracteres, sin tildes (tu estándar de canal)
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
        print("Uso: python generar_metadata.py output/evangelio_<fecha>.json [reflexion.txt]")
        sys.exit(1)
 
    json_path = sys.argv[1]
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
 
    reflexion_texto = None
    if len(sys.argv) > 2:
        with open(sys.argv[2], "r", encoding="utf-8") as f:
            reflexion_texto = f.read().strip()
 
    titulo = generar_titulo(data)
    descripcion = generar_descripcion(data, reflexion_texto)
    tags = generar_tags(data)
 
    resultado = {
        "fecha": data["fecha"],
        "titulo": titulo,
        "descripcion": descripcion,
        "tags": tags,
        "tags_string": ", ".join(tags),
    }
 
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_path = os.path.join(OUTPUT_DIR, f"metadata_{data['fecha']}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)
 
    print(f"TÍTULO ({len(titulo)} caracteres):\n{titulo}\n")
    print(f"DESCRIPCIÓN:\n{descripcion}\n")
    print(f"TAGS ({len(', '.join(tags))} caracteres):\n{', '.join(tags)}\n")
    print(f"Guardado en: {out_path}")
 
 
if __name__ == "__main__":
    main()
 
