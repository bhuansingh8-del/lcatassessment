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
import textwrap

# Try to load streamlit-plotly-events for native click interaction
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
    .stToggle label,
    .stRadio label {
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
        background: #ffffff;
        border: 1px solid #e2e8f0;
        padding: 16px 24px;
        border-radius: 8px;
        margin-bottom: 24px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
    }
    
    .header-title {
        color: #1e293b;
        font-size: 1.25rem;
        font-weight: 700;
        margin: 0;
    }
    .header-subtitle {
        color: #64748b;
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
        height: 100%;
    }
    
    .metric-label {
        font-size: 0.9rem; 
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
    "Hydrology": "#0284c7", 
    "Land cover and Agriculture": "#16a34a",
    "Cultural and historical features": "#db2777",
    "Visual and Sensory qualities": "#7c3aed",
    "Wildlife and Biodiversity richness": "#ea580c",
    "Infrastructure and Economic factors": "#64748b",
    "Community and Governance": "#ca8a04",
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
        return "#fef08a" 
    elif demand <= 65:
        return "#f59e0b" 
    elif demand <= 90:
        return "#ea580c" 
    return "#712416" 

@st.cache_data
def load_climate_data() -> pd.DataFrame:
    path = "data/climate_vulnerability/climate_vulnerability_results.csv"
    if os.path.exists(path):
        try:
            df = pd.read_csv(path)
            df.columns = df.columns.str.strip().str.lower()
            return df
        except Exception as e:
            st.error(f"Error reading climate CSV: {e}")
            return pd.DataFrame()
            
    return pd.DataFrame([
        {
            "state": "Unknown", "district": "Unknown",
            "canopy_moisture_baseline": 0.0, "canopy_moisture_recent": 0.0,
            "canopy_moisture_change": 0.0, "canopy_moisture_pct_change": "0%",
            "canopy_moisture_status": "Stable",
            "summer_lst_baseline_c": 0.0, "summer_lst_recent_c": 0.0,
            "summer_lst_change_c": 0.0, "summer_lst_status": "Stable",
            "extreme_heat_days_baseline": 0, "extreme_heat_days_recent": 0,
            "extreme_heat_days_change": 0
        }
    ])


# -----------------------------------------------------------------------------
# 2.5 POPULATION RASTER PROCESSOR
# -----------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def get_population_raster_overlay(raster_path: str, bounds: Optional[List[List[float]]] = None):
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
                window = from_bounds(min_lon, min_lat, max_lon, max_lat, src.transform)
                window = window.intersection(rasterio.windows.Window(0, 0, src.width, src.height))
                
                if window.width <= 0 or window.height <= 0:
                    return None, None
                    
                out_shape = (1, int(window.height), int(window.width))
                max_dim = 1200
                scale = 1.0
                if out_shape[1] > max_dim or out_shape[2] > max_dim:
                    scale = max_dim / max(out_shape[1], out_shape[2])
                    out_shape = (1, int(out_shape[1] * scale), int(out_shape[2] * scale))
                    
                data = src.read(1, window=window, out_shape=out_shape, resampling=Resampling.bilinear)
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
                scale = 0.05 
                out_shape = (1, int(src.height * scale), int(src.width * scale))
                data = src.read(1, out_shape=out_shape, resampling=Resampling.bilinear)
                overlay_bounds = [[src.bounds.bottom, src.bounds.left], [src.bounds.top, src.bounds.right]]
                
            if src.nodata is not None:
                data = np.ma.masked_equal(data, src.nodata)
                
            data = np.ma.masked_less_equal(data, 0)
            valid_data = data.compressed()
            if len(valid_data) == 0:
                return None, None
                
            vmax = np.percentile(valid_data, 98)
            vmin = valid_data.min()
            cmap = plt.get_cmap('RdPu')
            norm = mcolors.PowerNorm(gamma=0.4, vmin=vmin, vmax=vmax)
            
            rgba = cmap(norm(data))
            rgba[data.mask] = 0
            
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
    try:
        import rasterio
        from rasterio.windows import from_bounds
        import numpy as np
        
        with rasterio.open(raster_path) as src:
            min_lat, min_lon = bounds[0]
            max_lat, max_lon = bounds[1]
            window = from_bounds(min_lon, min_lat, max_lon, max_lat, src.transform)
            window = window.intersection(rasterio.windows.Window(0, 0, src.width, src.height))
            
            if window.width <= 0 or window.height <= 0:
                return 0, 0.0
                
            data = src.read(1, window=window)
            
            if src.nodata is not None:
                data = np.ma.masked_equal(data, src.nodata)
                
            data = np.ma.masked_less_equal(data, 0)
            valid_data = data.compressed()
            
            if len(valid_data) == 0:
                return 0, 0.0
                
            return int(valid_data.sum()), float(valid_data.mean())
    except Exception:
        return 0, 0.0

# -----------------------------------------------------------------------------
# 2.6 THEME INSIGHTS MODAL OVERLAY
# -----------------------------------------------------------------------------
@st.dialog("Theme Insights", width="large")
def show_theme_overlay(theme: str, state: str, district: str, village: str):
    st.markdown(f"<h2 style='color: #712416; margin-top: 0; margin-bottom: 20px;'>{theme}</h2>", unsafe_allow_html=True)
    
    col_act, col_voice = st.columns([1.2, 1.0])
    
    with col_act:
        st.markdown("### Priority Actions")
        gpdp_path = "data/GPDP_Action_Plans_Themed_v2_Pillars.xlsx"
        if os.path.exists(gpdp_path):
            df_gpdp = pd.read_excel(gpdp_path)
            
            if state != "Unknown":
                df_gpdp = df_gpdp[df_gpdp['State'] == state]
            if district != "All Districts":
                df_gpdp = df_gpdp[df_gpdp['District'] == district]
            if village != "All Villages":
                df_gpdp = df_gpdp[df_gpdp['Panchayat/Village'] == village]
                
            if 'Theme' in df_gpdp.columns:
                df_gpdp['Clean_Theme'] = df_gpdp['Theme'].astype(str).apply(lambda x: x.split(')')[-1].strip() if ')' in x else x)
                df_gpdp = df_gpdp[df_gpdp['Clean_Theme'] == theme]
            else:
                df_gpdp = pd.DataFrame()
                
            if not df_gpdp.empty:
             total_actions = len(df_gpdp)
             st.markdown(f"<div style='font-size: 0.95rem; color: #475569; margin-bottom: 20px;'><b>{total_actions}</b> actions</div>", unsafe_allow_html=True)
            
             tier_groups = {
                "Tier 1 — Community Led": {"color": "#d97706", "actions": []},
                "Tier 2 — Minor Support": {"color": "#712416", "actions": []},
                "Tier 3 — External Support & Convergence": {"color": "#0ea5e9", "actions": []},
                "Other / Uncategorized": {"color": "#64748b", "actions": []}
            }
            
            for i, row in df_gpdp.iterrows():
                action_text = row.get("Priority Action", "N/A")
                tier_info = str(row.get("Tier", ""))
                pillar_info = row.get("Pillars", "")
                
                action_data = {"text": action_text, "pillars": pillar_info}
                
                if 'Tier 1' in tier_info:
                    tier_groups["Tier 1 — Community Led"]["actions"].append(action_data)
                elif 'Tier 2' in tier_info:
                    tier_groups["Tier 2 — Minor Support"]["actions"].append(action_data)
                elif 'Tier 3' in tier_info:
                    tier_groups["Tier 3 — External Support & Convergence"]["actions"].append(action_data)
                else:
                    tier_groups["Other / Uncategorized"]["actions"].append(action_data)
            
            for group_name, group_data in tier_groups.items():
                    actions = group_data["actions"]
                    color = group_data["color"]
                    
                    if actions:
                        st.markdown(f"""
                        <div style="margin-top: 16px; margin-bottom: 12px;">
                            <div style="font-size: 1rem; font-weight: 700; color: {color};">{group_name}</div>
                            <div style="font-size: 0.8rem; color: #64748b;">{len(actions)} actions</div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        for idx, act in enumerate(actions, 1):
                            num_str = f"{idx:02d}"
                            pillar_info = act["pillars"]
                            pillar_html = f'<span style="background: #f1f5f9; padding: 2px 6px; border-radius: 4px; font-size: 0.75rem; color: #475569;">{pillar_info}</span>' if pd.notna(pillar_info) and str(pillar_info).strip() else ''
                            
                            st.markdown(f"""
                            <div style="background: #ffffff; border: 1px solid #e2e8f0; border-left: 4px solid {color}; border-radius: 6px; padding: 12px; margin-bottom: 12px; display: flex; gap: 12px;">
                                <div style="color: {color}; font-weight: 700; font-size: 0.95rem; opacity: 0.85;">{num_str}</div>
                                <div>
                                    <div style="font-size: 0.95rem; color: #1e293b; font-weight: 500; margin-bottom: 6px; line-height: 1.4;">{act['text']}</div>
                                    <div style="margin-top: 6px;">
                                        {pillar_html}
                                    </div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
            else:
                st.info("No specific priority actions found for this selection.")
        else:
            st.info("Priority Action data source not available.")
            
    with col_voice:
        st.markdown("### Community Voices")
        quotes_path = "data/lcat/LCAT_Verbatim_Quote_Classification.xlsx"
        if os.path.exists(quotes_path):
            df_quotes = pd.read_excel(quotes_path)
            
            if state != "Unknown":
                df_quotes = df_quotes[df_quotes['State'] == state]
            if district != "All Districts":
                df_quotes = df_quotes[df_quotes['District'] == district]
                
            df_quotes = df_quotes[df_quotes['Primary LCAT Element'] == theme]
            
            display_quotes = pd.DataFrame()
            fallback_used = False
            
            if village != "All Villages":
                village_quotes = df_quotes[df_quotes['Village'] == village]
                if not village_quotes.empty:
                    display_quotes = village_quotes
                else:
                    display_quotes = df_quotes
                    fallback_used = True
            else:
                display_quotes = df_quotes
                
            if fallback_used and not display_quotes.empty:
                st.caption("Showing *District-level evidence* (No specific quotes for selected village)")
                
            if not display_quotes.empty:
                for _, row in display_quotes.iterrows():
                    quote = row.get("Verbatim Quote", "")
                    if pd.isna(quote) or not str(quote).strip():
                        continue
                        
                    speaker = row.get("Speaker / Attribution", "Community Member")
                    
                    st.markdown(f"""
                    <div style="background: #f8fafc; border-left: 4px solid #712416; padding: 16px; margin-bottom: 16px; border-radius: 0 6px 6px 0;">
                        <div style="font-size: 1.05rem; color: #0f172a; font-style: italic; margin-bottom: 12px;">"{quote}"</div>
                        <div style="font-size: 0.8rem; color: #475569;">
                            <span style="font-weight: 600; color: #1e293b;">{speaker}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No verbatim quotes available for this theme at the selected geography.")
        else:
            st.info("Community Voices dataset not found.")

# -----------------------------------------------------------------------------
# 3. SIDEBAR & GEOGRAPHIC SELECTION
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown('<div class="badge-burgundy">DASHBOARD CONTROLS</div>', unsafe_allow_html=True)
    
    dashboard_mode = st.radio("Dashboard Mode", ["LCAT & GPDP", "Climate Signals"])
    st.markdown("---")
    
    st.subheader("Geographic Filters")
    
    if dashboard_mode == "LCAT & GPDP":
        df_villages = load_data_from_folder()
        
        available_states = df_villages["state"].dropna().unique().tolist()
        if not available_states:
            available_states = ["Unknown"]
            
        selected_state = st.selectbox("State", available_states, key="lcat_state")
        
        dist_options = ["All Districts"] + df_villages[df_villages["state"] == selected_state]["district"].dropna().unique().tolist()
            
        selected_district = st.selectbox("District", dist_options, key="lcat_dist")
        
        if selected_district != "All Districts":
            vill_options = ["All Villages"] + df_villages[(df_villages["state"] == selected_state) & (df_villages["district"] == selected_district)]["name"].dropna().unique().tolist()
        else:
            vill_options = ["All Villages"] + df_villages[df_villages["state"] == selected_state]["name"].dropna().unique().tolist()
            
        selected_village = st.selectbox("Gram Panchayat / Village", vill_options, key="lcat_vill")
        
        metric_choice = st.selectbox(
            "Map Metric",
            ["Total GPDP Demand", "Highest Demand Concentration", "Implementation Tiers"]
        )
        
        basemap_choice = st.selectbox(
            "Basemap Style",
            ["CartoDB Positron (Light)", "CartoDB Dark", "OpenStreetMap"]
        )
        
        st.markdown("---")
        
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
        
        st.subheader("Population Layer")
        pop_layer_enabled = st.toggle("Enable Population Density (1km)", value=False, help="Display actual values from 2020 Population Density COG.")
        pop_opacity = 0.5
        if pop_layer_enabled:
            pop_opacity = st.slider("Population Layer Opacity", min_value=0.1, max_value=1.0, value=0.5, step=0.05)
            
    elif dashboard_mode == "Climate Signals":
        climate_df = load_climate_data()
        
        avail_clim_states = climate_df["state"].dropna().unique().tolist() if not climate_df.empty else ["Unknown"]
        selected_clim_state = st.selectbox("State", avail_clim_states, key="clim_state")
        
        if not climate_df.empty:
            clim_dist_opts = ["All Districts"] + climate_df[climate_df["state"] == selected_clim_state]["district"].dropna().unique().tolist()
        else:
            clim_dist_opts = ["All Districts"]
            
        selected_clim_dist = st.selectbox("District", clim_dist_opts, key="clim_dist")

if dashboard_mode == "LCAT & GPDP":
    if selected_district != "All Districts":
        filtered_df = df_villages[(df_villages["district"] == selected_district) & (df_villages["state"] == selected_state)]
    else:
        filtered_df = df_villages[df_villages["state"] == selected_state]

    if selected_village != "All Villages":
        filtered_df = filtered_df[filtered_df["name"] == selected_village]

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
            <div class="metric-label">TIER 1 — COMMUNITY LED</div>
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
        
        if selected_district in DISTRICT_CENTERS:
            center_lat = DISTRICT_CENTERS[selected_district]["lat"]
            center_lng = DISTRICT_CENTERS[selected_district]["lng"]
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
        
        m = folium.Map(
            location=[center_lat, center_lng],
            zoom_start=zoom_start,
            tiles=tile_dict[basemap_choice],
            control_scale=True
        )
        
        if pop_layer_enabled:
            pop_raster_path = "data/population/ind_pd_2020_1km_COG.tif"
            if os.path.exists(pop_raster_path):
                pop_bounds = None
                if selected_district in DISTRICT_CENTERS:
                    pop_bounds = DISTRICT_CENTERS[selected_district]["bounds"]
                elif not filtered_df.empty:
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
                        zindex=200 
                    ).add_to(m)
            else:
                st.warning(f"Population raster file not found at: {pop_raster_path}")
                
        if imagery_enabled:
            target_dist = selected_district if selected_district != "All Districts" else "Bastar"
            if target_dist in DISTRICT_CENTERS:
                bounds = DISTRICT_CENTERS[target_dist]["bounds"]
                
                if custom_image_file is not None:
                    img_bytes = custom_image_file.read()
                    encoded_png = "data:image/png;base64," + base64.b64encode(img_bytes).decode()
                    image_source = encoded_png
                else:
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
                popup=f"{v['name']} Village ({v['district']})"
            ).add_to(m)

        st_folium(m, width="100%", height=560)

    # -----------------------------------------------------------------------------
    # 7. ANALYTICS & LCAT CHARTS (PLOTLY)
    # -----------------------------------------------------------------------------
    with analytics_col:
        st.markdown("### LCAT Elements & Risk Breakdown")
        st.markdown("<p style='font-size: 0.85rem; color: #64748b; margin-top: -10px; margin-bottom: 20px;'>Click a theme ring to view priority actions and community voices</p>", unsafe_allow_html=True)
        
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
            if selected_state != "Unknown" and 'State' in raw_df.columns:
                raw_df = raw_df[raw_df['State'] == selected_state]
            if selected_district != "All Districts" and 'District' in raw_df.columns:
                raw_df = raw_df[raw_df['District'] == selected_district]
            if selected_village != "All Villages" and 'Panchayat/Village' in raw_df.columns:
                raw_df = raw_df[raw_df['Panchayat/Village'] == selected_village]
                
            if 'Theme' in raw_df.columns:
                raw_df['Clean_Theme'] = raw_df['Theme'].astype(str).apply(lambda x: x.split(')')[-1].strip() if ')' in x else x)
            else:
                raw_df['Clean_Theme'] = 'Unknown'
                
            if 'Tier' in raw_df.columns:
                raw_df['Clean_Tier'] = raw_df['Tier'].astype(str).apply(
                    lambda x: 'Tier 1 — Community Led' if 'Tier 1' in x else (
                        'Tier 2 — Minor Support' if 'Tier 2' in x else (
                        'Tier 3 — External Support & Convergence' if 'Tier 3' in x else 'Unknown'
                    ))
                )
            else:
                raw_df['Clean_Tier'] = 'Unknown'
                
            pillar_col = 'Pillars' if 'Pillars' in raw_df.columns else ('Pillar' if 'Pillar' in raw_df.columns else None)
            if pillar_col:
                raw_df['Clean_Pillar'] = raw_df[pillar_col].astype(str).fillna('Unknown')
            else:
                raw_df['Clean_Pillar'] = 'Unknown'
                
            tier_colors = {
                "Tier 1 — Community Led": "#d97706",
                "Tier 2 — Minor Support": "#712416",
                "Tier 3 — External Support & Convergence": "#0ea5e9"
            }

            # -------------------------------------------------------------
            # Visualization 1: Tiers across Themes (Radial Grid)
            # -------------------------------------------------------------
            theme_tier_df = raw_df[raw_df['Clean_Tier'] != 'Unknown'].groupby(['Clean_Theme', 'Clean_Tier']).size().reset_index(name='Count')
            
            if not theme_tier_df.empty:
                theme_pivot = theme_tier_df.pivot(index='Clean_Theme', columns='Clean_Tier', values='Count').fillna(0)
                theme_pivot['Total'] = theme_pivot.sum(axis=1)
                plot_df_theme = theme_pivot.drop(columns=['Total']).reset_index().melt(id_vars='Clean_Theme', var_name='Tier', value_name='Count')
            else:
                theme_pivot = pd.DataFrame(columns=['Total'])
                plot_df_theme = pd.DataFrame(columns=['Clean_Theme', 'Tier', 'Count'])
                
            themes_list = LCAT_ELEMENTS
            n_themes = len(themes_list)
            
            cols = 4
            rows = 2
            
            fig_theme = make_subplots(
                rows=rows, cols=cols,
                specs=[[{'type': 'domain'}] * cols] * rows,
                subplot_titles=themes_list,
                vertical_spacing=0.15
            )
            
            for i, theme in enumerate(themes_list):
                r = i // cols + 1
                c = i % cols + 1
                
                if theme in theme_pivot.index:
                    theme_data = plot_df_theme[plot_df_theme['Clean_Theme'] == theme]
                    theme_data = theme_data[theme_data['Count'] > 0] 
                    
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
                else:
                    fig_theme.add_trace(go.Pie(
                        labels=['No Data'],
                        values=[1],
                        hole=0.68,
                        title={'text': "<b>0</b>", 'font': {'size': 15, 'color': '#94a3b8'}},
                        marker=dict(colors=['#f1f5f9'], line=dict(color='#ffffff', width=1.5)),
                        textinfo='none',
                        hoverinfo='none',
                        name=theme,
                        sort=False
                    ), row=r, col=c)
                    
            fig_theme.update_layout(
                title_text="Tiers across Themes",
                title_font=dict(size=14, color="#1e293b", family="sans-serif"),
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#1e293b", size=11),
                    margin=dict(l=10, r=10, t=50, b=90),
                    height=450,
                    showlegend=True,
                    legend=dict(orientation="h", yanchor="top", y=-0.15, xanchor="center", x=0.5, font=dict(color="#475569"), title="")
                )
                
            for annotation in fig_theme['layout']['annotations']:
                    annotation['yanchor'] = 'top'
                    annotation['y'] -= 0.48
                    annotation['align'] = 'center'
                    annotation['text'] = "<br>".join(textwrap.wrap(annotation['text'], width=22))
                    annotation['font'] = dict(size=11, color="#475569")
                    
                if HAS_PLOTLY_EVENTS:
                        clicked = plotly_events(
                        fig_theme,
                        click_event=True,
                        hover_event=False,
                        select_event=False,
                        key="theme_chart_events",
                        override_height=450,
                        override_width="100%"
                    )
                    if clicked and len(clicked) > 0:
                        curve_idx = clicked[0].get("curveNumber", -1)
                        if 0 <= curve_idx < len(themes_list):
                            selected_theme = themes_list[curve_idx]
                            show_theme_overlay(selected_theme, selected_state, selected_district, selected_village)
                else:
                    st.warning("Please install `streamlit-plotly-events` to enable clickable rings.")
                    st.plotly_chart(fig_theme, use_container_width=True, config={'displayModeBar': False})

            # -------------------------------------------------------------
            # Visualization 2: Tiers across 3 Pillars (Radial Grid)
            # -------------------------------------------------------------
            if pillar_col:
                pillar_tier_df = raw_df[(raw_df['Clean_Tier'] != 'Unknown') & (raw_df['Clean_Pillar'] != 'Unknown') & (raw_df['Clean_Pillar'] != 'nan')].groupby(['Clean_Pillar', 'Clean_Tier']).size().reset_index(name='Count')
                
                if not pillar_tier_df.empty:
                    pillar_pivot = pillar_tier_df.pivot(index='Clean_Pillar', columns='Clean_Tier', values='Count').fillna(0)
                    pillar_pivot['Total'] = pillar_pivot.sum(axis=1)
                    plot_df_pillar = pillar_pivot.drop(columns=['Total']).reset_index().melt(id_vars='Clean_Pillar', var_name='Tier', value_name='Count')
                else:
                    pillar_pivot = pd.DataFrame(columns=['Total'])
                    plot_df_pillar = pd.DataFrame(columns=['Clean_Pillar', 'Tier', 'Count'])
                    
                pillars_list = ["Adaptation", "Mitigation", "Restoration"]
                n_pillars = 3
                
                fig_pillar = make_subplots(
                    rows=1, cols=3,
                    specs=[[{'type': 'domain'}] * 3],
                    subplot_titles=pillars_list
                )
                
                for i, pillar in enumerate(pillars_list):
                    if pillar in pillar_pivot.index:
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
                    else:
                        fig_pillar.add_trace(go.Pie(
                            labels=['No Data'],
                            values=[1],
                            hole=0.68,
                            title={'text': "<b>0</b>", 'font': {'size': 18, 'color': '#94a3b8'}},
                            marker=dict(colors=['#f1f5f9'], line=dict(color='#ffffff', width=2)),
                            textinfo='none',
                            hoverinfo='none',
                            name=pillar,
                            sort=False
                        ), row=1, col=i+1)
                        
                fig_pillar.update_layout(
                    title_text="Tiers across Pillars",
                    title_font=dict(size=14, color="#1e293b", family="sans-serif"),
                        plot_bgcolor="rgba(0,0,0,0)",
                        paper_bgcolor="rgba(0,0,0,0)",
                        font=dict(color="#1e293b", size=11),
                        margin=dict(l=10, r=10, t=50, b=90),
                        height=280,
                        showlegend=True,
                        legend=dict(orientation="h", yanchor="top", y=-0.3, xanchor="center", x=0.5, font=dict(color="#475569"), title="")
                    )
                    
                    for annotation in fig_pillar['layout']['annotations']:
                        annotation['yanchor'] = 'top'
                        annotation['y'] -= 1.05
                        annotation['font'] = dict(size=12, color="#475569")
                        
                    st.plotly_chart(fig_pillar, use_container_width=True, config={'displayModeBar': False})
                else:
                    st.info("No mapped pillar data available for this selection.")
        else:
            st.info("No raw data available for the selected filters to generate tier breakdowns.")

    # -----------------------------------------------------------------------------
    # 8. LANDSCAPE TRAJECTORY
    # -----------------------------------------------------------------------------
    st.markdown("---")
    st.markdown("### District LCAT Landscape Trajectory")

    @st.cache_data
    def load_trajectory_data():
        file_path = "data/District Wise LCAT.xlsx"
        if os.path.exists(file_path):
            try:
                df = pd.read_excel(file_path)
                dist_col = next((c for c in df.columns if 'district' in str(c).lower()), None)
                if dist_col:
                    df = df.rename(columns={dist_col: "District"})
                return df
            except Exception:
                return pd.DataFrame()
        return pd.DataFrame()

    traj_df = load_trajectory_data()

    if not traj_df.empty and "District" in traj_df.columns:
        if selected_district != "All Districts":
            filtered_traj_df = traj_df[traj_df["District"] == selected_district]
        else:
            if selected_state != "Unknown":
                filtered_traj_df = traj_df[traj_df["District"].isin(dist_options)]
            else:
                filtered_traj_df = traj_df.copy()

        if filtered_traj_df.empty:
            st.info("No trajectory data available for the selected geographic filters.")
        else:
            traj_themes = [c for c in filtered_traj_df.columns if c not in ["District", "State"]]
            valid_themes = [t for t in traj_themes if t in LCAT_ELEMENTS]
            if not valid_themes:
                valid_themes = traj_themes 
                
            status_colors = {
                "Improving": "#16a34a",
                "Stable": "#3b82f6",
                "Mixed": "#eab308",
                "Declining": "#ef4444",
                "Unknown": "#cbd5e1"
            }

            st.markdown("##### Visual Summary")
            n_districts = len(filtered_traj_df)
            st.caption(f"Showing trajectory distribution across **{n_districts}** district(s).")
            
            num_rings = len(valid_themes)
            r_cols = 4
            r_rows = max(1, (num_rings + r_cols - 1) // r_cols)
            
            fig_health = make_subplots(
                rows=r_rows, cols=r_cols,
                specs=[[{'type': 'domain'}] * r_cols] * r_rows,
                subplot_titles=valid_themes,
                vertical_spacing=0.25
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
            
            fig_health.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#1e293b", size=11),
                margin=dict(l=10, r=10, t=40, b=60),
                height=200 * r_rows,
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=-0.15 / max(1, r_rows), xanchor="center", x=0.5, font=dict(color="#475569"))
            )
            
            for annotation in fig_health['layout']['annotations']:
                annotation['y'] -= (1.0 / max(1, r_rows)) * 1.15
                annotation['font'] = dict(size=11, color="#475569")
                
            st.plotly_chart(fig_health, use_container_width=True, config={'displayModeBar': False})
            
            st.markdown("##### District × Theme Trajectory Matrix")
            
            matrix_df = filtered_traj_df.set_index("District")[valid_themes]
            status_to_num = {"Declining": 0, "Mixed": 1, "Stable": 2, "Improving": 3}
            
            z_data = matrix_df.copy()
            for col in z_data.columns:
                z_data[col] = z_data[col].apply(lambda x: status_to_num.get(str(x).strip(), -1))
                
            text_matrix = matrix_df.fillna("Unknown").values
            
            heatmap_colors = [
                [0.0, "#cbd5e1"], [0.2, "#cbd5e1"],       
                [0.2, "#ef4444"], [0.4, "#ef4444"],       
                [0.4, "#eab308"], [0.6, "#eab308"],       
                [0.6, "#3b82f6"], [0.8, "#3b82f6"],       
                [0.8, "#16a34a"], [1.0, "#16a34a"]        
            ]
            
            fig_matrix = go.Figure(data=go.Heatmap(
                z=z_data.values,
                x=valid_themes,
                y=matrix_df.index,
                text=text_matrix,
                hovertemplate="<b>District:</b> %{y}<br><b>Theme:</b> %{x}<br><b>Status:</b> %{text}<extra></extra>",
                colorscale=heatmap_colors,
                zmin=-1,
                zmax=3,
                showscale=False,
                xgap=3,
                ygap=3
            ))
            
            wrapped_themes = ["<br>".join(textwrap.wrap(t, width=16)) for t in valid_themes]
            
            fig_matrix.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#1e293b", size=11),
                margin=dict(l=10, r=10, t=10, b=60),
                height=max(200, len(matrix_df) * 35 + 120),
                xaxis=dict(
                    tickangle=0, 
                    tickvals=valid_themes,
                    ticktext=wrapped_themes,
                    tickfont=dict(color="#475569")
                ),
                yaxis=dict(tickfont=dict(color="#1e293b", weight="bold"))
            )
            
            st.plotly_chart(fig_matrix, use_container_width=True, config={'displayModeBar': False})
    else:
        st.info("Please add 'District Wise LCAT.xlsx' to the data folder to view the Landscape Trajectory.")

# -----------------------------------------------------------------------------
# CLIMATE SIGNALS DASHBOARD MODE
# -----------------------------------------------------------------------------
elif dashboard_mode == "Climate Signals":
    
    st.markdown(f"""
    <div class="header-banner">
        <div>
            <h1 class="header-title">Climate Signals Dashboard</h1>
            <p class="header-subtitle">Vulnerability & Thermal Stress &nbsp;·&nbsp; {selected_clim_state} › {selected_clim_dist}</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    df_climate = load_climate_data()
    df_state = df_climate[df_climate["state"] == selected_clim_state] if not df_climate.empty else df_climate
    
    ndmi_colors = {
        "Severe Canopy Desiccation": "#7f1d1d",
        "Moisture Loss": "#ea580c",
        "Stable": "#cbd5e1",
        "Moisture Gain": "#0284c7",
        "Little or No Change": "#cbd5e1"
    }
    lst_colors = {
        "Severe Warming": "#7f1d1d",
        "Moderate Warming": "#ea580c",
        "Stable": "#cbd5e1",
        "Cooling Trend": "#0284c7",
        "Little or No Change": "#cbd5e1"
    }

    if selected_clim_dist == "All Districts":
        st.markdown("### Climate Signals Overview")
        if not df_state.empty:
            col_ndmi, col_lst = st.columns(2)
            
            with col_ndmi:
                st.markdown("##### NDMI Status Distribution")
                ndmi_counts = df_state['canopy_moisture_status'].value_counts().reset_index()
                ndmi_counts.columns = ['Status', 'Districts']
                fig_ndmi = px.pie(ndmi_counts, names='Status', values='Districts', hole=0.6,
                                  color='Status', color_discrete_map=ndmi_colors)
                fig_ndmi.update_layout(margin=dict(t=20, b=20, l=10, r=10), showlegend=True, 
                                       legend=dict(orientation="h", y=-0.2), height=350)
                st.plotly_chart(fig_ndmi, use_container_width=True, config={'displayModeBar': False})
                
            with col_lst:
                st.markdown("##### LST Status Distribution")
                lst_counts = df_state['summer_lst_status'].value_counts().reset_index()
                lst_counts.columns = ['Status', 'Districts']
                fig_lst = px.pie(lst_counts, names='Status', values='Districts', hole=0.6,
                                 color='Status', color_discrete_map=lst_colors)
                fig_lst.update_layout(margin=dict(t=20, b=20, l=10, r=10), showlegend=True, 
                                      legend=dict(orientation="h", y=-0.2), height=350)
                st.plotly_chart(fig_lst, use_container_width=True, config={'displayModeBar': False})
        else:
            st.info("No climate data available for this state.")
            
    else:
        dist_row = df_state[df_state["district"] == selected_clim_dist]
        
        if not dist_row.empty:
            row = dist_row.iloc[0]
            
            k1, k2, k3, k4 = st.columns(4)
            with k1:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">NDMI CHANGE</div>
                    <div class="metric-value">{row.get('canopy_moisture_pct_change', 'N/A')}</div>
                    <div class="metric-desc">Percentage Change</div>
                </div>
                """, unsafe_allow_html=True)
            with k2:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">NDMI STATUS</div>
                    <div class="metric-value" style="font-size:1.3rem;">{row.get('canopy_moisture_status', 'N/A')}</div>
                    <div class="metric-desc">Canopy Moisture</div>
                </div>
                """, unsafe_allow_html=True)
            with k3:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">LST CHANGE</div>
                    <div class="metric-value">{row.get('summer_lst_change_c', 'N/A')} °C</div>
                    <div class="metric-desc">Temperature Change</div>
                </div>
                """, unsafe_allow_html=True)
            with k4:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">LST STATUS</div>
                    <div class="metric-value" style="font-size:1.3rem;">{row.get('summer_lst_status', 'N/A')}</div>
                    <div class="metric-desc">Thermal Stress</div>
                </div>
                """, unsafe_allow_html=True)
                
            st.markdown("<br>", unsafe_allow_html=True)
            
            dist_clean = str(selected_clim_dist).lower().replace(' ', '_')
            
            st.markdown("### Canopy Moisture — NDMI")
            i1, i2, i3 = st.columns(3)
            
            with i1:
                st.markdown("**2001–2010 Baseline**")
                path_b = f"data/climate_vulnerability/imagery/{dist_clean}_ndmi_baseline.png"
                if os.path.exists(path_b): st.image(path_b, use_container_width=True)
                else: st.info(f"Image not found: {os.path.basename(path_b)}")
            with i2:
                st.markdown("**2015–2024 Recent**")
                path_r = f"data/climate_vulnerability/imagery/{dist_clean}_ndmi_recent.png"
                if os.path.exists(path_r): st.image(path_r, use_container_width=True)
                else: st.info(f"Image not found: {os.path.basename(path_r)}")
            with i3:
                st.markdown("**Change**")
                path_c = f"data/climate_vulnerability/imagery/{dist_clean}_ndmi_change.png"
                if os.path.exists(path_c): st.image(path_c, use_container_width=True)
                else: st.info(f"Image not found: {os.path.basename(path_c)}")
                
            st.markdown("""
            <div style='text-align: center; font-size: 0.9rem; padding: 10px; color: #475569;'>
                🔴 <b>Red</b> → Moisture Loss / Drying &nbsp;&nbsp;&nbsp; ⚪ <b>White</b> → Little or No Change &nbsp;&nbsp;&nbsp; 🔵 <b>Blue</b> → Moisture Gain
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <div style='background-color: #ffffff; padding: 16px; border-radius: 8px; border: 1px solid #e2e8f0; margin-top: 10px; font-size: 0.9rem; color: #1e293b;'>
                <b>Baseline:</b> {row.get('canopy_moisture_baseline', 'N/A')} &nbsp;|&nbsp; 
                <b>Recent:</b> {row.get('canopy_moisture_recent', 'N/A')} &nbsp;|&nbsp; 
                <b>Absolute Change:</b> {row.get('canopy_moisture_change', 'N/A')} &nbsp;|&nbsp; 
                <b>Status:</b> {row.get('canopy_moisture_status', 'N/A')}
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("<hr style='margin: 32px 0; border-color: #e2e8f0;'>", unsafe_allow_html=True)
            
            st.markdown("### Thermal Stress — LST")
            l1, l2, l3 = st.columns(3)
            
            with l1:
                st.markdown("**2001–2010 Baseline**")
                path_lb = f"data/climate_vulnerability/imagery/{dist_clean}_lst_baseline.png"
                if os.path.exists(path_lb): st.image(path_lb, use_container_width=True)
                else: st.info(f"Image not found: {os.path.basename(path_lb)}")
            with l2:
                st.markdown("**2015–2024 Recent**")
                path_lr = f"data/climate_vulnerability/imagery/{dist_clean}_lst_recent.png"
                if os.path.exists(path_lr): st.image(path_lr, use_container_width=True)
                else: st.info(f"Image not found: {os.path.basename(path_lr)}")
            with l3:
                st.markdown("**Change**")
                path_lc = f"data/climate_vulnerability/imagery/{dist_clean}_lst_change.png"
                if os.path.exists(path_lc): st.image(path_lc, use_container_width=True)
                else: st.info(f"Image not found: {os.path.basename(path_lc)}")
                
            st.markdown("""
            <div style='text-align: center; font-size: 0.9rem; padding: 10px; color: #475569;'>
                🔵 <b>Blue</b> → Cooling &nbsp;&nbsp;&nbsp; ⚪ <b>White</b> → Little or No Change &nbsp;&nbsp;&nbsp; 🔴 <b>Red</b> → Warming
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <div style='background-color: #ffffff; padding: 16px; border-radius: 8px; border: 1px solid #e2e8f0; margin-top: 10px; font-size: 0.9rem; color: #1e293b;'>
                <b>Baseline:</b> {row.get('summer_lst_baseline_c', 'N/A')} °C &nbsp;|&nbsp; 
                <b>Recent:</b> {row.get('summer_lst_recent_c', 'N/A')} °C &nbsp;|&nbsp; 
                <b>Change:</b> {row.get('summer_lst_change_c', 'N/A')} °C &nbsp;|&nbsp; 
                <b>Status:</b> {row.get('summer_lst_status', 'N/A')}
                <br><br>
                <span style='color: #64748b; font-weight: 600;'>Extreme Heat Days:</span> &nbsp;
                <b>Baseline:</b> {row.get('extreme_heat_days_baseline', 'N/A')} &nbsp;|&nbsp; 
                <b>Recent:</b> {row.get('extreme_heat_days_recent', 'N/A')} &nbsp;|&nbsp; 
                <b>Change:</b> {row.get('extreme_heat_days_change', 'N/A')}
            </div>
            """, unsafe_allow_html=True)
            
        else:
            st.warning("Data not found for the selected district.")

    st.markdown("<br><br>", unsafe_allow_html=True)
    with st.expander("Methodology & Data Sources"):
        st.markdown("""
        **Canopy Moisture (NDMI)**
        * Source: MODIS MOD09A1
        * Resolution: 500 m
        * Season: October–November
        * Baseline: 2001–2010
        * Recent: 2015–2024
        
        **Thermal Stress (LST)**
        * Source: MODIS MOD11A1
        * Resolution: 1 km
        * Season: May–June
        * Baseline: 2001–2010
        * Recent: 2015–2024
        """)
