# -*- coding: utf-8 -*-
"""
guion_corto.py — Short diario del Evangelio · Viva la Fe Católica TV
========================================================================
Genera el guion de un Short de YouTube de 2 MINUTOS (~330 palabras) sobre
la historia del Evangelio del día (corto_rotativo.py), con estructura
pensada para retener desde el primer segundo: gancho de curiosidad, relato
dramatizado (con la voz de Jesús o del personaje en primera persona cuando
corresponde), y un cierre breve con aplicación a la vida diaria y llamado a
suscribirse.

Se apoya en el TEXTO BÍBLICO REAL (Biblia Platense, dominio público) que le
pasa corto_rotativo.py, así el relato nunca inventa hechos que no estén en
el pasaje.

Uso:
    python guion_corto.py                # short de hoy
    python guion_corto.py 2026-09-05     # una fecha concreta
"""

import json
import os
import re
import sys
from datetime import date, datetime

try:
    from zoneinfo import ZoneInfo
    _ZONA_NY = ZoneInfo("America/New_York")
except Exception:                                                # noqa: BLE001
    _ZONA_NY = None

import anthropic

from corto_rotativo import historia_del_dia

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output_corto")

MODELO = "claude-sonnet-5"
MAX_TOKENS_INTENTOS = [2000, 3000, 4000]

PALABRAS_POR_MINUTO = 167          # medido con edge-tts real (mismo valor
                                    # que usan santo_del_dia.py y salmo_del_dia.py)
MINUTOS_OBJETIVO = 2.0
PALABRAS_OBJETIVO = int(MINUTOS_OBJETIVO * PALABRAS_POR_MINUTO)   # ~334

VOCES_PERSONAJE = ("jesus", "testigo")

# ---------------------------------------------------------------------------
# IMPORTANTE: este prompt va escrito CON TILDES a propósito.
# El modelo imita el estilo del texto que recibe: si las instrucciones van
# sin tildes, el guion sale sin tildes por más que se lo pidamos.
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """Sos guionista católico del canal de YouTube "Viva la Fe \
Católica TV", dirigido a una audiencia católica latinoamericana, mayormente \
mujeres de 55 años en adelante, en México y Estados Unidos. Esta serie \
publica UN SHORT CADA DÍA, dramatizando una historia del Evangelio.

Te doy el TEXTO BÍBLICO REAL del pasaje (Biblia Platense, versión católica \
de dominio público). Basate en ese texto para los hechos: quién dijo qué, \
qué ocurrió y en qué orden. Podés dramatizar el tono y el ritmo, pero NUNCA \
inventes hechos, personajes o diálogos que contradigan el texto.

REGLAS DE CONTENIDO (obligatorias):
1. FIDELIDAD: los hechos y las palabras clave salen del texto bíblico que te \
doy. Podés parafrasear para que suene natural narrado en voz alta, pero no \
alterés el sentido.
2. FORMATO VIRAL DE SHORT (así se enganchan los primeros tres segundos, que \
son los que deciden si alguien sigue viendo):
   - GANCHO: arranca con una pregunta o una afirmación intrigante sobre el \
personaje o el momento, SIN spoilear el desenlace todavía. Frases cortas.
   - RELATO: contá la historia en presente o pasado narrativo, con ritmo \
ágil. Cuando el texto bíblico registra que un personaje habla (Jesús, la \
samaritana, el ciego, etc.), dale esa línea en PRIMERA PERSONA a ese \
personaje en vez de narrarla indirectamente: eso es lo que sostiene la \
atención.
   - GIRO O REVELACIÓN: el momento más fuerte del pasaje (el milagro, la \
confesión, el perdón, la respuesta que nadie esperaba).
   - CIERRE: una aplicación breve a la vida de hoy (una sola idea, en una o \
dos frases) y una invitación cálida a suscribirse a Viva la Fe Católica TV. \
NO uses la palabra "conclusión" ni suene a sermón.
3. Tono cálido, cercano, con emoción contenida; nunca sensacionalista.
4. Español neutro latinoamericano, frases cortas y claras (lo lee una voz \
sintética a un ritmo rápido de Short).
5. ORTOGRAFÍA PERFECTA (MUY IMPORTANTE): tu respuesta debe llevar TODAS las \
tildes y la letra ñ donde correspondan. Escribí correctamente: "año", \
"México", "corazón", "apareció", "señor", "días", "según", "también", \
"después", "más", "así", "aún", "está", "había". Esto es obligatorio en \
TODO el texto, con especial cuidado en el gancho, que se muestra en \
pantalla. Un texto sin tildes se ve mal escrito y la voz sintética lo \
pronuncia mal.
6. Escribí los números en letras ('tres días', no '3 días').
7. NO repitas literalmente frases largas del texto bíblico palabra por \
palabra salvo las líneas de diálogo directo más importantes; el resto, \
narralo con tus propias palabras mantenendo el sentido exacto.

DURACIÓN OBJETIVO: 2 minutos de audio narrado, es decir unas 330 palabras \
sumando TODOS los segmentos. Es un Short: tiene que ser compacto y rápido, \
sin relleno.

FORMATO DE SALIDA:
Devolvé ÚNICAMENTE un objeto JSON válido, sin texto antes ni después y sin \
bloques de markdown:

{
  "subtitulo": "referencia breve del pasaje, 3-6 palabras (ej: 'Juan 4, el \
pozo de Jacob')",
  "gancho_pantalla": "frase para la miniatura en 2 líneas separadas por \\n, \
unas 6-7 palabras por línea, intrigante pero reverente",
  "segmentos": [
    {"seccion": "gancho", "voz": "NARRACION", "texto": "..."},
    {"seccion": "relato", "voz": "NARRACION", "texto": "..."},
    {"seccion": "relato", "voz": "jesus", "texto": "..."},
    {"seccion": "giro", "voz": "NARRACION", "texto": "..."},
    {"seccion": "cierre", "voz": "NARRACION", "texto": "..."}
  ]
}

En "voz" poné "NARRACION" para el narrador, "jesus" cuando habla Jesús en \
primera persona, o "testigo" cuando habla cualquier otro personaje en \
primera persona (la samaritana, el ciego, el padre del hijo pródigo, etc.). \
No inventes otros nombres de voz."""


# ---------------------------------------------------------------------------
# Red de seguridad ortográfica (misma lista que usa milagro_del_dia.py, para
# que el Short mantenga la misma calidad de escritura que el resto del canal).
# ---------------------------------------------------------------------------
_CORRECCIONES = {
    "ano": "año", "anos": "años",
    "nino": "niño", "ninos": "niños", "nina": "niña", "ninas": "niñas",
    "senor": "señor", "senora": "señora", "senores": "señores",
    "manana": "mañana", "compania": "compañía",
    "pequeno": "pequeño", "pequena": "pequeña",
    "pequenos": "pequeños", "pequenas": "pequeñas",
    "espanol": "español", "espanola": "española",
    "ensena": "enseña", "ensenanza": "enseñanza",
    "sueno": "sueño", "montana": "montaña", "extrano": "extraño",
    "Mexico": "México", "Peru": "Perú", "Jerusalen": "Jerusalén",
    "Jesus": "Jesús", "Maria": "María", "Jose": "José",
    "corazon": "corazón", "razon": "razón", "ocasion": "ocasión",
    "tradicion": "tradición", "situacion": "situación", "atencion": "atención",
    "oracion": "oración", "devocion": "devoción", "veneracion": "veneración",
    "salvacion": "salvación", "compasion": "compasión", "conversion": "conversión",
    "dia": "día", "dias": "días", "aqui": "aquí", "alli": "allí",
    "asi": "así", "mas": "más", "segun": "según", "aun": "aún",
    "tambien": "también", "despues": "después", "jamas": "jamás",
    "ademas": "además", "detras": "detrás", "atras": "atrás",
    "esta": "está", "estan": "están", "habia": "había", "habian": "habían",
    "seria": "sería", "podria": "podría", "tenia": "tenía",
    "queria": "quería", "sabia": "sabía", "creia": "creía",
    "aparecio": "apareció", "sucedio": "sucedió", "ocurrio": "ocurrió",
    "reconocio": "reconoció", "encontro": "encontró", "llego": "llegó",
    "quedo": "quedó", "volvio": "volvió", "decidio": "decidió",
    "sintio": "sintió", "murio": "murió", "nacio": "nació",
    "cayo": "cayó", "convirtio": "convirtió", "perdono": "perdonó",
    "sano": "sanó", "curo": "curó", "salvo": "salvó", "escucho": "escuchó",
    "publico": "público", "unico": "único", "ultimo": "último",
    "proximo": "próximo", "facil": "fácil", "dificil": "difícil",
}


def _corregir_ortografia(texto):
    if not texto:
        return texto
    for sin, con in _CORRECCIONES.items():
        if sin == con:
            continue
        texto = re.sub(r"\b%s\b" % re.escape(sin), con, texto)
        texto = re.sub(r"\b%s\b" % re.escape(sin.capitalize()),
                       con.capitalize(), texto)
    return texto


def fecha_hoy_ny():
    if _ZONA_NY is not None:
        return datetime.now(_ZONA_NY).date()
    return date.today()


def extraer_texto(mensaje):
    for bloque in mensaje.content:
        if getattr(bloque, "type", None) == "text":
            return bloque.text.strip()
    raise RuntimeError("La respuesta de Claude no incluyó ningún bloque de texto.")


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


def _validar(datos):
    segs = datos.get("segmentos") or []
    if not segs:
        raise ValueError("El guion no trae segmentos.")
    limpios = []
    for s in segs:
        texto = _corregir_ortografia((s.get("texto") or "").strip())
        if not texto:
            continue
        voz = s.get("voz", "NARRACION")
        if voz not in VOCES_PERSONAJE:
            voz = "NARRACION"
        limpios.append({"seccion": s.get("seccion", ""), "voz": voz, "texto": texto})
    if not limpios:
        raise ValueError("Todos los segmentos vinieron vacíos.")
    datos["segmentos"] = limpios
    datos["subtitulo"] = _corregir_ortografia(datos.get("subtitulo", ""))
    datos["gancho_pantalla"] = _corregir_ortografia(datos.get("gancho_pantalla", ""))
    return datos


def construir_peticion(entrada):
    return (
        "Pasaje: %s (%s)\n\n"
        "TEXTO BÍBLICO (Biblia Platense):\n\"\"\"\n%s\n\"\"\"\n\n"
        "DURACIÓN OBJETIVO: %d minutos, unas %d palabras sumando TODOS los "
        "segmentos.\n\n"
        "Recordá: el texto debe llevar todas las tildes y la ñ donde "
        "correspondan.\n\n"
        "Devolvé solo el JSON."
        % (entrada["titulo"], entrada["cita_es"], entrada["texto_biblico"],
           MINUTOS_OBJETIVO, PALABRAS_OBJETIVO)
    )


def generar_contenido(entrada):
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise RuntimeError("Falta la variable de entorno ANTHROPIC_API_KEY.")

    client = anthropic.Anthropic()
    peticion = construir_peticion(entrada)

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

            datos = _validar(_parsear_json(extraer_texto(msg)))
            n = contar_palabras(datos["segmentos"])
            print("     OK: %d segmentos, %d palabras, ~%.1f min estimados"
                  % (len(datos["segmentos"]), n, n / PALABRAS_POR_MINUTO))
            return datos

        except json.JSONDecodeError as e:
            ultimo = "JSON inválido: %s" % e
            print("     %s" % ultimo)
        except Exception as e:                                   # noqa: BLE001
            ultimo = e
            print("     error: %s" % e)

    raise RuntimeError("No se pudo generar el guion. Último error: %s" % ultimo)


def main():
    fecha_str = sys.argv[1] if len(sys.argv) > 1 else fecha_hoy_ny().isoformat()
    fecha_obj = date.fromisoformat(fecha_str)

    entrada = historia_del_dia(fecha_obj)
    if not entrada:
        print("[ERROR] No se pudo elegir una historia para %s." % fecha_str)
        sys.exit(1)

    print("=== Short del Evangelio para %s ===" % fecha_str)
    print("Historia: %s (%s)" % (entrada["titulo"], entrada["cita_es"]))
    print("Voz del narrador: %s\n" % entrada["voz"])

    try:
        contenido = generar_contenido(entrada)
    except RuntimeError as e:
        print("[ERROR] %s" % e)
        sys.exit(1)

    data = {
        "fecha": fecha_str,
        "clave": entrada["clave"],
        "titulo_historia": entrada["titulo"],
        "cita_es": entrada["cita_es"],
        "categoria": entrada.get("categoria"),
        "voz_narracion": entrada["voz"],
        "voz_narracion_nombre": entrada.get("voz_nombre"),
        "subtitulo": contenido.get("subtitulo", ""),
        "gancho_pantalla": contenido.get("gancho_pantalla", ""),
        "segmentos": contenido["segmentos"],
    }
    n = contar_palabras(data["segmentos"])
    data["palabras"] = n
    data["minutos_estimados"] = round(n / PALABRAS_POR_MINUTO, 2)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_path = os.path.join(OUTPUT_DIR, "corto_%s.json" % fecha_str)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print("\nGuardado en: %s" % out_path)


if __name__ == "__main__":
    main()
