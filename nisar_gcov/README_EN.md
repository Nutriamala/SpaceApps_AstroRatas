# Reusable NISAR L2 GCOV SAR Processing Guide

Example scripts for downloading, cropping, analyzing, and visualizing NISAR **HH/HV** data in any study area **supported by the available acquisitions and polarizations**.

> **Exploratory use only:** radar change detections do not, by themselves, confirm deforestation, flooding, or biomass loss. The thresholds are heuristic and require local verification. This repository does not implement Random Forest.

## 1. Configure your study area here

Open **[`config.py`](config.py)**. This is normally the only file you need to edit:

```python
# HERE, set the folder containing your GeoTIFFs or where they will be saved.
CARPETA_DATOS = Path(__file__).resolve().parent / 'datos'
# Alternative path example: Path('/path/to/my/files')

# HERE, set a name for your study area and the prefix for all output files.
NOMBRE_ZONA = 'Study area'
PREFIJO_ARCHIVOS = 'AOI'

# HERE, set the search point (longitude, latitude).
PUNTO_BUSQUEDA = (-75.0, 5.0)  # EXAMPLE: change this

# HERE, set the analysis rectangle (west, south, east, north).
BBOX = (-75.05, 4.95, -74.95, 5.05)  # EXAMPLE: change this

# HERE, choose your date range.
FECHA_INICIO = '2026-06-01'  # EXAMPLE: change this
FECHA_FIN = '2026-10-01'     # EXAMPLE: change this

# If you know the stable track/frame identifier, enter it here.
# Otherwise, leave it as None: the downloader will try to group compatible scenes.
PATRON_GRANULO = None
```

The sample coordinates and dates above are **illustrative** and have not been verified for data coverage. **In the provided `config.py`, these values are set to `None` so users must configure their own area of interest (AOI)** before downloading.

`CRS_DESTINO = None` automatically determines the UTM zone from the bounding box, where UTM is applicable. Alternatively, specify a projected EPSG CRS **with meter units**. Output pixel spacing is set using `RESOLUCION_M = 20`, but **resampling to 20 m does not mean the sensor's native spatial resolution is 20 m**.

## 2. Requirements

Python 3.10+. On Ubuntu/WSL, you can install the GDAL command-line tools using `sudo apt install gdal-bin` (with NETCDF/HDF5 driver support compatible with the product). Then run:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

On Windows, activate the virtual environment with `.venv\Scripts\activate`, and ensure `gdalwarp` and `gdalinfo` are available on your PATH if you plan to download data.

**Authentication:** to download from Earthdata, set up NASA Earthdata Login access and a local `~/.netrc` file for GDAL `/vsicurl`, following the official documentation. **Never commit your `.netrc`, passwords, cookies, or tokens to the repository.** You do not need a NASA connection to process previously downloaded GeoTIFFs.

## 3. Processing pipeline

| Order | Script | What it does |
|---|---|---|
| 1 | `descargar_nisar.py` | Searches for NISAR GCOV products, selects compatible dates, and extracts HH (`HHHH`) and HV (`HVHV`) subsets. Requires an AOI, dates, internet access, and authentication. |
| 2 | `procesar_nisar.py` | Reads **linear-power** rasters, applies an **approximate** Lee filter, computes multitemporal differences and an HV trend, and creates an **UNVALIDATED** categorical candidate map. Requires at least four dates. |
| 3 | `analizar_clases.py` | Counts pixels and calculates hectares per category. |
| 4 | `analizar_parches.py` | Identifies connected patches in class 1; calculates their areas, centroids, and distances to class 2; exports CSV, GeoJSON, GeoTIFF, and a figure. |
| Optional | `comparar_fechas.py` | Direct HH/HV comparison between two dates (without Lee filtering). |
| Optional | `generar_rgb.py` | Creates an exploratory false-color composite **R=HH, G=HV, B=HV/HH** for each date using Lee-filtered GeoTIFFs in dB. |
| Optional | `generar_gif.py` | Creates a chronological GIF from the generated RGB images (any number of dates >= 2). |

```bash
python descargar_nisar.py
python procesar_nisar.py
python analizar_clases.py
python analizar_parches.py

# Optional
python comparar_fechas.py
python generar_rgb.py
python generar_gif.py
```

**Already have GeoTIFFs?** Skip `descargar_nisar.py` and place them in `CARPETA_DATOS`, following these names and replacing `AOI` with the `PREFIJO_ARCHIVOS` value from `config.py`:

- `AOI_HH_YYYYMMDD.tif`
- `AOI_HV_YYYYMMDD.tif`

Both polarizations must correspond to the same acquisition date, extent, CRS, and aligned pixel grid. The files used by `procesar_nisar.py` must contain **positive linear-power values**, not values already converted to dB.

## 4. Interpreting the candidate map

- `0`: no change detected under the applied thresholds.
- `1`: persistent HV decrease under the exploratory rules.
- `2`: candidate near radiometrically dark surfaces (**ambiguous** change; **not** a validated water mask).
- `255`: no data.

By default, the change detection algorithm compares the median of the **first two** dates with the median of the **last two** dates (configured by `FECHAS_POR_GRUPO`). Class 2 is a subset of change candidates flagged by a low-backscatter proximity heuristic; **classes 1 and 2 must not be reported as confirmed deforestation**.

The distance to class 2 calculated by `analizar_parches.py` is **not the distance to a river**. The `AREA_DESTACADA_HA` threshold is used only to highlight patches in the visualization; it does not exclude them from the GeoJSON or CSV. Patch IDs will change when the AOI changes.

The `HV/HH` index is a ratio of **linear powers**; its equivalent in dB is `HV_dB - HH_dB`. The false-color composite uses consistent percentile scaling across dates to support visual comparison, but it must not be treated as a validated vegetation classification.

## 5. Output products

- `datos/`: original HH/HV GeoTIFFs and optional simple change maps.
- `datos/procesados/`: Lee-filtered maps, HH/HV change layers, HV trend and variability, the candidate map, JSON metadata, a summary CSV, and a multitemporal figure.
- `datos/procesados/parches/`: WGS84 GeoJSON polygons, a CSV, patch-ID raster, and patch map.
- `datos/procesados/RGB_HV_HH/`: RGB PNG/GeoTIFF composites, HV/HH ratio layers, and a GIF.

> **Note:** searching and downloading depend on NISAR scene availability, product polarizations, Earthdata permissions, and GDAL compatibility. These conditions are not guaranteed for every region.

## 6. Safe publication

This package contains no author-specific personal file paths, private coordinates, identities, or credentials. Scientific data files are excluded from Git via `.gitignore` to prevent accidental uploads of large files or secrets. Before distributing sample data, check their source, permissions, and size.

**Testing status:** `procesar_nisar.py`, `analizar_clases.py`, `analizar_parches.py`, `comparar_fechas.py`, `generar_rgb.py`, and `generar_gif.py` were tested using synthetic GeoTIFF data. Remote downloading must be tested with your own Earthdata/GDAL access; it has not been verified here against a new study area.
