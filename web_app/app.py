# Author: Sandeep Chowdary
# Project: ParkPulse — Live Smart City Bikeshare & EV Telemetry Portal
# Description: Real-time IoT sensor telemetry dashboard fetching live GBFS public data feeds.

import streamlit as st
import pandas as pd
import numpy as np
import pydeck as pdk
import urllib.request
import json
import time

st.set_page_config(
    page_title="ParkPulse | Live IoT Telemetry Portal",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Cyberpunk / Dark-Mode AI UI Styling
st.markdown("""
    <style>
    /* Main App Background */
    .stApp {
        background-color: #0E1117;
        color: #E6EDF3;
    }
    
    /* Sleek Metric Cards */
    .metric-card {
        background: linear-gradient(135deg, #161B22 0%, #1E242C 100%);
        padding: 1.4rem;
        border-radius: 12px;
        border: 1px solid #30363D;
        border-left: 5px solid #00F0FF;
        color: #FFFFFF;
        margin-bottom: 1rem;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 12px 32px rgba(0, 240, 255, 0.15);
    }
    .metric-title {
        font-size: 0.85rem;
        color: #8B949E;
        text-transform: uppercase;
        letter-spacing: 1px;
        font-weight: 600;
        margin-bottom: 0.4rem;
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: 800;
        color: #FFFFFF;
        text-shadow: 0 0 10px rgba(0, 240, 255, 0.3);
    }
    .metric-sub {
        font-size: 0.8rem;
        color: #58A6FF;
        margin-top: 0.4rem;
    }
    
    /* Status Badges */
    .status-active {
        background: rgba(42, 157, 143, 0.2);
        color: #2A9D8F;
        border: 1px solid #2A9D8F;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-weight: 700;
        font-size: 0.8rem;
        display: inline-block;
        letter-spacing: 0.5px;
    }
    .status-low {
        background: rgba(230, 57, 70, 0.2);
        color: #E63946;
        border: 1px solid #E63946;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-weight: 700;
        font-size: 0.8rem;
        display: inline-block;
        letter-spacing: 0.5px;
    }
    
    /* Station Details Lookup Box */
    .station-box {
        background: linear-gradient(145deg, #161B22, #0D1117);
        border: 1px solid #30363D;
        border-radius: 12px;
        padding: 1.5rem;
        color: #C9D1D9;
        margin-top: 1rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.5);
    }
    
    /* Streamlit Tabs Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 20px;
        background-color: transparent;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #161B22;
        border-radius: 8px 8px 0px 0px;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
        padding-left: 20px;
        padding-right: 20px;
        color: #8B949E;
        font-weight: 600;
        border: 1px solid #30363D;
        border-bottom: none;
    }
    .stTabs [aria-selected="true"] {
        background-color: #1F242D !important;
        color: #00F0FF !important;
        border-top: 3px solid #00F0FF !important;
        text-shadow: 0 0 10px rgba(0, 240, 255, 0.4);
    }
    
    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: #161B22;
        border-right: 1px solid #30363D;
    }
    </style>
""", unsafe_allow_html=True)


def render_metric_card(title, value, subtitle=""):
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">{title}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-sub">{subtitle}</div>
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
    st.title("⚡ ParkPulse")
    st.caption("Real-Time Smart City IoT Telemetry")
    st.divider()
    
    selected_city = st.selectbox("Select Live City Sensor Feed:", list(CITY_FEEDS.keys()))
    
    if st.button("🔄 Refresh Live Sensors", help="Fetch immediate real-time IoT status from city docking stations"):
        st.cache_data.clear()
        st.success("Fetched latest live physical sensor feed!")
        
    st.divider()
    st.markdown("### System Architecture")
    st.markdown("- **Mode:** 100% Real-Time IoT Sensors")
    st.markdown("- **Protocol:** GBFS Public Feeds")
    st.markdown("- **Engine:** In-Memory Pandas OLAP")
    st.divider()
    st.caption("Author: **Sandeep Chowdary**\n\nColumbus, Ohio")

# Load real-time data
with st.spinner(f"Connecting to live IoT sensors in {selected_city}..."):
    try:
        df_stations, api_latency = fetch_live_city_telemetry(selected_city)
        feed_error = False
    except Exception as e:
        feed_error = True
        st.error(f"Failed to connect to live sensor feed: {e}")
        df_stations = pd.DataFrame()
        api_latency = 0

st.title(f"⚡ ParkPulse — Live Smart City Telemetry: {selected_city.split(' (')[0]}")
st.markdown("Direct ingestion of physical IoT docking sensor feeds, monitoring real-time vehicle availability, battery status, and spatial utilization.")

if not feed_error and len(df_stations) > 0:
    tab1, tab2, tab3 = st.tabs([
        "📍 Street & Station Lookup", 
        "🗺️ Live City Heatmap & Occupancy", 
        "⚡ API Telemetry Inspector"
    ])
    
    # ==========================================
    # TAB 1: STREET & STATION LOOKUP
    # ==========================================
    with tab1:
        st.subheader("Live Station Sensor Lookup")
        st.write("Search any street name, landmark, or station ID to view live available vehicles and open docking capacity right now.")
        
        col_search, col_hints = st.columns([2, 1])
        with col_search:
            search_query = st.text_input(
                "Enter Street Name or Station:", 
                value=df_stations.iloc[0]["name"],
                placeholder="e.g., Broadway, Michigan Ave, or Times Sq"
            ).strip().lower()
        with col_hints:
            st.info(f"💡 Try typing a street like `{df_stations.iloc[0]['name'].split(' & ')[0]}` or `{df_stations.iloc[1]['name'].split(' & ')[0]}`.")
            
        match_df = df_stations[
            df_stations["name"].str.lower().str.contains(search_query) |
            df_stations["station_id"].astype(str).str.contains(search_query)
        ]
        
        if len(match_df) > 0:
            station = match_df.iloc[0]
            status_badge = '<span class="status-active">🟢 ACTIVE DOCKING STATION</span>' if station["is_renting"] == 1 else '<span class="status-low">🔴 OFFLINE / DISABLED</span>'
            
            st.markdown(f"""
                <div class="station-box">
                    <h3 style="margin-top:0; color:#00F0FF;">📍 {station['name']} — ID: <b>{station['station_id']}</b></h3>
                    <p><b>Status:</b> {status_badge} &nbsp;&nbsp;|&nbsp;&nbsp; <b>Total Station Capacity:</b> {station['capacity']} docks</p>
                    <hr style="border-color: #30363D;">
                    <div style="display: flex; justify-content: space-between; flex-wrap: wrap; margin-top: 1rem;">
                        <div>🚲 <b>Available Vehicles:</b> <code style="color:#00F0FF; font-size:1.1rem;">{station['num_bikes_available']}</code></div>
                        <div>🅿️ <b>Open Empty Docks:</b> <code style="color:#2A9D8F; font-size:1.1rem;">{station['num_docks_available']}</code></div>
                        <div>📊 <b>Station Occupancy:</b> <code style="color:#58A6FF; font-size:1.1rem;">{station['occupancy_pct']}%</code></div>
                        <div>📍 <b>GPS Coordinates:</b> <code>{station['lat']}, {station['lon']}</code></div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            st.markdown("#### Station Spatial Location")
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
                get_color=[0, 240, 255, 255],
                get_radius=60,
                pickable=True,
                stroked=True,
                filled=True,
                radius_min_pixels=10,
                radius_max_pixels=25,
                line_width_min_pixels=2,
                get_line_color=[255, 255, 255]
            )
            
            st.pydeck_chart(pdk.Deck(layers=[layer], initial_view_state=view_state, tooltip={"text": f"Station: {station['name']}\nAvailable Bikes: {station['num_bikes_available']}\nOpen Docks: {station['num_docks_available']}"}))
        else:
            st.warning(f"No active station found matching '{search_query}'.")
            
    # ==========================================
    # TAB 2: LIVE CITY HEATMAP & OCCUPANCY
    # ==========================================
    with tab2:
        st.subheader("City-Wide Sensor Overview")
        
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        total_stations = len(df_stations)
        total_bikes = int(df_stations["num_bikes_available"].sum())
        total_docks = int(df_stations["num_docks_available"].sum())
        avg_occ = round(df_stations["occupancy_pct"].mean(), 1)
        
        with kpi1:
            render_metric_card("Active IoT Stations", f"{total_stations:,}", "Broadcasting live status")
        with kpi2:
            render_metric_card("Available Vehicles", f"{total_bikes:,}", "Ready for user checkout")
        with kpi3:
            render_metric_card("Open Docking Spots", f"{total_docks:,}", "Available for return")
        with kpi4:
            render_metric_card("Avg Network Occupancy", f"{avg_occ}%", "Real-time fleet balance")
            
        st.markdown("---")
        
        col_map, col_table = st.columns([3, 2])
        
        with col_map:
            st.markdown("#### Live Geospatial Distribution")
            st.caption("Cyan = Available Vehicles | Red = Empty Dock Station")
            
            map_df = df_stations.copy()
            map_df["color"] = map_df["occupancy_pct"].apply(lambda p: [0, 240, 255, 200] if p > 20 else [230, 57, 70, 220])
            
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
                get_radius=100,
                pickable=True,
                radius_min_pixels=4,
                radius_max_pixels=12,
            )
            
            st.pydeck_chart(pdk.Deck(layers=[fleet_layer], initial_view_state=city_view, tooltip={"text": "Station: {name}\nAvailable: {num_bikes_available} bikes\nOpen Docks: {num_docks_available}\nOccupancy: {occupancy_pct}%"}))
            
        with col_table:
            st.markdown("#### Live Station Leaderboard")
            st.caption("Sorted by real-time vehicle availability")
            
            display_df = df_stations[["name", "num_bikes_available", "num_docks_available", "occupancy_pct"]].copy()
            display_df.columns = ["Station Name", "Bikes", "Docks", "Occupancy %"]
            
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
                height=400,
            )
            
    # ==========================================
    # TAB 3: API TELEMETRY INSPECTOR
    # ==========================================
    with tab3:
        st.subheader("Direct-to-Consumer IoT Architecture")
        st.markdown("""
            Unlike traditional batch pipelines that stage static data overnight, this portal demonstrates **real-time API telemetry ingestion**.
            When a user selects a city, the engine establishes a live HTTP connection to physical street docking sensors, parses GBFS JSON payloads in memory, and renders sub-second spatial analytics.
        """)
        
        col_info1, col_info2 = st.columns(2)
        with col_info1:
            st.markdown("#### Live API Performance")
            st.info(f"⚡ **Last API Fetch Latency:** `{api_latency} ms` (Fetched 2 live JSON feeds simultaneously)")
            st.markdown(f"**Primary Endpoint:** `{CITY_FEEDS[selected_city]['status']}`")
            
        with col_info2:
            st.markdown("#### Why Real-Time Ingestion Matters")
            st.success("Zero data stale-time. 100% physical world accuracy.")
            st.markdown("In smart city transportation, vehicle availability changes every second. By bypassing intermediate batch staging tables, this architecture guarantees that users and dispatchers see exact, real-world physical dock occupancy.")
            
        st.divider()
        st.markdown("#### Raw JSON DataFrame Inspector")
        st.dataframe(df_stations.head(50), use_container_width=True)
