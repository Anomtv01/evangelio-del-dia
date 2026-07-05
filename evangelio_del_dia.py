# -*- coding: utf-8 -*-
"""
Evangelio del Día - Viva la Fe Católica TV
==========================================

Toma la fecha (hoy por defecto), busca la cita del Evangelio de esa fecha:

  1) Primero en la fuente automática (metadata del leccionario, scrapeada
     de USCCB, sin texto con derechos de autor).
  2) Si esa fuente no tiene la lectura (pasa en ~11% de los días, sobre
     todo en las solemnidades grandes), cae automáticamente al archivo de
     respaldo data/fiestas_especiales.json, generado y verificado a mano
     contra las tablas de Felix Just, S.J. (catholic-resources.org).

En ambos casos, arma el texto completo en español usando la Biblia
Platense (revisión Straubinger), traducción católica de dominio público.

Uso:
    python evangelio_del_dia.py                  # evangelio de hoy
    python evangelio_del_dia.py 2026-12-25        # evangelio de una fecha específica

Salida: un JSON en output/ listo para alimentar el resto del pipeline
(narración ElevenLabs, thumbnail, metadata de YouTube).
"""

import json
import sys
import os
from datetime import date

from citas import parsear_cita, CitaNoReconocida
from libros import normalizar_libro, nombre_espanol
from traducir_fiesta import traducir_fiesta

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CITAS_PATH = os.path.join(BASE_DIR, "data", "citas_diarias.json")
FIESTAS_PATH = os.path.join(BASE_DIR, "data", "fiestas_especiales.json")
BIBLIA_PATH = os.path.join(BASE_DIR, "data", "biblia_platense.json")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")


def cargar_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def cargar_biblia():
    data = cargar_json(BIBLIA_PATH)
    return {libro["name"]: libro for libro in data["books"]}


def obtener_registro_del_dia(citas, fecha_str):
    """Busca en la fuente principal (USCCB scraper). Devuelve
    (cita_texto, feast, lectionary_number) o None si no hay datos."""
    registros = citas.get(fecha_str)
    if not registros:
        return None
    candidatos = [r for r in registros if r.get("mass") == "default" and r.get("readings")]
    if not candidatos:
        candidatos = [r for r in registros if r.get("readings")]
    if not candidatos:
        return None
    r = candidatos[0]
    gospel = r.get("readings", {}).get("gospel")
    if not gospel:
        return None
    return gospel[0]["citation"], traducir_fiesta(r.get("feast", "")), r.get("lectionary_number")


def obtener_registro_de_fiesta(fiestas, fecha_str):
    """Busca en el archivo de respaldo de solemnidades/fiestas grandes.
    Devuelve (cita_texto, feast, None) o None."""
    registros = fiestas.get(fecha_str)
    if not registros:
        return None
    r = registros[0]  # si hay varias (ej. fiesta + domingo de cuaresma), la primera manda
    return r["citation"], r["feast"], None


def extraer_texto_evangelio(biblia_idx, cita_texto):
    libro_raw, capitulo, rangos = parsear_cita(cita_texto)
    libro_en = normalizar_libro(libro_raw)

    libro_data = biblia_idx.get(libro_en)
    if not libro_data:
        raise CitaNoReconocida(f"Libro no encontrado en la Biblia: {libro_en}")

    capitulo_data = next(
        (c for c in libro_data["chapters"] if c["chapter"] == capitulo), None
    )
    if not capitulo_data:
        raise CitaNoReconocida(f"Capítulo no encontrado: {libro_en} {capitulo}")

    versos_por_numero = {v["verse"]: v["text"].strip() for v in capitulo_data["verses"]}

    fragmentos = []
    for v_ini, v_fin in rangos:
        for num in range(v_ini, v_fin + 1):
            if num in versos_por_numero:
                fragmentos.append(versos_por_numero[num])

    if not fragmentos:
        raise CitaNoReconocida(f"Versos no encontrados para: {cita_texto}")

    texto_completo = " ".join(fragmentos)
    v_ini_total = rangos[0][0]
    v_fin_total = rangos[-1][1]
    return libro_en, capitulo, v_ini_total, v_fin_total, texto_completo


def main():
    fecha_str = sys.argv[1] if len(sys.argv) > 1 else date.today().isoformat()

    citas = cargar_json(CITAS_PATH)
    fiestas = cargar_json(FIESTAS_PATH)

    resultado_dia = obtener_registro_del_dia(citas, fecha_str)
    fuente_usada = "citas_diarias (USCCB)"

    if not resultado_dia:
        resultado_dia = obtener_registro_de_fiesta(fiestas, fecha_str)
        fuente_usada = "fiestas_especiales (respaldo manual)"

    if not resultado_dia:
        print(f"No se encontró cita de Evangelio para la fecha {fecha_str} "
              f"(ni en la fuente automática ni en el respaldo de fiestas).")
        sys.exit(1)

    cita_texto, feast, lectionary_number = resultado_dia

    biblia_idx = cargar_biblia()

    try:
        libro_en, capitulo, v_ini, v_fin, texto = extraer_texto_evangelio(
            biblia_idx, cita_texto
        )
    except CitaNoReconocida as e:
        print(f"[AVISO] No se pudo procesar automáticamente la cita '{cita_texto}': {e}")
        print("Este caso necesita revisión manual (cita compuesta o formato no soportado).")
        sys.exit(1)

    libro_es = nombre_espanol(libro_en)
    if v_ini == v_fin:
        cita_es = f"{libro_es} {capitulo},{v_ini}"
    else:
        cita_es = f"{libro_es} {capitulo},{v_ini}-{v_fin}"

    resultado = {
        "fecha": fecha_str,
        "fiesta_liturgica": feast,
        "lectionary_number": lectionary_number,
        "cita_original_en": cita_texto,
        "cita_es": cita_es,
        "libro": libro_es,
        "capitulo": capitulo,
        "verso_inicio": v_ini,
        "verso_fin": v_fin,
        "texto_evangelio": texto,
        "fuente_cita": fuente_usada,
        "fuente_texto": "Biblia Platense (revisión Straubinger) - Dominio Público",
    }

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_path = os.path.join(OUTPUT_DIR, f"evangelio_{fecha_str}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)

    print(f"Fecha: {fecha_str}")
    print(f"Fiesta: {feast}")
    print(f"Cita: {cita_es}  (fuente: {fuente_usada})")
    print()
    print(f"Lectura del Santo Evangelio según San {libro_es}:")
    print(texto)
    print()
    print(f"Guardado en: {out_path}")


if __name__ == "__main__":
    main()
