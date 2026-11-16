"""Buscar escenas NISAR L2 GCOV y extraer HH/HV para el AOI configurado.

REQUISITOS: Earthdata Login configurado en ~/.netrc (nunca lo subas a Git),
GDAL con drivers NETCDF/HDF5 y /vsicurl, acceso a la red.
"""
from collections import defaultdict
from urllib.parse import urlparse
from pathlib import Path
import math
import re
import subprocess
import tempfile

import earthaccess
from rasterio.warp import transform_bounds
from rasterio.crs import CRS

from config import (
    CARPETA_DATOS, PREFIJO_ARCHIVOS, NOMBRE_ZONA,
    PUNTO_BUSQUEDA, BBOX, FECHA_INICIO, FECHA_FIN,
    PRODUCTO_NISAR, PATRON_GRANULO, MAX_RESULTADOS,
    NUM_FECHAS, CRS_DESTINO, RESOLUCION_M,
)


def verificar_configuracion():
    """Verifica los campos que debes completar para tu propio lugar."""
    if BBOX is None or len(BBOX) != 4:
        raise ValueError("Configura BBOX = (oeste, sur, este, norte) en config.py")
    oeste, sur, este, norte = BBOX
    if not (-180 <= oeste < este <= 180 and -90 <= sur < norte <= 90):
        raise ValueError("BBOX invalido. Usa grados WGS84: oeste, sur, este, norte")
    if FECHA_INICIO is None or FECHA_FIN is None:
        raise ValueError("Completa FECHA_INICIO y FECHA_FIN en config.py")
    if NUM_FECHAS < 2:
        raise ValueError("NUM_FECHAS debe ser como minimo 2")
    punto = PUNTO_BUSQUEDA or ((oeste + este) / 2, (sur + norte) / 2)
    if not (oeste <= punto[0] <= este and sur <= punto[1] <= norte):
        raise ValueError("El PUNTO_BUSQUEDA debe estar dentro del BBOX")
    return punto


def utm_automatico(bbox):
    longitud = (bbox[0] + bbox[2]) / 2
    latitud = (bbox[1] + bbox[3]) / 2
    if not (-80 <= latitud <= 84):
        raise ValueError("UTM automatico no cubre esta latitud; indica CRS_DESTINO")
    zona = max(1, min(60, math.floor((longitud + 180) / 6) + 1))
    return f"EPSG:{32600 + zona if latitud >= 0 else 32700 + zona}"


def clave_trayectoria(nombre):
    """Agrupacion tentativa de adquisiciones para no combinar geometrías distintas."""
    patron = re.search(r"_(\d{3}_[AD]_\d{3}_\d{4}_[A-Z]{4}_[A-Z])_", nombre)
    return patron.group(1) if patron else None


def main():
    punto = verificar_configuracion()
    CARPETA_DATOS.mkdir(parents=True, exist_ok=True)

    print(f"Buscando {PRODUCTO_NISAR} para {NOMBRE_ZONA}")
    print(f"AOI: {BBOX} | punto de consulta: {punto}")
    escenas = earthaccess.search_data(
        short_name=PRODUCTO_NISAR,
        point=punto,
        temporal=(FECHA_INICIO, FECHA_FIN),
        count=MAX_RESULTADOS,
    )
    grupos = defaultdict(list)
    for escena in escenas:
        nombre = escena["umm"]["GranuleUR"]
        if PATRON_GRANULO and PATRON_GRANULO not in nombre:
            continue
        fecha = re.search(r"_(20\d{6})T", nombre)
        version = re.search(r"_P\d{5}_", nombre)
        clave = clave_trayectoria(nombre)
        if not fecha or not clave:
            continue
        # Mantiene la misma geometria y version de procesamiento.
        grupos[(clave, version.group(0) if version else "sin-version")].append(
            (fecha.group(1), escena)
        )

    if not grupos:
        raise RuntimeError(
            "No se encontraron escenas compatibles. Revisa BBOX, fechas, "
            "PATRON_GRANULO, cobertura y disponibilidad del producto."
        )

    (trayectoria, version), candidatas = max(
        grupos.items(), key=lambda item: len({x[0] for x in item[1]})
    )
    por_fecha = {}
    for fecha, escena in sorted(candidatas, key=lambda x: x[0]):
        por_fecha.setdefault(fecha, escena)
    fechas = sorted(por_fecha)
    if len(fechas) < 2:
        raise RuntimeError("No hay por lo menos 2 fechas compatibles")
    n = min(NUM_FECHAS, len(fechas))
    indices = sorted({round(i * (len(fechas) - 1) / (n - 1)) for i in range(n)})
    seleccionadas = [(fechas[i], por_fecha[fechas[i]]) for i in indices]

    print("Trayectoria seleccionada:", trayectoria)
    print("Version:", version)
    print("Fechas:", [f for f, _ in seleccionadas])
    if n < 2 * 2:
        print("AVISO: El script multitemporal predeterminado requiere 4 fechas o mas")

    crs = CRS_DESTINO or utm_automatico(BBOX)
    dst_crs = CRS.from_user_input(crs)
    if not dst_crs.is_projected or abs(dst_crs.linear_units_factor[1] - 1.0) > 1e-6:
        raise ValueError("CRS_DESTINO debe ser proyectado en metros")
    oeste, sur, este, norte = transform_bounds("EPSG:4326", crs, *BBOX)
    res = RESOLUCION_M
    extension = [
        math.floor(oeste / res) * res,
        math.floor(sur / res) * res,
        math.ceil(este / res) * res,
        math.ceil(norte / res) * res,
    ]

    # Archivo de cookies fuera del repositorio (nunca subir a Git).
    cookies = Path(tempfile.gettempdir()) / "nisar_gcov_gdal_cookies.txt"
    errores = 0
    for fecha, escena in seleccionadas:
        enlaces = escena.data_links(access="external")
        url = next(
            (x for x in enlaces if urlparse(x).path.lower().endswith(".h5")), None
        )
        if url is None:
            print("SIN enlace HDF5:", fecha)
            errores += 1
            continue

        for pol, capa in (("HH", "HHHH"), ("HV", "HVHV")):
            salida = CARPETA_DATOS / f"{PREFIJO_ARCHIVOS}_{pol}_{fecha}.tif"
            if salida.exists() and salida.stat().st_size > 0:
                print("Ya existe:", salida.name)
                continue
            origen = (
                f'NETCDF:"/vsicurl/{url}":'
                f'//science/LSAR/GCOV/grids/frequencyA/{capa}'
            )
            comando = [
                "gdalwarp", "-of", "GTiff", "-t_srs", crs,
                "-te", *map(str, extension), "-tr", str(res), str(res),
                "-r", "near", "-dstnodata", "nan",
                "-co", "COMPRESS=DEFLATE", "-co", "TILED=YES",
                "--config", "GDAL_HTTP_NETRC", "YES",
                "--config", "GDAL_HTTP_COOKIEFILE", str(cookies),
                "--config", "GDAL_HTTP_COOKIEJAR", str(cookies),
                origen, str(salida),
            ]
            print("Extrayendo:", fecha, pol)
            try:
                subprocess.run(comando, check=True)
                subprocess.run(
                    ["gdalinfo", str(salida)], check=True,
                    stdout=subprocess.DEVNULL,
                )
                print("Guardado:", salida)
            except (subprocess.CalledProcessError, FileNotFoundError) as exc:
                salida.unlink(missing_ok=True)
                errores += 1
                print("Error en extraccion:", exc)

    print("Finalizado. Salidas:", CARPETA_DATOS, "| fallos:", errores)
    if errores:
        print("Revisa autenticacion Earthdata, drivers GDAL y acceso a archivos HDF5.")


if __name__ == "__main__":
    main()
