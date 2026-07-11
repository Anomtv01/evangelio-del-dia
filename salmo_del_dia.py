# -*- coding: utf-8 -*-
"""
Salmo del Día - Viva la Fe Católica TV
========================================

Cada día elige un Salmo distinto (rotando por el día del año, sin repetir
hasta pasar por los 150), toma su texto de la Biblia Platense (Straubinger,
católica, dominio público) que ya está en data/biblia_platense.json, y usa
la API de Claude para generar:
  - Un subtítulo corto (tema del salmo)
  - Un "gancho" de 2 líneas para el thumbnail
  - Una reflexión original (~150 palabras) sobre el salmo

IMPORTANTE sobre la numeración:
El archivo de la Biblia usa numeración HEBREA (masorética). Para el canal
católico mostramos la numeración CATÓLICA (Vulgata), que se desfasa en 1
entre los salmos 10 y 146. La conversión está en numero_catolico().

Uso:
    python salmo_del_dia.py                # salmo de hoy
    python salmo_del_dia.py 2026-08-11      # salmo de una fecha específica

Salida: output_salmo/salmo_<fecha>.json
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

MODELO = "claude-sonnet-5"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_DIR = os.path.join(BASE_DIR, "output_salmo")

# Fecha ancla fija para la rotación (no cambiar en producción).
FECHA_ANCLA = date(2026, 1, 1)
BIBLIA_PATH = os.path.join(DATA_DIR, "biblia_platense.json")

SYSTEM_PROMPT = """Sos un guionista católico para el canal de YouTube \
"Viva la Fe Católica TV", dirigido a una audiencia católica \
latinoamericana, mayormente de 55 años en adelante, en México y Estados \
Unidos.

Te doy el texto de un Salmo (traducción católica), y vos generás un \
paquete para un video devocional, usando tus propias palabras -- NUNCA \
copies ni parafrasees de cerca ningún comentario o sitio en particular.

Devolvé SOLO un objeto JSON (nada de texto antes o después), con estas \
claves exactas:

{
  "subtitulo": "un epíteto corto del tema del salmo, 3-6 palabras (ej. 'El Señor es mi pastor', 'Un canto de confianza')",
  "gancho": "una frase de gancho para el thumbnail, en 2 líneas separadas \
por \\n, máximo ~10 palabras por línea, llamativa pero reverente",
  "reflexion": "130-170 palabras, en español neutro y cálido. Explicá el \
mensaje central del salmo y cómo se aplica a la vida diaria del oyente. \
Estructura: (1) la idea central del salmo, (2) cómo consuela o interpela \
hoy, (3) una invitación breve a la oración o a la confianza en Dios. Tono \
pastoral, cercano, esperanzador."
}

Reglas importantes:
- No inventes datos históricos sobre la autoría que no estés seguro. Podés \
decir generalidades conocidas (muchos salmos son atribuidos a David, otros \
a Asaf, hijos de Coré, etc.) pero no afirmes autoría específica si no es \
segura.
- No repitas literalmente versículos largos del salmo; comentalo con tus \
palabras.
- Tono pastoral, cercano, nunca académico ni frío.
- Nunca uses comillas dobles dentro de los valores del JSON (usá comillas \
simples si hace falta).
- IMPORTANTE: el JSON debe estar COMPLETO y bien cerrado."""


def fecha_hoy_ny():
    if _ZONA_NY is not None:
        return datetime.now(_ZONA_NY).date()
    return date.today()


def numero_catolico(h):
    """El archivo de la Biblia Platense YA usa numeración católica (verificado
    con salmos conocidos: 'El Señor es mi pastor' está en chapter 22, 'Como el
    ciervo' en chapter 41 -- sus números católicos correctos). Por eso el
    número se usa tal cual, sin conversión."""
    return str(h)


def cargar_salmos():
    """Devuelve la lista de los 150 salmos de la Biblia Platense."""
    with open(BIBLIA_PATH, encoding="utf-8") as f:
        biblia = json.load(f)
    libro = next(b for b in biblia["books"] if b["name"] == "Psalms")
    return libro["chapters"]


def salmo_rotativo(fecha_iso, salmos):
    """Elige el salmo que le toca a esta fecha, rotando por los 150.
    Usa los días transcurridos desde una fecha ancla fija, así cada día
    avanza exactamente +1 y dos días seguidos nunca dan el mismo salmo.
    Mismo día siempre da el mismo salmo (determinístico)."""
    y, m, d = (int(x) for x in fecha_iso.split("-"))
    dias_transcurridos = (date(y, m, d) - FECHA_ANCLA).days
    idx = dias_transcurridos % len(salmos)  # 0..149
    salmo = salmos[idx]
    num_hebreo = salmo["chapter"]          # número tal cual el archivo (hebreo)
    num_cat = numero_catolico(num_hebreo)  # número católico para mostrar
    # Texto completo del salmo (unimos los versículos)
    versiculos = salmo["verses"]
    texto = " ".join(v["text"].strip() for v in versiculos)
    return {
        "num_hebreo": num_hebreo,
        "num_catolico": num_cat,
        "texto": texto,
        "cantidad_versiculos": len(versiculos),
    }


def extraer_texto(mensaje):
    """Devuelve el bloque de texto de la respuesta de Claude, ignorando
    posibles bloques de 'thinking' que vengan antes."""
    for bloque in mensaje.content:
        if getattr(bloque, "type", None) == "text":
            return bloque.text.strip()
    raise RuntimeError("La respuesta de Claude no incluyó bloque de texto.")


def _pedir(client, prompt_usuario, max_tokens):
    mensaje = client.messages.create(
        model=MODELO,
        max_tokens=max_tokens,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt_usuario}],
    )
    texto = extraer_texto(mensaje)
    return texto.replace("```json", "").replace("```", "").strip()


def generar_contenido_salmo(num_catolico, texto_salmo):
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("Falta la variable de entorno ANTHROPIC_API_KEY.")

    client = anthropic.Anthropic(api_key=api_key)
    prompt_usuario = f"Salmo {num_catolico}:\n\n{texto_salmo}"

    ultimo_texto = ""
    # Límites crecientes: si el JSON viene truncado (el bloque de
    # "thinking" consume tokens), se reintenta con más espacio.
    for intento, max_tok in enumerate([4000, 6000, 8000], 1):
        try:
            ultimo_texto = _pedir(client, prompt_usuario, max_tok)
            return json.loads(ultimo_texto, strict=False)
        except json.JSONDecodeError as e:
            print(f"[AVISO] Intento {intento}/3: JSON inválido o truncado ({e}). "
                  f"Reintentando con más tokens...")

    print(f"[DEBUG] Último texto recibido (primeros 1500):\n{ultimo_texto[:1500]}")
    raise RuntimeError("Claude no devolvió un JSON válido tras 3 intentos.")


def main():
    fecha_str = sys.argv[1] if len(sys.argv) > 1 else fecha_hoy_ny().isoformat()

    salmos = cargar_salmos()
    info = salmo_rotativo(fecha_str, salmos)

    print(f"Fecha: {fecha_str}")
    print(f"Salmo del día (católico): {info['num_catolico']} "
          f"(hebreo {info['num_hebreo']}, {info['cantidad_versiculos']} versículos)")

    try:
        contenido = generar_contenido_salmo(info["num_catolico"], info["texto"])
    except Exception as e:
        print(f"[ERROR] Falló la generación de contenido con Claude: {e}")
        sys.exit(1)

    resultado = {
        "fecha": fecha_str,
        "num_catolico": info["num_catolico"],
        "num_hebreo": info["num_hebreo"],
        "texto_salmo": info["texto"],
        "subtitulo": contenido["subtitulo"],
        "gancho": contenido["gancho"],
        "reflexion": contenido["reflexion"],
    }

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_path = os.path.join(OUTPUT_DIR, f"salmo_{fecha_str}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)

    print(f"\nSalmo {info['num_catolico']} — {contenido['subtitulo']}")
    print(f"Gancho: {contenido['gancho']}")
    print(f"\nReflexión:\n{contenido['reflexion']}")
    print(f"\nGuardado en: {out_path}")


if __name__ == "__main__":
    main()
