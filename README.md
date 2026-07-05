# ParkPulse - Connected Vehicle Telemetry & Parking Engine

A lightweight data engineering pipeline and interactive dashboard that ingests vehicle GPS telemetry, automatically detects parking state transitions using SQL window functions, and maps fleet availability across Columbus, Ohio.

## Background & Motivation

Most "Find My Car" applications rely on manual user input—a user taps a button on their phone to save a GPS coordinate when they park. In reality, modern connected vehicles (EVs and telematics-equipped fleets) continuously transmit diagnostic and location data back to cloud servers. 

I built this project to simulate and solve the backend data engineering problem behind vehicle tracking:
1. **Ingesting time-series telemetry:** Processing GPS pings, speed, battery percentage, and engine ignition states over time.
2. **Automated state transition detection:** Using SQL window functions (`LAG` and `ROW_NUMBER`) inside an OLAP engine to identify the exact timestamp and coordinates where a vehicle transitioned from driving (`IGNITION_ON`) to parked (`IGNITION_OFF`), removing the need for manual user triggers.
3. **Low-latency serving:** Storing transformed records in DuckDB and serving them to a frontend web application for real-time lookup and spatial visualization.

## Architecture

```
[Telemetry Generator] -> [Staging: stg_telemetry] -> [SQL Window Functions] -> [Analytical Marts] -> [Streamlit / Pydeck UI]
```

* **Ingestion / Simulation:** Python script generating time-series telematics for 150 vehicles across 8 Columbus districts.
* **Database / Processing:** DuckDB (embedded OLAP engine) performing ELT transformations and window queries.
* **Visualization:** Streamlit web app with custom styling and Pydeck 3D spatial mapping.

## Repository Structure

```text
parkpulse/
├── data_pipeline/
│   ├── generator.py      # Telemetry simulation script
│   └── engine.py         # DuckDB database schema and SQL transformation pipelines
├── web_app/
│   ├── app.py            # Main Streamlit web dashboard
│   └── components.py     # UI components and layout styling
├── requirements.txt      # Python dependencies
├── run.py                # Command-line entry point
└── README.md
```

## Getting Started

### 1. Install Dependencies
Requires Python 3.10 or higher. Install the required packages using pip:

```bash
pip install -r requirements.txt
```

### 2. Run the Application
To run the end-to-end data pipeline and start the local web server:

```bash
python3 run.py
```

Open your browser to `http://localhost:8501`. 

To execute only the DuckDB transformation pipeline without launching the UI:

```bash
python3 run.py --data-only
```

## Data Engineering Notes: How State Detection Works

The core transformation logic resides in `data_pipeline/engine.py`. Rather than updating rows in place, the pipeline loads raw event logs into a staging table and applies analytical window functions to compare the current ping against the preceding ping:

```sql
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
```

This identifies the exact point in time when a vehicle stopped moving and turned off its engine, allowing the downstream analytical mart (`mart_current_vehicle_status`) to calculate accurate parking duration intervals.

## Author

**Sandeep Chowdary**
* Software / Data Engineer
* Based in Columbus, OH
* GitHub: [sandeepchowdary](https://github.com/)

## License

This project is open-source and available under the MIT License.
