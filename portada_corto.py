# -*- coding: utf-8 -*-
"""Portada católica dinámica para el Short diario del Evangelio."""

import hashlib
import math
import os
import re
from datetime import date

from PIL import Image, ImageDraw, ImageFilter, ImageFont

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
W, H = 1080, 1920
AZUL = (5, 18, 42)
AZUL_MEDIO = (12, 42, 78)
ORO = (214, 174, 78)
ORO_CLARO = (250, 224, 158)
MARFIL = (239, 229, 204)
ROJO_MANTO = (126, 27, 34)


def _semilla(fecha_iso, texto):
    return int(hashlib.sha256((fecha_iso + "|" + texto).encode("utf-8")).hexdigest()[:12], 16)


def _fuente(negrita, tam):
    repo_fonts = os.path.join(os.path.dirname(BASE_DIR), "fonts")
    nombres = (["Lora-Bold.ttf", "DejaVuSerif-Bold.ttf"] if negrita else
               ["Lora-Regular.ttf", "DejaVuSerif.ttf"])
    candidatos = []
    for nombre in nombres:
        candidatos.extend([
            os.path.join(BASE_DIR, "fonts", nombre),
            os.path.join(repo_fonts, nombre),
            "/usr/share/fonts/truetype/dejavu/" + nombre,
            "C:\\Windows\\Fonts\\arialbd.ttf" if negrita else "C:\\Windows\\Fonts\\arial.ttf",
        ])
    for ruta in candidatos:
        try:
            return ImageFont.truetype(ruta, tam)
        except Exception:
            pass
    return ImageFont.load_default()


def _degradado():
    img = Image.new("RGB", (W, H), AZUL)
    d = ImageDraw.Draw(img)
    for y in range(H):
        t = y / max(H - 1, 1)
        luz = math.exp(-((t - .43) / .27) ** 2)
        color = tuple(int(AZUL[i] * (1 - .42 * luz) + AZUL_MEDIO[i] * .42 * luz)
                      for i in range(3))
        d.line((0, y, W, y), fill=color)
    return img


def _eje_de_luz(img, centro_x):
    capa = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    px = capa.load()
    for y in range(H):
        apertura = 105 + int(y * .22)
        for x in range(max(0, centro_x - apertura), min(W, centro_x + apertura)):
            distancia = abs(x - centro_x) / apertura
            alpha = int(80 * (1 - distancia) ** 2 * (1 - .32 * y / H))
            px[x, y] = ORO_CLARO + (alpha,)
    capa = capa.filter(ImageFilter.GaussianBlur(32))
    return Image.alpha_composite(img.convert("RGBA"), capa).convert("RGB")


def _escena(texto):
    t = texto.lower()
    reglas = [
        ("agua", ("agua", "mar", "barca", "tormenta", "pozo", "pesca")),
        ("pan", ("pan", "multiplic", "eucar", "comer", "cena")),
        ("montana", ("monte", "montaña", "transfigur", "bienavent")),
        ("sanacion", ("sanó", "sano", "ciego", "lepro", "enfer", "curó", "milagro")),
        ("templo", ("templo", "sinagoga", "farise", "escriba")),
        ("ovejas", ("oveja", "pastor", "rebaño")),
        ("semilla", ("semilla", "sembr", "viña", "cosecha", "higuera")),
        ("camino", ("camino", "discípulo", "discipulo", "seguir", "envió", "envio")),
    ]
    for escena, palabras in reglas:
        if any(p in t for p in palabras):
            return escena
    return "amanecer"


def _motivo(img, escena, semilla):
    d = ImageDraw.Draw(img, "RGBA")
    horizonte = 1110
    if escena == "agua":
        d.rectangle((0, horizonte, W, 1450), fill=(7, 45, 76, 180))
        for i in range(12):
            y = horizonte + 18 + i * 25
            desplazamiento = (semilla >> i) % 90
            d.arc((-80 + desplazamiento, y, 1160 - desplazamiento, y + 70), 190, 350,
                  fill=ORO_CLARO + (34,), width=3)
    elif escena == "pan":
        for x, y, r in ((210, 1220, 115), (430, 1285, 100), (760, 1215, 125)):
            d.ellipse((x-r, y-r*.55, x+r, y+r*.55), fill=(167, 112, 48, 160), outline=ORO+(100,), width=4)
            d.arc((x-r*.5, y-r*.42, x+r*.5, y+r*.42), 205, 335, fill=ORO_CLARO+(110,), width=5)
    elif escena == "montana":
        d.polygon(((0, 1380), (330, 940), (540, 1180), (760, 860), (1080, 1360), (1080, 1500), (0, 1500)),
                  fill=(4, 20, 34, 210))
        d.line(((760, 860), (760, 1190)), fill=ORO_CLARO+(90,), width=5)
    elif escena == "sanacion":
        d.ellipse((120, 1170, 410, 1470), outline=ORO_CLARO+(65,), width=9)
        d.line((265, 1280, 265, 1510), fill=ORO_CLARO+(70,), width=15)
        d.line((265, 1340, 160, 1420), fill=ORO_CLARO+(70,), width=12)
    elif escena == "templo":
        d.polygon(((120, 1190), (540, 910), (960, 1190)), fill=(10, 31, 55, 210), outline=ORO+(75,))
        for x in range(190, 940, 130):
            d.rectangle((x, 1190, x+45, 1510), fill=(8, 24, 42, 220), outline=ORO+(60,))
    elif escena == "ovejas":
        for x, y in ((170, 1340), (330, 1280), (820, 1340)):
            d.ellipse((x-70, y-45, x+70, y+45), fill=MARFIL+(135,), outline=ORO+(70,))
            d.ellipse((x+45, y-35, x+95, y+15), fill=(30, 24, 24, 170))
    elif escena == "semilla":
        for x in (140, 300, 780, 930):
            alto = 170 + ((semilla >> (x % 17)) % 140)
            d.line((x, 1470, x, 1470-alto), fill=ORO_CLARO+(95,), width=5)
            d.ellipse((x-45, 1470-alto+30, x+4, 1470-alto+70), fill=(84, 132, 77, 130))
            d.ellipse((x-4, 1470-alto+65, x+45, 1470-alto+105), fill=(84, 132, 77, 130))
    elif escena == "camino":
        d.polygon(((420, 1540), (660, 1540), (585, 1090), (510, 1090)), fill=ORO_CLARO+(42,))
    else:
        d.ellipse((180, 970, 900, 1690), fill=ORO+(12,), outline=ORO+(30,), width=4)


def _jesus(img, lado):
    """Figura reverente y estilizada: túnica marfil, manto rojo y halo fino."""
    d = ImageDraw.Draw(img, "RGBA")
    cx = 670 if lado == "derecha" else 410
    cabeza_y = 720
    # halo fino y resplandor, sin iconografía recargada
    for r, a, w in ((175, 22, 20), (135, 45, 8), (105, 185, 5)):
        d.ellipse((cx-r, cabeza_y-r, cx+r, cabeza_y+r), outline=ORO_CLARO+(a,), width=w)
    # cabello, rostro sereno de perfil y barba
    d.ellipse((cx-76, cabeza_y-95, cx+74, cabeza_y+86), fill=(74, 47, 34, 255))
    d.ellipse((cx-51, cabeza_y-72, cx+72, cabeza_y+66), fill=(206, 163, 125, 255))
    perfil = 1 if lado == "derecha" else -1
    d.polygon(((cx+35*perfil, cabeza_y-18), (cx+88*perfil, cabeza_y+5),
               (cx+34*perfil, cabeza_y+24)), fill=(206, 163, 125, 255))
    d.arc((cx-48, cabeza_y-42, cx+48, cabeza_y+40), 18 if perfil > 0 else 162,
          122 if perfil > 0 else 262, fill=(54, 37, 31, 220), width=3)
    d.polygon(((cx-50, cabeza_y+42), (cx+52, cabeza_y+42),
               (cx+38, cabeza_y+110), (cx-34, cabeza_y+112)), fill=(78, 49, 36, 250))
    # túnica y manto
    d.polygon(((cx-82, 830), (cx+82, 830), (cx+220, 1510), (cx-235, 1510)), fill=MARFIL+(250,))
    if lado == "derecha":
        d.polygon(((cx+12, 835), (cx+115, 875), (cx+205, 1510), (cx-12, 1510), (cx-85, 1000)),
                  fill=ROJO_MANTO+(242,))
    else:
        d.polygon(((cx-12, 835), (cx-115, 875), (cx-205, 1510), (cx+12, 1510), (cx+85, 1000)),
                  fill=ROJO_MANTO+(242,))
    d.line((cx, 850, cx-30*perfil, 1470), fill=ORO+(60,), width=4)


def _envolver(draw, texto, fuente, max_ancho, max_lineas):
    palabras = re.sub(r"\s+", " ", (texto or "").replace("\n", " ")).strip().split()
    lineas, linea = [], ""
    for palabra in palabras:
        prueba = (linea + " " + palabra).strip()
        if linea and draw.textlength(prueba, font=fuente) > max_ancho:
            lineas.append(linea)
            linea = palabra
        else:
            linea = prueba
    if linea:
        lineas.append(linea)
    if len(lineas) > max_lineas:
        lineas = lineas[:max_lineas]
        lineas[-1] = lineas[-1].rstrip(".,;:!?") + "…"
    return lineas


def _texto_centrado(draw, lineas, y, fuente, color, interlineado, sombra=5):
    for linea in lineas:
        caja = draw.textbbox((0, 0), linea, font=fuente, stroke_width=1)
        x = (W - (caja[2] - caja[0])) / 2
        draw.text((x+sombra, y+sombra), linea, font=fuente, fill=(0, 0, 0, 205), stroke_width=2)
        draw.text((x, y), linea, font=fuente, fill=color, stroke_width=1, stroke_fill=(25, 19, 14))
        y += interlineado
    return y


def _vineta(img):
    mascara = Image.new("L", (W, H), 0)
    p = mascara.load()
    for y in range(H):
        for x in range(W):
            borde = min(x, W-1-x, y, H-1-y)
            p[x, y] = int(170 * max(0, 1 - borde / 190) ** 1.7)
    return Image.composite(Image.new("RGB", (W, H), (0, 0, 0)), img,
                           mascara.filter(ImageFilter.GaussianBlur(18)))


def crear_portada_corto(cita_es, fiesta_liturgica, gancho_pantalla, subtitulo,
                         carpeta, fecha_iso=None, nombre_archivo="thumbnail_vertical.png"):
    fecha_iso = fecha_iso or date.today().isoformat()
    contexto = " ".join((cita_es or "", fiesta_liturgica or "", gancho_pantalla or "", subtitulo or ""))
    semilla = _semilla(fecha_iso, contexto)
    escena = _escena(contexto)
    lado = "derecha" if semilla % 2 else "izquierda"

    img = _degradado()
    img = _eje_de_luz(img, 660 if lado == "derecha" else 420)
    _motivo(img, escena, semilla)
    _jesus(img, lado)
    img = _vineta(img)
    draw = ImageDraw.Draw(img, "RGBA")

    # Marco sobrio y católico; deja respirar la composición en móvil.
    draw.rounded_rectangle((34, 34, W-34, H-34), radius=18, outline=ORO+(170,), width=3)
    draw.line((82, 88, W-82, 88), fill=ORO_CLARO+(90,), width=2)

    f_kicker = _fuente(True, 34)
    f_cita = _fuente(True, 52)
    f_gancho = _fuente(True, 78)
    f_sub = _fuente(False, 40)
    f_marca = _fuente(True, 28)

    kicker = "EVANGELIO DEL DÍA"
    kw = draw.textlength(kicker, font=f_kicker)
    draw.text(((W-kw)/2, 126), kicker, font=f_kicker, fill=ORO_CLARO+(255,))
    draw.line((315, 184, 765, 184), fill=ORO+(125,), width=2)
    _texto_centrado(draw, _envolver(draw, cita_es, f_cita, 880, 2), 215,
                    f_cita, (255, 250, 236, 255), 62, sombra=4)

    # Banda inferior translúcida: el gancho es lo primero que se lee en móvil.
    banda = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    bd = ImageDraw.Draw(banda, "RGBA")
    bd.rounded_rectangle((64, 1290, W-64, 1780), radius=34, fill=(2, 10, 25, 216), outline=ORO+(105,), width=3)
    img = Image.alpha_composite(img.convert("RGBA"), banda).convert("RGB")
    draw = ImageDraw.Draw(img, "RGBA")

    lineas = _envolver(draw, gancho_pantalla, f_gancho, 850, 3)
    alto = len(lineas) * 94
    y = 1385 + max(0, (245 - alto) // 2)
    y = _texto_centrado(draw, lineas, y, f_gancho, (255, 250, 238, 255), 94)
    if subtitulo:
        _texto_centrado(draw, _envolver(draw, subtitulo, f_sub, 820, 1), min(y+18, 1692),
                        f_sub, ORO_CLARO+(255,), 50, sombra=3)

    marca = "VIVA LA FE CATÓLICA TV"
    mw = draw.textlength(marca, font=f_marca)
    draw.text(((W-mw)/2, 1830), marca, font=f_marca, fill=(220, 215, 202, 235))

    os.makedirs(carpeta, exist_ok=True)
    ruta = os.path.join(carpeta, nombre_archivo)
    img.save(ruta, quality=95)
    print("Portada dinámica: escena=%s, composición=%s" % (escena, lado))
    return ruta


if __name__ == "__main__":
    print(crear_portada_corto(
        cita_es="Juan 6,44-51",
        fiesta_liturgica="Jueves de la decimonovena semana",
        gancho_pantalla="YO SOY EL PAN VIVO",
        subtitulo="Una promesa para siempre",
        carpeta=".", fecha_iso="2026-08-27",
        nombre_archivo="_prueba_portada_corto.png"))

