import streamlit as st
import folium
from streamlit_folium import st_folium
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import os
import glob
import textwrap
import base64
from typing import Dict, Any, List, Optional
import rasterio
from rasterio.windows import from_bounds
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

try:
    from streamlit_plotly_events import plotly_events
    HAS_PLOTLY_EVENTS = True
except ImportError:
    HAS_PLOTLY_EVENTS = False

# -----------------------------------------------------------------------------
# 1. PAGE CONFIGURATION & CUSTOM CSS (Brand Colors: #712416 & #f8fafc)
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Landscape Assessment",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Removed all fragile CSS hitboxes, negative margins, and nth-child rules.
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
    
    /* Overlay Quote Cards */
    .quote-card {
        background: #f8fafc;
        border-left: 4px solid #712416;
        padding: 16px;
        margin-bottom: 16px;
        border-radius: 0 6px 6px 0;
    }
    .quote-text {
        font-size: 1.05rem;
        color: #0f172a;
        font-style: italic;
        margin-bottom: 12px;
    }
    .quote-meta {
        font-size: 0.8rem;
        color: #475569;
    }
    .quote-meta span {
        font-weight: 600;
        color: #1e293b;
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
    "Hydrology": "#0284c7", 
    "Land cover and Agriculture": "#16a34a",
    "Cultural and historical features": "#db2777",
    "Visual and Sensory qualities": "#7c3aed",
    "Wildlife and Biodiversity richness": "#ea580c", 
    "Infrastructure and Economic factors": "#64748b",
    "Community and Governance": "#ca8a04",
    "Unknown": "#cbd5e1"
}

TIER_COLORS = {
    "Tier 1 (community alone)": "#d97706",
    "Tier 2 (Minor Support)": "#712416",
    "Tier 3 (Convergence)": "#0ea5e9"
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
        all_files = glob.glob(os.path.join(data_dir, "*.xlsx")) + glob.glob(os.path.join(data_dir, "*.csv"))
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
                
                if 'Theme' in raw_df.columns:
                    raw_df['Clean_Theme'] = raw_df['Theme'].astype(str).apply(lambda x: x.split(')')[-1].strip() if ')' in x else x)
                else:
                    raw_df['Clean_Theme'] = 'Unknown'
                    
                villages = []
                np.random.seed(42)
                
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

@st.cache_data
def load_raw_demand_data() -> pd.DataFrame:
    data_dir = "data"
    all_files = glob.glob(os.path.join(data_dir, "*.xlsx")) + glob.glob(os.path.join(data_dir, "*.csv"))
    gpdp_files = [f for f in all_files if "GPDP" in os.path.basename(f) or "gpdp" in os.path.basename(f).lower()]
    df_list = []
    if gpdp_files:
        for f in gpdp_files:
            try:
                df = pd.read_csv(f) if f.endswith('.csv') else pd.read_excel(f)
                df_list.append(df)
            except Exception:
                pass
    if df_list:
        raw = pd.concat(df_list, ignore_index=True)
        if 'Theme' in raw.columns:
            raw['Clean_Theme'] = raw['Theme'].astype(str).apply(lambda x: x.split(')')[-1].strip() if ')' in x else x)
        else:
            raw['Clean_Theme'] = 'Unknown'
            
        if 'Pillars' not in raw.columns:
            raw['Pillars'] = 'Unknown'
            
        return raw
    return pd.DataFrame()

@st.cache_data
def load_landscape_trajectory() -> pd.DataFrame:
    filepath = os.path.join("data", "District Wise LCAT.xlsx")
    if os.path.exists(filepath):
        try:
            df = pd.read_excel(filepath)
            return df
        except Exception as e:
            st.error(f"Error reading Trajectory file: {e}")
    return pd.DataFrame()

@st.cache_data
def load_climate_data() -> pd.DataFrame:
    filepath = os.path.join("data", "climate_vulnerability", "climate_vulnerability_results.csv")
    if os.path.exists(filepath):
        try:
            df = pd.read_csv(filepath)
            df.columns = df.columns.str.strip().str.lower()
            return df
        except Exception as e:
            st.error(f"Error reading Climate Signals CSV: {e}")
    return pd.DataFrame()

def get_demand_color(demand: int) -> str:
    if demand <= 35:
        return "#fef08a"
    elif demand <= 65:
        return "#f59e0b"
    elif demand <= 90:
        return "#ea580c"
    return "#712416"

@st.cache_data
def get_population_stats(bounds: list) -> dict:
    pop_raster_path = os.path.join("data", "population", "ind_pd_2020_1km_COG.tif")
    if not os.path.exists(pop_raster_path):
        return {"sum": 0, "mean": 0, "available": False}
    
    try:
        with rasterio.open(pop_raster_path) as src:
            min_lat, min_lng = bounds[0]
            max_lat, max_lng = bounds[1]
            window = from_bounds(min_lng, min_lat, max_lng, max_lat, src.transform)
            
            w_data = src.read(1, window=window)
            nodata = src.nodata if src.nodata is not None else -9999
            
            valid_mask = (w_data != nodata) & (w_data > 0)
            valid_data = w_data[valid_mask]
            
            if len(valid_data) == 0:
                return {"sum": 0, "mean": 0, "available": True}
                
            return {
                "sum": int(np.sum(valid_data)),
                "mean": round(float(np.mean(valid_data)), 2),
                "available": True
            }
    except Exception as e:
        return {"sum": 0, "mean": 0, "available": False, "error": str(e)}

@st.cache_data
def get_population_raster_overlay(bounds: list) -> str:
    pop_raster_path = os.path.join("data", "population", "ind_pd_2020_1km_COG.tif")
    if not os.path.exists(pop_raster_path):
        return None
        
    try:
        with rasterio.open(pop_raster_path) as src:
            min_lat, min_lng = bounds[0]
            max_lat, max_lng = bounds[1]
            window = from_bounds(min_lng, min_lat, max_lng, max_lat, src.transform)
            
            w_data = src.read(1, window=window)
            nodata = src.nodata if src.nodata is not None else -9999
            
            data_masked = np.where((w_data == nodata) | (w_data <= 0), np.nan, w_data)
            
            if np.all(np.isnan(data_masked)):
                return None
            
            norm = mcolors.LogNorm(vmin=1, vmax=np.nanpercentile(data_masked, 99))
            cmap = plt.get_cmap('RdPu')
            
            colored_data = cmap(norm(data_masked))
            colored_data[np.isnan(data_masked)] = [0, 0, 0, 0]
            
            fig, ax = plt.subplots(figsize=(w_data.shape[1]/100, w_data.shape[0]/100), dpi=100)
            fig.patch.set_alpha(0)
            ax.imshow(colored_data, origin='upper')
            ax.axis('off')
            
            import io
            buf = io.BytesIO()
            plt.savefig(buf, format='png', bbox_inches='tight', pad_inches=0, transparent=True)
            plt.close(fig)
            
            encoded = base64.b64encode(buf.getvalue()).decode('utf-8')
            return f"data:image/png;base64,{encoded}"
            
    except Exception:
        return None

@st.dialog("Theme Insights", width="large")
def show_theme_overlay(theme: str, state: str, district: str, village: str):
    st.markdown(f"<h2 style='color: #712416; margin-top: 0;'>{theme}</h2>", unsafe_allow_html=True)
    
    col_act, col_voice = st.columns([1.2, 1.0])
    
    with col_act:
        st.markdown("### Priority Actions")
        df_gpdp = load_raw_demand_data()
        
        if not df_gpdp.empty:
            filt_gpdp = df_gpdp[(df_gpdp['State'] == state) & (df_gpdp['District'] == district) & (df_gpdp['Clean_Theme'] == theme)]
            if village != "All Villages":
                filt_gpdp = filt_gpdp[filt_gpdp['Panchayat/Village'] == village]
                
            if not filt_gpdp.empty:
                for i, row in filt_gpdp.iterrows():
                    action_text = row.get("Priority Action", "N/A")
                    tier_info = row.get("Tier", "")
                    pillar_info = row.get("Pillars", "")
                    
                    st.markdown(f"""
                    <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 6px; padding: 12px; margin-bottom: 12px;">
                        <div style="font-size: 1rem; color: #1e293b; font-weight: 500;">{i+1}. {action_text}</div>
                        <div style="font-size: 0.8rem; color: #64748b; margin-top: 8px;">
                            {'<span style="background: #f1f5f9; padding: 2px 6px; border-radius: 4px; margin-right: 8px;">' + tier_info + '</span>' if tier_info else ''}
                            {'<span style="background: #f1f5f9; padding: 2px 6px; border-radius: 4px;">' + pillar_info + '</span>' if pillar_info else ''}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No specific priority actions found for this selection.")
        else:
            st.info("Priority Action data source not available.")
            
    with col_voice:
        st.markdown("### Community Voices")
        quotes_path = os.path.join("data", "lcat", "LCAT_Verbatim_Quote_Classification.xlsx")
        
        if os.path.exists(quotes_path):
            try:
                df_quotes = pd.read_excel(quotes_path)
                
                filt_quotes = df_quotes[(df_quotes['State'] == state) & (df_quotes['District'] == district) & (df_quotes['Primary LCAT Element'] == theme)]
                display_quotes = pd.DataFrame()
                
                if village != "All Villages":
                    village_quotes = filt_quotes[filt_quotes['Village'] == village]
                    if not village_quotes.empty:
                        display_quotes = village_quotes
                    else:
                        display_quotes = filt_quotes
                        if not filt_quotes.empty:
                            st.caption("Showing *District-level evidence* (No specific quotes for selected village)")
                else:
                    display_quotes = filt_quotes
                
                if not display_quotes.empty:
                    for _, row in display_quotes.iterrows():
                        quote = row.get("Verbatim Quote", "")
                        speaker = row.get("Speaker / Attribution", "Community Member")
                        v_name = row.get("Village", "")
                        b_name = row.get("Block / Tehsil (as stated)", "")
                        
                        loc_str = ", ".join([x for x in [v_name, b_name] if pd.notna(x) and str(x).strip() != ""])
                        
                        if pd.notna(quote):
                            st.markdown(f"""
                            <div class="quote-card">
                                <div class="quote-text">"{quote}"</div>
                                <div class="quote-meta">
                                    <span>{speaker}</span> {f' • {loc_str}' if loc_str else ''}
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                else:
                    st.info("No verbatim quotes available for this theme at the selected geography.")
                    
            except Exception as e:
                st.error(f"Could not load Community Voices: {e}")
        else:
            st.info("Community Voices dataset not found.")

# -----------------------------------------------------------------------------
# 3. SIDEBAR & GEOGRAPHIC SELECTION
# -----------------------------------------------------------------------------
with st.sidebar:
    app_mode = st.radio(
        "Dashboard Mode",
        ["LCAT & GPDP", "Climate Signals"],
        index=0,
        help="Switch between landscape assessment and pure climate signal data."
    )
    
    st.markdown("---")
    
    st.markdown('<div class="badge-burgundy">DASHBOARD CONTROLS</div>', unsafe_allow_html=True)
    st.subheader("Geographic Filters")
    
    if app_mode == "LCAT & GPDP":
        df_villages = load_data_from_folder()
        available_states = df_villages["state"].dropna().unique().tolist() if not df_villages.empty else ["Unknown"]
        selected_state = st.selectbox("State", available_states, key="state_lcat")
        
        dist_options = ["All Districts"] + df_villages[df_villages["state"] == selected_state]["district"].dropna().unique().tolist()
        selected_district = st.selectbox("District", dist_options, key="dist_lcat")
        
        village_options = ["All Villages"]
        if selected_district != "All Districts":
            v_list = df_villages[(df_villages["state"] == selected_state) & (df_villages["district"] == selected_district)]["name"].dropna().unique().tolist()
            village_options.extend(v_list)
        selected_village = st.selectbox("Village / Gram Panchayat", village_options, key="vill_lcat")
        
        metric_choice = st.selectbox("Map Metric", ["Total GPDP Demand", "Highest Demand Concentration", "Implementation Tiers"])
        basemap_choice = st.selectbox("Basemap Style", ["CartoDB Positron (Light)", "CartoDB Dark", "OpenStreetMap"])
        
        st.markdown("---")
        st.subheader("Spatial Overlays")
        pop_layer_enabled = st.toggle("Enable Population Raster", value=False, help="Render actual population density from COG raster.")
        pop_opacity = st.slider("Population Raster Opacity", min_value=0.1, max_value=1.0, value=0.7, step=0.05) if pop_layer_enabled else 0.7
        
        st.markdown("---")
        st.subheader("District Geospatial Imagery")
        imagery_enabled = st.toggle("Enable District Imagery", value=False)
        selected_year = "2025"
        imagery_opacity = 0.85
        custom_image_file = None
        
        if imagery_enabled:
            selected_year = st.selectbox("Imagery Year", ["2015", "2020", "2024", "2025"], index=3)
            imagery_opacity = st.slider("Overlay Opacity", min_value=0.1, max_value=1.0, value=0.85, step=0.05)
            custom_image_file = st.file_uploader("Upload Custom District PNG", type=["png", "jpg", "jpeg", "webp"])

    else:
        climate_df = load_climate_data()
        available_states = climate_df["state"].dropna().unique().tolist() if not climate_df.empty else ["Unknown"]
        selected_state = st.selectbox("State", available_states, key="state_clim")
        
        dist_options = ["All Districts"]
        if not climate_df.empty:
            dist_options.extend(climate_df[climate_df["state"] == selected_state]["district"].dropna().unique().tolist())
            
        selected_district = st.selectbox("District", dist_options, key="dist_clim")


# -----------------------------------------------------------------------------
# LCAT & GPDP DASHBOARD LOGIC
# -----------------------------------------------------------------------------
if app_mode == "LCAT & GPDP":

    if selected_district != "All Districts":
        filtered_df = df_villages[(df_villages["district"] == selected_district) & (df_villages["state"] == selected_state)]
    else:
        filtered_df = df_villages[df_villages["state"] == selected_state]
        
    if selected_village != "All Villages":
        filtered_df = filtered_df[filtered_df["name"] == selected_village]

    st.markdown(f"""
    <div class="header-banner">
        <div>
            <h1 class="header-title">Landscape Assessment Atlas</h1>
            <p class="header-subtitle">Climate Risk & Community Demand &nbsp;·&nbsp; {selected_state} › {selected_district} {f'› {selected_village}' if selected_village != 'All Villages' else ''}</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # High-level KPIs
    col1, col2, col3 = st.columns(3)
    total_villages = len(filtered_df)
    total_demands = filtered_df["totalDemand"].sum() if total_villages > 0 else 0
    t1_demands = filtered_df["tier1"].sum() if total_villages > 0 else 0

    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">ACTIVE VILLAGES</div>
            <div class="metric-value">{total_villages}</div>
            <div class="metric-desc">Covered Gram Panchayats</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">TOTAL GPDP DEMANDS</div>
            <div class="metric-value">{total_demands}</div>
            <div class="metric-desc">Demands Identified in Atlas</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">TIER 1 (COMMUNITY ALONE)</div>
            <div class="metric-value">{t1_demands}</div>
            <div class="metric-desc">Immediate Local Delivery</div>
        </div>
        """, unsafe_allow_html=True)
        
    if selected_district != "All Districts" and selected_district in DISTRICT_CENTERS:
        bounds = DISTRICT_CENTERS[selected_district]["bounds"]
        pop_stats = get_population_stats(bounds)
        
        if pop_stats.get("available", False):
            p_col1, p_col2 = st.columns(2)
            with p_col1:
                st.markdown(f"""
                <div class="metric-card" style="margin-top: 16px; border-top-color: #0f172a;">
                    <div class="metric-label">TOTAL RASTER POPULATION</div>
                    <div class="metric-value">{pop_stats['sum']:,}</div>
                    <div class="metric-desc">Dynamic sum for {selected_district} bounds</div>
                </div>
                """, unsafe_allow_html=True)
            with p_col2:
                st.markdown(f"""
                <div class="metric-card" style="margin-top: 16px; border-top-color: #0f172a;">
                    <div class="metric-label">MEAN POPULATION PER 1 KM CELL</div>
                    <div class="metric-value">{pop_stats['mean']:,}</div>
                    <div class="metric-desc">Average density across non-empty cells</div>
                </div>
                """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    map_col, analytics_col = st.columns([1.6, 1.0])

    with map_col:
        st.markdown("### Geospatial Demand & Landscape Map")
        
        if selected_district in DISTRICT_CENTERS:
            center_lat, center_lng = DISTRICT_CENTERS[selected_district]["lat"], DISTRICT_CENTERS[selected_district]["lng"]
            zoom_start = 9
        else:
            center_lat = filtered_df["lat"].mean() if not filtered_df.empty else 21.0
            center_lng = filtered_df["lng"].mean() if not filtered_df.empty else 81.0
            zoom_start = 8

        tile_dict = {
            "CartoDB Positron (Light)": "CartoDB positron",
            "CartoDB Dark": "CartoDB dark_matter",
            "OpenStreetMap": "OpenStreetMap"
        }
        
        m = folium.Map(location=[center_lat, center_lng], zoom_start=zoom_start, tiles=tile_dict[basemap_choice], control_scale=True)
        
        if pop_layer_enabled and selected_district in DISTRICT_CENTERS:
            bounds = DISTRICT_CENTERS[selected_district]["bounds"]
            pop_overlay = get_population_raster_overlay(bounds)
            if pop_overlay:
                folium.raster_layers.ImageOverlay(
                    name="Population Density (1km COG)",
                    image=pop_overlay,
                    bounds=bounds,
                    opacity=pop_opacity,
                    interactive=False,
                    cross_origin=False,
                    zindex=200
                ).add_to(m)
        
        if imagery_enabled:
            target_dist = selected_district if selected_district != "All Districts" else "Bastar"
            if target_dist in DISTRICT_CENTERS:
                bounds = DISTRICT_CENTERS[target_dist]["bounds"]
                if custom_image_file is not None:
                    encoded_png = "data:image/png;base64," + base64.b64encode(custom_image_file.read()).decode()
                    image_source = encoded_png
                else:
                    svg_overlay = f"""
                    <svg xmlns="http://www.w3.org/2000/svg" width="600" height="600" viewBox="0 0 600 600">
                        <rect width="600" height="600" fill="#f8fafc" fill-opacity="0.65" />
                        <circle cx="300" cy="300" r="220" fill="none" stroke="#712416" stroke-width="3" stroke-dasharray="8,6" />
                        <text x="40" y="60" font-family="sans-serif" font-size="24" font-weight="bold" fill="#1e293b">{target_dist} District ({selected_year})</text>
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

        for _, v in filtered_df.iterrows():
            fill_col = get_demand_color(v["totalDemand"]) if metric_choice == "Total GPDP Demand" else ELEMENT_COLORS.get(v["dominantElement"], "#cbd5e1")
            radius = max(6, min(22, int(v["totalDemand"] * 0.35)))
            
            tooltip_html = f"""
            <div style="background-color:#ffffff; color:#1e293b; border:1px solid #e2e8f0; border-top:3px solid #712416; border-radius:6px; padding:12px; font-family:sans-serif; min-width:180px; box-shadow: 0 4px 10px rgba(0,0,0,0.08);">
                <div style="font-weight:700; font-size:14px; color:#1e293b;">{v['name']} Village</div>
                <div style="font-weight:600; font-size:12px; color:#712416; margin-top:4px;">Total GPDP Demands: {v['totalDemand']}</div>
                <div style="font-size:11px; color:#475569; border-top:1px solid #f1f5f9; margin-top:8px; padding-top:6px;">
                    T1: <b>{v['tier1']}</b> · T2: <b>{v['tier2']}</b> · T3: <b>{v['tier3']}</b>
                </div>
                <div style="font-size:11px; color:#64748b; margin-top:4px;">
                    Highest Demand Concentration: <span style="color:#0f172a; font-weight:600;">{v['dominantElement']}</span>
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
            ).add_to(m)

        st_folium(m, width="100%", height=560)

    with analytics_col:
        st.markdown("### LCAT Elements & Risk Breakdown")
        st.markdown("<p style='font-size: 0.85rem; color: #64748b; margin-top: -10px; margin-bottom: 20px;'>Click a theme ring to view priority actions and community voices</p>", unsafe_allow_html=True)
        
        raw_demands = load_raw_demand_data()
        
        if not raw_demands.empty:
            filt_raw = raw_demands[raw_demands["State"] == selected_state]
            if selected_district != "All Districts":
                filt_raw = filt_raw[filt_raw["District"] == selected_district]
            if selected_village != "All Villages":
                filt_raw = filt_raw[filt_raw["Panchayat/Village"] == selected_village]
                
            st.markdown("#### Tiers across Themes")
            
            themes_list = LCAT_ELEMENTS
            themes_list_wrapped = ["<br>".join(textwrap.wrap(t, width=22)) for t in themes_list]
            
            fig_theme = make_subplots(
                rows=2, cols=4,
                specs=[[{'type': 'domain'}] * 4] * 2,
                subplot_titles=themes_list_wrapped,
                vertical_spacing=0.15,
                horizontal_spacing=0.02
            )
            
            for i, theme in enumerate(themes_list):
                theme_data = filt_raw[filt_raw['Clean_Theme'] == theme]
                t1 = len(theme_data[theme_data['Tier'].astype(str).str.contains('Tier 1', na=False)])
                t2 = len(theme_data[theme_data['Tier'].astype(str).str.contains('Tier 2', na=False)])
                t3 = len(theme_data[theme_data['Tier'].astype(str).str.contains('Tier 3', na=False)])
                
                total_t = t1 + t2 + t3
                
                r = (i // 4) + 1
                c = (i % 4) + 1
                
                fig_theme.add_trace(go.Pie(
                    labels=list(TIER_COLORS.keys()),
                    values=[t1, t2, t3],
                    hole=0.65,
                    title={'text': f"<b>{total_t}</b>", 'font': {'size': 16, 'color': '#1e293b'}},
                    marker=dict(colors=list(TIER_COLORS.values()), line=dict(color='#ffffff', width=2)),
                    textinfo='none',
                    hoverinfo='label+value',
                    name=theme,
                    showlegend=False,
                    sort=False
                ), row=r, col=c)
                
            for k, color in TIER_COLORS.items():
                fig_theme.add_trace(go.Pie(labels=[k], values=[0], marker=dict(colors=[color]), name=k, showlegend=True, sort=False), row=1, col=1)
            
            fig_theme.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#1e293b", size=11),
                margin=dict(l=10, r=10, t=40, b=60),
                height=450,
                legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5, font=dict(color="#475569"))
            )
            
            for annotation in fig_theme['layout']['annotations']:
                annotation['yanchor'] = 'top'
                annotation['y'] -= 0.12 if annotation['y'] > 0.5 else 0.05
                annotation['font'] = dict(size=11, color="#475569")
                
            if HAS_PLOTLY_EVENTS:
                clicked_points = plotly_events(
                    fig_theme, 
                    click_event=True, 
                    hover_event=False, 
                    select_event=False, 
                    key="theme_chart_events", 
                    override_height=450, 
                    override_width="100%"
                )
                if clicked_points and len(clicked_points) > 0:
                    curve_idx = clicked_points[0].get("curveNumber", -1)
                    if 0 <= curve_idx < len(themes_list):
                        selected_theme_to_open = themes_list[curve_idx]
                        show_theme_overlay(selected_theme_to_open, selected_state, selected_district, selected_village)
            else:
                st.warning("Please install `streamlit-plotly-events` to enable clickable rings.")
                st.plotly_chart(fig_theme, use_container_width=True, config={'displayModeBar': False})
            
            st.markdown("#### Tiers across Pillars")
            pillars_list = ["Adaptation", "Mitigation", "Restoration"]
            fig_pillars = make_subplots(
                rows=1, cols=3,
                specs=[[{'type': 'domain'}] * 3],
                subplot_titles=pillars_list
            )
            
            for i, pillar in enumerate(pillars_list):
                pillar_data = filt_raw[filt_raw['Pillars'].astype(str).str.contains(pillar, na=False, case=False)]
                t1 = len(pillar_data[pillar_data['Tier'].astype(str).str.contains('Tier 1', na=False)])
                t2 = len(pillar_data[pillar_data['Tier'].astype(str).str.contains('Tier 2', na=False)])
                t3 = len(pillar_data[pillar_data['Tier'].astype(str).str.contains('Tier 3', na=False)])
                
                total_p = t1 + t2 + t3
                
                fig_pillars.add_trace(go.Pie(
                    labels=list(TIER_COLORS.keys()),
                    values=[t1, t2, t3],
                    hole=0.65,
                    title={'text': f"<b>{total_p}</b>", 'font': {'size': 18, 'color': '#1e293b'}},
                    marker=dict(colors=list(TIER_COLORS.values()), line=dict(color='#ffffff', width=2)),
                    textinfo='none',
                    hoverinfo='label+value',
                    name=pillar,
                    showlegend=False,
                    sort=False
                ), row=1, col=i+1)
            
            for k, color in TIER_COLORS.items():
                fig_pillars.add_trace(go.Pie(labels=[k], values=[0], marker=dict(colors=[color]), name=k, showlegend=True, sort=False), row=1, col=1)
                
            fig_pillars.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#1e293b", size=12),
                margin=dict(l=10, r=10, t=30, b=60),
                height=300,
                legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5, font=dict(color="#475569"))
            )
            
            for annotation in fig_pillars['layout']['annotations']:
                annotation['yanchor'] = 'top'
                annotation['y'] -= 1.15
                annotation['font'] = dict(size=13, color="#1e293b")
                
            st.plotly_chart(fig_pillars, use_container_width=True, config={'displayModeBar': False})
        else:
            st.info("Raw GPDP data unavailable.")

    st.markdown("---")
    st.markdown("### District LCAT Landscape Trajectory")
    
    traj_df = load_landscape_trajectory()
    
    if not traj_df.empty:
        filtered_traj_df = traj_df[traj_df["State"] == selected_state]
        if selected_district != "All Districts":
            filtered_traj_df = filtered_traj_df[filtered_traj_df["District"] == selected_district]
            
        n_districts = len(filtered_traj_df)
        
        if n_districts > 0:
            st.markdown("#### Visual Summary")
            st.markdown(f"<p style='font-size: 0.9rem; color: #64748b; margin-top: -10px;'>Showing trajectory distribution across {n_districts} district(s).</p>", unsafe_allow_html=True)
            
            valid_themes = [t for t in LCAT_ELEMENTS if t in filtered_traj_df.columns]
            
            status_colors = {
                "Improving": "#16a34a",
                "Stable": "#0ea5e9",
                "Mixed": "#f59e0b",
                "Declining": "#dc2626",
                "Unknown": "#cbd5e1"
            }
            
            r_cols = 4
            r_rows = (len(valid_themes) + r_cols - 1) // r_cols
            
            fig_health = make_subplots(
                rows=r_rows, cols=r_cols,
                specs=[[{'type': 'domain'}] * r_cols] * r_rows,
                subplot_titles=valid_themes,
                vertical_spacing=0.28,
                horizontal_spacing=0.02
            )
            
            for i, theme in enumerate(valid_themes):
                r = (i // r_cols) + 1
                c = (i % r_cols) + 1
                
                counts = filtered_traj_df[theme].astype(str).str.strip().value_counts().reset_index()
                counts.columns = ["Status", "Count"]
                
                colors = [status_colors.get(s, status_colors["Unknown"]) for s in counts["Status"]]
                
                fig_health.add_trace(go.Pie(
                    labels=counts["Status"],
                    values=counts["Count"],
                    hole=0.65,
                    title={'text': f"<b>{n_districts}</b>", 'font': {'size': 14, 'color': '#1e293b'}},
                    marker=dict(colors=colors, line=dict(color='#ffffff', width=1.5)),
                    textinfo='none',
                    hoverinfo='label+value',
                    name=theme,
                    sort=False
                ), row=r, col=c)
            
            # Subplot height formatting explicitly separates elements
            calc_height = 280 if r_rows == 1 else 450
            y_shift = 1.05 if r_rows == 1 else 0.45
            
            fig_health.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#1e293b", size=11),
                margin=dict(l=0, r=0, t=10, b=80),
                height=calc_height,
                showlegend=True,
                legend=dict(orientation="h", yanchor="top", y=-0.2, xanchor="center", x=0.5, font=dict(color="#475569"))
            )
            
            for annotation in fig_health['layout']['annotations']:
                annotation['yanchor'] = 'top'
                annotation['y'] -= y_shift
                annotation['font'] = dict(size=11, color="#475569")
                
            st.plotly_chart(fig_health, use_container_width=True, config={'displayModeBar': False})
            
            # Standard vertical gap to prevent Matrix Overlap
            st.markdown("<br>", unsafe_allow_html=True)
            
            st.markdown("#### District × Theme Trajectory Matrix")
            
            heat_data = filtered_traj_df[["District"] + valid_themes].set_index("District")
            
            num_map = {"Improving": 3, "Stable": 2, "Mixed": 1, "Declining": 0}
            rev_map = {v: k for k, v in num_map.items()}
            heat_num = heat_data.replace(num_map).fillna(-1).apply(pd.to_numeric, errors='coerce')
            
            text_wrap_themes = ["<br>".join(textwrap.wrap(t, width=16)) for t in valid_themes]
            
            fig_matrix = go.Figure(data=go.Heatmap(
                z=heat_num.values,
                x=valid_themes,
                y=heat_data.index,
                colorscale=[
                    [0.0, status_colors["Declining"]],
                    [0.33, status_colors["Mixed"]],
                    [0.66, status_colors["Stable"]],
                    [1.0, status_colors["Improving"]]
                ],
                showscale=False,
                xgap=3,
                ygap=3,
                hovertemplate="District: %{y}<br>Theme: %{x}<br>Status: %{customdata}<extra></extra>",
                customdata=heat_data.values
            ))
            
            fig_matrix.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#1e293b", size=11),
                height=max(350, n_districts * 40 + 150),
                margin=dict(l=10, r=10, t=10, b=80),
                xaxis=dict(
                    tickangle=0,
                    ticktext=text_wrap_themes,
                    tickvals=valid_themes,
                    side="bottom"
                )
            )
            st.plotly_chart(fig_matrix, use_container_width=True, config={'displayModeBar': False})
        else:
            st.info("No district trajectory data available for the current selection.")
    else:
        st.info("Landscape Trajectory dataset (District Wise LCAT.xlsx) not found.")

# -----------------------------------------------------------------------------
# CLIMATE SIGNALS LOGIC
# -----------------------------------------------------------------------------
elif app_mode == "Climate Signals":
    
    climate_df = load_climate_data()
    
    st.markdown(f"""
    <div class="header-banner" style="background: linear-gradient(90deg, #0f172a 0%, #1e293b 100%);">
        <div>
            <h1 class="header-title">Climate Signals & Vulnerability</h1>
            <p class="header-subtitle">NDMI & LST Deviations &nbsp;·&nbsp; {selected_state} › {selected_district}</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if climate_df.empty:
        st.warning("Climate vulnerability dataset not found. Please ensure data/climate_vulnerability/climate_vulnerability_results.csv is present.")
    
    elif selected_district == "All Districts":
        st.markdown("### State Overview")
        state_df = climate_df[climate_df["state"] == selected_state]
        
        ndmi_counts = state_df["canopy_moisture_status"].value_counts().reset_index()
        ndmi_counts.columns = ["Status", "Districts"]
        lst_counts = state_df["summer_lst_status"].value_counts().reset_index()
        lst_counts.columns = ["Status", "Districts"]
        
        col_ndmi, col_lst = st.columns(2)
        
        with col_ndmi:
            fig_ndmi = px.pie(ndmi_counts, names="Status", values="Districts", title="NDMI Status Distribution", hole=0.5)
            fig_ndmi.update_layout(margin=dict(t=30, b=10, l=10, r=10), height=300)
            st.plotly_chart(fig_ndmi, use_container_width=True)
            
        with col_lst:
            fig_lst = px.pie(lst_counts, names="Status", values="Districts", title="LST Status Distribution", hole=0.5)
            fig_lst.update_layout(margin=dict(t=30, b=10, l=10, r=10), height=300)
            st.plotly_chart(fig_lst, use_container_width=True)
            
        st.info("Select a specific district from the sidebar to view detailed baseline and recent imagery.")
        
    else:
        dist_data = climate_df[(climate_df["state"] == selected_state) & (climate_df["district"] == selected_district)]
        if not dist_data.empty:
            d_row = dist_data.iloc[0]
            
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("NDMI Change", f"{d_row.get('canopy_moisture_pct_change', 'N/A')}")
            c2.metric("NDMI Status", f"{d_row.get('canopy_moisture_status', 'N/A')}")
            c3.metric("LST Change", f"{d_row.get('summer_lst_change_c', 'N/A')}")
            c4.metric("LST Status", f"{d_row.get('summer_lst_status', 'N/A')}")
            
            st.markdown("---")
            
            def render_image_triptych(prefix, title, legend_html, data_row):
                st.markdown(f"### {title}")
                
                safe_dist_name = str(selected_district).lower().replace(" ", "_")
                base_dir = os.path.join("data", "climate_vulnerability", "imagery")
                
                col_img1, col_img2, col_img3 = st.columns(3)
                
                def load_img(suffix):
                    path = os.path.join(base_dir, f"{safe_dist_name}_{prefix}_{suffix}.png")
                    if os.path.exists(path):
                        return path
                    return None
                    
                with col_img1:
                    st.markdown("**2001–2010 Baseline**")
                    img = load_img("baseline")
                    if img: st.image(img, use_container_width=True)
                    else: st.caption("Image not available")
                        
                with col_img2:
                    st.markdown("**2015–2024 Recent**")
                    img = load_img("recent")
                    if img: st.image(img, use_container_width=True)
                    else: st.caption("Image not available")
                        
                with col_img3:
                    st.markdown("**Change**")
                    img = load_img("change")
                    if img: st.image(img, use_container_width=True)
                    else: st.caption("Image not available")
                        
                st.markdown(legend_html, unsafe_allow_html=True)

            ndmi_legend = "<p style='font-size: 0.85rem; color:#475569;'><b>Red</b> → Moisture Loss / Drying &nbsp;|&nbsp; <b>White</b> → Stable &nbsp;|&nbsp; <b>Blue</b> → Moisture Gain</p>"
            render_image_triptych("ndmi", "Canopy Moisture — NDMI", ndmi_legend, d_row)
            
            st.markdown(f"""
            <div style="font-size:0.9rem; color:#475569; margin-bottom: 24px;">
            <b>Baseline:</b> {d_row.get('canopy_moisture_baseline', 'N/A')} &nbsp;|&nbsp; 
            <b>Recent:</b> {d_row.get('canopy_moisture_recent', 'N/A')} &nbsp;|&nbsp; 
            <b>Absolute Change:</b> {d_row.get('canopy_moisture_change', 'N/A')}
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("---")
            
            lst_legend = "<p style='font-size: 0.85rem; color:#475569;'><b>Blue</b> → Cooling &nbsp;|&nbsp; <b>White</b> → Stable &nbsp;|&nbsp; <b>Red</b> → Warming</p>"
            render_image_triptych("lst", "Thermal Stress — LST", lst_legend, d_row)

            st.markdown(f"""
            <div style="font-size:0.9rem; color:#475569; margin-bottom: 24px;">
            <b>Baseline:</b> {d_row.get('summer_lst_baseline_c', 'N/A')} °C &nbsp;|&nbsp; 
            <b>Recent:</b> {d_row.get('summer_lst_recent_c', 'N/A')} °C &nbsp;|&nbsp; 
            <b>Extreme Heat Days Baseline:</b> {d_row.get('extreme_heat_days_baseline', 'N/A')} &nbsp;|&nbsp; 
            <b>Extreme Heat Days Recent:</b> {d_row.get('extreme_heat_days_recent', 'N/A')} &nbsp;|&nbsp; 
            <b>Change:</b> {d_row.get('extreme_heat_days_change', 'N/A')}
            </div>
            """, unsafe_allow_html=True)

        else:
            st.warning("No data found for the selected district.")
            
    with st.expander("Methodology & Technical Details"):
        st.markdown("""
        **NDMI (Normalized Difference Moisture Index)**
        * Source: MODIS MOD09A1 (500 m)
        * Window: October–November
        * Baseline: 2001–2010 | Recent: 2015–2024
        
        **LST (Land Surface Temperature)**
        * Source: MODIS MOD11A1 (1 km)
        * Window: May–June
        * Baseline: 2001–2010 | Recent: 2015–2024
        """)
