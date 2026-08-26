#!/usr/bin/env python3
"""
generar_portada.py
===================
Genera automáticamente la portada (1080x1920) para "Santos y sus Milagros" /
Viva la Fe Católica TV, replicando el estilo aprobado el 26/08/2026
(diseño "Classic Editorial Cover" en Canva).

USO EN EL PIPELINE (GitHub Actions / local):
    python3 generar_portada.py \
        --imagen fondo_santo.jpg \
        --titulo1 "SAN JOSÉ DE" \
        --titulo2 "CUPERTINO" \
        --subtitulo "El Santo que Volaba" \
        --gancho "Levitaba en pleno vuelo|durante la Santa Misa,|ante el asombro de todos 😱" \
        --dato "La Inquisición lo interrogó.|Los médicos lo examinaron.|Nadie halló una explicación." \
        --salida portada_final.png

Cada "|" dentro de --gancho y --dato marca un salto de línea.
La imagen de fondo (--imagen) debe ser un retrato/pintura relacionada al santo
(usa ElevenLabs/Canva o tu banco de imágenes; este script NO la genera).

Requiere: pip install pillow --break-system-packages
"""

import argparse
import textwrap
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps

# ---------------------------------------------------------------------------
# CONFIGURACIÓN DE ESTILO — valores tomados directamente del diseño aprobado
# ---------------------------------------------------------------------------
ANCHO, ALTO = 1080, 1920

COLOR_FONDO_PANEL = (10, 22, 40)        # navy oscuro del panel inferior
COLOR_TEXTO_CREMA = (232, 224, 192)     # #e8e0c0 - texto principal
COLOR_DORADO = (212, 175, 55)           # #d4af37 - acentos / líneas
COLOR_TEXTO_DATO = (232, 224, 192)

FUENTE_DIR = "/usr/share/fonts/truetype/dejavu/"
F_TAG = FUENTE_DIR + "DejaVuSerif.ttf"
F_TITULO = FUENTE_DIR + "DejaVuSerif-Bold.ttf"
F_SUBTITULO = FUENTE_DIR + "DejaVuSerif-Italic.ttf"
F_GANCHO = FUENTE_DIR + "DejaVuSerif.ttf"
F_DATO = FUENTE_DIR + "DejaVuSerif-Bold.ttf"
F_CTA = FUENTE_DIR + "DejaVuSans-Bold.ttf"

# Panel de texto empieza al 39% de la altura (igual que el diseño Canva)
PANEL_TOP = int(ALTO * 0.393)

MARGEN_LATERAL = 68


def cargar_fuente(ruta, size):
    return ImageFont.truetype(ruta, size)


def texto_centrado(draw, texto, y, fuente, color, ancho_lienzo=ANCHO):
    bbox = draw.textbbox((0, 0), texto, font=fuente)
    w = bbox[2] - bbox[0]
    x = (ancho_lienzo - w) / 2
    draw.text((x, y), texto, font=fuente, fill=color)
    return bbox[3] - bbox[1]  # alto del texto dibujado


def bloque_multilinea(draw, lineas, y_inicio, fuente, color, interlineado=1.35):
    y = y_inicio
    for linea in lineas:
        alto_linea = texto_centrado(draw, linea, y, fuente, color)
        y += alto_linea * interlineado
    return y


def preparar_fondo(ruta_imagen):
    """Recorta/ajusta la imagen de fondo para llenar el ancho 1080 y la altura del panel superior."""
    img = Image.open(ruta_imagen).convert("RGB")
    img = ImageOps.fit(img, (ANCHO, PANEL_TOP + 40), method=Image.LANCZOS)
    return img


def generar_portada(imagen_fondo, titulo1, titulo2, subtitulo, gancho_lineas,
                     dato_lineas, cta, tag="SANTOS Y SUS MILAGROS", salida="portada_final.png"):

    lienzo = Image.new("RGB", (ANCHO, ALTO), COLOR_FONDO_PANEL)

    # 1) Foto de fondo arriba
    foto = preparar_fondo(imagen_fondo)
    lienzo.paste(foto, (0, 0))

    # Degradado suave hacia el panel oscuro para que el texto no "corte" feo
    gradiente = Image.new("L", (ANCHO, 220), 0)
    for i in range(220):
        gradiente.putpixel((0, i), int(255 * (i / 220)))
    gradiente = gradiente.resize((ANCHO, 220))
    overlay = Image.new("RGB", (ANCHO, 220), COLOR_FONDO_PANEL)
    lienzo.paste(overlay, (0, PANEL_TOP - 220), gradiente)

    draw = ImageDraw.Draw(lienzo, "RGBA")

    # 2) Panel inferior sólido
    draw.rectangle([0, PANEL_TOP, ANCHO, ALTO], fill=COLOR_FONDO_PANEL)

    y = PANEL_TOP + 40

    # 3) Tag superior "SANTOS Y SUS MILAGROS" con crucecitas
    f_tag = cargar_fuente(F_TAG, 26)
    texto_centrado(draw, f"†  †  †", y - 40, cargar_fuente(F_TAG, 22), COLOR_DORADO)
    texto_centrado(draw, tag.upper(), y, f_tag, COLOR_TEXTO_CREMA)
    y += 55

    # línea decorativa
    draw.line([(MARGEN_LATERAL, y), (ANCHO - MARGEN_LATERAL, y)], fill=(*COLOR_DORADO, 90), width=1)
    y += 30

    # 4) Título (2 líneas: nombre pequeño + apellido/título grande dorado)
    f_t1 = cargar_fuente(F_TITULO, 50)
    texto_centrado(draw, titulo1.upper(), y, f_t1, COLOR_TEXTO_CREMA)
    y += 62

    f_t2 = cargar_fuente(F_TITULO, 100)
    texto_centrado(draw, titulo2.upper(), y, f_t2, COLOR_DORADO)
    y += 128

    # 5) Subtítulo
    f_sub = cargar_fuente(F_SUBTITULO, 34)
    texto_centrado(draw, subtitulo, y, f_sub, (200, 195, 175))
    y += 60

    draw.line([(ANCHO // 2 - 160, y), (ANCHO // 2 - 20, y)], fill=(*COLOR_DORADO, 130), width=1)
    draw.line([(ANCHO // 2 + 20, y), (ANCHO // 2 + 160, y)], fill=(*COLOR_DORADO, 130), width=1)
    y += 70

    # 6) Bloque "gancho" (hook) — el dato más impactante, letras grandes
    f_gancho = cargar_fuente(F_GANCHO, 38)
    y = bloque_multilinea(draw, gancho_lineas, y, f_gancho, COLOR_TEXTO_CREMA)
    y += 60

    # 7) Bloque de datos verificados (negrita, un poco más chico)
    f_dato = cargar_fuente(F_DATO, 30)
    y = bloque_multilinea(draw, dato_lineas, y, f_dato, COLOR_TEXTO_DATO)
    y += 70

    # 8) CTA final
    f_cta = cargar_fuente(F_CTA, 38)
    texto_centrado(draw, cta, y, f_cta, COLOR_TEXTO_CREMA)
    y += 60
    texto_centrado(draw, "✦", y, cargar_fuente(F_TAG, 26), COLOR_DORADO)

    # 9) Marco decorativo (esquinas doradas)
    L = 40
    grosor = 3
    for (x0, y0, dx, dy) in [(MARGEN_LATERAL - 20, 30, 1, 1),
                              (ANCHO - MARGEN_LATERAL + 20, 30, -1, 1),
                              (MARGEN_LATERAL - 20, ALTO - 30, 1, -1),
                              (ANCHO - MARGEN_LATERAL + 20, ALTO - 30, -1, -1)]:
        draw.line([(x0, y0), (x0 + L * dx, y0)], fill=COLOR_DORADO, width=grosor)
        draw.line([(x0, y0), (x0, y0 + L * dy)], fill=COLOR_DORADO, width=grosor)

    lienzo.save(salida, quality=95)
    print(f"✅ Portada generada: {salida}")
    return salida


def main():
    p = argparse.ArgumentParser(description="Genera portada estilo 'Santos y sus Milagros'")
    p.add_argument("--imagen", required=True, help="Ruta a la imagen/pintura de fondo")
    p.add_argument("--titulo1", required=True, help='Primera línea del título, ej. "SAN JOSÉ DE"')
    p.add_argument("--titulo2", required=True, help='Segunda línea (grande, dorada), ej. "CUPERTINO"')
    p.add_argument("--subtitulo", required=True, help='Ej. "El Santo que Volaba"')
    p.add_argument("--gancho", required=True, help='Líneas separadas por "|"')
    p.add_argument("--dato", required=True, help='Líneas separadas por "|"')
    p.add_argument("--cta", default="¿LO CONOCÍAS? COMENTA 👇")
    p.add_argument("--tag", default="Santos y sus Milagros")
    p.add_argument("--salida", default="portada_final.png")
    args = p.parse_args()

    generar_portada(
        imagen_fondo=args.imagen,
        titulo1=args.titulo1,
        titulo2=args.titulo2,
        subtitulo=args.subtitulo,
        gancho_lineas=args.gancho.split("|"),
        dato_lineas=args.dato.split("|"),
        cta=args.cta,
        tag=args.tag,
        salida=args.salida,
    )


if __name__ == "__main__":
    main()
