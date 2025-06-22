#import 
import streamlit as st
import uuid
import plotly.express as px
import pandas as pd
from plotly.subplots import make_subplots
import plotly.graph_objects as go
from datetime import datetime, timedelta
from alert import detect_alerts, log_alerts_to_db
import sqlite3

# KPI card function 
def kpi_card(label, value, color="#2ECC71"):
    card_id = f"kpi-card-{uuid.uuid4().hex[:6]}"  # unique ID per card

    st.markdown(f"""
        <style>
        .{card_id} {{
            padding: 1rem;
            background-color: {color};
            border-radius: 12px;
            text-align: center;
            color: white;
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }}
        .{card_id}:hover {{
            transform: translateY(-5px);
            box-shadow: 0 8px 16px rgba(0,0,0,0.3);
        }}
        </style>

        <div class="{card_id}">
            <div style="font-size: 18px; margin-bottom: 0.25rem;">{label}</div>
            <div style="font-size: 26px; font-weight: bold;">{value}</div>
        </div>
    """, unsafe_allow_html=True)

def line_chart(df):
    """Create subplots for Temp, Humidity, CO2 with separate y-axes and downsampling."""
    df['timestamp'] = pd.to_datetime(df['timestamp'], format='mixed')
    df.set_index('timestamp', inplace=True)

    # Only keep numeric columns for resampling
    numeric_cols = ['temperature', 'humidity', 'co2']
    resampled_df = df[numeric_cols].resample('15min').mean()
    resampled_df.reset_index(inplace=True)

    # Plotting
    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.1,
        subplot_titles=("🌡️ Temperature", "💧 Humidity", "🏭 CO₂")
    )

    fig.add_trace(go.Scatter(x=resampled_df['timestamp'], y=resampled_df['temperature'],
                             mode='lines+markers', name='Temperature (°C)', line=dict(color='tomato')),
                  row=1, col=1)

    fig.add_trace(go.Scatter(x=resampled_df['timestamp'], y=resampled_df['humidity'],
                             mode='lines+markers', name='Humidity (%)', line=dict(color='royalblue')),
                  row=2, col=1)

    fig.add_trace(go.Scatter(x=resampled_df['timestamp'], y=resampled_df['co2'],
                             mode='lines+markers', name='CO₂ (ppm)', line=dict(color='green')),
                  row=3, col=1)

    fig.update_layout(
        height=780,
        # title="📈 Environmental Trends (15-Minute Intervals)",
        showlegend=False,
        margin=dict(t=60, b=40),
    )

    return fig

def generate_pie_chart(df,room_label):
    # Load alert data once
    conn = sqlite3.connect("alert_log.db")
    alert_df = pd.read_sql_query("SELECT * FROM alert_log", conn)
    conn.close()

    alert_df['timestamp'] = pd.to_datetime(alert_df['timestamp'], errors='coerce')
    alert_df = alert_df[alert_df['timestamp'] > datetime.now() - timedelta(hours=6)]

    if alert_df.empty:
        return px.pie(title="No recent alerts to display")

    if room_label == "All":
        # Pie by room
        data = alert_df['room'].value_counts().reset_index()
        data.columns = ['Room', 'Alerts']
        fig = px.pie(data, names='Room', values='Alerts', title="Alert Distribution by Room")

    else:
        # Pie by alert type for a specific room
        room_map = {
            "Living Room": "living_Room",
            "Kitchen": "kitchen",
            "Bedroom": "bedroom",
            "Garage": "garage"
        }
        db_room = room_map.get(room_label)
        room_df = alert_df[alert_df['room'] == db_room]

        if room_df.empty:
            return px.pie(title=f"No alerts in {room_label}")

        data = room_df['alert_type'].value_counts().reset_index()
        data.columns = ['Alert Type', 'Count']
        fig = px.pie(data, names='Alert Type', values='Count', title=f"{room_label} – Alert Type Share")


    fig.update_traces(textinfo='percent+label', hole=0.4)
    fig.update_layout(height = 450)
    return fig

def pie_chart(df,room_label, key_suffix=""):
    pie_chart = generate_pie_chart(df, room_label)

    # Styled container
    with st.container():
        st.subheader("Sensor Metric Contribution")
        st.markdown("<div style='height=400; margin-bottom: 0.5rem;'>", unsafe_allow_html=True)
        st.plotly_chart(pie_chart, use_container_width=True,key=f"pie_chart_{room_label}_{key_suffix}")
        st.markdown("</div>", unsafe_allow_html=True)

def mood_emoji(score):
    if score >= 90:
        return "😌"
    elif score >= 75:
        return "🙂"
    elif score >= 60:
        return "😐"
    elif score >= 40:
        return "😤"
    else:
        return "🫠"

def generate_bar_chart(df,room_label):

    df = df.reset_index()

    # Shared color map
    room_color_map = {
        "kitchen": "#1f77b4",
        "garage": "#66b2ff",
        "living_Room": "#ff6666",
        "bedroom": "#ff9999"
    }

    # Compute mood score
    df["temperature_f"] = df["temperature"] * 9/5 + 32
    df["mood_score"] = 100 - (
        abs(df["temperature_f"] - 72) * 1.2 +
        abs(df["humidity"] - 40) * 0.8 +
        abs(df["co2"] - 450) * 0.05
    )

    def mood_emoji(score):
        if score >= 90:
            return "😌"
        elif score >= 75:
            return "🙂"
        elif score >= 60:
            return "😐"
        elif score >= 40:
            return "😤"
        else:
            return "🫠"
    
    room_map = {
        "Living Room": "living_Room",
        "Kitchen": "kitchen",
        "Bedroom": "bedroom",
        "Garage": "garage"
    }

    if room_label == "All":
        mood_df = df.groupby("room")["mood_score"].mean().reset_index()
        mood_df = mood_df.sort_values("mood_score", ascending=True)
        mood_df["label"] = mood_df["mood_score"].round(1).astype(str) + " " + mood_df["mood_score"].apply(mood_emoji)

        fig = go.Figure(go.Bar(
            x=mood_df["mood_score"],
            y=mood_df["room"],
            orientation='h',
            text=mood_df["label"],
            textposition="outside",
            marker=dict(
                color=[room_color_map.get(r, "#888") for r in mood_df["room"]],
            )
        ))

        fig.update_layout(
            title="Room Mood Score (Comfort Index)",
            xaxis=dict(range=[0, 100], title="Mood Score"),
            yaxis=dict(title="Room", autorange="reversed"),
            height=400,
            margin=dict(l=120, r=60, t=60, b=40),
        )

    else:

        room_df = df[df["room"] == room_map[room_label]].sort_values("timestamp").tail(8)
        if room_df.empty:
            return go.Figure()  # Empty fallback

        room_df["label"] = room_df["mood_score"].round(1).astype(str) + " " + room_df["mood_score"].apply(mood_emoji)
        room_df["time"] = room_df["timestamp"].dt.strftime("%H:%M:%S")

        fig = go.Figure(go.Bar(
            x=room_df["mood_score"],
            y=room_df["time"],
            orientation='h',
            text=room_df["label"],
            textposition="outside",
            marker=dict(
                color=room_color_map.get(room_label, "#888"),
            )
        ))

        fig.update_layout(
            title=f"Mood Score Trend - {room_label}",
            xaxis=dict(range=[0, 100], title="Mood Score"),
            yaxis=dict(title="Time", autorange="reversed"),
            height=400,
            margin=dict(l=120, r=60, t=60, b=40),
        )

    return fig


def bar_chart(df, room_label, key_suffix = ""):
    bar_chart = generate_bar_chart(df, room_label)
    
    # Styled container
    with st.container():
        st.markdown("<div style='border-radius:10px; height=300; margin-bottom: 1.5rem;'>", unsafe_allow_html=True)
        st.plotly_chart(bar_chart, use_container_width=True, key=f"{key_suffix}_mood_chart")
        st.markdown("</div>", unsafe_allow_html=True)


def render_dash_tab(df, room_label, key_prefix):
    # === Alert ===
    alerts = detect_alerts(df)
    if alerts:
        alert_df = pd.DataFrame(alerts, columns=["timestamp", "room", "alert_type", "value"])
        log_alerts_to_db(alert_df)  # ✅ Append to database

    # === Main Container ===
    with st.container():
        colA, colB = st.columns([2,1], gap = 'large') # as such Column A (2/3), and Column B (1/3) size

        # Column A => KPI and line chart 
        # === KPI Section ===
        with colA:
            col1, col2, col3, col4 = st.columns(4)

            with col1: kpi_card("🌡️ Avg. Temp (°C) ", f"{df['temperature'].mean():.2f}", "#FF6B6B")
            with col2: kpi_card("💧 Avg. Humidity (%)", f"{df['humidity'].mean():.2f}", "#1E90FF")
            with col3: kpi_card("🏭 Max CO₂ (ppm)", f"{df['co2'].max():.2f}", "#FFA500")
            with col4: kpi_card("📈 Total Records", f"{len(df)}", "#2ECC71")

            st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
        # === Line Chart Section ===    
            st.markdown("#### 📈 Environment Metrics Trend (Temp, Humidity, CO₂)")
            linechart = line_chart(df)
            st.plotly_chart(linechart, use_container_width=True)


        with colB:
            # === Pie Chart ===
            pie_chart(df, room_label, key_suffix = key_prefix)

            # === Bar Chart ===
            bar_chart(df, room_label, key_suffix = key_prefix)