# Author: Sandeep Chowdary
# Project: ParkPulse Telemetry Engine
# Description: Simulates GPS and telematics data for connected vehicles across Columbus, OH.

import random
import datetime
import pandas as pd
import numpy as np
import os

DISTRICTS = [
    {"name": "Downtown / Statehouse", "lat": 39.9612, "lon": -82.9988, "lat_range": 0.008, "lon_range": 0.008},
    {"name": "Short North Arts District", "lat": 39.9815, "lon": -83.0035, "lat_range": 0.007, "lon_range": 0.006},
    {"name": "OSU Campus Area", "lat": 40.0000, "lon": -83.0145, "lat_range": 0.010, "lon_range": 0.010},
    {"name": "German Village", "lat": 39.9430, "lon": -82.9930, "lat_range": 0.006, "lon_range": 0.007},
    {"name": "Arena District", "lat": 39.9690, "lon": -83.0060, "lat_range": 0.005, "lon_range": 0.005},
    {"name": "Easton Town Center", "lat": 40.0520, "lon": -82.9150, "lat_range": 0.009, "lon_range": 0.009},
    {"name": "Grandview Heights", "lat": 39.9800, "lon": -83.0400, "lat_range": 0.008, "lon_range": 0.008},
    {"name": "Clintonville", "lat": 40.0350, "lon": -83.0180, "lat_range": 0.009, "lon_range": 0.008},
]

CAR_MODELS = [
    ("Tesla Model 3", "Electric"), ("Tesla Model Y", "Electric"),
    ("Rivian R1S", "Electric"), ("Ford F-150 Lightning", "Electric"),
    ("Honda Civic", "Gasoline"), ("Toyota RAV4 Hybrid", "Hybrid"),
    ("Subaru Outback", "Gasoline"), ("Jeep Grand Cherokee", "Gasoline"),
    ("BMW X5", "Gasoline"), ("Hyundai Ioniq 5", "Electric")
]


def generate_license_plate(index):
    if index == 0:
        return "MY-CAR-01"
    elif index == 1:
        return "OH-8842-EV"
    letters = "".join(random.choices("ABCDEFGHJKLMNPQRSTUVWXYZ", k=3))
    numbers = "".join(random.choices("0123456789", k=4))
    return f"{letters}-{numbers}"


def generate_fleet_telemetry(num_vehicles=120, events_per_vehicle=15):
    random.seed(42)
    np.random.seed(42)
    
    now = datetime.datetime.now()
    records = []
    
    for i in range(num_vehicles):
        vehicle_id = f"V-{1000 + i}"
        plate = generate_license_plate(i)
        model, fuel_type = CAR_MODELS[i % len(CAR_MODELS)]
        district = random.choice(DISTRICTS)
        
        is_currently_parked = (i % 4 != 0)
        
        base_lat = district["lat"] + random.uniform(-district["lat_range"], district["lat_range"])
        base_lon = district["lon"] + random.uniform(-district["lon_range"], district["lon_range"])
        battery_level = random.randint(35, 98)
        
        for step in range(events_per_vehicle):
            timestamp = now - datetime.timedelta(minutes=step * random.randint(15, 30))
            
            if step == 0:
                if is_currently_parked:
                    status = "PARKED"
                    ignition = "OFF"
                    speed = 0.0
                    lat, lon = base_lat, base_lon
                else:
                    status = "DRIVING"
                    ignition = "ON"
                    speed = round(random.uniform(18.5, 55.0), 1)
                    lat = base_lat + random.uniform(-0.003, 0.003)
                    lon = base_lon + random.uniform(-0.003, 0.003)
            elif step == 1 and is_currently_parked:
                status = "PARKED"
                ignition = "OFF"
                speed = 0.0
                lat, lon = base_lat, base_lon
            else:
                was_driving = random.choice([True, True, False])
                if was_driving:
                    status = "DRIVING"
                    ignition = "ON"
                    speed = round(random.uniform(15.0, 65.0), 1)
                    lat = base_lat + random.uniform(-0.015, 0.015)
                    lon = base_lon + random.uniform(-0.015, 0.015)
                else:
                    status = "PARKED"
                    ignition = "OFF"
                    speed = 0.0
                    lat = base_lat + random.uniform(-0.005, 0.005)
                    lon = base_lon + random.uniform(-0.005, 0.005)
            
            ping_battery = max(10, battery_level - int(step * 0.5))
            
            records.append({
                "event_id": f"EVT-{abs(hash((vehicle_id, timestamp))) % 10000000}",
                "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                "vehicle_id": vehicle_id,
                "license_plate": plate,
                "car_model": model,
                "fuel_type": fuel_type,
                "district": district["name"],
                "latitude": round(lat, 6),
                "longitude": round(lon, 6),
                "speed_mph": speed,
                "ignition_state": ignition,
                "status": status,
                "battery_pct": ping_battery
            })
            
    df = pd.DataFrame(records)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values(by=["timestamp"]).reset_index(drop=True)
    df["timestamp"] = df["timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S")
    return df


if __name__ == "__main__":
    df = generate_fleet_telemetry()
    os.makedirs("data", exist_ok=True)
    df.to_csv("data/raw_telemetry.csv", index=False)
    print(f"Generated {len(df)} telemetry logs across {len(df['vehicle_id'].unique())} vehicles.")
