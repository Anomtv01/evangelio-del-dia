# -*- coding: utf-8 -*-
"""
milagro_del_dia.py — Jueves Eucarístico · Viva la Fe Católica TV
=================================================================
Genera un guion LARGO (unos 13 minutos) sobre el Milagro Eucarístico de la
semana, con voces alternadas y estructura de retención.

CLAVE DOCTRINAL: cuando existe, se le pasa a Claude el TEXTO FUENTE del propio
documento (la exposición de san Carlo Acutis, con prefacio del cardenal
Comastri). Así el guion se apoya en la fuente reconocida por la Iglesia y no
solo en la memoria del modelo, lo que reduce el riesgo de inventar datos.

Los milagros admiten más duración que un santo (13 min -> 2 o 3 mid-roll),
porque tienen hecho + investigación + respuesta de la Iglesia + significado.

Uso:
    python milagro_del_dia.py                # milagro de la semana (próximo jueves)
    python milagro_del_dia.py 2026-08-06     # una fecha concreta
"""

import json
import os
import re
import sys
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


# ---------------------------------------------------------------------------
# IMPORTANTE: este prompt va escrito CON TILDES a propósito.
# El modelo imita el estilo del texto que recibe: si las instrucciones van sin
# tildes, el guion sale sin tildes por más que se lo pidamos. No quitar los
# acentos de este bloque.
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """Sos guionista católico del canal de YouTube "Viva la Fe \
Católica TV", dirigido a una audiencia católica latinoamericana, mayormente \
mujeres de 55 años en adelante, en México y Estados Unidos. La serie se \
titula "Jueves Eucarístico" y da a conocer los Milagros Eucarísticos \
reconocidos por la Iglesia.

Te doy el TEXTO FUENTE de la exposición de san Carlo Acutis sobre el milagro. \
Usalo como base de los hechos (lugar, fecha, qué ocurrió, estudios, situación \
actual de la reliquia). Desarrollalo y ampliaslo con tu conocimiento general, \
pero NO contradigas la fuente.

REGLAS DE CONTENIDO (obligatorias):
1. RIGOR: usá los datos de la fuente. Si añadís algo que no está en ella, que \
sea historia ampliamente conocida. NUNCA inventes fechas, nombres, resultados \
de análisis ni frases.
2. DISTINGUÍ CON CLARIDAD tres niveles y que se note en el guion:
   - lo que está DOCUMENTADO y estudiado (decí "los estudios científicos \
determinaron que...", "la Iglesia reconoció...");
   - lo que es TRADICIÓN piadosa (decí "según la tradición", "cuenta la piedad \
popular");
   - lo que la CIENCIA no puede explicar (presentalo con sobriedad, sin \
exagerar).
   Esta honestidad hace el video más creíble, no menos.
3. Recordá el criterio de la Iglesia: la fe no se funda en los milagros \
eucarísticos, sino en Cristo; el creyente no está obligado a creer en ellos, \
pero los milagros reconocidos ayudan y confirman la fe en la Presencia Real. \
Incluí esta idea hacia el final, con respeto.
4. Doctrina católica correcta sobre la Eucaristía y la transustanciación.
5. Tono reverente y cálido, nunca sensacionalista ni morboso. Podés narrar la \
sangre o la carne del milagro con emoción contenida, sin truculencia.
6. Español neutro latinoamericano, frases claras y de longitud media (lo lee \
una voz sintética y lo escuchan personas mayores).
7. ORTOGRAFÍA PERFECTA (MUY IMPORTANTE): tu respuesta debe llevar TODAS las \
tildes y la letra ñ donde correspondan. Escribí correctamente: "año" (no \
"ano"), "México", "corazón", "apareció", "niño", "compañía", "señor", "días", \
"milagro eucarístico", "básica", "científicos", "sacerdote", "reliquia", \
"veneración", "análisis", "investigación", "también", "después", "aún", \
"así", "según", "más". Esto es obligatorio en TODO el texto, y con especial \
cuidado en el gancho y el subtítulo, que se muestran en pantalla. Un texto \
sin tildes se ve mal escrito y la voz sintética lo pronuncia mal.
8. Escribí los números en letras ('mil doscientos sesenta y cuatro', no '1264').

ESTRUCTURA DEL GUION (en este orden):
- gancho: el momento más impactante del milagro, SIN revelar todo. 2-3 frases.
- introducción: dónde y cuándo ocurrió, en qué contexto de la Iglesia.
- relato: cómo sucedió el milagro, paso a paso. Acá puede intervenir en \
primera persona un testigo o el sacerdote (voz de personaje), alternando con \
el narrador. Al menos tres intervenciones.
- investigación: qué se examinó, qué análisis se hicieron, qué reconoció la \
Iglesia. Es lo que da credibilidad; desarrollalo con cuidado.
- actualidad: dónde se conserva hoy la reliquia y cómo se venera.
- significado: qué nos dice este milagro sobre la Presencia Real, y el \
criterio de la Iglesia (punto 3).
- cierre: invitación a la Adoración al Santísimo, a suscribirse y a dejar la \
intención de oración en los comentarios. Mencioná que es Jueves Eucarístico.

FORMATO DE SALIDA:
Devolvé ÚNICAMENTE un objeto JSON válido, sin texto antes ni después y sin \
bloques de markdown:

{
  "subtitulo": "lugar y año, 3-6 palabras (ej: 'Lanciano, Italia, siglo VIII')",
  "gancho": "frase para el thumbnail en 2 líneas separadas por \\n, unas 7 \
palabras por línea, impactante pero reverente",
  "segmentos": [
    {"seccion": "gancho", "voz": "NARRACION", "texto": "..."},
    {"seccion": "relato", "voz": "PERSONAJE", "texto": "..."}
  ]
}

En "voz" poné el perfil de narración indicado, o "testigo"/"sacerdote" cuando \
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


# ---------------------------------------------------------------------------
# Red de seguridad ortográfica.
# Para agregar una palabra nueva: añadí una línea "sin_tilde": "con_tilde".
# El código se encarga solo de los límites de palabra y de la mayúscula
# inicial, así que no hace falta escribir expresiones regulares.
# ---------------------------------------------------------------------------
_CORRECCIONES = {
    # ñ
    "ano": "año", "anos": "años",
    "nino": "niño", "ninos": "niños",
    "nina": "niña", "ninas": "niñas",
    "senor": "señor", "senora": "señora", "senores": "señores",
    "manana": "mañana", "companía": "compañía", "compania": "compañía",
    "pequeno": "pequeño", "pequena": "pequeña",
    "pequenos": "pequeños", "pequenas": "pequeñas",
    "espanol": "español", "espanola": "española",
    "ensena": "enseña", "ensenanza": "enseñanza",
    "sueno": "sueño", "montana": "montaña", "banado": "bañado",
    "acompano": "acompañó", "danado": "dañado", "extrano": "extraño",

    # lugares y nombres propios
    "Mexico": "México", "Peru": "Perú", "Panama": "Panamá",
    "Bogota": "Bogotá", "Cordoba": "Córdoba", "Cadiz": "Cádiz",
    "Belen": "Belén", "Jerusalen": "Jerusalén", "Jesus": "Jesús",
    "Maria": "María", "Jose": "José", "Nicolas": "Nicolás",
    "Sebastian": "Sebastián", "Martin": "Martín", "Ines": "Inés",
    "Angel": "Ángel", "Angeles": "Ángeles",

    # vocabulario eucarístico y religioso
    "eucaristico": "eucarístico", "eucaristica": "eucarística",
    "eucaristicos": "eucarísticos", "eucaristicas": "eucarísticas",
    "Eucaristia": "Eucaristía", "eucaristia": "eucaristía",
    "catolico": "católico", "catolica": "católica",
    "catolicos": "católicos", "catolicas": "católicas",
    "basilica": "basílica", "sacerdote": "sacerdote",
    "liturgia": "liturgia", "santisimo": "santísimo",
    "Santisimo": "Santísimo", "oracion": "oración",
    "devocion": "devoción", "veneracion": "veneración",
    "adoracion": "adoración", "Adoracion": "Adoración",
    "consagracion": "consagración", "transustanciacion": "transustanciación",
    "comunion": "comunión", "Comunion": "Comunión",
    "bendicion": "bendición", "conversion": "conversión",
    "aparicion": "aparición", "apariciones": "apariciones",
    "peregrinacion": "peregrinación", "reliquia": "reliquia",
    "milagro": "milagro", "parroquia": "parroquia",
    "Espiritu": "Espíritu", "espiritual": "espiritual",
    "fe": "fe", "Trinidad": "Trinidad",

    # vocabulario de investigación
    "cientifico": "científico", "cientifica": "científica",
    "cientificos": "científicos", "cientificas": "científicas",
    "analisis": "análisis", "investigacion": "investigación",
    "examen": "examen", "medico": "médico", "medicos": "médicos",
    "microscopio": "microscopio", "biologia": "biología",
    "quimico": "químico", "quimicos": "químicos",
    "conclusion": "conclusión", "conclusiones": "conclusiones",
    "comision": "comisión", "verificacion": "verificación",
    "documentacion": "documentación", "practicamente": "prácticamente",
    "basica": "básica", "basico": "básico",

    # palabras frecuentes
    "corazon": "corazón", "razon": "razón", "ocasion": "ocasión",
    "tradicion": "tradición", "generacion": "generación",
    "situacion": "situación", "atencion": "atención",
    "explicacion": "explicación", "narracion": "narración",
    "region": "región", "vision": "visión", "mision": "misión",
    "dia": "día", "dias": "días", "aqui": "aquí", "alli": "allí",
    "asi": "así", "mas": "más", "segun": "según", "aun": "aún",
    "tambien": "también", "despues": "después", "quizas": "quizás",
    "jamas": "jamás", "ademas": "además", "detras": "detrás",
    "atras": "atrás", "alla": "allá", "esta": "está",
    "estan": "están", "habia": "había", "habian": "habían",
    "seria": "sería", "podria": "podría", "vendria": "vendría",
    "tenia": "tenía", "tenian": "tenían", "venia": "venía",
    "creia": "creía", "sabia": "sabía", "queria": "quería",
    "aparecio": "apareció", "sucedio": "sucedió", "ocurrio": "ocurrió",
    "reconocio": "reconoció", "determino": "determinó",
    "examino": "examinó", "encontro": "encontró", "llego": "llegó",
    "quedo": "quedó", "volvio": "volvió", "decidio": "decidió",
    "sintio": "sintió", "vio": "vio", "murio": "murió",
    "nacio": "nació", "cayo": "cayó", "levanto": "levantó",
    "convirtio": "convirtió", "transformo": "transformó",
    "conservo": "conservó", "guardo": "guardó", "confirmo": "confirmó",
    "declaro": "declaró", "aprobo": "aprobó", "permitio": "permitió",
    "recibio": "recibió", "pidio": "pidió", "sirvio": "sirvió",
    "abrio": "abrió", "escribio": "escribió", "descubrio": "descubrió",
    "comenzo": "comenzó", "termino": "terminó", "paso": "pasó",
    "dejo": "dejó", "mostro": "mostró", "guio": "guió",
    "historico": "histórico", "historica": "histórica",
    "publico": "público", "publica": "pública",
    "unico": "único", "unica": "única",
    "ultimo": "último", "ultima": "última",
    "proximo": "próximo", "proxima": "próxima",
    "rapido": "rápido", "rapida": "rápida",
    "facil": "fácil", "dificil": "difícil",
    "increible": "increíble", "creible": "creíble",
    "siglo": "siglo", "epoca": "época", "numero": "número",
    "cristiano": "cristiano", "espectaculo": "espectáculo",
}


def _corregir_ortografia(texto):
    """
    Red de seguridad: repone tildes y ñ en palabras que el modelo a veces
    devuelve sin ellas. Solo toca palabras completas (límites \\b) y respeta
    la mayúscula inicial cuando la palabra abre una frase.
    """
    if not texto:
        return texto
    for sin, con in _CORRECCIONES.items():
        if sin == con:                    # entradas que ya están bien
            continue
        # minúscula exacta
        texto = re.sub(r"\b%s\b" % re.escape(sin), con, texto)
        # con mayúscula inicial (Ano -> Año)
        texto = re.sub(r"\b%s\b" % re.escape(sin.capitalize()),
                       con.capitalize(), texto)
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
        "TEXTO FUENTE (exposición de san Carlo Acutis):\n\"\"\"\n%s\n\"\"\"\n\n"
        % fuente[:6000] if fuente else
        "(No hay texto fuente para este caso; usá tu conocimiento general con "
        "el máximo rigor y marcá lo que sea tradición.)\n\n")

    peticion = (
        "%s"
        "Milagro: %s%s.\n\n"
        "Perfil de voz para la narración: \"%s\"\n"
        "Perfil de voz para el testigo o sacerdote en primera persona: \"%s\"\n\n"
        "DURACIÓN OBJETIVO: %d minutos, unas %d palabras sumando TODOS los "
        "segmentos. Es imprescindible alcanzar esa extensión: desarrollá con "
        "detalle el relato, la investigación y el significado.\n\n"
        "Recordá: el texto debe llevar todas las tildes y la ñ donde "
        "correspondan.\n\n"
        "Devolvé solo el JSON."
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
        "credito_imagenes": ("Usado con permiso. (c) Asociación de Amigos de "
                             "Carlo Acutis. Milagros Eucarísticos del Mundo, "
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
