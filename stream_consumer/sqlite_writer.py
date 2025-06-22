# storage writer for real-time IoT analytics

import sqlite3
import os
from datetime import datetime


BASE_DIR = os.path.dirname(os.path.dirname(__file__))  # Get the directory of this script
DB_PATH = os.path.join(BASE_DIR, 'storage', 'sensor_data.db') # Storage directory for date-specific files

#ensure the storage directory exists
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

#create a table if it does not exist
def init_db():

    """Initialize the SQLite database and create the sensor_data table if it doesn't exist."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sensor_data (
                timestamp TEXT,
                device_id TEXT,
                room TEXT,
                temperature REAL,
                humidity REAL,
                co2 REAL
            )
        ''')
        conn.commit()

# Function to write sensor data to the SQLite database
def insert_sensor_data(sensor_data):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO sensor_data (timestamp, device_id, room, temperature, humidity, co2)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            sensor_data['timestamp'],
            sensor_data['device_id'],
            sensor_data['room'],
            sensor_data['temperature'],
            sensor_data['humidity'],
            sensor_data['co2']
        ))
        conn.commit()


# Initialize the database and create the table if it doesn't exist
init_db()
