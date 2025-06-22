import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import plotly.express as px
from streamlit_autorefresh import st_autorefresh
import uuid

#importing components
from components import kpi_card, line_chart, pie_chart, bar_chart, render_dash_tab
from components import render_dash_tab
from components import detect_alerts
from alert import get_recent_alert_count, get_all_alerts

# Configure page layout
st.set_page_config(page_title="IoT Sensor Dashboard", layout="wide")

# Enable auto-refresh every 30 seconds
st_autorefresh(interval=30000, key="auto-refresh")

# Database path
DB_PATH = "../storage/sensor_data.db"

# Load data from DB
@st.cache_data(ttl=30)
def load_sensor_data(room=None, hours=2):
    conn = sqlite3.connect(DB_PATH)
    end_time = datetime.now()
    start_time = end_time - timedelta(hours = hours)

    query = """
        SELECT * FROM sensor_data
        WHERE datetime(timestamp) >= datetime(?) AND datetime(timestamp) <= datetime(?)
    """
    params = [start_time.isoformat(), end_time.isoformat()]

    if room and isinstance(room, str):
        query += " AND room = ?"
        params.append(room)

    df = pd.read_sql_query(query, conn, params=params)
    conn.close()

    if not df.empty:
        df['timestamp'] = pd.to_datetime(df['timestamp'], format='mixed')
    return df

# === HEADER ===

st.markdown("""
    <style>
    .dashboard-header {
        background: #F9FAFB;
        border-left: 6px solid #2D9CDB;
        border-radius: 10px;
        margin-top: -1rem;
        margin-bottom: 1.5rem;
        color: #333;
        box-shadow: 0 2px 6px rgba(0,0,0,0.05);
    }
    .dashboard-header h1 {
        font-size: 1.8rem;
        font-weight: 600;
        margin: 0;
    }
     /* Target the full tab container */
    div[data-testid="stTabs"] div[role="tablist"] > button {
        background-color: transparent;
        padding: 0.75rem 1.25rem;
        margin-right: 0.25rem;
        border: none;
        border-radius: 8px 8px 0 0;
        color: #444;
        font-size: 20px !important ;  /* ✅ Around 21px - readable but doesn't break layout */
        font-weight: 600;
        line-height: 1.4;
        transition: all 0.2s ease-in-out;
        flex-shrink: 0;
    }

    /* Style for the selected (active) tab */
    div[data-testid="stTabs"] div[role="tablist"] > button[aria-selected="true"] {
        background-color: #e6f7ff;
        color: #007acc;
        font-size: 2.05rem;
        font-weight: 600;
        box-shadow: 0 -3px 6px rgba(0, 0, 0, 0.05);
        border: 1px solid #e6f7ff;
        border-bottom: none;

    </style>

    <div class="dashboard-header">
        <h1>🏠 Real-Time IoT Environment Dashboard</h1>
    </div>
""", unsafe_allow_html=True)

# === Tabs ==== 
tab_all, tab_living, tab_kitchen, tab_bedroom, tab_garage, tab_data, tab_alert = st.tabs(
    ["🏠 All Rooms",
    "🛋️ Living Room",
    "🍳 Kitchen",
    "🛏️ Bedroom",
    "🚗 Garage",
    "📋 All Data",
    f"🚨 Alerts ({get_recent_alert_count()} active)"]
)

def render_room_tab(room_label: str, key_prefix: str):
    emoji_map = {
        "All": "🏠",
        "Living Room": "🛋️",
        "Kitchen": "🍳",
        "Bedroom": "🛏️",
        "Garage": "🚗"
    }
    room_map = {
        "Living Room": "living_Room",
        "Kitchen": "kitchen",
        "Bedroom": "bedroom",
        "Garage": "garage"
    }

    # ✅ Get emoji 
    emoji = emoji_map.get(room_label, "📊")

    with st.container():
        colL, colDt, colD = st.columns([8,1,1])

        with colL:
            st.markdown(f"### {emoji} {room_label} — Sensor Trend")

        with colDt:
            # 📅 Date picker
            selected_date = st.date_input(f" {emoji} Choose a date", datetime.today().date(), key=f"{key_prefix}_date")
        with colD:
            # ⏱️ Hour range selector
            hours_options = [1, 2, 4, 6, 8, 12, 18, 24]
            hours_back = st.selectbox("⏱️ Hours", options=hours_options, index=1, key=f"{key_prefix}_hours")

    # 🧮 Combine selected date with time now to form cutoff
    selected_datetime = datetime.combine(selected_date, datetime.now().time())
    cutoff_time = selected_datetime - timedelta(hours=hours_back)

    # 🧾 Load & filter data
    rooms = None if room_label == "All" else room_map.get(room_label)
    df_all = load_sensor_data(room=rooms, hours=24)  # Load all 24 hrs of data
    df_filtered = df_all[df_all['timestamp'] >= cutoff_time].copy()

    if df_filtered.empty:
        st.warning("No data available for the selected date and time range.")
        return

    # 📊 Render the tab
    render_dash_tab(df_filtered, room_label, key_prefix)

def render_all_data_tab():
    st.markdown("## 📋 All Sensor Data (Latest 50)")

    # Load last 2–4 hours to cover recent events (can tweak)
    df_all = load_sensor_data(room=None, hours=4)

    if df_all.empty:
        st.warning("No recent data available.")
        return

    df_display = df_all.sort_values(by="timestamp", ascending=False).head(50)

    # Optional: reformat timestamp nicely
    df_display['timestamp'] = pd.to_datetime(df_display['timestamp']).dt.strftime('%Y-%m-%d %H:%M:%S')

    # Optional: reorder columns
    display_cols = ['timestamp', 'room', 'temperature', 'humidity', 'co2']
    df_display = df_display[display_cols]

    st.dataframe(df_display, use_container_width=True, hide_index=True)


with tab_all:
    render_room_tab("All", "All")

with tab_living:
    render_room_tab("Living Room", "living_Room")

with tab_kitchen:
    render_room_tab("Kitchen", "kitchen")

with tab_bedroom:
    render_room_tab("Bedroom", "bedroom")

with tab_garage:
    render_room_tab("Garage", "garage")

with tab_data:
    render_all_data_tab()

with tab_alert:
    st.markdown("### 🚨 Recent Sensor Alerts")
    get_all_alerts()



















# # === Main Container ===
# with st.container():
#     colA, colB = st.columns([2,1], gap = 'large') # as such Column A (2/3), and Column B (1/3) size

#     # Column A => KPI and line chart 

#     # === KPI Section ===
#     with colA:
#         col1, col2, col3, col4 = st.columns(4)

#         with col1: kpi_card("🌡️ Avg. Temp (°C) ", f"{df['temperature'].mean():.2f}", "#FF6B6B")
#         with col2: kpi_card("💧 Avg. Humidity (%)", f"{df['humidity'].mean():.2f}", "#1E90FF")
#         with col3: kpi_card("🏭 Max CO₂ (ppm)", f"{df['co2'].max():.2f}", "#FFA500")
#         with col4: kpi_card("📈 Total Records", f"{len(df)}", "#2ECC71")

#         st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)

#     # === Line Chart Section ===    
#         st.markdown("#### 📈 Environment Metrics Trend (Temp, Humidity, CO₂)")
#         linechart = line_chart(df)
#         st.plotly_chart(linechart, use_container_width=True)
        

#     with colB:
#         # === Pie Chart ===
#         pie_chart(df)

#         # === Bar Chart ===
#         bar_chart(df)












# st.markdown(f"📍 Monitoring **{selected_room}** over the last **{hours_back} hours** on {selected_date.strftime('%B %d, %Y')}.")

# # ======================
# # UI SECTION 2: KPIs
# # ======================

# st.subheader("📌 Key Metrics Overview")

# kpi1, kpi2, kpi3, kpi4 = st.columns(4)

# with kpi1: kpi_card("🌡️ Avg. Temperature (°C) ", f"{df['temperature'].mean():.2f}", "#FF6B6B")
# with kpi2: kpi_card("💧 Avg. Humidity (%)", f"{df['humidity'].mean():.2f}", "#1E90FF")
# with kpi3: kpi_card("🏭 Max CO₂ (ppm)", f"{df['co2'].max():.2f}", "#FFA500")
# with kpi4: kpi_card("📈 Total Records", f"{len(df)}", "#2ECC71")


# # implementing tabs for the plots and tables
# # ======================
# # UI SECTION 3: PLOTS
# # ======================
# st.subheader("📈 Sensor Readings Over Time")
# df = df.sort_values("timestamp")

# with st.container():
#     fig_temp = px.line(df, x="timestamp", y="temperature", title="🌡️ Temperature Over Time", markers=True)
#     st.plotly_chart(fig_temp, use_container_width=True)

# with st.container():
#     fig_humidity = px.line(df, x="timestamp", y="humidity", title="💧 Humidity Over Time", markers=True)
#     st.plotly_chart(fig_humidity, use_container_width=True)

# with st.container():
#     fig_co2 = px.line(df, x="timestamp", y="co2", title="🏭 CO₂ Levels Over Time", markers=True)
#     st.plotly_chart(fig_co2, use_container_width=True)

# # ======================
# # UI SECTION 4: TABLE + EXPORT
# # ======================
# st.subheader("🧾 Latest Sensor Data")

# st.dataframe(df.tail(10), use_container_width=True)

# st.download_button(
#     label="⬇️ Download Full Data as CSV",
#     data=df.to_csv(index=False).encode("utf-8"),
#     file_name="filtered_sensor_data.csv",
#     mime="text/csv"
# )
