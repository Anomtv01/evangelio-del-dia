# -*- coding: utf-8 -*-
"""
Genera una reflexión/comentario ORIGINAL (nunca copiado de un sacerdote o
sitio real) sobre el Evangelio del día, usando la API de Claude (Anthropic).

Requiere la librería oficial:
    pip install anthropic

Y la variable de entorno con tu API key:
    Windows (PowerShell):  $env:ANTHROPIC_API_KEY = "sk-ant-..."
    Windows (permanente):  setx ANTHROPIC_API_KEY "sk-ant-..."

Uso:
    python generar_reflexion.py output/evangelio_2026-07-04.json

Salida: output/reflexion_<fecha>.txt (texto plano, listo para el guion de
narración y para pegar en la descripción de YouTube).
"""

import json
import os
import sys

import anthropic

MODELO = "claude-sonnet-5"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

SYSTEM_PROMPT = """Sos un guionista católico que escribe reflexiones breves y \
pastorales para un canal de YouTube/TikTok llamado "Viva la Fe Católica TV", \
dirigido a una audiencia católica latinoamericana, mayormente de 55 años en \
adelante, en México y Estados Unidos.

Reglas:
- Escribís SIEMPRE en español neutro, cálido y sencillo (nada de tecnicismos \
teológicos innecesarios).
- La reflexión es 100% ORIGINAL, en tus propias palabras. Nunca copiás ni \
parafraseás de cerca ningún comentario, homilía o libro real existente.
- Extensión: 120-180 palabras. Para narración de 1-2 minutos.
- Estructura sugerida: (1) una idea central del pasaje, (2) cómo se aplica a \
la vida diaria del oyente, (3) una invitación breve a la oración o a vivir \
ese mensaje hoy.
- Tono pastoral, cercano, esperanzador. Evitá el tono de sermón severo o \
académico.
- No inventés citas de santos, Papas niautores reales. No agregues datos \
históricos que no estés seguro de que son correctos.
- No repitas literalmente el texto del Evangelio, coméntalo con tus propias \
palabras.
"""


def construir_prompt_usuario(data):
    return f"""Fecha: {data['fecha']}
Fiesta litúrgica: {data.get('fiesta_liturgica', '')}
Cita: {data['cita_es']}

Texto del Evangelio de hoy:
\"\"\"{data['texto_evangelio']}\"\"\"

Escribí la reflexión siguiendo las reglas del sistema."""


def generar_reflexion(data):
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError(
            "No se encontró la variable de entorno ANTHROPIC_API_KEY. "
            "Configurala antes de correr este script (ver comentario arriba)."
        )

    client = anthropic.Anthropic(api_key=api_key)

    mensaje = client.messages.create(
        model=MODELO,
        max_tokens=500,
        system=SYSTEM_PROMPT,
        messages=[
            {"role": "user", "content": construir_prompt_usuario(data)}
        ],
    )

    return mensaje.content[0].text.strip()


def main():
    if len(sys.argv) < 2:
        print("Uso: python generar_reflexion.py output/evangelio_<fecha>.json")
        sys.exit(1)

    json_path = sys.argv[1]
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    try:
        reflexion = generar_reflexion(data)
    except RuntimeError as e:
        print(f"[ERROR] {e}")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Falló la llamada a la API de Claude: {e}")
        sys.exit(1)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_path = os.path.join(OUTPUT_DIR, f"reflexion_{data['fecha']}.txt")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(reflexion)

    print(f"Reflexión ({len(reflexion.split())} palabras):\n")
    print(reflexion)
    print(f"\nGuardado en: {out_path}")


if __name__ == "__main__":
    main()
