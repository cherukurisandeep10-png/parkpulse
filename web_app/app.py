# Author: Sandeep Chowdary
# Project: ParkPulse Telemetry Engine
# Description: Streamlit interactive frontend for vehicle tracking and telemetry analysis.

import streamlit as st
import pandas as pd
import numpy as np
import pydeck as pdk
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from data_pipeline.engine import get_connection, run_pipeline
from web_app.components import apply_custom_styles, render_metric_card

st.set_page_config(
    page_title="ParkPulse | Vehicle Telemetry Engine",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)

apply_custom_styles()


@st.cache_data(ttl=60)
def load_fleet_data():
    conn = get_connection()
    df = conn.execute("SELECT * FROM mart_current_vehicle_status").fetchdf()
    district_stats = conn.execute("SELECT * FROM mart_district_parking_stats").fetchdf()
    conn.close()
    return df, district_stats


with st.sidebar:
    st.title("🚗 ParkPulse")
    st.caption("Connected Vehicle Telematics & Parking Engine")
    st.divider()
    
    if st.button("Refresh Telemetry Stream", help="Execute DuckDB pipeline to ingest new pings"):
        with st.spinner("Executing pipeline..."):
            run_pipeline()
            st.cache_data.clear()
        st.success("Pipeline updated successfully.")
        
    st.subheader("Filters")
    df_fleet, df_districts = load_fleet_data()
    
    all_districts = ["All Districts"] + sorted(df_fleet["district"].unique().tolist())
    selected_district = st.selectbox("District:", all_districts)
    
    status_filter = st.radio("Status:", ["All", "PARKED", "DRIVING"], horizontal=True)
    
    st.divider()
    st.markdown("### System Specs")
    st.markdown("- **Engine:** DuckDB (In-Memory OLAP)")
    st.markdown("- **Ingestion:** Time-Series Telemetry")
    st.markdown("- **Mapping:** Pydeck / Mapbox GL")
    st.divider()
    st.caption("Author: **Sandeep Chowdary**\n\nColumbus, Ohio")

# Filter DataFrame based on sidebar selections
filtered_df = df_fleet.copy()
if selected_district != "All Districts":
    filtered_df = filtered_df[filtered_df["district"] == selected_district]
if status_filter != "All":
    filtered_df = filtered_df[filtered_df["status"] == status_filter]

st.title("ParkPulse - Connected Fleet Telemetry Portal")
st.markdown("Monitoring GPS telemetry, state transitions, and parking availability across **Columbus, Ohio**.")

tab1, tab2, tab3 = st.tabs([
    "Vehicle Lookup", 
    "City Telemetry Map", 
    "SQL Architecture & Logs"
])

# ==========================================
# TAB 1: VEHICLE LOOKUP
# ==========================================
with tab1:
    st.subheader("Vehicle Lookup")
    st.write("Search by license plate or vehicle ID to retrieve current coordinates, battery diagnostic data, and parking duration.")
    
    col_search, col_hints = st.columns([2, 1])
    with col_search:
        search_query = st.text_input(
            "License Plate or Vehicle ID:", 
            value="MY-CAR-01",
            placeholder="e.g., MY-CAR-01, OH-8842-EV, or V-1005"
        ).strip().upper()
    with col_hints:
        st.info("Demo test vehicles: `MY-CAR-01` or `OH-8842-EV`.")
        
    match_df = df_fleet[
        (df_fleet["license_plate"].str.upper() == search_query) | 
        (df_fleet["vehicle_id"].str.upper() == search_query)
    ]
    
    if len(match_df) > 0:
        car = match_df.iloc[0]
        
        status_badge = f'<span class="status-parked">PARKED ({car["hours_parked"]} hrs)</span>' if car["status"] == "PARKED" else '<span class="status-driving">ACTIVE DRIVING</span>'
        
        st.markdown(f"""
            <div class="vehicle-details-box">
                <h3 style="margin-top:0; color:#00F0FF;">{car['car_model']} ({car['fuel_type']}) — Plate: <b>{car['license_plate']}</b></h3>
                <p><b>Status:</b> {status_badge} &nbsp;&nbsp;|&nbsp;&nbsp; <b>ID:</b> {car['vehicle_id']} &nbsp;&nbsp;|&nbsp;&nbsp; <b>District:</b> {car['district']}</p>
                <hr style="border-color: #313244;">
                <div style="display: flex; justify-content: space-between; flex-wrap: wrap;">
                    <div>📍 <b>GPS:</b> <code>{car['latitude']}, {car['longitude']}</code></div>
                    <div>⚡ <b>Battery:</b> <code>{car['battery_pct']}%</code></div>
                    <div>🏎️ <b>Speed:</b> <code>{car['speed_mph']} mph</code></div>
                    <div>🔑 <b>Ignition:</b> <code>{car['ignition_state']}</code></div>
                </div>
                <div style="margin-top: 0.8rem; font-size: 0.85rem; color: #A6ADC8;">
                    Last Telemetry Ping: {car['last_ping_time']} &nbsp;|&nbsp; Parked Since: {car['parked_since']}
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("#### Spatial Coordinates")
        
        view_state = pdk.ViewState(
            latitude=car['latitude'],
            longitude=car['longitude'],
            zoom=15,
            pitch=45
        )
        
        layer = pdk.Layer(
            "ScatterplotLayer",
            data=pd.DataFrame([car]),
            get_position=["longitude", "latitude"],
            get_color=[0, 240, 255, 255] if car["status"] == "PARKED" else [42, 157, 143, 255],
            get_radius=45,
            pickable=True,
            stroked=True,
            filled=True,
            radius_scale=1,
            radius_min_pixels=8,
            radius_max_pixels=20,
            line_width_min_pixels=2,
            get_line_color=[255, 255, 255]
        )
        
        r = pdk.Deck(
            layers=[layer],
            initial_view_state=view_state,
            tooltip={"text": f"Plate: {car['license_plate']}\nStatus: {car['status']}\nBattery: {car['battery_pct']}%"}
        )
        st.pydeck_chart(r)
        
    else:
        st.warning(f"No vehicle found matching '{search_query}'.")
        with st.expander("View All Tracked License Plates"):
            st.dataframe(df_fleet[["vehicle_id", "license_plate", "car_model", "status", "district", "hours_parked"]], use_container_width=True)

# ==========================================
# TAB 2: CITY TELEMETRY MAP
# ==========================================
with tab2:
    st.subheader("Fleet Telemetry Overview")
    
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    total_cars = len(df_fleet)
    parked_cars = len(df_fleet[df_fleet["status"] == "PARKED"])
    driving_cars = len(df_fleet[df_fleet["status"] == "DRIVING"])
    avg_bat = round(df_fleet["battery_pct"].mean(), 1)
    
    with kpi1:
        render_metric_card("Tracked Fleet", f"{total_cars}", "Total vehicles")
    with kpi2:
        render_metric_card("Parked Vehicles", f"{parked_cars}", f"{round((parked_cars/total_cars)*100,1)}% utilization")
    with kpi3:
        render_metric_card("Active On-Road", f"{driving_cars}", "Transmitting GPS")
    with kpi4:
        render_metric_card("Average Battery", f"{avg_bat}%", "Fleet diagnostic avg")
        
    st.markdown("---")
    
    col_map, col_table = st.columns([3, 2])
    
    with col_map:
        st.markdown("#### Live Spatial Distribution")
        st.caption("Green = Parked | Red = Driving")
        
        map_df = filtered_df.copy()
        map_df["color"] = map_df["status"].apply(lambda s: [0, 240, 255, 200] if s == "PARKED" else [230, 57, 70, 220])
        
        city_view = pdk.ViewState(
            latitude=39.9850,
            longitude=-83.0000,
            zoom=11.5,
            pitch=40
        )
        
        fleet_layer = pdk.Layer(
            "ScatterplotLayer",
            data=map_df,
            get_position=["longitude", "latitude"],
            get_color="color",
            get_radius=80,
            pickable=True,
            radius_min_pixels=6,
            radius_max_pixels=15,
        )
        
        deck_city = pdk.Deck(
            layers=[fleet_layer],
            initial_view_state=city_view,
            tooltip={"text": "Vehicle: {license_plate}\nModel: {car_model}\nStatus: {status}\nDistrict: {district}"}
        )
        st.pydeck_chart(deck_city)
        
    with col_table:
        st.markdown("#### District Aggregations")
        st.caption("Data source: `mart_district_parking_stats`")
        
        display_districts = df_districts[["district", "currently_parked_count", "active_driving_count", "avg_parking_duration_hrs", "parking_utilization_rate"]].copy()
     st.dataframe(
            display_districts,
            column_config={
                "Utilization %": st.column_config.ProgressColumn(
                    "Utilization %",
                    help="Percentage of tracked vehicles currently parked in this district",
                    format="%.1f%%",
                    min_value=0,
                    max_value=100,
                )
            },
            use_container_width=True,
            hide_index=True,
            height=380,
        )

# ==========================================
# TAB 3: SQL ARCHITECTURE & LOGS
# ==========================================
with tab3:
    st.subheader("Data Transformation Logic")
    st.markdown("""
        In raw telematics streams, vehicles emit periodic pings containing timestamps, coordinates, and diagnostic flags.
        To calculate parking intervals without relying on client-side state, this pipeline uses window functions over the raw staging table.
    """)
    
    col_arch1, col_arch2 = st.columns(2)
    with col_arch1:
        st.markdown("#### Window Function State Detection")
        st.markdown("""
            By partitioning event records by `vehicle_id` and ordering chronologically, we evaluate state transitions:
            ```sql
            SELECT 
                *,
                LAG(ignition_state) OVER (
                    PARTITION BY vehicle_id 
                    ORDER BY timestamp ASC
                ) as prev_ignition
            FROM stg_telemetry;
            ```
            When `prev_ignition = 'ON'` and `ignition_state = 'OFF'`, the record is categorized as a `JUST_PARKED` transition event, establishing the initial timestamp for the parking interval.
        """)
        
    with col_arch2:
        st.markdown("#### Data Mart Schema")
        st.markdown("""
            The pipeline separates staging data from downstream analytical tables:
            1. **`stg_telemetry`**: Append-only log of incoming vehicle pings.
            2. **`int_vehicle_state_transitions`**: Intermediate view computing lag states and event ranks.
            3. **`mart_current_vehicle_status`**: Materialized table containing the latest ping per vehicle and calculated parking duration.
            4. **`mart_district_parking_stats`**: Aggregate table grouped by district for spatial analysis.
        """)
        
    st.divider()
    st.markdown("#### Database Table Inspector")
    
    table_choice = st.selectbox("Select Table:", ["mart_current_vehicle_status", "mart_district_parking_stats", "stg_telemetry"])
    
    conn = get_connection()
    if table_choice == "mart_current_vehicle_status":
        st.dataframe(conn.execute("SELECT * FROM mart_current_vehicle_status LIMIT 50").fetchdf(), use_container_width=True)
    elif table_choice == "mart_district_parking_stats":
        st.dataframe(conn.execute("SELECT * FROM mart_district_parking_stats").fetchdf(), use_container_width=True)
    else:
        st.dataframe(conn.execute("SELECT * FROM stg_telemetry ORDER BY timestamp DESC LIMIT 50").fetchdf(), use_container_width=True)
    conn.close()
