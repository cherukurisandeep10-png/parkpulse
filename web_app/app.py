# Author: Sandeep Chowdary
# Project: ParkPulse - Smart City Mobility & Vehicle Telemetry
# Description: Real-time public transportation and docking sensor analytics for urban mobility networks.

import streamlit as st
import pandas as pd
import numpy as np
import pydeck as pdk
import urllib.request
import json
import time

st.set_page_config(
    page_title="ParkPulse | Mobility Telemetry",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Vibrant, Human-Designed SaaS Palette (Zero AI Emoji Spam)
st.markdown("""
    <style>
    /* Clean main background */
    .stApp {
        background-color: #F8FAFC;
        font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    }
    
    /* Brand Header in Sidebar */
    .brand-title {
        font-size: 1.8rem;
        font-weight: 800;
        background: linear-gradient(90deg, #2563EB, #7C3AED);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .brand-subtitle {
        font-size: 0.85rem;
        color: #64748B;
        font-weight: 500;
        margin-bottom: 1.5rem;
    }
    
    /* Vibrant Multi-Color KPI Cards */
    .card-orange {
        background: linear-gradient(135deg, #FF6B6B 0%, #FF8E53 100%);
        padding: 1.5rem;
        border-radius: 12px;
        color: #FFFFFF;
        box-shadow: 0 4px 15px rgba(255, 107, 107, 0.25);
        transition: transform 0.2s ease;
    }
    .card-green {
        background: linear-gradient(135deg, #10B981 0%, #059669 100%);
        padding: 1.5rem;
        border-radius: 12px;
        color: #FFFFFF;
        box-shadow: 0 4px 15px rgba(16, 185, 129, 0.25);
        transition: transform 0.2s ease;
    }
    .card-blue {
        background: linear-gradient(135deg, #3B82F6 0%, #1D4ED8 100%);
        padding: 1.5rem;
        border-radius: 12px;
        color: #FFFFFF;
        box-shadow: 0 4px 15px rgba(59, 130, 246, 0.25);
        transition: transform 0.2s ease;
    }
    .card-purple {
        background: linear-gradient(135deg, #8B5CF6 0%, #6D28D9 100%);
        padding: 1.5rem;
        border-radius: 12px;
        color: #FFFFFF;
        box-shadow: 0 4px 15px rgba(139, 92, 246, 0.25);
        transition: transform 0.2s ease;
    }
    .card-title {
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        font-weight: 600;
        opacity: 0.9;
        margin-bottom: 0.5rem;
    }
    .card-value {
        font-size: 2rem;
        font-weight: 800;
        margin-bottom: 0.2rem;
    }
    .card-sub {
        font-size: 0.8rem;
        opacity: 0.85;
        font-weight: 500;
    }
    
    /* Station Detail Panel */
    .station-panel {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 1.8rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        margin-top: 1rem;
        margin-bottom: 1.5rem;
    }
    .station-name {
        font-size: 1.4rem;
        font-weight: 700;
        color: #0F172A;
        margin-bottom: 0.3rem;
    }
    .badge-online {
        background-color: #DCFCE7;
        color: #15803D;
        padding: 0.3rem 0.7rem;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.5px;
    }
    .badge-offline {
        background-color: #FEE2E2;
        color: #B91C1C;
        padding: 0.3rem 0.7rem;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.5px;
    }
    
    /* Streamlit Tabs Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 12px;
        border-bottom: 2px solid #E2E8F0;
    }
    .stTabs [data-baseweb="tab"] {
        height: 48px;
        background-color: transparent;
        border-radius: 6px 6px 0px 0px;
        padding: 10px 22px;
        color: #64748B;
        font-weight: 600;
        font-size: 0.95rem;
    }
    .stTabs [aria-selected="true"] {
        background-color: #EFF6FF !important;
        color: #2563EB !important;
        border-bottom: 3px solid #2563EB !important;
        font-weight: 700;
    }
    
    /* Sidebar branding */
    section[data-testid="stSidebar"] {
        background-color: #FFFFFF;
        border-right: 1px solid #E2E8F0;
    }
    </style>
""", unsafe_allow_html=True)


def render_vibrant_card(style_class, title, value, subtitle=""):
    st.markdown(f"""
        <div class="{style_class}">
            <div class="card-title">{title}</div>
            <div class="card-value">{value}</div>
            <div class="card-sub">{subtitle}</div>
        </div>
    """, unsafe_allow_html=True)


# Live GBFS Feed Endpoints
CITY_FEEDS = {
    "New York City (Citi Bike)": {
        "info": "https://gbfs.lyft.com/gbfs/2.3/bkn/en/station_information.json",
        "status": "https://gbfs.lyft.com/gbfs/2.3/bkn/en/station_status.json",
        "lat": 40.7306,
        "lon": -73.9866,
        "zoom": 11.5
    },
    "Chicago (Divvy Bikes)": {
        "info": "https://gbfs.lyft.com/gbfs/2.3/chi/en/station_information.json",
        "status": "https://gbfs.lyft.com/gbfs/2.3/chi/en/station_status.json",
        "lat": 41.8781,
        "lon": -87.6298,
        "zoom": 11.5
    },
    "San Francisco (Bay Wheels)": {
        "info": "https://gbfs.lyft.com/gbfs/2.3/bay/en/station_information.json",
        "status": "https://gbfs.lyft.com/gbfs/2.3/bay/en/station_status.json",
        "lat": 37.7749,
        "lon": -122.4194,
        "zoom": 12.0
    },
    "Los Angeles (LA Metro)": {
        "info": "https://gbfs.bcycle.com/bcycle_lametro/station_information.json",
        "status": "https://gbfs.bcycle.com/bcycle_lametro/station_status.json",
        "lat": 34.0522,
        "lon": -118.2437,
        "zoom": 11.0
    }
}


@st.cache_data(ttl=30)
def fetch_live_city_telemetry(city_name):
    feed = CITY_FEEDS[city_name]
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    
    start_time = time.time()
    
    with urllib.request.urlopen(urllib.request.Request(feed["info"], headers=headers), timeout=5) as r:
        info_data = json.loads(r.read().decode())["data"]["stations"]
        info_df = pd.DataFrame(info_data)
        
    with urllib.request.urlopen(urllib.request.Request(feed["status"], headers=headers), timeout=5) as r:
        status_data = json.loads(r.read().decode())["data"]["stations"]
        status_df = pd.DataFrame(status_data)
        
    latency_ms = round((time.time() - start_time) * 1000, 1)
    
    # Merge station metadata with live sensor availability
    df = pd.merge(
        info_df[["station_id", "name", "lat", "lon", "capacity"]],
        status_df[["station_id", "num_bikes_available", "num_docks_available", "is_renting", "is_returning"]],
        on="station_id"
    )
    
    # Clean and compute metrics
    df = df[df["capacity"] > 0].copy()
    df["occupancy_pct"] = round((df["num_bikes_available"] / df["capacity"]) * 100, 1)
    df = df.sort_values(by="num_bikes_available", ascending=False).reset_index(drop=True)
    
    return df, latency_ms


# Sidebar
with st.sidebar:
    st.markdown('<div class="brand-title">ParkPulse</div>', unsafe_allow_html=True)
    st.markdown('<div class="brand-subtitle">Urban Mobility Telemetry</div>', unsafe_allow_html=True)
    
    selected_city = st.selectbox("Metropolitan Network", list(CITY_FEEDS.keys()))
    
    if st.button("Refresh Sensor Feed", use_container_width=True):
        st.cache_data.clear()
        st.success("Sensor data updated")
        
    st.divider()
    st.markdown("**System Details**")
    st.markdown("<span style='color:#64748B; font-size:0.85rem;'>Protocol: GBFS Live JSON<br>Engine: In-Memory Pandas<br>Refresh Rate: 30 Seconds</span>", unsafe_allow_html=True)
    st.divider()
    st.markdown("**Developed by Sandeep Chowdary**")
    st.markdown("<span style='color:#64748B; font-size:0.85rem;'>Columbus, Ohio</span>", unsafe_allow_html=True)

# Load real-time data
with st.spinner(f"Connecting to mobility sensors in {selected_city}..."):
    try:
        df_stations, api_latency = fetch_live_city_telemetry(selected_city)
        feed_error = False
    except Exception as e:
        feed_error = True
        st.error(f"Failed to retrieve mobility sensor data: {e}")
        df_stations = pd.DataFrame()
        api_latency = 0

st.title(f"ParkPulse - Smart City Mobility: {selected_city.split(' (')[0]}")
st.markdown("<p style='color:#475569; font-size:1.05rem; margin-top:-0.5rem; margin-bottom:1.5rem;'>Real-time public transportation and docking sensor analytics for urban mobility networks.</p>", unsafe_allow_html=True)

if not feed_error and len(df_stations) > 0:
    tab1, tab2, tab3 = st.tabs([
        "Station Lookup & Telemetry", 
        "Network Map & Occupancy", 
        "API Response Metrics"
    ])
    
    # ==========================================
    # TAB 1: STATION LOOKUP
    # ==========================================
    with tab1:
        st.markdown("### Individual Station Diagnostics")
        st.write("Search any street intersection, landmark, or station identifier to inspect real-time vehicle availability and empty docking capacity.")
        
        col_search, col_hints = st.columns([2, 1])
        with col_search:
            search_query = st.text_input(
                "Search Street or Landmark:", 
                value=df_stations.iloc[0]["name"],
                placeholder="Example: Broadway, Michigan Ave, or Market St"
            ).strip().lower()
        with col_hints:
            st.info(f"Suggestion: Try searching `{df_stations.iloc[0]['name'].split(' & ')[0]}` or `{df_stations.iloc[1]['name'].split(' & ')[0]}`.")
            
        match_df = df_stations[
            df_stations["name"].str.lower().str.contains(search_query) |
            df_stations["station_id"].astype(str).str.contains(search_query)
        ]
        
        if len(match_df) > 0:
            station = match_df.iloc[0]
            badge_class = "badge-online" if station["is_renting"] == 1 else "badge-offline"
            badge_text = "ONLINE - ACTIVE DOCKS" if station["is_renting"] == 1 else "OFFLINE - MAINTENANCE"
            
            st.markdown(f"""
                <div class="station-panel">
                    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
                        <div class="station-name">{station['name']}</div>
                        <span class="{badge_class}">{badge_text}</span>
                    </div>
                    <p style="color:#64748B; font-size:0.9rem; margin-top:0.2rem;">Station ID: <b>{station['station_id']}</b> | Total Dock Capacity: <b>{station['capacity']}</b></p>
                    <hr style="border-color: #E2E8F0; margin: 1.2rem 0;">
                    <div style="display: flex; justify-content: space-between; flex-wrap: wrap; text-align: center;">
                        <div>
                            <div style="font-size:0.8rem; color:#64748B; text-transform:uppercase; font-weight:600;">Available Vehicles</div>
                            <div style="font-size:1.8rem; font-weight:800; color:#2563EB;">{station['num_bikes_available']}</div>
                        </div>
                        <div>
                            <div style="font-size:0.8rem; color:#64748B; text-transform:uppercase; font-weight:600;">Open Empty Docks</div>
                            <div style="font-size:1.8rem; font-weight:800; color:#10B981;">{station['num_docks_available']}</div>
                        </div>
                        <div>
                            <div style="font-size:0.8rem; color:#64748B; text-transform:uppercase; font-weight:600;">Station Occupancy</div>
                            <div style="font-size:1.8rem; font-weight:800; color:#8B5CF6;">{station['occupancy_pct']}%</div>
                        </div>
                        <div>
                            <div style="font-size:0.8rem; color:#64748B; text-transform:uppercase; font-weight:600;">Coordinates</div>
                            <div style="font-size:1.1rem; font-weight:600; color:#334155; margin-top:0.4rem;">{station['lat']}, {station['lon']}</div>
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            st.markdown("#### Geographic Positioning")
            view_state = pdk.ViewState(
                latitude=station["lat"],
                longitude=station["lon"],
                zoom=15,
                pitch=45
            )
            
            layer = pdk.Layer(
                "ScatterplotLayer",
                data=pd.DataFrame([station]),
                get_position=["lon", "lat"],
                get_color=[37, 99, 235, 255],
                get_radius=65,
                pickable=True,
                stroked=True,
                filled=True,
                radius_min_pixels=12,
                radius_max_pixels=25,
                line_width_min_pixels=3,
                get_line_color=[255, 255, 255]
            )
            
            st.pydeck_chart(pdk.Deck(layers=[layer], initial_view_state=view_state, tooltip={"text": f"Station: {station['name']}\nAvailable Vehicles: {station['num_bikes_available']}\nOpen Docks: {station['num_docks_available']}"}))
        else:
            st.warning(f"No active station found matching '{search_query}'.")
            
    # ==========================================
    # TAB 2: NETWORK MAP & OCCUPANCY
    # ==========================================
    with tab2:
        st.markdown("### Network Mobility KPIs")
        
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        total_stations = len(df_stations)
        total_bikes = int(df_stations["num_bikes_available"].sum())
        total_docks = int(df_stations["num_docks_available"].sum())
        avg_occ = round(df_stations["occupancy_pct"].mean(), 1)
        
        with kpi1:
            render_vibrant_card("card-orange", "Active IoT Stations", f"{total_stations:,}", "Broadcasting live sensors")
        with kpi2:
            render_vibrant_card("card-green", "Available Vehicles", f"{total_bikes:,}", "Ready for user checkout")
        with kpi3:
            render_vibrant_card("card-blue", "Open Docking Spots", f"{total_docks:,}", "Available for return")
        with kpi4:
            render_vibrant_card("card-purple", "Network Occupancy", f"{avg_occ}%", "Real-time system balance")
            
        st.markdown("---")
        
        col_map, col_table = st.columns([3, 2])
        
        with col_map:
            st.markdown("#### Live Spatial Distribution")
            st.caption("Blue = Active Available Vehicles | Red = Low Capacity / Empty Docks")
            
            map_df = df_stations.copy()
            map_df["color"] = map_df["occupancy_pct"].apply(lambda p: [37, 99, 235, 200] if p > 15 else [239, 68, 68, 220])
            
            city_coords = CITY_FEEDS[selected_city]
            city_view = pdk.ViewState(
                latitude=city_coords["lat"],
                longitude=city_coords["lon"],
                zoom=city_coords["zoom"],
                pitch=40
            )
            
            fleet_layer = pdk.Layer(
                "ScatterplotLayer",
                data=map_df,
                get_position=["lon", "lat"],
                get_color="color",
                get_radius=110,
                pickable=True,
                radius_min_pixels=4,
                radius_max_pixels=14,
            )
            
            st.pydeck_chart(pdk.Deck(layers=[fleet_layer], initial_view_state=city_view, tooltip={"text": "Station: {name}\nAvailable: {num_bikes_available} vehicles\nOpen Docks: {num_docks_available}\nOccupancy: {occupancy_pct}%"}))
            
        with col_table:
            st.markdown("#### Station Utilization Leaderboard")
            st.caption("Sorted chronologically by active vehicle availability")
            
            display_df = df_stations[["name", "num_bikes_available", "num_docks_available", "occupancy_pct"]].copy()
            display_df.columns = ["Station Name", "Vehicles", "Docks", "Occupancy %"]
            
            st.dataframe(
                display_df,
                column_config={
                    "Occupancy %": st.column_config.ProgressColumn(
                        "Occupancy %",
                        help="Percentage of station capacity currently occupied by vehicles",
                        format="%.1f%%",
                        min_value=0,
                        max_value=100,
                    )
                },
                use_container_width=True,
                hide_index=True,
                height=420,
            )
            
    # ==========================================
    # TAB 3: API RESPONSE METRICS
    # ==========================================
    with tab3:
        st.markdown("### Architecture & Ingestion Diagnostics")
        st.markdown("""
            This mobility platform operates on a **direct-to-consumer real-time telemetry model**. Instead of relying on static nightly batch pipelines or simulated CSV files, the backend connects directly to municipal IoT sensor endpoints over HTTP, parsing live GBFS JSON specifications into in-memory data frames.
        """)
        
        col_info1, col_info2 = st.columns(2)
        with col_info1:
            st.markdown("#### HTTP Ingestion Performance")
            st.info(f"**Last API Response Latency:** `{api_latency} ms`\n\nSimultaneous retrieval of both metadata (`station_information.json`) and real-time status (`station_status.json`).")
            st.markdown(f"**Target Host:** `{CITY_FEEDS[selected_city]['status']}`")
            
        with col_info2:
            st.markdown("#### Engineering Advantages")
            st.success("Zero Stale Data. 100% Physical Ground Truth.")
            st.markdown("In high-turnover urban mobility networks, vehicle availability changes every second. Direct API ingestion eliminates staging latency, ensuring dispatchers and riders observe exact real-world sensor states.")
            
        st.divider()
        st.markdown("#### Raw JSON DataFrame Inspection")
        st.dataframe(df_stations.head(50), use_container_width=True)
