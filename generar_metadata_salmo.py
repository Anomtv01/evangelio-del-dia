# -*- coding: utf-8 -*-
"""
Genera título, descripción y tags de YouTube para el video del Salmo del
Día, a partir del JSON de salmo_del_dia.py, guardándolos en el mismo JSON.
Uso:
    python generar_metadata_salmo.py output_salmo/salmo_2026-08-11.json
"""
import json
import os
import sys
import unicodedata
MESES_ES = ["", "enero", "febrero", "marzo", "abril", "mayo", "junio",
            "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
TAGS_BASE = [
    "salmo del dia", "salmos", "biblia catolica", "palabra de dios",
    "oracion catolica", "iglesia catolica", "fe catolica",
    "viva la fe catolica tv", "salmo de hoy", "reflexion catolica",
]
RECORDATORIO = ("🙏 Si este salmo te bendijo, suscríbete a Viva la Fe Católica "
                "TV para orar juntos cada día.")
 
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
 
def fecha_es(fecha_iso):
    y, m, d = fecha_iso.split("-")
    return f"{int(d)} de {MESES_ES[int(m)]} de {y}"
def quitar_acentos(s):
    s = s.replace("ª", "a").replace("º", "")
    return "".join(c for c in unicodedata.normalize("NFD", s)
                   if unicodedata.category(c) != "Mn")
def generar_titulo(data):
    num = data["num_catolico"]
    sub = data.get("subtitulo", "").strip()
    if sub:
        base = f"Salmo {num}: {sub}"
    else:
        base = f"Salmo {num} — Palabra de Dios"
    if len(base) <= 60:
        return base
    return f"Salmo {num}"[:60]
def generar_descripcion(data):
    fecha_larga = fecha_es(data["fecha"])
    num = data["num_catolico"]
    sub = data.get("subtitulo", "").strip()
    reflexion = data.get("reflexion", "")
    texto = data.get("texto_salmo", "")
    partes = []
    partes.append(f"🎵 Salmo del día, {fecha_larga}")
    if sub:
        partes.append(f"📖 Salmo {num} — {sub}\n")
    else:
        partes.append(f"📖 Salmo {num}\n")
    if texto:
        # Un extracto del salmo (no todo, para no llenar la descripción)
        extracto = texto[:400].strip()
        partes.append(f"«{extracto}...»\n")
    if reflexion:
        partes.append("💭 Reflexión:")
        partes.append(reflexion + "\n")
    partes.append(bloque_afiliados() + "\n")
    partes.append(RECORDATORIO)
    partes.append("\nTexto bíblico: Biblia Platense (Straubinger) - Dominio Público")
    hashtags = " ".join(f"#{t.replace(' ', '')}" for t in
                        ["SalmoDelDia", "Salmos", "PalabraDeDios", "FeCatolica"])
    partes.append("\n" + hashtags)
    return "\n".join(partes)
def generar_tags(data):
    tags = list(TAGS_BASE)
    tags.append(f"salmo {data['num_catolico']}")
    sub = data.get("subtitulo", "")
    if sub:
        tags.append(quitar_acentos(sub.lower()))
    tags_norm = [quitar_acentos(t.lower()) for t in tags]
    resultado, total = [], 0
    for t in tags_norm:
        if total + len(t) + 2 > 490:
            break
        resultado.append(t)
        total += len(t) + 2
    return resultado
def main():
    if len(sys.argv) < 2:
        print("Uso: python generar_metadata_salmo.py output_salmo/salmo_<fecha>.json")
        sys.exit(1)
    json_path = sys.argv[1]
    with open(json_path, encoding="utf-8") as f:
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
    print(f"TAGS:\n{data['tags_string']}\n")
    print(f"Guardado (agregado) en: {json_path}")
if __name__ == "__main__":
    main()
 
