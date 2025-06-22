#data simulation for the real-time IoT analytics project

import json
import random
import time
import paho.mqtt.client as mqtt
from datetime import datetime

# MQTT broker configuration
MQTT_BROKER = 'localhost'  # Change to your MQTT broker address
MQTT_PORT = 1883
MQTT_TOPIC = 'iot/sensor/data'

# MQTT client setup
client = mqtt.Client()
client.connect(MQTT_BROKER, MQTT_PORT, 60)


# similated rooms 
rooms = ['living_Room','kitchen', 'bedroom', 'garage']

# simulated sensors
def generate_sensor_data(room):
    """Generate simulated sensor data for a given room."""
    temperature = round(random.uniform(15.0, 30.0), 2)  # Temperature in Celsius
    humidity = round(random.uniform(30.0, 70.0), 2)      # Humidity in percentage
    co2 = round(random.uniform(400, 1000), 2)            # CO2 level in ppm
    timestamp = datetime.now().isoformat()               # Current timestamp

    sensor_data = {
        "device_id": f"sensor_{room}",
        "room": room,
        "timestamp": timestamp,
        "temperature": temperature,
        "humidity": humidity,
        "co2": co2
    }    
    return sensor_data


while True:
    for room in rooms:
        sensor_data = generate_sensor_data(room)
        payload = json.dumps(sensor_data)
        
        # Publish the sensor data to the MQTT topic
        client.publish(MQTT_TOPIC, payload)
        print(f"Published data: {payload} to topic: {MQTT_TOPIC}")
    
    # Sleep for a while before the next iteration
    time.sleep(20)  # Sleep for 20 seconds before the next round of data generation
