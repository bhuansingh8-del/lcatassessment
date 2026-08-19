import streamlit as st
import folium
from streamlit_folium import st_folium
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import json
import base64
from typing import Dict, Any, List, Optional

# -----------------------------------------------------------------------------
# 1. PAGE CONFIGURATION & CUSTOM CSS (Brand Colors: #712416 & #151827)
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Landscape Assessment",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    /* Global Dark Theme */
    .stApp {
        background-color: #0b0f19;
        color: #f8fafc;
        font-family: 'Inter', sans-serif;
    }
    
    /* Fix for text rendering black in Streamlit's Light Mode */
    .stApp p, .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6, .stApp label {
        color: #f8fafc !important;
    }
    
    /* Top Header Bar */
    .header-banner {
        background: linear-gradient(90deg, #712416 0%, #54190F 100%);
        border-bottom: 2px solid #8C2F1E;
        padding: 12px 20px;
        border-radius: 10px;
        margin-bottom: 16px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 4px 20px rgba(0,0,0,0.5);
    }
    
    .header-title {
        color: #ffffff;
        font-size: 1.15rem;
        font-weight: 700;
        margin: 0;
    }
    .header-subtitle {
        color: #fde68a;
        font-size: 0.78rem;
        margin: 0;
    }

    /* Cards */
    .metric-card {
        background: #151827;
        border: 1px solid #712416;
        border-radius: 10px;
        padding: 14px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.4);
    }
    
    .metric-value {
        font-size: 1.6rem;
        font-weight: 700;
        color: #fbbf24;
    }

    /* Tooltip / Badges */
    .badge-burgundy {
        background-color: #712416;
        color: #ffffff;
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 600;
        border: 1px solid #8C2F1E;
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
    "Hydrology": "#38bdf8",
    "Land cover and Agriculture": "#4ade80",
    "Cultural and historical features": "#f472b6",
    "Visual and Sensory qualities": "#a78bfa",
    "Wildlife and Biodiversity richness": "#fb923c",
    "Infrastructure and Economic factors": "#94a3b8",
    "Community and Governance": "#facc15"
}

DISTRICT_CENTERS = {
    "Bastar": {"lat": 19.35, "lng": 81.80, "bounds": [[18.90, 81.55], [19.75, 82.50]]},
    "Kanker": {"lat": 20.27, "lng": 81.49, "bounds": [[19.90, 80.95], [20.75, 81.95]]},
    "Dhamtari": {"lat": 20.70, "lng": 81.55, "bounds": [[20.40, 81.20], [21.05, 81.90]]},
    "Kondagaon": {"lat": 19.60, "lng": 81.66, "bounds": [[19.30, 81.30], [19.90, 82.00]]},
    "Aligarh": {"lat": 27.89, "lng": 78.08, "bounds": [[27.65, 77.40], [28.25, 78.20]]},
    "Banda": {"lat": 25.48, "lng": 80.33, "bounds": [[24.85, 80.05], [25.55, 80.85]]}
}

@st.cache_data
def get_sample_villages() -> pd.DataFrame:
    data = [
        # Bastar
        {"id": "V_001", "name": "Sidesar", "district": "Bastar", "block": "Bakawand", "lat": 19.12, "lng": 81.85, "totalDemand": 28, "tier1": 8, "tier2": 8, "tier3": 12, "dominantElement": "Land cover and Agriculture", "riskScore": 68},
        {"id": "V_002", "name": "Karpawand", "district": "Bastar", "block": "Bakawand", "lat": 19.18, "lng": 81.92, "totalDemand": 45, "tier1": 15, "tier2": 18, "tier3": 12, "dominantElement": "Hydrology", "riskScore": 74},
        {"id": "V_003", "name": "Nagarnar", "district": "Bastar", "block": "Jagdalpur", "lat": 19.08, "lng": 82.10, "totalDemand": 36, "tier1": 10, "tier2": 14, "tier3": 12, "dominantElement": "Infrastructure and Economic factors", "riskScore": 55},
        {"id": "V_004", "name": "Tokapal", "district": "Bastar", "block": "Tokapal", "lat": 18.98, "lng": 81.78, "totalDemand": 52, "tier1": 20, "tier2": 18, "tier3": 14, "dominantElement": "Wildlife and Biodiversity richness", "riskScore": 82},
        # Kanker
        {"id": "V_005", "name": "Narharpur", "district": "Kanker", "block": "Narharpur", "lat": 20.35, "lng": 81.65, "totalDemand": 40, "tier1": 12, "tier2": 16, "tier3": 12, "dominantElement": "Hydrology", "riskScore": 62},
        {"id": "V_006", "name": "Charama", "district": "Kanker", "block": "Charama", "lat": 20.48, "lng": 81.38, "totalDemand": 30, "tier1": 9, "tier2": 11, "tier3": 10, "dominantElement": "Landform and topography", "riskScore": 50},
        {"id": "V_007", "name": "Antagarh", "district": "Kanker", "block": "Antagarh", "lat": 20.08, "lng": 81.18, "totalDemand": 65, "tier1": 24, "tier2": 26, "tier3": 15, "dominantElement": "Land cover and Agriculture", "riskScore": 85},
        # Kondagaon
        {"id": "V_008", "name": "Keskal", "district": "Kondagaon", "block": "Keskal", "lat": 19.88, "lng": 81.58, "totalDemand": 58, "tier1": 20, "tier2": 22, "tier3": 16, "dominantElement": "Landform and topography", "riskScore": 79},
        {"id": "V_009", "name": "Makdi", "district": "Kondagaon", "block": "Makdi", "lat": 19.72, "lng": 81.82, "totalDemand": 34, "tier1": 10, "tier2": 14, "tier3": 10, "dominantElement": "Cultural and historical features", "riskScore": 48},
        # Dhamtari
        {"id": "V_010", "name": "Nagri", "district": "Dhamtari", "block": "Nagri", "lat": 20.55, "lng": 81.85, "totalDemand": 48, "tier1": 16, "tier2": 18, "tier3": 14, "dominantElement": "Hydrology", "riskScore": 70},
        {"id": "V_011", "name": "Kurud", "district": "Dhamtari", "block": "Kurud", "lat": 20.82, "lng": 81.71, "totalDemand": 22, "tier1": 6, "tier2": 8, "tier3": 8, "dominantElement": "Infrastructure and Economic factors", "riskScore": 42},
    ]
    return pd.DataFrame(data)

def get_demand_color(demand: int) -> str:
    if demand <= 35:
        return "#F3E3C1"
    elif demand <= 65:
        return "#D99A38"
    elif demand <= 90:
        return "#C85C3A"
    return "#712416"


# -----------------------------------------------------------------------------
# 3. SIDEBAR & GEOGRAPHIC SELECTION
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown('<div class="badge-burgundy">#712416 CONTROLS</div>', unsafe_allow_html=True)
    st.subheader("Geographic Filters")
    
    df_villages = get_sample_villages()
    
    # State & District Selector
    selected_state = st.selectbox("State", ["Chhattisgarh", "Uttar Pradesh"])
    
    if selected_state == "Chhattisgarh":
        dist_options = ["All Districts", "Bastar", "Kanker", "Kondagaon", "Dhamtari"]
    else:
        dist_options = ["All Districts", "Aligarh", "Banda"]
        
    selected_district = st.selectbox("District", dist_options)
    
    # Map Metric
    metric_choice = st.selectbox(
        "Map Metric",
        ["Total GPDP Demand", "Dominant LCAT Element", "Climate Risk Index", "Implementation Tiers"]
    )
    
    # Basemap Mode
    basemap_choice = st.selectbox(
        "Basemap Style",
        ["CartoDB Dark", "CartoDB Positron (Light)", "OpenStreetMap"]
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

# Filter Data
if selected_district != "All Districts":
    filtered_df = df_villages[df_villages["district"] == selected_district]
else:
    filtered_df = df_villages


# -----------------------------------------------------------------------------
# 4. MAIN HEADER BANNER
# -----------------------------------------------------------------------------
st.markdown(f"""
<div class="header-banner">
    <div>
        <h1 class="header-title">Landscape Assessment Atlas</h1>
        <p class="header-subtitle">Climate Risk & Community Demand &nbsp;·&nbsp; {selected_state} › {selected_district}</p>
    </div>
    <div>
        <span class="badge-burgundy">PANTONE 181 C (#712416)</span>
    </div>
</div>
""", unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# 5. HIGH-LEVEL KPI METRICS
# -----------------------------------------------------------------------------
col1, col2, col3, col4 = st.columns(4)

total_villages = len(filtered_df)
total_demands = filtered_df["totalDemand"].sum()
t1_demands = filtered_df["tier1"].sum()
avg_risk = filtered_df["riskScore"].mean() if total_villages > 0 else 0

with col1:
    st.markdown(f"""
    <div class="metric-card">
        <div style="font-size:0.8rem; color:#94a3b8; font-weight:600;">ACTIVE VILLAGES</div>
        <div class="metric-value">{total_villages}</div>
        <div style="font-size:0.75rem; color:#cbd5e1;">Covered Gram Panchayats</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="metric-card">
        <div style="font-size:0.8rem; color:#94a3b8; font-weight:600;">TOTAL GPDP DEMANDS</div>
        <div class="metric-value">{total_demands}</div>
        <div style="font-size:0.75rem; color:#cbd5e1;">Demands Identified in Atlas</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="metric-card">
        <div style="font-size:0.8rem; color:#94a3b8; font-weight:600;">TIER 1 (COMMUNITY ALONE)</div>
        <div class="metric-value">{t1_demands}</div>
        <div style="font-size:0.75rem; color:#cbd5e1;">Immediate Local Delivery</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="metric-card">
        <div style="font-size:0.8rem; color:#94a3b8; font-weight:600;">AVG CLIMATE RISK</div>
        <div class="metric-value" style="color:#ef4444;">{avg_risk:.1f}</div>
        <div style="font-size:0.75rem; color:#cbd5e1;">Composite Vulnerability Index</div>
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
        center_lat = 19.85
        center_lng = 81.65
        zoom_start = 8

    # Basemap tiles
    tile_dict = {
        "CartoDB Dark": "CartoDB dark_matter",
        "CartoDB Positron (Light)": "CartoDB positron",
        "OpenStreetMap": "OpenStreetMap"
    }
    
    m = folium.Map(
        location=[center_lat, center_lng],
        zoom_start=zoom_start,
        tiles=tile_dict[basemap_choice],
        control_scale=True
    )
    
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
                # SVG sample fallback representing district-cut orthorectified imagery
                svg_overlay = f"""
                <svg xmlns="http://www.w3.org/2000/svg" width="600" height="600" viewBox="0 0 600 600">
                    <rect width="600" height="600" fill="#1e3a5f" fill-opacity="0.75" />
                    <circle cx="300" cy="300" r="220" fill="none" stroke="#fbbf24" stroke-width="3" stroke-dasharray="8,6" />
                    <path d="M 80 400 Q 250 150 520 300" fill="none" stroke="#38bdf8" stroke-width="6" />
                    <text x="40" y="60" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">{target_dist} District ({selected_year})</text>
                    <text x="40" y="90" font-family="sans-serif" font-size="16" fill="#fde68a">Orthorectified Geospatial Composite Layer</text>
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
        fill_col = get_demand_color(v["totalDemand"]) if metric_choice == "Total GPDP Demand" else ELEMENT_COLORS.get(v["dominantElement"], "#fbbf24")
        
        radius = max(6, min(22, int(v["totalDemand"] * 0.35)))
        
        # High contrast custom tooltip matching #712416
        tooltip_html = f"""
        <div style="background-color:#151827; color:#ffffff; border:1.5px solid #712416; border-radius:8px; padding:10px; font-family:sans-serif; min-width:180px;">
            <div style="font-weight:bold; font-size:13px; color:#ffffff;">{v['name']} Village</div>
            <div style="font-weight:bold; font-size:12px; color:#fbbf24; margin-top:2px;">Total GPDP Demands: {v['totalDemand']}</div>
            <div style="font-size:11px; color:#cbd5e1; border-top:1px solid #343A4D; margin-top:6px; padding-top:4px;">
                T1: <b>{v['tier1']}</b> · T2: <b>{v['tier2']}</b> · T3: <b>{v['tier3']}</b>
            </div>
            <div style="font-size:10px; color:#94a3b8; margin-top:4px;">
                Dominant Theme: <span style="color:#fde68a; font-weight:600;">{v['dominantElement']}</span>
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
    
    # 1. Demand by LCAT Life Element Bar Chart
    element_counts = filtered_df["dominantElement"].value_counts().reset_index()
    element_counts.columns = ["Element", "Villages"]
    
    fig_bar = px.bar(
        element_counts,
        x="Villages",
        y="Element",
        orientation="h",
        color="Element",
        color_discrete_map=ELEMENT_COLORS,
        title="Dominant LCAT Life Elements across Panchayats"
    )
    
    fig_bar.update_layout(
        plot_bgcolor="#151827",
        paper_bgcolor="#151827",
        font=dict(color="#f8fafc", size=11),
        showlegend=False,
        margin=dict(l=10, r=10, t=35, b=10),
        height=260,
        xaxis=dict(gridcolor="#343a4d"),
        yaxis=dict(gridcolor="#343a4d", categoryorder="total ascending")
    )
    st.plotly_chart(fig_bar, use_container_width=True)
    
    # 2. Tiers Breakdown Donut Chart
    tier_data = pd.DataFrame({
        "Tier": ["Tier 1 (community alone)", "Tier 2 (Minor Support)", "Tier 3 (Convergence)"],
        "Demands": [filtered_df["tier1"].sum(), filtered_df["tier2"].sum(), filtered_df["tier3"].sum()]
    })
    
    fig_donut = px.pie(
        tier_data,
        names="Tier",
        values="Demands",
        hole=0.55,
        color="Tier",
        color_discrete_map={
            "Tier 1 (community alone)": "#fbbf24",
            "Tier 2 (Minor Support)": "#712416",
            "Tier 3 (Convergence)": "#38bdf8"
        },
        title="Implementation Tier Convergence"
    )
    
    fig_donut.update_layout(
        plot_bgcolor="#151827",
        paper_bgcolor="#151827",
        font=dict(color="#f8fafc", size=11),
        margin=dict(l=10, r=10, t=35, b=10),
        height=260,
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
    )
    st.plotly_chart(fig_donut, use_container_width=True)


# -----------------------------------------------------------------------------
# 8. VILLAGE DATA TABLE
# -----------------------------------------------------------------------------
st.markdown("### Gram Panchayat Action Registry")
st.dataframe(
    filtered_df[["name", "district", "block", "totalDemand", "tier1", "tier2", "tier3", "dominantElement", "riskScore"]],
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
        "dominantElement": "Dominant LCAT Element",
        "riskScore": st.column_config.NumberColumn("Risk Index", format="%.1f")
    }
)
