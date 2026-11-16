import streamlit as st
import pandas as pd
import numpy as np
import time
import base64
import streamlit.components.v1 as components
import folium
from streamlit_folium import st_folium

# 1. Page Configuration
st.set_page_config(page_title="Dancing with the SARS", page_icon="icon.png", layout="wide", initial_sidebar_state="collapsed")

def obtener_base64(ruta_archivo):
    try:
        with open(ruta_archivo, 'rb') as f:
            return base64.b64encode(f.read()).decode()
    except:
        return None

fondo_gif = obtener_base64("fondo_header.gif")

# =====================================================================
# 🔁 CONFIGURACIÓN DE LOS 3 PUNTOS DEL MAPA (TODO EN INGLÉS)
# =====================================================================
IMG_DEMO = [
    "https://images.unsplash.com/photo-1511497584788-876760111969?q=80&w=1000&auto=format&fit=crop",
    "https://images.unsplash.com/photo-1541427468627-a89a96e5ca1d?q=80&w=1000&auto=format&fit=crop",
    "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?q=80&w=1000&auto=format&fit=crop",
    "https://images.unsplash.com/photo-1500382017468-9049fed747ef?q=80&w=1000&auto=format&fit=crop",
]

ZONAS = {
    # ---------- POINT 1: BAUDOCITO ----------
    "baudocito": {
        "nombre": "Baudocito",
        "detalle": "Medio Atrato, Chocó",
        "lat": 5.90, "lon": -76.78,
        "color": "#FA5C5E",
        
        "gif": "baudogif.gif", 
        "texto_gif": "This visualization corresponds to a frame of the GIF animation generated directly from GCOV SAR radar products extracted from ASF Vertex for the Río Quito region, Chocó, comparing October 22 and November 3, 2026. By using the HH and HV bands in their raw state, without applying any spatial smoothing filter, the texture and the original backscatter response are fully preserved, allowing an accurate appreciation of the structural patterns and natural radiometric changes that occurred in the area between both dates.",
        
        "titulo_grande": "Multitemporal Analysis",
        "graf_grande": "baudomultitiempo.png",          
        "texto_grande": "The figure compares the NISAR images of Río Quito from October 22 and November 3, 2026. In the initial and final HV maps, dark tones indicate a weak signal, such as that observed in the riverbed. In the HH and HV change maps, blue indicates signal increases and red indicates decreases. The HV change rate expresses this difference in dB per month. The last panel shows the areas pending validation, with HV decreases in red and ambiguous changes in yellow.", 
        
        "titulo_cuadrada": "Radar Variations",
        "graf_cuadrada": "baudomapa.png",        
        "texto_cuadrada": "The map on the left shows HV decreases in red and ambiguous changes in yellow. By grouping neighboring pixels with HV decrease, 112 scattered patches were identified. In the map on the right, all these patches appear in gray because they fell below the 0.50 ha threshold. The largest occupies 0.32 ha.",
        
        "stats_html": """<div class="sar-stats-container">
<div class="stats-header">
<div>
<div class="sar-stats-title">TOTAL RASTER SURFACE</div>
<div class="sar-stats-total">1,117.80 ha</div>
</div>
<div class="stats-subtitle">Río Quito, Chocó</div>
</div>
<div class="sar-stacked-bar">
<div class="bar-grey" style="width: 98.79%;"></div>
<div class="bar-red" style="width: 0.63%;"></div>
<div class="bar-orange" style="width: 0.49%;"></div>
<div class="bar-blue" style="width: 0.09%;"></div>
</div>
<div class="sar-legend">
<div class="leg-item"><span class="leg-dot bar-grey"></span><span class="leg-name">No indication</span><span class="leg-val">1,104.32 ha</span><span class="leg-pct">98.79 %</span></div>
<div class="leg-item"><span class="leg-dot bar-red"></span><span class="leg-name">HV decrease</span><span class="leg-val">7.00 ha</span><span class="leg-pct">0.63 %</span></div>
<div class="leg-item"><span class="leg-dot bar-orange"></span><span class="leg-name">Radiometrically ambiguous change</span><span class="leg-val">5.52 ha</span><span class="leg-pct">0.49 %</span></div>
<div class="leg-item"><span class="leg-dot bar-blue"></span><span class="leg-name">No data</span><span class="leg-val">0.96 ha</span><span class="leg-pct">0.09 %</span></div>
</div>
</div>"""
    },
    
    # ---------- POINT 2: SAN ISIDRO ----------
    "san_isidro": {
        "nombre": "San Isidro",
        "detalle": "Río Quito, Chocó",
        "lat": 5.62465, "lon": -76.7490,     
        "color": "#FC8E42",
        "poligono": [(-76.795, 5.580), (-76.703, 5.580), (-76.703, 5.670), (-76.795, 5.670), (-76.795, 5.580)],
        "gif": "gifSI.gif",                  
        "texto_gif": "Animation of the scientific product NISAR L2 GCOV, obtained directly from the official consultation platform. It presents radar backscatter information of the Earth's surface, without additional processing by our team.",
        "titulo_grande": "Multitemporal Analysis",
        "graf_grande": "multitemporalSI.png",  
        "texto_grande": "635.20 hectares with indications of change were identified, of which 196.56 ha show a persistent decrease in the HV signal. The patches allow locating the priority areas for analysis.",
        "titulo_cuadrada": "Radar Variations",
        "graf_cuadrada": "mapaSI.png",       
        "texto_cuadrada": "The maps show variations in the HH and HV radar signal, with outstanding changes in the Río Quito corridor, possibly associated with humidity, fluvial dynamics, or vegetation alterations.",
        
        "stats_html": """<div class="sar-stats-container">
<div class="sar-stats-title">TOTAL ANALYZED SURFACE</div>
<div class="sar-stats-total">10,240 ha</div>
<div class="sar-stacked-bar">
<div class="bar-grey" style="width: 93.8%;"></div>
<div class="bar-red" style="width: 1.92%;"></div>
<div class="bar-orange" style="width: 4.28%;"></div>
</div>
<div class="sar-legend">
<div class="leg-item"><span class="leg-dot bar-grey"></span><span class="leg-name">No indication</span><span class="leg-val">9,604.80 ha</span><span class="leg-pct">93.80 %</span></div>
<div class="leg-item"><span class="leg-dot bar-red"></span><span class="leg-name">Persistent HV decrease</span><span class="leg-val">196.56 ha</span><span class="leg-pct">1.92 %</span></div>
<div class="leg-item"><span class="leg-dot bar-orange"></span><span class="leg-name">Ambiguous change</span><span class="leg-val">438.64 ha</span><span class="leg-pct">4.28 %</span></div>
</div>
</div>"""
    },
    
    # ---------- POINT 3: PIE DE PATO ----------
    "pie_de_pato": {
        "nombre": "Pie de Pato",
        "detalle": "Alto Baudó, Chocó",
        "lat": 5.5258, "lon": -76.9950,      
        "color": "#F8F7F2",
        "gif": "patogif.gif",                  
        "texto_gif": "Animation of the scientific product NISAR L2 GCOV in HV polarization for the six analyzed dates, cropped to the study area and smoothed with a Lee filter. It allows tracking the evolution of radar backscatter in the surroundings of Pie de Pató with the same grayscale. It corresponds to the same GIF as the San Isidro region due to its proximity.",
        "titulo_grande": "Multitemporal Analysis",
        "graf_grande": "patomultitemporal.png",          
        "texto_grande": "275.52 hectares with indications of change were identified, of which 168.76 ha show a persistent decrease in the HV signal. No patch exceeds 0.5 ha: candidates appear as isolated pixels, without clearly defined priority areas.",
        "titulo_cuadrada": "Radar Variations",
        "graf_cuadrada": "patomapa.png",        
        "texto_cuadrada": "The maps show the variations of the HH and HV radar signal between June 26 and October 12, 2026. The change is distributed almost uniformly, without extensive areas of decrease. The most visible contrasts follow the north-south linear feature and the eastern relief, possibly associated with the radar observation geometry rather than vegetation alterations.",
        
        "stats_html": """<div class="sar-stats-container">
<div class="sar-stats-title">TOTAL ANALYZED SURFACE</div>
<div class="sar-stats-total">10,100.24 ha</div>
<div class="sar-stacked-bar">
<div class="bar-grey" style="width: 97.27%;"></div>
<div class="bar-red" style="width: 1.67%;"></div>
<div class="bar-orange" style="width: 1.06%;"></div>
</div>
<div class="sar-legend">
<div class="leg-item"><span class="leg-dot bar-grey"></span><span class="leg-name">No indication</span><span class="leg-val">9,824.72 ha</span><span class="leg-pct">97.27 %</span></div>
<div class="leg-item"><span class="leg-dot bar-red"></span><span class="leg-name">Persistent HV decrease</span><span class="leg-val">168.76 ha</span><span class="leg-pct">1.67 %</span></div>
<div class="leg-item"><span class="leg-dot bar-orange"></span><span class="leg-name">Ambiguous change</span><span class="leg-val">106.76 ha</span><span class="leg-pct">1.06 %</span></div>
</div>
</div>"""
    },
}

for _z in ZONAS.values():
    _z.setdefault("gif", IMG_DEMO[0])
    _z.setdefault("texto_gif", "")
    _z.setdefault("graf_grande", IMG_DEMO[2])
    _z.setdefault("graf_cuadrada", IMG_DEMO[3])
    _z.setdefault("titulo_grande", "Multitemporal Analysis")
    _z.setdefault("texto_grande", "")
    _z.setdefault("titulo_cuadrada", "Radar Variations")
    _z.setdefault("texto_cuadrada", "")
    _z.setdefault("stats_html", "")

@st.cache_data(show_spinner=False)
def src_media(ruta):
    if ruta.startswith("http"):
        return ruta
    try:
        with open(ruta, "rb") as f:
            data = base64.b64encode(f.read()).decode()
        ext = ruta.lower().rsplit(".", 1)[-1]
        mime = {"gif": "image/gif", "png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg", "webp": "image/webp"}.get(ext, "image/png")
        return f"data:{mime};base64,{data}"
    except:
        return IMG_DEMO[0]

@st.cache_data(show_spinner=False)
def proporcion_imagen(ruta):
    try:
        from PIL import Image
        import io
        if ruta.startswith("http"):
            import requests
            img = Image.open(io.BytesIO(requests.get(ruta, timeout=6).content))
        else:
            img = Image.open(ruta)
        w, h = img.size
        if img.getexif().get(274) in (5, 6, 7, 8):
            w, h = h, w
        return (w, h)
    except:
        return (16, 9)

def formato_coords(lat, lon):
    ns = "N" if lat >= 0 else "S"
    ew = "E" if lon >= 0 else "W"
    return f"{abs(lat):.4f}° {ns}, {abs(lon):.4f}° {ew}"

# 2. Base CSS and Styles
css = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;700&family=Orbitron:wght@700&display=swap');

#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
[data-testid="collapsedControl"] {display: none;}

h1, h2, h3, h4 {
    font-family: 'Orbitron', sans-serif !important;
    color: #FA5C5E !important;
    text-shadow: 0 0 5px #FA5C5E, 0 0 15px rgba(250, 92, 94, 0.5);
    text-transform: uppercase;
    letter-spacing: 2px;
}

p, span, div, li { font-family: 'Space Grotesk', sans-serif; }

[data-testid="stMetric"] {
    background: linear-gradient(135deg, rgba(40, 71, 96, 0.8) 0%, rgba(5, 35, 69, 0.8) 100%);
    border: 1px solid #FC8E42;
    border-radius: 15px;
    padding: 20px;
    box-shadow: 0 0 20px rgba(252, 142, 66, 0.2);
    backdrop-filter: blur(10px);
    text-align: center;
    transition: transform 0.3s ease;
}
[data-testid="stMetric"]:hover { transform: translateY(-5px); box-shadow: 0 0 30px rgba(252, 142, 66, 0.5); }
[data-testid="stMetricValue"] { color: #F8F7F2 !important; font-size: 3.5rem !important; font-weight: 700; }
[data-testid="stMetricLabel"] { color: #FA5C5E !important; font-size: 1.2rem !important; }

/* Círculos del equipo */
.team-circle {
    border-radius: 50%;
    width: 125px;
    height: 125px;
    object-fit: cover;
    border: 2px solid #FC8E42;
    box-shadow: 0 0 10px rgba(252, 142, 66, 0.4);
    margin: 0 auto;
    display: block;
}
.team-name { text-align: center; color: #F8F7F2; font-family: 'Orbitron', sans-serif; margin-top: 8px; font-size: 0.9rem; }
.team-role { text-align: center; color: #FA5C5E; font-size: 0.75rem; }

.logo-centro { max-width: 100%; height: auto; }

/* HEADER */
.header-container {
    display: grid; grid-template-columns: 1fr 3fr 1fr; grid-template-areas: "lillo ww by";
    align-items: center; gap: 10px; width: 100%; margin: 1rem 0 2rem 0;
}
.header-left   { grid-area: lillo; display: flex; justify-content: flex-start; align-items: center; }
.header-center { grid-area: ww;    display: flex; justify-content: center;     align-items: center; }
.header-right  { grid-area: by;    display: flex; justify-content: flex-end;   align-items: flex-end; padding-top: 60px; }
.header-left img  { width: 200px; max-width: 100%; height: auto; }
.header-right img { width: 150px; max-width: 100%; height: auto; }

/* PANEL DERECHO DEL MAPA */
.zona-nombre { font-family: 'Orbitron', sans-serif; color: #F8F7F2; font-size: 1.1rem; letter-spacing: 2px; text-transform: uppercase; margin: 0 0 2px 0; }
.zona-coords { color: #FC8E42; font-size: 0.8rem; letter-spacing: 1px; margin: 0 0 10px 0; }
.zona-vacio { display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; gap: 12px; min-height: 300px; padding: 24px; border: 1px dashed #FC8E42; border-radius: 14px; background: rgba(5, 35, 69, 0.45); color: #F8F7F2; }
.zona-vacio p { margin: 0; font-size: 1rem; line-height: 1.5; }
.zona-vacio-icono { font-size: 2.6rem; animation: zonaPulso 2s ease-in-out infinite; }
@keyframes zonaPulso { 0%, 100% { transform: scale(1); filter: drop-shadow(0 0 4px rgba(252, 142, 66, 0.3)); } 50% { transform: scale(1.15); filter: drop-shadow(0 0 14px rgba(252, 142, 66, 0.9)); } }
.zona-gif { width: 100%; height: auto; max-height: 340px; object-fit: contain; display: block; background: rgba(1, 17, 36, 0.6); border-radius: 12px; border: 1px solid #FC8E42; box-shadow: 0 0 12px rgba(252, 142, 66, 0.25); }

/* VENTANAS DE ANÁLISIS */
.sar-section { animation: sarIn 0.7s ease both; }
@keyframes sarIn { from { opacity: 0; transform: translateY(30px); } to { opacity: 1; transform: translateY(0); } }
.sar-stack { display: flex; flex-direction: column; gap: 24px; margin-top: 1.5rem; }
.sar-window { display: flex; flex-direction: column; background: linear-gradient(135deg, rgba(40, 71, 96, 0.75) 0%, rgba(5, 35, 69, 0.85) 100%); border: 1px solid #FC8E42; border-radius: 14px; overflow: hidden; box-shadow: 0 0 25px rgba(252, 142, 66, 0.18); backdrop-filter: blur(10px); transition: transform 0.3s ease, box-shadow 0.3s ease; }
.sar-window:hover { transform: translateY(-6px); box-shadow: 0 0 35px rgba(252, 142, 66, 0.45); }
.sar-titlebar { display: flex; align-items: center; gap: 8px; padding: 9px 14px; background: rgba(1, 17, 36, 0.85); border-bottom: 1px solid rgba(252, 142, 66, 0.5); font-family: 'Orbitron', sans-serif; font-size: 0.72rem; letter-spacing: 2px; color: #F8F7F2; }
.sar-dot { width: 11px; height: 11px; border-radius: 50%; display: inline-block; }
.sar-dot.r { background: #FA5C5E; } .sar-dot.o { background: #FC8E42; } .sar-dot.w { background: #F8F7F2; }
.sar-live { margin-left: auto; color: #FA5C5E; font-size: 0.7rem; animation: sarBlink 1.4s infinite; }
@keyframes sarBlink { 50% { opacity: 0.25; } }
.sar-content { display: grid; grid-template-columns: 3fr 2fr; align-items: center; }
.sar-figure { padding: 16px; }
.sar-figure img { width: 100%; height: auto; display: block; border-radius: 10px; border: 1px solid rgba(252, 142, 66, 0.4); }
.sar-body { padding: 24px 26px; }
.sar-body h4 { margin: 0 0 8px 0; font-size: 1rem !important; }
.sar-body p { color: #F8F7F2; font-size: 0.92rem; line-height: 1.55; margin: 0; text-align: justify; }

/* BARRA DE SUPERFICIE */
.sar-stats-container { padding: 20px 26px; background: rgba(1, 17, 36, 0.55); border-top: 1px solid rgba(252, 142, 66, 0.3); }
.stats-header { display: flex; justify-content: space-between; align-items: flex-end; }
.sar-stats-title { font-size: 0.75rem; color: #A0B0C0; font-weight: 700; letter-spacing: 1px; margin-bottom: 5px; text-transform: uppercase; }
.sar-stats-total { font-family: 'Orbitron', sans-serif; font-size: 1.8rem; color: #F8F7F2; margin-bottom: 18px; }
.stats-subtitle { color: #A0B0C0; font-size: 0.85rem; margin-bottom: 18px; }
.sar-stacked-bar { display: flex; gap: 4px; height: 18px; width: 100%; margin-bottom: 20px; }
.sar-stacked-bar > div { border-radius: 4px; transition: filter 0.3s ease, transform 0.2s ease; }
.sar-stacked-bar:hover > div { filter: brightness(0.6); }
.sar-stacked-bar > div:hover { filter: brightness(1.2); transform: scaleY(1.15); }
.bar-grey { background: #A4B2A6; } .bar-red { background: #C85A5A; } .bar-orange { background: #ECAE5A; } .bar-blue { background: #7C98B3; }
.sar-legend { display: flex; flex-direction: column; gap: 12px; }
.leg-item { display: flex; align-items: center; color: #F8F7F2; font-size: 0.85rem; }
.leg-dot { width: 12px; height: 12px; border-radius: 50%; margin-right: 12px; flex-shrink: 0; }
.leg-name { flex: 1; }
.leg-val { color: #A0B0C0; font-family: 'Space Grotesk', monospace; font-size: 0.9rem; margin-right: 25px; text-align: right; }
.leg-pct { font-weight: bold; width: 65px; text-align: right; }

/* CELULARES */
@media (max-width: 768px) {
    h1 { font-size: 2rem !important; } h2 { font-size: 1.5rem !important; }
    .logo-centro { min-width: 250px !important; }
    .header-container { grid-template-columns: 1fr 1fr; grid-template-areas: "ww ww" "lillo by"; row-gap: 20px; }
    .header-left { justify-content: center; margin-top: -15px; }
    .header-right { justify-content: center; align-items: center; padding-top: 0; margin-top: -15px; }
    .header-left img { width: 130px; } .header-right img { width: 110px; } 
    .team-circle { width: 80px !important; height: 80px !important; }
    .team-name { font-size: 0.8rem !important; } .team-role { font-size: 0.7rem !important; margin-bottom: 20px !important; }
    iframe[title="streamlit_folium.st_folium"] { height: 350px !important; }
    .sar-content { grid-template-columns: 1fr; }
    .sar-content.img-right .sar-figure { order: -1; }
    .sar-body { padding: 8px 18px 20px 18px; }
    .leg-val { font-size: 0.8rem; margin-right: 15px; } .leg-pct { width: 50px; font-size: 0.8rem; }
    .stats-header { flex-direction: column; align-items: flex-start; }
    .stats-subtitle { margin-top: -10px; margin-bottom: 12px; }
}
"""

if fondo_gif:
    css += f"""
    .stApp {{
        background-color: #011124;
        background-image: linear-gradient(to bottom, rgba(1, 17, 36, 0) 0%, rgba(1, 17, 36, 1) 600px), url("data:image/gif;base64,{fondo_gif}");
        background-size: cover; background-position: top center; background-attachment: fixed; background-repeat: no-repeat; color: #F8F7F2;
    }}
    """
else:
    css += ".stApp { background-color: #011124; background-image: radial-gradient(circle at 50% 0%, #052345 0%, #011124 70%); color: #F8F7F2; }"

css += "</style>"
st.markdown(css, unsafe_allow_html=True)

# 3. HEADER
lillo_b64 = obtener_base64("lilloguito.png")
ww_b64 = obtener_base64("ww.png")
by_b64 = obtener_base64("by.png")

lillo_img = f'<img src="data:image/png;base64,{lillo_b64}">' if lillo_b64 else ''
ww_img = f'<img src="data:image/png;base64,{ww_b64}" class="logo-centro">' if ww_b64 else '<h1 style="color:#F8F7F2; text-align:center;">DANCING WITH THE SARS</h1>'
by_img = f'<img src="data:image/png;base64,{by_b64}">' if by_b64 else '<span style="color:#FC8E42; font-style:italic;">by astroRatas</span>'

st.markdown(f"""
<div class="header-container">
<div class="header-left">{lillo_img}</div>
<div class="header-center">{ww_img}</div>
<div class="header-right">{by_img}</div>
</div>
""", unsafe_allow_html=True)

# 4. INTRODUCTION
intro_col, video_col = st.columns([1, 1], gap="large")
with intro_col:
    st.subheader("Why NISAR?")
    st.write("""
    Earth's surface is in an endless dance of changes. From wetland loss to deforestation and mining, our planet never stops. 
    However, in areas like the Colombian Chocó, clouds prevent constant monitoring. **NISAR (NASA-ISRO Synthetic Aperture Radar)** changes the game: its radio waves penetrate clouds and foliage, allowing us to visualize land transformation 24/7, regardless of the weather.
    """)
    st.info("📡 Operating frequencies: L-Band (NASA) and S-Band (ISRO).")
with video_col:
    st.video("https://youtu.be/zM_0aXxGN6g?si=QyNhjol2RtQhAAjM")
st.markdown("<br><br>", unsafe_allow_html=True)

with st.expander("💻 ACCESS SYSTEM LOGS (TECHNICAL DATA)"):
    st.markdown("""**Transmission Logs:**\n* Sat: NISAR-1 (L-Band & S-Band)\n* Latency: 12ms\n* Coordinates Lock: 5.6945° N, 76.6611° W (Chocó)\n\n*All datasets processed using NASA-ISRO protocols.*""")

# 5. INDICATORS
@st.cache_data
def cargar_datos_choco():
    np.random.seed(42)
    return pd.DataFrame({'lat': np.random.uniform(4.5, 7.5, 100), 'lon': np.random.uniform(-77.5, -76.0, 100), 'cambio_superficie': np.random.normal(70, 15, 100)})
datos = cargar_datos_choco()

met1, met2, met3 = st.columns(3)
met1.metric("Natural Forest (Tree Biome)", "~4,400,000 ha", "Chocó Region", delta_color="off")
met2.metric("Deforested Area", "6,945 ha", "0.158% of tree biome", delta_color="inverse")
met3.metric("Illegal Mining Area", "41,493 ha", "88% of total mining", delta_color="inverse")
st.markdown("<br><br>", unsafe_allow_html=True)

# 6. GEOGRAPHIC ANALYSIS ZONE
zona_actual = st.session_state.get("zona_sel")
cols_ratio = [5, 5] if zona_actual else [7, 3]
map_col, panel_col = st.columns(cols_ratio, gap="large")

with map_col:
    st.subheader("🌐 Real-Time Satellite Mapping (NISAR)")
    m = folium.Map(location=[5.68, -76.85], zoom_start=10, tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}", attr="Esri World Imagery")
    
    for _clave, _z in ZONAS.items():
        if "poligono" in _z:
            folium.Polygon(locations=[(la, lo) for lo, la in _z["poligono"]], color=_z["color"], weight=2, fill=True, fill_color=_z["color"], fill_opacity=0.12, interactive=False).add_to(m)
        folium.CircleMarker([_z["lat"], _z["lon"]], radius=10, color=_z["color"], fill=True, fill_color=_z["color"], tooltip=f"Click: {_z['nombre']}").add_to(m)

    _lats = [z["lat"] for z in ZONAS.values()]
    _lons = [z["lon"] for z in ZONAS.values()]
    m.fit_bounds([[min(_lats), min(_lons)], [max(_lats), max(_lons)]], padding=(40, 40))
    mapa_interactivo = st_folium(m, height=450, use_container_width=True)

if mapa_interactivo and mapa_interactivo.get("last_object_clicked"):
    _clic = mapa_interactivo["last_object_clicked"]
    zona_calculada = min(ZONAS, key=lambda k: (ZONAS[k]["lat"] - _clic["lat"]) ** 2 + (ZONAS[k]["lon"] - _clic["lng"]) ** 2)
    if st.session_state.get("zona_sel") != zona_calculada:
        st.session_state["zona_sel"] = zona_calculada
        st.rerun()

zona_sel = st.session_state.get("zona_sel")

with panel_col:
    st.subheader("⚡ Data Analysis")
    if zona_sel:
        z = ZONAS[zona_sel]
        html_panel = f"""
        <p class="zona-nombre">📍 {z['nombre']}</p>
        <p class="zona-coords">🛰️ {formato_coords(z['lat'], z['lon'])} · {z['detalle']}</p>
        <img class="zona-gif" src="{src_media(z['gif'])}">
        """
        if z.get('texto_gif'):
            html_panel += f'<p style="color: #A0B0C0; font-size: 0.85rem; margin-top: 10px; line-height: 1.4; text-align: justify;">{z["texto_gif"]}</p>'
        
        st.markdown(html_panel, unsafe_allow_html=True)
    else:
        st.markdown("""<div class="zona-vacio"><div class="zona-vacio-icono">🛰️</div><p>Click on the zone you want to learn more about.</p></div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🛰️ SYNCHRONIZE WITH SATELLITE", use_container_width=True):
        with st.status("Establishing Uplink with NISAR...", expanded=True) as status:
            st.write("📡 Connecting to orbital network...")
            time.sleep(0.6)
            st.write("🔄 Calibrating L-Band & S-Band sensors...")
            time.sleep(0.6)
            st.write("📥 Downloading SAR telemetry data...")
            time.sleep(0.8)
            st.write("✅ Decrypting coordinates...")
            time.sleep(0.4)
            status.update(label="Database Synchronized", state="complete", expanded=False)
        st.toast('NISAR Telemetry updated successfully!', icon='🛰️')

def mostrar_separador():
    st.markdown("<br><br>", unsafe_allow_html=True)
    try:
        st.image("separador.png", use_container_width=True) 
    except:
        st.markdown("<hr style='border-color: #FC8E42;'>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

mostrar_separador()

# 7.5 SUBSECCIÓN DE VENTANAS Y BARRA
if zona_sel:
    z = ZONAS[zona_sel]
    st.markdown(f"""
<div class="sar-section">
<h2 style="text-align: center;">📡 Zone Report: {z['nombre']}</h2>
<p class="zona-coords" style="text-align: center;">🛰️ {formato_coords(z['lat'], z['lon'])} · {z['detalle']}</p>
<div class="sar-stack">
<div class="sar-window">
<div class="sar-titlebar"><span class="sar-dot r"></span><span class="sar-dot o"></span><span class="sar-dot w"></span><span>&nbsp;{z['nombre'].upper()}_TIMELINE.SAR</span><span class="sar-live">● LIVE</span></div>
<div class="sar-content img-left">
<div class="sar-figure"><img src="{src_media(z['graf_grande'])}"></div>
<div class="sar-body"><h4>{z['titulo_grande']}</h4><p>{z['texto_grande']}</p></div>
</div>
</div>
<div class="sar-window">
<div class="sar-titlebar"><span class="sar-dot r"></span><span class="sar-dot o"></span><span class="sar-dot w"></span><span>&nbsp;{z['nombre'].upper()}_SNAPSHOT.SAR</span><span class="sar-live">● LIVE</span></div>
<div class="sar-content img-right">
<div class="sar-body"><h4>{z['titulo_cuadrada']}</h4><p>{z['texto_cuadrada']}</p></div>
<div class="sar-figure"><img src="{src_media(z['graf_cuadrada'])}"></div>
</div>
{z['stats_html']}
</div>
</div>
</div>
""", unsafe_allow_html=True)
    mostrar_separador()

# 8. OTROS USOS DE LA DATA
st.markdown("<h3 style='text-align: center;'>🛰️ Other Data Applications</h3>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; max-width: 720px; margin: 0 auto 1.2rem auto;'>This section compiles information on other events detected from SAR satellite data (NISAR GCOV), which are attributed to natural phenomena and not to human intervention.</p>", unsafe_allow_html=True)

IMG_ANTES   = "anteslluvia.png"
IMG_DESPUES = "despueslluvia.png"
LABEL_ANTES   = "Before"
LABEL_DESPUES = "After"
SLIDER_ANCHO_MAX = 720

SLIDER_HTML = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;700&family=Orbitron:wght@700&display=swap');
* { box-sizing: border-box; margin: 0; padding: 0; } html, body { background: transparent; font-family: 'Space Grotesk', sans-serif; } body { padding: 6px 4px 10px 4px; }
.win { max-width: @@MAXW@@px; margin: 0 auto; background: linear-gradient(135deg, rgba(40, 71, 96, 0.75) 0%, rgba(5, 35, 69, 0.85) 100%); border: 1px solid #FC8E42; border-radius: 14px; overflow: hidden; box-shadow: 0 0 25px rgba(252, 142, 66, 0.25); }
.bar { display: flex; align-items: center; gap: 8px; padding: 9px 14px; background: rgba(1, 17, 36, 0.85); border-bottom: 1px solid rgba(252, 142, 66, 0.5); font-family: 'Orbitron', sans-serif; font-size: 11px; letter-spacing: 2px; color: #F8F7F2; }
.dot { width: 11px; height: 11px; border-radius: 50%; display: inline-block; } .r { background: #FA5C5E; } .o { background: #FC8E42; } .w { background: #F8F7F2; }
.stage { position: relative; width: 100%; aspect-ratio: @@W@@ / @@H@@; overflow: hidden; cursor: ew-resize; touch-action: pan-y; user-select: none; -webkit-user-select: none; }
.stage img { position: absolute; top: 0; left: 0; width: 100%; height: 100%; object-fit: cover; display: block; pointer-events: none; -webkit-user-drag: none; }
#top { clip-path: inset(0 50% 0 0); }
.line { position: absolute; top: 0; bottom: 0; left: 50%; width: 3px; margin-left: -1.5px; background: #F8F7F2; box-shadow: 0 0 10px rgba(248, 247, 242, 0.9), 0 0 20px rgba(252, 142, 66, 0.7); pointer-events: none; }
.knob { position: absolute; top: 50%; left: 50%; width: 46px; height: 46px; margin: -23px 0 0 -23px; border-radius: 50%; background: rgba(1, 17, 36, 0.9); border: 2px solid #FC8E42; color: #F8F7F2; display: flex; align-items: center; justify-content: center; font-size: 13px; letter-spacing: 1px; box-shadow: 0 0 14px rgba(252, 142, 66, 0.7); pointer-events: none; }
.tag { position: absolute; top: 12px; padding: 5px 12px; border-radius: 999px; background: rgba(1, 17, 36, 0.8); border: 1px solid #FC8E42; color: #F8F7F2; font-family: 'Orbitron', sans-serif; font-size: 11px; letter-spacing: 2px; text-transform: uppercase; pointer-events: none; }
.tl { left: 12px; } .tr { right: 12px; }
</style>
<div class="win">
  <div class="bar"><span class="dot r"></span><span class="dot o"></span><span class="dot w"></span><span>&nbsp;BEFORE_AFTER.SAR</span></div>
  <div class="stage" id="stage">
    <img src="@@DESPUES@@"><img id="top" src="@@ANTES@@"><div class="tag tl">@@LABEL_A@@</div><div class="tag tr">@@LABEL_D@@</div><div class="line" id="line"></div><div class="knob" id="knob">&#9664; &#9654;</div>
  </div>
</div>
<script>
(function () {
  var stage = document.getElementById('stage'), top = document.getElementById('top'), line = document.getElementById('line'), knob = document.getElementById('knob'), win = document.querySelector('.win'), dragging = false;
  function setPos(x) { var r = stage.getBoundingClientRect(); var p = Math.max(0, Math.min(100, (x - r.left) / r.width * 100)); top.style.clipPath = 'inset(0 ' + (100 - p) + '% 0 0)'; line.style.left = p + '%'; knob.style.left = p + '%'; }
  stage.addEventListener('pointerdown', function (e) { dragging = true; try { stage.setPointerCapture(e.pointerId); } catch (err) {} setPos(e.clientX); }); stage.addEventListener('pointermove', function (e) { if (dragging) setPos(e.clientX); }); stage.addEventListener('pointerup', function () { dragging = false; }); stage.addEventListener('pointercancel', function () { dragging = false; });
  function fit() { try { window.frameElement.style.height = (win.getBoundingClientRect().height + 20) + 'px'; } catch (err) {} }
  window.addEventListener('load', fit); window.addEventListener('resize', fit); setTimeout(fit, 300); setTimeout(fit, 1200);
})();
</script>
"""

_w, _h = proporcion_imagen(IMG_ANTES)
_slider = (SLIDER_HTML.replace("@@MAXW@@", str(SLIDER_ANCHO_MAX)).replace("@@W@@", str(_w)).replace("@@H@@", str(_h)).replace("@@ANTES@@", src_media(IMG_ANTES)).replace("@@DESPUES@@", src_media(IMG_DESPUES)).replace("@@LABEL_A@@", LABEL_ANTES).replace("@@LABEL_D@@", LABEL_DESPUES))
_alto = int(SLIDER_ANCHO_MAX * _h / _w) + 70
if hasattr(st, "iframe"): st.iframe(_slider, height=_alto)
else: components.html(_slider, height=_alto)

st.markdown("<br><p style='text-align: justify; max-width: 720px; margin: 0 auto; color: #A0B0C0; font-size: 0.9rem;'>Bitemporal static SAR radar images (NISAR GCOV) of the Río Quito, Chocó, Colombia (October 22 and November 3, 2026). Using the RGB false color (R=HH, G=HV, B=HV/HH Ratio), a notable increase in blue tones is highlighted on the second date, evidencing changes in surface humidity and the soil's dielectric coefficient caused by temporary rains or floods. By preserving the original raw texture without smoothing filters, the meander details and the intrinsic roughness of the radar data can be fully appreciated.</p><br><br>", unsafe_allow_html=True)

# 9. TEAM SECTION
st.markdown("<h2 style='text-align: center;'>Meet the crew</h2><br>", unsafe_allow_html=True)
t1, t2, t3, t4, t5 = st.columns(5)
def render_team_member(columna, ruta_imagen, nombre, rol):
    try:
        with open(ruta_imagen, "rb") as image_file: encoded_string = base64.b64encode(image_file.read()).decode()
        img_src = f"data:image/png;base64,{encoded_string}"
    except: img_src = "https://cdn-icons-png.flaticon.com/512/3011/3011270.png"
    with columna: st.markdown(f'<img src="{img_src}" class="team-circle"><div class="team-name">{nombre}</div><div class="team-role">{rol}</div>', unsafe_allow_html=True)

render_team_member(t1, "checho.png", "Sergio Carrasquilla", "Physics Student / Data Processing")
render_team_member(t2, "camila.png", "Camila Perez", "Physics Student / Data Analyst")
render_team_member(t3, "angie.png", "Angie Gómez", "Physics Student / Frontend & UI Design")
render_team_member(t4, "leon.png", "Leonardo Tovar", "Physics Student / Image Processing")
render_team_member(t5, "moteo.png", "Mateo Maldonado", "Physics Student / Remote Sensing")
st.markdown("<br><br>", unsafe_allow_html=True)
