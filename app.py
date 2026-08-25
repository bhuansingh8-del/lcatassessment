import streamlit as st
import folium
from streamlit_folium import st_folium
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import os
import re
import html
from typing import Any, Dict, List, Optional
from plotly.subplots import make_subplots
import textwrap

# Optional Plotly click-event component. The dashboard remains usable if it is absent.
try:
    from streamlit_plotly_events import plotly_events
    HAS_PLOTLY_EVENTS = True
except ImportError:
    HAS_PLOTLY_EVENTS = False


# =============================================================================
# 1. PAGE CONFIGURATION + HTML-REFERENCE DESIGN SYSTEM
# =============================================================================
st.set_page_config(
    page_title="LCAT — Landscape Character Assessment Tool",
    page_icon="",
    layout="wide",
    initial_sidebar_state="collapsed",
)

COLORS = {
    "paper": "#EAE6D9",
    "paper_deep": "#DFDACB",
    "ink": "#20281F",
    "ink_soft": "#4C5646",
    "line": "#C9C2AC",
    "pine": "#243D2C",
    "pine_2": "#345040",
    "moss": "#6C7C55",
    "ochre": "#B9863E",
    "brick": "#8C4536",
    "sage": "#7E9767",
    "deepsage": "#3E6B47",
    "slate": "#3E6B78",
    "card": "#F4F1E7",
    "white": "#FCFBF6",
}

TIER_COLORS = {
    "Tier 1 — Community Led": "#d97706",
    "Tier 2 — Minor Support": "#712416",
    "Tier 3 — External Support & Convergence": "#0ea5e9",
}

LCAT_ELEMENTS = [
    "Landform and topography",
    "Hydrology",
    "Land cover and Agriculture",
    "Cultural and historical features",
    "Visual and Sensory qualities",
    "Wildlife and Biodiversity richness",
    "Infrastructure and Economic factors",
    "Community and Governance",
]

PILLARS = ["Adaptation", "Mitigation", "Restoration"]

STATUS_COLORS = {
    "Declining": "#8C4536",
    "Mixed": "#B9863E",
    "Stable": "#3E6B78",
    "Improving": "#3E6B47",
    "Unknown": "#DFDACB",
}

# The current application is intended for light mode only.
st.markdown(
    f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500;600&display=swap');

:root {{
    --paper:{COLORS["paper"]};
    --paper-deep:{COLORS["paper_deep"]};
    --ink:{COLORS["ink"]};
    --ink-soft:{COLORS["ink_soft"]};
    --line:{COLORS["line"]};
    --pine:{COLORS["pine"]};
    --pine-2:{COLORS["pine_2"]};
    --moss:{COLORS["moss"]};
    --ochre:{COLORS["ochre"]};
    --brick:{COLORS["brick"]};
    --sage:{COLORS["sage"]};
    --deepsage:{COLORS["deepsage"]};
    --slate:{COLORS["slate"]};
    --card:{COLORS["card"]};
    --white:{COLORS["white"]};
}}

.stApp {{
    background: var(--paper);
    color: var(--ink);
    font-family: 'IBM Plex Sans', sans-serif;
}}

[data-testid="stSidebar"] {{
    display: none;
}}

section[data-testid="stSidebar"] {{
    display: none;
}}

.block-container {{
    max-width: 100%;
    padding: 0 24px 48px 24px;
}}

h1, h2, h3, h4, h5 {{
    font-family: 'Space Grotesk', sans-serif !important;
    color: var(--ink) !important;
}}

p, label, span, div {{
    font-family: 'IBM Plex Sans', sans-serif;
}}

.lcat-header {{
    background: var(--pine);
    color: var(--white);
    margin: 0 -24px;
    padding: 14px 24px;
    display: flex;
    align-items: center;
    gap: 16px;
    border-bottom: 3px solid var(--ochre);
}}

.lcat-brandmark {{
    width: 34px;
    height: 34px;
    flex: none;
}}

.lcat-brand {{
    display: flex;
    flex-direction: column;
    line-height: 1.08;
}}

.lcat-brand strong {{
    font-family: 'Space Grotesk', sans-serif;
    font-size: 19px;
    letter-spacing: .5px;
}}

.lcat-brand small {{
    font-family: 'IBM Plex Sans', sans-serif;
    font-size: 10px;
    color: #C9D3C2;
    letter-spacing: .35px;
}}

.mode-bar {{
    margin: 10px 0 0 0;
    padding: 5px 8px;
    border: 1px solid var(--line);
    background: rgba(252,251,246,.6);
    border-radius: 7px;
}}

.breadcrumb {{
    margin: 0 -24px;
    padding: 8px 24px;
    background: var(--pine-2);
    color: #DCE4D4;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 12px;
    display: flex;
    align-items: center;
    gap: 6px;
    overflow-x: auto;
    white-space: nowrap;
}}

.breadcrumb .sep {{ opacity: .5; }}
.breadcrumb .current {{ color: var(--ochre); font-weight: 600; }}

.section-label {{
    font-family: 'IBM Plex Mono', monospace;
    font-size: 10.5px;
    letter-spacing: 1.15px;
    text-transform: uppercase;
    color: var(--ink-soft);
    margin: 18px 0 9px;
}}

.subtle-note {{
    color: var(--ink-soft);
    font-family: 'IBM Plex Mono', monospace;
    font-size: 10.5px;
    line-height: 1.45;
}}

.card {{
    background: var(--card);
    border: 1px solid var(--line);
    border-radius: 10px;
    padding: 15px 16px;
}}

.map-title {{
    display:flex;
    justify-content:space-between;
    align-items:baseline;
    gap:12px;
    margin-bottom:10px;
}}

.map-title h2 {{
    font-size:15px !important;
    margin:0 !important;
}}

.map-title span {{
    color:var(--ink-soft);
    font-family:'IBM Plex Mono', monospace;
    font-size:10.5px;
}}

.profile-title {{
    margin:0;
    font-size:20px !important;
}}

.profile-location {{
    margin-top:2px;
    color:var(--ink-soft);
    font-size:11.5px;
}}

.score-card {{
    display:flex;
    align-items:center;
    gap:14px;
    background:var(--card);
    border:1px solid var(--line);
    border-radius:10px;
    padding:13px 14px;
    margin-top:12px;
}}

.score-gauge {{
    width:68px;
    height:68px;
    border-radius:50%;
    border:8px solid var(--paper-deep);
    display:flex;
    align-items:center;
    justify-content:center;
    flex:none;
    background:var(--white);
}}

.score-gauge span {{
    font-family:'IBM Plex Mono', monospace;
    font-weight:600;
    color:var(--pine);
    font-size:15px;
}}

.score-copy strong {{
    display:block;
    font-family:'Space Grotesk', sans-serif;
    font-size:14px;
}}

.score-copy small {{
    display:inline-block;
    margin-top:4px;
    padding:2px 7px;
    border-radius:10px;
    background:var(--paper-deep);
    color:var(--ink-soft);
    font-family:'IBM Plex Mono', monospace;
    font-size:10px;
}}

.subscore {{
    margin: 0 0 10px;
}}

.subscore-head {{
    display:flex;
    justify-content:space-between;
    gap:8px;
    font-size:11.5px;
    margin-bottom:4px;
}}

.subscore-head b {{
    font-family:'IBM Plex Mono', monospace;
}}

.subscore-track {{
    height:7px;
    background:var(--paper-deep);
    border-radius:4px;
    overflow:hidden;
}}

.stat-grid {{
    display:grid;
    grid-template-columns:1fr 1fr;
    gap:10px 16px;
}}

.stat-grid .value {{
    font-family:'IBM Plex Mono', monospace;
    font-size:14px;
    color:var(--ink);
}}

.stat-grid .label {{
    font-size:10px;
    color:var(--ink-soft);
    margin-top:2px;
}}

.summary-title {{
    display:flex;
    justify-content:space-between;
    align-items:baseline;
    gap:10px;
}}

.summary-title h3 {{
    font-size:14px !important;
    margin:0 !important;
}}

.summary-title span {{
    font-family:'IBM Plex Mono', monospace;
    font-size:10.5px;
    color:var(--ink-soft);
}}

.tier-bar {{
    display:flex;
    height:19px;
    border-radius:5px;
    overflow:hidden;
    margin:12px 0 8px;
    background:var(--paper-deep);
}}

.tier-legend {{
    display:flex;
    gap:12px;
    flex-wrap:wrap;
    font-family:'IBM Plex Mono', monospace;
    font-size:9.8px;
    color:var(--ink-soft);
}}

.tier-legend span {{
    display:inline-flex;
    align-items:center;
    gap:4px;
}}

.legend-dot {{
    width:8px;
    height:8px;
    border-radius:2px;
    display:inline-block;
}}

.tier-counts {{
    display:flex;
    gap:26px;
    margin-top:13px;
}}

.tier-counts > div {{
    display:flex;
    flex-direction:column;
}}

.tier-counts .num {{
    font-family:'IBM Plex Mono', monospace;
    font-size:18px;
    color:var(--pine);
}}

.tier-counts .label {{
    font-size:10px;
    color:var(--ink-soft);
}}

.action-preview {{
    border-left:3px solid var(--ochre);
    background:var(--card);
    border-radius:0 8px 8px 0;
    padding:10px 11px;
    margin-bottom:8px;
}}

.action-preview.t2 {{ border-left-color:var(--brick); }}
.action-preview.t3 {{ border-left-color:#0ea5e9; }}

.action-preview .text {{
    font-size:12px;
    line-height:1.36;
    margin-bottom:6px;
}}

.tag-row {{
    display:flex;
    flex-wrap:wrap;
    gap:4px;
}}

.tag {{
    font-family:'IBM Plex Mono', monospace;
    font-size:9px;
    padding:2px 6px;
    border-radius:9px;
    background:var(--paper-deep);
    color:var(--ink-soft);
}}

.tag.t1 {{ background:#d97706; color:#241505; font-weight:600; }}
.tag.t2 {{ background:#712416; color:#fff; font-weight:600; }}
.tag.t3 {{ background:#0ea5e9; color:#06263b; font-weight:600; }}

.focus-pill {{
    display:inline-block;
    font-family:'IBM Plex Mono', monospace;
    font-size:10px;
    padding:5px 9px;
    border-radius:14px;
    background:var(--pine);
    color:var(--white);
    margin:3px 4px 0 0;
}}

.focus-pill.muted {{
    background:var(--paper-deep);
    color:var(--ink-soft);
}}

.analytical-heading {{
    text-align:center;
    margin: 30px 0 18px;
}}

.analytical-heading h2 {{
    margin:0 !important;
    font-size:25px !important;
}}

.analytical-heading p {{
    margin:4px 0 0;
    color:var(--ink-soft);
    font-size:12px;
}}

.chart-card {{
    background:var(--white);
    border:1px solid var(--line);
    border-radius:10px;
    padding:15px 10px 12px;
}}

.chart-title {{
    font-family:'IBM Plex Mono', monospace;
    font-size:10.5px;
    letter-spacing:.4px;
    color:var(--ink-soft);
    text-align:center;
    margin-bottom:5px;
}}

.theme-label {{
    text-align:center;
    color:var(--ink-soft);
    font-family:'IBM Plex Mono', monospace;
    font-size:9.4px;
    line-height:1.25;
    min-height:34px;
    margin-top:-1px;
}}

.trajectory-card {{
    background:var(--card);
    border:1px solid var(--line);
    border-radius:10px;
    padding:14px 10px 11px;
}}

.trajectory-status {{
    display:inline-block;
    font-family:'IBM Plex Mono', monospace;
    font-size:9px;
    padding:3px 7px;
    border-radius:10px;
    margin-top:4px;
}}

.quote-card {{
    background:var(--card);
    border-left:4px solid var(--brick);
    border-radius:0 8px 8px 0;
    padding:13px 14px;
    margin-bottom:12px;
}}

.quote-card .quote {{
    font-size:15px;
    font-style:italic;
    color:var(--ink);
    line-height:1.45;
    margin-bottom:8px;
}}

.quote-card .speaker {{
    font-size:11px;
    font-weight:600;
    color:var(--ink-soft);
}}

.modal-hint {{
    color:var(--ink-soft);
    font-size:11px;
    margin: -2px 0 12px;
}}

div[data-baseweb="select"] > div {{
    background:var(--white) !important;
    color:var(--ink) !important;
    border:1px solid var(--line) !important;
    border-radius:7px !important;
}}

div[data-baseweb="select"] input {{
    color:var(--ink) !important;
}}

[data-testid="stRadio"] > div {{
    gap: 5px;
}}

[data-testid="stRadio"] label {{
    color: var(--ink) !important;
}}

button[kind="secondary"] {{
    border-color:var(--line) !important;
    color:var(--ink-soft) !important;
    background:var(--white) !important;
}}

button[kind="secondary"]:hover {{
    border-color:var(--pine) !important;
    color:var(--pine) !important;
}}

.stButton button {{
    font-family:'IBM Plex Mono', monospace !important;
    font-size:10px !important;
    border-radius:14px !important;
}}

div[data-testid="stExpander"] {{
    border:1px solid var(--line);
    border-radius:8px;
    background:rgba(252,251,246,.45);
}}

footer {{
    visibility:hidden;
}}

@media (max-width: 1100px) {{
    .block-container {{ padding-left:14px; padding-right:14px; }}
    .lcat-header {{ margin-left:-14px; margin-right:-14px; }}
    .breadcrumb {{ margin-left:-14px; margin-right:-14px; }}
}}
</style>
""",
    unsafe_allow_html=True,
)


# =============================================================================
# 2. DATA / NORMALIZATION HELPERS
# =============================================================================
LCAT_ALIASES = {
    "landform & topography": "Landform and topography",
    "landform and topography": "Landform and topography",
    "hydrology": "Hydrology",
    "land cover & agriculture": "Land cover and Agriculture",
    "land cover and agriculture": "Land cover and Agriculture",
    "cultural & historical features": "Cultural and historical features",
    "cultural and historical features": "Cultural and historical features",
    "visual & sensory qualities": "Visual and Sensory qualities",
    "visual and sensory qualities": "Visual and Sensory qualities",
    "wildlife & biodiversity": "Wildlife and Biodiversity richness",
    "wildlife and biodiversity": "Wildlife and Biodiversity richness",
    "wildlife and biodiversity richness": "Wildlife and Biodiversity richness",
    "infrastructure & economy": "Infrastructure and Economic factors",
    "infrastructure and economy": "Infrastructure and Economic factors",
    "infrastructure & economic factors": "Infrastructure and Economic factors",
    "infrastructure and economic factors": "Infrastructure and Economic factors",
    "community & governance": "Community and Governance",
    "community and governance": "Community and Governance",
}


def normalize_text(value: Any) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip()


def normalize_theme(value: Any) -> str:
    if pd.isna(value):
        return "Unknown"

    v = str(value).strip()
    v = re.sub(r"^\s*\d+\s*[\)\.\-:]\s*", "", v)
    v = re.sub(r"\s+", " ", v).strip()
    key = v.lower().replace("–", "-").replace("—", "-")

    if key in LCAT_ALIASES:
        return LCAT_ALIASES[key]

    for alias, canonical in LCAT_ALIASES.items():
        if alias in key or key in alias:
            return canonical

    return v if v in LCAT_ELEMENTS else "Unknown"


def normalize_tier(value: Any) -> str:
    s = normalize_text(value).lower()
    if "tier 1" in s:
        return "Tier 1 — Community Led"
    if "tier 2" in s:
        return "Tier 2 — Minor Support"
    if "tier 3" in s:
        return "Tier 3 — External Support & Convergence"
    return "Unknown"


def normalize_pillar(value: Any) -> str:
    s = normalize_text(value).lower()
    for pillar in PILLARS:
        if pillar.lower() == s:
            return pillar
    return "Unknown"


def find_column(df: pd.DataFrame, candidates: List[str]) -> Optional[str]:
    lowered = {str(c).strip().lower(): c for c in df.columns}
    for candidate in candidates:
        if candidate.lower() in lowered:
            return lowered[candidate.lower()]
    for c in df.columns:
        lc = str(c).strip().lower()
        if any(candidate.lower() in lc for candidate in candidates):
            return c
    return None


# =============================================================================
# 3. REAL GPDP DATA
# =============================================================================
@st.cache_data(show_spinner=False)
def load_gpdp_data() -> pd.DataFrame:
    workbook = "data/GPDP_Action_Plans_Themed_v2_Pillars.xlsx"

    if os.path.exists(workbook):
        frames = []
        try:
            sheets = pd.read_excel(workbook, sheet_name=None)
        except Exception as exc:
            st.error(f"Could not read GPDP workbook: {exc}")
            return pd.DataFrame()

        for sheet_name, frame in sheets.items():
            if frame is None or frame.empty:
                continue

            frame = frame.copy()
            frame.columns = [str(c).strip() for c in frame.columns]

            # If State is absent but the worksheet itself is a state sheet,
            # use the worksheet name only as a geographic fallback.
            if "State" not in frame.columns:
                frame["State"] = sheet_name

            frames.append(frame)

        if frames:
            df = pd.concat(frames, ignore_index=True)

            for col in ["State", "District", "Block", "Panchayat/Village",
                        "Theme", "Priority Action", "Tier", "Pillars", "Pillar"]:
                if col in df.columns:
                    df[col] = df[col].apply(normalize_text)

            if "Theme" in df.columns:
                df["Clean_Theme"] = df["Theme"].apply(normalize_theme)
            else:
                df["Clean_Theme"] = "Unknown"

            if "Tier" in df.columns:
                df["Clean_Tier"] = df["Tier"].apply(normalize_tier)
            else:
                df["Clean_Tier"] = "Unknown"

            pillar_col = "Pillars" if "Pillars" in df.columns else (
                "Pillar" if "Pillar" in df.columns else None
            )
            if pillar_col:
                df["Clean_Pillar"] = df[pillar_col].apply(normalize_pillar)
            else:
                df["Clean_Pillar"] = "Unknown"

            return df

    st.warning(
        "GPDP_Action_Plans_Themed_v2_Pillars.xlsx was not found in data/. "
        "No demo/fallback data are being used."
    )
    return pd.DataFrame()


@st.cache_data(show_spinner=False)
def build_village_summary(df: pd.DataFrame) -> pd.DataFrame:
    required = ["State", "District", "Block", "Panchayat/Village"]
    if df.empty or any(c not in df.columns for c in required):
        return pd.DataFrame()

    rows = []
    grouped = df.groupby(required, dropna=False)

    for (state, district, block, village), group in grouped:
        if not str(village).strip():
            continue

        rows.append(
            {
                "state": state,
                "district": district,
                "block": block,
                "name": village,
                "totalDemand": int(len(group)),
                "tier1": int((group["Clean_Tier"] == "Tier 1 — Community Led").sum()),
                "tier2": int((group["Clean_Tier"] == "Tier 2 — Minor Support").sum()),
                "tier3": int((group["Clean_Tier"] == "Tier 3 — External Support & Convergence").sum()),
                "dominantElement": (
                    group.loc[group["Clean_Theme"] != "Unknown", "Clean_Theme"].mode().iloc[0]
                    if not group.loc[group["Clean_Theme"] != "Unknown", "Clean_Theme"].mode().empty
                    else "Unknown"
                ),
            }
        )

    result = pd.DataFrame(rows)

    # The existing project does not contain a village geometry dataset in this
    # application, so keep the current deterministic visual marker fallback.
    # This does NOT alter the underlying counts/data.
    if not result.empty:
        rng = np.random.default_rng(42)
        district_centers = DISTRICT_CENTERS
        latitudes = []
        longitudes = []
        for _, row in result.iterrows():
            center = district_centers.get(
                row["district"], {"lat": 21.0, "lng": 81.0}
            )
            latitudes.append(center["lat"] + rng.uniform(-0.15, 0.15))
            longitudes.append(center["lng"] + rng.uniform(-0.15, 0.15))
        result["lat"] = latitudes
        result["lng"] = longitudes

    return result


# Same geographic centre information used by the existing application.
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
    "Dhar": {"lat": 22.59, "lng": 75.30, "bounds": [[22.30, 75.00], [22.90, 75.60]]},
}


# =============================================================================
# 4. CLIMATE SIGNALS DATA
# =============================================================================
@st.cache_data(show_spinner=False)
def load_climate_data() -> pd.DataFrame:
    path = "data/climate_vulnerability/climate_vulnerability_results.csv"
    if not os.path.exists(path):
        return pd.DataFrame()

    try:
        df = pd.read_csv(path)
        df.columns = df.columns.str.strip().str.lower()
        return df
    except Exception as exc:
        st.error(f"Error reading climate CSV: {exc}")
        return pd.DataFrame()


# =============================================================================
# 5. VERBATIM DATA
# =============================================================================
@st.cache_data(show_spinner=False)
def load_verbatim_data() -> pd.DataFrame:
    path = "data/lcat/LCAT_Verbatim_Quote_Classification.xlsx"
    if not os.path.exists(path):
        return pd.DataFrame()

    # The verbatim workbook contains introductory rows before the real header.
    # Try the known structure first, then safely fall back to detected headers.
    attempts = [2, 1, 0]
    for header_row in attempts:
        try:
            df = pd.read_excel(path, header=header_row)
            df.columns = [str(c).strip() for c in df.columns]
            required_markers = ["State", "District", "Primary LCAT Element"]
            if all(marker in df.columns for marker in required_markers):
                for c in ["State", "District", "Block / Tehsil", "Panchayat", "Village",
                          "Speaker / Attribution", "Verbatim Quote", "Primary LCAT Element"]:
                    if c in df.columns:
                        df[c] = df[c].apply(normalize_text)
                df["Clean_Theme"] = df["Primary LCAT Element"].apply(normalize_theme)
                return df
        except Exception:
            continue

    st.warning("The LCAT verbatim workbook could not be matched to its expected columns.")
    return pd.DataFrame()


# =============================================================================
# 6. TRAJECTORY DATA
# =============================================================================
@st.cache_data(show_spinner=False)
def load_trajectory_data() -> pd.DataFrame:
    path = "data/District Wise LCAT.xlsx"
    if not os.path.exists(path):
        return pd.DataFrame()

    try:
        df = pd.read_excel(path)
        df.columns = [str(c).strip() for c in df.columns]

        district_col = next(
            (c for c in df.columns if "district" in str(c).lower()), None
        )
        if district_col and district_col != "District":
            df = df.rename(columns={district_col: "District"})

        # Normalize theme column names to the dashboard's exact eight themes.
        rename_map = {}
        for col in df.columns:
            if col in ["District", "State"]:
                continue
            canonical = normalize_theme(col)
            if canonical in LCAT_ELEMENTS:
                rename_map[col] = canonical

        df = df.rename(columns=rename_map)

        return df
    except Exception as exc:
        st.warning(f"Could not read District Wise LCAT.xlsx: {exc}")
        return pd.DataFrame()


# =============================================================================
# 7. MAP HELPERS
# =============================================================================
def get_demand_color(demand: int) -> str:
    if demand <= 35:
        return "#fef08a"
    if demand <= 65:
        return "#f59e0b"
    if demand <= 90:
        return "#ea580c"
    return "#712416"


def get_map_center(selected_district: str, filtered_geo: pd.DataFrame):
    if selected_district in DISTRICT_CENTERS:
        center = DISTRICT_CENTERS[selected_district]
        return center["lat"], center["lng"], 9

    if not filtered_geo.empty:
        return (
            float(filtered_geo["lat"].mean()),
            float(filtered_geo["lng"].mean()),
            8,
        )

    return 21.0, 81.0, 6


def make_map(
    filtered_geo: pd.DataFrame,
    selected_district: str,
    basemap_choice: str,
):
    center_lat, center_lng, zoom_start = get_map_center(
        selected_district, filtered_geo
    )

    tile_dict = {
        "CartoDB Positron": "CartoDB positron",
        "OpenStreetMap": "OpenStreetMap",
        "CartoDB Dark": "CartoDB dark_matter",
    }

    m = folium.Map(
        location=[center_lat, center_lng],
        zoom_start=zoom_start,
        tiles=tile_dict.get(basemap_choice, "CartoDB positron"),
        control_scale=True,
    )

    for _, row in filtered_geo.iterrows():
        radius = max(6, min(20, int(max(1, row["totalDemand"]) * 0.35)))
        fill = get_demand_color(int(row["totalDemand"]))

        tooltip_html = f"""
        <div style="
            background:#FCFBF6;
            color:#20281F;
            border:1px solid #C9C2AC;
            border-top:3px solid #B9863E;
            border-radius:6px;
            padding:10px;
            min-width:185px;
            font-family:'IBM Plex Sans',sans-serif;
        ">
            <div style="font-weight:700;font-size:14px;">{html.escape(str(row['name']))}</div>
            <div style="font-size:11px;color:#4C5646;margin-top:4px;">
                {html.escape(str(row['block']))} · {html.escape(str(row['district']))}
            </div>
            <div style="font-size:12px;font-weight:600;color:#243D2C;margin-top:8px;">
                Total GPDP Demands: {int(row['totalDemand'])}
            </div>
            <div style="font-family:'IBM Plex Mono',monospace;font-size:10px;color:#4C5646;margin-top:6px;">
                T1: {int(row['tier1'])} · T2: {int(row['tier2'])} · T3: {int(row['tier3'])}
            </div>
            <div style="font-size:10px;color:#4C5646;margin-top:5px;">
                Highest Demand Concentration: {html.escape(str(row['dominantElement']))}
            </div>
        </div>
        """

        folium.CircleMarker(
            location=[row["lat"], row["lng"]],
            radius=radius,
            color="#FCFBF6",
            weight=1.5,
            fill=True,
            fill_color=fill,
            fill_opacity=0.84,
            tooltip=folium.Tooltip(tooltip_html, sticky=True),
        ).add_to(m)

    return m


# =============================================================================
# 8. THEME INSIGHTS MODAL
# =============================================================================
@st.dialog("Theme Insights", width="large")
def show_theme_overlay(
    theme: str,
    state: str,
    district: str,
    village: str,
):
    st.markdown(
        f"<h2 style='font-family:Space Grotesk,sans-serif;color:{COLORS['pine']};"
        f"margin:0 0 4px 0;'>{html.escape(theme)}</h2>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<div class='modal-hint'>Priority actions and community evidence for the selected geography.</div>",
        unsafe_allow_html=True,
    )

    df_gpdp = load_gpdp_data()

    if not df_gpdp.empty:
        action_df = df_gpdp.copy()
        if state and state != "Unknown" and "State" in action_df.columns:
            action_df = action_df[action_df["State"] == state]
        if district and district != "All Districts" and "District" in action_df.columns:
            action_df = action_df[action_df["District"] == district]
        if village and village != "All Villages" and "Panchayat/Village" in action_df.columns:
            action_df = action_df[action_df["Panchayat/Village"] == village]
        if "Clean_Theme" in action_df.columns:
            action_df = action_df[action_df["Clean_Theme"] == theme]
    else:
        action_df = pd.DataFrame()

    df_quotes = load_verbatim_data()

    if not df_quotes.empty:
        quote_df = df_quotes.copy()
        if state and state != "Unknown" and "State" in quote_df.columns:
            quote_df = quote_df[quote_df["State"] == state]
        if district and district != "All Districts" and "District" in quote_df.columns:
            quote_df = quote_df[quote_df["District"] == district]
        quote_df = quote_df[quote_df["Clean_Theme"] == theme]

        fallback_used = False
        if village and village != "All Villages" and "Village" in quote_df.columns:
            village_quotes = quote_df[quote_df["Village"] == village]
            if not village_quotes.empty:
                quote_df = village_quotes
            else:
                fallback_used = True
        else:
            fallback_used = False
    else:
        quote_df = pd.DataFrame()
        fallback_used = False

    left, right = st.columns([1.2, 1.0], gap="large")

    with left:
        st.markdown("### Priority Actions")

        if action_df.empty:
            st.info("No specific Priority Actions found for this selection.")
        else:
            st.markdown(
                f"<div class='subtle-note'><b>{len(action_df)}</b> actions</div>",
                unsafe_allow_html=True,
            )

            tier_groups = [
                ("Tier 1 — Community Led", "t1"),
                ("Tier 2 — Minor Support", "t2"),
                ("Tier 3 — External Support & Convergence", "t3"),
            ]

            for tier_name, tier_class in tier_groups:
                group = action_df[action_df["Clean_Tier"] == tier_name]
                if group.empty:
                    continue

                st.markdown(
                    f"<div class='section-label' style='color:{TIER_COLORS[tier_name]};"
                    f"margin-top:16px;'>{tier_name}</div>",
                    unsafe_allow_html=True,
                )

                for idx, (_, row) in enumerate(group.iterrows(), 1):
                    action_text = normalize_text(row.get("Priority Action", ""))
                    pillar = normalize_text(row.get("Clean_Pillar", ""))
                    if not action_text:
                        continue

                    pillar_tag = (
                        f"<span class='tag'>{html.escape(pillar)}</span>"
                        if pillar and pillar != "Unknown" else ""
                    )

                    st.markdown(
                        f"""
                        <div class="action-preview {tier_class}">
                            <div class="text">{html.escape(action_text)}</div>
                            <div class="tag-row">
                                <span class="tag {tier_class}">
                                    {html.escape(tier_name)}
                                </span>
                                <span class="tag">{html.escape(theme)}</span>
                                {pillar_tag}
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

    with right:
        st.markdown("### Community Voices")

        if fallback_used and not quote_df.empty:
            st.caption(
                "Showing district-level evidence because no specific village quote was found."
            )

        if quote_df.empty:
            st.info("No verbatim quotes available for this theme at the selected geography.")
        else:
            for _, row in quote_df.iterrows():
                quote = normalize_text(row.get("Verbatim Quote", ""))
                if not quote:
                    continue
                speaker = normalize_text(
                    row.get("Speaker / Attribution", "Community Member")
                )

                st.markdown(
                    f"""
                    <div class="quote-card">
                        <div class="quote">“{html.escape(quote)}”</div>
                        <div class="speaker">{html.escape(speaker)}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )


# =============================================================================
# 9. SESSION STATE
# =============================================================================
if "dashboard_mode" not in st.session_state:
    st.session_state["dashboard_mode"] = "LCAT & GPDP"

if "theme_filter" not in st.session_state:
    st.session_state["theme_filter"] = "All"

if "show_all_themes" not in st.session_state:
    st.session_state["show_all_themes"] = False

if "tier_filter" not in st.session_state:
    st.session_state["tier_filter"] = "All"

if "pillar_filter" not in st.session_state:
    st.session_state["pillar_filter"] = "All"

if "basemap_choice" not in st.session_state:
    st.session_state["basemap_choice"] = "CartoDB Positron"


# =============================================================================
# 10. LOAD BASE DATA
# =============================================================================
df_gpdp = load_gpdp_data()
df_villages = build_village_summary(df_gpdp)

available_states = (
    sorted(df_villages["state"].dropna().unique().tolist())
    if not df_villages.empty else []
)

# Climate mode data is loaded separately below.


# =============================================================================
# 11. LCAT & GPDP MODE
# =============================================================================
dashboard_mode = st.session_state["dashboard_mode"]

# Compact mode selector. It deliberately sits outside the large dashboard canvas.
mode_choice = st.radio(
    "Dashboard mode",
    ["LCAT & GPDP", "Climate Signals"],
    index=0 if dashboard_mode == "LCAT & GPDP" else 1,
    horizontal=True,
    label_visibility="collapsed",
    key="mode_selector",
)
st.session_state["dashboard_mode"] = mode_choice
dashboard_mode = mode_choice


if dashboard_mode == "LCAT & GPDP":
    # -------------------------------------------------------------------------
    # Header
    # -------------------------------------------------------------------------
    display_state = st.session_state.get("lcat_state", available_states[0] if available_states else "Unknown")
    display_district = st.session_state.get("lcat_dist", "All Districts")
    display_block = st.session_state.get("lcat_block", "All Blocks")
    display_village = st.session_state.get("lcat_vill", "All Villages")

    display_level = (
        "Village" if display_village != "All Villages"
        else "Block" if display_block != "All Blocks"
        else "District" if display_district != "All Districts"
        else "State"
    )

    st.markdown(
        f"""
        <div class="lcat-header">
            <svg class="lcat-brandmark" viewBox="0 0 40 40" fill="none">
                <circle cx="20" cy="20" r="17" stroke="#B9863E" stroke-width="2"/>
                <circle cx="20" cy="20" r="11" stroke="#7E9767" stroke-width="2"/>
                <circle cx="20" cy="20" r="5" stroke="#FCFBF6" stroke-width="2"/>
            </svg>
            <div class="lcat-brand">
                <strong>LCAT</strong>
                <small>LANDSCAPE CHARACTER ASSESSMENT TOOL</small>
            </div>
            <div style="margin-left:auto;display:flex;align-items:center;gap:3px;
                        background:rgba(0,0,0,.2);padding:3px;border-radius:8px;">
                <span style="font-family:'IBM Plex Mono';font-size:10.5px;color:#CBD4C4;padding:7px 9px;">India</span>
                <span style="font-family:'IBM Plex Mono';font-size:10.5px;color:#CBD4C4;padding:7px 9px;">State</span>
                <span style="font-family:'IBM Plex Mono';font-size:10.5px;color:#CBD4C4;padding:7px 9px;">District</span>
                <span style="font-family:'IBM Plex Mono';font-size:10.5px;color:#CBD4C4;padding:7px 9px;">Block</span>
                <span style="font-family:'IBM Plex Mono';font-size:10.5px;color:#CBD4C4;padding:7px 9px;">GP</span>
                <span style="font-family:'IBM Plex Mono';font-size:10.5px;background:#B9863E;color:#241505;
                             font-weight:600;padding:7px 10px;border-radius:6px;">{display_level}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # -------------------------------------------------------------------------
    # Canonical compact geographic selection row.
    # -------------------------------------------------------------------------
    if not available_states:
        selected_state = "Unknown"
        selected_district = "All Districts"
        selected_block = "All Blocks"
        selected_village = "All Villages"
        state_geo = pd.DataFrame()
        district_geo = pd.DataFrame()
        block_geo = pd.DataFrame()
    else:
        state_col, district_col, block_col, village_col = st.columns(
            [1.0, 1.0, 1.0, 1.2], gap="small"
        )

        with state_col:
            st.markdown("<div class='subtle-note'>STATE</div>", unsafe_allow_html=True)
            state_index = (
                available_states.index(display_state)
                if display_state in available_states else 0
            )
            selected_state = st.selectbox(
                "State",
                available_states,
                index=state_index,
                key="lcat_state",
                label_visibility="collapsed",
            )

        state_geo = df_villages[df_villages["state"] == selected_state]

        dist_options = ["All Districts"] + sorted(
            state_geo["district"].dropna().unique().tolist()
        )
        current_dist = display_district if display_district in dist_options else "All Districts"

        with district_col:
            st.markdown("<div class='subtle-note'>DISTRICT</div>", unsafe_allow_html=True)
            selected_district = st.selectbox(
                "District",
                dist_options,
                index=dist_options.index(current_dist),
                key="lcat_dist",
                label_visibility="collapsed",
            )

        district_geo = (
            state_geo[state_geo["district"] == selected_district]
            if selected_district != "All Districts"
            else state_geo
        )

        block_options = ["All Blocks"] + sorted(
            district_geo["block"].dropna().unique().tolist()
        )
        current_block = display_block if display_block in block_options else "All Blocks"

        with block_col:
            st.markdown("<div class='subtle-note'>BLOCK</div>", unsafe_allow_html=True)
            selected_block = st.selectbox(
                "Block",
                block_options,
                index=block_options.index(current_block),
                key="lcat_block",
                label_visibility="collapsed",
            )

        block_geo = (
            district_geo[district_geo["block"] == selected_block]
            if selected_block != "All Blocks"
            else district_geo
        )

        village_options = ["All Villages"] + sorted(
            block_geo["name"].dropna().unique().tolist()
        )
        current_village = (
            display_village if display_village in village_options else "All Villages"
        )

        with village_col:
            st.markdown("<div class='subtle-note'>VILLAGE / GP</div>", unsafe_allow_html=True)
            selected_village = st.selectbox(
                "Gram Panchayat / Village",
                village_options,
                index=village_options.index(current_village),
                key="lcat_vill",
                label_visibility="collapsed",
            )

    # Recompute final geography after all selections.
    if available_states:
        state_geo = df_villages[df_villages["state"] == selected_state]
        district_geo = (
            state_geo[state_geo["district"] == selected_district]
            if selected_district != "All Districts"
            else state_geo
        )
        block_geo = (
            district_geo[district_geo["block"] == selected_block]
            if selected_block != "All Blocks"
            else district_geo
        )

    # Breadcrumb is the primary geographic display.
    breadcrumb = ["India"]
    if selected_state != "Unknown":
        breadcrumb.append(selected_state)
    if selected_district != "All Districts":
        breadcrumb.append(f"{selected_district} District")
    if selected_block != "All Blocks":
        breadcrumb.append(f"{selected_block} Block")
    if selected_village != "All Villages":
        breadcrumb.append(selected_village)

    breadcrumb_html = ""
    for idx, part in enumerate(breadcrumb):
        if idx:
            breadcrumb_html += '<span class="sep">›</span>'
        cls = "current" if idx == len(breadcrumb) - 1 else ""
        breadcrumb_html += f'<span class="{cls}">{html.escape(part)}</span>'

    st.markdown(
        f'<div class="breadcrumb">{breadcrumb_html}</div>',
        unsafe_allow_html=True,
    )

    filtered_geo = df_villages.copy()
    if selected_state != "Unknown":
        filtered_geo = filtered_geo[filtered_geo["state"] == selected_state]
    if selected_district != "All Districts":
        filtered_geo = filtered_geo[filtered_geo["district"] == selected_district]
    if selected_block != "All Blocks":
        filtered_geo = filtered_geo[filtered_geo["block"] == selected_block]
    if selected_village != "All Villages":
        filtered_geo = filtered_geo[filtered_geo["name"] == selected_village]

    # -------------------------------------------------------------------------
    # THREE-COLUMN CORE WORKSPACE
    # -------------------------------------------------------------------------
    # Modifying layout ratios to strictly make Left/Right thinner and Center wider
    # Original: [0.84, 1.85, 1.02] -> New: [1.7, 6.1, 2.2]
    # -------------------------------------------------------------------------
    left_col, center_col, right_col = st.columns([1.7, 6.1, 2.2], gap="medium")

    # -------------------------------------------------------------------------
    # LEFT PANEL: layers + filters
    # -------------------------------------------------------------------------
    with left_col:
        st.markdown("<div class='section-label' style='margin-top:0;'>Map layers</div>", unsafe_allow_html=True)

        # Placeholder controls only. They do not invent or draw unsupported data.
        for label in ["LULC (Placeholder)", "NDVI (Placeholder)", "Soil (Placeholder)",
                      "DEM / Slope (Placeholder)", "Rivers (Placeholder)", "LCAT choropleth"]:
            st.toggle(label, value=(label == "LCAT choropleth"), key=f"layer_{label}")

        st.markdown("<div class='section-label'>Filter priority actions</div>", unsafe_allow_html=True)

        st.markdown(
            "<div class='subtle-note' style='margin-bottom:6px;'>LANDSCAPE THEMES</div>",
            unsafe_allow_html=True,
        )

        visible_themes = LCAT_ELEMENTS[:3] if not st.session_state["show_all_themes"] else LCAT_ELEMENTS

        theme_cols = st.columns(2)
        theme_choices = ["All"] + visible_themes

        for idx, option in enumerate(theme_choices):
            with theme_cols[idx % 2]:
                active = st.session_state["theme_filter"] == option
                if st.button(
                    option,
                    key=f"theme_chip_{idx}_{option}",
                    width="stretch",
                    type="primary" if active else "secondary",
                ):
                    st.session_state["theme_filter"] = option
                    st.rerun()

        if not st.session_state["show_all_themes"]:
            if st.button("+5 more", key="expand_themes", width="stretch"):
                st.session_state["show_all_themes"] = True
                st.rerun()
        else:
            if st.button("Show fewer", key="collapse_themes", width="stretch"):
                st.session_state["show_all_themes"] = False
                if st.session_state["theme_filter"] not in ["All"] + LCAT_ELEMENTS[:3]:
                    st.session_state["theme_filter"] = "All"
                st.rerun()

        st.markdown(
            "<div class='subtle-note' style='margin:10px 0 6px;'>TIER</div>",
            unsafe_allow_html=True,
        )
        tier_choices = ["All"] + list(TIER_COLORS.keys())
        tier_labels = {
            "All": "All",
            "Tier 1 — Community Led": "Tier 1",
            "Tier 2 — Minor Support": "Tier 2",
            "Tier 3 — External Support & Convergence": "Tier 3",
        }
        tc = st.columns(2)
        for idx, option in enumerate(tier_choices):
            with tc[idx % 2]:
                active = st.session_state["tier_filter"] == option
                if st.button(
                    tier_labels[option],
                    key=f"tier_chip_{idx}",
                    width="stretch",
                    type="primary" if active else "secondary",
                ):
                    st.session_state["tier_filter"] = option
                    st.rerun()

        st.markdown(
            "<div class='subtle-note' style='margin:10px 0 6px;'>PILLAR</div>",
            unsafe_allow_html=True,
        )
        pillar_choices = ["All"] + PILLARS
        pc = st.columns(2)
        for idx, option in enumerate(pillar_choices):
            with pc[idx % 2]:
                active = st.session_state["pillar_filter"] == option
                if st.button(
                    option,
                    key=f"pillar_chip_{idx}",
                    width="stretch",
                    type="primary" if active else "secondary",
                ):
                    st.session_state["pillar_filter"] = option
                    st.rerun()

        st.markdown("<div class='section-label'>Basemap</div>", unsafe_allow_html=True)
        st.session_state["basemap_choice"] = st.selectbox(
            "Basemap",
            ["CartoDB Positron", "OpenStreetMap", "CartoDB Dark"],
            index=["CartoDB Positron", "OpenStreetMap", "CartoDB Dark"].index(
                st.session_state["basemap_choice"]
            ),
            label_visibility="collapsed",
        )

    # -------------------------------------------------------------------------
    # CENTRAL MAP + BLOCK SUMMARY
    # -------------------------------------------------------------------------
    with center_col:
        map_title = (
            f"{selected_block} — Geospatial View"
            if selected_block != "All Blocks"
            else f"{selected_district if selected_district != 'All Districts' else selected_state} — Geospatial View"
        )

        st.markdown(
            f"""
            <div class="card">
                <div class="map-title">
                    <h2>{html.escape(map_title)}</h2>
                    <span>LCAT village demand view · current selection</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        map_obj = make_map(
            filtered_geo,
            selected_district,
            st.session_state["basemap_choice"],
        )
        st_folium(
            map_obj,
            use_container_width=True,
            height=500,
            returned_objects=[],
        )

        # Filter actual action records according to action filter controls.
        filtered_actions = df_gpdp.copy()
        if not filtered_actions.empty:
            if selected_state != "Unknown" and "State" in filtered_actions.columns:
                filtered_actions = filtered_actions[filtered_actions["State"] == selected_state]
            if selected_district != "All Districts" and "District" in filtered_actions.columns:
                filtered_actions = filtered_actions[filtered_actions["District"] == selected_district]
            if selected_block != "All Blocks" and "Block" in filtered_actions.columns:
                filtered_actions = filtered_actions[filtered_actions["Block"] == selected_block]
            if selected_village != "All Villages" and "Panchayat/Village" in filtered_actions.columns:
                filtered_actions = filtered_actions[
                    filtered_actions["Panchayat/Village"] == selected_village
                ]
            if st.session_state["theme_filter"] != "All":
                filtered_actions = filtered_actions[
                    filtered_actions["Clean_Theme"] == st.session_state["theme_filter"]
                ]
            if st.session_state["tier_filter"] != "All":
                filtered_actions = filtered_actions[
                    filtered_actions["Clean_Tier"] == st.session_state["tier_filter"]
                ]
            if st.session_state["pillar_filter"] != "All":
                filtered_actions = filtered_actions[
                    filtered_actions["Clean_Pillar"] == st.session_state["pillar_filter"]
                ]

        summary_scope = (
            selected_block if selected_block != "All Blocks"
            else selected_district if selected_district != "All Districts"
            else selected_state
        )

        scope_villages = filtered_geo["name"].nunique() if not filtered_geo.empty else 0
        total_actions = len(filtered_actions)

        t1_count = int((filtered_actions["Clean_Tier"] == "Tier 1 — Community Led").sum()) if not filtered_actions.empty else 0
        t2_count = int((filtered_actions["Clean_Tier"] == "Tier 2 — Minor Support").sum()) if not filtered_actions.empty else 0
        t3_count = int((filtered_actions["Clean_Tier"] == "Tier 3 — External Support & Convergence").sum()) if not filtered_actions.empty else 0
        tier_total = t1_count + t2_count + t3_count

        if tier_total > 0:
            widths = [
                f"{100 * t1_count / tier_total:.3f}%",
                f"{100 * t2_count / tier_total:.3f}%",
                f"{100 * t3_count / tier_total:.3f}%",
            ]
        else:
            widths = ["0%", "0%", "0%"]

        st.markdown(
            f"""
            <div class="card" style="margin-top:14px;">
                <div class="summary-title">
                    <h3>{html.escape(str(summary_scope))} Summary</h3>
                    <span>{scope_villages} villages · {total_actions} priority actions</span>
                </div>
                <div class="tier-bar">
                    <div style="width:{widths[0]};background:{TIER_COLORS['Tier 1 — Community Led']};"></div>
                    <div style="width:{widths[1]};background:{TIER_COLORS['Tier 2 — Minor Support']};"></div>
                    <div style="width:{widths[2]};background:{TIER_COLORS['Tier 3 — External Support & Convergence']};"></div>
                </div>
                <div class="tier-legend">
                    <span><i class="legend-dot" style="background:{TIER_COLORS['Tier 1 — Community Led']};"></i>Tier 1</span>
                    <span><i class="legend-dot" style="background:{TIER_COLORS['Tier 2 — Minor Support']};"></i>Tier 2</span>
                    <span><i class="legend-dot" style="background:{TIER_COLORS['Tier 3 — External Support & Convergence']};"></i>Tier 3</span>
                </div>
                <div class="tier-counts">
                    <div><span class="num">{t1_count}</span><span class="label">Tier 1 actions</span></div>
                    <div><span class="num">{t2_count}</span><span class="label">Tier 2 actions</span></div>
                    <div><span class="num">{t3_count}</span><span class="label">Tier 3 actions</span></div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # -------------------------------------------------------------------------
    # RIGHT PROFILE
    # -------------------------------------------------------------------------
    with right_col:
        selected_profile = None
        if selected_village != "All Villages" and not filtered_geo.empty:
            selected_profile = filtered_geo.iloc[0]
            profile_name = str(selected_profile["name"])
            profile_loc = f"{selected_profile['block']} · {selected_profile['district']} · {selected_profile['state']}"
        elif selected_block != "All Blocks":
            profile_name = f"{selected_block} Profile"
            profile_loc = f"{selected_district} · {selected_state}"
        elif selected_district != "All Districts":
            profile_name = f"{selected_district} Profile"
            profile_loc = str(selected_state)
        else:
            profile_name = f"{selected_state} Profile"
            profile_loc = "Current State selection"

        st.markdown(
            f"""
            <div class="profile-header">
                <h2 class="profile-title">{html.escape(profile_name)}</h2>
                <div class="profile-location">{html.escape(profile_loc)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Condition-score placeholder: keep names/logic ready, values are NaN.
        st.markdown(
            """
            <div class="score-card">
                <div class="score-gauge"><span>NaN</span></div>
                <div class="score-copy">
                    <strong>Overall LCAT score</strong>
                    <small>Score logic pending</small>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("<div class='section-label'>Sub-scores (pending)</div>", unsafe_allow_html=True)

        for label, color in [
            ("Physical condition", COLORS["moss"]),
            ("Vegetation condition", COLORS["sage"]),
            ("Hydrological condition", COLORS["slate"]),
            ("Anthropogenic pressure (inv.)", COLORS["brick"]),
        ]:
            st.markdown(
                f"""
                <div class="subscore">
                    <div class="subscore-head"><span>{label}</span><b>NaN</b></div>
                    <div class="subscore-track"><div style="width:0%;height:100%;background:{color};"></div></div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("<div class='section-label'>Land characteristics</div>", unsafe_allow_html=True)
        st.markdown(
            """
            <div class="stat-grid">
                <div><div class="value">NaN</div><div class="label">Elevation</div></div>
                <div><div class="value">NaN</div><div class="label">Mean slope</div></div>
                <div><div class="value">NaN</div><div class="label">Forest cover</div></div>
                <div><div class="value">NaN</div><div class="label">Agriculture</div></div>
                <div><div class="value">NaN</div><div class="label">Built-up</div></div>
                <div><div class="value">NaN</div><div class="label">Dist. to river</div></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("<div class='section-label'>Priority actions preview</div>", unsafe_allow_html=True)

        if selected_district == "All Districts" or st.session_state["theme_filter"] == "All":
            st.markdown(
                "<div class='subtle-note'>Select at least a district and an LCAT theme to view priority actions and community voices.</div>",
                unsafe_allow_html=True,
            )
        else:
            preview_df = df_gpdp.copy()
            if not preview_df.empty:
                if "State" in preview_df.columns:
                    preview_df = preview_df[preview_df["State"] == selected_state]
                if "District" in preview_df.columns:
                    preview_df = preview_df[preview_df["District"] == selected_district]
                if selected_block != "All Blocks" and "Block" in preview_df.columns:
                    preview_df = preview_df[preview_df["Block"] == selected_block]
                if selected_village != "All Villages" and "Panchayat/Village" in preview_df.columns:
                    preview_df = preview_df[preview_df["Panchayat/Village"] == selected_village]
                preview_df = preview_df[
                    preview_df["Clean_Theme"] == st.session_state["theme_filter"]
                ]
                if st.session_state["tier_filter"] != "All":
                    preview_df = preview_df[preview_df["Clean_Tier"] == st.session_state["tier_filter"]]
                if st.session_state["pillar_filter"] != "All":
                    preview_df = preview_df[preview_df["Clean_Pillar"] == st.session_state["pillar_filter"]]

            if preview_df.empty:
                st.markdown(
                    "<div class='subtle-note'>No actions match the current filters.</div>",
                    unsafe_allow_html=True,
                )
            else:
                for _, row in preview_df.head(4).iterrows():
                    tier = row["Clean_Tier"]
                    tclass = {
                        "Tier 1 — Community Led": "t1",
                        "Tier 2 — Minor Support": "t2",
                        "Tier 3 — External Support & Convergence": "t3",
                    }.get(tier, "")

                    action_text = normalize_text(row.get("Priority Action", ""))
                    pillar = normalize_text(row.get("Clean_Pillar", ""))
                    st.markdown(
                        f"""
                        <div class="action-preview {tclass}">
                            <div class="text">{html.escape(action_text)}</div>
                            <div class="tag-row">
                                <span class="tag {tclass}">{html.escape(tier)}</span>
                                <span class="tag">{html.escape(st.session_state['theme_filter'])}</span>
                                <span class="tag">{html.escape(pillar)}</span>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                if st.button("See more", key="see_more_theme", width="stretch"):
                    show_theme_overlay(
                        st.session_state["theme_filter"],
                        selected_state,
                        selected_district,
                        selected_village,
                    )

        st.markdown("<div class='section-label'>Recommended focus</div>", unsafe_allow_html=True)
        st.markdown(
            "<span class='focus-pill muted'>NaN</span>"
            "<span class='focus-pill muted'>Recommendations require scores</span>",
            unsafe_allow_html=True,
        )

    # -----------------------------------------------------------------------------
    # DISTRICT TRAJECTORY
    # -----------------------------------------------------------------------------
    st.markdown(
        """
        <div class="analytical-heading" style="margin-top:24px;margin-bottom:6px;">
            <h2>District LCAT Landscape Trajectory</h2>
            <p>Improving, declining, mixed or stable by LCAT theme</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    trajectory_df = load_trajectory_data()

    if selected_district == "All Districts":
        st.info("Select a district to view the trajectory status of all 8 LCAT themes.")

    elif trajectory_df.empty or "District" not in trajectory_df.columns:
        st.info("No District Wise LCAT trajectory data is available.")

    else:
        one = trajectory_df[
            trajectory_df["District"].astype(str).str.strip() == str(selected_district).strip()
        ]

        if one.empty:
            st.info(f"No trajectory data available for {selected_district}.")

        else:
            row = one.iloc[0]

            # Visual status system matched specifically to requested aesthetic
            trajectory_style = {
                "Declining": {
                    "arrow": "↓",
                    "color": "#8C4536",
                    "bg": "#F2E1DC",
                },
                "Improving": {
                    "arrow": "↑",
                    "color": "#3E6B47",
                    "bg": "#E2EBDD",
                },
                "Stable": {
                    "arrow": "→",
                    "color": "#3E6B78",
                    "bg": "#EAE6D9",
                },
                "Mixed": {
                    "arrow": "↕",
                    "color": "#B9863E",
                    "bg": "#F8F3E6",
                },
                "Unknown": {
                    "arrow": "—",
                    "color": "#8A9086",
                    "bg": "#DFDACB",
                },
            }

            # Render 8 themes strictly mapped into 2 horizontal rows (4 columns each)
            for start in [0, 4]:
                theme_cols = st.columns(4)

                for col, theme in zip(theme_cols, LCAT_ELEMENTS[start:start + 4]):
                    with col:
                        status_raw = normalize_text(row.get(theme, "Unknown"))
                        
                        status_key = "Unknown"
                        for k in trajectory_style.keys():
                            if k.lower() in status_raw.lower():
                                status_key = k
                                break
                        
                        style = trajectory_style[status_key]
                        display_status = status_key if status_key != "Unknown" else "Unknown"

                        st.markdown(
                            f"""
                                <div style="
                                    background:#F4F1E7;
                                    border:1px solid #C9C2AC;
                                    border-radius:8px;
                                    padding:12px 10px;
                                    text-align:center;
                                    display:flex;
                                    flex-direction:column;
                                    align-items:center;
                                    justify-content:center;
                                    min-height:85px;
                                    margin-bottom:12px;
                                ">
                                    <div style="
                                        font-family:'IBM Plex Mono',monospace;
                                        font-size:10.5px;
                                        line-height:1.3;
                                        color:#4C5646;
                                        margin-bottom:8px;
                                        height:28px;
                                        display:flex;
                                        align-items:center;
                                        justify-content:center;
                                    ">
                                        {html.escape(theme)}
                                    </div>
                                
                                    <div style="
                                        background:{style['bg']};
                                        color:{style['color']};
                                        border-radius:14px;
                                        padding:4px 10px;
                                        font-family:'IBM Plex Mono',monospace;
                                        font-size:11px;
                                        font-weight:600;
                                        display:inline-flex;
                                        align-items:center;
                                        gap:4px;
                                    ">
                                        <span style="font-weight:700; font-size:13px;">{style['arrow']}</span>
                                        {display_status}
                                    </div>
                                </div>
                                """,
                            unsafe_allow_html=True,
                        )
            # Subtle spacer below trajectory section
            st.markdown("<div style='margin-bottom: 24px;'></div>", unsafe_allow_html=True)


# =============================================================================
# 12. CLIMATE SIGNALS MODE
# =============================================================================
else:
    climate_df = load_climate_data()

    st.markdown(
        f"""
        <div class="lcat-header">
            <svg class="lcat-brandmark" viewBox="0 0 40 40" fill="none">
                <circle cx="20" cy="20" r="17" stroke="#B9863E" stroke-width="2"/>
                <circle cx="20" cy="20" r="11" stroke="#7E9767" stroke-width="2"/>
                <circle cx="20" cy="20" r="5" stroke="#FCFBF6" stroke-width="2"/>
            </svg>
            <div class="lcat-brand">
                <strong>LCAT</strong>
                <small>LANDSCAPE CHARACTER ASSESSMENT TOOL</small>
            </div>
            <div style="margin-left:auto;font-family:'IBM Plex Mono';font-size:11px;color:#CBD4C4;">
                CLIMATE SIGNALS
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if climate_df.empty:
        st.warning("Climate Signals dataset was not found in data/climate_vulnerability/.")
    else:
        climate_states = sorted(climate_df["state"].dropna().unique().tolist())
        c1, c2 = st.columns([1.0, 1.2])

        with c1:
            climate_state = st.selectbox("State", climate_states, key="clim_state_new")

        state_rows = climate_df[climate_df["state"] == climate_state]
        climate_districts = ["All Districts"] + sorted(
            state_rows["district"].dropna().unique().tolist()
        )

        with c2:
            climate_district = st.selectbox(
                "District",
                climate_districts,
                key="clim_dist_new",
            )

        st.markdown(
            f"""
            <div class="breadcrumb" style="margin:12px 0 0 0;">
                <span>India</span><span class="sep">›</span>
                <span>{html.escape(climate_state)}</span><span class="sep">›</span>
                <span class="current">{html.escape(climate_district)}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        ndmi_colors = {
            "Severe Canopy Desiccation": "#8C4536",
            "Moisture Loss": "#B9863E",
            "Stable": "#DFDACB",
            "Moisture Gain": "#3E6B78",
            "Little or No Change": "#DFDACB",
        }
        lst_colors = {
            "Severe Warming": "#8C4536",
            "Moderate Warming": "#B9863E",
            "Stable": "#DFDACB",
            "Cooling Trend": "#3E6B78",
            "Little or No Change": "#DFDACB",
        }

        if climate_district == "All Districts":
            st.markdown(
                "<div class='analytical-heading'><h2>Climate Signals Overview</h2>"
                "<p>District-level distribution of canopy moisture and thermal stress status</p></div>",
                unsafe_allow_html=True,
            )

            ndmi_counts = (
                state_rows["canopy_moisture_status"]
                .value_counts()
                .reset_index()
            )
            ndmi_counts.columns = ["Status", "Districts"]

            lst_counts = (
                state_rows["summer_lst_status"]
                .value_counts()
                .reset_index()
            )
            lst_counts.columns = ["Status", "Districts"]

            a, b = st.columns(2)

            with a:
                st.markdown("<div class='card'><h3 style='font-size:15px;'>NDMI Status Distribution</h3></div>", unsafe_allow_html=True)
                fig = go.Figure(
                    go.Pie(
                        labels=ndmi_counts["Status"],
                        values=ndmi_counts["Districts"],
                        hole=0.62,
                        marker=dict(
                            colors=[ndmi_colors.get(x, COLORS["paper_deep"]) for x in ndmi_counts["Status"]],
                            line=dict(color=COLORS["white"], width=2),
                        ),
                    )
                )
                fig.update_layout(
                    height=330,
                    margin=dict(l=0, r=0, t=5, b=10),
                    paper_bgcolor="rgba(0,0,0,0)",
                    showlegend=True,
                    legend=dict(orientation="h", y=-0.15),
                )
                st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})

            with b:
                st.markdown("<div class='card'><h3 style='font-size:15px;'>LST Status Distribution</h3></div>", unsafe_allow_html=True)
                fig = go.Figure(
                    go.Pie(
                        labels=lst_counts["Status"],
                        values=lst_counts["Districts"],
                        hole=0.62,
                        marker=dict(
                            colors=[lst_colors.get(x, COLORS["paper_deep"]) for x in lst_counts["Status"]],
                            line=dict(color=COLORS["white"], width=2),
                        ),
                    )
                )
                fig.update_layout(
                    height=330,
                    margin=dict(l=0, r=0, t=5, b=10),
                    paper_bgcolor="rgba(0,0,0,0)",
                    showlegend=True,
                    legend=dict(orientation="h", y=-0.15),
                )
                st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})

        else:
            row_df = state_rows[state_rows["district"] == climate_district]

            if row_df.empty:
                st.warning("Data not found for the selected district.")
            else:
                row = row_df.iloc[0]

                k1, k2, k3, k4 = st.columns(4)
                cards = [
                    (
                        "NDMI STATUS",
                        row.get("canopy_moisture_status", "N/A"),
                        "Canopy Moisture",
                    ),
                    (
                        "NDMI CHANGE",
                        row.get("canopy_moisture_pct_change", "N/A"),
                        "Percentage Change",
                    ),
                    (
                        "LST STATUS",
                        row.get("summer_lst_status", "N/A"),
                        "Thermal Stress",
                    ),
                    (
                        "LST CHANGE",
                        f"{row.get('summer_lst_change_c', 'N/A')} °C",
                        "Temperature Change",
                    ),
                ]

                for col, (label, value, desc) in zip([k1, k2, k3, k4], cards):
                    with col:
                        st.markdown(
                            f"""
                            <div class="card">
                                <div class="subtle-note">{label}</div>
                                <div style="font-family:'IBM Plex Mono';font-size:20px;font-weight:600;color:{COLORS['ink']};margin:4px 0;">
                                    {html.escape(str(value))}
                                </div>
                                <div style="font-size:10px;color:{COLORS['ink_soft']};">{desc}</div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

                dist_clean = re.sub(r"[^a-z0-9]+", "_", str(climate_district).lower()).strip("_")

                st.markdown("<div class='section-label'>Canopy Moisture — NDMI</div>", unsafe_allow_html=True)
                ndmi_cols = st.columns(3)
                ndmi_files = [
                    ("2001–2010 Baseline", f"data/climate_vulnerability/imagery/{dist_clean}_ndmi_baseline.png"),
                    ("2015–2024 Recent", f"data/climate_vulnerability/imagery/{dist_clean}_ndmi_recent.png"),
                    ("Change", f"data/climate_vulnerability/imagery/{dist_clean}_ndmi_change.png"),
                ]
                for col, (label, path) in zip(ndmi_cols, ndmi_files):
                    with col:
                        st.markdown(f"**{label}**")
                        if os.path.exists(path):
                            st.image(path, width="stretch")
                        else:
                            st.info(f"Image not found: {os.path.basename(path)}")

                st.markdown(
                    f"""
                    <div class="card" style="margin-top:10px;">
                        <b>Baseline:</b> {html.escape(str(row.get('canopy_moisture_baseline', 'N/A')))}
                        &nbsp;|&nbsp; <b>Recent:</b> {html.escape(str(row.get('canopy_moisture_recent', 'N/A')))}
                        &nbsp;|&nbsp; <b>Absolute Change:</b> {html.escape(str(row.get('canopy_moisture_change', 'N/A')))}
                        &nbsp;|&nbsp; <b>Status:</b> {html.escape(str(row.get('canopy_moisture_status', 'N/A')))}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                st.markdown("<div class='section-label'>Thermal Stress — LST</div>", unsafe_allow_html=True)
                lst_cols = st.columns(3)
                lst_files = [
                    ("2001–2010 Baseline", f"data/climate_vulnerability/imagery/{dist_clean}_lst_baseline.png"),
                    ("2015–2024 Recent", f"data/climate_vulnerability/imagery/{dist_clean}_lst_recent.png"),
                    ("Change", f"data/climate_vulnerability/imagery/{dist_clean}_lst_change.png"),
                ]
                for col, (label, path) in zip(lst_cols, lst_files):
                    with col:
                        st.markdown(f"**{label}**")
                        if os.path.exists(path):
                            st.image(path, width="stretch")
                        else:
                            st.info(f"Image not found: {os.path.basename(path)}")

                st.markdown(
                    f"""
                    <div class="card" style="margin-top:10px;">
                        <b>Baseline:</b> {html.escape(str(row.get('summer_lst_baseline_c', 'N/A')))} °C
                        &nbsp;|&nbsp; <b>Recent:</b> {html.escape(str(row.get('summer_lst_recent_c', 'N/A')))} °C
                        &nbsp;|&nbsp; <b>Change:</b> {html.escape(str(row.get('summer_lst_change_c', 'N/A')))} °C
                        &nbsp;|&nbsp; <b>Status:</b> {html.escape(str(row.get('summer_lst_status', 'N/A')))}
                        <br><br>
                        <b>Extreme Heat Days:</b>
                        Baseline {html.escape(str(row.get('extreme_heat_days_baseline', 'N/A')))}
                        · Recent {html.escape(str(row.get('extreme_heat_days_recent', 'N/A')))}
                        · Change {html.escape(str(row.get('extreme_heat_days_change', 'N/A')))}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                with st.expander("Methodology & Data Sources"):
                    st.markdown(
                        """
**Canopy Moisture (NDMI)**
- Source: MODIS MOD09A1
- Resolution: 500 m
- Season: October–November
- Baseline: 2001–2010
- Recent: 2015–2024

**Thermal Stress (LST)**
- Source: MODIS MOD11A1
- Resolution: 1 km
- Season: May–June
- Baseline: 2001–2010
- Recent: 2015–2024
"""
                    )
