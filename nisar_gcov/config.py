"""CONFIGURACION UNICA: modifica este archivo para tu propia zona de estudio.

No incluyas credenciales ni datos personales en este repositorio.
Coordenadas: longitud, latitud (EPSG:4326).
"""
from pathlib import Path

# RUTAS: carpeta que contiene los GeoTIFF HH/HV y recibira los resultados.
# Cambia esta linea por Path('/ruta/a/mis/datos') si ya tienes archivos.
CARPETA_DATOS = Path(__file__).resolve().parent / 'datos'

# ETIQUETAS: nombre visible en mapas, prefijo en nombres de archivo.
NOMBRE_ZONA = 'Area de estudio'  # EJEMPLO: 'Mi zona de estudio'
PREFIJO_ARCHIVOS = 'AOI'         # EJEMPLO: 'Zona01' (sin espacios)

# AREA DE INTERES: reemplaza estos None antes de descargar.
# PUNTO_BUSQUEDA = (longitud, latitud), p.ej. (-75.0, 5.0)
PUNTO_BUSQUEDA = None
# BBOX = (oeste, sur, este, norte), p.ej. (-75.05, 4.95, -74.95, 5.05)
BBOX = None

# FECHAS: usa cadenas AAAA-MM-DD.
FECHA_INICIO = None  # EJEMPLO: '2026-06-01'
FECHA_FIN = None     # EJEMPLO: '2026-10-01'

# Descarga NISAR L2 GCOV. El patron es opcional pero recomendado
# para fijar el mismo trayecto/fotograma entre todas las fechas.
PRODUCTO_NISAR = 'NISAR_L2_GCOV_PROVISIONAL_V1'
PATRON_GRANULO = None  # EJEMPLO: 'fragmento_exacto_del_identificador'
MAX_RESULTADOS = 500
NUM_FECHAS = 6
RESOLUCION_M = 20
CRS_DESTINO = None  # None = UTM calculado automaticamente desde BBOX

# Comparacion simple de dos fechas: None = primera y ultima disponibles.
FECHA_COMPARACION_INICIAL = None  # EJEMPLO: '20260601'
FECHA_COMPARACION_FINAL = None    # EJEMPLO: '20261001'

# PARAMETROS EXPLORATORIOS. Ajustar segun el area y su validacion.
VENTANA_LEE = 3
ENL_APROX = 4.0
FECHAS_POR_GRUPO = 2
UMBRAL_HV_DB = -2.0
PERSISTENCIA_HV_DB = -1.5
AREA_DESTACADA_HA = 0.5

# GIF: duracion de cada frame en milisegundos.
DURACION_GIF_MS = 1000
