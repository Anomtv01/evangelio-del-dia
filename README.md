# Evangelio del Día - Viva la Fe Católica TV

Pipeline automático que genera, cada día, el paquete completo para un video
del Evangelio: texto en español (dominio público), reflexión original
(Claude API), thumbnail y metadata de YouTube.

## Instalación (una sola vez)

```
pip install -r requisitos.txt --break-system-packages
```

Configurar la API key de Claude (Windows PowerShell):
```
setx ANTHROPIC_API_KEY "sk-ant-tu-key-aqui"
```
(Cerrá y volvé a abrir la terminal para que tome la variable.)

## Uso diario

```
python generar_todo.py               # Evangelio de hoy
python generar_todo.py 2026-12-25    # Evangelio de una fecha específica
```

Esto genera en `output/`:
- `evangelio_<fecha>.json` — cita, texto completo en español, fiesta litúrgica
- `reflexion_<fecha>.txt` — reflexión original de ~150 palabras
- `thumbnail_<fecha>.png` — imagen 1280x720 lista para YouTube
- `metadata_<fecha>.json` — título, descripción y tags

## Estructura del proyecto

```
mensajes_virgen/
├── generar_todo.py              <- correr este (orquesta todo)
├── evangelio_del_dia.py         <- Paso 1: texto del Evangelio
├── generar_reflexion.py         <- Paso 2: reflexión (Claude API)
├── generar_thumbnail.py         <- Paso 3: thumbnail
├── generar_metadata.py          <- Paso 4: metadata de YouTube
├── generar_fiestas_especiales.py <- genera data/fiestas_especiales.json
│                                    (ya ejecutado; volver a correr solo si
│                                     hace falta regenerar el archivo)
├── citas.py                     <- parser de citas bíblicas
├── libros.py                    <- nombres de libros bíblicos EN->ES
├── traducir_fiesta.py           <- traductor de nombres litúrgicos EN->ES
├── data/
│   ├── biblia_platense.json     <- Biblia Platense (Straubinger), dominio público
│   ├── citas_diarias.json       <- citas del leccionario (2023-2027), sin texto
│   └── fiestas_especiales.json  <- respaldo para solemnidades grandes
├── fonts/                       <- tipografía Lora (licencia OFL, uso libre)
└── output/                      <- acá caen los archivos generados
```

## Fuentes usadas (100% en regla)

- **Texto bíblico:** Biblia Platense (revisión Mons. Juan Straubinger),
  traducción católica en español, **dominio público**.
- **Citas del leccionario:** metadata pública (fecha → referencia bíblica),
  sin texto con derechos de autor — repositorio `catholic-daily-readings`.
- **Solemnidades grandes** (Navidad, Asunción, Pentecostés, Ascensión, etc.):
  citas verificadas a mano contra las tablas de Felix Just, S.J.
  (catholic-resources.org/Lectionary), cubriendo 2023-2027.
- **Reflexión:** texto 100% original generado por la API de Claude —
  nunca copiado de una homilía, sacerdote o sitio real.
- **Tipografía:** Lora (Google Fonts / Open Font License, uso libre incluso
  comercial).

## Limitaciones conocidas

- El respaldo de fiestas especiales cubre 2023-2027 (mismo rango que la
  fuente de citas). Si necesitás fechas de 2028 en adelante, hay que
  extender `generar_fiestas_especiales.py`.
- La fuente automática tiene un hueco de datos entre junio y octubre de
  2027 (~116 días) — todavía falta que se scrapee esa parte. No es
  urgente (falta más de un año), pero conviene revisarlo más adelante.
- El parser de citas (`citas.py`) cubre el ~95% de los formatos de cita
  del leccionario. Si aparece una cita rara que no reconoce, el script
  avisa con "[AVISO]" en vez de fallar en silencio — revisar a mano esos
  casos puntuales.
