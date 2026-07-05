# -*- coding: utf-8 -*-
"""
Recorre el santoral del año (generado por obtener_santoral_anual.py) y
para cada santo busca una imagen de DOMINIO PÚBLICO en Wikimedia Commons
(pinturas, íconos, grabados antiguos - nunca fotografías con copyright
vigente), descargándola a tu carpeta local de fotos para que santo.py
la encuentre automáticamente con su función buscar_foto().

Requiere:
    pip install requests

Uso:
    python descargar_fotos_santoral.py 2026

Salida:
    - Imágenes descargadas en C:\\VivaLaFe\\fotos\\<nombre_santo>.jpg
    - data/fotos_no_encontradas.txt -> lista de santos sin imagen segura
      (probablemente canonizados recientemente, sin arte de dominio público)
"""

import json
import os
import re
import sys
import time

import requests

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
CARPETA_FOTOS = "C:\\VivaLaFe\\fotos"

COMMONS_API = "https://commons.wikimedia.org/w/api.php"

# Licencias que consideramos seguras (dominio público o equivalente).
# Rechazamos cualquier imagen que no matchee claramente con alguna de estas.
LICENCIAS_SEGURAS = [
    "public domain", "pd-old", "pd-art", "pd-us", "pd-1923",
    "cc0", "cc-pd", "no known copyright",
]

# Patrones de nombre que indican grado litúrgico "genérico" (sin santo
# protagonista) - los saltamos al elegir a quién buscarle foto
PATRONES_GENERICOS = re.compile(
    r"^(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday|"
    r"\d+(st|nd|rd|th) (Sunday|Week)|Solemnity of |Ash Wednesday|"
    r"Holy|Easter |Christmas |Ordinary Time)",
    re.IGNORECASE,
)


def limpiar_nombre_archivo(nombre):
    """Convierte 'Saint Francis Xavier, Priest' -> 'Francis Xavier' para
    usar como nombre de archivo (y para que buscar_foto() lo matchee)."""
    n = nombre
    n = re.sub(r"^(Saint|Blessed)\s+", "", n)
    n = re.sub(r",.*$", "", n)  # corta ", Priest", ", Bishop", etc.
    n = n.strip()
    return n


def es_santo_real(nombre):
    """Filtra entradas genéricas (días feriales, tiempos litúrgicos) que
    no representan a una persona/santo en particular."""
    if PATRONES_GENERICOS.match(nombre):
        return False
    if len(nombre) < 3:
        return False
    return True


def cargar_lista_santos(year):
    path = os.path.join(DATA_DIR, f"santoral_{year}.json")
    with open(path, "r", encoding="utf-8") as f:
        santoral = json.load(f)

    nombres_unicos = {}
    for fecha, eventos in santoral.items():
        for e in eventos:
            nombre = e["nombre"]
            if es_santo_real(nombre):
                clave = limpiar_nombre_archivo(nombre)
                nombres_unicos[clave] = nombre  # se queda con la última variante

    return nombres_unicos


def buscar_imagen_commons(nombre_busqueda):
    """Busca en Wikimedia Commons y devuelve (url_imagen, licencia) del
    primer resultado con licencia de dominio público, o (None, None)."""
    params = {
        "action": "query",
        "generator": "search",
        "gsrsearch": f"{nombre_busqueda} painting OR icon OR engraving",
        "gsrnamespace": 6,  # namespace File:
        "gsrlimit": 8,
        "prop": "imageinfo",
        "iiprop": "url|extmetadata",
        "format": "json",
    }
    try:
        resp = requests.get(COMMONS_API, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        return None, None

    paginas = data.get("query", {}).get("pages", {})
    for pagina in paginas.values():
        imageinfo = pagina.get("imageinfo")
        if not imageinfo:
            continue
        info = imageinfo[0]
        url = info.get("url", "")
        if not url.lower().endswith((".jpg", ".jpeg", ".png")):
            continue

        extmeta = info.get("extmetadata", {})
        licencia_texto = " ".join([
            str(extmeta.get("LicenseShortName", {}).get("value", "")),
            str(extmeta.get("UsageTerms", {}).get("value", "")),
            str(extmeta.get("Copyrighted", {}).get("value", "")),
        ]).lower()

        if any(seguro in licencia_texto for seguro in LICENCIAS_SEGURAS):
            return url, licencia_texto

    return None, None


def descargar_imagen(url, destino):
    resp = requests.get(url, timeout=60, headers={"User-Agent": "VivaLaFeCatolicaTV/1.0"})
    resp.raise_for_status()
    with open(destino, "wb") as f:
        f.write(resp.content)


def main():
    year = sys.argv[1] if len(sys.argv) > 1 else "2026"

    print(f"Cargando santoral {year}...")
    nombres_unicos = cargar_lista_santos(year)
    print(f"Total de santos únicos a buscar: {len(nombres_unicos)}")

    os.makedirs(CARPETA_FOTOS, exist_ok=True)

    no_encontrados = []
    ya_existentes = 0
    descargados = 0

    for i, (clave, nombre_completo) in enumerate(sorted(nombres_unicos.items()), 1):
        nombre_archivo = re.sub(r'[<>:"/\\|?*]', "", clave).strip()
        destino = os.path.join(CARPETA_FOTOS, f"{nombre_archivo}.jpg")

        if os.path.exists(destino):
            ya_existentes += 1
            continue

        print(f"[{i}/{len(nombres_unicos)}] Buscando: {clave}...")
        url, licencia = buscar_imagen_commons(f"Saint {clave}")

        if not url:
            print(f"   -> No se encontró imagen segura para: {nombre_completo}")
            no_encontrados.append(nombre_completo)
            continue

        try:
            descargar_imagen(url, destino)
            print(f"   -> Descargada ({licencia[:40]}...)")
            descargados += 1
        except Exception as e:
            print(f"   -> Error al descargar: {e}")
            no_encontrados.append(nombre_completo)

        time.sleep(0.5)  # ser considerados con la API de Commons

    os.makedirs(DATA_DIR, exist_ok=True)
    with open(os.path.join(DATA_DIR, "fotos_no_encontradas.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(no_encontrados))

    print(f"\n=== Listo ===")
    print(f"Ya existían: {ya_existentes}")
    print(f"Descargadas ahora: {descargados}")
    print(f"Sin imagen segura: {len(no_encontrados)} (ver data/fotos_no_encontradas.txt)")


if __name__ == "__main__":
    main()
