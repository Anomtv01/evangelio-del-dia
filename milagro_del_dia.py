# -*- coding: utf-8 -*-
"""
milagro_del_dia.py — Jueves Eucaristico · Viva la Fe Catolica TV
=================================================================
Genera un guion LARGO (unos 13 minutos) sobre el Milagro Eucaristico de la
semana, con voces alternadas y estructura de retencion.

CLAVE DOCTRINAL: cuando existe, se le pasa a Claude el TEXTO FUENTE del propio
documento (la exposicion de san Carlo Acutis, con prefacio del cardenal
Comastri). Asi el guion se apoya en la fuente reconocida por la Iglesia y no
solo en la memoria del modelo, lo que reduce el riesgo de inventar datos.

Los milagros admiten mas duracion que un santo (13 min -> 2 o 3 mid-roll),
porque tienen hecho + investigacion + respuesta de la Iglesia + significado.

Uso:
    python milagro_del_dia.py                # milagro de la semana (proximo jueves)
    python milagro_del_dia.py 2026-08-06     # una fecha concreta
"""

import json
import os
import re
import sys
import time
from datetime import date, datetime, timedelta

try:
    from zoneinfo import ZoneInfo
    _ZONA_NY = ZoneInfo("America/New_York")
except Exception:                                                # noqa: BLE001
    _ZONA_NY = None

import anthropic

from milagro_rotativo import milagro_de_la_semana

MODELO = "claude-sonnet-5"

PALABRAS_POR_MINUTO = 167
MINUTOS_OBJETIVO = 13
MINUTOS_MINIMOS = 8.5
PALABRAS_OBJETIVO = int(MINUTOS_OBJETIVO * PALABRAS_POR_MINUTO)

MAX_TOKENS_INTENTOS = [12000, 16000, 20000]

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output_milagro")

VOCES_NARRACION = ("narrador", "narradora", "narrador_us", "narradora_us")
VOCES_PERSONAJE = ("testigo", "sacerdote", "jesus", "escritura")


SYSTEM_PROMPT = """Sos guionista catolico del canal de YouTube "Viva la Fe \
Catolica TV", dirigido a una audiencia catolica latinoamericana, mayormente \
mujeres de 55 anos en adelante, en Mexico y Estados Unidos. La serie se \
titula "Jueves Eucaristico" y da a conocer los Milagros Eucaristicos \
reconocidos por la Iglesia.

Te doy el TEXTO FUENTE de la exposicion de san Carlo Acutis sobre el milagro. \
Usalo como base de los hechos (lugar, fecha, que ocurrio, estudios, situacion \
actual de la reliquia). Desarrollalo y ampliaslo con tu conocimiento general, \
pero NO contradigas la fuente.

REGLAS DE CONTENIDO (obligatorias):
1. RIGOR: usa los datos de la fuente. Si anades algo que no esta en ella, que \
sea historia ampliamente conocida. NUNCA inventes fechas, nombres, resultados \
de analisis ni frases.
2. DISTINGUE CON CLARIDAD tres niveles y que se note en el guion:
   - lo que esta DOCUMENTADO y estudiado (di "los estudios cientificos \
determinaron que...", "la Iglesia reconocio...");
   - lo que es TRADICION piadosa (di "segun la tradicion", "cuenta la piedad \
popular");
   - lo que la CIENCIA no puede explicar (presentalo con sobriedad, sin \
exagerar).
   Esta honestidad hace el video mas creible, no menos.
3. Recuerda el criterio de la Iglesia: la fe no se funda en los milagros \
eucaristicos, sino en Cristo; el creyente no esta obligado a creer en ellos, \
pero los milagros reconocidos ayudan y confirman la fe en la Presencia Real. \
Incluye esta idea hacia el final, con respeto.
4. Doctrina catolica correcta sobre la Eucaristia y la transustanciacion.
5. Tono reverente y calido, nunca sensacionalista ni morboso. Podes narrar la \
sangre o la carne del milagro con emocion contenida, sin truculencia.
6. Espanol neutro latinoamericano, frases claras y de longitud media (lo lee \
una voz sintetica y lo escuchan personas mayores).
7. ORTOGRAFIA PERFECTA (MUY IMPORTANTE): aunque estas instrucciones esten \
escritas sin tildes, TU RESPUESTA debe llevar TODAS las tildes y la letra ñ \
donde correspondan. Escribe correctamente: "año" (no "ano"), "México", \
"corazón", "apareció", "niño", "compañía", "señor", "días", "milagro \
eucarístico", "básica", "científicos". Esto es obligatorio en TODO el texto, \
y con especial cuidado en el gancho y el subtitulo, que se muestran en \
pantalla. Un texto sin tildes se ve mal escrito y la voz lo pronuncia mal.
8. Escribi los numeros en letras ('mil doscientos sesenta y cuatro', no '1264').

ESTRUCTURA DEL GUION (en este orden):
- gancho: el momento mas impactante del milagro, SIN revelar todo. 2-3 frases.
- introduccion: donde y cuando ocurrio, en que contexto de la Iglesia.
- relato: como sucedio el milagro, paso a paso. Aca puede intervenir en \
primera persona un testigo o el sacerdote (voz de personaje), alternando con \
el narrador. Al menos tres intervenciones.
- investigacion: que se examino, que analisis se hicieron, que reconocio la \
Iglesia. Es lo que da credibilidad; desarrollalo con cuidado.
- actualidad: donde se conserva hoy la reliquia y como se venera.
- significado: que nos dice este milagro sobre la Presencia Real, y el \
criterio de la Iglesia (punto 3).
- cierre: invitacion a la Adoracion al Santisimo, a suscribirse y a dejar la \
intencion de oracion en los comentarios. Menciona que es Jueves Eucaristico.

FORMATO DE SALIDA:
Devolve UNICAMENTE un objeto JSON valido, sin texto antes ni despues y sin \
bloques de markdown:

{
  "subtitulo": "lugar y ano, 3-6 palabras (ej: 'Lanciano, Italia, siglo VIII')",
  "gancho": "frase para el thumbnail en 2 lineas separadas por \\n, unas 7 \
palabras por linea, impactante pero reverente",
  "segmentos": [
    {"seccion": "gancho", "voz": "NARRACION", "texto": "..."},
    {"seccion": "relato", "voz": "PERSONAJE", "texto": "..."}
  ]
}

En "voz" pone el perfil de narracion indicado, o "testigo"/"sacerdote" cuando \
alguien habla en primera persona. No inventes otros nombres."""


def proximo_jueves(fecha):
    d = fecha
    while d.weekday() != 3:      # 3 = jueves
        d += timedelta(days=1)
    return d


def fecha_objetivo():
    if len(sys.argv) > 1:
        y, m, d = (int(x) for x in sys.argv[1].split("-"))
        return date(y, m, d)
    hoy = datetime.now(_ZONA_NY).date() if _ZONA_NY else date.today()
    return proximo_jueves(hoy)


def extraer_texto(mensaje):
    for b in mensaje.content:
        if getattr(b, "type", None) == "text":
            return b.text.strip()
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


def _corregir_ortografia(texto):
    """
    Red de seguridad: corrige palabras comunes que el modelo a veces devuelve
    sin tilde o sin ñ. Solo toca palabras completas (con limites \\b), para no
    dañar otras. No pretende ser exhaustivo, cubre lo mas frecuente.
    """
    import re
    reemplazos = {
        r"\bano\b": "año", r"\banos\b": "años",
        r"\bnino\b": "niño", r"\bninos\b": "niños",
        r"\bnina\b": "niña", r"\bninas\b": "niñas",
        r"\bMexico\b": "México", r"\bPeru\b": "Perú",
        r"\bcorazon\b": "corazón", r"\boracion\b": "oración",
        r"\bcompania\b": "compañía", r"\bsenor\b": "señor",
        r"\bsenora\b": "señora", r"\bmanana\b": "mañana",
        r"\bpequeno\b": "pequeño", r"\bpequena\b": "pequeña",
        r"\bespanol\b": "español", r"\bensena\b": "enseña",
    }
    for patron, correcto in reemplazos.items():
        # minuscula
        texto = re.sub(patron, correcto, texto)
        # con mayuscula inicial (Ano -> Año al empezar frase)
        pat_may = patron[:2] + patron[2].upper() + patron[3:]
        texto = re.sub(pat_may, correcto.capitalize(), texto)
    return texto


def _validar(datos, voz_nar, voz_personaje="testigo"):
    segs = datos.get("segmentos") or []
    if not segs:
        raise ValueError("El guion no trae segmentos.")
    limpios = []
    for s in segs:
        texto = (s.get("texto") or "").strip()
        if not texto:
            continue
        texto = _corregir_ortografia(texto)
        voz = s.get("voz", voz_nar)
        if voz in VOCES_PERSONAJE or voz in ("testigo", "sacerdote"):
            voz = voz_personaje
        else:
            voz = voz_nar
        limpios.append({"seccion": s.get("seccion", ""), "voz": voz, "texto": texto})
    if not limpios:
        raise ValueError("Todos los segmentos venian vacios.")
    datos["segmentos"] = limpios
    datos["subtitulo"] = _corregir_ortografia(datos.get("subtitulo", ""))
    datos["gancho"] = _corregir_ortografia(datos.get("gancho", ""))
    return datos


def generar_contenido(entrada, voz_nar, voz_personaje="testigo"):
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise RuntimeError("Falta la variable de entorno ANTHROPIC_API_KEY.")

    client = anthropic.Anthropic()

    fuente = entrada.get("texto_fuente")
    bloque_fuente = (
        "TEXTO FUENTE (exposicion de san Carlo Acutis):\n\"\"\"\n%s\n\"\"\"\n\n"
        % fuente[:6000] if fuente else
        "(No hay texto fuente para este caso; usa tu conocimiento general con "
        "el maximo rigor y marca lo que sea tradicion.)\n\n")

    peticion = (
        "%s"
        "Milagro: %s%s.\n\n"
        "Perfil de voz para la narracion: \"%s\"\n"
        "Perfil de voz para el testigo o sacerdote en primera persona: \"%s\"\n\n"
        "DURACION OBJETIVO: %d minutos, unas %d palabras sumando TODOS los "
        "segmentos. Es imprescindible alcanzar esa extension: desarrolla con "
        "detalle el relato, la investigacion y el significado.\n\n"
        "Devolve solo el JSON."
        % (bloque_fuente, entrada["titulo"],
           (" (%s, %s)" % (entrada.get("lugar"), entrada.get("anio"))
            if entrada.get("lugar") else ""),
           voz_nar, voz_personaje, MINUTOS_OBJETIVO, PALABRAS_OBJETIVO)
    )

    ultimo = None
    for i, mx in enumerate(MAX_TOKENS_INTENTOS, 1):
        print("  [intento %d/%d] max_tokens=%d" % (i, len(MAX_TOKENS_INTENTOS), mx))
        try:
            msg = client.messages.create(
                model=MODELO, max_tokens=mx, system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": peticion}])
            if getattr(msg, "stop_reason", None) == "max_tokens":
                print("     truncado, subiendo tokens...")
                ultimo = "truncado"
                continue
            datos = _validar(_parsear_json(extraer_texto(msg)), voz_nar, voz_personaje)
            n = contar_palabras(datos["segmentos"])
            print("     OK: %d segmentos, %d palabras, ~%.1f min"
                  % (len(datos["segmentos"]), n, n / PALABRAS_POR_MINUTO))
            return datos
        except json.JSONDecodeError as e:
            ultimo = "JSON invalido: %s" % e
            print("     %s" % ultimo)
        except Exception as e:                                   # noqa: BLE001
            ultimo = e
            print("     error: %s" % e)
            # Si el servidor esta saturado (529 overloaded) o hay limite de
            # tasa (429), esperar antes de reintentar da tiempo a que se
            # recupere. Espera creciente: 20s, 40s, 60s...
            msg_err = str(e).lower()
            if ("overloaded" in msg_err or "529" in msg_err
                    or "rate" in msg_err or "429" in msg_err
                    or "timeout" in msg_err):
                if i < len(MAX_TOKENS_INTENTOS):
                    espera = 20 * i
                    print("     servidor ocupado; esperando %ds antes de "
                          "reintentar..." % espera)
                    time.sleep(espera)
    raise RuntimeError("No se pudo generar el guion. Ultimo error: %s" % ultimo)


def main():
    fobj = fecha_objetivo()
    entrada = milagro_de_la_semana(fobj)
    if not entrada:
        print("El banco de milagros (data/pool_milagros.json) esta vacio.")
        sys.exit(1)

    voz_nar = entrada["voz"]
    voz_personaje = "sacerdote"

    print("Jueves: %s" % fobj.isoformat())
    print("Milagro: %s" % entrada["titulo"])
    print("Pais/anio: %s / %s" % (entrada.get("pais"), entrada.get("anio")))
    print("Voz: %s | Fuente del PDF: %s"
          % (voz_nar, "si" if entrada["tiene_fuente"] else "NO"))
    print("Objetivo: %d min (~%d palabras)\n" % (MINUTOS_OBJETIVO, PALABRAS_OBJETIVO))

    try:
        contenido = generar_contenido(entrada, voz_nar, voz_personaje)
    except Exception as e:                                       # noqa: BLE001
        print("[ERROR] Fallo la generacion con Claude: %s" % e)
        sys.exit(1)

    biografia = " ".join(s["texto"] for s in contenido["segmentos"])
    n = contar_palabras(contenido["segmentos"])

    resultado = {
        "fecha": fobj.isoformat(),
        "clave": entrada["clave"],
        "titulo_milagro": entrada["titulo"],
        "pais": entrada.get("pais"),
        "anio": entrada.get("anio"),
        "imagen": entrada.get("imagen"),
        "subtitulo": contenido["subtitulo"],
        "gancho": contenido["gancho"],
        "biografia": biografia,
        "segmentos": contenido["segmentos"],
        "voz_narracion": voz_nar,
        "voz_personaje": voz_personaje,
        "palabras": n,
        "minutos_estimados": round(n / PALABRAS_POR_MINUTO, 1),
        "credito_imagenes": ("Usado con permiso. (c) Asociacion de Amigos de "
                             "Carlo Acutis. Milagros Eucaristicos del Mundo, "
                             "www.miracolieucaristici.org"),
    }

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out = os.path.join(OUTPUT_DIR, "milagro_%s.json" % fobj.isoformat())
    with open(out, "w", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)

    print("\n%s - %s" % (entrada["titulo"], contenido["subtitulo"]))
    print("Gancho: %s" % contenido["gancho"])
    print("Segmentos: %d | Palabras: %d | Estimado: %s min"
          % (len(contenido["segmentos"]), n, resultado["minutos_estimados"]))
    print("\nGuardado en: %s" % out)


if __name__ == "__main__":
    main()
