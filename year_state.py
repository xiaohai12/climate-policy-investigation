import streamlit as st
import geopandas as gpd
import rasterio
import numpy as np
import glob, os
from rasterstats import zonal_stats
import folium
from streamlit_folium import st_folium
import branca


# ================================
# Streamlit UI
# ================================
st.set_page_config(page_title="State-Level CO₂ Summary", layout="wide")
st.title("🗺️ CO₂ Emissions per US State (Aggregated from 1 km raster)")

DATA_DIR = "AIR_CO2_USA"
SHAPEFILE = "cb_2024_us_state_5m/cb_2024_us_state_5m.shp"

# ================================
# Load CO₂ Raster Files
# ================================
tif_files = sorted(glob.glob(os.path.join(DATA_DIR, "*.tif")))
if not tif_files:
    st.error("❌ No TIF files found in folder.")
    st.stop()

# Extract years from filenames
files_by_year = {}
for fp in tif_files:
    year = int(os.path.basename(fp).split("_")[-1][:4])
    files_by_year.setdefault(year, []).append(fp)

years = sorted(files_by_year.keys())
selected_year = st.slider(
    "Select Year",
    min_value=int(min(years)),
    max_value=int(max(years)),
    value=int(min(years)),     # default starting year
    step=1
)
tif_list = files_by_year[selected_year]


# ================================
# Load USA States Shapefile
# ================================
@st.cache_data
def load_states():
    gdf = gpd.read_file(SHAPEFILE)
    gdf = gdf.to_crs("EPSG:4326")  # ensure WGS84
    return gdf

# states = load_states()


# ================================
# Compute State-Level CO₂ Sums
# ================================
@st.cache_data(show_spinner=True)
def compute_state_sums(tif_list):
    states = load_states()   # load inside function (OK for caching)
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

        vals = np.array([d["sum"] for d in zs], dtype="float64")
        vals = np.nan_to_num(vals, nan=0.0)
        results.append(vals)

    totals = np.sum(np.vstack(results), axis=0)

    states_out = states.copy()
    states_out["emission_sum"] = totals/1e6
    return states_out


states_sum = compute_state_sums(tif_list)
states_sum['year']= selected_year


# ================================
# Build Folium Choropleth Map
# ================================
m = folium.Map(location=[39, -98], zoom_start=4, tiles="CartoDB positron")

folium.Choropleth(
    geo_data=states_sum,
    name="State CO₂ sum",
    data=states_sum,
    columns=["NAME", "emission_sum"],
    key_on="feature.properties.NAME",
    fill_color="YlOrRd",
    fill_opacity=0.8,
    line_opacity=0.3,
    nan_fill_opacity=0,
    legend_name=f"Total CO₂ Emissions in {selected_year} (million tons)"
).add_to(m)

# Tooltip layer
folium.GeoJson(
    states_sum,
    name="State details",
    tooltip=folium.GeoJsonTooltip(
        fields=["NAME", "emission_sum"],
        aliases=["State:", "Total CO₂ (million tons):"],
        localize=True
    )
).add_to(m)
# ============================================================
# Custom Legend (HTML) — NO OVERLAP EVER
# ============================================================


folium.LayerControl().add_to(m)

# ============================================================
# Display in Streamlit
# ============================================================
st_folium(m, width=900, height=600)


# ============================================================
# Bar Chart: State Emissions for Selected Year
# ============================================================
st.subheader(f"📊 CO₂ Emissions by State in {selected_year} (million tons)")

# Prepare sorted bar chart data
bar_df = (
    states_sum[["NAME", "emission_sum"]]
    .rename(columns={"NAME": "State", "emission_sum": "CO₂ (million tons)"})
    .sort_values("CO₂ (million tons)", ascending=False)
)

# Streamlit bar chart
st.bar_chart(
    bar_df.set_index("State"),
    use_container_width=True
)


# show the data table
with st.expander("Show State-Level CO₂ Emission Data Table"):
    st.dataframe(
        states_sum[["NAME", "emission_sum", "year"]].rename(
            columns={
                "NAME": "State",
                "emission_sum": "Total CO₂ Emissions (million tons)",
                "year": "Year"
            }
        ).sort_values(by="Total CO₂ Emissions (million tons)", ascending=False).reset_index(drop=True),
        use_container_width=True
    )
