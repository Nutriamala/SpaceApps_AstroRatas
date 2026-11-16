"""Composicion de falso color SAR por fecha: R=HH, G=HV, B=HV/HH.

Entrada: GeoTIFF Lee filtrados en dB del paso procesar_nisar.py.
Los RGB son imagenes exploratorias; sus colores no equivalen a clases de cobertura.
"""
from pathlib import Path
import csv
import re

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import rasterio
from PIL import Image

from config import CARPETA_DATOS, PREFIJO_ARCHIVOS, NOMBRE_ZONA

BASE = CARPETA_DATOS / 'procesados'
SALIDA = BASE / 'RGB_HV_HH'
SALIDA.mkdir(parents=True, exist_ok=True)


def buscar(pol):
    patron = re.compile(rf'{re.escape(PREFIJO_ARCHIVOS)}_{pol}_(\d{{8}})_Lee\.tif$')
    hallados = {}
    for ruta in BASE.glob(f'{PREFIJO_ARCHIVOS}_{pol}_*_Lee.tif'):
        m = patron.fullmatch(ruta.name)
        if m:
            hallados[m.group(1)] = ruta
    return hallados


def leer(ruta):
    with rasterio.open(ruta) as src:
        return (
            src.read(1, masked=True).filled(np.nan).astype(np.float32),
            (src.crs, src.transform, src.shape),
            src.profile.copy(), src.bounds,
        )


def limites(datos, clave):
    valores = np.concatenate([
        item[clave][np.isfinite(item[clave])]
        for item in datos.values()
    ])
    if valores.size == 0:
        raise RuntimeError('Ningun pixel valido para ' + clave)
    min_v, max_v = np.percentile(valores, (2, 98))
    if max_v <= min_v:
        max_v = min_v + 1
    return float(min_v), float(max_v)


def normalizar(img, lim):
    return np.clip((img - lim[0]) / (lim[1] - lim[0]), 0, 1)


def main():
    hh_files, hv_files = buscar('HH'), buscar('HV')
    fechas = sorted(set(hh_files) & set(hv_files))
    if len(fechas) < 2:
        raise RuntimeError('Se requieren >= 2 fechas Lee filtradas con HH y HV')
    datos, grid, perfil, bounds = {}, None, None, None
    for fecha in fechas:
        hh_db, grid_hh, perfil_hh, bounds_hh = leer(hh_files[fecha])
        hv_db, grid_hv, _, _ = leer(hv_files[fecha])
        if grid_hh != grid_hv or (grid is not None and grid != grid_hh):
            raise ValueError('GeoTIFF no alineados: ' + fecha)
        grid, perfil, bounds = grid_hh, perfil_hh, bounds_hh
        valido = np.isfinite(hh_db) & np.isfinite(hv_db)
        # HV/HH en lineal = 10 ** ((HV_dB-HH_dB)/10)
        ratio_db = np.where(valido, hv_db - hh_db, np.nan).astype(np.float32)
        ratio = np.power(10.0, ratio_db / 10.0).astype(np.float32)
        ratio[~np.isfinite(ratio)] = np.nan
        datos[fecha] = {'HH': hh_db, 'HV': hv_db, 'ratio': ratio,
                        'ratio_db': ratio_db, 'valido': valido}

    lhh, lhv, lratio = (limites(datos, x) for x in ('HH', 'HV', 'ratio'))
    float_profile = perfil.copy()
    float_profile.update(driver='GTiff', dtype='float32', count=1,
                         nodata=np.nan, compress='deflate')
    rgb_profile = perfil.copy()
    rgb_profile.update(driver='GTiff', dtype='uint8', count=3,
                       compress='deflate', photometric='RGB')
    rgb_profile.pop('nodata', None)
    resumen = []

    for fecha in fechas:
        d = datos[fecha]
        rgb = np.dstack((normalizar(d['HH'], lhh),
                         normalizar(d['HV'], lhv),
                         normalizar(d['ratio'], lratio)))
        rgb_8 = (np.nan_to_num(rgb, nan=0.0) * 255).astype(np.uint8)
        alpha = np.where(d['valido'], 255, 0).astype(np.uint8)
        rgba = np.dstack((rgb_8, alpha))
        Image.fromarray(rgba).save(SALIDA / f'{PREFIJO_ARCHIVOS}_RGB_{fecha}.png')
        with rasterio.open(SALIDA / f'{PREFIJO_ARCHIVOS}_RGB_{fecha}.tif', 'w', **rgb_profile) as dst:
            for banda in range(3):
                dst.write(rgb_8[:, :, banda], banda + 1)
            dst.write_mask(alpha)
        for nombre, contenido in (('ratio_HV_HH', d['ratio']),
                                  ('ratio_HV_HH_dB', d['ratio_db'])):
            with rasterio.open(SALIDA / f'{PREFIJO_ARCHIVOS}_{nombre}_{fecha}.tif', 'w', **float_profile) as dst:
                dst.write(contenido, 1)
        resumen.append({'fecha': fecha,
                        'ratio_mediana_db': float(np.nanmedian(d['ratio_db'])),
                        'pixeles_validos': int(d['valido'].sum())})
        print('RGB generado:', fecha)

    delta = (datos[fechas[-1]]['ratio_db'] - datos[fechas[0]]['ratio_db']).astype('float32')
    with rasterio.open(SALIDA / f'{PREFIJO_ARCHIVOS}_delta_ratio_HV_HH_dB.tif', 'w', **float_profile) as dst:
        dst.write(delta, 1)
    with open(SALIDA / f'{PREFIJO_ARCHIVOS}_ratio_estadisticas.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(resumen[0]))
        w.writeheader()
        w.writerows(resumen)

    extent = (bounds.left, bounds.right, bounds.bottom, bounds.top)
    fig, axs = plt.subplots(1, 3, figsize=(15, 5), constrained_layout=True)
    for ax, fecha in zip(axs[:2], (fechas[0], fechas[-1])):
        d = datos[fecha]
        rgb = np.dstack((normalizar(d['HH'], lhh), normalizar(d['HV'], lhv),
                         normalizar(d['ratio'], lratio)))
        ax.imshow(np.nan_to_num(rgb, nan=0.0), extent=extent)
        ax.set_title(f'RGB {fecha}')
    im = axs[2].imshow(delta, extent=extent, cmap='RdBu_r', vmin=-4, vmax=4)
    axs[2].set_title('Cambio HV/HH (dB)')
    fig.colorbar(im, ax=axs[2], shrink=0.75)
    for ax in axs:
        ax.set_xlabel('Este (m)')
        ax.set_ylabel('Norte (m)')
    fig.suptitle(f'NISAR - {NOMBRE_ZONA} | R=HH, G=HV, B=HV/HH')
    fig.savefig(SALIDA / f'{PREFIJO_ARCHIVOS}_comparacion_RGB.png', dpi=150)
    plt.close(fig)
    print('RGB y mapas guardados en:', SALIDA)


if __name__ == '__main__':
    main()
