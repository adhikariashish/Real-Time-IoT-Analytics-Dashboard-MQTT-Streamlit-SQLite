# dashboard for real-time IoT analytics

import streamlit as st
from datetime import datetime
import pandas as pd
import os
import time
from streamlit_autorefresh import st_autorefresh

# Set the title of the dashboard
st.set_page_config(page_title="IoT Sensor Dashboard", layout="wide")
# st_autorefresh(interval=10000, key="data_refresh")  # Refresh every 10 seconds

# Header for the dashboard
st.title("Real-Time IoT Home Environment Dashboard")
st.markdown("Live monitoring of room conditions with temperature, humidity, and CO₂ levels and their trends.")

# Function to load current data sensor data from CSV files

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))  # Get the directory of this script
STORAGE_DIR = os.path.join(BASE_DIR, 'storage')  # Storage directory for date-specific files
today_str = datetime.now().strftime('%Y-%m-%d')
csv_file_path = os.path.join(STORAGE_DIR, f'sensor_data_{today_str}.csv')
    
# check for the existence of the CSV file
if not os.path.exists(csv_file_path):
    st.warning(f"No sensor data available yet for today. Waiting for sensor data to be published...")
    st.stop()

df = pd.read_csv(csv_file_path)

if df.empty:
    st.warning("No sensor data available yet. Waiting for sensor data to be published...")
    st.stop()

# 

else:
    # Load the sensor data from the CSV file
    df = pd.read_csv(csv_file_path)

    # show timestamp of the last update
    last_updated = df['timestamp'].iloc[-1] if not df.empty else "No data available"
    st.caption(f"📅  Last update: {last_updated}")


    # layout for the dashboard
    rooms = df['room'].unique()
    tabs = st.tabs([room for room in rooms])

    for i, room in enumerate(rooms):
        with tabs[i]:
            room_df = df[df['room'] == room].tail(100)  # Get the last 10 entries for the room

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("🌡️ Temperature (°C)", f"{room_df['temperature'].iloc[-1]:.2f}")
                st.line_chart(room_df[['timestamp', 'temperature']].set_index('timestamp'))

            with col2:
                st.metric("💧 Humidity (%)", f"{room_df['humidity'].iloc[-1]:.2f}")
                st.line_chart(room_df[['timestamp', 'humidity']].set_index('timestamp'))

            with col3:
                st.metric("🟫 CO₂ (ppm)", f"{room_df['co2'].iloc[-1]:.2f}")
                st.line_chart(room_df[['timestamp', 'co2']].set_index('timestamp'))
