import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from pyproj import Transformer, CRS
import numpy as np
import geopandas as gpd
from shapely.geometry import Polygon

# 1. KONFIGURASI HALAMAN
st.set_page_config(layout="wide", page_title="WebGIS Lot Tanah Malaysia")
st.title("🏛️ WebGIS Lot Tanah (Versi Online)")

# 2. SIDEBAR (TASK 4: Kawalan Layer)
with st.sidebar:
    st.header("⚙️ Tetapan Peta")
    
    # Mapping untuk elakkan ralat CRSError
    map_negeri = {
        "Selangor (3376)": 3376,
        "Johor (3375)": 3375,
        "Kedah/Perlis (3377)": 3377,
        "N.Sembilan/Melaka (3378)": 3378,
        "Pahang (3379)": 3379,
        "Perak (3380)": 3380,
        "Kelantan (3381)": 3381,
        "Terengganu (3382)": 3382
    }
    
    pilihan_negeri = st.selectbox("Pilih Negeri:", list(map_negeri.keys()))
    epsg_id = map_negeri[pilihan_negeri]
    epsg_code = f"EPSG:{epsg_id}"

    st.divider()
    st.subheader("🛠️ Kawalan Layer (Task 4)")
    show_stn = st.checkbox("Paparkan No. Stesen", value=True)
    show_geom = st.checkbox("Paparkan Bering & Jarak", value=True)
    mode_satelit = st.checkbox("Aktifkan Imej Satelit (Task 3)", value=True)

# 3. FUNGSI PENGIRAAN (TASK 1)
def calculate_geom(p1, p2):
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    dist = np.sqrt(dx**2 + dy**2)
    bearing = np.degrees(np.arctan2(dx, dy)) % 360
    return bearing, dist

# Inisialisasi Transformer
transformer = Transformer.from_crs(epsg_code, "EPSG:4326", always_xy=True)

# 4. BAHAGIAN MUAT NAIK
uploaded_file = st.file_uploader("Muat naik fail CSV (E, N, STN)", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    df.columns = df.columns.str.upper().str.strip()
    df = df.dropna(subset=['E', 'N'])

    # Tukar ke WGS84
    df['lon'], df['lat'] = zip(*df.apply(lambda r: transformer.transform(r['E'], r['N']), axis=1))

    # TASK 1: Kira Luas (GeoPandas)
    poly_shape = Polygon(zip(df['E'], df['N']))
    gdf = gpd.GeoDataFrame(index=[0], crs=epsg_code, geometry=[poly_shape])
    area_m2 = gdf.area.iloc[0]
    
    st.success(f"✅ Luas Terkira: {area_m2:.2f} m² | {area_m2 * 0.000247105:.3f} Ekar")

    # TASK 3: Overlay Satelit
    m = folium.Map(location=[df['lat'].mean(), df['lon'].mean()], zoom_start=19)
    
    if mode_satelit:
        folium.TileLayer(
            tiles='https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
            attr='Google Satelit', name='Satelit', overlay=False
        ).add_to(m)
    else:
        folium.TileLayer('openstreetmap').add_to(m)

    # Lukis Lot
    points = list(zip(df['lat'], df['lon']))
    folium.Polygon(locations=points, color="yellow", fill=True, fill_opacity=0.2).add_to(m)

    # TASK 4: On/Off Maklumat
    for i in range(len(df)):
        p1, p2 = df.iloc[i], df.iloc[(i + 1) % len(df)]
        if show_stn:
            folium.Marker([p1['lat'], p1['lon']], 
                icon=folium.DivIcon(html=f'<div style="color:white; background:red; border-radius:50%; width:20px; text-align:center; font-weight:bold;">{int(p1["STN"])}</div>')).add_to(m)
        if show_geom:
            brg, dst = calculate_geom((p1['E'], p1['N']), (p2['E'], p2['N']))
            mid = [(p1['lat']+p2['lat'])/2, (p1['lon']+p2['lon'])/2]
            folium.Marker(mid, icon=folium.DivIcon(html=f'<div style="color:cyan; font-size:8pt; text-shadow:1px 1px black;">{dst:.1f}m<br>{brg:.0f}°</div>')).add_to(m)

    folium.LayerControl().add_to(m)
    st_folium(m, width="100%", height=600)

    # TASK 2: Export GeoJSON
    st.download_button("📥 Muat Turun GeoJSON (Task 2)", data=gdf.to_json(), file_name="lot.geojson")

else:
    st.info("Sila muat naik CSV untuk bermula.")