# subscriber for the real-time IoT analytics system

import json
import paho.mqtt.client as mqtt
# from csv_writer import write_sensor_data_csv  # Import the CSV writer function
from sqlite_writer import insert_sensor_data  # Import the sqlite writer function


# callback function when client connects to the broker
def on_connect(client, userdata, flags, rc):
    print(f"✅ Connected to MQTT Broker with result code {rc}")
    client.subscribe("iot/sensor/data")  # Subscribe to the topic for sensor data


# callback function when a message is received from the broker
def on_message(client, userdata, msg):
    try:
        payload = msg.payload.decode('utf-8')  # Decode the message payload
        sensor_data = json.loads(payload)  # Parse the JSON data
        print(f"📥 Received message on {msg.topic}: {sensor_data}")
        insert_sensor_data(sensor_data)  # Write the sensor data to a SQLite database

        # write_sensor_data_csv(sensor_data)  # Write the sensor data to a CSV instead
    
    except json.JSONDecodeError as e:
        print(f"❌ Error parsing message : {e}")


# MQTT broker configuration
MQTT_BROKER = 'localhost'  # Change to your MQTT broker address
MQTT_PORT = 1883

# MQTT client setup
client = mqtt.Client(protocol=mqtt.MQTTv311)  # Create a new MQTT client instance
client.on_connect = on_connect  # Assign the on_connect callback
client.on_message = on_message  # Assign the on_message callback

# Connect to the MQTT broker
client.connect(MQTT_BROKER, MQTT_PORT, 60)  # Connect to the MQTT broker

# Start the MQTT client loop to process network traffic and dispatch callbacks
client.loop_forever()  # Keep the client running to listen for messages
# Note: Make sure the MQTT broker is running and the publisher is sending data to the same topic.
def on_disconnect(client, userdata, rc):
    print("🚨 Disconnected from MQTT broker. Trying to reconnect...")
    while rc != 0:
        time.sleep(5)
        try:
            rc = client.reconnect()
        except:
            pass

client.on_disconnect = on_disconnect
