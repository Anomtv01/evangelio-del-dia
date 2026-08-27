# -*- coding: utf-8 -*-
"""
portada_corto.py — Portada extravagante del Short diario del Evangelio
=========================================================================
Miniatura VERTICAL (1080x1920) para el Short diario, con un diseño mucho
más elaborado que el genérico de santo_utils.fondo_generico(): rayos
dorados radiantes tipo custodia, halo múltiple, cruz con resplandor, marco
ornamentado doble y tipografía grande de alto contraste — pensado para
destacar en el feed de Shorts, no solo para funcionar.

No depende de fotos curadas por historia (fotos_cortos/): desde que el
pasaje del Short es el Evangelio litúrgico real del día (ver
corto_rotativo.py), cambia todos los días sin repetirse, así que no tiene
sentido mantener un banco de portadas hechas a mano por historia. Todo el
fondo es generado, sin depender de conseguir una imagen para cada pasaje.

Uso:
    from portada_corto import crear_portada_corto
    ruta = crear_portada_corto(
        cita_es="Mateo 5,1-12",
        fiesta_liturgica="",
        gancho_pantalla="¿Qué dijo Jesús\nque nadie esperaba?",
        subtitulo="Las Bienaventuranzas",
        carpeta="output_corto/2026-08-27",
        fecha_iso="2026-08-27",
    )
"""

import hashlib
import math
import os
from datetime import date

from PIL import Image, ImageDraw, ImageFilter, ImageFont

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
W, H = 1080, 1920

# Paletas dramáticas: (nombre, dorado, dorado_claro, tinte_fondo)
PALETAS = [
    ("Oro y grana",     (212, 175, 55), (250, 224, 150), (24, 7, 9)),
    ("Oro y noche",     (212, 175, 55), (250, 224, 150), (7, 9, 22)),
    ("Oro y púrpura",   (212, 175, 55), (250, 224, 150), (18, 7, 22)),
    ("Oro y esmeralda", (212, 175, 55), (250, 224, 150), (5, 17, 13)),
    ("Oro puro",        (230, 190, 60), (255, 235, 170), (16, 12, 4)),
    ("Grana imperial",  (224, 130, 60), (250, 200, 140), (22, 6, 7)),
]


def _paleta_del_dia(fecha_iso):
    idx = int(hashlib.md5(fecha_iso.encode()).hexdigest(), 16) % len(PALETAS)
    return PALETAS[idx]


def _fuentes(escala=1.0):
    """Cadena de respaldo Windows -> fonts/Lora del repo -> DejaVu/Liberation
    del sistema (Linux, GitHub Actions). Sin el último paso, en CI la
    portada sale sin texto legible, en silencio."""
    fdir = os.path.join(BASE_DIR, "fonts")
    bold = [
        "C:\\Windows\\Fonts\\arialbd.ttf",
        os.path.join(fdir, "Lora-Bold.ttf"),
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ]
    reg = [
        "C:\\Windows\\Fonts\\arial.ttf",
        os.path.join(fdir, "Lora-Regular.ttf"),
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ]

    def _t(rutas, tam):
        for r in rutas:
            try:
                return ImageFont.truetype(r, int(tam * escala))
            except Exception:                                    # noqa: BLE001
                continue
        print("[AVISO] No se encontró ninguna fuente TrueType para la "
              "portada del Short; el texto saldrá muy pequeño.")
        return ImageFont.load_default()

    return {
        "kicker": _t(bold, 32),
        "cita":   _t(reg, 38),
        "gancho": _t(bold, 78),
        "sub":    _t(reg, 44),
        "marca":  _t(bold, 30),
    }


def _fondo_base(tinte):
    """Degradado vertical: casi negro arriba, tinte de la paleta abajo."""
    top = (6, 5, 8)
    img = Image.new("RGB", (W, H), top)
    d = ImageDraw.Draw(img)
    for y in range(H):
        t = (y / H) ** 1.4
        d.line([(0, y), (W, y)], fill=(
            int(top[0] + (tinte[0] - top[0]) * t),
            int(top[1] + (tinte[1] - top[1]) * t),
            int(top[2] + (tinte[2] - top[2]) * t)))
    return img


def _rayos_divinos(img, centro, dorado, n_grandes=12, n_finos=28, radio=1600):
    """Rayos radiantes tipo custodia/gloria, con desvanecido hacia afuera."""
    cx, cy = centro
    capa = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(capa, "RGBA")

    for i in range(n_grandes):
        ang = (2 * math.pi / n_grandes) * i
        x2 = cx + radio * math.cos(ang)
        y2 = cy + radio * math.sin(ang)
        for grosor in range(24, 0, -3):
            alpha = int(65 * (grosor / 24))
            d.line([(cx, cy), (x2, y2)], fill=dorado + (alpha,), width=grosor)

    for i in range(n_finos):
        ang = (2 * math.pi / n_finos) * i + (math.pi / n_finos)
        x2 = cx + (radio * 0.7) * math.cos(ang)
        y2 = cy + (radio * 0.7) * math.sin(ang)
        d.line([(cx, cy), (x2, y2)], fill=dorado + (50,), width=3)

    capa = capa.filter(ImageFilter.GaussianBlur(6))
    return Image.alpha_composite(img.convert("RGBA"), capa).convert("RGB")


def _halo(img, centro, color, radio_ext):
    cx, cy = centro
    capa = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(capa, "RGBA")
    for r in range(radio_ext, 40, -8):
        alpha = int(120 * ((radio_ext - r) / (radio_ext - 40)) ** 2)
        d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=color + (alpha,), width=4)
    capa = capa.filter(ImageFilter.GaussianBlur(3))
    return Image.alpha_composite(img.convert("RGBA"), capa).convert("RGB")


def _cruz_resplandor(img, centro, dorado):
    cx, cy = centro
    tam, grosor = 250, 28
    capa = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(capa, "RGBA")
    yh = cy - tam // 6
    d.rectangle([cx - grosor // 2, cy - tam // 2, cx + grosor // 2, cy + tam // 2],
                fill=dorado + (235,))
    d.rectangle([cx - tam // 3, yh - grosor // 2, cx + tam // 3, yh + grosor // 2],
                fill=dorado + (235,))
    glow = capa.filter(ImageFilter.GaussianBlur(16))
    img = Image.alpha_composite(img.convert("RGBA"), glow).convert("RGB")

    d2 = ImageDraw.Draw(img)
    d2.rectangle([cx - grosor // 2, cy - tam // 2, cx + grosor // 2, cy + tam // 2],
                 fill=(255, 250, 236))
    d2.rectangle([cx - tam // 3, yh - grosor // 2, cx + tam // 3, yh + grosor // 2],
                 fill=(255, 250, 236))
    return img


def _vineta(img, profundidad=220, alpha_max=175):
    """Oscurece los BORDES (no un anillo interior): alpha máximo justo en el
    borde de la imagen, decreciendo suavemente hasta 0 hacia el interior."""
    capa = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(capa)
    for i in range(profundidad):
        alpha = int(alpha_max * ((profundidad - i) / profundidad) ** 1.6)
        d.rectangle([i, i, W - i, H - i], outline=alpha, width=1)
    capa = capa.filter(ImageFilter.GaussianBlur(3))
    negro = Image.new("RGB", (W, H), (0, 0, 0))
    return Image.composite(negro, img, capa)


def _marco_ornamentado(draw, dorado, dorado_claro, margen_ext=32, margen_int=54):
    draw.rectangle([margen_ext, margen_ext, W - margen_ext, H - margen_ext],
                    outline=dorado, width=3)
    draw.rectangle([margen_int, margen_int, W - margen_int, H - margen_int],
                    outline=dorado, width=1)
    largo = 44
    for x, y, sx, sy in ((margen_int, margen_int, 1, 1),
                          (W - margen_int, margen_int, -1, 1),
                          (margen_int, H - margen_int, 1, -1),
                          (W - margen_int, H - margen_int, -1, -1)):
        draw.line([(x, y), (x + largo * sx, y)], fill=dorado_claro, width=4)
        draw.line([(x, y), (x, y + largo * sy)], fill=dorado_claro, width=4)


def _envolver(draw, texto, fuente, ancho_max):
    palabras = texto.split()
    if not palabras:
        return []
    lineas, actual = [], palabras[0]
    for p in palabras[1:]:
        prueba = actual + " " + p
        if draw.textlength(prueba, font=fuente) <= ancho_max:
            actual = prueba
        else:
            lineas.append(actual)
            actual = p
    lineas.append(actual)
    return lineas


def _texto_centrado_sombra(draw, texto, y, fuente, color, sombra=(0, 0, 0)):
    w = draw.textlength(texto, font=fuente)
    x = (W - w) / 2
    draw.text((x + 4, y + 4), texto, font=fuente, fill=sombra)
    draw.text((x, y), texto, font=fuente, fill=color)


def crear_portada_corto(cita_es, fiesta_liturgica, gancho_pantalla, subtitulo,
                         carpeta, fecha_iso=None, nombre_archivo="thumbnail_vertical.png"):
    """
    Genera la portada VERTICAL 1080x1920 del Short: fondo con rayos dorados
    y cruz radiante (sin depender de fotos), gancho en tipografía grande,
    marco ornamentado doble. Devuelve la ruta del PNG generado.
    """
    fecha_iso = fecha_iso or date.today().isoformat()
    _nombre_paleta, dorado, dorado_claro, tinte = _paleta_del_dia(fecha_iso)

    centro = (W // 2, int(H * 0.40))

    img = _fondo_base(tinte)
    img = _rayos_divinos(img, centro, dorado)
    img = _halo(img, centro, dorado_claro, radio_ext=560)
    img = _halo(img, centro, dorado, radio_ext=340)
    img = _cruz_resplandor(img, centro, dorado_claro)
    img = _vineta(img)

    draw = ImageDraw.Draw(img)
    _marco_ornamentado(draw, dorado, dorado_claro)

    f = _fuentes()
    margen_x = 96
    ancho_txt = W - margen_x * 2

    # --- kicker + cita litúrgica, arriba ---
    y = 128
    kicker = "EVANGELIO DE HOY"
    kw = sum(draw.textlength(c, font=f["kicker"]) + 4 for c in kicker) - 4
    xk = (W - kw) / 2
    for c in kicker:
        draw.text((xk, y), c, font=f["kicker"], fill=dorado_claro)
        xk += draw.textlength(c, font=f["kicker"]) + 4
    y += 58

    for linea in _envolver(draw, cita_es, f["cita"], ancho_txt)[:2]:
        w = draw.textlength(linea, font=f["cita"])
        draw.text(((W - w) / 2, y), linea, font=f["cita"], fill=(225, 220, 205))
        y += 48

    if fiesta_liturgica:
        for linea in _envolver(draw, fiesta_liturgica, f["cita"], ancho_txt)[:1]:
            w = draw.textlength(linea, font=f["cita"])
            draw.text(((W - w) / 2, y), linea, font=f["cita"], fill=dorado)
            y += 44

    # --- gancho: hasta 2 líneas "de autor" (separadas por \n), cada una
    # reenvuelta si no entra en el ancho disponible ---
    lineas_originales = [l.strip() for l in (gancho_pantalla or "").split("\n") if l.strip()]
    if not lineas_originales:
        lineas_originales = [gancho_pantalla or ""]

    lineas_g = []
    for linea in lineas_originales:
        lineas_g.extend(_envolver(draw, linea, f["gancho"], ancho_txt))

    alto_linea_g = 96
    y_g = int(H * 0.62)

    for ln in lineas_g:
        _texto_centrado_sombra(draw, ln, y_g, f["gancho"], (255, 250, 238))
        y_g += alto_linea_g

    # --- subtítulo + marca, abajo ---
    y_sub = H - 216
    if subtitulo:
        for linea in _envolver(draw, subtitulo, f["sub"], ancho_txt)[:1]:
            w = draw.textlength(linea, font=f["sub"])
            draw.text(((W - w) / 2, y_sub), linea, font=f["sub"], fill=dorado_claro)
            y_sub += 58

    marca = "VIVA LA FE CATÓLICA TV"
    w = draw.textlength(marca, font=f["marca"])
    draw.text(((W - w) / 2, H - 108), marca, font=f["marca"], fill=(200, 195, 180))

    os.makedirs(carpeta, exist_ok=True)
    ruta = os.path.join(carpeta, nombre_archivo)
    img.save(ruta)
    return ruta


if __name__ == "__main__":
    # Prueba rápida: python portada_corto.py
    ruta = crear_portada_corto(
        cita_es="Mateo 5,1-12",
        fiesta_liturgica="",
        gancho_pantalla="¿Qué dijo Jesús\nque nadie esperaba?",
        subtitulo="Las Bienaventuranzas",
        carpeta=".",
        fecha_iso="2026-08-27",
        nombre_archivo="_prueba_portada_corto.png",
    )
    print("Portada de prueba:", ruta)
