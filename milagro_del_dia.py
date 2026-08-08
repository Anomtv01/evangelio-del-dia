@@ -1,20 +1,20 @@
# -*- coding: utf-8 -*-
"""
milagro_del_dia.py — Jueves Eucaristico · Viva la Fe Catolica TV
milagro_del_dia.py — Jueves Eucarístico · Viva la Fe Católica TV
=================================================================
Genera un guion LARGO (unos 13 minutos) sobre el Milagro Eucaristico de la
semana, con voces alternadas y estructura de retencion.
Genera un guion LARGO (unos 13 minutos) sobre el Milagro Eucarístico de la
semana, con voces alternadas y estructura de retención.

CLAVE DOCTRINAL: cuando existe, se le pasa a Claude el TEXTO FUENTE del propio
documento (la exposicion de san Carlo Acutis, con prefacio del cardenal
Comastri). Asi el guion se apoya en la fuente reconocida por la Iglesia y no
documento (la exposición de san Carlo Acutis, con prefacio del cardenal
Comastri). Así el guion se apoya en la fuente reconocida por la Iglesia y no
solo en la memoria del modelo, lo que reduce el riesgo de inventar datos.

Los milagros admiten mas duracion que un santo (13 min -> 2 o 3 mid-roll),
porque tienen hecho + investigacion + respuesta de la Iglesia + significado.
Los milagros admiten más duración que un santo (13 min -> 2 o 3 mid-roll),
porque tienen hecho + investigación + respuesta de la Iglesia + significado.

Uso:
    python milagro_del_dia.py                # milagro de la semana (proximo jueves)
    python milagro_del_dia.py                # milagro de la semana (próximo jueves)
    python milagro_del_dia.py 2026-08-06     # una fecha concreta
"""

@@ -50,76 +50,83 @@
VOCES_PERSONAJE = ("testigo", "sacerdote", "jesus", "escritura")


SYSTEM_PROMPT = """Sos guionista catolico del canal de YouTube "Viva la Fe \
Catolica TV", dirigido a una audiencia catolica latinoamericana, mayormente \
mujeres de 55 anos en adelante, en Mexico y Estados Unidos. La serie se \
titula "Jueves Eucaristico" y da a conocer los Milagros Eucaristicos \
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

Te doy el TEXTO FUENTE de la exposicion de san Carlo Acutis sobre el milagro. \
Usalo como base de los hechos (lugar, fecha, que ocurrio, estudios, situacion \
Te doy el TEXTO FUENTE de la exposición de san Carlo Acutis sobre el milagro. \
Usalo como base de los hechos (lugar, fecha, qué ocurrió, estudios, situación \
actual de la reliquia). Desarrollalo y ampliaslo con tu conocimiento general, \
pero NO contradigas la fuente.

REGLAS DE CONTENIDO (obligatorias):
1. RIGOR: usa los datos de la fuente. Si anades algo que no esta en ella, que \
1. RIGOR: usá los datos de la fuente. Si añadís algo que no está en ella, que \
sea historia ampliamente conocida. NUNCA inventes fechas, nombres, resultados \
de analisis ni frases.
2. DISTINGUE CON CLARIDAD tres niveles y que se note en el guion:
   - lo que esta DOCUMENTADO y estudiado (di "los estudios cientificos \
determinaron que...", "la Iglesia reconocio...");
   - lo que es TRADICION piadosa (di "segun la tradicion", "cuenta la piedad \
de análisis ni frases.
2. DISTINGUÍ CON CLARIDAD tres niveles y que se note en el guion:
   - lo que está DOCUMENTADO y estudiado (decí "los estudios científicos \
determinaron que...", "la Iglesia reconoció...");
   - lo que es TRADICIÓN piadosa (decí "según la tradición", "cuenta la piedad \
popular");
   - lo que la CIENCIA no puede explicar (presentalo con sobriedad, sin \
exagerar).
   Esta honestidad hace el video mas creible, no menos.
3. Recuerda el criterio de la Iglesia: la fe no se funda en los milagros \
eucaristicos, sino en Cristo; el creyente no esta obligado a creer en ellos, \
   Esta honestidad hace el video más creíble, no menos.
3. Recordá el criterio de la Iglesia: la fe no se funda en los milagros \
eucarísticos, sino en Cristo; el creyente no está obligado a creer en ellos, \
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
- gancho: el momento mas impactante del milagro, SIN revelar todo. 2-3 frases.
- introduccion: donde y cuando ocurrio, en que contexto de la Iglesia.
- relato: como sucedio el milagro, paso a paso. Aca puede intervenir en \
- gancho: el momento más impactante del milagro, SIN revelar todo. 2-3 frases.
- introducción: dónde y cuándo ocurrió, en qué contexto de la Iglesia.
- relato: cómo sucedió el milagro, paso a paso. Acá puede intervenir en \
primera persona un testigo o el sacerdote (voz de personaje), alternando con \
el narrador. Al menos tres intervenciones.
- investigacion: que se examino, que analisis se hicieron, que reconocio la \
- investigación: qué se examinó, qué análisis se hicieron, qué reconoció la \
Iglesia. Es lo que da credibilidad; desarrollalo con cuidado.
- actualidad: donde se conserva hoy la reliquia y como se venera.
- significado: que nos dice este milagro sobre la Presencia Real, y el \
- actualidad: dónde se conserva hoy la reliquia y cómo se venera.
- significado: qué nos dice este milagro sobre la Presencia Real, y el \
criterio de la Iglesia (punto 3).
- cierre: invitacion a la Adoracion al Santisimo, a suscribirse y a dejar la \
intencion de oracion en los comentarios. Menciona que es Jueves Eucaristico.
- cierre: invitación a la Adoración al Santísimo, a suscribirse y a dejar la \
intención de oración en los comentarios. Mencioná que es Jueves Eucarístico.

FORMATO DE SALIDA:
Devolve UNICAMENTE un objeto JSON valido, sin texto antes ni despues y sin \
Devolvé ÚNICAMENTE un objeto JSON válido, sin texto antes ni después y sin \
bloques de markdown:

{
  "subtitulo": "lugar y ano, 3-6 palabras (ej: 'Lanciano, Italia, siglo VIII')",
  "gancho": "frase para el thumbnail en 2 lineas separadas por \\n, unas 7 \
palabras por linea, impactante pero reverente",
  "subtitulo": "lugar y año, 3-6 palabras (ej: 'Lanciano, Italia, siglo VIII')",
  "gancho": "frase para el thumbnail en 2 líneas separadas por \\n, unas 7 \
palabras por línea, impactante pero reverente",
  "segmentos": [
    {"seccion": "gancho", "voz": "NARRACION", "texto": "..."},
    {"seccion": "relato", "voz": "PERSONAJE", "texto": "..."}
  ]
}

En "voz" pone el perfil de narracion indicado, o "testigo"/"sacerdote" cuando \
En "voz" poné el perfil de narración indicado, o "testigo"/"sacerdote" cuando \
alguien habla en primera persona. No inventes otros nombres."""


@@ -160,30 +167,123 @@ def contar_palabras(segmentos):
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
    Red de seguridad: corrige palabras comunes que el modelo a veces devuelve
    sin tilde o sin ñ. Solo toca palabras completas (con limites \\b), para no
    dañar otras. No pretende ser exhaustivo, cubre lo mas frecuente.
    Red de seguridad: repone tildes y ñ en palabras que el modelo a veces
    devuelve sin ellas. Solo toca palabras completas (límites \\b) y respeta
    la mayúscula inicial cuando la palabra abre una frase.
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


@@ -219,20 +319,22 @@ def generar_contenido(entrada, voz_nar, voz_personaje="testigo"):

    fuente = entrada.get("texto_fuente")
    bloque_fuente = (
        "TEXTO FUENTE (exposicion de san Carlo Acutis):\n\"\"\"\n%s\n\"\"\"\n\n"
        "TEXTO FUENTE (exposición de san Carlo Acutis):\n\"\"\"\n%s\n\"\"\"\n\n"
        % fuente[:6000] if fuente else
        "(No hay texto fuente para este caso; usa tu conocimiento general con "
        "el maximo rigor y marca lo que sea tradicion.)\n\n")
        "(No hay texto fuente para este caso; usá tu conocimiento general con "
        "el máximo rigor y marcá lo que sea tradición.)\n\n")

    peticion = (
        "%s"
        "Milagro: %s%s.\n\n"
        "Perfil de voz para la narracion: \"%s\"\n"
        "Perfil de voz para la narración: \"%s\"\n"
        "Perfil de voz para el testigo o sacerdote en primera persona: \"%s\"\n\n"
        "DURACION OBJETIVO: %d minutos, unas %d palabras sumando TODOS los "
        "segmentos. Es imprescindible alcanzar esa extension: desarrolla con "
        "detalle el relato, la investigacion y el significado.\n\n"
        "Devolve solo el JSON."
        "DURACIÓN OBJETIVO: %d minutos, unas %d palabras sumando TODOS los "
        "segmentos. Es imprescindible alcanzar esa extensión: desarrollá con "
        "detalle el relato, la investigación y el significado.\n\n"
        "Recordá: el texto debe llevar todas las tildes y la ñ donde "
        "correspondan.\n\n"
        "Devolvé solo el JSON."
        % (bloque_fuente, entrada["titulo"],
           (" (%s, %s)" % (entrada.get("lugar"), entrada.get("anio"))
            if entrada.get("lugar") else ""),
@@ -305,8 +407,8 @@ def main():
        "voz_personaje": voz_personaje,
        "palabras": n,
        "minutos_estimados": round(n / PALABRAS_POR_MINUTO, 1),
        "credito_imagenes": ("Usado con permiso. (c) Asociacion de Amigos de "
                             "Carlo Acutis. Milagros Eucaristicos del Mundo, "
        "credito_imagenes": ("Usado con permiso. (c) Asociación de Amigos de "
                             "Carlo Acutis. Milagros Eucarísticos del Mundo, "
                             "www.miracolieucaristici.org"),
    }
