import streamlit as st
import geopandas as gpd
import rasterio
import numpy as np
import pandas as pd
import glob, os
from rasterstats import zonal_stats


# ============================================================
# Streamlit UI
# ============================================================
st.set_page_config(page_title="US CO₂ Emission Time Series", layout="wide")
st.title("📈 US State CO₂ Emission Time Series Dashboard")

DATA_DIR = "AIR_CO2_USA"
SHAPEFILE = "cb_2024_us_state_5m/cb_2024_us_state_5m.shp"


# ============================================================
# Load USA states
# ============================================================
@st.cache_data
def load_states():
    gdf = gpd.read_file(SHAPEFILE)
    return gdf.to_crs("EPSG:4326")

states_gdf = load_states()


# ============================================================
# Load raster TIFFs grouped by year
# ============================================================
tif_files = sorted(glob.glob(os.path.join(DATA_DIR, "*.tif")))
if not tif_files:
    st.error("❌ No TIFF files found!")
    st.stop()

files_by_year = {}
for fp in tif_files:
    year = int(os.path.basename(fp).split("_")[-1][:4])
    files_by_year.setdefault(year, []).append(fp)

years = sorted(files_by_year.keys())


# ============================================================
# Compute state-level emission (million tons)
# ============================================================
@st.cache_data(show_spinner=True)
def compute_state_sums(tif_list):
    states = load_states()
    results = []

    for tif in tif_list:
        with rasterio.open(tif) as src:
            raster = src.read(1)
            raster = np.where(raster < 0, 0, raster)

            zs = zonal_stats(
                vectors=states.geometry,
                raster=raster,
                affine=src.transform,
                stats=["sum"],
                nodata=None,
                geojson_out=False
            )

        vals = np.array([d["sum"] for d in zs], dtype=float)
        vals = np.nan_to_num(vals, nan=0.0)
        results.append(vals)

    totals = np.sum(np.vstack(results), axis=0)

    states_out = states.copy()
    states_out["emission_sum"] = totals / 1e6     # convert to million tons
    return states_out[["NAME", "emission_sum"]]


# ============================================================
# Build full panel (state × year)
# ============================================================
@st.cache_data(show_spinner=True)
def build_panel(files_by_year):
    rows = []
    for yr, flist in files_by_year.items():
        df = compute_state_sums(flist)
        df["year"] = yr
        rows.append(df)
    return pd.concat(rows, ignore_index=True)

panel_df = build_panel(files_by_year)


# ============================================================
# UI: State selection
# ============================================================
state_list = sorted(panel_df["NAME"].unique())
selected_state = st.selectbox("Select a State", state_list)


# ============================================================
# Extract time-series for selected state
# ============================================================
df_state = (
    panel_df[panel_df["NAME"] == selected_state]
    .sort_values("year")
    .rename(columns={"emission_sum": "CO₂ (million tons)"})
    .reset_index(drop=True)
)


# ============================================================
# Plot line chart
# ============================================================
st.subheader(f"📈 CO₂ Emissions for {selected_state} (All Years)")

st.line_chart(
    df_state.set_index("year")["CO₂ (million tons)"],
    use_container_width=True
)


# ============================================================
# Display data table
# ============================================================
st.subheader("📄 Data Table")

st.dataframe(df_state, use_container_width=True)