# storage writer for real-time IoT analytics

import csv
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(__file__))  # Get the directory of this script
FIELDNAMES = ['timestamp', 'device_id', 'room', 'temperature', 'humidity', 'co2']  # CSV field names
STORAGE_DIR = os.path.join(BASE_DIR, 'storage') # Storage directory for date-specific files

# Function to write sensor data to a CSV file

#ensure the storage directory exists
os.makedirs(STORAGE_DIR, exist_ok=True)

def get_file_path_for_today():
    """Generate a CSV file path based on current date."""
    today_str = datetime.now().strftime('%Y-%m-%d')
    return os.path.join(STORAGE_DIR, f'sensor_data_{today_str}.csv')

def write_sensor_data_csv(sensor_data):
    """Write sensor data to a date-specific CSV file."""
    file_path = get_file_path_for_today()

    # Write header only if file doesn't exist
    file_exists = os.path.exists(file_path)

    with open(file_path, mode='a', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=FIELDNAMES)
        if not file_exists:
            writer.writeheader()
        writer.writerow(sensor_data)


