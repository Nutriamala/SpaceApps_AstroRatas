# Guía reutilizable de procesamiento SAR NISAR L2 GCOV

Scripts de ejemplo para descargar, recortar, analizar y visualizar **HH/HV** de NISAR en cualquier área de estudio **compatible con las adquisiciones y polarizaciones disponibles**.

> **Uso exploratorio:** las detecciones de cambio radar no equivalen por sí mismas a deforestación, inundación o pérdida de biomasa confirmadas. Los umbrales son heurísticos y necesitan comprobación local. Este repositorio no implementa Random Forest.

## 1. Configura tu zona aquí

Abre **[`config.py`](config.py)**. Es el único archivo que normalmente necesitas modificar:

```python
# AQUÍ escribe la carpeta donde están tus GeoTIFF o donde se guardarán.
CARPETA_DATOS = Path(__file__).resolve().parent / 'datos'
# Ejemplo de ruta alternativa: Path('/ruta/a/mis/archivos')

# AQUÍ identifica tu zona y el prefijo de todos los archivos.
NOMBRE_ZONA = 'Area de estudio'
PREFIJO_ARCHIVOS = 'AOI'

# AQUÍ pon el punto de consulta (longitud, latitud).
PUNTO_BUSQUEDA = (-75.0, 5.0)  # EJEMPLO: cámbialo

# AQUÍ pon el rectángulo de análisis (oeste, sur, este, norte).
BBOX = (-75.05, 4.95, -74.95, 5.05)  # EJEMPLO: cámbialo

# AQUÍ selecciona las fechas.
FECHA_INICIO = '2026-06-01'  # EJEMPLO: cámbiala
FECHA_FIN = '2026-10-01'     # EJEMPLO: cámbiala

# Si conoces el identificador estable de trayectoria/fotograma, ponlo aquí.
# Si no, deja None: el descargador intentará agrupar escenas compatibles.
PATRON_GRANULO = None
```

Los valores de coordenadas/fechas de este ejemplo son **ilustrativos**, no una selección verificada con cobertura. **En el archivo entregado vienen en `None` para obligar a configurar una AOI propia** antes de descargar.

`CRS_DESTINO = None` calcula automáticamente la zona UTM desde el BBOX, válida para latitudes UTM; o puedes especificar un CRS EPSG proyectado **en metros**. La resolución de salida se configura con `RESOLUCION_M = 20`, pero **remuestrear a 20 m no implica resolución física nativa de 20 m**.

## 2. Requisitos

Python 3.10+; en Ubuntu/WSL puedes instalar GDAL CLI con `sudo apt install gdal-bin` (además del driver NETCDF/HDF5 compatible con el producto). Luego:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

En Windows, activa el entorno con `.venv\Scripts\activate` y asegúrate de tener `gdalwarp` / `gdalinfo` disponibles en PATH si vas a descargar.

**Autenticación:** para descargar de Earthdata, configura el acceso a NASA Earthdata Login y el `~/.netrc` local para GDAL `/vsicurl` según su documentación oficial. **Nunca subas tu `.netrc`, contraseñas, cookies ni tokens al repositorio.** Para procesar GeoTIFF ya descargados no necesitas conexión a NASA.

## 3. Pipeline

| Orden | Archivo | Qué hace |
|---|---|---|
| 1 | `descargar_nisar.py` | Busca producto NISAR GCOV, selecciona fechas compatibles y extrae recortes HH (`HHHH`) y HV (`HVHV`). Requiere AOI, fechas, red y autenticación. |
| 2 | `procesar_nisar.py` | Lee las fechas en **potencia lineal**, aplica un filtro Lee **aproximado**, calcula diferencias multitemporales, tendencia HV y mapa categórico **NO VALIDADO**. Requiere 4 o más fechas. |
| 3 | `analizar_clases.py` | Cuenta píxeles y calcula hectáreas por categoría. |
| 4 | `analizar_parches.py` | Encuentra parches conectados en clase 1, calcula área, centroide, distancia a clase 2, exporta CSV/GeoJSON/GeoTIFF y figura. |
| Extra | `comparar_fechas.py` | Comparación directa de dos fechas HH/HV (sin filtro Lee). |
| Extra | `generar_rgb.py` | Crea un falso color exploratorio **R=HH, G=HV, B=HV/HH** para cada fecha a partir de GeoTIFF Lee en dB. |
| Extra | `generar_gif.py` | Crea un GIF cronológico a partir de los RGB anteriores (cualquier número de fechas >=2). |

```bash
python descargar_nisar.py
python procesar_nisar.py
python analizar_clases.py
python analizar_parches.py

# Opcionales
python comparar_fechas.py
python generar_rgb.py
python generar_gif.py
```

**Ya tienes GeoTIFF:** omite `descargar_nisar.py` y colócalos en `CARPETA_DATOS` con estos nombres, sustituyendo `AOI` por el `PREFIJO_ARCHIVOS` de `config.py`:

- `AOI_HH_AAAAMMDD.tif`
- `AOI_HV_AAAAMMDD.tif`

Es imprescindible que ambas polarizaciones correspondan a la misma fecha, misma extensión, CRS y píxeles alineados. Los archivos que procesa `procesar_nisar.py` deben ser **potencia lineal positiva**, no valores ya transformados a dB.

## 4. Significado del mapa de candidatos

- `0`: sin indicio de cambio bajo los umbrales aplicados.
- `1`: descenso persistente de HV según las reglas exploratorias.
- `2`: candidato próximo a superficies radiométricamente oscuras (cambio **ambiguo**; no es una máscara confirmada de agua).
- `255`: sin datos.

El algoritmo de cambios compara la mediana de las **primeras dos** fechas con la mediana de las **últimas dos** por defecto (parámetro `FECHAS_POR_GRUPO`). La clase 2 es un subconjunto de candidatos marcado por una heurística de cercanía a señales bajas; **la clase 1 y 2 no deben sumarse como deforestación confirmada**.

La distancia a clase 2 calculada por `analizar_parches.py` **no es la distancia al río**. El umbral `AREA_DESTACADA_HA` sirve únicamente para resaltar visualmente parches, sin excluirlos del GeoJSON o el CSV. Los identificadores de los parches cambian cuando cambia la AOI.

El índice `HV/HH` es una razón **de potencias lineales**; su equivalente en dB es `HV_dB - HH_dB`. El falso color se normaliza con los mismos percentiles entre fechas para facilitar comparaciones, pero no debe utilizarse como clasificación validada de vegetación.

## 5. Productos resultantes

- `datos/`: GeoTIFF originales HH/HV y, opcionalmente, cambios simples.
- `datos/procesados/`: mapas Lee, cambios HH/HV, tendencia y variabilidad de HV, mapa de candidatos, metadatos JSON, resumen CSV y figura multitemporal.
- `datos/procesados/parches/`: polígonos GeoJSON en WGS84, CSV, raster de IDs y mapa de parches.
- `datos/procesados/RGB_HV_HH/`: RGB PNG/GeoTIFF, razón HV/HH y GIF.

> **Aviso:** La búsqueda/descarga depende de disponibilidad de escenas NISAR, polarizaciones del producto, permisos de Earthdata y compatibilidad de GDAL. Estas condiciones no están garantizadas para cualquier región.

## 6. Publicación segura

Este paquete no contiene rutas a la carpeta personal del autor, coordenadas privadas, identidades ni credenciales. Los datos científicos se mantienen fuera de Git con `.gitignore` para evitar subir archivos grandes o secretos accidentalmente. Para distribuir una muestra de datos, revisa su procedencia, permisos y tamaño antes de añadirla.

**Estado de pruebas:** `procesar_nisar.py`, `analizar_clases.py`, `analizar_parches.py`, `comparar_fechas.py`, `generar_rgb.py` y `generar_gif.py` se probaron con datos GeoTIFF sintéticos. La descarga remota requiere probarse con acceso propio a Earthdata/GDAL; no se ha verificado aquí contra una nueva zona.
