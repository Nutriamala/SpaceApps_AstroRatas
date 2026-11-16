import streamlit as st
import pandas as pd
import numpy as np
import time
import base64
from streamlit_image_comparison import image_comparison
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
.team-name { 
    text-align: center; 
    color: #F8F7F2; 
    font-family: 'Orbitron', sans-serif; 
    margin-top: 8px; 
    font-size: 0.9rem; 
}
.team-role { 
    text-align: center; 
    color: #FA5C5E; 
    font-size: 0.75rem; 
}

/* Base para el logo central */
.logo-centro {
    max-width: 100%;
    height: auto;
}

/* =========================================
   📱 OPTIMIZACIÓN RESPONSIVE (CELULARES)
   ========================================= */
@media (max-width: 768px) {
    h1 { font-size: 2rem !important; }
    h2 { font-size: 1.5rem !important; }
    
    /* AGRANDAMOS EL LOGO CENTRAL "WW" SOLO EN CELULAR */
    .logo-centro { 
        min-width: 250px !important; 
    }
    
    /* REORDENAMOS EL HEADER PARA QUE WW QUEDE ARRIBA Y LOS OTROS ABAJO */
    .header-center { 
        order: 1 !important; 
        flex: 0 0 100% !important; 
        margin-bottom: 20px !important;
    }
    .header-left { 
        order: 2 !important; 
        justify-content: center !important; 
    }
    .header-right { 
        order: 3 !important; 
        justify-content: center !important; 
        align-items: center !important; 
        padding-top: 0 !important; 
    }
    
    .team-circle { width: 80px !important; height: 80px !important; }
    .team-name { font-size: 0.8rem !important; }
    .team-role { font-size: 0.7rem !important; margin-bottom: 20px !important; }
    
    iframe { height: 350px !important; }
}
"""

if fondo_gif:
    css += f"""
    .stApp {{
        background-color: #011124;
        background-image: linear-gradient(to bottom, rgba(1, 17, 36, 0) 0%, rgba(1, 17, 36, 1) 600px), url("data:image/gif;base64,{fondo_gif}");
        background-size: cover; 
        background-position: top center;
        background-attachment: fixed;
        background-repeat: no-repeat;
        color: #F8F7F2;
    }}
    """
else:
    css += ".stApp { background-color: #011124; background-image: radial-gradient(circle at 50% 0%, #052345 0%, #011124 70%); color: #F8F7F2; }"

css += "</style>"
st.markdown(css, unsafe_allow_html=True)

# 3. HEADER (LILLOGUITO 200px Y WW RESPONSIVE APILADO EN CELULAR)
lillo_b64 = obtener_base64("lilloguito.png")
ww_b64 = obtener_base64("ww.png")
by_b64 = obtener_base64("by.png")

# Mantenemos tus 200px para lilloguito
lillo_img = f'<img src="data:image/png;base64,{lillo_b64}" style="width: 200px;">' if lillo_b64 else ''
# Le metemos la clase para controlarlo desde el celular
ww_img = f'<img src="data:image/png;base64,{ww_b64}" class="logo-centro">' if ww_b64 else '<h1 style="color:#F8F7F2; text-align:center;">DANCING WITH THE SARS</h1>'
by_img = f'<img src="data:image/png;base64,{by_b64}" style="width: 150px;">' if by_b64 else '<span style="color:#FC8E42; font-style:italic;">by astroRatas</span>'

st.markdown(f"""
<div class="header-container" style="display: flex; flex-wrap: wrap; flex-direction: row; justify-content: space-between; align-items: center; width: 100%; margin-top: 1rem; margin-bottom: 2rem;">
<div class="header-left" style="flex: 1; display: flex; justify-content: flex-start; align-items: center;">
{lillo_img}
</div>
<div class="header-center" style="flex: 3; display: flex; justify-content: center; align-items: center;">
{ww_img}
</div>
<div class="header-right" style="flex: 1; display: flex; justify-content: flex-end; align-items: flex-end; padding-top: 60px;">
{by_img}
</div>
</div>
""", unsafe_allow_html=True)

# 4. INTRODUCTION & YOUTUBE VIDEO
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

# Expander para info
with st.expander("💻 ACCEDER A REGISTROS DE SISTEMA (DATOS TÉCNICOS)"):
    st.markdown("""
    **Transmission Logs:**
    * Sat: NISAR-1 (L-Band & S-Band)
    * Latency: 12ms
    * Coordinates Lock: 5.6945° N, 76.6611° W (Chocó)
    
    *All datasets processed using NASA-ISRO protocols.*
    """)

# 5. INDICATOR PANELS
@st.cache_data
def cargar_datos_choco():
    np.random.seed(42)
    return pd.DataFrame({
        'lat': np.random.uniform(4.5, 7.5, 100), 
        'lon': np.random.uniform(-77.5, -76.0, 100),
        'cambio_superficie': np.random.normal(70, 15, 100)
    })
datos = cargar_datos_choco()

met1, met2, met3 = st.columns(3)
met1.metric("Transformed Area (Chocó)", "4,250 ha", "+15% Expansion")
met2.metric("NISAR Radar Coherence", "0.88", "Optimal Signal (L-Band)")
met3.metric("Surface Alerts", "342", "Critical", delta_color="inverse")

st.markdown("<br><br>", unsafe_allow_html=True)

# 6. GEOGRAPHIC ANALYSIS ZONE
map_col, panel_col = st.columns([7, 3], gap="large")

with map_col:
    st.subheader("🌐 Real-Time Satellite Mapping (NISAR)")
    
    m = folium.Map(
        location=[5.2, -76.8], 
        zoom_start=6.5, 
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}", 
        attr="Esri World Imagery"
    )
    
    folium.CircleMarker([5.6945, -76.6611], radius=10, color="#FA5C5E", fill=True, fill_color="#FA5C5E", tooltip="Click: Quibdó (North)").add_to(m)
    folium.CircleMarker([5.7125, -77.2675], radius=10, color="#FC8E42", fill=True, fill_color="#FC8E42", tooltip="Click: Nuquí (Coast)").add_to(m)
    folium.CircleMarker([4.1667, -76.9667], radius=10, color="#F8F7F2", fill=True, fill_color="#F8F7F2", tooltip="Click: San Juan (South)").add_to(m)

    mapa_interactivo = st_folium(m, height=450, use_container_width=True)

with panel_col:
    st.subheader("⚡ Data Analysis")
    
    if mapa_interactivo and mapa_interactivo.get("last_object_clicked"):
        lat_clic = mapa_interactivo["last_object_clicked"]["lat"]
        
        if round(lat_clic, 2) == 5.69:
            st.markdown("**📍 Zone: Quibdó (North)**")
            st.markdown("<span style='color:#FA5C5E;'>Alert Level: 85 ha transformed</span>", unsafe_allow_html=True)
            st.bar_chart(pd.DataFrame({'Deforestation': [20, 35, 50, 85]}, index=['2021', '2022', '2023', '2024']), color="#FA5C5E")
            
        elif round(lat_clic, 2) == 5.71:
            st.markdown("**📍 Zone: Nuquí (Coast)**")
            st.markdown("<span style='color:#FC8E42;'>Alert Level: 42 ha transformed</span>", unsafe_allow_html=True)
            st.bar_chart(pd.DataFrame({'Deforestation': [10, 15, 25, 42]}, index=['2021', '2022', '2023', '2024']), color="#FC8E42")
            
        elif round(lat_clic, 2) == 4.17:
            st.markdown("**📍 Zone: San Juan (South)**")
            st.markdown("<span style='color:#F8F7F2;'>Alert Level: 110 ha transformed</span>", unsafe_allow_html=True)
            st.bar_chart(pd.DataFrame({'Deforestation': [50, 70, 90, 110]}, index=['2021', '2022', '2023', '2024']), color="#F8F7F2")
    else:
        st.info("👆 Click on a red marker on the map to analyze the sector data.")
        st.bar_chart(pd.DataFrame({'Deforestation': [0, 0, 0, 0]}, index=['2021', '2022', '2023', '2024']), color="#333333")

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

# 7. CUSTOM DIVIDER
st.markdown("<br><br>", unsafe_allow_html=True)
try:
    st.image("separador.png", use_container_width=True) 
except:
    st.markdown("<hr style='border-color: #FC8E42;'>", unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

# 8. DYNAMIC MULTITEMPORAL ANALYSIS
st.subheader("🛰️ Surface Change Monitor")
st.write("Select a zone and period to compare radar reflectance data.")

ctrl1, ctrl2, ctrl3 = st.columns(3)
with ctrl1:
    zona_seleccionada = st.selectbox("📍 Analysis Zone:", ["Chocó - Quibdó", "Chocó - Nuquí (Coast)"])
with ctrl2:
    anio_antes = st.selectbox("📅 Base Date (Before):", ["2020", "2021", "2022"])
with ctrl3:
    anio_despues = st.selectbox("📅 Current Date (After):", ["2023", "2024"])

if zona_seleccionada == "Chocó - Quibdó":
    img_antes = "https://images.unsplash.com/photo-1511497584788-876760111969?q=80&w=1000&auto=format&fit=crop"
    img_despues = "https://images.unsplash.com/photo-1541427468627-a89a96e5ca1d?q=80&w=1000&auto=format&fit=crop"
else:
    img_antes = "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?q=80&w=1000&auto=format&fit=crop"
    img_despues = "https://images.unsplash.com/photo-1500382017468-9049fed747ef?q=80&w=1000&auto=format&fit=crop"

_, col_centro, _ = st.columns([1, 6, 1])
with col_centro:
    image_comparison(
        img1=img_antes,
        img2=img_despues,
        label1=f"Before ({anio_antes})",
        label2=f"After ({anio_despues})",
        width=900,
        starting_position=50,
        show_labels=True,
        make_responsive=True,
    )

st.markdown("<br><br><br>", unsafe_allow_html=True)

# 9. TEAM SECTION
st.markdown("<h2 style='text-align: center;'>Meet the crew</h2><br>", unsafe_allow_html=True)

t1, t2, t3, t4, t5 = st.columns(5)

def render_team_member(columna, ruta_imagen, nombre, rol):
    try:
        with open(ruta_imagen, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode()
        img_src = f"data:image/png;base64,{encoded_string}"
    except:
        img_src = "https://cdn-icons-png.flaticon.com/512/3011/3011270.png"

    with columna:
        st.markdown(f"""
            <img src="{img_src}" class="team-circle">
            <div class="team-name">{nombre}</div>
            <div class="team-role">{rol}</div>
        """, unsafe_allow_html=True)

render_team_member(t1, "checho.png", "Sergio Carrasquilla", "Physics Student / Data Processing")
render_team_member(t2, "camila.png", "Camila Perez", "Physics Student / Data Analyst")
render_team_member(t3, "angie.png", "Angie Gómez", "Physics Student / Frontend & UI Design")
render_team_member(t4, "leon.png", "Leonardo Tovar", "Physics Student / Image Processing")
render_team_member(t5, "moteo.png", "Mateo Maldonado", "Physics Student / Remote Sensing")
st.markdown("<br><br>", unsafe_allow_html=True)
