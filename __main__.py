#!/usr/bin/env python3

"""A MQTT to InfluxDB Bridge

This script receives MQTT data and saves those to InfluxDB.

"""

import os
import re
from typing import NamedTuple

from dotenv import load_dotenv
import paho.mqtt.client as mqtt
from influxdb import InfluxDBClient

# Load environment variables from .env
load_dotenv()

INFLUXDB_HOST = os.getenv('INFLUXDB_HOST', 'localhost')
INFLUXDB_PORT = os.getenv('INFLUXDB_PORT', 8086)
INFLUXDB_USER = os.getenv('INFLUXDB_USER', '')
INFLUXDB_PASSWORD = os.getenv('INFLUXDB_PASSWORD', '')
INFLUXDB_DATABASE = os.getenv('INFLUXDB_DATABASE', 'home')
INFLUXDB_TIMEOUT = os.getenv('INFLUXDB_TIMEOUT', 10)

MQTT_HOST = os.getenv('MQTT_HOST', 'localhost')
MQTT_PORT = os.getenv('MQTT_PORT', 1883)
MQTT_USER = os.getenv('MQTT_USER', '')
MQTT_PASSWORD = os.getenv('MQTT_PASSWORD', '')
MQTT_TOPIC = os.getenv('MQTT_TOPIC', '/devices/+/controls/+')
MQTT_REGEX = '/devices/([^/]+)/controls/([^/]+)'
MQTT_CLIENT_ID = 'MQTTInfluxDBBridge'


message_count = 0  # Global variable to track message count
MAX_MESSAGES = 10  # Limit of messages to print

influxdb_client = InfluxDBClient(host=INFLUXDB_HOST, port=INFLUXDB_PORT, username=INFLUXDB_USER, password=INFLUXDB_PASSWORD, database=None, timeout=INFLUXDB_TIMEOUT)


class SensorData(NamedTuple):
    location: str
    measurement: str
    value: float


def on_connect(client, userdata, flags, rc):
    """Callback for when the client receives a CONNACK response from the server."""
    print(f"Connected to InfluxDB {INFLUXDB_HOST}:{INFLUXDB_PORT} database, result code {str(rc)}")
    client.subscribe(MQTT_TOPIC)
    print(f"Subscribed on MQTT broker {MQTT_HOST}:{MQTT_PORT} to topic '{MQTT_TOPIC}'")

def on_message(client, userdata, msg):
    """Callback for when a PUBLISH message is received from the server."""
    global message_count
    message_count += 1

    if message_count <= MAX_MESSAGES:
        print(f'Message {message_count}: {msg.topic} {msg.payload.decode("utf-8")}')

    # print(msg.topic + ' ' + str(msg.payload))
    sensor_data = _parse_mqtt_message(msg.topic, msg.payload.decode('utf-8'))
    if sensor_data is not None:
        _send_sensor_data_to_influxdb(sensor_data)


def _parse_mqtt_message(topic, payload):
    match = re.match(MQTT_REGEX, topic)
    if match:
        location = match.group(1)
        measurement = match.group(2)
        if measurement == 'status':
            return None
        return SensorData(location, measurement, float(payload))
    return None


def _send_sensor_data_to_influxdb(sensor_data):
    json_body = [
        {
            'measurement': sensor_data.measurement,
            'tags': {
                'location': sensor_data.location
            },
            'fields': {
                'value': sensor_data.value
            }
        }
    ]
    influxdb_client.write_points(json_body)


def _init_influxdb_database():
    databases = influxdb_client.get_list_database()
    if not any(db['name'] == INFLUXDB_DATABASE for db in databases):
        influxdb_client.create_database(INFLUXDB_DATABASE)
    influxdb_client.switch_database(INFLUXDB_DATABASE)


def main():
    _init_influxdb_database()

    mqtt_client = mqtt.Client(MQTT_CLIENT_ID)
    mqtt_client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message

    mqtt_client.connect(MQTT_HOST, MQTT_PORT)
    mqtt_client.loop_forever()


if __name__ == '__main__':
    print('MQTT to InfluxDB bridge')
    main()
