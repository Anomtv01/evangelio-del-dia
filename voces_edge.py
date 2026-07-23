# -*- coding: utf-8 -*-
"""
voces_edge.py — Motor de voz GRATIS para Viva la Fe Catolica TV
================================================================
edge-tts (voces neuronales de Microsoft). Sin clave API, sin creditos.

    pip install edge-tts

TRES MODOS DE USO
-----------------
1) VOZ SIMPLE
     generar_voz("texto...", "salida.mp3", "narrador")

2) VOZ ROTATIVA POR DIA  (cada dia narra una voz distinta, automatico)
     perfil = voz_del_dia()
     generar_voz("texto...", "salida.mp3", perfil)

3) DIALOGO / REZO  (varias voces alternadas en un solo MP3)
     guion = [
        ("narrador", "Hoy la Iglesia celebra a San Pantaleon."),
        ("santo",    "Soy cristiano, y en Cristo esta mi fuerza."),
     ]
     generar_dialogo(guion, "video_completo.mp3")

     generar_rezo([("guia","Dios te salve Maria..."),
                   ("respuesta","Santa Maria, Madre de Dios...")],
                  "rosario.mp3", repeticiones=10)

VER VOCES REALES:   edge-tts --list-voices | findstr es-
"""

import asyncio
import os
import re
import shutil
import subprocess
import tempfile
import time
from datetime import date

import edge_tts

# ---------------------------------------------------------------------------
# CATALOGO DE VOCES
# ---------------------------------------------------------------------------
VOCES = {
    # --- Narracion (rotan entre si dia a dia) ---
    "narrador":     "es-MX-JorgeNeural",     # masculina, seria
    "narradora":    "es-MX-DaliaNeural",     # femenina, neutra
    "narrador_us":  "es-US-AlonsoNeural",    # masculina, espanol EE.UU.
    "narradora_us": "es-US-PalomaNeural",    # femenina, espanol EE.UU.

    # --- Rezo: guia y respuesta ---
    "guia":          "es-MX-DaliaNeural",    # guia femenina (Santa Faustina)
    "respuesta":     "es-MX-JorgeNeural",    # respuesta masculina
    "guia_alt":      "es-US-PalomaNeural",
    "respuesta_alt": "es-US-AlonsoNeural",

    # --- Proclamacion de la Escritura (Salmos, Evangelio) ---
    "escritura": "es-MX-JorgeNeural",       # solemne, pausada

    # --- Personajes (modo dialogo) ---
    "santo":   "es-US-AlonsoNeural",
    "santa":   "es-US-PalomaNeural",
    "jesus":   "es-MX-JorgeNeural",
    "virgen":  "es-MX-DaliaNeural",

    # --- Espana (opcional) ---
    "es_mujer":  "es-ES-ElviraNeural",
    "es_hombre": "es-ES-AlvaroNeural",
}

# rate = velocidad, pitch = tono. Mas lento = mas solemne.
PERFILES = {
    "narrador":      {"rate": "-4%",  "pitch": "-2Hz"},
    "narradora":     {"rate": "-4%",  "pitch": "+0Hz"},
    "narrador_us":   {"rate": "-4%",  "pitch": "+0Hz"},
    "narradora_us":  {"rate": "-4%",  "pitch": "+0Hz"},

    "guia":          {"rate": "-12%", "pitch": "+0Hz"},
    "respuesta":     {"rate": "-10%", "pitch": "-2Hz"},
    "guia_alt":      {"rate": "-12%", "pitch": "+0Hz"},
    "respuesta_alt": {"rate": "-10%", "pitch": "-2Hz"},

    "escritura": {"rate": "-16%", "pitch": "-3Hz"},   # muy pausada, orante

    "santo":   {"rate": "-6%",  "pitch": "-3Hz"},
    "santa":   {"rate": "-6%",  "pitch": "+2Hz"},
    "jesus":   {"rate": "-14%", "pitch": "-4Hz"},
    "virgen":  {"rate": "-12%", "pitch": "+2Hz"},

    "es_mujer":  {"rate": "-4%", "pitch": "+0Hz"},
    "es_hombre": {"rate": "-4%", "pitch": "+0Hz"},
}

# ---------------------------------------------------------------------------
# ROTACION POR FECHA ANCLA (mismo criterio que santo_rotativo.py)
# ---------------------------------------------------------------------------
FECHA_ANCLA = date(2026, 1, 1)

ROTACION_NARRACION = ["narrador", "narradora", "narrador_us", "narradora_us"]

ROTACION_REZO = [
    ("guia", "respuesta"),
    ("guia_alt", "respuesta_alt"),
]


def _dias_desde_ancla(fecha=None):
    return ((fecha or date.today()) - FECHA_ANCLA).days


def voz_del_dia(fecha=None):
    """Perfil de narracion que toca hoy (rotacion secuencial)."""
    return ROTACION_NARRACION[_dias_desde_ancla(fecha) % len(ROTACION_NARRACION)]


def pareja_rezo_del_dia(fecha=None):
    """Devuelve (guia, respuesta) que toca hoy."""
    return ROTACION_REZO[_dias_desde_ancla(fecha) % len(ROTACION_REZO)]


# ---------------------------------------------------------------------------
# NUCLEO TTS
# ---------------------------------------------------------------------------
REINTENTOS = 3
ESPERA = 4


async def _generar_async(texto, salida, perfil="narrador",
                         rate=None, pitch=None, subtitulos=False):
    if not texto or not texto.strip():
        raise ValueError("El texto esta vacio.")

    voz = VOCES.get(perfil)
    if voz is None:
        # El perfil no esta en el catalogo. Puede ser el nombre real de una
        # voz ("es-MX-DaliaNeural") o un perfil que no existe en esta version
        # del archivo. Si no tiene forma de voz real, se usa una por defecto
        # en vez de tumbar todo el pipeline con "Invalid voice".
        if re.match(r"^[a-z]{2}-[A-Z]{2}-\w+$", str(perfil)):
            voz = perfil
        else:
            voz = VOCES["narrador"]
            print("   [aviso] Perfil de voz '%s' desconocido; se usa "
                  "'narrador'. Actualiza voces_edge.py." % perfil)
            perfil = "narrador"
    base = PERFILES.get(perfil, {})
    ajustes = {
        "rate":  rate  if rate  is not None else base.get("rate", "+0%"),
        "pitch": pitch if pitch is not None else base.get("pitch", "+0Hz"),
    }

    carpeta = os.path.dirname(os.path.abspath(salida))
    if carpeta:
        os.makedirs(carpeta, exist_ok=True)

    ultimo = None
    for intento in range(1, REINTENTOS + 1):
        try:
            com = edge_tts.Communicate(texto, voz, **ajustes)
            if subtitulos:
                sub = edge_tts.SubMaker()
                with open(salida, "wb") as f:
                    async for ch in com.stream():
                        if ch["type"] == "audio":
                            f.write(ch["data"])
                        elif ch["type"] == "WordBoundary":
                            sub.feed(ch)
                with open(os.path.splitext(salida)[0] + ".srt", "w",
                          encoding="utf-8") as f:
                    f.write(sub.get_srt())
            else:
                await com.save(salida)

            if os.path.getsize(salida) < 1024:
                raise RuntimeError("Audio vacio o corrupto.")
            return salida
        except Exception as e:                                   # noqa: BLE001
            ultimo = e
            print(f"   [intento {intento}/{REINTENTOS}] {e}")
            if intento < REINTENTOS:
                await asyncio.sleep(ESPERA)
    raise RuntimeError(f"No se pudo generar '{salida}': {ultimo}")


def generar_voz(texto, salida, perfil="narrador",
                rate=None, pitch=None, subtitulos=False):
    return asyncio.run(_generar_async(texto, salida, perfil, rate, pitch, subtitulos))


async def _lote_async(trabajos, max_paralelo=3):
    sem = asyncio.Semaphore(max_paralelo)

    async def _uno(t):
        texto, salida = t[0], t[1]
        perfil = t[2] if len(t) > 2 else "narrador"
        async with sem:
            return await _generar_async(texto, salida, perfil)

    return await asyncio.gather(*[_uno(t) for t in trabajos])


def generar_lote(trabajos, max_paralelo=3):
    """trabajos = [(texto, salida, perfil), ...]"""
    t0 = time.time()
    res = asyncio.run(_lote_async(trabajos, max_paralelo))
    print(f"  {len(res)} audios en {time.time()-t0:.1f}s")
    return res


# ---------------------------------------------------------------------------
# ENSAMBLAJE CON FFMPEG (dialogo y rezo)
# ---------------------------------------------------------------------------
def _ffmpeg():
    exe = shutil.which("ffmpeg")
    if not exe:
        raise RuntimeError("FFmpeg no encontrado en el PATH.")
    return exe


def _silencio(ruta, segundos):
    subprocess.run(
        [_ffmpeg(), "-y", "-v", "error", "-f", "lavfi",
         "-i", "anullsrc=r=24000:cl=mono",
         "-t", str(segundos), "-c:a", "libmp3lame", "-q:a", "4", ruta],
        check=True)


def _unir(partes, salida):
    fd, lista = tempfile.mkstemp(suffix=".txt")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        for p in partes:
            ruta = os.path.abspath(p).replace("\\", "/").replace("'", "'\\''")
            f.write(f"file '{ruta}'\n")
    try:
        subprocess.run(
            [_ffmpeg(), "-y", "-v", "error", "-f", "concat", "-safe", "0",
             "-i", lista, "-c:a", "libmp3lame", "-q:a", "2", salida],
            check=True)
    finally:
        os.unlink(lista)
    return salida


def generar_dialogo(guion, salida, pausa=0.6):
    """
    Varias voces alternadas en un solo MP3.
    guion = [(perfil, texto), ...]
    pausa = segundos de silencio entre intervenciones
    """
    tmp = tempfile.mkdtemp(prefix="dialogo_")
    try:
        trabajos, partes = [], []
        for i, (perfil, texto) in enumerate(guion):
            a = os.path.join(tmp, f"p{i:03d}.mp3")
            trabajos.append((texto, a, perfil))
            partes.append(a)

        print(f"  Generando {len(trabajos)} intervenciones...")
        generar_lote(trabajos)

        if pausa > 0:
            sil = os.path.join(tmp, "sil.mp3")
            _silencio(sil, pausa)
            inter = []
            for i, p in enumerate(partes):
                inter.append(p)
                if i < len(partes) - 1:
                    inter.append(sil)
            partes = inter

        _unir(partes, salida)
        print(f"  -> {salida}")
        return salida
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def generar_rezo(par, salida, repeticiones=1, pausa=0.8):
    """
    Rezo alternado guia/respuesta.
    par = [("guia", "texto guia"), ("respuesta", "texto respuesta")]
    repeticiones = ciclos (p.ej. 10 avemarias)
    """
    guion = []
    for _ in range(repeticiones):
        guion.extend(par)
    return generar_dialogo(guion, salida, pausa=pausa)


def listar_voces_es():
    async def _run():
        vs = await edge_tts.list_voices()
        es = [v for v in vs if v["Locale"].startswith("es-")]
        for v in sorted(es, key=lambda x: x["Locale"]):
            print(f"  {v['ShortName']:30} {v['Gender']:8} {v['Locale']}")
        print(f"\nTotal: {len(es)} voces en espanol")
    asyncio.run(_run())


# ---------------------------------------------------------------------------
# PRUEBA:  python voces_edge.py
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print(f"Voz de narracion de hoy: {voz_del_dia()}")
    print(f"Pareja de rezo de hoy:   {pareja_rezo_del_dia()}\n")

    print("1) Dialogo narrador + santo:")
    generar_dialogo([
        ("narrador", "Hoy la Iglesia celebra a San Pantaleon, medico y martir. "
                     "Cuando el emperador le exigio renegar de su fe, respondio:"),
        ("santo",    "Soy cristiano. Y si mi vida os pertenece, mi alma es de Cristo."),
        ("narrador", "Aquellas palabras le costaron la vida, "
                     "pero le ganaron la corona de los martires."),
    ], "demo_dialogo.mp3")

    print("\n2) Rezo guia + respuesta (3 avemarias):")
    g, r = pareja_rezo_del_dia()
    generar_rezo([
        (g, "Dios te salve Maria, llena eres de gracia, el Senor es contigo."),
        (r, "Santa Maria, Madre de Dios, ruega por nosotros, pecadores."),
    ], "demo_rezo.mp3", repeticiones=3)

    print("\nListo: demo_dialogo.mp3 y demo_rezo.mp3")
