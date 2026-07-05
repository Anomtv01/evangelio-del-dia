# -*- coding: utf-8 -*-
"""
Descarga el calendario litúrgico completo de un año (santoral) desde la
LiturgicalCalendarAPI (litcal.johnromanodorazio.com) — basada en fuentes
oficiales (Misal Romano, decretos vaticanos), no en sitios random.

Uso:
    python obtener_santoral_anual.py 2026

Salida: data/santoral_2026.json — un diccionario {fecha: [lista de santos]}
listo para que santo.py (o su versión automatizada) elija el santo del día.
"""

import json
import os
import sys
from datetime import datetime

import requests

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

API_URL = "https://litcal.johnromanodorazio.com/api/v5/calendar"


def descargar_calendario(year, locale="en"):
    """NOTA: usamos locale='en' porque el servidor de la API tiene un bug
    (le falta el archivo de santos en español). Los nombres se traducen
    después, en el paso de reescritura con Claude (ver generar_santo_dia.py)."""
    params = {
        "year": year,
        "locale": locale,
        "returntype": "JSON",
    }
    resp = requests.get(API_URL, params=params, timeout=60)
    resp.raise_for_status()
    return resp.json()


def procesar_calendario(data):
    """Convierte la respuesta de la API en {fecha_iso: [nombres]}"""
    santoral = {}

    eventos = data.get("litcal", [])

    for evento in eventos:
        nombre = evento.get("name", "")
        fecha_raw = evento.get("date")  # ej. "2025-12-03T00:00:00+00:00"
        if not fecha_raw:
            continue
        fecha = fecha_raw[:10]  # nos quedamos con "YYYY-MM-DD"

        santoral.setdefault(fecha, []).append({
            "nombre": nombre,
            "grado": evento.get("grade"),
            "grado_texto": evento.get("grade_lcl"),
            "tipo": evento.get("type"),  # "fixed" o "mobile"
            "color": evento.get("color"),
        })

    return santoral


def main():
    year = sys.argv[1] if len(sys.argv) > 1 else str(datetime.now().year)

    print(f"Descargando santoral del año {year} (locale ES)...")
    data = descargar_calendario(year)

    print("Procesando eventos...")
    santoral = procesar_calendario(data)

    os.makedirs(DATA_DIR, exist_ok=True)
    out_path = os.path.join(DATA_DIR, f"santoral_{year}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(santoral, f, ensure_ascii=False, indent=2)

    print(f"Guardado: {out_path}")
    print(f"Total de fechas con datos: {len(santoral)}")

    # Mostrar unos ejemplos para verificar que está bien
    ejemplos = list(santoral.items())[:5]
    print("\nEjemplos:")
    for fecha, lista in ejemplos:
        nombres = ", ".join(e["nombre"] for e in lista)
        print(f"  {fecha}: {nombres}")


if __name__ == "__main__":
    main()
