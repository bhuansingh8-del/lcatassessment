import streamlit as st
import folium
from streamlit_folium import st_folium
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import os
import glob
import re
from typing import Any
from plotly.subplots import make_subplots
import textwrap

# Try to load streamlit-plotly-events for native click interaction
try:
    from streamlit_plotly_events import plotly_events
    HAS_PLOTLY_EVENTS = True
except ImportError:
    HAS_PLOTLY_EVENTS = False

# -----------------------------------------------------------------------------
# 1. PAGE CONFIGURATION & CUSTOM CSS 
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="LCAT — Landscape Character Assessment Tool",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500;600&display=swap');
    
    :root {
        --paper: #EAE6D9;
        --paper-deep: #DFDACB;
        --ink: #20281F;
        --ink-soft: #4C5646;
        --line: #C9C2AC;
        --pine: #243D2C;
        --pine-2: #345040;
        --moss: #6C7C55;
        --ochre: #B9863E;
        --brick: #8C4536;
        --sage: #7E9767;
        --deepsage: #3E6B47;
        --slate: #3E6B78;
        --card: #F4F1E7;
        --white: #FCFBF6;
    }
    
    /* Global Theme */
    .stApp {
        background-color: var(--paper);
        color: var(--ink);
        font-family: 'IBM Plex Sans', sans-serif;
    }
    
    /* Hide Default Header */
    header[data-testid="stHeader"] {
        display: none;
    }
    
    /* Typography Overrides */
    h1, h2, h3, h4, h5, h6, .display {
        font-family: 'Space Grotesk', sans-serif !important;
        color: var(--ink);
    }
    .mono {
        font-family: 'IBM Plex Mono', monospace !important;
    }
    
    /* Streamlit Widget Overrides */
    [data-testid="stMarkdownContainer"] p, 
    .stSelectbox label, .stToggle label, .stRadio label {
        color: var(--ink) !important;
        font-family: 'IBM Plex Sans', sans-serif;
    }
    
    /* Selectboxes / Inputs */
    div[data-baseweb="select"] > div, input {
        background-color: var(--white) !important;
        color: var(--ink) !important;
        border: 1px solid var(--line) !important;
        border-radius: 6px;
    }
    ul[data-baseweb="menu"] {
        background-color: var(--white) !important;
        border: 1px solid var(--line);
    }
    li[data-baseweb="option"] {
        color: var(--ink) !important;
    }
    li[data-baseweb="option"]:hover {
        background-color: var(--paper-deep) !important;
    }
    
    /* Top Header Bar */
    .lcat-header {
        background: var(--pine);
        color: var(--white);
        padding: 14px 24px;
        display: flex;
        align-items: center;
        gap: 20px;
        border-bottom: 3px solid var(--ochre);
        margin-top: -60px; 
        margin-bottom: 0px;
        margin-left: -5rem;
        margin-right: -5rem;
    }
    .brandmark { width: 34px; height: 34px; flex: none; }
    .brand { display: flex; flex-direction: column; line-height: 1.1; margin-right: 12px; }
    .brand b { font-family: 'Space Grotesk', sans-serif; font-size: 19px; letter-spacing: 0.5px; }
    .brand span { font-size: 11px; color: #C9D3C2; letter-spacing: 0.4px; }
    
    /* Breadcrumb */
    .breadcrumb {
        background: var(--pine-2); color: #DCE4D4; font-size: 12.5px; padding: 8px 24px;
        font-family: 'IBM Plex Mono', monospace; display: flex; align-items: center; gap: 6px;
        margin-left: -5rem; margin-right: -5rem; margin-bottom: 24px;
    }
    .breadcrumb .sep { opacity: 0.5; }
    .breadcrumb .current { color: var(--ochre); font-weight: 600; }

    /* Left Panel Styles */
    .section-label {
        font-family: 'IBM Plex Mono', monospace; font-size: 10.5px; letter-spacing: 1.2px; text-transform: uppercase;
        color: var(--ink-soft); margin: 18px 0 10px;
    }
    .layer-toggle {
        display: flex; align-items: center; justify-content: space-between; padding: 7px 2px; font-size: 13.5px; color: var(--ink);
    }

    /* Center & Right Cards */
    .html-card {
        background: var(--card); border: 1px solid var(--line); border-radius: 10px; padding: 16px;
    }
    
    /* Block Summary */
    .block-summary { margin-top: 16px; background: var(--card); border: 1px solid var(--line); border-radius: 10px; padding: 16px 18px; }
    .block-summary h3 { font-family: 'Space Grotesk', sans-serif; font-size: 13.5px; margin: 0 0 12px; display: flex; justify-content: space-between; color: var(--ink); }
    .block-summary h3 .n { color: var(--ink-soft); font-family: 'IBM Plex Mono', monospace; font-weight: 400; font-size: 11.5px; }
    .dist-bar { display: flex; height: 20px; border-radius: 5px; overflow: hidden; margin-bottom: 8px; }
    .dist-bar div { height: 100%; }
    .tier-counts { display: flex; gap: 22px; margin-top: 14px;}
    .tier-counts div { display: flex; flex-direction: column; }
    .tier-counts b { font-family: 'IBM Plex Mono', monospace; font-size: 18px; color: var(--pine); }
    .tier-counts span { font-size: 10.5px; color: var(--ink-soft); }

    /* Profile Panel */
    .profile-header h2 { font-family: 'Space Grotesk', sans-serif; font-size: 19px; margin: 0 0 2px; }
    .profile-header .loc { font-size: 12px; color: var(--ink-soft); font-family: 'IBM Plex Sans'; margin-bottom: 14px;}
    
    .score-block {
        display: flex; align-items: center; gap: 16px; background: var(--card); border: 1px solid var(--line);
        border-radius: 10px; padding: 14px 16px; margin-bottom: 14px;
    }
    .score-block .txt b { display: block; font-family: 'Space Grotesk', sans-serif; font-size: 14px; }
    .score-block .txt .cls {
        display: inline-block; margin-top: 4px; font-size: 11px; font-family: 'IBM Plex Mono', monospace;
        padding: 2px 8px; border-radius: 10px; background: var(--line); color: var(--ink); font-weight: 600;
    }
    
    .stat-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px 14px; margin-top: 12px; }
    .stat-grid div { display: flex; flex-direction: column; }
    .stat-grid b { font-family: 'IBM Plex Mono', monospace; font-size: 14px; color: var(--ink); }
    .stat-grid span { font-size: 10.5px; color: var(--ink-soft); }

    /* Action items */
    .action-item {
        border-left: 3px solid var(--ochre); background: var(--card); border-radius: 0 8px 8px 0;
        padding: 10px 12px; margin-bottom: 8px; border-top: 1px solid var(--line); border-right: 1px solid var(--line); border-bottom: 1px solid var(--line);
    }
    .action-item .atxt { font-size: 13px; margin-bottom: 6px; line-height: 1.35; color: var(--ink); }
    .tag-row { display: flex; gap: 5px; flex-wrap: wrap; }
    .tag {
        font-size: 9.5px; font-family: 'IBM Plex Mono', monospace; padding: 2px 7px; border-radius: 9px;
        background: var(--paper-deep); color: var(--ink-soft);
    }
    
    .focus-pills { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 6px; }
    .focus-pills span {
        font-size: 11px; padding: 5px 10px; border-radius: 14px; background: var(--line); color: var(--ink);
        font-family: 'IBM Plex Mono', monospace;
    }
    
    .stButton>button {
        background-color: var(--paper-deep); color: var(--ink); border: 1px solid var(--line);
        font-family: 'IBM Plex Mono', monospace; font-size: 12px; width: 100%; border-radius: 6px;
    }
    .stButton>button:hover { background-color: var(--line); color: var(--ink); border-color: var(--pine); }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. CONSTANTS & SEED MAPPINGS
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

def normalize_theme(x: Any) -> str:
    if pd.isna(x): return "Unknown"
    v = str(x).strip()
    v = re.sub(r'^[\d]+\s*[\)\.]?\s*', '', v).strip()
    v_lower = v.lower()
    for valid in LCAT_ELEMENTS:
        if valid.lower() in v_lower:
            return valid
    return "Unknown"

ELEMENT_COLORS = {
    "Landform and topography": "#D89A2B", "Hydrology": "#0284c7", 
    "Land cover and Agriculture": "#16a34a", "Cultural and historical features": "#db2777",
    "Visual and Sensory qualities": "#7c3aed", "Wildlife and Biodiversity richness": "#ea580c",
    "Infrastructure and Economic factors": "#64748b", "Community and Governance": "#ca8a04",
    "Unknown": "#cbd5e1"
}

tier_colors = {
    "Tier 1 — Community Led": "#d97706",
    "Tier 2 — Minor Support": "#712416",
    "Tier 3 — External Support & Convergence": "#0ea5e9"
}

DISTRICT_CENTERS = {
    "Bastar": {"lat": 19.35, "lng": 81.80}, "Kanker": {"lat": 20.27, "lng": 81.49},
    "Dhamtari": {"lat": 20.70, "lng": 81.55}, "Kondagaon": {"lat": 19.60, "lng": 81.66},
    "Aligarh": {"lat": 27.89, "lng": 78.08}, "Banda": {"lat": 25.48, "lng": 80.33},
    "Jhabua": {"lat": 22.76, "lng": 74.59}, "Sehore": {"lat": 23.20, "lng": 77.08},
    "Prayagraj": {"lat": 25.43, "lng": 81.84}, "Dhar": {"lat": 22.59, "lng": 75.30}
}

# -----------------------------------------------------------------------------
# 3. DATA LOADING (Real files only)
# -----------------------------------------------------------------------------
@st.cache_data
def get_raw_gpdp_data() -> pd.DataFrame:
    """Loads all GPDP data in raw format, parsing all sheets strictly from files."""
    data_dir = "data"
    df_list = []
    
    if os.path.exists(data_dir):
        all_files = glob.glob(os.path.join(data_dir, "*.xlsx")) + glob.glob(os.path.join(data_dir, "*.csv"))
        gpdp_files = [f for f in all_files if "GPDP" in os.path.basename(f).upper() or "GPDP" in os.path.basename(f)]
        
        for f in gpdp_files:
            try:
                if f.endswith('.csv'):
                    df_list.append(pd.read_csv(f))
                else:
                    dfs = pd.read_excel(f, sheet_name=None)
                    df_list.extend(dfs.values())
            except Exception:
                pass
                
    if df_list:
        raw_df = pd.concat(df_list, ignore_index=True)
        # Normalize core dimensions
        raw_df['Clean_Theme'] = raw_df.get('Theme', pd.Series(dtype=str)).apply(normalize_theme)
        
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
        raw_df['Clean_Pillar'] = raw_df[pillar_col].astype(str).fillna('Unknown') if pillar_col else 'Unknown'
        
        # Ensure geographic columns exist
        for col in ['State', 'District', 'Block', 'Panchayat/Village']:
            if col not in raw_df.columns:
                raw_df[col] = "Unknown"
        return raw_df
        
    return pd.DataFrame()

@st.cache_data
def load_climate_data() -> pd.DataFrame:
    path = "data/climate_vulnerability/climate_vulnerability_results.csv"
    if os.path.exists(path):
        try:
            df = pd.read_csv(path)
            df.columns = df.columns.str.strip().str.lower()
            return df
        except Exception:
            pass
    return pd.DataFrame()

# -----------------------------------------------------------------------------
# 4. MODALS & OVERLAYS
# -----------------------------------------------------------------------------
@st.dialog("Theme Insights", width="large")
def show_theme_overlay(theme: str, state: str, district: str, village: str, raw_df: pd.DataFrame):
    st.markdown(f"<h2 style='color: var(--pine); margin-top: 0; margin-bottom: 20px; font-family: Space Grotesk;'>{theme}</h2>", unsafe_allow_html=True)
    
    col_act, col_voice = st.columns([1.2, 1.0])
    
    with col_act:
        st.markdown("<div class='section-label' style='margin-top:0;'>Priority Actions</div>", unsafe_allow_html=True)
        if not raw_df.empty:
            df_gpdp = raw_df[raw_df['State'] == state] if state != "Unknown" else raw_df
            if district != "All Districts": df_gpdp = df_gpdp[df_gpdp['District'] == district]
            if village != "All Villages": df_gpdp = df_gpdp[df_gpdp['Panchayat/Village'] == village]
            df_gpdp = df_gpdp[df_gpdp['Clean_Theme'] == theme]
            
            if not df_gpdp.empty:
                st.markdown(f"<div style='font-size: 0.95rem; color: var(--ink-soft); margin-bottom: 20px; font-family: IBM Plex Mono;'><b>{len(df_gpdp)}</b> actions</div>", unsafe_allow_html=True)
                
                tier_groups = {
                    "Tier 1 — Community Led": {"color": "#d97706", "actions": []},
                    "Tier 2 — Minor Support": {"color": "#712416", "actions": []},
                    "Tier 3 — External Support & Convergence": {"color": "#0ea5e9", "actions": []},
                }
                
                for _, row in df_gpdp.iterrows():
                    tier = row['Clean_Tier']
                    if tier in tier_groups:
                        tier_groups[tier]["actions"].append({"text": row.get("Priority Action", "N/A"), "pillars": row['Clean_Pillar']})
                
                for group_name, group_data in tier_groups.items():
                    actions = group_data["actions"]
                    color = group_data["color"]
                    if actions:
                        st.markdown(f"""
                        <div style="margin-top: 16px; margin-bottom: 12px;">
                            <div style="font-size: 1rem; font-weight: 700; color: {color};">{group_name}</div>
                            <div style="font-size: 0.8rem; color: var(--ink-soft);">{len(actions)} actions</div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        for idx, act in enumerate(actions, 1):
                            pill_html = f'<span style="background: var(--paper-deep); padding: 2px 6px; border-radius: 4px; font-size: 0.75rem; color: var(--ink-soft);">{act["pillars"]}</span>' if act["pillars"] != "Unknown" else ''
                            st.markdown(f"""
                            <div style="background: var(--card); border: 1px solid var(--line); border-left: 4px solid {color}; border-radius: 6px; padding: 12px; margin-bottom: 12px; display: flex; gap: 12px;">
                                <div style="color: {color}; font-weight: 700; font-size: 0.95rem; font-family: IBM Plex Mono;">{idx:02d}</div>
                                <div>
                                    <div style="font-size: 0.95rem; color: var(--ink); font-weight: 500; margin-bottom: 6px; line-height: 1.4;">{act['text']}</div>
                                    <div style="margin-top: 6px;">{pill_html}</div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
            else:
                st.info("No specific priority actions found for this selection.")
        else:
            st.info("Priority Action data source not available.")
            
    with col_voice:
        st.markdown("<div class='section-label' style='margin-top:0;'>Community Voices</div>", unsafe_allow_html=True)
        quotes_path = "data/lcat/LCAT_Verbatim_Quote_Classification.xlsx"
        if os.path.exists(quotes_path):
            try:
                df_quotes = pd.read_excel(quotes_path)
                if state != "Unknown": df_quotes = df_quotes[df_quotes['State'] == state]
                if district != "All Districts": df_quotes = df_quotes[df_quotes['District'] == district]
                df_quotes = df_quotes[df_quotes['Primary LCAT Element'] == theme]
                
                display_quotes = pd.DataFrame()
                fallback_used = False
                
                if village != "All Villages":
                    village_quotes = df_quotes[df_quotes['Village'] == village]
                    if not village_quotes.empty: display_quotes = village_quotes
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
                        if pd.isna(quote) or not str(quote).strip(): continue
                        speaker = row.get("Speaker / Attribution", "Community Member")
                        st.markdown(f"""
                        <div style="background: var(--card); border-left: 4px solid var(--moss); padding: 16px; margin-bottom: 16px; border-radius: 0 6px 6px 0; border: 1px solid var(--line); border-left-width: 4px;">
                            <div style="font-size: 1.05rem; color: var(--ink); font-style: italic; margin-bottom: 12px;">"{quote}"</div>
                            <div style="font-size: 0.8rem; color: var(--ink-soft); font-family: 'IBM Plex Mono', monospace;">
                                <span style="font-weight: 600; color: var(--ink);">{speaker}</span>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("No verbatim quotes available for this theme at the selected geography.")
            except Exception:
                st.info("Error reading Community Voices file.")
        else:
            st.info("Community Voices dataset not found.")

# -----------------------------------------------------------------------------
# MAIN APP EXECUTION
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown('<div style="font-family: Space Grotesk; font-size: 14px; font-weight: bold; color: var(--pine); margin-bottom: 10px;">DASHBOARD MODE</div>', unsafe_allow_html=True)
    dashboard_mode = st.radio("Mode", ["LCAT & GPDP", "Climate Signals"], label_visibility="collapsed")

if dashboard_mode == "LCAT & GPDP":
    raw_gpdp_df = get_raw_gpdp_data()
    
    # -------------------------------------------------------------------------
    # LAYOUT & CONTROLS
    # -------------------------------------------------------------------------
    st.markdown("""
    <div class="lcat-header">
      <svg class="brandmark" viewBox="0 0 40 40" fill="none">
        <circle cx="20" cy="20" r="17" stroke="#B9863E" stroke-width="2"/>
        <circle cx="20" cy="20" r="11" stroke="#7E9767" stroke-width="2"/>
        <circle cx="20" cy="20" r="5" stroke="#FCFBF6" stroke-width="2"/>
      </svg>
      <div class="brand"><b>LCAT</b><span>LANDSCAPE CHARACTER ASSESSMENT TOOL</span></div>
    </div>
    """, unsafe_allow_html=True)

    col_left, col_center, col_right = st.columns([1.2, 2.5, 1.4], gap="large")

    with col_left:
        st.markdown('<div class="section-label">Geographic selection</div>', unsafe_allow_html=True)
        
        available_states = raw_gpdp_df["State"].dropna().unique().tolist() if not raw_gpdp_df.empty else ["No Data"]
        selected_state = st.selectbox("State", available_states)
        
        if not raw_gpdp_df.empty and selected_state != "No Data":
            state_df = raw_gpdp_df[raw_gpdp_df["State"] == selected_state]
            dist_options = ["All Districts"] + state_df["District"].dropna().unique().tolist()
        else:
            dist_options = ["All Districts"]
        selected_district = st.selectbox("District", dist_options)
        
        if selected_district != "All Districts" and not raw_gpdp_df.empty:
            dist_df = state_df[state_df["District"] == selected_district]
            block_options = ["All Blocks"] + dist_df["Block"].dropna().unique().tolist()
            vill_options = ["All Villages"] + dist_df["Panchayat/Village"].dropna().unique().tolist()
        else:
            block_options = ["All Blocks"]
            vill_options = ["All Villages"] + (state_df["Panchayat/Village"].dropna().unique().tolist() if not raw_gpdp_df.empty else [])
            
        selected_block = st.selectbox("Block", block_options)
        
        if selected_block != "All Blocks" and not raw_gpdp_df.empty:
            block_df = state_df[(state_df["District"] == selected_district) & (state_df["Block"] == selected_block)]
            vill_options = ["All Villages"] + block_df["Panchayat/Village"].dropna().unique().tolist()
            
        selected_village = st.selectbox("Gram Panchayat / Village", vill_options)
        
        st.markdown('<div class="section-label" style="margin-top: 30px;">Map layers</div>', unsafe_allow_html=True)
        st.checkbox("LULC", value=True, help="Placeholder for future spatial layer")
        st.checkbox("NDVI", value=True, help="Placeholder for future spatial layer")
        st.checkbox("Soil", value=False, help="Placeholder for future spatial layer")
        st.checkbox("DEM / Slope", value=False, help="Placeholder for future spatial layer")
        st.checkbox("Rivers", value=True, help="Placeholder for future spatial layer")
        st.checkbox("LCAT choropleth", value=True)
        
        st.markdown('<div class="section-label" style="margin-top: 30px;">Filter priority actions</div>', unsafe_allow_html=True)
        
        # Theme 'expandable' chip behavior simulated via selectbox state
        if 'show_all_themes' not in st.session_state:
            st.session_state.show_all_themes = False
            
        if not st.session_state.show_all_themes:
            theme_options = ["All", "Hydrology", "Land cover and Agriculture", "+ 6 more themes"]
        else:
            theme_options = ["All"] + LCAT_ELEMENTS
            
        selected_theme_raw = st.selectbox("Landscape Themes", theme_options)
        
        if selected_theme_raw == "+ 6 more themes":
            st.session_state.show_all_themes = True
            st.rerun()
            
        selected_theme = selected_theme_raw if selected_theme_raw != "+ 6 more themes" else "All"
        
        selected_tier = st.selectbox("Tier", ["All", "Tier 1 — Community Led", "Tier 2 — Minor Support", "Tier 3 — External Support & Convergence"])
        selected_pillar = st.selectbox("Pillar", ["All", "Restoration", "Adaptation", "Mitigation"])

    # -------------------------------------------------------------------------
    # DATA FILTERING (Applying the rules accurately to real data)
    # -------------------------------------------------------------------------
    filtered_df = raw_gpdp_df.copy()
    if not filtered_df.empty:
        if selected_state != "No Data": filtered_df = filtered_df[filtered_df['State'] == selected_state]
        if selected_district != "All Districts": filtered_df = filtered_df[filtered_df['District'] == selected_district]
        if selected_block != "All Blocks": filtered_df = filtered_df[filtered_df['Block'] == selected_block]
        if selected_village != "All Villages": filtered_df = filtered_df[filtered_df['Panchayat/Village'] == selected_village]
        
        if selected_theme != "All": filtered_df = filtered_df[filtered_df['Clean_Theme'] == selected_theme]
        if selected_tier != "All": filtered_df = filtered_df[filtered_df['Clean_Tier'] == selected_tier]
        if selected_pillar != "All": filtered_df = filtered_df[filtered_df['Clean_Pillar'].str.contains(selected_pillar, case=False, na=False)]

    # -------------------------------------------------------------------------
    # CENTER MAP & SUMMARY
    # -------------------------------------------------------------------------
    crumb_state = selected_state if selected_state != "No Data" else "State"
    crumb_dist = selected_district if selected_district != "All Districts" else "District"
    crumb_block = selected_block if selected_block != "All Blocks" else "Block"
    crumb_vill = selected_village if selected_village != "All Villages" else "Village"

    st.markdown(f"""
    <div class="breadcrumb">
      <span>India</span><span class="sep">›</span>
      <span>{crumb_state}</span><span class="sep">›</span>
      <span>{crumb_dist}</span><span class="sep">›</span>
      <span>{crumb_block}</span><span class="sep">›</span>
      <span>GP</span><span class="sep">›</span>
      <span class="current">{crumb_vill}</span>
    </div>
    """, unsafe_allow_html=True)

    with col_center:
        st.markdown('<div class="html-card">', unsafe_allow_html=True)
        st.markdown(f"<div style='font-family: Space Grotesk; font-size: 15px; margin-bottom: 10px;'>{crumb_dist} — Geospatial View<br><span style='font-family: IBM Plex Mono; font-size: 11px; color: var(--ink-soft);'>Filtered LCAT locations</span></div>", unsafe_allow_html=True)
        
        center_lat, center_lng = 21.0, 81.0
        zoom_start = 8
        if selected_district in DISTRICT_CENTERS:
            center_lat, center_lng = DISTRICT_CENTERS[selected_district]["lat"], DISTRICT_CENTERS[selected_district]["lng"]
            zoom_start = 9
        
        m = folium.Map(location=[center_lat, center_lng], zoom_start=zoom_start, tiles="CartoDB positron")
        
        # Build map points from filtered data
        v_count = 0
        if not filtered_df.empty:
            village_groups = filtered_df.groupby('Panchayat/Village')
            v_count = len(village_groups)
            
            for v_name, group in village_groups:
                total_demands = len(group)
                dominant = group['Clean_Theme'].mode()
                dom_element = dominant.iloc[0] if not dominant.empty else "Unknown"
                
                # Jitter for map display based on district center
                dist_name = group['District'].iloc[0] if 'District' in group.columns else ""
                dc = DISTRICT_CENTERS.get(dist_name, {"lat": center_lat, "lng": center_lng})
                lat = dc["lat"] + np.random.uniform(-0.15, 0.15)
                lng = dc["lng"] + np.random.uniform(-0.15, 0.15)
                
                radius = max(6, min(22, int(total_demands * 0.5)))
                fill_col = ELEMENT_COLORS.get(dom_element, "#cbd5e1")
                
                folium.CircleMarker(
                    location=[lat, lng], radius=radius, color="#FCFBF6", weight=1.5, fill=True, fill_color=fill_col, fill_opacity=0.85,
                    tooltip=folium.Tooltip(f"<div style='font-family:IBM Plex Sans;padding:8px;'><b>{v_name}</b><br>Filtered Demands: {total_demands}<br>Dom. Theme: {dom_element}</div>", sticky=True)
                ).add_to(m)
            
        st_folium(m, use_container_width=True, height=400, returned_objects=[])
        st.markdown('</div>', unsafe_allow_html=True)

        # Block Summary
        if not filtered_df.empty:
            total_actions = len(filtered_df)
            t1_count = len(filtered_df[filtered_df['Clean_Tier'] == 'Tier 1 — Community Led'])
            t2_count = len(filtered_df[filtered_df['Clean_Tier'] == 'Tier 2 — Minor Support'])
            t3_count = len(filtered_df[filtered_df['Clean_Tier'] == 'Tier 3 — External Support & Convergence'])
        else:
            total_actions = t1_count = t2_count = t3_count = 0
            
        p1 = (t1_count / total_actions * 100) if total_actions > 0 else 0
        p2 = (t2_count / total_actions * 100) if total_actions > 0 else 0
        p3 = (t3_count / total_actions * 100) if total_actions > 0 else 0

        st.markdown(f"""
        <div class="block-summary">
            <h3>{crumb_block} Summary <span class="n">{v_count} villages · {total_actions} priority actions</span></h3>
            <div class="dist-bar">
                <div style="width:{p1}%;background:{tier_colors['Tier 1 — Community Led']}"></div>
                <div style="width:{p2}%;background:{tier_colors['Tier 2 — Minor Support']}"></div>
                <div style="width:{p3}%;background:{tier_colors['Tier 3 — External Support & Convergence']}"></div>
            </div>
            <div class="tier-counts">
                <div><b>{t1_count}</b><span>Tier 1 actions</span></div>
                <div><b>{t2_count}</b><span>Tier 2 actions</span></div>
                <div><b>{t3_count}</b><span>Tier 3 actions</span></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # -------------------------------------------------------------------------
    # RIGHT PROFILE
    # -------------------------------------------------------------------------
    with col_right:
        st.markdown(f"""
        <div class="profile-header">
            <h2>{crumb_vill} Profile</h2>
            <div class="loc">{crumb_block} · {crumb_dist} · {crumb_state}</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="score-block">
            <div class="txt" style="width: 100%">
                <b>Overall LCAT score</b>
                <span class="cls">NaN</span>
                <span style="font-size: 11px; color: var(--ink-soft); float: right; margin-top: 4px;">Score logic pending</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown('<div class="section-label">Sub-scores</div>', unsafe_allow_html=True)
        for lbl in ["Physical condition", "Vegetation condition", "Hydrological condition", "Anthropogenic pressure (inv.)"]:
            st.markdown(f"""
            <div style="margin-bottom:10px;">
                <div style="display:flex;justify-content:space-between;font-size:12px;margin-bottom:4px;">
                    <span>{lbl}</span><b style="font-family:'IBM Plex Mono'">NaN</b>
                </div>
                <div style="height:7px;background:var(--paper-deep);border-radius:4px;"></div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown('<div class="section-label">Land characteristics</div>', unsafe_allow_html=True)
        st.markdown("""
        <div class="stat-grid">
            <div><b>NaN</b><span>Elevation</span></div>
            <div><b>NaN</b><span>Mean slope</span></div>
            <div><b>NaN</b><span>Forest cover</span></div>
            <div><b>NaN</b><span>Agriculture</span></div>
            <div><b>NaN</b><span>Built-up</span></div>
            <div><b>NaN</b><span>Dist. to river</span></div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="section-label" style="margin-top: 24px;">Priority actions preview</div>', unsafe_allow_html=True)
        
        if selected_district != "All Districts" and selected_theme != "All":
            if not filtered_df.empty:
                display_acts = filtered_df.head(3)
                for _, row in display_acts.iterrows():
                    tier_name = row['Clean_Tier']
                    tier_col = tier_colors.get(tier_name, "var(--line)")
                    pill_text = "TIER" if tier_name == "Unknown" else tier_name.split(" —")[0].upper()
                    
                    st.markdown(f"""
                    <div class="action-item" style="border-left-color: {tier_col};">
                        <div class="atxt">{row.get('Priority Action', 'N/A')}</div>
                        <div class="tag-row">
                            <span class="tag" style="background: {tier_col}; color: #fff; font-weight: 600;">{pill_text}</span>
                            <span class="tag">{row['Clean_Theme']}</span>
                            <span class="tag">{row['Clean_Pillar']}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                if len(filtered_df) > 3:
                    if st.button("See more actions & community voices"):
                        show_theme_overlay(selected_theme, selected_state, selected_district, selected_village, raw_gpdp_df)
            else:
                st.markdown("<div style='color: var(--ink-soft); font-size: 12.5px;'>No actions match the current filters.</div>", unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="background: var(--paper-deep); padding: 12px; border-radius: 8px; font-size: 12.5px; color: var(--ink-soft); text-align: center;">
                Select a <b>District</b> and an <b>LCAT Theme</b> to view specific priority actions and community voices.
            </div>
            """, unsafe_allow_html=True)

    # -------------------------------------------------------------------------
    # LOWER ANALYTICS (Filtered by Geo ONLY, not Theme/Tier)
    # -------------------------------------------------------------------------
    st.markdown("<hr style='border-color: var(--line); margin: 40px 0;'>", unsafe_allow_html=True)
    
    st.markdown("<h3 style='text-align:center; font-family: Space Grotesk;'>Analytical Summary</h3>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color: var(--ink-soft); font-size: 13px; margin-bottom: 30px;'>Distribution of implementation tiers across landscape themes and pillars</p>", unsafe_allow_html=True)
    
    col_a1, col_a2 = st.columns([1, 1], gap="large")
    
    geo_df = raw_gpdp_df.copy()
    if not geo_df.empty:
        if selected_state != "No Data": geo_df = geo_df[geo_df['State'] == selected_state]
        if selected_district != "All Districts": geo_df = geo_df[geo_df['District'] == selected_district]
        if selected_block != "All Blocks": geo_df = geo_df[geo_df['Block'] == selected_block]
        if selected_village != "All Villages": geo_df = geo_df[geo_df['Panchayat/Village'] == selected_village]
    
    with col_a1:
        if not geo_df.empty:
            theme_tier_df = geo_df[geo_df['Clean_Tier'] != 'Unknown'].groupby(['Clean_Theme', 'Clean_Tier']).size().reset_index(name='Count')
            if not theme_tier_df.empty:
                theme_pivot = theme_tier_df.pivot(index='Clean_Theme', columns='Clean_Tier', values='Count').fillna(0)
                theme_pivot['Total'] = theme_pivot.sum(axis=1)
                plot_df_theme = theme_pivot.drop(columns=['Total']).reset_index().melt(id_vars='Clean_Theme', var_name='Tier', value_name='Count')
                
                fig_theme = make_subplots(rows=2, cols=4, specs=[[{'type': 'domain'}] * 4] * 2, subplot_titles=LCAT_ELEMENTS, vertical_spacing=0.15)
                
                for i, theme in enumerate(LCAT_ELEMENTS):
                    r, c = (i // 4) + 1, (i % 4) + 1
                    if theme in theme_pivot.index:
                        tdata = plot_df_theme[(plot_df_theme['Clean_Theme'] == theme) & (plot_df_theme['Count'] > 0)]
                        colors = [tier_colors.get(t, "#cbd5e1") for t in tdata['Tier']]
                        fig_theme.add_trace(go.Pie(
                            labels=tdata['Tier'], values=tdata['Count'], hole=0.68,
                            title={'text': f"<b>{int(theme_pivot.loc[theme, 'Total'])}</b>", 'font': {'size': 14, 'color': '#20281F'}},
                            marker=dict(colors=colors, line=dict(color='#F4F1E7', width=1.5)),
                            textinfo='none', hoverinfo='label+percent+value', name=theme, sort=False
                        ), row=r, col=c)
                    else:
                        fig_theme.add_trace(go.Pie(labels=['No Data'], values=[1], hole=0.68, title={'text': "0", 'font': {'size': 14, 'color': '#C9C2AC'}}, marker=dict(colors=['#DFDACB']), textinfo='none', hoverinfo='none', sort=False), row=r, col=c)
                        
                fig_theme.update_layout(
                    title_text="Tiers across Themes", title_font=dict(size=15, color="#20281F", family="Space Grotesk"),
                    plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#20281F", size=11, family="IBM Plex Sans"),
                    margin=dict(l=10, r=10, t=50, b=90), height=400, showlegend=False
                )
                
                for annotation in fig_theme['layout']['annotations']:
                    annotation['yanchor'] = 'top'
                    annotation['y'] -= 0.48
                    annotation['text'] = "<br>".join(textwrap.wrap(annotation['text'], width=22))
                    annotation['font'] = dict(size=10.5, color="#4C5646", family="IBM Plex Mono")
                    
                if HAS_PLOTLY_EVENTS:
                    clicked = plotly_events(fig_theme, click_event=True, hover_event=False, select_event=False, key="theme_chart", override_height=400)
                    if clicked and len(clicked) > 0:
                        curve_idx = clicked[0].get("curveNumber", -1)
                        if 0 <= curve_idx < len(LCAT_ELEMENTS):
                            show_theme_overlay(LCAT_ELEMENTS[curve_idx], selected_state, selected_district, selected_village, raw_gpdp_df)
                else:
                    st.plotly_chart(fig_theme, use_container_width=True, config={'displayModeBar': False})
            else:
                st.info("No tier data available for rings.")
        else:
            st.info("No data available.")

    with col_a2:
        if not geo_df.empty and 'Clean_Pillar' in geo_df.columns:
            pillar_tier_df = geo_df[(geo_df['Clean_Tier'] != 'Unknown') & (geo_df['Clean_Pillar'] != 'Unknown')].groupby(['Clean_Pillar', 'Clean_Tier']).size().reset_index(name='Count')
            if not pillar_tier_df.empty:
                pillar_pivot = pillar_tier_df.pivot(index='Clean_Pillar', columns='Clean_Tier', values='Count').fillna(0)
                pillar_pivot['Total'] = pillar_pivot.sum(axis=1)
                plot_df_pillar = pillar_pivot.drop(columns=['Total']).reset_index().melt(id_vars='Clean_Pillar', var_name='Tier', value_name='Count')
                
                pillars_list = ["Adaptation", "Mitigation", "Restoration"]
                fig_pillar = make_subplots(rows=1, cols=3, specs=[[{'type': 'domain'}] * 3], subplot_titles=pillars_list)
                
                for i, pillar in enumerate(pillars_list):
                    if pillar in pillar_pivot.index:
                        pdata = plot_df_pillar[(plot_df_pillar['Clean_Pillar'] == pillar) & (plot_df_pillar['Count'] > 0)]
                        colors = [tier_colors.get(t, "#cbd5e1") for t in pdata['Tier']]
                        fig_pillar.add_trace(go.Pie(
                            labels=pdata['Tier'], values=pdata['Count'], hole=0.68,
                            title={'text': f"<b>{int(pillar_pivot.loc[pillar, 'Total'])}</b>", 'font': {'size': 18, 'color': '#20281F'}},
                            marker=dict(colors=colors, line=dict(color='#F4F1E7', width=2)),
                            textinfo='none', hoverinfo='label+percent+value', name=pillar, sort=False
                        ), row=1, col=i+1)
                    else:
                        fig_pillar.add_trace(go.Pie(labels=['No Data'], values=[1], hole=0.68, title={'text': "0", 'font': {'size': 18, 'color': '#C9C2AC'}}, marker=dict(colors=['#DFDACB']), textinfo='none', hoverinfo='none', sort=False), row=1, col=i+1)
                        
                fig_pillar.update_layout(
                    title_text="Tiers across Pillars", title_font=dict(size=15, color="#20281F", family="Space Grotesk"),
                    plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#20281F", size=11, family="IBM Plex Sans"),
                    margin=dict(l=10, r=10, t=50, b=90), height=250, showlegend=True,
                    legend=dict(orientation="h", yanchor="top", y=-0.3, xanchor="center", x=0.5, font=dict(color="#4C5646", family="IBM Plex Mono"), title="")
                )
                
                for annotation in fig_pillar['layout']['annotations']:
                    annotation['yanchor'] = 'top'
                    annotation['y'] -= 1.05
                    annotation['font'] = dict(size=11, color="#4C5646", family="IBM Plex Mono")
                    
                st.plotly_chart(fig_pillar, use_container_width=True, config={'displayModeBar': False})
                
        # District Trajectory (Pie charts only)
        st.markdown("<h4 style='margin-top: 20px; font-family: Space Grotesk;'>District LCAT Landscape Trajectory</h4>", unsafe_allow_html=True)
        
        file_path = "data/District Wise LCAT.xlsx"
        if os.path.exists(file_path):
            try:
                traj_df = pd.read_excel(file_path)
                dist_col = next((c for c in traj_df.columns if 'district' in str(c).lower()), None)
                if dist_col: traj_df = traj_df.rename(columns={dist_col: "District"})
                
                if selected_district != "All Districts":
                    filtered_traj = traj_df[traj_df["District"] == selected_district]
                else:
                    filtered_traj = traj_df[traj_df["District"].isin(dist_options)] if selected_state != "No Data" else traj_df.copy()
                    
                if not filtered_traj.empty:
                    valid_themes = [t for t in traj_df.columns if t in LCAT_ELEMENTS]
                    if not valid_themes: valid_themes = [c for c in traj_df.columns if c not in ["District", "State"]]
                    
                    status_colors = {"Improving": "var(--sage)", "Stable": "var(--slate)", "Mixed": "var(--ochre)", "Declining": "var(--brick)", "Unknown": "var(--paper-deep)"}
                    
                    fig_traj = make_subplots(rows=2, cols=4, specs=[[{'type': 'domain'}] * 4] * 2, subplot_titles=valid_themes, vertical_spacing=0.2)
                    for i, theme in enumerate(valid_themes):
                        r, c = (i // 4) + 1, (i % 4) + 1
                        if theme in filtered_traj.columns:
                            counts = filtered_traj[theme].astype(str).str.strip().value_counts().reset_index()
                            counts.columns = ["Status", "Count"]
                            colors = [status_colors.get(s, status_colors["Unknown"]) for s in counts["Status"]]
                            
                            fig_traj.add_trace(go.Pie(
                                labels=counts["Status"], values=counts["Count"], hole=0.65,
                                title={'text': f"<b>{len(filtered_traj)}</b>", 'font': {'size': 14, 'color': '#20281F'}},
                                marker=dict(colors=colors, line=dict(color='#F4F1E7', width=1.5)),
                                textinfo='none', hoverinfo='label+value', name=theme, sort=False
                            ), row=r, col=c)
                        else:
                            fig_traj.add_trace(go.Pie(labels=['Unavailable'], values=[1], hole=0.65, title={'text': "0", 'font': {'size': 14, 'color': '#C9C2AC'}}, marker=dict(colors=['#DFDACB']), textinfo='none', hoverinfo='none', sort=False), row=r, col=c)

                    fig_traj.update_layout(
                        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#20281F", size=11, family="IBM Plex Sans"),
                        margin=dict(l=10, r=10, t=30, b=40), height=300, showlegend=True,
                        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5, font=dict(color="#4C5646", family="IBM Plex Mono"))
                    )
                    for annotation in fig_traj['layout']['annotations']:
                        annotation['y'] -= 0.6
                        annotation['text'] = "<br>".join(textwrap.wrap(annotation['text'], width=16))
                        annotation['font'] = dict(size=10.5, color="#4C5646", family="IBM Plex Mono")
                        
                    st.plotly_chart(fig_traj, use_container_width=True, config={'displayModeBar': False})
                else:
                    st.info("No trajectory data available for selection.")
            except Exception:
                st.info("Error reading trajectory file.")
        else:
            st.info("Trajectory file not found in data/.")

# -----------------------------------------------------------------------------
# CLIMATE SIGNALS DASHBOARD MODE
# -----------------------------------------------------------------------------
elif dashboard_mode == "Climate Signals":
    df_climate = load_climate_data()
    avail_clim_states = df_climate["state"].dropna().unique().tolist() if not df_climate.empty else ["No Data"]
    
    st.markdown("""
    <div class="lcat-header">
      <div class="brand"><b>CLIMATE SIGNALS</b><span>VULNERABILITY & THERMAL STRESS</span></div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    c_left, c_right = st.columns([1, 4])
    
    with c_left:
        st.markdown('<div class="section-label">Geographic selection</div>', unsafe_allow_html=True)
        selected_clim_state = st.selectbox("State", avail_clim_states, key="clim_state")
        df_state = df_climate[df_climate["state"] == selected_clim_state] if not df_climate.empty else df_climate
        clim_dist_opts = ["All Districts"] + df_state["district"].dropna().unique().tolist() if not df_state.empty else ["All Districts"]
        selected_clim_dist = st.selectbox("District", clim_dist_opts, key="clim_dist")

    ndmi_colors = {"Severe Canopy Desiccation": "var(--brick)", "Moisture Loss": "var(--ochre)", "Stable": "var(--paper-deep)", "Moisture Gain": "var(--slate)", "Little or No Change": "var(--paper-deep)"}
    lst_colors = {"Severe Warming": "var(--brick)", "Moderate Warming": "var(--ochre)", "Stable": "var(--paper-deep)", "Cooling Trend": "var(--slate)", "Little or No Change": "var(--paper-deep)"}

    with c_right:
        if selected_clim_dist == "All Districts":
            st.markdown("<h3 style='font-family: Space Grotesk;'>Climate Signals Overview</h3>", unsafe_allow_html=True)
            if not df_state.empty:
                col_ndmi, col_lst = st.columns(2)
                with col_ndmi:
                    st.markdown("##### NDMI Status Distribution")
                    ndmi_counts = df_state['canopy_moisture_status'].value_counts().reset_index()
                    ndmi_counts.columns = ['Status', 'Districts']
                    fig_ndmi = px.pie(ndmi_counts, names='Status', values='Districts', hole=0.6, color='Status', color_discrete_map=ndmi_colors)
                    fig_ndmi.update_layout(paper_bgcolor='rgba(0,0,0,0)', font=dict(family='IBM Plex Mono'), margin=dict(t=20, b=20, l=10, r=10), legend=dict(orientation="h", y=-0.2), height=350)
                    st.plotly_chart(fig_ndmi, use_container_width=True, config={'displayModeBar': False})
                    
                with col_lst:
                    st.markdown("##### LST Status Distribution")
                    lst_counts = df_state['summer_lst_status'].value_counts().reset_index()
                    lst_counts.columns = ['Status', 'Districts']
                    fig_lst = px.pie(lst_counts, names='Status', values='Districts', hole=0.6, color='Status', color_discrete_map=lst_colors)
                    fig_lst.update_layout(paper_bgcolor='rgba(0,0,0,0)', font=dict(family='IBM Plex Mono'), margin=dict(t=20, b=20, l=10, r=10), legend=dict(orientation="h", y=-0.2), height=350)
                    st.plotly_chart(fig_lst, use_container_width=True, config={'displayModeBar': False})
            else:
                st.info("No climate data available for this state.")
        else:
            dist_row = df_state[df_state["district"] == selected_clim_dist]
            if not dist_row.empty:
                row = dist_row.iloc[0]
                
                k1, k2, k3, k4 = st.columns(4)
                def render_metric(label, val, desc):
                    return f"""
                    <div style="background: var(--card); border: 1px solid var(--line); border-top: 3px solid var(--ochre); border-radius: 8px; padding: 18px;">
                        <div style="font-family: 'IBM Plex Mono'; font-size: 10.5px; color: var(--ink-soft); text-transform: uppercase;">{label}</div>
                        <div style="font-size: 1.6rem; font-weight: 700; color: var(--pine); font-family: 'Space Grotesk'; margin: 4px 0;">{val}</div>
                        <div style="font-size: 11px; color: var(--ink-soft);">{desc}</div>
                    </div>
                    """
                
                with k1: st.markdown(render_metric("NDMI CHANGE", row.get('canopy_moisture_pct_change', 'N/A'), "Percentage Change"), unsafe_allow_html=True)
                with k2: st.markdown(render_metric("NDMI STATUS", f"<span style='font-size:1.1rem;'>{row.get('canopy_moisture_status', 'N/A')}</span>", "Canopy Moisture"), unsafe_allow_html=True)
                with k3: st.markdown(render_metric("LST CHANGE", f"{row.get('summer_lst_change_c', 'N/A')} °C", "Temperature Change"), unsafe_allow_html=True)
                with k4: st.markdown(render_metric("LST STATUS", f"<span style='font-size:1.1rem;'>{row.get('summer_lst_status', 'N/A')}</span>", "Thermal Stress"), unsafe_allow_html=True)
                
                st.markdown("<br><hr style='border-color: var(--line);'>", unsafe_allow_html=True)
                dist_clean = str(selected_clim_dist).lower().replace(' ', '_')
                
                st.markdown("<h3 style='font-family: Space Grotesk;'>Canopy Moisture — NDMI</h3>", unsafe_allow_html=True)
                i1, i2, i3 = st.columns(3)
                with i1:
                    st.markdown("**2001–2010 Baseline**")
                    path_b = f"data/climate_vulnerability/imagery/{dist_clean}_ndmi_baseline.png"
                    if os.path.exists(path_b): st.image(path_b, use_container_width=True)
                    else: st.info("Image not found")
                with i2:
                    st.markdown("**2015–2024 Recent**")
                    path_r = f"data/climate_vulnerability/imagery/{dist_clean}_ndmi_recent.png"
                    if os.path.exists(path_r): st.image(path_r, use_container_width=True)
                    else: st.info("Image not found")
                with i3:
                    st.markdown("**Change**")
                    path_c = f"data/climate_vulnerability/imagery/{dist_clean}_ndmi_change.png"
                    if os.path.exists(path_c): st.image(path_c, use_container_width=True)
                    else: st.info("Image not found")
                    
                st.markdown("""
                <div style='text-align: center; font-size: 11px; padding: 10px; color: var(--ink-soft); font-family: IBM Plex Mono;'>
                    🔴 <b>Red</b> → Moisture Loss / Drying &nbsp;&nbsp;&nbsp; ⚪ <b>White</b> → Little or No Change &nbsp;&nbsp;&nbsp; 🔵 <b>Blue</b> → Moisture Gain
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown("<hr style='border-color: var(--line); margin: 32px 0;'>", unsafe_allow_html=True)
                
                st.markdown("<h3 style='font-family: Space Grotesk;'>Thermal Stress — LST</h3>", unsafe_allow_html=True)
                l1, l2, l3 = st.columns(3)
                with l1:
                    st.markdown("**2001–2010 Baseline**")
                    path_lb = f"data/climate_vulnerability/imagery/{dist_clean}_lst_baseline.png"
                    if os.path.exists(path_lb): st.image(path_lb, use_container_width=True)
                    else: st.info("Image not found")
                with l2:
                    st.markdown("**2015–2024 Recent**")
                    path_lr = f"data/climate_vulnerability/imagery/{dist_clean}_lst_recent.png"
                    if os.path.exists(path_lr): st.image(path_lr, use_container_width=True)
                    else: st.info("Image not found")
                with l3:
                    st.markdown("**Change**")
                    path_lc = f"data/climate_vulnerability/imagery/{dist_clean}_lst_change.png"
                    if os.path.exists(path_lc): st.image(path_lc, use_container_width=True)
                    else: st.info("Image not found")
                    
                st.markdown("""
                <div style='text-align: center; font-size: 11px; padding: 10px; color: var(--ink-soft); font-family: IBM Plex Mono;'>
                    🔵 <b>Blue</b> → Cooling &nbsp;&nbsp;&nbsp; ⚪ <b>White</b> → Little or No Change &nbsp;&nbsp;&nbsp; 🔴 <b>Red</b> → Warming
                </div>
                """, unsafe_allow_html=True)
            else:
                st.warning("Data not found for the selected district.")
```eof
