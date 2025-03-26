import requests
import time
import paho.mqtt.client as mqtt
from dotenv import load_dotenv
import os

# Replace with your location (or use GPS module if available)
LAT = 42.0971
LONG = -75.9117

# Other Constants
SLEEP_TIME = 5
QOS = 0
KEEPALIVE = 60
TOPIC = "emp/weather"
BROKER_AUTHENTICATION = True
PORT = 1883

# Note: these constants must be set if broker requires authentication
load_dotenv()
BROKER = os.getenv("BROKER")
USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")




client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

if BROKER_AUTHENTICATION:
    client.username_pw_set(USERNAME,password=PASSWORD)
client.connect(BROKER, PORT, KEEPALIVE)

point_info_url = f"https://api.weather.gov/points/{LAT},{LONG}"

response = requests.get(point_info_url)
data = response.json()

# Extract the nearest station URL
stations_url = data["properties"]["observationStations"]

# Step 2: Get the first (nearest) station
stations_response = requests.get(stations_url)
stations_data = stations_response.json()

# Extract the station ID
nearest_station = stations_data["features"][0]["properties"]["stationIdentifier"]
print(f"Nearest Weather Station: {nearest_station}")

# While loop with five second sleep
while True:
    print("Checking weather...")
    weather_url = f"https://api.weather.gov/stations/{nearest_station}/observations/latest"
    weather_response = requests.get(weather_url)
    weather_data = weather_response.json()
    current_weather = weather_data["properties"]["textDescription"]
    if "rain" in current_weather.lower():
      print("It's raining!")
      client.publish(TOPIC, "rain", QOS)
    elif "snow" in current_weather.lower():
      print("It's snowing!")
      client.publish(TOPIC, "snow", QOS)
    elif "hail" in current_weather.lower():
      print("It's hailing!")
      client.publish(TOPIC, "hail", QOS)
    elif "drizzle" in current_weather.lower():
      print("It's drizzling!")
      client.publish(TOPIC, "drizzle", QOS)
    else:
      print("No precipitation detected.")
    time.sleep(SLEEP_TIME)

