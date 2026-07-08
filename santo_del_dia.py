# -*- coding: utf-8 -*-
"""
Santo del Día - Viva la Fe Católica TV
=======================================

Determina el santo/fiesta que corresponde a la fecha (hoy por defecto,
según hora de Nueva York), y usa la API de Claude para generar:
  - El nombre en español (San/Santa + nombre)
  - Un subtítulo corto (epíteto)
  - Un "gancho" de 2 líneas para el thumbnail
  - Una biografía breve, ORIGINAL (basada en el conocimiento general de
    Claude, no copiada de ningún sitio) lista para narrar

Uso:
    python santo_del_dia.py                # santo de hoy
    python santo_del_dia.py 2026-08-11      # santo de una fecha específica

Salida: output_santo/santo_<fecha>.json
"""

import json
import os
import sys
from datetime import date, datetime

try:
    from zoneinfo import ZoneInfo
    _ZONA_NY = ZoneInfo("America/New_York")
except Exception:
    _ZONA_NY = None

import anthropic

from santo_rotativo import santo_rotativo

MODELO = "claude-sonnet-5"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output_santo")

SYSTEM_PROMPT = """Sos un guionista católico para el canal de YouTube \
"Viva la Fe Católica TV", dirigido a una audiencia católica \
latinoamericana, mayormente de 55 años en adelante, en México y Estados \
Unidos.

Te doy el nombre de un santo/fiesta católica (ya en español), y vos \
generás un paquete completo, usando tu conocimiento general sobre esa \
persona o fiesta -- NUNCA copies ni parafrasees de cerca ningún sitio o \
libro en particular, escribís con tus propias palabras.

Devolvé SOLO un objeto JSON (nada de texto antes o después), con estas \
claves exactas:

{
  "subtitulo": "un epíteto corto, 3-6 palabras (ej. 'Apóstol de las Indias')",
  "gancho": "una frase de gancho para el thumbnail, en 2 líneas separadas \
por \\n, máximo ~10 palabras por línea, llamativa pero reverente",
  "biografia": "150-220 palabras, en español neutro y cálido, con la \
vida/importancia de este santo o el significado de esta fiesta. Si es \
una fiesta del Señor o de la Virgen (no una persona con biografía), \
explicá el significado teológico/histórico de la fiesta en su lugar. \
Terminá con una invitación breve a vivir esa virtud o a la oración."
}

Reglas importantes:
- Si NO estás seguro de un dato específico (fecha exacta, lugar preciso, \
detalle biográfico puntual), no lo inventes -- quedate en generalidades \
conocidas y ampliamente documentadas sobre esa persona/fiesta.
- Tono pastoral, cercano, nunca académico ni frío.
- Nunca uses comillas dobles dentro de los valores del JSON (usá comillas \
simples si hace falta citar algo)."""


def fecha_hoy_ny():
    if _ZONA_NY is not None:
        return datetime.now(_ZONA_NY).date()
    return date.today()


def extraer_texto(mensaje):
    """Devuelve el texto de la respuesta de Claude, buscando el bloque de
    tipo 'text' en vez de asumir que es el primer bloque (content[0]).
    Necesario porque el modelo puede devolver primero un bloque de
    'thinking' (razonamiento interno) antes del bloque de texto real."""
    for bloque in mensaje.content:
        if getattr(bloque, "type", None) == "text":
            return bloque.text.strip()
    raise RuntimeError(
        "La respuesta de Claude no incluyó ningún bloque de texto "
        f"(tipos recibidos: {[getattr(b, 'type', '?') for b in mensaje.content]})."
    )


def generar_contenido_santo(nombre_es):
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("Falta la variable de entorno ANTHROPIC_API_KEY.")

    client = anthropic.Anthropic(api_key=api_key)
    mensaje = client.messages.create(
        model=MODELO,
        max_tokens=800,
        system=SYSTEM_PROMPT,
        messages=[
            {"role": "user", "content": f"Santo/fiesta: {nombre_es}"}
        ],
    )
    texto = extraer_texto(mensaje)
    texto = texto.replace("```json", "").replace("```", "").strip()
    return json.loads(texto)


def main():
    fecha_str = sys.argv[1] if len(sys.argv) > 1 else fecha_hoy_ny().isoformat()

    info = santo_rotativo(fecha_str)
    if not info:
        print("El banco de santos (data/pool_santos.json) está vacío. "
              "Corré descargar_fotos_wikitolica.py primero.")
        sys.exit(1)

    print(f"Fecha: {fecha_str}")
    print(f"Santo del día (rotativo): {info['nombre_es']}")

    try:
        contenido = generar_contenido_santo(info["nombre_es"])
    except Exception as e:
        print(f"[ERROR] Falló la generación de contenido con Claude: {e}")
        sys.exit(1)

    resultado = {
        "fecha": fecha_str,
        "nombre_en": info["nombre_en"],
        "nombre_limpio_en": info["nombre_limpio_en"],
        "nombre_es": info["nombre_es"],
        "foto": info.get("foto"),
        "subtitulo": contenido["subtitulo"],
        "gancho": contenido["gancho"],
        "biografia": contenido["biografia"],
    }

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_path = os.path.join(OUTPUT_DIR, f"santo_{fecha_str}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)

    print(f"\n{info['nombre_es']} — {contenido['subtitulo']}")
    print(f"Gancho: {contenido['gancho']}")
    print(f"\nBiografía:\n{contenido['biografia']}")
    print(f"\nGuardado en: {out_path}")


if __name__ == "__main__":
    main()
