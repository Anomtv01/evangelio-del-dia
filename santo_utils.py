# -*- coding: utf-8 -*-
"""
Versión adaptada de las funciones de santo.py para la automatización
diaria: misma lógica de paletas/thumbnail/video, con dos cambios:

1. crear_thumbnail() puede recibir la ruta de la foto explícita (en vez
   de buscarla siempre por el nombre en español, que no coincide con
   los archivos descargados de Wikimedia, nombrados en inglés).
2. generar_audio() rota la voz de ElevenLabs por día (igual que
   generar_narracion.py del Evangelio), en vez de una voz fija.
"""

import os
import re
import subprocess

from elevenlabs.client import ElevenLabs
from PIL import Image, ImageDraw, ImageFont, ImageFilter

from voces import voz_del_dia

# Mismas 34 paletas de color que ya usa santo.py (copiadas acá para que
# este módulo sea autocontenido: no importamos santo.py directamente
# porque ese script ejecuta un procesamiento al final del archivo y
# depende de un config.py local con la API key de ElevenLabs, que no
# existe en el entorno de GitHub Actions).
PALETAS = {
    "rojo_verde":        {"acento": (220, 40, 20),  "caja": (10, 65, 30),   "borde": (255, 70, 40)},
    "azul_naranja":      {"acento": (30, 100, 220),  "caja": (100, 45, 0),   "borde": (255, 140, 20)},
    "amarillo_violeta":  {"acento": (240, 210, 0),   "caja": (60, 15, 90),   "borde": (200, 70, 240)},
    "cian_rojo":         {"acento": (0, 190, 210),   "caja": (100, 15, 8),   "borde": (255, 60, 30)},
    "magenta_verde":     {"acento": (210, 30, 120),  "caja": (10, 65, 35),   "borde": (50, 200, 100)},
    "purpura_dorado":    {"acento": (150, 40, 210),  "caja": (85, 60, 8),    "borde": (240, 190, 40)},
    "borgona_turquesa":  {"acento": (160, 20, 60),   "caja": (0, 70, 65),    "borde": (20, 210, 190)},
    "indigo_ambar":      {"acento": (70, 50, 180),   "caja": (90, 55, 0),    "borde": (255, 180, 20)},
    "triada_rjo_azl_aml":{"acento": (220, 40, 20),  "caja": (10, 35, 100),  "borde": (240, 200, 0)},
    "triada_vrd_nrj_vlt":{"acento": (30, 160, 80),  "caja": (100, 45, 0),   "borde": (150, 40, 210)},
    "triada_mgn_cel_drd":{"acento": (210, 30, 120), "caja": (20, 65, 95),   "borde": (210, 165, 25)},
    "triada_cyn_crL_ndg":{"acento": (0, 190, 210),  "caja": (110, 35, 25),  "borde": (70, 50, 180)},
    "mono_rojo":         {"acento": (255, 60, 30),   "caja": (80, 10, 5),    "borde": (180, 30, 15)},
    "mono_azul":         {"acento": (80, 150, 255),  "caja": (8, 22, 70),    "borde": (30, 100, 200)},
    "mono_verde":        {"acento": (60, 200, 100),  "caja": (8, 50, 25),    "borde": (25, 140, 70)},
    "mono_purpura":      {"acento": (190, 80, 255),  "caja": (50, 10, 75),   "borde": (120, 30, 180)},
    "mono_dorado":       {"acento": (255, 210, 40),  "caja": (70, 50, 5),    "borde": (190, 150, 20)},
    "mono_rosa":         {"acento": (255, 100, 160), "caja": (110, 20, 60),  "borde": (200, 60, 120)},
    "mono_cian":         {"acento": (0, 220, 240),   "caja": (0, 75, 90),    "borde": (0, 170, 190)},
    "mono_naranja":      {"acento": (255, 130, 0),   "caja": (100, 45, 0),   "borde": (200, 100, 0)},
    "tetrada_1":         {"acento": (220, 40, 20),   "caja": (0, 75, 90),    "borde": (240, 190, 40)},
    "tetrada_2":         {"acento": (30, 100, 220),  "caja": (100, 45, 0),   "borde": (150, 40, 210)},
    "tetrada_3":         {"acento": (0, 190, 210),   "caja": (80, 10, 5),    "borde": (210, 165, 25)},
    "tetrada_4":         {"acento": (210, 30, 120),  "caja": (10, 65, 35),   "borde": (70, 50, 180)},
    "analogo_fuego":     {"acento": (230, 80, 0),    "caja": (120, 15, 8),   "borde": (240, 150, 20)},
    "analogo_oceano":    {"acento": (0, 160, 200),   "caja": (8, 22, 70),    "borde": (20, 200, 160)},
    "analogo_bosque":    {"acento": (30, 160, 80),   "caja": (8, 28, 85),    "borde": (0, 190, 130)},
    "analogo_atardecer": {"acento": (210, 80, 150),  "caja": (100, 45, 0),   "borde": (240, 120, 40)},
    "analogo_aurora":    {"acento": (150, 40, 210),  "caja": (8, 22, 70),    "borde": (0, 160, 200)},
    "esmeralda":         {"acento": (0, 200, 130),   "caja": (0, 70, 45),    "borde": (20, 230, 150)},
    "zafiro":            {"acento": (20, 80, 200),   "caja": (8, 28, 85),    "borde": (50, 110, 240)},
    "rubi":              {"acento": (200, 10, 50),   "caja": (80, 4, 20),    "borde": (240, 30, 70)},
    "ambar":             {"acento": (220, 150, 0),   "caja": (90, 55, 0),    "borde": (255, 180, 20)},
    "jade":              {"acento": (0, 160, 110),   "caja": (0, 60, 42),    "borde": (20, 190, 130)},
    "amatista":          {"acento": (170, 60, 220),  "caja": (55, 12, 80),   "borde": (210, 100, 255)},
    "topacio":           {"acento": (0, 180, 200),   "caja": (0, 65, 80),    "borde": (20, 220, 230)},
    "coral":             {"acento": (230, 90, 70),   "caja": (110, 35, 25),  "borde": (255, 120, 90)},
}
LISTA_COLORES = list(PALETAS.keys())


def obtener_color(nombre):
    index = sum(ord(c) for c in nombre) % len(LISTA_COLORES)
    return LISTA_COLORES[index]


def buscar_foto(santo, carpetas_fotos=None):
    """Busca en la(s) carpeta(s) de fotos. Por defecto revisa primero la
    carpeta 'fotos/' dentro del proyecto (la que subimos a GitHub, así
    funciona igual en GitHub Actions), y como respaldo la ruta de
    Windows C:\\VivaLaFe\\fotos (para cuando corras algo en tu compu)."""
    if carpetas_fotos is None:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        carpetas_fotos = [
            os.path.join(base_dir, "fotos"),
            "C:\\VivaLaFe\\fotos",
        ]
    elif isinstance(carpetas_fotos, str):
        carpetas_fotos = [carpetas_fotos]

    nombre_buscar = santo.lower()
    for carpeta in carpetas_fotos:
        if not os.path.isdir(carpeta):
            continue
        for archivo in os.listdir(carpeta):
            if archivo.lower().endswith((".jpg", ".jpeg", ".png")):
                nombre_archivo = os.path.splitext(archivo)[0].lower()
                nombre_archivo = nombre_archivo.replace("_", " ").replace("-", " ")
                if nombre_buscar in nombre_archivo or nombre_archivo in nombre_buscar:
                    return os.path.join(carpeta, archivo)
    return None


def fondo_generico(W, H, paleta):
    """Portada de respaldo elaborada, para cuando no se encuentra foto
    del santo: degradado oscuro + resplandor dorado/de la paleta del día
    + una cruz sencilla, en vez de un color plano."""
    color_acento = paleta["acento"]
    color_borde = paleta["borde"]

    top = (8, 8, 14)
    bottom = tuple(max(0, c // 6) for c in color_acento)  # tinte sutil de la paleta

    img = Image.new("RGB", (W, H), top)
    draw_grad = ImageDraw.Draw(img)
    for y in range(H):
        t = y / H
        r = int(top[0] + (bottom[0] - top[0]) * t)
        g = int(top[1] + (bottom[1] - top[1]) * t)
        b = int(top[2] + (bottom[2] - top[2]) * t)
        draw_grad.line([(0, y), (W, y)], fill=(r, g, b))

    # Resplandor radial suave, centrado un poco arriba del medio
    overlay = Image.new("L", (W, H), 0)
    odraw = ImageDraw.Draw(overlay)
    cx, cy, radio = W // 2, int(H * 0.38), int(W * 0.9)
    for i in range(radio, 0, -6):
        alpha = int(90 * (1 - i / radio) ** 2)
        odraw.ellipse([cx - i, cy - i, cx + i, cy + i], fill=alpha)
    overlay = overlay.filter(ImageFilter.GaussianBlur(40))
    glow_layer = Image.new("RGB", (W, H), color_acento)
    img = Image.composite(glow_layer, img, overlay)

    # Cruz simple centrada en la zona del resplandor
    draw = ImageDraw.Draw(img)
    tam = int(W * 0.22)
    grosor = max(10, tam // 10)
    draw.rectangle(
        [cx - grosor // 2, cy - tam // 2, cx + grosor // 2, cy + tam // 2],
        fill=color_borde,
    )
    y_h = cy - tam // 6
    draw.rectangle(
        [cx - tam // 3, y_h - grosor // 2, cx + tam // 3, y_h + grosor // 2],
        fill=color_borde,
    )

    return img


def crear_thumbnail(santo, carpeta, subtitulo="", gancho="", foto_path=None):
    W, H = 1080, 1920
    color = obtener_color(santo)
    paleta = PALETAS[color]

    ruta_foto = foto_path or buscar_foto(santo)
    if ruta_foto and os.path.exists(ruta_foto):
        foto = Image.open(ruta_foto).convert("RGB")
        ratio_w = W / foto.width
        ratio_h = H / foto.height
        ratio = max(ratio_w, ratio_h)
        nuevo_w = int(foto.width * ratio)
        nuevo_h = int(foto.height * ratio)
        foto = foto.resize((nuevo_w, nuevo_h), Image.LANCZOS)
        left = (nuevo_w - W) // 2
        top = (nuevo_h - H) // 2
        foto = foto.crop((left, top, left + W, top + H))
        img = foto.copy()
    else:
        img = fondo_generico(W, H, paleta)

    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    for i in range(900):
        alpha = int(230 * (i / 900))
        overlay_draw.rectangle([0, H - 900 + i, W, H - 900 + i + 1], fill=(0, 0, 0, alpha))
    img = img.convert("RGBA")
    img = Image.alpha_composite(img, overlay)
    img = img.convert("RGB")
    draw = ImageDraw.Draw(img)

    corner = 50
    lw = 4
    cb = paleta["borde"]
    draw.line([(25, 25), (25 + corner, 25)], fill=cb, width=lw)
    draw.line([(25, 25), (25, 25 + corner)], fill=cb, width=lw)
    draw.line([(W - 25, 25), (W - 25 - corner, 25)], fill=cb, width=lw)
    draw.line([(W - 25, 25), (W - 25, 25 + corner)], fill=cb, width=lw)
    draw.line([(25, H - 25), (25 + corner, H - 25)], fill=cb, width=lw)
    draw.line([(25, H - 25), (25, H - 25 - corner)], fill=cb, width=lw)
    draw.line([(W - 25, H - 25), (W - 25 - corner, H - 25)], fill=cb, width=lw)
    draw.line([(W - 25, H - 25), (W - 25, H - 25 - corner)], fill=cb, width=lw)

    try:
        font_san = ImageFont.truetype("C:\\Windows\\Fonts\\arialbd.ttf", 75)
        font_nombre1 = ImageFont.truetype("C:\\Windows\\Fonts\\arialbd.ttf", 150)
        font_nombre2 = ImageFont.truetype("C:\\Windows\\Fonts\\arialbd.ttf", 120)
        font_subtitulo = ImageFont.truetype("C:\\Windows\\Fonts\\arial.ttf", 48)
        font_gancho = ImageFont.truetype("C:\\Windows\\Fonts\\arialbd.ttf", 52)
    except Exception:
        # En GitHub Actions (Linux) no existen las fuentes de Windows;
        # usamos Lora, que ya viene incluida en el repo.
        fonts_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")
        try:
            font_san = ImageFont.truetype(os.path.join(fonts_dir, "Lora-Bold.ttf"), 75)
            font_nombre1 = ImageFont.truetype(os.path.join(fonts_dir, "Lora-Bold.ttf"), 150)
            font_nombre2 = ImageFont.truetype(os.path.join(fonts_dir, "Lora-Bold.ttf"), 120)
            font_subtitulo = ImageFont.truetype(os.path.join(fonts_dir, "Lora-Regular.ttf"), 48)
            font_gancho = ImageFont.truetype(os.path.join(fonts_dir, "Lora-Bold.ttf"), 52)
        except Exception:
            font_san = ImageFont.load_default()
            font_nombre1 = font_san
            font_nombre2 = font_san
            font_subtitulo = font_san
            font_gancho = font_san

    cx = W // 2
    y = H - 780

    palabras = santo.split()
    prefijo = ""
    nombre_resto = santo
    if palabras[0].lower() in ["san", "santa", "santo"]:
        prefijo = palabras[0].upper()
        nombre_resto = " ".join(palabras[1:])

    if prefijo:
        draw.text((cx, y), prefijo, font=font_san, fill=(255, 255, 255), anchor="mm")
        y += 95

    partes = nombre_resto.upper().split()
    if len(partes) >= 2:
        draw.text((cx, y), partes[0], font=font_nombre1, fill=paleta["acento"], anchor="mm")
        y += 155
        draw.text((cx, y), " ".join(partes[1:]), font=font_nombre2, fill=(255, 255, 255), anchor="mm")
        y += 130
    else:
        draw.text((cx, y), nombre_resto.upper(), font=font_nombre1, fill=paleta["acento"], anchor="mm")
        y += 160

    if subtitulo:
        draw.text((cx, y), subtitulo, font=font_subtitulo, fill=(200, 200, 200), anchor="mm")
        y += 65

    if gancho:
        y += 20
        lineas = gancho.split("\n")
        alto_caja = len(lineas) * 65 + 45
        draw.rectangle([50, y, W - 50, y + alto_caja], fill=paleta["caja"], outline=paleta["borde"], width=3)
        for i, linea in enumerate(lineas):
            draw.text((cx, y + 30 + i * 65), linea, font=font_gancho, fill=(255, 230, 200), anchor="mm")

    path = os.path.join(carpeta, "thumbnail.png")
    img.save(path)
    return path


def generar_audio(guion, carpeta, fecha_iso, api_key):
    """Igual que santo.py, pero rotando la voz por día (ver voces.py)
    en vez de una voz fija."""
    voice_id = voz_del_dia(fecha_iso)
    client = ElevenLabs(api_key=api_key)
    audio = client.text_to_speech.convert(
        voice_id=voice_id,
        text=guion,
        model_id="eleven_multilingual_v2",
        voice_settings={
            "stability": 0.62,
            "similarity_boost": 0.80,
            "style": 0.27,
            "use_speaker_boost": True,
        },
    )
    path = os.path.join(carpeta, "audio.mp3")
    with open(path, "wb") as f:
        for chunk in audio:
            f.write(chunk)
    return path, voice_id


def crear_video(thumbnail, audio, carpeta, nombre_archivo_base):
    nombre_archivo = re.sub(r'[<>:"/\\|?*]', "", nombre_archivo_base) + ".mp4"
    output = os.path.join(carpeta, nombre_archivo)
    if os.path.exists(output):
        os.remove(output)
    subprocess.run([
        "ffmpeg", "-y", "-loop", "1", "-i", thumbnail,
        "-i", audio, "-c:v", "libx264", "-tune", "stillimage",
        "-c:a", "aac", "-b:a", "192k", "-pix_fmt", "yuv420p",
        "-shortest", output
    ], check=True)
    return output
