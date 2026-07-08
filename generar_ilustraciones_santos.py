#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generar_ilustraciones_santos.py
--------------------------------
Genera ILUSTRACIONES de santos con la API de imágenes de OpenAI (GPT Image),
para los santos del pool que TODAVÍA NO tienen foto real.

Estructura esperada del pool (dict, no lista):
{
  "Bernardine of Siena": {"foto": "Bernardine of Siena.jpg", "nombre_es": "San Bernardino de Siena"},
  "Ignatius of Loyola":  {"foto": "Ignatius of Loyola.jpg",  "nombre_es": "San Ignacio de Loyola"},
  "Algun Santo Sin Foto": {"nombre_es": "San Alguien"}   <- este SÍ es candidato
}

Regla de oro (definida por el proyecto):
  - Un santo es candidato a ilustración SOLO si no tiene "foto" (o está vacío).
  - Antes de generar nada, el script SIEMPRE imprime la lista completa de
    candidatos para que el usuario la revise a simple vista: si algún santo
    moderno con rostro real documentado se coló ahí (porque Wikitólica no
    encontró su foto), el usuario lo excluye a mano con --excluir antes de
    confirmar el gasto.
  - Nunca se sobreescribe un santo que ya tenga "foto".

La imagen se marca en el JSON con  "origen": "ilustracion_ia"  para que
siempre sea transparente que es una representación artística, no una foto,
y se guarda también en "foto" para que el resto del pipeline la use igual
que una foto real.

Uso típico (protegiendo tu crédito):
    export OPENAI_API_KEY="sk-..."
    # 1) Ver la lista completa de candidatos y el costo, SIN gastar:
    python generar_ilustraciones_santos.py --dry-run
    # 2) Probar con UN solo santo:
    python generar_ilustraciones_santos.py --solo "Ignatius of Loyola"
    # 3) Generar de a poco (ej. 10 por corrida):
    python generar_ilustraciones_santos.py --limite 10
    # 4) Excluir santos puntuales aunque no tengan foto (modernos, etc.):
    python generar_ilustraciones_santos.py --excluir "Juan Pablo II,Padre Pio"
"""

import argparse
import base64
import json
import os
import re
import shutil
import sys
import time
from datetime import datetime

# --------------------------------------------------------------------------- #
# Configuración por defecto  (todo se puede sobreescribir por CLI)
# --------------------------------------------------------------------------- #
RUTA_POOL_DEFAULT   = os.path.join("data", "pool_santos.json")
CARPETA_SALIDA      = os.path.join("assets", "ilustraciones_santos")
MODELO_DEFAULT      = "gpt-image-1" # explícito para costo predecible
CALIDAD_DEFAULT     = "low"         # low ≈ mas barato; medium/high = mejor y mas caro
TAMANO_DEFAULT      = "1024x1536"   # vertical, ideal para figura devocional / movil
PAUSA_ENTRE_LLAMADAS = 1.5          # segundos, para no chocar con rate limits

# Costo aproximado por imagen (USD) segun calidad, imagen cuadrada 1024x1024.
# Para tamaños verticales/horizontales (mas pixeles) sube ~1.5x. Solo orientativo.
COSTO_APROX = {"low": 0.02, "medium": 0.07, "high": 0.19}

# Campos donde puede venir la ruta de la foto real (tu pool usa "foto").
CAMPOS_FOTO = ["foto", "imagen", "foto_real", "ruta_foto", "image", "path_foto"]
# Campos donde puede venir el nombre en español (tu pool usa "nombre_es").
CAMPOS_NOMBRE_ES = ["nombre_es", "nombre", "name_es", "titulo"]
# Campos con atributos/iconografia para enriquecer el prompt (si existieran).
CAMPOS_ATRIBUTOS = ["atributos", "iconografia", "simbolos", "descripcion", "desc"]


# --------------------------------------------------------------------------- #
# Utilidades
# --------------------------------------------------------------------------- #
def slug(texto: str) -> str:
    """Convierte 'San Francisco de Asís' -> 'san_francisco_de_asis'."""
    t = texto.lower().strip()
    reemplazos = (("á", "a"), ("é", "e"), ("í", "i"), ("ó", "o"), ("ú", "u"),
                  ("ü", "u"), ("ñ", "n"))
    for a, b in reemplazos:
        t = t.replace(a, b)
    t = re.sub(r"[^a-z0-9]+", "_", t)
    return t.strip("_")


def primer_campo(dic: dict, campos: list):
    """Devuelve el primer valor no vacío entre una lista de posibles claves."""
    for c in campos:
        if c in dic and dic[c] not in (None, "", []):
            return dic[c]
    return None


def tiene_foto_real(santo: dict) -> bool:
    ruta = primer_campo(santo, CAMPOS_FOTO)
    if not ruta:
        return False
    # Si ya es una ilustracion IA previa, no cuenta como "foto real" para
    # efectos de reportar, pero igual cuenta como "ya resuelto" (no se regenera
    # salvo --forzar). Eso se maneja en evaluar_santo.
    return True


def nombre_es_santo(santo: dict, clave_en: str = "") -> str:
    """Nombre en español para el prompt; si no hay, cae a la clave en inglés."""
    return primer_campo(santo, CAMPOS_NOMBRE_ES) or clave_en or "santo desconocido"


# --------------------------------------------------------------------------- #
# Decisión: ¿este santo es candidato a ilustración?
# --------------------------------------------------------------------------- #
def evaluar_santo(santo: dict, excluidos: set, clave_en: str):
    """
    Devuelve (accion, motivo):
      accion in {"generar", "omitir_foto", "ya_ilustrado", "excluido"}
    """
    if clave_en in excluidos or nombre_es_santo(santo, clave_en) in excluidos:
        return "excluido", "en la lista --excluir (revisión manual del usuario)"

    if santo.get("origen") == "ilustracion_ia":
        return "ya_ilustrado", "ya tiene ilustración IA generada antes"

    if tiene_foto_real(santo):
        return "omitir_foto", "ya tiene foto real (se respeta, nunca se sobreescribe)"

    return "generar", "sin foto en el pool"


# --------------------------------------------------------------------------- #
# Prompt de imagen (arte sacro tradicional, sin texto dentro de la imagen)
# --------------------------------------------------------------------------- #
def construir_prompt(santo: dict, clave_en: str) -> str:
    nombre = nombre_es_santo(santo, clave_en)
    atributos = primer_campo(santo, CAMPOS_ATRIBUTOS)
    prompt = (
        f"Retrato realista y pictórico de {nombre}, estilo icono religioso "
        "católico tradicional. Rostro sereno, mirada contemplativa dirigida "
        "ligeramente hacia arriba o al frente. Aureola dorada sutil detrás "
        "de la cabeza. Fondo ornamentado tipo icono bizantino/renacentista, "
        "con patrones dorados grabados o un halo decorativo circular con "
        "motivos florales o geométricos repujados. Iluminación cálida tipo "
        "claroscuro, con la luz destacando el rostro y las manos. Paleta de "
        "colores dominada por dorados, marrones cálidos, y acentos en rojo "
        "carmesí o dorado en la vestimenta. Textura pictórica realista, "
        "como una pintura al óleo detallada, no plana ni caricaturesca. "
        "Composición vertical, centrada, con el cuerpo desde el pecho hacia "
        "arriba. Importante: la imagen NO debe contener ningún texto, letra "
        "ni palabra, ni marcas de agua."
    )
    if atributos:
        prompt += f" Sostiene o está acompañado de: {atributos}."
    return prompt


# --------------------------------------------------------------------------- #
# Llamada a la API
# --------------------------------------------------------------------------- #
def generar_imagen(client, modelo, prompt, tamano, calidad):
    """Llama a la API y devuelve los bytes PNG de la imagen."""
    kwargs = dict(model=modelo, prompt=prompt, size=tamano, n=1)
    if modelo.startswith("dall-e"):
        # DALL-E usa response_format; GPT Image ya devuelve b64 por defecto.
        kwargs["response_format"] = "b64_json"
    else:
        kwargs["quality"] = calidad  # low/medium/high solo aplica a GPT Image

    resp = client.images.generate(**kwargs)
    dato = resp.data[0]

    b64 = getattr(dato, "b64_json", None)
    if b64:
        return base64.b64decode(b64)

    # Fallback: algunos modelos devuelven URL.
    url = getattr(dato, "url", None)
    if url:
        import urllib.request
        with urllib.request.urlopen(url) as r:
            return r.read()

    raise RuntimeError("La respuesta no trajo ni b64_json ni url.")


# --------------------------------------------------------------------------- #
# Guardado del JSON con respaldo
# --------------------------------------------------------------------------- #
def guardar_pool(ruta_pool, datos):
    if os.path.exists(ruta_pool):
        marca = datetime.now().strftime("%Y%m%d_%H%M%S")
        respaldo = f"{ruta_pool}.bak_{marca}"
        shutil.copy2(ruta_pool, respaldo)
        print(f"   💾 Respaldo del pool -> {respaldo}")
    with open(ruta_pool, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main():
    ap = argparse.ArgumentParser(description="Genera ilustraciones de santos (pre-fotografía) con OpenAI.")
    ap.add_argument("--pool", default=RUTA_POOL_DEFAULT, help="Ruta al pool_santos.json")
    ap.add_argument("--salida", default=CARPETA_SALIDA, help="Carpeta de salida de las imágenes")
    ap.add_argument("--modelo", default=MODELO_DEFAULT, help="Modelo (gpt-image-1, gpt-image-1.5, dall-e-3...)")
    ap.add_argument("--calidad", default=CALIDAD_DEFAULT, choices=["low", "medium", "high"])
    ap.add_argument("--tamano", default=TAMANO_DEFAULT, help="1024x1024, 1024x1536 o 1536x1024")
    ap.add_argument("--limite", type=int, default=0, help="Máx. imágenes a generar en esta corrida (0 = sin tope)")
    ap.add_argument("--solo", default=None, help="Generar solo el santo cuya clave o nombre_es contenga este texto")
    ap.add_argument("--excluir", default="", help="Lista separada por comas de santos a NUNCA ilustrar (clave en o nombre_es)")
    ap.add_argument("--forzar", action="store_true", help="Regenerar aunque ya exista la ilustración")
    ap.add_argument("--dry-run", action="store_true", help="Solo mostrar la lista completa de candidatos y el costo, sin llamar a la API")
    args = ap.parse_args()

    excluidos = {e.strip() for e in args.excluir.split(",") if e.strip()}

    # --- cargar pool ---
    if not os.path.exists(args.pool):
        sys.exit(f"❌ No encuentro el pool: {args.pool}")
    with open(args.pool, encoding="utf-8") as f:
        datos = json.load(f)

    # El pool real es un dict {clave_en: {foto, nombre_es, ...}, ...}.
    # Se soporta también {"santos": {...}} por si en algún momento se anida.
    if isinstance(datos, dict) and "santos" in datos and isinstance(datos["santos"], dict):
        pool = datos["santos"]
    elif isinstance(datos, dict):
        pool = datos
    else:
        sys.exit("❌ Estructura de pool no reconocida (esperaba un dict clave->santo).")

    # --- clasificar ---
    a_generar, resumen = [], {}
    for clave_en, santo in pool.items():
        etiqueta_busqueda = f"{clave_en} {nombre_es_santo(santo, clave_en)}".lower()
        if args.solo and args.solo.lower() not in etiqueta_busqueda:
            continue
        accion, motivo = evaluar_santo(santo, excluidos, clave_en)
        resumen[accion] = resumen.get(accion, 0) + 1
        if accion == "generar":
            destino = os.path.join(args.salida, slug(clave_en) + ".png")
            if os.path.exists(destino) and not args.forzar:
                resumen["ya_ilustrado"] = resumen.get("ya_ilustrado", 0) + 1
                continue
            a_generar.append((clave_en, santo, destino, motivo))

    if args.limite and len(a_generar) > args.limite:
        a_generar = a_generar[:args.limite]

    # --- reporte ---
    print("\n=== CLASIFICACIÓN DEL BANCO ===")
    etiquetas = {
        "omitir_foto":  "Con foto real (se respetan)   ",
        "excluido":     "Excluidos a mano (--excluir)  ",
        "ya_ilustrado": "Ya ilustrados / archivo existe",
        "generar":      "Candidatos a ilustrar         ",
    }
    for k, txt in etiquetas.items():
        print(f"  {txt}: {resumen.get(k, 0)}")
    print(f"\n  -> Se generarían AHORA: {len(a_generar)}")

    costo_unit = COSTO_APROX.get(args.calidad, 0.05)
    factor = 1.5 if args.tamano != "1024x1024" else 1.0
    print(f"  -> Costo estimado: ~${len(a_generar) * costo_unit * factor:.2f} USD "
          f"(≈ ${costo_unit*factor:.3f}/img, calidad {args.calidad}, {args.tamano})")

    if args.dry_run:
        print("\n(dry-run) No se llamó a la API. Revisa la lista completa antes de generar:\n")
        # Lista COMPLETA (no solo los primeros) para que el usuario la revise
        # a simple vista y detecte si algún santo moderno se coló.
        for clave_en, santo, _, _ in a_generar:
            print(f"   • {clave_en}  ->  {nombre_es_santo(santo, clave_en)}")
        print(f"\nSi ves algún santo moderno (con rostro real conocido) en esta lista,")
        print(f"exclúyelo con --excluir \"clave o nombre\" antes de generar.")
        return

    if not a_generar:
        print("\nNada que generar. 👌\n")
        return

    # --- confirmación de gasto ---
    resp = input(f"\n¿Generar {len(a_generar)} imagen(es)? Esto GASTA crédito. [s/N] ").strip().lower()
    if resp not in ("s", "si", "sí", "y", "yes"):
        print("Cancelado.")
        return

    # --- API key + cliente ---
    if not os.environ.get("OPENAI_API_KEY"):
        sys.exit("❌ Falta la variable OPENAI_API_KEY. Expórtala antes de correr.")
    try:
        from openai import OpenAI
    except ImportError:
        sys.exit("❌ Falta el paquete. Instala con:  pip install openai")
    client = OpenAI()

    os.makedirs(args.salida, exist_ok=True)

    # --- generación ---
    ok, err = 0, 0
    for i, (clave_en, santo, destino, motivo) in enumerate(a_generar, 1):
        nombre = nombre_es_santo(santo, clave_en)
        print(f"\n[{i}/{len(a_generar)}] {clave_en}  ->  {nombre}  ({motivo})")
        try:
            prompt = construir_prompt(santo, clave_en)
            imagen = generar_imagen(client, args.modelo, prompt, args.tamano, args.calidad)
            with open(destino, "wb") as f:
                f.write(imagen)
            # Marca el santo en el JSON de forma transparente. Se guarda la
            # ruta RELATIVA al archivo dentro de la carpeta de salida, igual
            # que como vienen las fotos reales (solo nombre de archivo) si
            # ese es el formato de tu pool; ajustamos a ruta completa para
            # evitar ambigüedad entre carpetas de fotos reales e ilustradas.
            santo["foto"] = destino
            santo["origen"] = "ilustracion_ia"
            santo["modelo_ia"] = args.modelo
            santo["generado"] = datetime.now().strftime("%Y-%m-%d")
            ok += 1
            print(f"   ✅ Guardado: {destino}")
            guardar_pool(args.pool, datos)
        except Exception as e:
            err += 1
            print(f"   ⚠️  Error: {e}")
        time.sleep(PAUSA_ENTRE_LLAMADAS)

    print(f"\n=== FIN ===  Generadas: {ok}   Errores: {err}")
    print(f"Costo real aproximado: ~${ok * costo_unit * factor:.2f} USD (revisa el panel de OpenAI para el dato exacto).\n")


if __name__ == "__main__":
    main()
