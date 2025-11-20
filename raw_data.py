import streamlit as st
import rasterio
from rasterio.warp import Resampling
import numpy as np
import folium
from streamlit_folium import st_folium
import branca.colormap as cm
import glob, os
from collections import defaultdict
from matplotlib import cm as mpl_cm

st.set_page_config(page_title="CO₂ Emission Map", layout="wide")
st.title("🌍 CO₂ Emission Visualization")

DATA_DIR = "AIR_CO2_USA"
tif_files = sorted(glob.glob(os.path.join(DATA_DIR, "*.tif")))

if not tif_files:
    st.error("No .tif files found!")
    st.stop()

# --- Group by year ---
files_by_year = defaultdict(list)
for fp in tif_files:
    year = int(os.path.basename(fp).split("_")[-1][:4])
    files_by_year[year].append(fp)

years = sorted(files_by_year.keys())

@st.cache_data(show_spinner=True)
def load_raster(tif_path, downsample=4):
    with rasterio.open(tif_path) as src:
        data = src.read(
            1,
            out_shape=(1, src.height // downsample, src.width // downsample),
            resampling=Resampling.average,
        )
        bounds = src.bounds
        return data, bounds

# --- Select year ---
selected_year = st.slider("Select Year", min_value=min(years), max_value=max(years))
tif_files = files_by_year[selected_year]

# --- Build map ---
m = folium.Map(location=[39, -98], zoom_start=4, tiles="CartoDB positron")

# compute global min/max for legend scaling
vals = []
for tif_path in tif_files:
    with rasterio.open(tif_path) as src:
        vals.append(src.read(1))
vals = np.concatenate([v.flatten() for v in vals])
vals = vals[np.isfinite(vals)]
vmin= 0
vmax = np.nanpercentile(vals, 99.5)

# create a continuous color scale
colormap = cm.linear.YlOrRd_09.scale(vmin, vmax)
colormap.caption = f"{selected_year} Total CO₂ Emissions (tonne CO₂ / km² / year)"

# --- Add layers ---
for tif_path in tif_files:
    data, bounds = load_raster(tif_path)
    data_clipped = np.clip(data, vmin, vmax)
    normed = (data_clipped - vmin) / (vmax - vmin)

    # --- Convert to RGBA and set transparent background ---
    cmap = mpl_cm.get_cmap("YlOrRd")
    rgba_img = cmap(normed)  # (H, W, 4) float 0–1

    # Set transparency: pixels with near-zero emission become transparent
    alpha = np.where(normed > 0.05, 1.0, 0.0)  # threshold, tweak 0.05→0.01 if needed
    rgba_img[..., -1] = alpha  # replace alpha channel

    rgba_img = np.uint8(rgba_img * 255)

    folium.raster_layers.ImageOverlay(
        image=rgba_img,
        bounds=[[bounds.bottom, bounds.left], [bounds.top, bounds.right]],
        opacity=1.0,  # keep 1.0 since alpha already applied
        name=os.path.basename(tif_path),
    ).add_to(m)

# add colorbar to map
colormap.add_to(m)

folium.LayerControl().add_to(m)

# --- Display in Streamlit ---
st_data = st_folium(m, width=900, height=600)