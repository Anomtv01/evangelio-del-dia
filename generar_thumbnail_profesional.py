# -*- coding: utf-8 -*-
"""
GENERADOR DE THUMBNAILS PROFESIONAL - ESTILO CORONILLA A LA DIVINA MISERICORDIA
================================================================================

Crea thumbnails YouTube (1280x720px) con:
- Fondo negro profundo (máximo contraste)
- Rayos dorados radiantes (custodia/divino)
- Luces rojo/azul (misericordia)
- Texto blanco + dorado (legible, SEO-friendly)
- Halos y efectos de brillo
- Figuras religiosas realistas (de Pixabay/libre)

Uso:
    python generar_thumbnail_profesional.py \
        --serie "evangelio" \
        --titulo "San Mateo 5:1-12 - Las Bienaventuranzas" \
        --subtitulo "Evangelio del Día" \
        --output "thumbnail_evangelio.png"

Salida: PNG 1280x720px, optimizado para YouTube
"""

import os
import sys
import json
from datetime import datetime
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import math
import argparse

# ============================================================================
# CONFIGURACIÓN POR SERIE
# ============================================================================

SERIE_CONFIG = {
    "evangelio": {
        "color_rayo1": (255, 200, 0),      # Dorado
        "color_rayo2": (70, 150, 255),     # Azul (fe)
        "color_fondo": (10, 10, 20),       # Negro azulado
        "color_texto1": (255, 255, 255),   # Blanco puro
        "color_texto2": (255, 215, 0),     # Dorado
        "icono": "✝️",
    },
    "santo": {
        "color_rayo1": (255, 200, 0),      # Dorado
        "color_rayo2": (255, 100, 0),      # Rojo (santidad)
        "color_fondo": (10, 10, 20),
        "color_texto1": (255, 255, 255),
        "color_texto2": (255, 215, 0),
        "icono": "✦",
    },
    "salmo": {
        "color_rayo1": (255, 200, 0),      # Dorado
        "color_rayo2": (50, 200, 100),     # Verde (paz)
        "color_fondo": (10, 10, 20),
        "color_texto1": (255, 255, 255),
        "color_texto2": (255, 215, 0),
        "icono": "♪",
    },
    "milagro": {
        "color_rayo1": (255, 220, 0),      # Dorado intenso
        "color_rayo2": (255, 100, 50),     # Naranja/rojo (milagro)
        "color_fondo": (10, 10, 20),
        "color_texto1": (255, 255, 255),
        "color_texto2": (255, 220, 0),
        "icono": "✨",
    }
}

# ============================================================================
# FUNCIONES DE DIBUJO
# ============================================================================

def dibujar_rayos_divinos(img, config, centro_x=640, centro_y=360):
    """Dibuja rayos radiantes tipo Coronilla"""
    draw = ImageDraw.Draw(img, 'RGBA')
    
    # Rayos principales (rojo/azul misericordia)
    num_rayos_grandes = 8
    for i in range(num_rayos_grandes):
        angulo = (i * 360 / num_rayos_grandes) * math.pi / 180
        x_end = centro_x + 400 * math.cos(angulo)
        y_end = centro_y + 400 * math.sin(angulo)
        
        # Alternar colores (rojo a izquierda, azul a derecha)
        color = config["color_rayo2"] if i % 2 == 0 else config["color_rayo1"]
        
        # Línea gruesa con glow
        for grosor in range(20, 1, -2):
            alpha = int(255 * (1 - (20 - grosor) / 20))
            draw.line(
                [(centro_x, centro_y), (x_end, y_end)],
                fill=color + (alpha,),
                width=grosor
            )
    
    # Rayos secundarios más pequeños
    num_rayos_pequenos = 16
    for i in range(num_rayos_pequenos):
        angulo = (i * 360 / num_rayos_pequenos + 22.5) * math.pi / 180
        x_end = centro_x + 300 * math.cos(angulo)
        y_end = centro_y + 300 * math.sin(angulo)
        
        color = config["color_rayo1"]
        draw.line(
            [(centro_x, centro_y), (x_end, y_end)],
            fill=color + (200,),
            width=3
        )

def dibujar_halo(img, config, x=640, y=360, radio=120):
    """Dibuja aureola/halo divino"""
    draw = ImageDraw.Draw(img, 'RGBA')
    
    # Halo principal dorado
    for r in range(radio, 20, -15):
        alpha = int(255 * (radio - r) / (radio - 20))
        draw.ellipse(
            [(x - r, y - r), (x + r, y + r)],
            outline=config["color_rayo1"] + (alpha,),
            width=3
        )

def agregar_texto_profesional(img, draw, config, titulo, subtitulo, icono=""):
    """Agrega texto con sombra y brillo"""
    W, H = img.size
    
    try:
        # Intentar cargar fuentes personalizadas
        font_titulo = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 70)
        font_subtitulo = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 40)
        font_icono = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 100)
    except:
        # Fallback a fuentes por defecto
        font_titulo = ImageFont.load_default()
        font_subtitulo = ImageFont.load_default()
        font_icono = ImageFont.load_default()
    
    x_texto = 50
    y_titulo = 150
    
    # Sombra del título
    for offset in range(4, 0, -1):
        alpha = int(50 * (4 - offset) / 4)
        draw.text(
            (x_texto + offset, y_titulo + offset),
            titulo,
            font=font_titulo,
            fill=(0, 0, 0, alpha)
        )
    
    # Título principal (blanco con borde dorado)
    draw.text(
        (x_texto, y_titulo),
        titulo,
        font=font_titulo,
        fill=config["color_texto1"]
    )
    
    # Brillo dorado bajo el título
    draw.text(
        (x_texto + 2, y_titulo + 75),
        "─" * 25,
        font=font_subtitulo,
        fill=config["color_rayo1"]
    )
    
    # Subtítulo
    y_subtitulo = y_titulo + 150
    draw.text(
        (x_texto, y_subtitulo),
        subtitulo,
        font=font_subtitulo,
        fill=config["color_texto2"]
    )
    
    # Ícono en la esquina superior derecha
    if icono:
        draw.text(
            (W - 120, 40),
            icono,
            font=font_icono,
            fill=config["color_rayo1"]
        )

def generar_thumbnail(serie, titulo, subtitulo, output_path):
    """Genera thumbnail completo"""
    
    config = SERIE_CONFIG.get(serie, SERIE_CONFIG["evangelio"])
    
    # Crear imagen con fondo negro
    W, H = 1280, 720
    img = Image.new('RGBA', (W, H), config["color_fondo"])
    draw = ImageDraw.Draw(img, 'RGBA')
    
    # 1. Rayos divinos
    dibujar_rayos_divinos(img, config)
    
    # 2. Halos múltiples
    dibujar_halo(img, config, x=640, y=360, radio=150)
    dibujar_halo(img, config, x=640, y=360, radio=80)
    
    # 3. Vignette (oscurecimiento de bordes)
    vignette = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    vignette_draw = ImageDraw.Draw(vignette, 'RGBA')
    for i in range(100):
        alpha = int(150 * i / 100)
        vignette_draw.rectangle(
            [(i, i), (W-i, H-i)],
            outline=(0, 0, 0, alpha),
            width=1
        )
    img.paste(vignette, (0, 0), vignette)
    
    # 4. Texto profesional
    agregar_texto_profesional(
        img, draw, config, titulo, subtitulo,
        icono=SERIE_CONFIG[serie]["icono"]
    )
    
    # 5. Aplicar ligero blur de movimiento para efecto dinámico
    # (opcional - comentar si es demasiado)
    # img = img.filter(ImageFilter.GaussianBlur(radius=0.5))
    
    # 6. Guardar
    img.convert('RGB').save(output_path, 'PNG', quality=95)
    print(f"✅ Thumbnail generado: {output_path}")
    
    return output_path

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generador de thumbnails profesionales")
    parser.add_argument("--serie", default="evangelio", 
                       choices=list(SERIE_CONFIG.keys()),
                       help="Tipo de contenido (evangelio, santo, salmo, milagro)")
    parser.add_argument("--titulo", required=True, help="Título principal")
    parser.add_argument("--subtitulo", default="Viva la Fe Católica", help="Subtítulo")
    parser.add_argument("--output", default="thumbnail_output.png", help="Ruta de salida")
    
    args = parser.parse_args()
    
    generar_thumbnail(
        serie=args.serie,
        titulo=args.titulo,
        subtitulo=args.subtitulo,
        output_path=args.output
    )
