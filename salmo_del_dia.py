# -*- coding: utf-8 -*-
"""
Salmo del Dia - Viva la Fe Catolica TV
========================================
CAMBIO CLAVE: antes se pedia una reflexion de 130-170 palabras, lo que con
el texto del salmo daba videos de 2 a 3.5 minutos (RPM ~$0.08). Ahora se
genera una MEDITACION GUIADA de unos 11 minutos:

  1. Introduccion del salmo
  2. Proclamacion del salmo (voz de Escritura)
  3. Meditacion VERSICULO A VERSICULO, alternando voz de Escritura y voz
     que medita  -- es oracion de verdad, no relleno
  4. Reflexion para la vida diaria
  5. Oracion final y cierre

Los videos de mas de 8 minutos admiten anuncios a mitad (mid-roll).

Se conservan las claves del JSON anterior (subtitulo, gancho, reflexion)
para no romper generar_metadata_salmo.py ni subir_youtube_salmo.py.
Se AGREGA la clave "segmentos".

Uso:
    python salmo_del_dia.py                # salmo de hoy
    python salmo_del_dia.py 2026-08-11     # una fecha especifica
"""

import json
import os
import sys
import time
from datetime import date, datetime

try:
    from zoneinfo import ZoneInfo
    _ZONA_NY = ZoneInfo("America/New_York")
except Exception:                                                # noqa: BLE001
    _ZONA_NY = None

import anthropic

MODELO = "claude-sonnet-5"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_DIR = os.path.join(BASE_DIR, "output_salmo")

FECHA_ANCLA = date(2026, 1, 1)
BIBLIA_PATH = os.path.join(DATA_DIR, "biblia_platense.json")

PALABRAS_POR_MINUTO = 167
MINUTOS_OBJETIVO = 11
MINUTOS_MINIMOS = 8.5
PALABRAS_OBJETIVO = int(MINUTOS_OBJETIVO * PALABRAS_POR_MINUTO)

MAX_TOKENS_INTENTOS = [8000, 12000, 16000]

VOZ_ESCRITURA = "escritura"
ROTACION_MEDITACION = ["narrador", "narradora", "narrador_us", "narradora_us"]

SYSTEM_PROMPT = """Sos guionista catolico del canal de YouTube "Viva la Fe \
Catolica TV", dirigido a una audiencia catolica latinoamericana, mayormente \
mujeres de 55 anos en adelante, en Mexico y Estados Unidos. Muchas rezan \
solas en casa y usan el video como su rato de oracion.

Te doy el texto de un Salmo en traduccion catolica y generas una MEDITACION \
GUIADA larga para rezar con el.

REGLAS DE CONTENIDO (obligatorias):
1. Doctrina catolica correcta, nada contrario al Magisterio.
2. No afirmes autoria concreta si no es segura. Podes decir generalidades \
conocidas ('muchos salmos se atribuyen a David', 'a Asaf', 'a los hijos de \
Core'), pero sin inventar datos historicos.
3. Cuando cites versiculos del salmo, usa EXACTAMENTE el texto que te doy, \
sin reescribirlo. El comentario va con tus propias palabras.
4. Tono pastoral, calido y orante. Nunca academico ni frio.
5. Espanol neutro latinoamericano, frases claras y de longitud media (lo lee \
una voz sintetica y lo escuchan personas mayores).
6. ORTOGRAFIA COMPLETA: escribi siempre con tildes y con la letra enye donde \
corresponda. El gancho y el subtitulo se muestran en pantalla, asi que deben \
estar perfectamente escritos.
7. Escribi los numeros en letras ('mil quinientos', no '1500').

ESTRUCTURA (en este orden):
- introduccion: presenta el salmo, su tono y que le pide al corazon (2-3 frases)
- proclamacion: el texto del salmo tal cual te lo doy. Si es muy largo, \
selecciona los versiculos centrales; si es corto, ponlo entero.
- meditacion: la parte principal. Toma versiculos UNO A UNO: primero el \
versiculo tal cual (voz de Escritura) y despues su meditacion (voz que \
medita). Repite ese par al menos seis veces, avanzando por el salmo.
- reflexion: como este salmo consuela o interpela la vida de hoy
- oracion: una oracion final dirigida a Dios, inspirada en el salmo
- cierre: invitacion breve a suscribirse y a dejar la intencion de oracion \
en los comentarios

FORMATO DE SALIDA:
Devolve UNICAMENTE un objeto JSON valido, sin texto antes ni despues y sin \
bloques de markdown:

{
  "subtitulo": "tema del salmo, 3-6 palabras",
  "gancho": "frase para el thumbnail en 2 lineas separadas por \\n, unas 8 \
palabras por linea, llamativa pero reverente",
  "segmentos": [
    {"seccion": "introduccion", "voz": "MEDITACION", "texto": "..."},
    {"seccion": "proclamacion", "voz": "ESCRITURA", "texto": "..."},
    {"seccion": "meditacion", "voz": "ESCRITURA", "texto": "versiculo tal cual"},
    {"seccion": "meditacion", "voz": "MEDITACION", "texto": "su comentario"}
  ]
}

En "voz" pone exactamente el perfil de Escritura o el de meditacion que se \
te indique. No inventes otros nombres."""


def fecha_hoy_ny():
    if _ZONA_NY is not None:
        return datetime.now(_ZONA_NY).date()
    return date.today()


def numero_catolico(h):
    """La Biblia Platense ya usa numeracion catolica (verificado)."""
    return str(h)


def cargar_salmos():
    with open(BIBLIA_PATH, encoding="utf-8") as f:
        biblia = json.load(f)
    libro = next(b for b in biblia["books"] if b["name"] == "Psalms")
    return libro["chapters"]


def _dias_desde_ancla(fecha_iso):
    y, m, d = (int(x) for x in fecha_iso.split("-"))
    return (date(y, m, d) - FECHA_ANCLA).days


def voz_meditacion_del_dia(fecha_iso):
    """Rota la voz que medita, igual que en el Santo del Dia."""
    return ROTACION_MEDITACION[_dias_desde_ancla(fecha_iso) % len(ROTACION_MEDITACION)]


def salmo_rotativo(fecha_iso, salmos):
    """Rotacion secuencial por fecha ancla: nunca repite dos dias seguidos."""
    idx = _dias_desde_ancla(fecha_iso) % len(salmos)
    salmo = salmos[idx]
    versiculos = salmo["verses"]
    texto = " ".join(v["text"].strip() for v in versiculos)
    numerados = "\n".join(
        "%s. %s" % (v.get("verse", i + 1), v["text"].strip())
        for i, v in enumerate(versiculos))
    return {
        "num_hebreo": salmo["chapter"],
        "num_catolico": numero_catolico(salmo["chapter"]),
        "texto": texto,
        "texto_numerado": numerados,
        "cantidad_versiculos": len(versiculos),
        "palabras": len(texto.split()),
    }


def extraer_texto(mensaje):
    for bloque in mensaje.content:
        if getattr(bloque, "type", None) == "text":
            return bloque.text.strip()
    raise RuntimeError("La respuesta de Claude no incluyo bloque de texto.")


def _parsear_json(texto):
    t = texto.replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(t, strict=False)
    except json.JSONDecodeError:
        ini, fin = t.find("{"), t.rfind("}")
        if ini != -1 and fin > ini:
            return json.loads(t[ini:fin + 1], strict=False)
        raise


def contar_palabras(segmentos):
    return sum(len(s.get("texto", "").split()) for s in segmentos)


def _validar(datos, voz_med, voz_esc):
    segs = datos.get("segmentos") or []
    if not segs:
        raise ValueError("El guion no trae segmentos.")
    limpios = []
    for s in segs:
        texto = (s.get("texto") or "").strip()
        if not texto:
            continue
        voz = s.get("voz", voz_med)
        if voz in (voz_esc, "escritura", "ESCRITURA"):
            voz = voz_esc
        else:
            voz = voz_med
        limpios.append({"seccion": s.get("seccion", ""), "voz": voz, "texto": texto})
    if not limpios:
        raise ValueError("Todos los segmentos venian vacios.")
    datos["segmentos"] = limpios
    datos.setdefault("subtitulo", "")
    datos.setdefault("gancho", "")
    return datos


def generar_contenido_salmo(num_cat, info, voz_med, voz_esc):
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise RuntimeError("Falta la variable de entorno ANTHROPIC_API_KEY.")

    client = anthropic.Anthropic()
    peticion = (
        "Salmo %s (%d versiculos):\n\n%s\n\n"
        "---\n"
        "Perfil de voz que proclama la Escritura: \"%s\"\n"
        "Perfil de voz que medita y explica: \"%s\"\n\n"
        "DURACION OBJETIVO: %d minutos de audio narrado, es decir unas %d "
        "palabras sumando TODOS los segmentos (el texto del salmo cuenta "
        "dentro de ese total).\n"
        "Es imprescindible alcanzar esa extension. La meditacion versiculo a "
        "versiculo debe llevar el mayor peso: al menos seis pares de "
        "versiculo y comentario.\n\nDevolve solo el JSON."
        % (num_cat, info["cantidad_versiculos"], info["texto_numerado"],
           voz_esc, voz_med, MINUTOS_OBJETIVO, PALABRAS_OBJETIVO)
    )

    ultimo = None
    for i, max_tokens in enumerate(MAX_TOKENS_INTENTOS, 1):
        print("  [intento %d/%d] max_tokens=%d" % (i, len(MAX_TOKENS_INTENTOS), max_tokens))
        try:
            msg = client.messages.create(
                model=MODELO, max_tokens=max_tokens,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": peticion}])
            if getattr(msg, "stop_reason", None) == "max_tokens":
                print("     respuesta truncada, subiendo tokens...")
                ultimo = "truncado"
                continue
            datos = _validar(_parsear_json(extraer_texto(msg)), voz_med, voz_esc)
            n = contar_palabras(datos["segmentos"])
            print("     OK: %d segmentos, %d palabras, ~%.1f min estimados"
                  % (len(datos["segmentos"]), n, n / PALABRAS_POR_MINUTO))
            return datos
        except json.JSONDecodeError as e:
            ultimo = "JSON invalido: %s" % e
            print("     %s" % ultimo)
        except Exception as e:                                   # noqa: BLE001
            ultimo = e
            print("     error: %s" % e)
            msg_err = str(e).lower()
            if ("overloaded" in msg_err or "529" in msg_err
                    or "rate" in msg_err or "429" in msg_err
                    or "timeout" in msg_err):
                if i < len(MAX_TOKENS_INTENTOS):
                    espera = 20 * i
                    print("     servidor ocupado; esperando %ds..." % espera)
                    time.sleep(espera)

    raise RuntimeError("No se pudo generar la meditacion. Ultimo error: %s" % ultimo)


def ampliar(datos, num_cat, info, voz_med, voz_esc, faltan):
    """Pide mas pares de versiculo y meditacion si quedo corto."""
    client = anthropic.Anthropic()
    hechos = " | ".join(s["texto"][:60] for s in datos["segmentos"]
                        if s["seccion"] == "meditacion")
    peticion = (
        "Meditacion del Salmo %s. Texto completo:\n\n%s\n\n"
        "Ya se meditaron estos pasajes: %s\n\n"
        "Quedo CORTA. Necesito %d palabras ADICIONALES.\n"
        "Genera mas pares de versiculo y meditacion sobre versiculos que aun "
        "NO se hayan tratado, con el mismo estilo. Los versiculos, tal cual "
        "aparecen arriba. No incluyas introduccion, oracion final ni cierre.\n\n"
        "Devolve solo:\n"
        '{"segmentos": [{"seccion": "meditacion", "voz": "%s", "texto": '
        '"versiculo"}, {"seccion": "meditacion", "voz": "%s", "texto": '
        '"comentario"}]}'
        % (num_cat, info["texto_numerado"], hechos[:1200], faltan, voz_esc, voz_med)
    )
    for max_tokens in MAX_TOKENS_INTENTOS:
        try:
            msg = client.messages.create(
                model=MODELO, max_tokens=max_tokens, system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": peticion}])
            if getattr(msg, "stop_reason", None) == "max_tokens":
                continue
            extra = _validar(_parsear_json(extraer_texto(msg)), voz_med, voz_esc)
            segs = datos["segmentos"]
            pos = next((i for i, s in enumerate(segs)
                        if s.get("seccion", "").lower() in
                        ("reflexion", "oracion", "cierre")), len(segs))
            datos["segmentos"] = segs[:pos] + extra["segmentos"] + segs[pos:]
            print("     +%d segmentos (%d palabras)"
                  % (len(extra["segmentos"]), contar_palabras(extra["segmentos"])))
            return datos
        except Exception as e:                                   # noqa: BLE001
            print("     error ampliando: %s" % e)
    print("     no se pudo ampliar; se continua igual")
    return datos


def main():
    fecha_str = sys.argv[1] if len(sys.argv) > 1 else fecha_hoy_ny().isoformat()

    salmos = cargar_salmos()
    info = salmo_rotativo(fecha_str, salmos)
    voz_med = voz_meditacion_del_dia(fecha_str)

    print("Fecha: %s" % fecha_str)
    print("Salmo del dia (catolico): %s (%d versiculos, %d palabras)"
          % (info["num_catolico"], info["cantidad_versiculos"], info["palabras"]))
    print("Voz meditacion: %s | Voz Escritura: %s" % (voz_med, VOZ_ESCRITURA))
    print("Objetivo: %d min (~%d palabras)\n" % (MINUTOS_OBJETIVO, PALABRAS_OBJETIVO))

    try:
        contenido = generar_contenido_salmo(info["num_catolico"], info,
                                            voz_med, VOZ_ESCRITURA)
    except Exception as e:                                       # noqa: BLE001
        print("[ERROR] Fallo la generacion con Claude: %s" % e)
        sys.exit(1)

    n = contar_palabras(contenido["segmentos"])
    minimo = int(MINUTOS_MINIMOS * PALABRAS_POR_MINUTO)
    if n < minimo:
        faltan = minimo - n + 200
        print("\n  Corto (%d palabras). Ampliando +%d..." % (n, faltan))
        contenido = ampliar(contenido, info["num_catolico"], info,
                            voz_med, VOZ_ESCRITURA, faltan)
        n = contar_palabras(contenido["segmentos"])
        print("  Ahora: %d palabras (~%.1f min)" % (n, n / PALABRAS_POR_MINUTO))

    reflexion = " ".join(s["texto"] for s in contenido["segmentos"]
                         if s["seccion"] in ("reflexion", "introduccion"))
    if not reflexion:
        reflexion = " ".join(s["texto"] for s in contenido["segmentos"])[:1200]

    resultado = {
        "fecha": fecha_str,
        "num_catolico": info["num_catolico"],
        "num_hebreo": info["num_hebreo"],
        "texto_salmo": info["texto"],
        "subtitulo": contenido["subtitulo"],
        "gancho": contenido["gancho"],
        "reflexion": reflexion,
        "segmentos": contenido["segmentos"],
        "voz_meditacion": voz_med,
        "voz_escritura": VOZ_ESCRITURA,
        "palabras": n,
        "minutos_estimados": round(n / PALABRAS_POR_MINUTO, 1),
    }

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_path = os.path.join(OUTPUT_DIR, "salmo_%s.json" % fecha_str)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)

    print("\nSalmo %s - %s" % (info["num_catolico"], contenido["subtitulo"]))
    print("Gancho: %s" % contenido["gancho"])
    print("Segmentos: %d | Palabras: %d | Estimado: %s min"
          % (len(contenido["segmentos"]), n, resultado["minutos_estimados"]))
    print("\nGuardado en: %s" % out_path)


if __name__ == "__main__":
    main()
