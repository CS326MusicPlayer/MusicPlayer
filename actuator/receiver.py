import paho.mqtt.client as mqtt
from pathlib import Path
from dotenv import load_dotenv
import os

# Constants
SLEEP_TIME = 5
QOS = 0
KEEPALIVE = 60
TOPIC = "emp/weather"
BROKER_AUTHENTICATION = True
PORT = 1883

# Note: these constants must be set if broker requires authentication
env_path = Path("../.env")
load_dotenv()
BROKER = os.getenv("BROKER")
USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")
API_KEY = os.getenv("WEATHER_API_KEY")

# Subscribe to topic "emp/weather"
def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        print(f'Connected to {BROKER} successfully.')
        # Subscribe to the topic
        client.subscribe(TOPIC, qos=QOS)
        print(f'Subscribed to {TOPIC}')
    else:
        print(f'Connection to {BROKER} failed. Return code={reason_code}')

def on_message(client, userdata, msg):
    print(f"Received message: {msg.payload.decode()}")

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
if BROKER_AUTHENTICATION:
    client.username_pw_set(USERNAME,password=PASSWORD)
client.on_connect = on_connect
client.on_message = on_message
client.connect(BROKER, PORT, KEEPALIVE)

try:
    client.loop_forever()
    pause()
except KeyboardInterrupt:
    client.disconnect()
    print('Done')

