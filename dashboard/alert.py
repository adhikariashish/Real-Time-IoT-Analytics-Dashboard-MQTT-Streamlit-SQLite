import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import streamlit as st

def detect_alerts(df):

    ALERT_THRESHOLDS = {
        "temperature": {"min": 16, "max": 29},   # °C
        "humidity": {"min": 30, "max": 69},      # %
        "co2": {"max": 980}                      # ppm
    }

    alerts = []

    for index, row in df.iterrows():
        ts = row['timestamp']
        room = row['room']
        
        if row['temperature'] < ALERT_THRESHOLDS['temperature']['min']:
            alerts.append((ts, room, "Low Temperature", row['temperature']))
        elif row['temperature'] > ALERT_THRESHOLDS['temperature']['max']:
            alerts.append((ts, room, "High Temperature", row['temperature']))

        if row['humidity'] < ALERT_THRESHOLDS['humidity']['min']:
            alerts.append((ts, room, "Low Humidity", row['humidity']))
        elif row['humidity'] > ALERT_THRESHOLDS['humidity']['max']:
            alerts.append((ts, room, "High Humidity", row['humidity']))

        if row['co2'] > ALERT_THRESHOLDS['co2']['max']:
            alerts.append((ts, room, "High CO₂", row['co2']))
    
    return alerts
    
def log_alerts_to_db(alert_df: pd.DataFrame):
    if alert_df.empty:
        return

    conn = sqlite3.connect("alert_log.db")
    existing_df = pd.read_sql_query("SELECT timestamp, room, alert_type, value FROM alert_log", conn)

    # Convert timestamps
    existing_df['timestamp'] = pd.to_datetime(existing_df['timestamp'], errors='coerce')
    alert_df['timestamp'] = pd.to_datetime(alert_df['timestamp'], errors='coerce')

    # Deduplicate: remove alerts already in DB
    merged = alert_df.merge(existing_df, on=["timestamp", "room", "alert_type", "value"], how="left", indicator=True)
    new_alerts = merged[merged['_merge'] == 'left_only'].drop(columns=['_merge'])

    if not new_alerts.empty:
        new_alerts.to_sql("alert_log", conn, if_exists="append", index=False)

    conn.close()


def get_recent_alert_count(hours: int = 2) -> int:
    try:
        conn = sqlite3.connect("alert_log.db")
        df = pd.read_sql_query("SELECT timestamp FROM alert_log", conn)
        conn.close()
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        recent = df[df['timestamp'] > datetime.now() - timedelta(hours=hours)]
        return len(recent)
    except Exception:
        return 0

def get_all_alerts():
    try:
        conn = sqlite3.connect("alert_log.db")
        df_alerts = pd.read_sql_query("SELECT * FROM alert_log ORDER BY timestamp DESC LIMIT 100", conn)
        conn.close()

        df_alerts['timestamp'] = pd.to_datetime(df_alerts['timestamp'], errors='coerce')

        if df_alerts.empty:
            st.success("✅ No alerts recorded yet.")
        else:
            grouped = df_alerts.groupby("room")
            for room, group in grouped:
                with st.expander(f"📍 {room.capitalize()} — {len(group)} alerts", expanded=False):
                    for _, row in group.iterrows():
                        st.markdown(f"""
                            <div style='padding: 0.4rem 0.75rem; background-color: #fff3f3; border-left: 6px solid #e74c3c;
                                        margin-bottom: 0.5rem; border-radius: 6px; font-size: 0.95rem;'>
                                <b>{row['alert_type']}</b> — 
                                <span style='color:#c0392b'>{row['value']:.2f}</span> at 
                                <code>{pd.to_datetime(row['timestamp']).strftime('%Y-%m-%d %H:%M')}</code>
                            </div>
                        """, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"⚠️ Failed to load alerts: {e}")