import requests
import time
import paho.mqtt.client as mqtt
from pathlib import Path
from dotenv import load_dotenv
import os
import json

# Constants
SLEEP_TIME = 5
QOS = 1
KEEPALIVE = 60
TOPIC = "emp/environment"
BROKER_AUTHENTICATION = True
PORT = 1883

# Note: these constants must be set if broker requires authentication
env_path = Path("../.env")
load_dotenv()
BROKER = os.getenv("BROKER")
USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")
API_KEY = os.getenv("WEATHER_API_KEY")

def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        print(f'Connected to {BROKER} successfully.')
    else:
        print(f'Connection to {BROKER} failed. Return code={reason_code}')

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

if BROKER_AUTHENTICATION:
    client.username_pw_set(USERNAME,password=PASSWORD)
    print(f"Connecting to broker {BROKER} with authentication {USERNAME}:{PASSWORD}")
client.on_connect=on_connect
client.connect(BROKER, PORT, KEEPALIVE)

try:
  client.loop_start()
  # While loop with five second sleep
  while True:
      # Get latitude and longitude based on IP (provided implicitly in the fetch)
      location_url = "http://ip-api.com/json/?fields=lat,lon,query"
      location_response = requests.get(location_url)
      location_data = location_response.json()
      latitude = location_data["lat"]
      longitude = location_data["lon"]
      print(f"Location: {latitude}, {longitude}")

      print("Checking weather...")
      weather_url = f"https://api.weatherapi.com/v1/current.json?key={API_KEY}&q={latitude},{longitude}&aqi=no"
      weather_response = requests.get(weather_url)
      weather_data = weather_response.json()
      current_weather = weather_data["current"]["condition"]["text"]
      print(f"Current weather: {current_weather}")
      
      precipitation_status = "none"
      if "rain" in current_weather.lower():
        print("It's raining!")
        precipitation_status = "rain"
      elif "snow" in current_weather.lower():
        print("It's snowing!")
        precipitation_status = "snow"
      elif "hail" in current_weather.lower():
        print("It's hailing!")
        precipitation_status = "hail"
      elif "drizzle" in current_weather.lower():
        print("It's drizzling!")
        precipitation_status = "drizzle"
      else:
        print("No precipitation detected.")
      
      weather_payload = {
          "precipitation_status": precipitation_status,
          "day_status": "day"
      }
      client.publish(TOPIC, json.dumps(weather_payload), QOS)

      time.sleep(SLEEP_TIME)
except KeyboardInterrupt:
  client.disconnect()
print("Done")

