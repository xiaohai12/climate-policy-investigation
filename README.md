# 🌍 CO₂ Emission Visualization — Vulcan FFCO₂ v4

An interactive **Streamlit** web app to visualize yearly **CO₂ emissions** across the U.S. using the **Vulcan FFCO₂ Yearly Gridded Emissions v4** GeoTIFF rasters. The app lets you select a year and overlays emissions on a web map with a clear color legend and transparent background (only non-zero cells are shown).

---

## ✨ Features
- 🗺️ Interactive Folium map (zoom, pan, layer toggles)  
- 📅 Year slider to switch between annual rasters  
- 🎨 Color legend (tonne CO₂/km²/year) and transparent background  
- ⚡ Caching for fast reloads  
- 🧰 Works fully offline once data are downloaded  

---

## 📊 Data Source
- **Dataset:** Vulcan FFCO₂ Yearly Gridded Emissions v4  
- **Portal:** https://earth.gov/ghgcenter/data-catalog/vulcan-ffco2-yeargrid-v4  
- **Notes:** Each `.tif` is a yearly gridded emission raster over the U.S.

---

## 📁 Repository Structure
climate-policy-investigation/
├── streamlit_app.py               # Streamlit application
├── requirements.txt     # Python dependencies
├── README.md            # This file
└── AIR_CO2_USA/         # Place your GeoTIFF files here
    ├── vulcan_ffco2_yeargrid_v4_2010.tif
    ├── vulcan_ffco2_yeargrid_v4_2011.tif
    .....

🔴 **Important:** The app expects all `.tif` files under `./AIR_CO2_USA/`.


## ✅ Prerequisites
- Python **3.10–3.12**  
- Ability to create a virtual environment (recommended)  

---

## ⚙️ Installation
```bash
git clone https://github.com/xiaohai12/climate-policy-investigation.git
cd climate-policy-investigation

# (Recommended) create a virtual environment
python -m venv venv
# macOS/Linux
source venv/bin/activate
# Windows
# venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt


## ⚙️ Running
Run app :
streamlit run streamlit_app.py