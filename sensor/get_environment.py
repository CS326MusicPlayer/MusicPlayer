import requests
import time
import paho.mqtt.client as mqtt
from pathlib import Path
from dotenv import load_dotenv
import os
import json
from datetime import datetime

import busio
import digitalio
import board
import adafruit_mcp3xxx.mcp3008 as MCP
from adafruit_mcp3xxx.analog_in import AnalogIn
import smbus

# Constants
SLEEP_TIME = 5
LIGHT_SAMPLE_SIZE = 20

# MQTT Broker settings
QOS = 1
KEEPALIVE = 60
TOPIC = "emp/environment"
BROKER_AUTHENTICATION = True
PORT = 1883
TIME_MODE = "system_time"

# Temperature sensor settings
BUS = 1            # I2C bus number
ADDRESS = 0x48     # TC74 I2C bus address

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

def get_precipitation(lat, lon):
    weather_url = f"https://api.weatherapi.com/v1/current.json?key={API_KEY}&q={lat},{lon}&aqi=no"
    weather_response = requests.get(weather_url)
    weather_data = weather_response.json()
    current_weather = weather_data["current"]["condition"]["text"]
    print(f"Current weather: {current_weather}")
    
    if "rain" in current_weather.lower():
      print("It's raining!")
      return "rain"
    elif "snow" in current_weather.lower():
      print("It's snowing!")
      return "snow"
    elif "hail" in current_weather.lower():
      print("It's hailing!")
      return "hail"
    elif "drizzle" in current_weather.lower():
      print("It's drizzling!")
      return "drizzle"
    else:
      print("No precipitation detected.")
      return "none"
    
def get_sun_times(lat, lon):
    sun_url = f"https://api.weatherapi.com/v1/astronomy.json?key={API_KEY}&q={lat},{lon}"
    astro_response = requests.get(sun_url)
    astro_data = astro_response.json()["astronomy"]["astro"]
    sunrise = datetime.strptime(astro_data["sunrise"], "%I:%M %p")
    sunset = datetime.strptime(astro_data["sunset"], "%I:%M %p")

    formatted_sunrise = sunrise.strftime("%H:%M")
    formatted_sunset = sunset.strftime("%H:%M")
    
    print(f"Sunrise: {formatted_sunrise}, Sunset: {formatted_sunset}")
    
    return {"sunrise": formatted_sunrise, "sunset": formatted_sunset}

def get_temperature():
    temperature = bus.read_byte(ADDRESS)
    print(f"Temperature: {temperature}°C")
    return temperature

def get_light():
    sensor_readings = []
    for i in range(LIGHT_SAMPLE_SIZE):
        raw_value = chan.value >> 6
        sensor_readings.append(raw_value)
    
    average_value = sum(sensor_readings) / LIGHT_SAMPLE_SIZE
    print(f"Light level: {average_value}")
    return average_value


# Connect to I2C bus
bus = smbus.SMBus(BUS)

# Create the SPI bus
spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)

# create the cs (chip select)
cs = digitalio.DigitalInOut(board.D5)

# create the mcp object
mcp = MCP.MCP3008(spi, cs)

# create an analog input for CH0
chan = AnalogIn(mcp, MCP.P0)

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
      lat = location_data["lat"]
      lon = location_data["lon"]
      print(f"Location: {lat}, {lon}")

      print("\nChecking weather...")
      precipitation_status = get_precipitation(lat, lon)

      print("\nChecking sunset/sunrise...")
      sun_times = get_sun_times(lat, lon)

      print("\nReading temperature...")
      temperature = get_temperature()

      print("\nReading light...")
      light_level = get_light()
      
      weather_payload = {
          "precipitation_status": precipitation_status,
          "sunrise": sun_times["sunrise"],
          "sunset": sun_times["sunset"],
          "temperature": temperature,
          "light_level": light_level,
      }
      client.publish(TOPIC, json.dumps(weather_payload), QOS)

      time.sleep(SLEEP_TIME)
except KeyboardInterrupt:
  client.disconnect()
print("Done")

