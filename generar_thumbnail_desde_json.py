# -*- coding: utf-8 -*-
"""
INTEGRADOR DE THUMBNAILS - Lee JSON y genera automáticamente
==============================================================

Lee la metadata JSON de cada video (evangelio, santo, salmo, milagro)
y genera el thumbnail correspondiente automáticamente.

Uso:
    python generar_thumbnail_desde_json.py output/evangelio_2026-08-26.json
    python generar_thumbnail_desde_json.py output/santo_2026-08-26.json
    python generar_thumbnail_desde_json.py output/milagro_2026-08-26.json
    python generar_thumbnail_desde_json.py output/salmo_2026-08-26.json

Salida: Crea PNG en output/thumbnails/
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Importar el generador
from generar_thumbnail_profesional import generar_thumbnail, SERIE_CONFIG

def extraer_serie(ruta_json):
    """Detecta la serie desde el nombre del archivo"""
    nombre = os.path.basename(ruta_json).lower()
    
    if "evangelio" in nombre:
        return "evangelio"
    elif "santo" in nombre:
        return "santo"
    elif "salmo" in nombre:
        return "salmo"
    elif "milagro" in nombre:
        return "milagro"
    else:
        return "evangelio"  # Default

def leer_json(ruta):
    """Lee el archivo JSON de metadata"""
    try:
        with open(ruta, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Error leyendo {ruta}: {e}")
        return None

def generar_desde_json(ruta_json):
    """Genera thumbnail desde JSON"""
    
    print(f"\n📄 Procesando: {ruta_json}")
    
    # Leer JSON
    data = leer_json(ruta_json)
    if not data:
        return False
    
    # Detectar serie
    serie = extraer_serie(ruta_json)
    print(f"📺 Serie detectada: {serie}")
    
    # Extraer campos según la serie
    try:
        if serie == "evangelio":
            titulo = data.get('titulo', 'Evangelio')
            referencia = data.get('referencia', '')
            if referencia:
                titulo = f"{referencia}\n{titulo}"
            subtitulo = "Evangelio del Día"
            
        elif serie == "santo":
            nombre = data.get('nombre', 'Santo')
            fecha = data.get('fecha', '')
            titulo = nombre
            if fecha:
                subtitulo = fecha
            else:
                subtitulo = "Santo del Día"
            
        elif serie == "salmo":
            numero = data.get('numero', '0')
            titulo = f"Salmo {numero}"
            titulo_salmo = data.get('titulo', '')
            if titulo_salmo:
                titulo += f"\n{titulo_salmo}"
            subtitulo = "Salmo del Día"
            
        elif serie == "milagro":
            titulo = data.get('titulo', 'Milagro Eucarístico')
            lugar = data.get('lugar', '')
            if lugar:
                subtitulo = lugar
            else:
                subtitulo = "Jueves Eucarístico"
        else:
            titulo = "Viva la Fe Católica"
            subtitulo = "Contenido religioso"
    
    except Exception as e:
        print(f"⚠️ Error extrayendo campos: {e}")
        titulo = "Viva la Fe Católica"
        subtitulo = serie.capitalize()
    
    # Crear carpeta de salida
    output_dir = os.path.join(os.path.dirname(ruta_json), "thumbnails")
    os.makedirs(output_dir, exist_ok=True)
    
    # Generar nombre de salida
    fecha = os.path.basename(ruta_json).split('_')[-1].replace('.json', '')
    nombre_salida = f"thumbnail_{serie}_{fecha}.png"
    output_path = os.path.join(output_dir, nombre_salida)
    
    print(f"🎨 Generando thumbnail:")
    print(f"   Título: {titulo}")
    print(f"   Subtítulo: {subtitulo}")
    
    # Generar thumbnail
    try:
        generar_thumbnail(
            serie=serie,
            titulo=titulo,
            subtitulo=subtitulo,
            output_path=output_path
        )
        print(f"✅ Saved: {output_path}")
        return True
    except Exception as e:
        print(f"❌ Error generando thumbnail: {e}")
        return False

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    
    if len(sys.argv) < 2:
        print("Uso: python generar_thumbnail_desde_json.py <archivo.json> [archivo2.json ...]")
        print("\nEjemplos:")
        print("  python generar_thumbnail_desde_json.py output/evangelio_2026-08-26.json")
        print("  python generar_thumbnail_desde_json.py output/santo_*.json")
        sys.exit(1)
    
    # Procesar todos los archivos JSON pasados como argumentos
    total = len(sys.argv) - 1
    exitosos = 0
    
    for ruta_json in sys.argv[1:]:
        if generar_desde_json(ruta_json):
            exitosos += 1
    
    print(f"\n{'='*60}")
    print(f"✅ Resultado: {exitosos}/{total} thumbnails generados")
    print(f"{'='*60}")
