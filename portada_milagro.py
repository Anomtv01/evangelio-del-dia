# -*- coding: utf-8 -*-
"""
portada_milagro.py — Miniatura del Jueves Eucaristico
======================================================
Monta sobre la imagen de marca (fondo_milagros.png: custodia + caliz + velas)
el texto con los colores exactos del canal:
  - "Milagros" en crema (#F5EDD8)
  - "Eucaristicos" en oro (#D4AF37)
  sobre una caja roja vino (#9B1B1E)
Y debajo, el nombre del milagro de la semana (lugar, pais - año).

El texto va en la mitad IZQUIERDA, sobre la zona negra libre, sin tapar la
custodia de la derecha.

Uso (directo):
    python portada_milagro.py "Eten, Perú" "1649"  salida.png
Como modulo:
    from portada_milagro import crear_portada_milagro
    crear_portada_milagro("Eten, Perú", "1649", "salida.png")
"""

import os
import sys

from PIL import Image, ImageDraw, ImageFont

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FONDO = os.path.join(BASE_DIR, "fondo_milagros.png")

CREMA = (245, 237, 216)
ORO = (212, 175, 55)
ROJO = (155, 27, 30)
BLANCO = (250, 248, 244)

W, H = 1920, 1080


def _font(bold, tam):
    rutas = ([
        "C:\\Windows\\Fonts\\arialbd.ttf",
        os.path.join(BASE_DIR, "fonts", "Lora-Bold.ttf"),
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ] if bold else [
        "C:\\Windows\\Fonts\\arial.ttf",
        os.path.join(BASE_DIR, "fonts", "Lora-Regular.ttf"),
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ])
    for r in rutas:
        try:
            return ImageFont.truetype(r, tam)
        except Exception:                                        # noqa: BLE001
            continue
    return ImageFont.load_default()


def _texto_sombra(d, xy, txt, font, fill, sombra=(0, 0, 0)):
    x, y = xy
    d.text((x + 4, y + 4), txt, font=font, fill=sombra)
    d.text((x, y), txt, font=font, fill=fill)


def crear_portada_milagro(lugar_pais, anio, salida, subtitulo_serie=True):
    """
    lugar_pais: p.ej. "Eten, Perú"
    anio:       p.ej. "1649"
    """
    if os.path.exists(FONDO):
        img = Image.open(FONDO).convert("RGB")
        if img.size != (W, H):
            img = img.resize((W, H), Image.LANCZOS)
    else:
        img = Image.new("RGB", (W, H), (10, 8, 8))

    d = ImageDraw.Draw(img)

    f_grande = _font(True, 150)
    f_med = _font(True, 120)
    f_lugar = _font(True, 82)
    f_anio = _font(True, 60)

    margen = 70

    # --- Caja roja tras "Milagros Eucaristicos" ---
    # medir para dimensionar la caja
    t1, t2 = "Milagros", "Eucarísticos"
    w1 = d.textbbox((0, 0), t1, font=f_grande)[2]
    w2 = d.textbbox((0, 0), t2, font=f_med)[2]
    caja_w = max(w1, w2) + 70
    caja_x0 = margen - 20
    caja_y0 = 330
    caja_y1 = caja_y0 + 300
    d.rectangle([caja_x0, caja_y0, caja_x0 + caja_w, caja_y1], fill=ROJO)

    # --- Titulo de la serie ---
    _texto_sombra(d, (margen, caja_y0 + 20), t1, f_grande, CREMA)
    _texto_sombra(d, (margen, caja_y0 + 165), t2, f_med, ORO)

    # --- Nombre del milagro debajo ---
    y_lugar = caja_y1 + 40
    _texto_sombra(d, (margen, y_lugar), lugar_pais, f_lugar, BLANCO)
    if anio:
        _texto_sombra(d, (margen, y_lugar + 95), "Año " + str(anio), f_anio, ORO)

    img.save(salida)
    return salida


def main():
    if len(sys.argv) >= 3:
        lugar = sys.argv[1]
        anio = sys.argv[2]
        salida = sys.argv[3] if len(sys.argv) > 3 else "portada_milagro.png"
    else:
        lugar, anio, salida = "Eten, Perú", "1649", "portada_milagro.png"
    crear_portada_milagro(lugar, anio, salida)
    print("Portada creada:", salida)


if __name__ == "__main__":
    main()
