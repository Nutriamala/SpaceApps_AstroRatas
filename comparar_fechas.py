from pathlib import Path
import numpy as np
import rasterio
import matplotlib.pyplot as plt
import re
from config import (CARPETA_DATOS, PREFIJO_ARCHIVOS, NOMBRE_ZONA,
                    FECHA_COMPARACION_INICIAL, FECHA_COMPARACION_FINAL)

CARPETA = CARPETA_DATOS

def encontrar(pol):
    patron = re.compile(rf"{re.escape(PREFIJO_ARCHIVOS)}_{pol}_(\d{{8}})\.tif$")
    resultado = {}
    for ruta in CARPETA.glob(f"{PREFIJO_ARCHIVOS}_{pol}_*.tif"):
        m = patron.fullmatch(ruta.name)
        if m:
            resultado[m.group(1)] = ruta.name
    return resultado

hh = encontrar("HH")
hv = encontrar("HV")
fechas = sorted(set(hh) & set(hv))
if len(fechas) < 2:
    raise RuntimeError("Se necesitan al menos dos fechas con HH y HV")

fecha_i = FECHA_COMPARACION_INICIAL or fechas[0]
fecha_f = FECHA_COMPARACION_FINAL or fechas[-1]
if fecha_i not in fechas or fecha_f not in fechas or fecha_i == fecha_f:
    raise ValueError("Revisa las fechas de comparacion en config.py")

archivos = {
    "HH_inicial": hh[fecha_i],
    "HV_inicial": hv[fecha_i],
    "HH_final": hh[fecha_f],
    "HV_final": hv[fecha_f],
}

datos = {}
perfil = None
bounds = None
crs = None
shape = None

# Leer y verificar
for nombre, archivo in archivos.items():
    with rasterio.open(CARPETA / archivo) as src:
        if perfil is None:
            perfil = src.profile.copy()
            bounds = src.bounds
            crs = src.crs
            shape = (src.height, src.width)
        else:
            if src.crs != crs:
                raise ValueError("CRS no coincide")
            if (src.height, src.width) != shape:
                raise ValueError("Dimensiones no coinciden")
            if src.bounds != bounds:
                raise ValueError("Bounds no coinciden")

        datos[nombre] = src.read(1, masked=True).filled(np.nan).astype("float32")

# Convertir a dB
def to_db(x):
    out = np.full(x.shape, np.nan, dtype="float32")
    mask = np.isfinite(x) & (x > 0)
    out[mask] = 10 * np.log10(x[mask])
    return out

hh_i = to_db(datos["HH_inicial"])
hv_i = to_db(datos["HV_inicial"])
hh_f = to_db(datos["HH_final"])
hv_f = to_db(datos["HV_final"])

valido = (
    np.isfinite(hh_i) &
    np.isfinite(hv_i) &
    np.isfinite(hh_f) &
    np.isfinite(hv_f)
)

if not np.any(valido):
    raise ValueError("No hay pixeles válidos en común")

delta_hh = np.where(valido, hh_f - hh_i, np.nan).astype("float32")
delta_hv = np.where(valido, hv_f - hv_i, np.nan).astype("float32")

# Guardar GeoTIFF de cambios
perfil.update(
    driver="GTiff",
    dtype="float32",
    count=1,
    nodata=np.nan,
    compress="deflate",
    tiled=True,
    blockxsize=256,
    blockysize=256,
)

with rasterio.open(CARPETA / f"{PREFIJO_ARCHIVOS}_delta_HH.tif", "w", **perfil) as dst:
    dst.write(delta_hh, 1)

with rasterio.open(CARPETA / f"{PREFIJO_ARCHIVOS}_delta_HV.tif", "w", **perfil) as dst:
    dst.write(delta_hv, 1)

# Visualización
extent = [bounds.left, bounds.right, bounds.bottom, bounds.top]

p_i = np.nanpercentile(hv_i[valido], [2, 98])
p_f = np.nanpercentile(hv_f[valido], [2, 98])

vmin = min(p_i[0], p_f[0])
vmax = max(p_i[1], p_f[1])

fig, axes = plt.subplots(2, 2, figsize=(12, 10))

im1 = axes[0, 0].imshow(hv_i, cmap="gray", vmin=vmin, vmax=vmax, extent=extent)
axes[0, 0].set_title(f"HV - {fecha_i}")

im2 = axes[0, 1].imshow(hv_f, cmap="gray", vmin=vmin, vmax=vmax, extent=extent)
axes[0, 1].set_title(f"HV - {fecha_f}")

im3 = axes[1, 0].imshow(delta_hh, cmap="RdBu", vmin=-5, vmax=5, extent=extent)
axes[1, 0].set_title("Cambio HH (dB)")

im4 = axes[1, 1].imshow(delta_hv, cmap="RdBu", vmin=-5, vmax=5, extent=extent)
axes[1, 1].set_title("Cambio HV (dB)")

for ax, im in zip(axes.flat, [im1, im2, im3, im4]):
    fig.colorbar(im, ax=ax, shrink=0.75)
    ax.set_xlabel("Este UTM (m)")
    ax.set_ylabel("Norte UTM (m)")

fig.suptitle(
    f"NISAR - Cambios de retrodispersion\n{NOMBRE_ZONA}",
    fontsize=15
)

plt.tight_layout()
salida = CARPETA / f"{PREFIJO_ARCHIVOS}_mapa_cambios.png"
plt.savefig(salida, dpi=180)
plt.show()

print("Mapa creado:", salida)
print("Pixeles válidos:", int(valido.sum()))
print("Mediana cambio HH (dB):", np.nanmedian(delta_hh))
print("Mediana cambio HV (dB):", np.nanmedian(delta_hv))