# Author: Sandeep Chowdary
# Project: ParkPulse Telemetry Engine
# Description: DuckDB transformation pipeline for state transition detection and aggregation.

import duckdb
import pandas as pd
import os
from data_pipeline.generator import generate_fleet_telemetry

DB_PATH = "data/parkpulse.duckdb"


def run_pipeline():
    os.makedirs("data", exist_ok=True)
    conn = duckdb.connect(DB_PATH)
    
    # 1. Load raw simulated telemetry into staging table
    raw_df = generate_fleet_telemetry(num_vehicles=150, events_per_vehicle=20)
    conn.execute("DROP TABLE IF EXISTS stg_telemetry;")
    conn.execute("CREATE TABLE stg_telemetry AS SELECT * FROM raw_df;")
    
    # 2. Window transformations to detect ignition state changes (driving -> parked)
    conn.execute("""
        CREATE OR REPLACE VIEW int_vehicle_state_transitions AS
        WITH ranked_events AS (
            SELECT 
                *,
                LAG(ignition_state) OVER (PARTITION BY vehicle_id ORDER BY timestamp ASC) as prev_ignition,
                ROW_NUMBER() OVER (PARTITION BY vehicle_id ORDER BY timestamp DESC) as event_rank
            FROM stg_telemetry
        )
        SELECT 
            *,
            CASE 
                WHEN ignition_state = 'OFF' AND prev_ignition = 'ON' THEN 'JUST_PARKED'
                WHEN ignition_state = 'ON' AND prev_ignition = 'OFF' THEN 'JUST_DEPARTED'
                ELSE status 
            END as transition_event
        FROM ranked_events;
    """)
    
    # 3. Build current vehicle status mart (used for individual lookup)
    conn.execute("""
        CREATE OR REPLACE TABLE mart_current_vehicle_status AS
        WITH latest_ping AS (
            SELECT * FROM int_vehicle_state_transitions WHERE event_rank = 1
        ),
        last_parked_time AS (
            SELECT 
                vehicle_id,
                MAX(timestamp) as parked_since
            FROM int_vehicle_state_transitions
            WHERE ignition_state = 'OFF'
            GROUP BY vehicle_id
        )
        SELECT 
            l.vehicle_id,
            l.license_plate,
            l.car_model,
            l.fuel_type,
            l.district,
            l.latitude,
            l.longitude,
            l.speed_mph,
            l.ignition_state,
            l.status,
            l.battery_pct,
            l.timestamp as last_ping_time,
            COALESCE(p.parked_since, l.timestamp) as parked_since,
            ROUND(DATE_DIFF('minute', CAST(COALESCE(p.parked_since, l.timestamp) AS TIMESTAMP), CURRENT_TIMESTAMP) / 60.0, 1) as hours_parked
        FROM latest_ping l
        LEFT JOIN last_parked_time p ON l.vehicle_id = p.vehicle_id
        ORDER BY l.license_plate ASC;
    """)
    
    # 4. Build district aggregation mart (used for city-wide metrics)
    conn.execute("""
        CREATE OR REPLACE TABLE mart_district_parking_stats AS
        SELECT 
            district,
            COUNT(*) as total_tracked_vehicles,
            SUM(CASE WHEN status = 'PARKED' THEN 1 ELSE 0 END) as currently_parked_count,
            SUM(CASE WHEN status = 'DRIVING' THEN 1 ELSE 0 END) as active_driving_count,
            ROUND(AVG(CASE WHEN status = 'PARKED' THEN hours_parked ELSE NULL END), 1) as avg_parking_duration_hrs,
            ROUND(AVG(battery_pct), 1) as avg_fleet_battery_pct,
            ROUND((SUM(CASE WHEN status = 'PARKED' THEN 1.0 ELSE 0.0 END) / COUNT(*)) * 100.0, 1) as parking_utilization_rate
        FROM mart_current_vehicle_status
        GROUP BY district
        ORDER BY currently_parked_count DESC;
    """)
    
    conn.close()
    return DB_PATH


def get_connection():
    if not os.path.exists(DB_PATH):
        run_pipeline()
    return duckdb.connect(DB_PATH, read_only=True)


if __name__ == "__main__":
    run_pipeline()
    print("Pipeline execution completed successfully.")
