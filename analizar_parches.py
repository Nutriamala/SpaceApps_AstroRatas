
from pathlib import Path
import json
import csv

import numpy as np
import rasterio
from rasterio.features import shapes
from rasterio.warp import transform, transform_geom
from scipy.ndimage import (
    label,
    find_objects,
    distance_transform_edt
)

import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm
from matplotlib.patches import Patch
from config import CARPETA_DATOS, PREFIJO_ARCHIVOS, NOMBRE_ZONA, AREA_DESTACADA_HA

# ==========================================
# 1. CONFIGURACION
# ==========================================

BASE = CARPETA_DATOS / "procesados"

ENTRADA = BASE / f"{PREFIJO_ARCHIVOS}_candidatos_NO_VALIDADO.tif"

SALIDA = BASE / "parches"
SALIDA.mkdir(exist_ok=True)

# Solo para destacar parches en el mapa.
# NO es un umbral de deforestacion.
# Define AREA_DESTACADA_HA en config.py

# ==========================================
# 2. LEER CLASIFICACION
# ==========================================

with rasterio.open(ENTRADA) as src:
    clases = src.read(1)
    perfil = src.profile.copy()
    transformacion = src.transform
    crs = src.crs
    bounds = src.bounds

if crs is None or not crs.is_projected or abs(crs.linear_units_factor[1] - 1.0) > 1e-6:
    raise ValueError("GeoTIFF: se requiere CRS proyectado en metros")
if abs(transformacion.b) > 1e-8 or abs(transformacion.d) > 1e-8:
    raise ValueError("El raster no debe estar rotado para calcular distancias en metros")

# Clase 1 = descenso HV persistente
candidatos = clases == 1

area_pixel_ha = abs(
    transformacion.a * transformacion.e -
    transformacion.b * transformacion.d
) / 10000

print("Area por pixel:", area_pixel_ha, "ha")

# ==========================================
# 3. IDENTIFICAR PARCHES CONECTADOS
# ==========================================

# Conectividad de 8 vecinos:
# horizontal, vertical y diagonal.
estructura = np.ones((3, 3), dtype=np.uint8)

etiquetas, cantidad = label(
    candidatos,
    structure=estructura
)

etiquetas = etiquetas.astype(np.int32)

print("Parches encontrados:", cantidad)

# ==========================================
# 4. DISTANCIA A ZONAS AMBIGUAS
# ==========================================

ambiguos = clases == 2

if np.any(ambiguos):
    distancias = distance_transform_edt(
        ~ambiguos,
        sampling=(
            abs(transformacion.e),
            abs(transformacion.a)
        )
    )
else:
    distancias = None

# Esto NO es distancia al rio.
# Solo mide distancia a pixeles clase 2.

# ==========================================
# 5. ESTADISTICAS POR PARCHE
# ==========================================

estadisticas = []
objetos = find_objects(etiquetas)

for identificador, region in enumerate(
    objetos, start=1
):
    if region is None:
        continue

    fragmento = etiquetas[region]
    mascara = fragmento == identificador

    pixeles = int(mascara.sum())
    area_ha = pixeles * area_pixel_ha

    # Centroide aproximado
    filas, columnas = np.nonzero(mascara)

    fila = filas.mean() + region[0].start
    columna = columnas.mean() + region[1].start

    x, y = rasterio.transform.xy(
        transformacion, fila, columna
    )

    lon, lat = transform(
        crs,
        "EPSG:4326",
        [x],
        [y]
    )

    # Distancia minima a clase 2
    if distancias is not None:
        distancia = float(
            np.min(distancias[region][mascara])
        )
    else:
        distancia = None

    estadisticas.append({
        "id": identificador,
        "pixeles": pixeles,
        "area_ha": round(area_ha, 4),
        "longitud": round(lon[0], 7),
        "latitud": round(lat[0], 7),
        "distancia_clase2_m": (
            round(distancia, 2)
            if distancia is not None
            else ""
        ),
        "destacado": area_ha >= AREA_DESTACADA_HA
    })

estadisticas.sort(
    key=lambda x: x["area_ha"],
    reverse=True
)

# ==========================================
# 6. EXPORTAR CSV
# ==========================================

csv_salida = SALIDA / f"{PREFIJO_ARCHIVOS}_parches.csv"

with open(
    csv_salida,
    "w",
    newline="",
    encoding="utf-8"
) as archivo:

    escritor = csv.DictWriter(
        archivo,
        fieldnames=["id", "pixeles", "area_ha", "longitud", "latitud", "distancia_clase2_m", "destacado"]
    )

    escritor.writeheader()
    escritor.writerows(estadisticas)

print("CSV generado")

# ==========================================
# 7. EXPORTAR GEOJSON
# ==========================================

por_id = {
    item["id"]: item
    for item in estadisticas
}

features = []

for geometria, valor in shapes(
    etiquetas,
    mask=candidatos,
    transform=transformacion,
    connectivity=8
):
    identificador = int(valor)

    if identificador == 0:
        continue

    geo_wgs84 = transform_geom(
        crs,
        "EPSG:4326",
        geometria,
        precision=7
    )

    features.append({
        "type": "Feature",
        "properties": por_id[identificador],
        "geometry": geo_wgs84
    })

geojson = {
    "type": "FeatureCollection",
    "features": features
}

geojson_salida = SALIDA / f"{PREFIJO_ARCHIVOS}_parches.geojson"

with open(
    geojson_salida,
    "w",
    encoding="utf-8"
) as archivo:

    json.dump(
        geojson,
        archivo,
        ensure_ascii=False
    )

print("GeoJSON generado")

# ==========================================
# 8. GUARDAR RASTER DE PARCHES
# ==========================================

perfil.update(
    driver="GTiff",
    dtype="int32",
    count=1,
    nodata=0,
    compress="deflate"
)

with rasterio.open(
    SALIDA / f"{PREFIJO_ARCHIVOS}_parches_id.tif",
    "w",
    **perfil
) as dst:
    dst.write(etiquetas, 1)

# ==========================================
# 9. VISUALIZAR RESULTADOS
# ==========================================

ids_destacados = [
    item["id"]
    for item in estadisticas
    if item["destacado"]
]

# Mapa original: clases 0, 1 y 2
mapa_original = clases.copy()
mapa_original[mapa_original == 255] = 3

# Mapa de parches destacados
mapa_destacados = np.zeros_like(clases)

mapa_destacados[clases == 2] = 2
mapa_destacados[
    np.isin(etiquetas, ids_destacados)
] = 1
mapa_destacados[clases == 255] = 3

colores = ListedColormap([
    "#D9DEDC",  # Sin indicio
    "#D04747",  # Descenso HV
    "#E9B457",  # Cambio ambiguo
    "#252525"   # Sin datos
])

norma = BoundaryNorm(
    [-0.5, 0.5, 1.5, 2.5, 3.5],
    colores.N
)

extent = [
    bounds.left,
    bounds.right,
    bounds.bottom,
    bounds.top
]

fig, axes = plt.subplots(
    1, 2,
    figsize=(14, 6),
    constrained_layout=True
)

axes[0].imshow(
    mapa_original,
    cmap=colores,
    norm=norma,
    interpolation="nearest",
    extent=extent
)

axes[0].set_title(
    "Todos los candidatos de cambio"
)

axes[1].imshow(
    mapa_destacados,
    cmap=colores,
    norm=norma,
    interpolation="nearest",
    extent=extent
)

axes[1].set_title(
    f"Parches >= {AREA_DESTACADA_HA} ha"
)

for ax in axes:
    ax.set_xlabel("Este UTM (m)")
    ax.set_ylabel("Norte UTM (m)")

leyenda = [
    Patch(color="#D9DEDC", label="Sin indicio"),
    Patch(color="#D04747", label="Descenso HV"),
    Patch(color="#E9B457", label="Cambio ambiguo"),
    Patch(color="#252525", label="Sin datos")
]

fig.legend(
    handles=leyenda,
    loc="lower center",
    ncol=4,
    bbox_to_anchor=(0.5, -0.06)
)

fig.suptitle(
    f"NISAR - {NOMBRE_ZONA}\n"
    "Analisis espacial de parches candidatos",
    fontsize=15
)

imagen_salida = SALIDA / f"{PREFIJO_ARCHIVOS}_mapa_parches.png"

plt.savefig(
    imagen_salida,
    dpi=180,
    bbox_inches="tight"
)

plt.show()

# ==========================================
# 10. RESUMEN
# ==========================================

total_area = sum(
    item["area_ha"]
    for item in estadisticas
)

area_destacada = sum(
    item["area_ha"]
    for item in estadisticas
    if item["destacado"]
)

print("\n==============================")
print("RESULTADOS DEL ANALISIS")
print("==============================")

print("Cantidad de parches:", cantidad)
print("Area total candidata:", round(total_area, 2), "ha")
print("Area en parches destacados:",
      round(area_destacada, 2), "ha")

print("\nLos 10 parches mas grandes:")

for item in estadisticas[:10]:
    print(
        f"Parche {item['id']}: "
        f"{item['area_ha']:.2f} ha"
    )

print("\nArchivos guardados en:")
print(SALIDA)

print(
    "\nADVERTENCIA: los parches no representan "
    "deforestacion confirmada."
)
