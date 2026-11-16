
import rasterio
import numpy as np
from pathlib import Path
from config import CARPETA_DATOS, PREFIJO_ARCHIVOS, NOMBRE_ZONA

ruta = CARPETA_DATOS / "procesados" / f"{PREFIJO_ARCHIVOS}_candidatos_NO_VALIDADO.tif"

with rasterio.open(ruta) as src:
    if not src.crs or not src.crs.is_projected or abs(src.crs.linear_units_factor[1] - 1.0) > 1e-6:
        raise ValueError("El raster debe estar en un CRS proyectado en metros")
    mapa = src.read(1)
    transform = src.transform

    # Superficie de cada pixel en hectareas
    area_pixel = abs(
        transform.a * transform.e -
        transform.b * transform.d
    ) / 10000

clases = {
    0: "Sin indicio",
    1: "Descenso HV persistente",
    2: "Cambio ambiguo",
    255: "Sin datos"
}

print(f"\nRESULTADOS - {NOMBRE_ZONA}\n")

for codigo, nombre in clases.items():
    cantidad = np.count_nonzero(mapa == codigo)
    hectareas = cantidad * area_pixel

    print(f"{nombre}: {hectareas:.2f} ha")

total = np.isin(mapa, [1, 2]).sum() * area_pixel

print(f"\nTOTAL CANDIDATOS: {total:.2f} ha")
