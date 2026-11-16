
from pathlib import Path
from datetime import datetime
import csv
import json
import re

import numpy as np
import rasterio
from scipy.ndimage import uniform_filter, binary_dilation
import matplotlib.pyplot as plt

from config import (CARPETA_DATOS, PREFIJO_ARCHIVOS, NOMBRE_ZONA, VENTANA_LEE,
                    ENL_APROX, FECHAS_POR_GRUPO, UMBRAL_HV_DB, PERSISTENCIA_HV_DB)

# ==========================================
# CONFIGURACION
# ==========================================

ENTRADA = CARPETA_DATOS
SALIDA = ENTRADA / "procesados"
SALIDA.mkdir(parents=True, exist_ok=True)

# Parametros exploratorios
# Cambia los parametros de filtrado y deteccion en config.py


# ==========================================
# 1. BUSCAR ARCHIVOS NISAR
# ==========================================

def archivos_por_pol(pol):
    regex = re.compile(
        rf"{re.escape(PREFIJO_ARCHIVOS)}_{pol}_(\d{{8}})\.tif$"
    )

    encontrados = {}

    for ruta in ENTRADA.glob(f"{PREFIJO_ARCHIVOS}_{pol}_*.tif"):
        m = regex.fullmatch(ruta.name)

        if m and ruta.stat().st_size > 0:
            encontrados[m.group(1)] = ruta

    return encontrados


def leer_tif(ruta, referencia=None):
    with rasterio.open(ruta) as src:
        cuadricula = (
            src.crs,
            src.transform,
            src.shape
        )

        if referencia and cuadricula != referencia:
            raise ValueError(
                f"Cuadricula diferente: {ruta.name}"
            )

        datos = (
            src.read(1, masked=True)
            .filled(np.nan)
            .astype(np.float32)
        )

        return (
            datos,
            cuadricula,
            src.profile.copy(),
            src.bounds
        )


# ==========================================
# 2. FILTRO LEE ADAPTATIVO APROXIMADO
# ==========================================

def lee_aproximado(potencia, ventana=3, enl=4.0):

    validos = (
        np.isfinite(potencia) &
        (potencia > 0)
    )

    x = np.where(
        validos, potencia, 0
    ).astype(np.float32)

    pesos = uniform_filter(
        validos.astype(np.float32),
        size=ventana
    )

    media = (
        uniform_filter(x, size=ventana) /
        np.maximum(pesos, 1e-6)
    )

    segundo_momento = (
        uniform_filter(x * x, size=ventana) /
        np.maximum(pesos, 1e-6)
    )

    var_local = np.maximum(
        segundo_momento - media * media,
        0
    )

    var_ruido = media * media / enl

    var_senal = np.maximum(
        var_local - var_ruido,
        0
    )

    peso = np.divide(
        var_senal,
        var_local,
        out=np.zeros_like(var_local),
        where=var_local > 1e-12
    )

    filtrado = media + peso * (x - media)

    filtrado[
        (~validos) | (pesos < 0.6)
    ] = np.nan

    return filtrado.astype(np.float32)


# ==========================================
# 3. CONVERSION A DECIBELIOS
# ==========================================

def convertir_db(potencia):

    resultado = np.full(
        potencia.shape,
        np.nan,
        dtype=np.float32
    )

    validos = (
        np.isfinite(potencia) &
        (potencia > 0)
    )

    resultado[validos] = (
        10 * np.log10(potencia[validos])
    )

    return resultado


# ==========================================
# 4. GUARDAR GEOTIFF
# ==========================================

def guardar_tif(nombre, datos, perfil, categorico=False):

    p = perfil.copy()

    p.update(
        driver="GTiff",
        count=1,
        compress="deflate",
        tiled=True,
        blockxsize=256,
        blockysize=256
    )

    if categorico:
        p.update(dtype="uint8", nodata=255)
        datos = datos.astype(np.uint8)

    else:
        p.update(dtype="float32", nodata=np.nan)
        datos = datos.astype(np.float32)

    with rasterio.open(SALIDA / nombre, "w", **p) as dst:
        dst.write(datos, 1)


# ==========================================
# 5. COMPOSICION MULTITEMPORAL
# ==========================================

def mediana_fechas(datos, fechas):

    pila = np.stack([
        datos[f] for f in fechas
    ])

    validos = np.all(
        np.isfinite(pila) & (pila > 0),
        axis=0
    )

    mediana = np.median(
        np.where(np.isfinite(pila), pila, 0),
        axis=0
    ).astype(np.float32)

    mediana[~validos] = np.nan

    return mediana


# ==========================================
# 6. TENDENCIA Y VARIABILIDAD TEMPORAL
# ==========================================

def tendencia_y_variabilidad(db_por_fecha, fechas):

    pila = np.stack([
        db_por_fecha[f] for f in fechas
    ])

    fecha_base = datetime.strptime(
        fechas[0], "%Y%m%d"
    )

    dias = np.array([
        (
            datetime.strptime(f, "%Y%m%d") -
            fecha_base
        ).days / 30.4375
        for f in fechas
    ], dtype=np.float32)

    t = dias[:, None, None]

    valido = np.isfinite(pila)

    n = valido.sum(axis=0).astype(np.float32)

    x = np.where(valido, t, 0)
    y = np.where(valido, pila, 0)

    sx = x.sum(axis=0)
    sy = y.sum(axis=0)

    sxx = (x * x).sum(axis=0)
    sxy = (x * y).sum(axis=0)

    denominador = n * sxx - sx * sx

    pendiente = np.full(
        n.shape, np.nan, dtype=np.float32
    )

    np.divide(
        n * sxy - sx * sy,
        denominador,
        out=pendiente,
        where=(n >= 4) & (denominador > 1e-8)
    )

    dispersion = np.full(
        n.shape, np.nan, dtype=np.float32
    )

    np.divide(
        (y * y).sum(axis=0),
        n,
        out=dispersion,
        where=n > 0
    )

    media_cuadrada = np.divide(
        sy * sy,
        n,
        out=np.zeros_like(sy),
        where=n > 0
    )

    dispersion = np.sqrt(
        np.maximum(dispersion - media_cuadrada, 0)
    )

    dispersion[n < 4] = np.nan

    return pendiente, dispersion


# ==========================================
# 7. PROCESAMIENTO PRINCIPAL
# ==========================================

def main():

    hh_files = archivos_por_pol("HH")
    hv_files = archivos_por_pol("HV")

    fechas = sorted(
        set(hh_files) & set(hv_files)
    )

    print("\nFechas NISAR disponibles:")

    for fecha in fechas:
        print(" -", fecha)

    if len(fechas) < 4:
        raise RuntimeError(
            "Se necesitan al menos 4 fechas con HH y HV"
        )

    if len(fechas) < 2 * FECHAS_POR_GRUPO:
        raise RuntimeError(
            "No hay fechas suficientes para comparar"
        )

    referencia = None
    perfil = None
    bounds = None

    lineales = {"HH": {}, "HV": {}}
    en_db = {"HH": {}, "HV": {}}

    estadisticas = []

    # Leer todas las fechas
    for fecha in fechas:

        for pol, rutas in [
            ("HH", hh_files),
            ("HV", hv_files)
        ]:

            datos, cuadr, perfil_actual, bounds_actual = (
                leer_tif(rutas[fecha], referencia)
            )

            if referencia is None:
                referencia = cuadr
                perfil = perfil_actual
                bounds = bounds_actual

            validos = (
                np.isfinite(datos) & (datos > 0)
            )

            porcentaje = 100 * validos.mean()

            if porcentaje < 80:
                raise RuntimeError(
                    f"Solo {porcentaje:.1f}% de pixeles "
                    f"positivos en {rutas[fecha].name}"
                )

            suavizada = lee_aproximado(
                datos,
                VENTANA_LEE,
                ENL_APROX
            )

            lineales[pol][fecha] = suavizada

            en_db[pol][fecha] = convertir_db(
                suavizada
            )

            guardar_tif(
                f"{PREFIJO_ARCHIVOS}_{pol}_{fecha}_Lee.tif",
                en_db[pol][fecha],
                perfil
            )

            estadisticas.append({
                "fecha": fecha,
                "polarizacion": pol,
                "porcentaje_positivo": round(
                    float(porcentaje), 3
                ),
                "mediana_db_filtrado": round(
                    float(np.nanmedian(en_db[pol][fecha])),
                    4
                )
            })

            print(
                f"Procesada: {fecha} - {pol} "
                f"({porcentaje:.1f}% validos)"
            )

    # ======================================
    # 8. COMPARACION INICIAL Y FINAL
    # ======================================

    fechas_iniciales = fechas[:FECHAS_POR_GRUPO]
    fechas_finales = fechas[-FECHAS_POR_GRUPO:]

    print("\nGrupo inicial:", fechas_iniciales)
    print("Grupo final:", fechas_finales)

    composiciones = {}
    diferencias = {}

    for pol in ("HH", "HV"):

        inicial = convertir_db(
            mediana_fechas(
                lineales[pol],
                fechas_iniciales
            )
        )

        final = convertir_db(
            mediana_fechas(
                lineales[pol],
                fechas_finales
            )
        )

        composiciones[(pol, "inicial")] = inicial
        composiciones[(pol, "final")] = final

        diferencias[pol] = final - inicial

        guardar_tif(
            f"{PREFIJO_ARCHIVOS}_{pol}_comp_inicial_db.tif",
            inicial,
            perfil
        )

        guardar_tif(
            f"{PREFIJO_ARCHIVOS}_{pol}_comp_final_db.tif",
            final,
            perfil
        )

        guardar_tif(
            f"{PREFIJO_ARCHIVOS}_delta_{pol}_Lee_dB.tif",
            diferencias[pol],
            perfil
        )

    # ======================================
    # 9. ANALISIS TEMPORAL
    # ======================================

    tendencia_hv, variabilidad_hv = (
        tendencia_y_variabilidad(
            en_db["HV"],
            fechas
        )
    )

    guardar_tif(
        f"{PREFIJO_ARCHIVOS}_tendencia_HV_db_mes.tif",
        tendencia_hv,
        perfil
    )

    guardar_tif(
        f"{PREFIJO_ARCHIVOS}_variabilidad_HV_db.tif",
        variabilidad_hv,
        perfil
    )

    # ======================================
    # 10. IDENTIFICAR CAMBIOS CANDIDATOS
    # ======================================

    base_hv = composiciones[("HV", "inicial")]

    las_dos_bajan = np.all(
        np.stack([
            en_db["HV"][f] - base_hv
            <= PERSISTENCIA_HV_DB
            for f in fechas_finales
        ]),
        axis=0
    )

    validos_cambio = (
        np.isfinite(diferencias["HH"]) &
        np.isfinite(diferencias["HV"])
    )

    candidatos = (
        validos_cambio &
        (diferencias["HV"] <= UMBRAL_HV_DB) &
        las_dos_bajan
    )

    # Superficies oscuras: indicador de ambiguedad,
    # NO una clasificacion confirmada de agua.

    hh_base = composiciones[("HH", "inicial")]

    lim_hh = np.nanpercentile(hh_base, 10)
    lim_hv = np.nanpercentile(base_hv, 10)

    superficies_oscuras = (
        (hh_base < lim_hh) &
        (base_hv < lim_hv)
    )

    proximidad_oscuras = binary_dilation(
        superficies_oscuras,
        iterations=2
    )

    clases = np.zeros(
        diferencias["HV"].shape,
        dtype=np.uint8
    )

    clases[~validos_cambio] = 255
    clases[candidatos] = 1

    clases[
        candidatos & proximidad_oscuras
    ] = 2

    guardar_tif(
        f"{PREFIJO_ARCHIVOS}_candidatos_NO_VALIDADO.tif",
        clases,
        perfil,
        categorico=True
    )

    # ======================================
    # 11. EXPORTAR CSV
    # ======================================

    with open(
        SALIDA / f"{PREFIJO_ARCHIVOS}_resumen_fechas.csv",
        "w",
        newline="",
        encoding="utf-8"
    ) as archivo:

        escritor = csv.DictWriter(
            archivo,
            fieldnames=list(estadisticas[0])
        )

        escritor.writeheader()
        escritor.writerows(estadisticas)

    # ======================================
    # 12. EXPORTAR METADATOS
    # ======================================

    transform = perfil["transform"]

    pixel_ha = abs(
        transform.a * transform.e -
        transform.b * transform.d
    ) / 10000

    area_candidatos = (
        np.isin(clases, [1, 2]).sum() * pixel_ha
    )

    metadata = {
        "fuente": "NISAR GCOV",
        "ubicacion": NOMBRE_ZONA,
        "fechas": fechas,
        "grupo_inicial": fechas_iniciales,
        "grupo_final": fechas_finales,
        "filtro": "Lee adaptativo aproximado",
        "ventana": VENTANA_LEE,
        "ENL_asumido": ENL_APROX,
        "umbral_HV_db": UMBRAL_HV_DB,
        "persistencia_HV_db": PERSISTENCIA_HV_DB,
        "area_candidatos_ha": round(
            float(area_candidatos), 2
        ),
        "clases": {
            "0": "Sin indicio segun estas reglas",
            "1": "Descenso HV persistente",
            "2": "Cambio radiometricamente ambiguo",
            "255": "Sin datos"
        },
        "advertencia": (
            "Los candidatos NO representan "
            "deforestacion confirmada. "
            "Se requiere validacion independiente."
        )
    }

    with open(
        SALIDA / f"{PREFIJO_ARCHIVOS}_metadatos.json",
        "w",
        encoding="utf-8"
    ) as archivo:

        json.dump(
            metadata,
            archivo,
            indent=2,
            ensure_ascii=False
        )

    # ======================================
    # 13. CREAR MAPA FINAL
    # ======================================

    extent = [
        bounds.left,
        bounds.right,
        bounds.bottom,
        bounds.top
    ]

    fig, axes = plt.subplots(
        2, 3,
        figsize=(17, 10),
        constrained_layout=True
    )

    hv_inicial = composiciones[("HV", "inicial")]
    hv_final = composiciones[("HV", "final")]

    valores = np.concatenate([
        hv_inicial[np.isfinite(hv_inicial)],
        hv_final[np.isfinite(hv_final)]
    ])

    vmin, vmax = np.percentile(
        valores, [2, 98]
    )

    imagenes = [
        hv_inicial,
        hv_final,
        diferencias["HV"],
        diferencias["HH"],
        tendencia_hv,
        clases.astype(float)
    ]

    titulos = [
        "HV inicial (dB)",
        "HV final (dB)",
        "Cambio HV (dB)",
        "Cambio HH (dB)",
        "Tendencia HV (dB/mes)",
        "Candidatos NO validados"
    ]

    from matplotlib.colors import (
        ListedColormap,
        BoundaryNorm
    )

    for i, (ax, datos, titulo) in enumerate(
        zip(axes.flat, imagenes, titulos)
    ):

        if i in (0, 1):
            kwargs = dict(
                cmap="gray",
                vmin=vmin,
                vmax=vmax
            )

        elif i in (2, 3):
            kwargs = dict(
                cmap="RdBu",
                vmin=-4,
                vmax=4
            )

        elif i == 4:
            kwargs = dict(
                cmap="RdBu",
                vmin=-2,
                vmax=2
            )

        else:
            colores = ListedColormap([
                "#E4E5E6",
                "#D14E47",
                "#EDB35B",
                "#181818"
            ])

            kwargs = dict(
                cmap=colores,
                norm=BoundaryNorm(
                    [-0.5, 0.5, 1.5, 2.5, 255.5],
                    colores.N
                )
            )

        im = ax.imshow(
            datos,
            extent=extent,
            **kwargs
        )

        ax.set_title(titulo)
        ax.set_xlabel("Este UTM (m)")
        ax.set_ylabel("Norte UTM (m)")

        if i != 5:
            fig.colorbar(
                im,
                ax=ax,
                shrink=0.7
            )

    fig.suptitle(
        f"NISAR - {NOMBRE_ZONA}\n"
        "Analisis multitemporal exploratorio",
        fontsize=15
    )

    figura = (
        SALIDA / f"{PREFIJO_ARCHIVOS}_procesamiento_multitemporal.png"
    )

    plt.savefig(figura, dpi=170)
    plt.close(fig)

    # ======================================
    # 14. RESULTADO
    # ======================================

    print("\n================================")
    print("PROCESAMIENTO COMPLETADO")
    print("================================")

    print("Carpeta:", SALIDA)
    print("Mapa:", figura.name)

    print(
        "Area total de candidatos de cambio (clases 1 y 2):",
        round(float(area_candidatos), 2),
        "hectareas"
    )

    print(
        "IMPORTANTE: Esta area no equivale "
        "a deforestacion confirmada."
    )


if __name__ == "__main__":
    main()
