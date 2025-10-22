import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json

np.random.seed(42)

# Parameters
n_sharks = 5
timestamps_per_shark = 20
start_date = datetime(2025, 10, 1, 6, 0, 0)
time_interval_hours = 12

species_list = ["Whale Shark", "Great White", "Tiger Shark", "Bull Shark", "Hammerhead"]
tag_status_choices = ["active", "inactive", "battery_low", "recovered"]
sources = ["satellite_tag", "photo_id", "acoustic_tag", "manual_sighting"]
behaviors = ["transiting", "foraging", "resting", "near_shore", "deep_dive"]

start_coords = [
    (14.5, 119.9), (-23.5, 151.9), (25.0, -80.2),
    (-34.9, 18.4), (7.0, -73.8)
]

def local_sst(lat, lon):
    base = 30 - (abs(lat) * 0.3)
    return round(base + np.sin(np.radians(lon))*1.5 + np.random.normal(0,0.5), 2)

def local_chl(lat, lon):
    coastal_factor = 1.0 if abs(lon) % 10 < 2 or abs(lat) % 10 < 2 else 0.4
    return round(max(0.05, np.random.gamma(1.2)*coastal_factor), 3)

records = []
for i in range(n_sharks):
    shark_id = f"S{i+1:03d}"
    species = species_list[i % len(species_list)]
    tag_id = f"T-{1000+i}"
    lat, lon = start_coords[i]
    for t in range(timestamps_per_shark):
        dt = start_date + timedelta(hours=time_interval_hours * t)
        step_dist_km = np.random.normal(25, 15)
        dlat = (np.random.normal(0,1) * step_dist_km) / 111.0
        dlon = (np.random.normal(0,1) * step_dist_km) / (111.0 * max(0.2, np.cos(np.radians(lat))))
        if np.random.rand() < 0.08:
            dlat += np.random.normal(0,2)
            dlon += np.random.normal(0,2)
        lat += dlat
        lon += dlon
        depth = abs(int(np.random.exponential(30)))
        temp = round(local_sst(lat, lon) - (0.02 * depth) + np.random.normal(0,0.3), 2)
        battery = round(4.2 - 0.002*(t+np.random.rand()*10), 2)
        tag_status = np.random.choice(tag_status_choices, p=[0.7,0.05,0.2,0.05])
        source = np.random.choice(sources, p=[0.45,0.2,0.2,0.15])
        behavior = np.random.choice(behaviors, p=[0.5,0.25,0.1,0.1,0.05])
        sst = local_sst(lat, lon)
        chl = local_chl(lat, lon)
        current = round(abs(np.random.normal(0.3, 0.2)), 2)
        image_id = f"{shark_id}_img_{t+1:03d}" if source == "photo_id" else ""
        records.append({
            "shark_id": shark_id,
            "species": species,
            "tag_id": tag_id,
            "datetime_utc": dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "latitude": round(lat, 6),
            "longitude": round(lon, 6),
            "depth_m": depth,
            "water_temp_C": temp,
            "battery_V": battery,
            "tag_status": tag_status,
            "source": source,
            "behavior": behavior,
            "sea_surface_temp_C": sst,
            "chlorophyll_mg_m3": chl,
            "ocean_current_speed_m_s": current,
            "image_id": image_id
        })

df = pd.DataFrame(records)
df.to_csv("shark_tracking_sample.csv", index=False)
print("✅ shark_tracking_sample.csv generated successfully!")
