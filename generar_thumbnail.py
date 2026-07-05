# -*- coding: utf-8 -*-
"""
Genera el thumbnail (1280x720) del Evangelio del Día, manteniendo el estilo
de marca del canal: fondo oscuro, luz dorada radial, líneas de acento
doradas, y el doble marco estilo manuscrito.

Uso:
    python generar_thumbnail.py output/evangelio_2026-07-04.json

Salida: output/thumbnail_<fecha>.png
"""

# -*- coding: utf-8 -*-
"""
Genera el thumbnail (1280x720) del Evangelio del Día: imagen religiosa a la
izquierda (con degradado hacia el fondo oscuro), y toda la información
(cita, fiesta, fecha) a la derecha. Paleta de color rotativa según el día
(ver paletas.py).

Uso:
    python generar_thumbnail.py output/evangelio_2026-07-04.json

Salida: output/thumbnail_<fecha>.png
"""

import json
import os
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from paletas import paleta_del_dia

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FONTS_DIR = os.path.join(BASE_DIR, "fonts")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

W, H = 1280, 720

# Ancho de la franja de imagen a la derecha
IMG_W = 560
IMG_X0 = W - IMG_W
# La zona de texto va del margen izquierdo hasta donde arranca la imagen
TEXTO_X1 = IMG_X0 + 40  # se solapa un poco con el degradado

COLOR_WHITE = (240, 235, 220)

MESES_ES = [
    "", "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
]

# Nombre de archivo de imagen a usar (podés rotar entre varias si subís más)
IMAGENES_DISPONIBLES = ["jesus_corona_espinas.png"]


def font(name, size):
    return ImageFont.truetype(os.path.join(FONTS_DIR, name), size)


def fecha_es(fecha_iso):
    y, m, d = fecha_iso.split("-")
    return f"{int(d)} de {MESES_ES[int(m)]} de {y}"


def elegir_imagen(fecha_iso):
    idx = int(fecha_iso.replace("-", "")) % len(IMAGENES_DISPONIBLES)
    return IMAGENES_DISPONIBLES[idx]


def fondo_degradado(color_bg_extra):
    """Fondo oscuro con un leve tinte según la paleta del día."""
    bg_top = (10, 8, 14)
    bg_bottom = color_bg_extra
    img = Image.new("RGB", (W, H), bg_top)
    px = img.load()
    for y in range(H):
        t = y / H
        r = int(bg_top[0] + (bg_bottom[0] - bg_top[0]) * t)
        g = int(bg_top[1] + (bg_bottom[1] - bg_top[1]) * t)
        b = int(bg_top[2] + (bg_bottom[2] - bg_top[2]) * t)
        for x in range(W):
            px[x, y] = (r, g, b)
    return img


def aplicar_imagen_fondo(base_img, nombre_archivo, color_tinte, opacidad=95):
    """Superpone una imagen de fondo (ej. Biblia/cruz), teñida con el color
    de la paleta del día (en vez de solo oscurecerla a negro), para que
    contraste lindo con el resto del diseño."""
    ruta = os.path.join(ASSETS_DIR, nombre_archivo)
    if not os.path.exists(ruta):
        return base_img

    fondo = Image.open(ruta).convert("RGB")
    ratio_objetivo = W / H
    ratio_img = fondo.width / fondo.height
    if ratio_img > ratio_objetivo:
        nuevo_alto = H
        nuevo_ancho = int(H * ratio_img)
        fondo = fondo.resize((nuevo_ancho, nuevo_alto), Image.LANCZOS)
        left = (nuevo_ancho - W) // 2
        fondo = fondo.crop((left, 0, left + W, H))
    else:
        nuevo_ancho = W
        nuevo_alto = int(W / ratio_img)
        fondo = fondo.resize((nuevo_ancho, nuevo_alto), Image.LANCZOS)
        top = (nuevo_alto - H) // 2
        fondo = fondo.crop((0, top, W, top + H))

    # Oscurecer un poco la base, y luego teñirla con el color de la paleta
    negro = Image.new("RGB", (W, H), (0, 0, 0))
    fondo_oscuro = Image.blend(negro, fondo, 0.55)

    tinte_oscuro = tuple(int(c * 0.35) for c in color_tinte)
    capa_tinte = Image.new("RGB", (W, H), tinte_oscuro)
    fondo_teñido = Image.blend(capa_tinte, fondo_oscuro, 0.7)

    mask = Image.new("L", (W, H), opacidad)
    return Image.composite(fondo_teñido, base_img, mask)


def preparar_imagen_lateral(nombre_archivo):
    """Recorta/escala la imagen para llenar la franja izquierda (IMG_W x H)
    y le agrega un degradado de opacidad hacia la derecha para que se
    funda con el fondo oscuro."""
    ruta = os.path.join(ASSETS_DIR, nombre_archivo)
    img = Image.open(ruta).convert("RGB")

    # Escalar para cubrir IMG_W x H manteniendo proporción, recortando el resto
    ratio_objetivo = IMG_W / H
    ratio_img = img.width / img.height

    if ratio_img > ratio_objetivo:
        # imagen más "ancha" que el objetivo -> recortar los costados
        nuevo_alto = H
        nuevo_ancho = int(H * ratio_img)
        img = img.resize((nuevo_ancho, nuevo_alto), Image.LANCZOS)
        # Priorizamos mostrar el lado IZQUIERDO de la imagen (donde suele
        # estar el rostro en fotos de perfil como esta)
        img = img.crop((0, 0, IMG_W, H))
    else:
        nuevo_ancho = IMG_W
        nuevo_alto = int(IMG_W / ratio_img)
        img = img.resize((nuevo_ancho, nuevo_alto), Image.LANCZOS)
        top = (nuevo_alto - H) // 2
        img = img.crop((0, top, IMG_W, top + H))

    return img


def componer_imagen_con_degradado(base_img, imagen_lateral, color_bg_extra):
    """Pega la imagen lateral (derecha) sobre el fondo, con una máscara de
    opacidad que se desvanece hacia la izquierda (lado que mira al texto),
    dejando el rostro -que está hacia ese mismo lado- sin taparse."""
    mask = Image.new("L", (IMG_W, H), 255)
    mdraw = ImageDraw.Draw(mask)
    # Fade acotado a una franja angosta del borde izquierdo, para no tapar
    # el rostro (que queda del lado izquierdo del recorte, mirando al texto)
    fade_width = int(IMG_W * 0.16)
    for x in range(0, fade_width):
        t = x / fade_width
        alpha = int(255 * t)
        mdraw.line([(x, 0), (x, H)], fill=alpha)

    # leve viñeta oscura arriba/abajo de la imagen para integrarla mejor
    vign = Image.new("L", (IMG_W, H), 0)
    vdraw = ImageDraw.Draw(vign)
    for y in range(H):
        d = min(y, H - y) / (H / 2)
        vdraw.line([(0, y), (IMG_W, y)], fill=int(60 * (1 - d)))
    oscurecido = Image.new("RGB", (IMG_W, H), (0, 0, 0))
    imagen_lateral = Image.composite(oscurecido, imagen_lateral, vign)

    base_img.paste(imagen_lateral, (IMG_X0, 0), mask)
    return base_img


def marco_doble(draw, color_gold, color_gold_light, margen_ext=28, margen_int=42):
    draw.rectangle([margen_ext, margen_ext, W - margen_ext, H - margen_ext],
                   outline=color_gold, width=3)
    draw.rectangle([margen_int, margen_int, W - margen_int, H - margen_int],
                   outline=color_gold, width=1)
    esquinas = [
        (margen_int, margen_int, 1, 1),
        (W - margen_int, margen_int, -1, 1),
        (margen_int, H - margen_int, 1, -1),
        (W - margen_int, H - margen_int, -1, -1),
    ]
    largo = 26
    for x, y, sx, sy in esquinas:
        draw.line([(x, y), (x + largo * sx, y)], fill=color_gold_light, width=3)
        draw.line([(x, y), (x, y + largo * sy)], fill=color_gold_light, width=3)


def texto_izquierda(draw, texto, x, y, fnt, color, letter_spacing=0):
    if letter_spacing:
        cx = x
        for c in texto:
            draw.text((cx, y), c, font=fnt, fill=color)
            cx += draw.textlength(c, font=fnt) + letter_spacing
    else:
        draw.text((x, y), texto, font=fnt, fill=color)


def envolver_texto(draw, texto, fnt, ancho_max):
    palabras = texto.split()
    lineas = []
    actual = ""
    for palabra in palabras:
        prueba = (actual + " " + palabra).strip()
        if draw.textlength(prueba, font=fnt) <= ancho_max:
            actual = prueba
        else:
            if actual:
                lineas.append(actual)
            actual = palabra
    if actual:
        lineas.append(actual)
    return lineas


def generar_thumbnail(evangelio_data, out_path):
    fecha = evangelio_data["fecha"]
    nombre_paleta, color_gold, color_gold_light, color_bg_extra = paleta_del_dia(fecha)

    img = fondo_degradado(color_bg_extra)
    img = aplicar_imagen_fondo(img, "biblia_cruz_fondo.png", color_gold, opacidad=95)

    imagen_lateral = preparar_imagen_lateral(elegir_imagen(fecha))
    img = componer_imagen_con_degradado(img, imagen_lateral, color_bg_extra)

    draw = ImageDraw.Draw(img)
    marco_doble(draw, color_gold, color_gold_light)

    text_x = 190
    ancho_texto = TEXTO_X1 - 40 - text_x

    f_kicker = font("Lora-Bold.ttf", 40)
    f_titulo = font("Lora-Bold.ttf", 58)
    f_fiesta = font("Lora-Regular.ttf", 26)
    f_fecha = font("Lora-Bold.ttf", 36)

    fiesta = evangelio_data.get("fiesta_liturgica", "").strip()
    lineas_cita = envolver_texto(draw, evangelio_data["cita_es"], f_titulo, ancho_texto)
    lineas_fiesta = envolver_texto(draw, fiesta, f_fiesta, ancho_texto)[:2] if fiesta else []

    # Alturas de cada bloque, para poder centrar todo el conjunto verticalmente
    ALTO_KICKER = 60
    ALTO_LINEA_CITA = 70
    ALTO_LINEA_FIESTA = 38
    ESPACIO_LINEA = 32   # espacio + línea decorativa
    ESPACIO_FECHA = 55

    alto_total = (
        ALTO_KICKER
        + len(lineas_cita) * ALTO_LINEA_CITA
        + ESPACIO_LINEA
        + len(lineas_fiesta) * ALTO_LINEA_FIESTA
        + ESPACIO_FECHA
        + 50  # alto de la línea de fecha
    )

    y = (H - alto_total) // 2

    texto_izquierda(draw, "EVANGELIO DE HOY", text_x, y, f_kicker, color_gold_light, letter_spacing=3)
    y += ALTO_KICKER

    for linea in lineas_cita:
        texto_izquierda(draw, linea, text_x, y, f_titulo, COLOR_WHITE)
        y += ALTO_LINEA_CITA

    y += 6
    draw.line([(text_x, y), (text_x + 220, y)], fill=color_gold, width=2)
    draw.ellipse([text_x - 8, y - 6, text_x + 4, y + 6], fill=color_gold_light)
    y += ESPACIO_LINEA

    for linea in lineas_fiesta:
        texto_izquierda(draw, linea, text_x, y, f_fiesta, color_gold)
        y += ALTO_LINEA_FIESTA

    y += ESPACIO_FECHA
    texto_izquierda(draw, fecha_es(fecha), text_x, y, f_fecha, COLOR_WHITE)

    img.save(out_path, "PNG")
    return out_path


def main():
    if len(sys.argv) < 2:
        print("Uso: python generar_thumbnail.py output/evangelio_<fecha>.json")
        sys.exit(1)

    json_path = sys.argv[1]
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    out_path = os.path.join(OUTPUT_DIR, f"thumbnail_{data['fecha']}.png")
    generar_thumbnail(data, out_path)
    print(f"Thumbnail guardado en: {out_path}")


if __name__ == "__main__":
    main()

