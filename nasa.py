import streamlit as st
import pandas as pd
import pydeck as pdk
import matplotlib.pyplot as plt
from datetime import datetime
import requests

st.set_page_config(page_title="NASA Shark Tracker", layout="wide")
st.title("🦈 NASA Shark Tracking Dashboard with Real-Time Ocean Data 🌊")

# --- Load Data ---
@st.cache_data
def load_data(file=None):
    if file is not None:
        df = pd.read_csv(file)
    else:
        df = pd.read_csv("shark_tracking_sample.csv")
    df["datetime_utc"] = pd.to_datetime(df["datetime_utc"])
    return df

uploaded_file = st.file_uploader("Upload Shark Tracking CSV", type=["csv"])
df = load_data(uploaded_file)

# --- Sidebar Filters ---
st.sidebar.header("🔎 Filters")
shark_ids = st.sidebar.multiselect("Shark ID", options=df["shark_id"].unique(), default=list(df["shark_id"].unique()))
species = st.sidebar.multiselect("Species", options=df["species"].unique(), default=list(df["species"].unique()))
status = st.sidebar.multiselect("Tag Status", options=df["tag_status"].unique(), default=list(df["tag_status"].unique()))

# --- Convert pandas Timestamp to Python datetime for Streamlit slider ---
min_date = df["datetime_utc"].min().to_pydatetime()
max_date = df["datetime_utc"].max().to_pydatetime()

date_range = st.sidebar.slider(
    "Date Range",
    min_value=min_date,
    max_value=max_date,
    value=(min_date, max_date)
)

# --- Filtered Data ---
filtered_df = df[
    (df["shark_id"].isin(shark_ids)) &
    (df["species"].isin(species)) &
    (df["tag_status"].isin(status)) &
    (df["datetime_utc"].between(date_range[0], date_range[1]))
]

st.subheader(f"Filtered Dataset — {len(filtered_df)} records")
st.dataframe(filtered_df.head(10))

# --- Metrics ---
col1, col2, col3, col4 = st.columns(4)
col1.metric("Time Span", f"{date_range[0].strftime('%Y-%m-%d')} → {date_range[1].strftime('%Y-%m-%d')}")
col2.metric("Avg Water Temp (°C)", f"{filtered_df['water_temp_C'].mean():.2f}")
col3.metric("Avg Depth (m)", f"{filtered_df['depth_m'].mean():.2f}")
col4.metric("Avg Battery (V)", f"{filtered_df['battery_V'].mean():.2f}")

# --- Map Setup ---
color_map = {
    "Whale Shark": [255, 165, 0],
    "Great White": [255, 0, 0],
    "Tiger Shark": [0, 255, 0],
    "Bull Shark": [0, 0, 255],
    "Hammerhead": [255, 255, 0]
}
filtered_df["color"] = filtered_df["species"].map(color_map)
filtered_df["color"] = filtered_df["color"].apply(lambda x: x if isinstance(x, list) else [200, 200, 200])

# --- Interactive Map ---
st.subheader("📍 Shark Tracks Map")
if not filtered_df.empty:
    scatter = pdk.Layer(
        "ScatterplotLayer",
        data=filtered_df,
        get_position='[longitude, latitude]',
        get_color='color',
        get_radius=1500,
        pickable=True,
    )

    tooltip = {
        "html": "<b>{species}</b><br/>Shark ID: {shark_id}<br/>Depth: {depth_m} m<br/>Temp: {water_temp_C} °C<br/>Behavior: {behavior}",
        "style": {"backgroundColor": "white", "color": "black"}
    }

    view_state = pdk.ViewState(
        latitude=filtered_df["latitude"].mean(),
        longitude=filtered_df["longitude"].mean(),
        zoom=3,
        pitch=0,
    )

    r = pdk.Deck(layers=[scatter], initial_view_state=view_state, tooltip=tooltip)
    st.pydeck_chart(r)
else:
    st.warning("No data for selected filters.")

# --- Time-Series Plots ---
st.subheader("📈 Shark Depth & Temperature Trends")
if not filtered_df.empty:
    shark_selected = st.selectbox("Select a shark", options=filtered_df["shark_id"].unique())
    df_shark = filtered_df[filtered_df["shark_id"] == shark_selected].sort_values("datetime_utc")

    fig, ax = plt.subplots(2, 1, figsize=(8, 6), sharex=True)
    ax[0].plot(df_shark["datetime_utc"], df_shark["depth_m"], marker='o')
    ax[0].invert_yaxis()
    ax[0].set_ylabel("Depth (m)")
    ax[0].set_title(f"Depth Profile — {shark_selected}")

    ax[1].plot(df_shark["datetime_utc"], df_shark["water_temp_C"], color='orange', marker='o')
    ax[1].set_ylabel("Water Temp (°C)")
    ax[1].set_xlabel("Datetime")
    st.pyplot(fig)

# --- Real-Time NASA Data ---
st.subheader("🛰 Real-Time Ocean Data from NASA")
st.write("Fetching real-time SST and Chlorophyll-a for each shark position...")

NASA_API_KEY = "YOUR_NASA_API_KEY"  # Replace with your actual NASA API key

def fetch_nasa_data(lat, lon):
    """Fetch SST and Chlorophyll-a from NASA APIs (simplified example)"""
    try:
        sst_url = f"https://api.nasa.gov/planetary/earth/assets?lon={lon}&lat={lat}&dim=0.1&date=2025-10-22&api_key={NASA_API_KEY}"
        resp = requests.get(sst_url)
        sst = resp.json().get("temperature") if resp.status_code == 200 else None

        # For demo: use dataset's chlorophyll value
        chl = filtered_df.loc[(filtered_df['latitude']==lat) & (filtered_df['longitude']==lon), 'chlorophyll_mg_m3'].mean()
        return sst, chl
    except:
        return None, None

if not filtered_df.empty:
    for i, row in filtered_df.head(5).iterrows():  # Top 5 sharks for demo
        sst, chl = fetch_nasa_data(row['latitude'], row['longitude'])
        st.write(f"Shark **{row['shark_id']}** ({row['species']}) at ({row['latitude']}, {row['longitude']}):")
        st.write(f"- Sea Surface Temp: {sst} °C")
        st.write(f"- Chlorophyll-a: {chl} mg/m³")

# --- Download Filtered Data ---
st.subheader("💾 Download Filtered Data")
csv = filtered_df.to_csv(index=False).encode('utf-8')
st.download_button("Download CSV", csv, "filtered_shark_tracking.csv", "text/csv")
