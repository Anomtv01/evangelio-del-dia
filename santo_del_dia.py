# -*- coding: utf-8 -*-
"""
Santo del Dia - Viva la Fe Catolica TV
=======================================
CAMBIO CLAVE: antes el prompt pedia "biografia de 150-220 palabras", lo que
daba videos de ~1:30 min. A 167 palabras/min eso son 54-79 segundos. Esos
videos cortos rinden RPM $0.08.

Ahora pide un GUION LARGO POR SEGMENTOS (~1.850 palabras = ~11 min) con
estructura de retencion y voces alternadas (narrador + el santo hablando
en primera persona). Videos de mas de 8 min admiten anuncios a mitad
(mid-roll) y rinden RPM ~$2.03 en este canal.

Se conservan las claves del JSON de salida (subtitulo, gancho, biografia)
para que generar_metadata_santo.py y subir_youtube_santo.py sigan
funcionando sin cambios. Se AGREGA la clave "segmentos".

Uso:
    python santo_del_dia.py                # santo de hoy
    python santo_del_dia.py 2026-08-11     # una fecha especifica
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

from santo_rotativo import santo_rotativo

MODELO = "claude-sonnet-5"

# --- Duracion objetivo -----------------------------------------------------
PALABRAS_POR_MINUTO = 167          # MEDIDO con edge-tts real
MINUTOS_OBJETIVO = 11              # margen sobre el minimo de 8 del mid-roll
MINUTOS_MINIMOS = 8.5
PALABRAS_OBJETIVO = int(MINUTOS_OBJETIVO * PALABRAS_POR_MINUTO)   # ~1837

# El JSON largo no cabe en 2000 tokens: se empieza alto y se sube si trunca
MAX_TOKENS_INTENTOS = [8000, 12000, 16000]

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output_santo")

VOCES_NARRACION = ("narrador", "narradora", "narrador_us", "narradora_us")
VOCES_PERSONAJE = ("santo", "santa", "jesus", "virgen")


SYSTEM_PROMPT = """Sos guionista catolico del canal de YouTube "Viva la Fe \
Catolica TV", dirigido a una audiencia catolica latinoamericana, mayormente \
mujeres de 55 anos en adelante, en Mexico y Estados Unidos.

Escribis usando tu conocimiento general sobre el santo o la fiesta. NUNCA \
copies ni parafrasees de cerca ningun sitio ni libro: escribis con tus \
propias palabras.

REGLAS DE CONTENIDO (obligatorias):
1. RIGOR: solo datos historicos y hagiograficos ampliamente documentados y \
reconocidos por la Iglesia. NO inventes fechas, lugares, milagros ni frases.
2. Si algo pertenece a la tradicion piadosa pero no esta documentado, \
introducilo con 'segun la tradicion' o 'cuenta la piedad popular'.
3. Si NO estas seguro de un dato puntual, quedate en generalidades conocidas.
4. Doctrina catolica correcta, nada contrario al Magisterio.
5. Tono pastoral, calido y reverente. Nunca sensacionalista ni morboso: \
podes narrar el martirio con emocion, pero sin regodearte en lo truculento.
6. Espanol neutro latinoamericano, frases claras y de longitud media (lo lee \
una voz sintetica y lo escuchan personas mayores).
7. Escribi los numeros en letras ('mil quinientos', no '1500') para que la \
voz los lea bien.
8. ORTOGRAFIA COMPLETA: escribi SIEMPRE con tildes y con la letra ñ donde \
corresponda ('años', no 'anos'; 'martirio', 'oracion' lleva tilde: \
'oración'). El texto se muestra en pantalla y lo lee una voz sintetica: sin \
tildes ni ñ, se ve mal escrito y se pronuncia mal. Esto aplica sobre todo al \
'gancho' y al 'subtitulo', que aparecen en la miniatura.
9. Las intervenciones en primera persona del santo deben ser verosimiles y \
coherentes con lo que se sabe de el, presentadas como reconstruccion \
narrativa, no como cita textual documentada.

ESTRUCTURA DEL GUION (en este orden):
- gancho: el momento mas impactante, SIN revelar el desenlace (2-3 frases)
- contexto: epoca, lugar, situacion de la Iglesia y de su familia
- vida: infancia, formacion, como llego a la fe o a su vocacion
- conflicto: la prueba, persecucion, tentacion o conversion
- dialogo: intervenciones donde el santo HABLA en primera persona, \
alternadas con el narrador. Es lo que mas retiene: al menos 5 replicas \
repartidas a lo largo del guion.
- climax: el martirio, el milagro o el momento culminante
- legado: que dejo a la Iglesia, devocion posterior, patronazgo
- aplicacion: que ensena hoy a la vida concreta del espectador
- cierre: invitacion breve a suscribirse y a dejar su intencion de oracion \
en los comentarios

FORMATO DE SALIDA:
Devolve UNICAMENTE un objeto JSON valido, sin texto antes ni despues y sin \
bloques de markdown:

{
  "subtitulo": "epiteto corto, 3-6 palabras",
  "gancho": "frase para el thumbnail en 2 lineas separadas por \\n, maximo \
unas 8 palabras por linea, llamativa pero reverente",
  "segmentos": [
    {"seccion": "gancho", "voz": "NARRACION", "texto": "..."},
    {"seccion": "dialogo", "voz": "PERSONAJE", "texto": "..."}
  ]
}

En cada segmento, "voz" debe ser exactamente el perfil de narracion que se \
te indique, o el perfil de personaje que se te indique cuando el santo \
habla en primera persona. No inventes otros nombres de voz."""


def fecha_hoy_ny():
    if _ZONA_NY is not None:
        return datetime.now(_ZONA_NY).date()
    return date.today()


def extraer_texto(mensaje):
    """Devuelve el bloque de texto (puede venir precedido de 'thinking')."""
    for bloque in mensaje.content:
        if getattr(bloque, "type", None) == "text":
            return bloque.text.strip()
    raise RuntimeError(
        "La respuesta de Claude no incluyo ningun bloque de texto "
        f"(tipos: {[getattr(b, 'type', '?') for b in mensaje.content]}).")


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


def _validar(datos, voz_narracion, voz_personaje):
    """Normaliza voces y descarta segmentos vacios."""
    segs = datos.get("segmentos") or []
    if not segs:
        raise ValueError("El guion no trae segmentos.")

    limpios = []
    for s in segs:
        texto = (s.get("texto") or "").strip()
        if not texto:
            continue
        voz = s.get("voz", voz_narracion)
        if voz in VOCES_PERSONAJE or voz == voz_personaje:
            voz = voz_personaje
        else:
            voz = voz_narracion
        limpios.append({"seccion": s.get("seccion", ""), "voz": voz, "texto": texto})

    if not limpios:
        raise ValueError("Todos los segmentos venian vacios.")

    datos["segmentos"] = limpios
    datos.setdefault("subtitulo", "")
    datos.setdefault("gancho", "")
    return datos


def generar_contenido_santo(nombre_es, voz_narracion, voz_personaje,
                            palabras=PALABRAS_OBJETIVO):
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise RuntimeError("Falta la variable de entorno ANTHROPIC_API_KEY.")

    client = anthropic.Anthropic()
    peticion = (
        f"Santo/fiesta: {nombre_es}\n\n"
        f"Perfil de voz para la narracion: \"{voz_narracion}\"\n"
        f"Perfil de voz para el personaje en primera persona: \"{voz_personaje}\"\n\n"
        f"DURACION OBJETIVO: {MINUTOS_OBJETIVO} minutos de audio narrado, es "
        f"decir unas {palabras} palabras sumando TODOS los segmentos.\n"
        f"Es imprescindible alcanzar esa extension: un guion corto no sirve "
        f"para este proyecto. Desarrolla con detalle el contexto historico, "
        f"la vida, las pruebas y el legado.\n\n"
        f"Incluye al menos cinco intervenciones del personaje en primera "
        f"persona, repartidas a lo largo del guion y alternadas con el "
        f"narrador.\n\nDevolve solo el JSON."
    )

    ultimo = None
    for i, max_tokens in enumerate(MAX_TOKENS_INTENTOS, 1):
        print(f"  [intento {i}/{len(MAX_TOKENS_INTENTOS)}] max_tokens={max_tokens}")
        try:
            msg = client.messages.create(
                model=MODELO, max_tokens=max_tokens,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": peticion}])

            if getattr(msg, "stop_reason", None) == "max_tokens":
                print("     respuesta truncada, subiendo tokens...")
                ultimo = "truncado"
                continue

            datos = _validar(_parsear_json(extraer_texto(msg)),
                             voz_narracion, voz_personaje)
            n = contar_palabras(datos["segmentos"])
            print(f"     OK: {len(datos['segmentos'])} segmentos, {n} palabras, "
                  f"~{n / PALABRAS_POR_MINUTO:.1f} min estimados")
            return datos

        except json.JSONDecodeError as e:
            ultimo = f"JSON invalido: {e}"
            print(f"     {ultimo}")
        except Exception as e:                                   # noqa: BLE001
            ultimo = e
            print(f"     error: {e}")

    raise RuntimeError(f"No se pudo generar el guion. Ultimo error: {ultimo}")


def ampliar(datos, nombre_es, voz_narracion, voz_personaje, palabras_faltan):
    """Pide segmentos adicionales si el guion quedo corto."""
    client = anthropic.Anthropic()
    resumen = "\n".join(f"[{s['seccion']}] {s['texto'][:100]}..."
                        for s in datos["segmentos"])
    peticion = (
        f"Guion actual sobre {nombre_es}:\n\n{resumen}\n\n"
        f"Quedo CORTO. Necesito {palabras_faltan} palabras ADICIONALES.\n"
        f"Genera segmentos NUEVOS que se insertaran antes del cierre. "
        f"Profundiza en el contexto historico, su formacion, otras pruebas y "
        f"mas intervenciones en primera persona. NO repitas lo ya escrito y "
        f"NO incluyas gancho ni cierre.\n\n"
        f"Devolve solo:\n"
        f'{{"segmentos": [{{"seccion": "ampliacion", "voz": "{voz_narracion}", '
        f'"texto": "..."}}]}}'
    )
    for max_tokens in MAX_TOKENS_INTENTOS:
        try:
            msg = client.messages.create(
                model=MODELO, max_tokens=max_tokens, system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": peticion}])
            if getattr(msg, "stop_reason", None) == "max_tokens":
                continue
            extra = _validar(_parsear_json(extraer_texto(msg)),
                             voz_narracion, voz_personaje)
            segs = datos["segmentos"]
            pos = next((i for i, s in enumerate(segs)
                        if s.get("seccion", "").lower().startswith("cierre")),
                       len(segs))
            datos["segmentos"] = segs[:pos] + extra["segmentos"] + segs[pos:]
            print(f"     +{len(extra['segmentos'])} segmentos "
                  f"({contar_palabras(extra['segmentos'])} palabras)")
            return datos
        except Exception as e:                                   # noqa: BLE001
            print(f"     error ampliando: {e}")
    print("     no se pudo ampliar; se continua igual")
    return datos


def main():
    fecha_str = sys.argv[1] if len(sys.argv) > 1 else fecha_hoy_ny().isoformat()

    info = santo_rotativo(fecha_str)
    if not info:
        print("El banco de santos (data/pool_santos.json) esta vacio.")
        sys.exit(1)

    nombre_es = info["nombre_es"]
    voz_narracion = info.get("voz", "narrador")
    voz_personaje = "santa" if nombre_es.strip().lower().startswith("santa") else "santo"

    print(f"Fecha: {fecha_str}")
    print(f"Santo del dia: {nombre_es}")
    print(f"Voz narracion: {voz_narracion} | Voz personaje: {voz_personaje}")
    print(f"Objetivo: {MINUTOS_OBJETIVO} min (~{PALABRAS_OBJETIVO} palabras)\n")

    try:
        contenido = generar_contenido_santo(nombre_es, voz_narracion, voz_personaje)
    except Exception as e:                                       # noqa: BLE001
        print(f"[ERROR] Fallo la generacion con Claude: {e}")
        sys.exit(1)

    # Ampliar si quedo corto
    n = contar_palabras(contenido["segmentos"])
    minimo = int(MINUTOS_MINIMOS * PALABRAS_POR_MINUTO)
    if n < minimo:
        faltan = minimo - n + 200
        print(f"\n  Corto ({n} palabras). Ampliando +{faltan}...")
        contenido = ampliar(contenido, nombre_es, voz_narracion,
                            voz_personaje, faltan)
        n = contar_palabras(contenido["segmentos"])
        print(f"  Ahora: {n} palabras (~{n / PALABRAS_POR_MINUTO:.1f} min)")

    # "biografia" se conserva (texto plano completo) para no romper los
    # scripts de metadata y subida que ya existen.
    biografia = " ".join(s["texto"] for s in contenido["segmentos"])

    resultado = {
        "fecha": fecha_str,
        "nombre_en": info["nombre_en"],
        "nombre_limpio_en": info["nombre_limpio_en"],
        "nombre_es": nombre_es,
        "foto": info.get("foto"),
        "subtitulo": contenido["subtitulo"],
        "gancho": contenido["gancho"],
        "biografia": biografia,
        # --- nuevo ---
        "segmentos": contenido["segmentos"],
        "voz_narracion": voz_narracion,
        "voz_personaje": voz_personaje,
        "palabras": n,
        "minutos_estimados": round(n / PALABRAS_POR_MINUTO, 1),
    }

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_path = os.path.join(OUTPUT_DIR, f"santo_{fecha_str}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)

    print(f"\n{nombre_es} - {contenido['subtitulo']}")
    print(f"Gancho: {contenido['gancho']}")
    print(f"Segmentos: {len(contenido['segmentos'])} | "
          f"Palabras: {n} | Estimado: {resultado['minutos_estimados']} min")
    print(f"\nGuardado en: {out_path}")


if __name__ == "__main__":
    main()
