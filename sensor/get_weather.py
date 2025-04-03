import requests
import time
import paho.mqtt.client as mqtt
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
load_dotenv()
BROKER = os.getenv("BROKER")
USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")
API_KEY = os.getenv("WEATHER_API_KEY")



client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

if BROKER_AUTHENTICATION:
    client.username_pw_set(USERNAME,password=PASSWORD)
client.connect(BROKER, PORT, KEEPALIVE)

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

