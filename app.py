import streamlit as st
import folium
from streamlit_folium import st_folium
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import os
import glob
import json
import base64
from typing import Dict, Any, List, Optional
from plotly.subplots import make_subplots

# -----------------------------------------------------------------------------
# 1. PAGE CONFIGURATION & CUSTOM CSS (Brand Colors: #712416 & #f8fafc)
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Landscape Assessment",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    /* Global Light Theme */
    .stApp {
        background-color: #f8fafc;
        color: #1e293b;
        font-family: 'Inter', sans-serif;
    }
    
    /* Clean white sidebar */
    [data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e2e8f0;
    }
    
    /* Force typography to dark charcoal for maximum contrast */
    [data-testid="stMarkdownContainer"] p, 
    [data-testid="stMarkdownContainer"] h1, 
    [data-testid="stMarkdownContainer"] h2, 
    [data-testid="stMarkdownContainer"] h3,
    .stSelectbox label,
    .stToggle label {
        color: #1e293b !important;
    }
    
    /* Professional Light Dropdowns */
    div[data-baseweb="select"] > div {
        background-color: #ffffff !important;
        color: #1e293b !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 6px;
    }
    ul[data-baseweb="menu"] {
        background-color: #ffffff !important;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    li[data-baseweb="option"] {
        color: #1e293b !important;
    }
    li[data-baseweb="option"]:hover {
        background-color: #f1f5f9 !important;
    }
    
    /* Top Header Bar */
    .header-banner {
        background: linear-gradient(90deg, #712416 0%, #9b2c1d 100%);
        padding: 16px 24px;
        border-radius: 8px;
        margin-bottom: 24px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 4px 12px rgba(113, 36, 22, 0.15);
    }
    
    .header-title {
        color: #ffffff;
        font-size: 1.25rem;
        font-weight: 700;
        margin: 0;
    }
    .header-subtitle {
        color: #f8fafc;
        font-size: 0.85rem;
        opacity: 0.95;
        margin: 4px 0 0 0;
    }

    /* Light Metric Cards */
    .metric-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-top: 3px solid #712416;
        border-radius: 8px;
        padding: 18px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }
    
    .metric-label {
        font-size: 0.75rem; 
        color: #64748b; 
        font-weight: 700;
        letter-spacing: 0.5px;
        text-transform: uppercase;
    }

    .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #1e293b;
        margin: 4px 0;
    }
    
    .metric-desc {
        font-size: 0.75rem; 
        color: #94a3b8;
    }

    /* Badges */
    .badge-burgundy {
        background-color: #712416;
        color: #ffffff;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 600;
        display: inline-block;
        margin-bottom: 12px;
    }
</style>
""", unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# 2. SEED DATA & CONSTANTS
# -----------------------------------------------------------------------------
LCAT_ELEMENTS = [
    "Landform and topography",
    "Hydrology",
    "Land cover and Agriculture",
    "Cultural and historical features",
    "Visual and Sensory qualities",
    "Wildlife and Biodiversity richness",
    "Infrastructure and Economic factors",
    "Community and Governance"
]

ELEMENT_COLORS = {
    "Landform and topography": "#D89A2B",
    "Hydrology": "#0284c7", # Deepened for light theme contrast
    "Land cover and Agriculture": "#16a34a", # Deepened for light theme contrast
    "Cultural and historical features": "#db2777", # Deepened for light theme contrast
    "Visual and Sensory qualities": "#7c3aed", # Deepened for light theme contrast
    "Wildlife and Biodiversity richness": "#ea580c", # Deepened for light theme contrast
    "Infrastructure and Economic factors": "#64748b",
    "Community and Governance": "#ca8a04", # Deepened for light theme contrast
    "Unknown": "#cbd5e1"
}

DISTRICT_CENTERS = {
    "Bastar": {"lat": 19.35, "lng": 81.80, "bounds": [[18.90, 81.55], [19.75, 82.50]]},
    "Kanker": {"lat": 20.27, "lng": 81.49, "bounds": [[19.90, 80.95], [20.75, 81.95]]},
    "Dhamtari": {"lat": 20.70, "lng": 81.55, "bounds": [[20.40, 81.20], [21.05, 81.90]]},
    "Kondagaon": {"lat": 19.60, "lng": 81.66, "bounds": [[19.30, 81.30], [19.90, 82.00]]},
    "Aligarh": {"lat": 27.89, "lng": 78.08, "bounds": [[27.65, 77.40], [28.25, 78.20]]},
    "Banda": {"lat": 25.48, "lng": 80.33, "bounds": [[24.85, 80.05], [25.55, 80.85]]},
    "Jhabua": {"lat": 22.76, "lng": 74.59, "bounds": [[22.50, 74.30], [23.00, 74.80]]},
    "Sehore": {"lat": 23.20, "lng": 77.08, "bounds": [[22.90, 76.80], [23.50, 77.40]]},
    "Prayagraj": {"lat": 25.43, "lng": 81.84, "bounds": [[25.10, 81.50], [25.80, 82.20]]},
    "Dhar": {"lat": 22.59, "lng": 75.30, "bounds": [[22.30, 75.00], [22.90, 75.60]]}
}

@st.cache_data
def load_data_from_folder() -> pd.DataFrame:
    """Reads GPDP Excel/CSV files from 'data/' folder and aggregates them to Village level."""
    data_dir = "data"
    
    if os.path.exists(data_dir):
        # Scan for Excel and CSV files
        all_files = glob.glob(os.path.join(data_dir, "*.xlsx")) + glob.glob(os.path.join(data_dir, "*.csv"))
        # Filter for files containing "GPDP" in the filename
        gpdp_files = [f for f in all_files if "GPDP" in os.path.basename(f) or "gpdp" in os.path.basename(f).lower()]
        
        if gpdp_files:
            df_list = []
            for f in gpdp_files:
                try:
                    if f.endswith('.csv'):
                        df = pd.read_csv(f)
                    else:
                        df = pd.read_excel(f)
                    df_list.append(df)
                except Exception as e:
                    st.error(f"Error reading {f}: {e}")
            
            if df_list:
                raw_df = pd.concat(df_list, ignore_index=True)
                
                # Clean the theme text (e.g., "1) Hydrology" -> "Hydrology")
                if 'Theme' in raw_df.columns:
                    raw_df['Clean_Theme'] = raw_df['Theme'].astype(str).apply(lambda x: x.split(')')[-1].strip() if ')' in x else x)
                else:
                    raw_df['Clean_Theme'] = 'Unknown'
                    
                villages = []
                np.random.seed(42) # Ensure consistent random offsets for lat/lng
                
                required_cols = ['State', 'District', 'Block', 'Panchayat/Village']
                missing = [c for c in required_cols if c not in raw_df.columns]
                
                if not missing:
                    grouped = raw_df.groupby(['State', 'District', 'Block', 'Panchayat/Village'])
                    for name, group in grouped:
                        state, district, block, village_name = name
                        total_demand = len(group)
                        
                        if 'Tier' in group.columns:
                            t1 = len(group[group['Tier'].astype(str).str.contains('Tier 1', na=False)])
                            t2 = len(group[group['Tier'].astype(str).str.contains('Tier 2', na=False)])
                            t3 = len(group[group['Tier'].astype(str).str.contains('Tier 3', na=False)])
                        else:
                            t1 = t2 = t3 = 0
                        
                        dominant = group['Clean_Theme'].mode()
                        dom_element = dominant.iloc[0] if not dominant.empty else "Unknown"
                        
                        # Apply a small random offset around the district center so points don't perfectly overlap
                        center = DISTRICT_CENTERS.get(district, {"lat": 21.0, "lng": 81.0})
                        lat = center["lat"] + np.random.uniform(-0.15, 0.15)
                        lng = center["lng"] + np.random.uniform(-0.15, 0.15)
                        
                        villages.append({
                            "name": village_name,
                            "state": state,
                            "district": district,
                            "block": block,
                            "lat": lat,
                            "lng": lng,
                            "totalDemand": total_demand,
                            "tier1": t1,
                            "tier2": t2,
                            "tier3": t3,
                            "dominantElement": dom_element
                        })
                    if villages:
                        return pd.DataFrame(villages)

    # -------------------------------------------------------------------------
    # FALLBACK DATA (If 'data/' folder is missing or empty)
    # -------------------------------------------------------------------------
    st.warning("No valid GPDP files found in 'data/' folder. Using fallback data.")
    fallback_data = [
        {"name": "Sidesar", "state": "Chhattisgarh", "district": "Bastar", "block": "Bakawand", "lat": 19.12, "lng": 81.85, "totalDemand": 28, "tier1": 8, "tier2": 8, "tier3": 12, "dominantElement": "Land cover and Agriculture"},
        {"name": "Karpawand", "state": "Chhattisgarh", "district": "Bastar", "block": "Bakawand", "lat": 19.18, "lng": 81.92, "totalDemand": 45, "tier1": 15, "tier2": 18, "tier3": 12, "dominantElement": "Hydrology"},
        {"name": "Nagarnar", "state": "Chhattisgarh", "district": "Bastar", "block": "Jagdalpur", "lat": 19.08, "lng": 82.10, "totalDemand": 36, "tier1": 10, "tier2": 14, "tier3": 12, "dominantElement": "Infrastructure and Economic factors"},
        {"name": "Tokapal", "state": "Chhattisgarh", "district": "Bastar", "block": "Tokapal", "lat": 18.98, "lng": 81.78, "totalDemand": 52, "tier1": 20, "tier2": 18, "tier3": 14, "dominantElement": "Wildlife and Biodiversity richness"},
        {"name": "Narharpur", "state": "Chhattisgarh", "district": "Kanker", "block": "Narharpur", "lat": 20.35, "lng": 81.65, "totalDemand": 40, "tier1": 12, "tier2": 16, "tier3": 12, "dominantElement": "Hydrology"},
        {"name": "Charama", "state": "Chhattisgarh", "district": "Kanker", "block": "Charama", "lat": 20.48, "lng": 81.38, "totalDemand": 30, "tier1": 9, "tier2": 11, "tier3": 10, "dominantElement": "Landform and topography"},
        {"name": "Antagarh", "state": "Chhattisgarh", "district": "Kanker", "block": "Antagarh", "lat": 20.08, "lng": 81.18, "totalDemand": 65, "tier1": 24, "tier2": 26, "tier3": 15, "dominantElement": "Land cover and Agriculture"},
        {"name": "Keskal", "state": "Chhattisgarh", "district": "Kondagaon", "block": "Keskal", "lat": 19.88, "lng": 81.58, "totalDemand": 58, "tier1": 20, "tier2": 22, "tier3": 16, "dominantElement": "Landform and topography"},
        {"name": "Makdi", "state": "Chhattisgarh", "district": "Kondagaon", "block": "Makdi", "lat": 19.72, "lng": 81.82, "totalDemand": 34, "tier1": 10, "tier2": 14, "tier3": 10, "dominantElement": "Cultural and historical features"},
        {"name": "Nagri", "state": "Chhattisgarh", "district": "Dhamtari", "block": "Nagri", "lat": 20.55, "lng": 81.85, "totalDemand": 48, "tier1": 16, "tier2": 18, "tier3": 14, "dominantElement": "Hydrology"},
        {"name": "Kurud", "state": "Chhattisgarh", "district": "Dhamtari", "block": "Kurud", "lat": 20.82, "lng": 81.71, "totalDemand": 22, "tier1": 6, "tier2": 8, "tier3": 8, "dominantElement": "Infrastructure and Economic factors"},
    ]
    return pd.DataFrame(fallback_data)

def get_demand_color(demand: int) -> str:
    if demand <= 35:
        return "#fef08a" # Lighter amber
    elif demand <= 65:
        return "#f59e0b" # Deep amber
    elif demand <= 90:
        return "#ea580c" # Orange
    return "#712416" # Brand burgundy


# -----------------------------------------------------------------------------
# 2.5 POPULATION RASTER PROCESSOR
# -----------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def get_population_raster_overlay(raster_path: str, bounds: Optional[List[List[float]]] = None):
    """
    Reads a GeoTIFF raster window based on target bounds, 
    applies a colormap to actual population values, and returns base64 image + bounds.
    Requires: rasterio, matplotlib
    """
    try:
        import rasterio
        from rasterio.windows import from_bounds
        from rasterio.enums import Resampling
        import matplotlib.pyplot as plt
        import matplotlib.colors as mcolors
        from PIL import Image
        from io import BytesIO
        
        with rasterio.open(raster_path) as src:
            if bounds:
                min_lat, min_lon = bounds[0]
                max_lat, max_lon = bounds[1]
                
                # Fetch only the pixels intersecting the map viewport
                window = from_bounds(min_lon, min_lat, max_lon, max_lat, src.transform)
                window = window.intersection(rasterio.windows.Window(0, 0, src.width, src.height))
                
                if window.width <= 0 or window.height <= 0:
                    return None, None
                    
                # Constrain max resolution for performant browser rendering
                out_shape = (1, int(window.height), int(window.width))
                max_dim = 1200
                scale = 1.0
                if out_shape[1] > max_dim or out_shape[2] > max_dim:
                    scale = max_dim / max(out_shape[1], out_shape[2])
                    out_shape = (1, int(out_shape[1] * scale), int(out_shape[2] * scale))
                    
                data = src.read(1, window=window, out_shape=out_shape, resampling=Resampling.bilinear)
                
                # Accurately project bounds to fit downscaled overlay
                win_transform = src.window_transform(window)
                if scale != 1.0:
                    win_transform = win_transform * win_transform.scale(
                        (window.width / out_shape[2]),
                        (window.height / out_shape[1])
                    )
                    
                calc_bounds = rasterio.windows.bounds(
                    rasterio.windows.Window(0, 0, out_shape[2], out_shape[1]), 
                    win_transform
                )
                overlay_bounds = [[calc_bounds[1], calc_bounds[0]], [calc_bounds[3], calc_bounds[2]]]
            else:
                # Optimized state-level fallback: decimated overview
                scale = 0.05 
                out_shape = (1, int(src.height * scale), int(src.width * scale))
                data = src.read(1, out_shape=out_shape, resampling=Resampling.bilinear)
                overlay_bounds = [[src.bounds.bottom, src.bounds.left], [src.bounds.top, src.bounds.right]]
                
            if src.nodata is not None:
                data = np.ma.masked_equal(data, src.nodata)
                
            # Filter zero population blocks out dynamically to keep the map clean
            data = np.ma.masked_less_equal(data, 0)
            
            valid_data = data.compressed()
            if len(valid_data) == 0:
                return None, None
                
            # Normalize colors around 98th percentile to prevent a few dense pixels skewing rendering
            vmax = np.percentile(valid_data, 98)
            vmin = valid_data.min()
            
            # Utilizing a subtle Red/Purple colormap (RdPu) that coordinates with brand typography 
            # PowerNorm ensures lighter visibility for rural areas without dominating screen
            cmap = plt.get_cmap('RdPu')
            norm = mcolors.PowerNorm(gamma=0.4, vmin=vmin, vmax=vmax)
            
            rgba = cmap(norm(data))
            rgba[data.mask] = 0 # Strictly transparent nodata & zerodata 
            
            img = Image.fromarray((rgba * 255).astype(np.uint8))
            buffered = BytesIO()
            img.save(buffered, format="PNG")
            encoded = base64.b64encode(buffered.getvalue()).decode()
            
            return f"data:image/png;base64,{encoded}", overlay_bounds
            
    except ImportError:
        st.error("Please run `pip install rasterio matplotlib` to process the dynamic population raster layer.")
        return None, None
    except Exception as e:
        st.error(f"Failed to process population raster: {e}")
        return None, None

@st.cache_data(show_spinner=False)
def get_population_stats(raster_path: str, bounds: List[List[float]]):
    """Calculates total and mean population from a specific bounding box in the raster."""
    try:
        import rasterio
        from rasterio.windows import from_bounds
        import numpy as np
        
        with rasterio.open(raster_path) as src:
            min_lat, min_lon = bounds[0]
            max_lat, max_lon = bounds[1]
            
            # Fetch only the pixels intersecting the map viewport bounds
            window = from_bounds(min_lon, min_lat, max_lon, max_lat, src.transform)
            window = window.intersection(rasterio.windows.Window(0, 0, src.width, src.height))
            
            if window.width <= 0 or window.height <= 0:
                return 0, 0.0
                
            data = src.read(1, window=window)
            
            if src.nodata is not None:
                data = np.ma.masked_equal(data, src.nodata)
                
            # Exclude zero or negative background values
            data = np.ma.masked_less_equal(data, 0)
            valid_data = data.compressed()
            
            if len(valid_data) == 0:
                return 0, 0.0
                
            return int(valid_data.sum()), float(valid_data.mean())
    except Exception:
        return 0, 0.0

# -----------------------------------------------------------------------------
# 3. SIDEBAR & GEOGRAPHIC SELECTION
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown('<div class="badge-burgundy">DASHBOARD CONTROLS</div>', unsafe_allow_html=True)
    st.subheader("Geographic Filters")
    
    df_villages = load_data_from_folder()
    
    # State Selector - dynamically sourced from loaded data
    available_states = df_villages["state"].dropna().unique().tolist()
    if not available_states:
        available_states = ["Unknown"]
        
    selected_state = st.selectbox("State", available_states)
    
    # District Selector - dynamically sourced based on selected state
    dist_options = ["All Districts"] + df_villages[df_villages["state"] == selected_state]["district"].dropna().unique().tolist()
        
    selected_district = st.selectbox("District", dist_options)
    
    # Map Metric
    metric_choice = st.selectbox(
        "Map Metric",
        ["Total GPDP Demand", "Dominant LCAT Element", "Implementation Tiers"]
    )
    
    # Basemap Mode
    basemap_choice = st.selectbox(
        "Basemap Style",
        ["CartoDB Positron (Light)", "CartoDB Dark", "OpenStreetMap"]
    )
    
    st.markdown("---")
    
    # -------------------------------------------------------------------------
    # DISTRICT GEOSPATIAL PNG IMAGERY (OFF BY DEFAULT)
    # -------------------------------------------------------------------------
    st.subheader("District Geospatial Imagery")
    imagery_enabled = st.toggle("Enable District Imagery", value=False, help="Display orthorectified district PNG overlay for selected year.")
    
    selected_year = "2025"
    imagery_opacity = 0.85
    custom_image_file = None
    
    if imagery_enabled:
        st.info("Displaying District PNG raster layer.")
        selected_year = st.selectbox("Imagery Year", ["2015", "2020", "2024", "2025"], index=3)
        imagery_opacity = st.slider("Overlay Opacity", min_value=0.1, max_value=1.0, value=0.85, step=0.05)
        
        custom_image_file = st.file_uploader(
            "Upload Custom District PNG", 
            type=["png", "jpg", "jpeg", "webp"],
            help="Upload a transparent district-cut geospatial PNG."
        )

    st.markdown("---")
    
    # -------------------------------------------------------------------------
    # POPULATION DENSITY LAYER (OPTIONAL)
    # -------------------------------------------------------------------------
    st.subheader("Population Layer")
    pop_layer_enabled = st.toggle("Enable Population Density (1km)", value=False, help="Display actual values from 2020 Population Density COG.")
    pop_opacity = 0.5
    if pop_layer_enabled:
        pop_opacity = st.slider("Population Layer Opacity", min_value=0.1, max_value=1.0, value=0.5, step=0.05)

# Filter Data
if selected_district != "All Districts":
    filtered_df = df_villages[(df_villages["district"] == selected_district) & (df_villages["state"] == selected_state)]
else:
    filtered_df = df_villages[df_villages["state"] == selected_state]


# -----------------------------------------------------------------------------
# 4. MAIN HEADER BANNER
# -----------------------------------------------------------------------------
st.markdown(f"""
<div class="header-banner">
    <div>
        <h1 class="header-title">Landscape Assessment Atlas</h1>
        <p class="header-subtitle">Climate Risk & Community Demand &nbsp;·&nbsp; {selected_state} › {selected_district}</p>
    </div>
</div>
""", unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# 5. HIGH-LEVEL KPI METRICS
# -----------------------------------------------------------------------------
# Calculate district population stats dynamically if a specific district is selected
tot_pop = 0
mean_pop = 0.0
show_pop_kpis = False

if selected_district != "All Districts":
    pop_raster_path = "data/population/ind_pd_2020_1km_COG.tif"
    if os.path.exists(pop_raster_path) and selected_district in DISTRICT_CENTERS:
        dist_bounds = DISTRICT_CENTERS[selected_district]["bounds"]
        tot_pop, mean_pop = get_population_stats(pop_raster_path, dist_bounds)
        if tot_pop > 0:
            show_pop_kpis = True

if show_pop_kpis:
    cols = st.columns(5)
else:
    cols = st.columns(3)

total_villages = len(filtered_df)
total_demands = filtered_df["totalDemand"].sum() if total_villages > 0 else 0
t1_demands = filtered_df["tier1"].sum() if total_villages > 0 else 0

with cols[0]:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">ACTIVE VILLAGES</div>
        <div class="metric-value">{total_villages}</div>
        <div class="metric-desc">Covered Gram Panchayats</div>
    </div>
    """, unsafe_allow_html=True)

with cols[1]:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">TOTAL GPDP DEMANDS</div>
        <div class="metric-value">{total_demands}</div>
        <div class="metric-desc">Demands Identified in Atlas</div>
    </div>
    """, unsafe_allow_html=True)

with cols[2]:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">TIER 1 (COMMUNITY ALONE)</div>
        <div class="metric-value">{t1_demands}</div>
        <div class="metric-desc">Immediate Local Delivery</div>
    </div>
    """, unsafe_allow_html=True)

if show_pop_kpis:
    with cols[3]:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">RASTER POPULATION</div>
            <div class="metric-value">{tot_pop:,.0f}</div>
            <div class="metric-desc">Total Est. (Selected Dist)</div>
        </div>
        """, unsafe_allow_html=True)
    with cols[4]:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">MEAN DENSITY</div>
            <div class="metric-value">{mean_pop:,.1f}</div>
            <div class="metric-desc">Avg per 1km Cell</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# 6. FOLIUM MAP VIEW & PNG RASTER OVERLAY
# -----------------------------------------------------------------------------
map_col, analytics_col = st.columns([1.6, 1.0])

with map_col:
    st.markdown("### Geospatial Demand & Landscape Map")
    
    # Calculate Center
    if selected_district in DISTRICT_CENTERS:
        center_lat = DISTRICT_CENTERS[selected_district]["lat"]
        center_lng = DISTRICT_CENTERS[selected_district]["lng"]
        zoom_start = 9
    else:
        # Fallback to the mean of current village coordinates
        center_lat = filtered_df["lat"].mean() if not filtered_df.empty else 21.0
        center_lng = filtered_df["lng"].mean() if not filtered_df.empty else 81.0
        zoom_start = 8

    # Basemap tiles
    tile_dict = {
        "CartoDB Positron (Light)": "CartoDB positron",
        "CartoDB Dark": "CartoDB dark_matter",
        "OpenStreetMap": "OpenStreetMap"
    }
    
    m = folium.Map(
        location=[center_lat, center_lng],
        zoom_start=zoom_start,
        tiles=tile_dict[basemap_choice],
        control_scale=True
    )
    
    # Render Population Density Raster if Enabled
    if pop_layer_enabled:
        pop_raster_path = "data/population/ind_pd_2020_1km_COG.tif"
        if os.path.exists(pop_raster_path):
            pop_bounds = None
            if selected_district in DISTRICT_CENTERS:
                pop_bounds = DISTRICT_CENTERS[selected_district]["bounds"]
            elif not filtered_df.empty:
                # Buffer viewport based on active filtered points
                pop_bounds = [
                    [filtered_df["lat"].min() - 1.0, filtered_df["lng"].min() - 1.0],
                    [filtered_df["lat"].max() + 1.0, filtered_df["lng"].max() + 1.0]
                ]
            
            with st.spinner("Processing Population Raster Window..."):
                pop_img_source, calc_bounds = get_population_raster_overlay(pop_raster_path, pop_bounds)
                
            if pop_img_source and calc_bounds:
                folium.raster_layers.ImageOverlay(
                    name="Population Density (2020)",
                    image=pop_img_source,
                    bounds=calc_bounds,
                    opacity=pop_opacity,
                    interactive=False,
                    cross_origin=False,
                    zindex=200 # Appears below the district PNG imagery (zindex:250) but over the basemap
                ).add_to(m)
        else:
            st.warning(f"Population raster file not found at: {pop_raster_path}")
            
    # Render District PNG Imagery if Enabled
    if imagery_enabled:
        target_dist = selected_district if selected_district != "All Districts" else "Bastar"
        if target_dist in DISTRICT_CENTERS:
            bounds = DISTRICT_CENTERS[target_dist]["bounds"]
            
            # If user uploaded a custom PNG, encode it; otherwise generate a demo district raster overlay
            if custom_image_file is not None:
                img_bytes = custom_image_file.read()
                encoded_png = "data:image/png;base64," + base64.b64encode(img_bytes).decode()
                image_source = encoded_png
            else:
                # SVG sample fallback representing district-cut orthorectified imagery (Light theme adjusted)
                svg_overlay = f"""
                <svg xmlns="http://www.w3.org/2000/svg" width="600" height="600" viewBox="0 0 600 600">
                    <rect width="600" height="600" fill="#f8fafc" fill-opacity="0.65" />
                    <circle cx="300" cy="300" r="220" fill="none" stroke="#712416" stroke-width="3" stroke-dasharray="8,6" />
                    <path d="M 80 400 Q 250 150 520 300" fill="none" stroke="#0284c7" stroke-width="6" />
                    <text x="40" y="60" font-family="sans-serif" font-size="24" font-weight="bold" fill="#1e293b">{target_dist} District ({selected_year})</text>
                    <text x="40" y="90" font-family="sans-serif" font-size="16" fill="#475569">Orthorectified Geospatial Composite Layer</text>
                </svg>
                """
                image_source = "data:image/svg+xml;utf8," + svg_overlay
            
            folium.raster_layers.ImageOverlay(
                name=f"District Imagery ({target_dist} - {selected_year})",
                image=image_source,
                bounds=bounds,
                opacity=imagery_opacity,
                interactive=False,
                cross_origin=False,
                zindex=250
            ).add_to(m)

    # Render Demand Village Bubbles
    for _, v in filtered_df.iterrows():
        fill_col = get_demand_color(v["totalDemand"]) if metric_choice == "Total GPDP Demand" else ELEMENT_COLORS.get(v["dominantElement"], "#cbd5e1")
        
        radius = max(6, min(22, int(v["totalDemand"] * 0.35)))
        
        # Clean, light-themed tooltip
        tooltip_html = f"""
        <div style="background-color:#ffffff; color:#1e293b; border:1px solid #e2e8f0; border-top:3px solid #712416; border-radius:6px; padding:12px; font-family:sans-serif; min-width:180px; box-shadow: 0 4px 10px rgba(0,0,0,0.08);">
            <div style="font-weight:700; font-size:14px; color:#1e293b;">{v['name']} Village</div>
            <div style="font-weight:600; font-size:12px; color:#712416; margin-top:4px;">Total GPDP Demands: {v['totalDemand']}</div>
            <div style="font-size:11px; color:#475569; border-top:1px solid #f1f5f9; margin-top:8px; padding-top:6px;">
                T1: <b>{v['tier1']}</b> · T2: <b>{v['tier2']}</b> · T3: <b>{v['tier3']}</b>
            </div>
            <div style="font-size:11px; color:#64748b; margin-top:4px;">
                Dominant Theme: <span style="color:#0f172a; font-weight:600;">{v['dominantElement']}</span>
            </div>
        </div>
        """
        
        folium.CircleMarker(
            location=[v["lat"], v["lng"]],
            radius=radius,
            color="#ffffff",
            weight=1.5,
            fill=True,
            fill_color=fill_col,
            fill_opacity=0.85,
            tooltip=folium.Tooltip(tooltip_html, sticky=True),
            popup=f"{v['name']} Village ({v['district']})"
        ).add_to(m)

    # Render Streamlit Folium
    st_folium(m, width="100%", height=560)


# -----------------------------------------------------------------------------
# 7. ANALYTICS & LCAT CHARTS (PLOTLY)
# -----------------------------------------------------------------------------
with analytics_col:
    st.markdown("### LCAT Elements & Risk Breakdown")
    
    # Localized function to fetch raw demand rows strictly for these charts, 
    # ensuring existing village-level dataframe & map logic is completely untouched.
    @st.cache_data
    def get_raw_chart_data():
        data_dir = "data"
        raw_df = pd.DataFrame()
        if os.path.exists(data_dir):
            all_files = glob.glob(os.path.join(data_dir, "*.xlsx")) + glob.glob(os.path.join(data_dir, "*.csv"))
            gpdp_files = [f for f in all_files if "GPDP" in os.path.basename(f) or "gpdp" in os.path.basename(f).lower()]
            if gpdp_files:
                df_list = []
                for f in gpdp_files:
                    try:
                        df_list.append(pd.read_csv(f) if f.endswith('.csv') else pd.read_excel(f))
                    except Exception:
                        pass
                if df_list:
                    raw_df = pd.concat(df_list, ignore_index=True)
        return raw_df
        
    raw_df = get_raw_chart_data()
    
    if not raw_df.empty:
        # Apply the same geographic filters active on the dashboard
        if selected_state != "Unknown" and 'State' in raw_df.columns:
            raw_df = raw_df[raw_df['State'] == selected_state]
        if selected_district != "All Districts" and 'District' in raw_df.columns:
            raw_df = raw_df[raw_df['District'] == selected_district]
            
        # Clean Theme formatting matching existing logic
        if 'Theme' in raw_df.columns:
            raw_df['Clean_Theme'] = raw_df['Theme'].astype(str).apply(lambda x: x.split(')')[-1].strip() if ')' in x else x)
        else:
            raw_df['Clean_Theme'] = 'Unknown'
            
        # Standardize Tier Definitions
        if 'Tier' in raw_df.columns:
            raw_df['Clean_Tier'] = raw_df['Tier'].astype(str).apply(
                lambda x: 'Tier 1 (community alone)' if 'Tier 1' in x else (
                    'Tier 2 (Minor Support)' if 'Tier 2' in x else (
                    'Tier 3 (Convergence)' if 'Tier 3' in x else 'Unknown'
                ))
            )
        else:
            raw_df['Clean_Tier'] = 'Unknown'
            
        # Retrieve Pillar data directly from Excel
        pillar_col = 'Pillars' if 'Pillars' in raw_df.columns else ('Pillar' if 'Pillar' in raw_df.columns else None)
        if pillar_col:
            raw_df['Clean_Pillar'] = raw_df[pillar_col].astype(str).fillna('Unknown')
        else:
            raw_df['Clean_Pillar'] = 'Unknown'
            
        # Existing color mapping
        tier_colors = {
            "Tier 1 (community alone)": "#d97706",
            "Tier 2 (Minor Support)": "#712416",
            "Tier 3 (Convergence)": "#0ea5e9"
        }
        tier_order = ["Tier 1 (community alone)", "Tier 2 (Minor Support)", "Tier 3 (Convergence)"]

        # -------------------------------------------------------------
        # Visualization 1: Tiers across Themes (Radial Grid)
        # -------------------------------------------------------------
        theme_tier_df = raw_df[raw_df['Clean_Tier'] != 'Unknown'].groupby(['Clean_Theme', 'Clean_Tier']).size().reset_index(name='Count')
        if not theme_tier_df.empty:
            theme_pivot = theme_tier_df.pivot(index='Clean_Theme', columns='Clean_Tier', values='Count').fillna(0)
            theme_pivot['Total'] = theme_pivot.sum(axis=1)
            theme_pivot = theme_pivot.sort_values('Total', ascending=False)
            
            plot_df_theme = theme_pivot.drop(columns=['Total']).reset_index().melt(id_vars='Clean_Theme', var_name='Tier', value_name='Count')
            
            themes_list = theme_pivot.index.tolist()
            n_themes = len(themes_list)
            
            # Formulate grid size (2 columns)
            cols = 2
            rows = max(1, (n_themes + 1) // cols)
            
            fig_theme = make_subplots(
                rows=rows, cols=cols,
                specs=[[{'type': 'domain'}] * cols] * rows,
                subplot_titles=themes_list,
                vertical_spacing=0.1
            )
            
            for i, theme in enumerate(themes_list):
                r = i // cols + 1
                c = i % cols + 1
                theme_data = plot_df_theme[plot_df_theme['Clean_Theme'] == theme]
                theme_data = theme_data[theme_data['Count'] > 0] # Filter out 0 for cleaner UI
                
                colors = [tier_colors.get(t, "#cbd5e1") for t in theme_data['Tier']]
                total = theme_pivot.loc[theme, 'Total']
                
                fig_theme.add_trace(go.Pie(
                    labels=theme_data['Tier'],
                    values=theme_data['Count'],
                    hole=0.68,
                    title={'text': f"<b>{int(total)}</b>", 'font': {'size': 15, 'color': '#1e293b'}},
                    marker=dict(colors=colors, line=dict(color='#ffffff', width=1.5)),
                    textinfo='none',
                    hoverinfo='label+percent+value',
                    name=theme,
                    sort=False
                ), row=r, col=c)
                
            fig_theme.update_layout(
                title_text="Tiers across Themes",
                title_font=dict(size=14, color="#1e293b", family="sans-serif"),
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#1e293b", size=11),
                margin=dict(l=10, r=10, t=50, b=30),
                height=160 * rows + 60,
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=-0.1 / rows, xanchor="center", x=0.5, font=dict(color="#475569"), title="")
            )
            
            # Shift generated subplot titles to sit directly underneath each ring
            for annotation in fig_theme['layout']['annotations']:
                annotation['y'] -= (1.0 / rows) * 0.95
                annotation['font'] = dict(size=11, color="#475569")
                
            st.plotly_chart(fig_theme, use_container_width=True, config={'displayModeBar': False})

        # -------------------------------------------------------------
        # Visualization 2: Tiers across 3 Pillars (Radial Grid)
        # -------------------------------------------------------------
        if pillar_col:
            pillar_tier_df = raw_df[(raw_df['Clean_Tier'] != 'Unknown') & (raw_df['Clean_Pillar'] != 'Unknown') & (raw_df['Clean_Pillar'] != 'nan')].groupby(['Clean_Pillar', 'Clean_Tier']).size().reset_index(name='Count')
            
            if not pillar_tier_df.empty:
                pillar_pivot = pillar_tier_df.pivot(index='Clean_Pillar', columns='Clean_Tier', values='Count').fillna(0)
                pillar_pivot['Total'] = pillar_pivot.sum(axis=1)
                pillar_pivot = pillar_pivot.sort_values('Total', ascending=False)
                
                plot_df_pillar = pillar_pivot.drop(columns=['Total']).reset_index().melt(id_vars='Clean_Pillar', var_name='Tier', value_name='Count')
                
                pillars_list = pillar_pivot.index.tolist()
                n_pillars = len(pillars_list)
                
                fig_pillar = make_subplots(
                    rows=1, cols=max(1, n_pillars),
                    specs=[[{'type': 'domain'}] * max(1, n_pillars)],
                    subplot_titles=pillars_list
                )
                
                for i, pillar in enumerate(pillars_list):
                    pillar_data = plot_df_pillar[plot_df_pillar['Clean_Pillar'] == pillar]
                    pillar_data = pillar_data[pillar_data['Count'] > 0]
                    colors = [tier_colors.get(t, "#cbd5e1") for t in pillar_data['Tier']]
                    total = pillar_pivot.loc[pillar, 'Total']
                    
                    fig_pillar.add_trace(go.Pie(
                        labels=pillar_data['Tier'],
                        values=pillar_data['Count'],
                        hole=0.68,
                        title={'text': f"<b>{int(total)}</b>", 'font': {'size': 18, 'color': '#1e293b'}},
                        marker=dict(colors=colors, line=dict(color='#ffffff', width=2)),
                        textinfo='none',
                        hoverinfo='label+percent+value',
                        name=pillar,
                        sort=False
                    ), row=1, col=i+1)
                    
                fig_pillar.update_layout(
                    title_text="Tiers across Pillars",
                    title_font=dict(size=14, color="#1e293b", family="sans-serif"),
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#1e293b", size=11),
                    margin=dict(l=10, r=10, t=50, b=30),
                    height=240,
                    showlegend=True,
                    legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5, font=dict(color="#475569"), title="")
                )
                
                # Shift titles underneath rings
                for annotation in fig_pillar['layout']['annotations']:
                    annotation['y'] -= 0.95
                    annotation['font'] = dict(size=12, color="#475569")
                    
                st.plotly_chart(fig_pillar, use_container_width=True, config={'displayModeBar': False})
            else:
                st.info("No mapped pillar data available for this selection.")
    else:
        st.info("No raw data available for the selected filters to generate tier breakdowns.")


# -----------------------------------------------------------------------------
# 8. VILLAGE DATA TABLE
# -----------------------------------------------------------------------------
st.markdown("### Gram Panchayat Action Registry")
if not filtered_df.empty:
    st.dataframe(
        filtered_df[["name", "district", "block", "totalDemand", "tier1", "tier2", "tier3", "dominantElement"]],
        use_container_width=True,
        hide_index=True,
        column_config={
            "name": "Village Name",
            "district": "District",
            "block": "Block",
            "totalDemand": st.column_config.ProgressColumn("Total Demands", format="%d", min_value=0, max_value=100),
            "tier1": "T1 (Local)",
            "tier2": "T2 (Minor)",
            "tier3": "T3 (Convergence)",
            "dominantElement": "Dominant LCAT Element"
        }
    )
else:
    st.info("Please adjust filters or ensure data is uploaded to view village registry.")
