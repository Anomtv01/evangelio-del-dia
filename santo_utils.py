# -*- coding: utf-8 -*-
"""
santo_utils.py — Viva la Fe Catolica TV
========================================
CAMBIOS FRENTE A LA VERSION ANTERIOR (los tres que costaban dinero):

1. VOZ: edge-tts (GRATIS, ilimitado) en vez de ElevenLabs.
   Soporta guion por SEGMENTOS con voces alternadas (narrador + santo),
   que es lo que sostiene la retencion en videos largos.

2. FORMATO: el video ahora es HORIZONTAL 1920x1080 (antes 1080x1920
   vertical, que YouTube clasificaba como Short y pagaba ~$0.08 RPM).
   La miniatura para YouTube sale en 1280x720.
   Se conserva crear_thumbnail_vertical() por si quieres seguir haciendo
   Shorts como embudo hacia los videos largos.

3. MOVIMIENTO: efecto Ken Burns opcional (zoom lentisimo) para que una
   imagen fija no mate la retencion en 11 minutos.

Las 34 paletas, la busqueda de fotos y el estilo grafico se conservan.
"""

import os
import re
import subprocess

from PIL import Image, ImageDraw, ImageFont, ImageFilter

# --- Voz gratuita (reemplaza a ElevenLabs) ---
from voces_edge import generar_voz, generar_dialogo, VOCES

PALETAS = {
    "rojo_verde":        {"acento": (220, 40, 20),  "caja": (10, 65, 30),   "borde": (255, 70, 40)},
    "azul_naranja":      {"acento": (30, 100, 220),  "caja": (100, 45, 0),   "borde": (255, 140, 20)},
    "amarillo_violeta":  {"acento": (240, 210, 0),   "caja": (60, 15, 90),   "borde": (200, 70, 240)},
    "cian_rojo":         {"acento": (0, 190, 210),   "caja": (100, 15, 8),   "borde": (255, 60, 30)},
    "magenta_verde":     {"acento": (210, 30, 120),  "caja": (10, 65, 35),   "borde": (50, 200, 100)},
    "purpura_dorado":    {"acento": (150, 40, 210),  "caja": (85, 60, 8),    "borde": (240, 190, 40)},
    "borgona_turquesa":  {"acento": (160, 20, 60),   "caja": (0, 70, 65),    "borde": (20, 210, 190)},
    "indigo_ambar":      {"acento": (70, 50, 180),   "caja": (90, 55, 0),    "borde": (255, 180, 20)},
    "triada_rjo_azl_aml":{"acento": (220, 40, 20),  "caja": (10, 35, 100),  "borde": (240, 200, 0)},
    "triada_vrd_nrj_vlt":{"acento": (30, 160, 80),  "caja": (100, 45, 0),   "borde": (150, 40, 210)},
    "triada_mgn_cel_drd":{"acento": (210, 30, 120), "caja": (20, 65, 95),   "borde": (210, 165, 25)},
    "triada_cyn_crL_ndg":{"acento": (0, 190, 210),  "caja": (110, 35, 25),  "borde": (70, 50, 180)},
    "mono_rojo":         {"acento": (255, 60, 30),   "caja": (80, 10, 5),    "borde": (180, 30, 15)},
    "mono_azul":         {"acento": (80, 150, 255),  "caja": (8, 22, 70),    "borde": (30, 100, 200)},
    "mono_verde":        {"acento": (60, 200, 100),  "caja": (8, 50, 25),    "borde": (25, 140, 70)},
    "mono_purpura":      {"acento": (190, 80, 255),  "caja": (50, 10, 75),   "borde": (120, 30, 180)},
    "mono_dorado":       {"acento": (255, 210, 40),  "caja": (70, 50, 5),    "borde": (190, 150, 20)},
    "mono_rosa":         {"acento": (255, 100, 160), "caja": (110, 20, 60),  "borde": (200, 60, 120)},
    "mono_cian":         {"acento": (0, 220, 240),   "caja": (0, 75, 90),    "borde": (0, 170, 190)},
    "mono_naranja":      {"acento": (255, 130, 0),   "caja": (100, 45, 0),   "borde": (200, 100, 0)},
    "tetrada_1":         {"acento": (220, 40, 20),   "caja": (0, 75, 90),    "borde": (240, 190, 40)},
    "tetrada_2":         {"acento": (30, 100, 220),  "caja": (100, 45, 0),   "borde": (150, 40, 210)},
    "tetrada_3":         {"acento": (0, 190, 210),   "caja": (80, 10, 5),    "borde": (210, 165, 25)},
    "tetrada_4":         {"acento": (210, 30, 120),  "caja": (10, 65, 35),   "borde": (70, 50, 180)},
    "analogo_fuego":     {"acento": (230, 80, 0),    "caja": (120, 15, 8),   "borde": (240, 150, 20)},
    "analogo_oceano":    {"acento": (0, 160, 200),   "caja": (8, 22, 70),    "borde": (20, 200, 160)},
    "analogo_bosque":    {"acento": (30, 160, 80),   "caja": (8, 28, 85),    "borde": (0, 190, 130)},
    "analogo_atardecer": {"acento": (210, 80, 150),  "caja": (100, 45, 0),   "borde": (240, 120, 40)},
    "analogo_aurora":    {"acento": (150, 40, 210),  "caja": (8, 22, 70),    "borde": (0, 160, 200)},
    "esmeralda":         {"acento": (0, 200, 130),   "caja": (0, 70, 45),    "borde": (20, 230, 150)},
    "zafiro":            {"acento": (20, 80, 200),   "caja": (8, 28, 85),    "borde": (50, 110, 240)},
    "rubi":              {"acento": (200, 10, 50),   "caja": (80, 4, 20),    "borde": (240, 30, 70)},
    "ambar":             {"acento": (220, 150, 0),   "caja": (90, 55, 0),    "borde": (255, 180, 20)},
    "jade":              {"acento": (0, 160, 110),   "caja": (0, 60, 42),    "borde": (20, 190, 130)},
    "amatista":          {"acento": (170, 60, 220),  "caja": (55, 12, 80),   "borde": (210, 100, 255)},
    "topacio":           {"acento": (0, 180, 200),   "caja": (0, 65, 80),    "borde": (20, 220, 230)},
    "coral":             {"acento": (230, 90, 70),   "caja": (110, 35, 25),  "borde": (255, 120, 90)},
}
LISTA_COLORES = list(PALETAS.keys())

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def obtener_color(nombre):
    index = sum(ord(c) for c in nombre) % len(LISTA_COLORES)
    return LISTA_COLORES[index]


def buscar_foto(santo, carpetas_fotos=None):
    """Busca la foto en fotos/ del repo y, como respaldo, C:\\VivaLaFe\\fotos."""
    if carpetas_fotos is None:
        carpetas_fotos = [os.path.join(BASE_DIR, "fotos"), "C:\\VivaLaFe\\fotos"]
    elif isinstance(carpetas_fotos, str):
        carpetas_fotos = [carpetas_fotos]

    nombre_buscar = santo.lower()
    for carpeta in carpetas_fotos:
        if not os.path.isdir(carpeta):
            continue
        for archivo in os.listdir(carpeta):
            if archivo.lower().endswith((".jpg", ".jpeg", ".png")):
                base = os.path.splitext(archivo)[0].lower()
                base = base.replace("_", " ").replace("-", " ")
                if nombre_buscar in base or base in nombre_buscar:
                    return os.path.join(carpeta, archivo)
    return None


def _fuentes(escala=1.0):
    """
    Carga fuentes con cadena de respaldo:
      1) Windows (tu PC)   2) fonts/Lora del repo   3) fuentes del sistema Linux
    Sin el paso 3, en GitHub Actions caia a load_default() (tamano 10) y la
    miniatura salia SIN TEXTO LEGIBLE, en silencio.
    """
    fdir = os.path.join(BASE_DIR, "fonts")
    bold = [
        "C:\\Windows\\Fonts\\arialbd.ttf",
        os.path.join(fdir, "Lora-Bold.ttf"),
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ]
    reg = [
        "C:\\Windows\\Fonts\\arial.ttf",
        os.path.join(fdir, "Lora-Regular.ttf"),
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ]

    def _t(rutas, tam):
        for r in rutas:
            try:
                return ImageFont.truetype(r, int(tam * escala))
            except Exception:                                    # noqa: BLE001
                continue
        print("[AVISO] No se encontro ninguna fuente TrueType: "
              "la miniatura saldra con texto MUY pequeno. "
              "Sube fonts/Lora-Bold.ttf y fonts/Lora-Regular.ttf al repo.")
        return ImageFont.load_default()

    return {
        "san": _t(bold, 75), "n1": _t(bold, 150), "n2": _t(bold, 120),
        "sub": _t(reg, 48), "gancho": _t(bold, 52),
    }


def fondo_generico(W, H, paleta):
    """Fondo de respaldo: degradado + resplandor + cruz."""
    ac, bo = paleta["acento"], paleta["borde"]
    top = (8, 8, 14)
    bottom = tuple(max(0, c // 6) for c in ac)

    img = Image.new("RGB", (W, H), top)
    d = ImageDraw.Draw(img)
    for y in range(H):
        t = y / H
        d.line([(0, y), (W, y)], fill=(
            int(top[0] + (bottom[0] - top[0]) * t),
            int(top[1] + (bottom[1] - top[1]) * t),
            int(top[2] + (bottom[2] - top[2]) * t)))

    ov = Image.new("L", (W, H), 0)
    od = ImageDraw.Draw(ov)
    cx, cy, radio = W // 2, int(H * 0.38), int(max(W, H) * 0.55)
    for i in range(radio, 0, -6):
        od.ellipse([cx - i, cy - i, cx + i, cy + i],
                   fill=int(90 * (1 - i / radio) ** 2))
    ov = ov.filter(ImageFilter.GaussianBlur(40))
    img = Image.composite(Image.new("RGB", (W, H), ac), img, ov)

    dr = ImageDraw.Draw(img)
    tam = int(min(W, H) * 0.22)
    gr = max(10, tam // 10)
    dr.rectangle([cx - gr // 2, cy - tam // 2, cx + gr // 2, cy + tam // 2], fill=bo)
    yh = cy - tam // 6
    dr.rectangle([cx - tam // 3, yh - gr // 2, cx + tam // 3, yh + gr // 2], fill=bo)
    return img


def _encuadrar(foto, W, H):
    """
    Encaja la foto en WxH. Si la proporcion no coincide (tipico: foto
    vertical del santo en marco horizontal), rellena con la misma imagen
    desenfocada de fondo -- se ve profesional y no deforma al santo.
    """
    ratio_dst = W / H
    ratio_src = foto.width / foto.height

    if abs(ratio_src - ratio_dst) < 0.12:
        r = max(W / foto.width, H / foto.height)
        im = foto.resize((int(foto.width * r), int(foto.height * r)), Image.LANCZOS)
        l = (im.width - W) // 2
        t = (im.height - H) // 2
        return im.crop((l, t, l + W, t + H))

    # Fondo desenfocado que llena el marco
    r = max(W / foto.width, H / foto.height)
    fondo = foto.resize((int(foto.width * r), int(foto.height * r)), Image.LANCZOS)
    l = (fondo.width - W) // 2
    t = (fondo.height - H) // 2
    fondo = fondo.crop((l, t, l + W, t + H)).filter(ImageFilter.GaussianBlur(45))
    fondo = Image.eval(fondo, lambda p: int(p * 0.55))

    # Foto completa centrada encima
    r2 = min(W / foto.width, H / foto.height) * 0.94
    front = foto.resize((int(foto.width * r2), int(foto.height * r2)), Image.LANCZOS)
    fondo.paste(front, ((W - front.width) // 2, (H - front.height) // 2))
    return fondo


def _componer_dividido(santo, W, H, subtitulo, gancho, foto_path, paleta):
    """
    Diseno para 16:9: foto del santo a la DERECHA (a sangre, altura completa)
    y bloque de texto a la IZQUIERDA sobre fondo oscuro.
    Aprovecha el ancho en vez de dejar franjas borrosas a los lados, y el
    texto no compite con la cara del santo.
    """
    ancho_foto = int(W * 0.46)
    escala = H / 1080.0

    # --- Fondo oscuro con tinte de la paleta ---
    ac = paleta["acento"]
    img = Image.new("RGB", (W, H), (10, 9, 12))
    d0 = ImageDraw.Draw(img)
    for y in range(H):
        t = y / H
        d0.line([(0, y), (W, y)], fill=(
            int(14 + ac[0] * 0.07 * (1 - t)),
            int(12 + ac[1] * 0.07 * (1 - t)),
            int(16 + ac[2] * 0.07 * (1 - t))))

    # --- Foto a la derecha, encuadrada en el ROSTRO ---
    if foto_path and os.path.exists(foto_path):
        foto = Image.open(foto_path).convert("RGB")

        # Las fotos de santos suelen ser de cuerpo entero: si se recorta sin
        # mas, la cara queda diminuta. Cuando la imagen es muy alargada
        # (vertical), nos quedamos con su parte SUPERIOR, donde esta el
        # rostro, y ampliamos esa zona.
        prop = foto.height / foto.width
        if prop > 1.5:
            alto_util = int(foto.height * 0.46)      # tercio-medio superior
            foto = foto.crop((0, 0, foto.width, alto_util))
        elif prop > 1.15:
            alto_util = int(foto.height * 0.68)
            foto = foto.crop((0, 0, foto.width, alto_util))

        r = max(ancho_foto / foto.width, H / foto.height)
        f2 = foto.resize((max(1, int(foto.width * r)), max(1, int(foto.height * r))),
                         Image.LANCZOS)
        l = (f2.width - ancho_foto) // 2
        t = max(0, int((f2.height - H) * 0.18))      # deja aire sobre la cabeza
        f2 = f2.crop((l, t, l + ancho_foto, t + H))
        img.paste(f2, (W - ancho_foto, 0))

        # Degradado que funde el borde izquierdo de la foto con el fondo
        fund = int(W * 0.13)
        mask = Image.new("L", (fund, H), 0)
        md = ImageDraw.Draw(mask)
        for x in range(fund):
            md.line([(x, 0), (x, H)], fill=int(255 * (1 - x / fund)))
        oscuro = Image.new("RGB", (fund, H), (12, 10, 14))
        region = (W - ancho_foto, 0, W - ancho_foto + fund, H)
        base = img.crop(region)
        img.paste(Image.composite(oscuro, base, mask), region)
    else:
        img.paste(fondo_generico(ancho_foto, H, paleta), (W - ancho_foto, 0))

    d = ImageDraw.Draw(img)

    # --- Barra de acento vertical a la izquierda ---
    bx = int(52 * escala)
    d.rectangle([bx, int(H * 0.16), bx + int(9 * escala), int(H * 0.84)],
                fill=paleta["acento"])

    # --- Textos, alineados a la izquierda ---
    f = _fuentes(escala * 0.95)
    x = bx + int(38 * escala)
    ancho_txt = W - ancho_foto - x - int(40 * escala)

    partes = santo.split()
    prefijo, resto = "", santo
    if partes and partes[0].lower() in ("san", "santa", "santo", "santos"):
        prefijo, resto = partes[0].upper(), " ".join(partes[1:])

    lineas_nom = _ajustar(resto.upper(), f["n1"], ancho_txt, d)
    lineas_g = [l.strip() for l in gancho.split("\n") if l.strip()] if gancho else []
    lineas_g = [ln for l in lineas_g for ln in _ajustar(l, f["gancho"], ancho_txt, d)]

    h_pref = int(82 * escala) if prefijo else 0
    h_nom = int(122 * escala)
    h_sub = int(62 * escala) if subtitulo else 0
    h_lg = int(56 * escala)
    h_caja = (len(lineas_g) * h_lg + int(40 * escala)) if lineas_g else 0

    total = h_pref + len(lineas_nom) * h_nom + h_sub + (int(26 * escala) + h_caja
                                                       if lineas_g else 0)
    y = max(int(H * 0.11), (H - total) // 2)

    if prefijo:
        d.text((x, y), prefijo, font=f["san"], fill=(240, 240, 240), anchor="la")
        y += h_pref

    for i, ln in enumerate(lineas_nom):
        col = paleta["acento"] if i == 0 else (255, 255, 255)
        d.text((x, y), ln, font=f["n1"], fill=col, anchor="la")
        y += h_nom

    if subtitulo:
        d.text((x, y + int(6 * escala)), subtitulo, font=f["sub"],
               fill=(198, 198, 198), anchor="la")
        y += h_sub

    if lineas_g:
        y += int(26 * escala)
        d.rectangle([x - int(16 * escala), y,
                     x + ancho_txt + int(10 * escala), y + h_caja],
                    fill=paleta["caja"], outline=paleta["borde"],
                    width=max(2, int(3 * escala)))
        for i, ln in enumerate(lineas_g):
            d.text((x, y + int(20 * escala) + i * h_lg), ln,
                   font=f["gancho"], fill=(255, 232, 205), anchor="la")

    # --- Esquinas decorativas ---
    m, c = int(24 * escala), int(46 * escala)
    lw = max(2, int(4 * escala))
    cb = paleta["borde"]
    for (px_, py_, dx, dy) in ((m, m, 1, 1), (W - m, m, -1, 1),
                               (m, H - m, 1, -1), (W - m, H - m, -1, -1)):
        d.line([(px_, py_), (px_ + c * dx, py_)], fill=cb, width=lw)
        d.line([(px_, py_), (px_, py_ + c * dy)], fill=cb, width=lw)

    return img


def _ajustar(texto, fuente, ancho_max, draw):
    """Parte el texto en lineas que quepan en ancho_max."""
    palabras = texto.split()
    if not palabras:
        return []
    lineas, actual = [], palabras[0]
    for p in palabras[1:]:
        prueba = actual + " " + p
        if draw.textlength(prueba, font=fuente) <= ancho_max:
            actual = prueba
        else:
            lineas.append(actual)
            actual = p
    lineas.append(actual)
    return lineas


def _componer(santo, W, H, subtitulo, gancho, foto_path, paleta, escala):
    """Dibuja el arte (foto + degradado + esquinas + textos)."""
    if foto_path and os.path.exists(foto_path):
        img = _encuadrar(Image.open(foto_path).convert("RGB"), W, H)
    else:
        img = fondo_generico(W, H, paleta)

    alto_grad = int(H * 0.47)
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    for i in range(alto_grad):
        od.rectangle([0, H - alto_grad + i, W, H - alto_grad + i + 1],
                     fill=(0, 0, 0, int(230 * (i / alto_grad))))
    img = Image.alpha_composite(img.convert("RGBA"), ov).convert("RGB")
    d = ImageDraw.Draw(img)

    m = int(25 * escala)
    c = int(50 * escala)
    lw = max(2, int(4 * escala))
    cb = paleta["borde"]
    for (x, y, dx, dy) in ((m, m, 1, 1), (W - m, m, -1, 1),
                           (m, H - m, 1, -1), (W - m, H - m, -1, -1)):
        d.line([(x, y), (x + c * dx, y)], fill=cb, width=lw)
        d.line([(x, y), (x, y + c * dy)], fill=cb, width=lw)

    f = _fuentes(escala)
    cx = W // 2

    # --- Layout calculado DESDE ABAJO para que nunca se desborde ---
    partes = santo.split()
    prefijo, resto = "", santo
    if partes and partes[0].lower() in ("san", "santa", "santo", "santos"):
        prefijo, resto = partes[0].upper(), " ".join(partes[1:])
    pr = resto.upper().split()

    h_pref = int(95 * escala) if prefijo else 0
    h_n1 = int(155 * escala)
    h_n2 = int(130 * escala) if len(pr) >= 2 else 0
    h_sub = int(70 * escala) if subtitulo else 0

    lineas_g = [l.strip() for l in gancho.split("\n") if l.strip()] if gancho else []
    h_linea = int(65 * escala)
    h_caja = (len(lineas_g) * h_linea + int(45 * escala)) if lineas_g else 0
    h_gap = int(22 * escala) if lineas_g else 0

    margen = int(38 * escala)
    total = h_pref + h_n1 + h_n2 + h_sub + h_gap + h_caja
    y = H - margen - total
    y = max(y, int(H * 0.30))            # nunca invadir el tercio superior

    if prefijo:
        d.text((cx, y + h_pref // 2), prefijo, font=f["san"],
               fill=(255, 255, 255), anchor="mm")
        y += h_pref

    if len(pr) >= 2:
        d.text((cx, y + h_n1 // 2), pr[0], font=f["n1"],
               fill=paleta["acento"], anchor="mm")
        y += h_n1
        d.text((cx, y + h_n2 // 2), " ".join(pr[1:]), font=f["n2"],
               fill=(255, 255, 255), anchor="mm")
        y += h_n2
    else:
        d.text((cx, y + h_n1 // 2), resto.upper(), font=f["n1"],
               fill=paleta["acento"], anchor="mm")
        y += h_n1

    if subtitulo:
        d.text((cx, y + h_sub // 2), subtitulo, font=f["sub"],
               fill=(205, 205, 205), anchor="mm")
        y += h_sub

    if lineas_g:
        y += h_gap
        d.rectangle([int(50 * escala), y, W - int(50 * escala), y + h_caja],
                    fill=paleta["caja"], outline=paleta["borde"],
                    width=max(2, int(3 * escala)))
        for i, linea in enumerate(lineas_g):
            d.text((cx, y + int(22 * escala) + i * h_linea + h_linea // 2),
                   linea, font=f["gancho"], fill=(255, 230, 200), anchor="mm")
    return img


def crear_thumbnail(santo, carpeta, subtitulo="", gancho="", foto_path=None):
    """
    HORIZONTAL 16:9 con diseno DIVIDIDO (foto derecha / texto izquierda).
    Genera dos archivos:
      thumbnail.png   -> 1280x720, la miniatura que se sube a YouTube
      fondo_video.png -> 1920x1080, el fotograma base del video
    Devuelve la ruta de thumbnail.png (compatible con el codigo anterior).
    """
    paleta = PALETAS[obtener_color(santo)]
    ruta_foto = foto_path or buscar_foto(santo)
    os.makedirs(carpeta, exist_ok=True)

    grande = _componer_dividido(santo, 1920, 1080, subtitulo, gancho,
                                ruta_foto, paleta)
    p_video = os.path.join(carpeta, "fondo_video.png")
    grande.save(p_video)

    thumb = grande.resize((1280, 720), Image.LANCZOS)
    p_thumb = os.path.join(carpeta, "thumbnail.png")
    thumb.save(p_thumb)
    return p_thumb


def crear_thumbnail_vertical(santo, carpeta, subtitulo="", gancho="", foto_path=None):
    """VERTICAL 1080x1920 — solo para Shorts (embudo hacia el video largo)."""
    paleta = PALETAS[obtener_color(santo)]
    ruta_foto = foto_path or buscar_foto(santo)
    os.makedirs(carpeta, exist_ok=True)
    img = _componer(santo, 1080, 1920, subtitulo, gancho, ruta_foto, paleta, 1.0)
    p = os.path.join(carpeta, "thumbnail_vertical.png")
    img.save(p)
    return p


# ---------------------------------------------------------------------------
# AUDIO (edge-tts, gratis)
# ---------------------------------------------------------------------------
def generar_audio(guion, carpeta, fecha_iso, api_key=None, perfil="narrador"):
    """
    Compatible con la firma anterior (api_key se ignora, ya no hace falta).
    - Si 'guion' es texto  -> una sola voz.
    - Si 'guion' es lista de (perfil, texto) -> voces alternadas.
    Devuelve (ruta_audio, nombre_de_voz).
    """
    os.makedirs(carpeta, exist_ok=True)
    path = os.path.join(carpeta, "audio.mp3")

    if isinstance(guion, (list, tuple)):
        generar_dialogo(list(guion), path, pausa=0.7)
        usadas = sorted({p for p, _ in guion})
        return path, "+".join(usadas)

    generar_voz(guion, path, perfil)
    return path, VOCES.get(perfil, perfil)


# ---------------------------------------------------------------------------
# VIDEO
# ---------------------------------------------------------------------------
def _duracion(audio):
    try:
        out = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=nw=1:nk=1", audio],
            capture_output=True, text=True, check=True).stdout.strip()
        return float(out)
    except Exception:                                            # noqa: BLE001
        return None


def crear_video(imagen, audio, carpeta, nombre_archivo_base,
                movimiento=True, fps=24):
    """
    Arma el MP4 HORIZONTAL 1920x1080.
    movimiento=True aplica un zoom lentisimo (Ken Burns) para que una
    imagen fija no mate la retencion en un video de 11 minutos.
    Si 'imagen' apunta al thumbnail 1280x720, usa fondo_video.png si existe.
    """
    base = os.path.join(os.path.dirname(imagen), "fondo_video.png")
    if os.path.exists(base):
        imagen = base

    nombre = re.sub(r'[<>:"/\\|?*]', "", nombre_archivo_base) + ".mp4"
    output = os.path.join(carpeta, nombre)
    if os.path.exists(output):
        os.remove(output)

    dur = _duracion(audio)

    if movimiento and dur:
        frames = max(1, int(dur * fps))
        vf = (f"scale=3840:-2,zoompan=z='min(zoom+0.00018,1.14)'"
              f":d={frames}:s=1920x1080:fps={fps},"
              f"format=yuv420p")
        cmd = ["ffmpeg", "-y", "-v", "error", "-loop", "1", "-i", imagen,
               "-i", audio, "-vf", vf, "-c:v", "libx264", "-preset", "veryfast",
               "-crf", "21", "-c:a", "aac", "-b:a", "192k", "-shortest", output]
    else:
        cmd = ["ffmpeg", "-y", "-v", "error", "-loop", "1", "-i", imagen,
               "-i", audio, "-vf", "scale=1920:1080,format=yuv420p",
               "-c:v", "libx264", "-tune", "stillimage", "-preset", "veryfast",
               "-crf", "21", "-c:a", "aac", "-b:a", "192k", "-shortest", output]

    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError:
        if movimiento:
            print("[AVISO] Fallo el efecto de movimiento; se usa imagen fija.")
            return crear_video(imagen, audio, carpeta, nombre_archivo_base,
                               movimiento=False, fps=fps)
        raise
    return output


def crear_video_vertical(imagen, audio, carpeta, nombre_archivo_base,
                         movimiento=True, fps=24):
    """
    Arma el MP4 VERTICAL 1080x1920 (para Shorts). Gemelo de crear_video(),
    pensado para 'imagen' = thumbnail_vertical.png de crear_thumbnail_vertical()
    (que ya es el fotograma completo, no hace falta un fondo_video separado).
    """
    nombre = re.sub(r'[<>:"/\\|?*]', "", nombre_archivo_base) + ".mp4"
    output = os.path.join(carpeta, nombre)
    if os.path.exists(output):
        os.remove(output)

    dur = _duracion(audio)

    if movimiento and dur:
        frames = max(1, int(dur * fps))
        vf = (f"scale=2160:-2,zoompan=z='min(zoom+0.00018,1.14)'"
              f":d={frames}:s=1080x1920:fps={fps},"
              f"format=yuv420p")
        cmd = ["ffmpeg", "-y", "-v", "error", "-loop", "1", "-i", imagen,
               "-i", audio, "-vf", vf, "-c:v", "libx264", "-preset", "veryfast",
               "-crf", "21", "-c:a", "aac", "-b:a", "192k", "-shortest", output]
    else:
        cmd = ["ffmpeg", "-y", "-v", "error", "-loop", "1", "-i", imagen,
               "-i", audio, "-vf", "scale=1080:1920,format=yuv420p",
               "-c:v", "libx264", "-tune", "stillimage", "-preset", "veryfast",
               "-crf", "21", "-c:a", "aac", "-b:a", "192k", "-shortest", output]

    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError:
        if movimiento:
            print("[AVISO] Fallo el efecto de movimiento; se usa imagen fija.")
            return crear_video_vertical(imagen, audio, carpeta, nombre_archivo_base,
                                        movimiento=False, fps=fps)
        raise
    return output
