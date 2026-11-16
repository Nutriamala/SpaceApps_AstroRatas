
from pathlib import Path
from PIL import Image, ImageDraw
import re
from config import CARPETA_DATOS, PREFIJO_ARCHIVOS, NOMBRE_ZONA, DURACION_GIF_MS

CARPETA = CARPETA_DATOS / "procesados" / "RGB_HV_HH"

# Buscar automaticamente los RGB por fecha
archivos = sorted(
    ruta for ruta in CARPETA.glob(f"{PREFIJO_ARCHIVOS}_RGB_*.png")
    if re.fullmatch(
        rf"{re.escape(PREFIJO_ARCHIVOS)}_RGB_\d{{8}}\.png",
        ruta.name
    )
)

if not archivos:
    raise FileNotFoundError(
        "No se encontraron imagenes RGB"
    )

print(f"Imagenes encontradas: {len(archivos)}")

if len(archivos) < 2:
    raise RuntimeError("Necesitas al menos 2 RGB para animar")

frames = []

for ruta in archivos:
    fecha = ruta.stem.replace(f"{PREFIJO_ARCHIVOS}_RGB_", "")

    imagen = Image.open(ruta).convert("RGB")

    # Ampliar para que se vea mejor
    imagen = imagen.resize(
        (imagen.width * 2, imagen.height * 2),
        Image.Resampling.NEAREST
    )

    ancho, alto = imagen.size

    # Encabezado con fecha y composicion
    lienzo = Image.new(
        "RGB",
        (ancho, alto + 100),
        "white"
    )

    lienzo.paste(imagen, (0, 100))

    dibujo = ImageDraw.Draw(lienzo)

    dibujo.text(
        (20, 15),
        f"NISAR - {NOMBRE_ZONA}",
        fill="black"
    )

    dibujo.text(
        (20, 42),
        f"Fecha: {fecha[:4]}-{fecha[4:6]}-{fecha[6:]}",
        fill="black"
    )

    dibujo.text(
        (20, 67),
        "Falso color: R=HH | G=HV | B=HV/HH",
        fill="black"
    )

    frames.append(lienzo)

    print("Agregada:", fecha)

# Guardar GIF
salida = CARPETA / f"{PREFIJO_ARCHIVOS}_RGB_fechas.gif"

frames[0].save(
    salida,
    save_all=True,
    append_images=frames[1:],
    duration=DURACION_GIF_MS,
    loop=0,
    optimize=False
)

print("\nGIF GENERADO CORRECTAMENTE")
print("Archivo:", salida)
