# This script reads environmental data from a Raspberry Pi and publishes it to an MQTT broker.
# Jason Chew (jgc23), Daniel Kim (jk254)

# Code to use light sensor derived from:
# https://github.com/dschuurman/cs326/blob/main/lab4/a2d.py

# Code to use temperature sensor derived from:
# https://github.com/dschuurman/cs326/blob/main/lab8/temptest.py

# Code to use LED with PWM derived from:
# https://github.com/dschuurman/cs326/blob/main/lab5/pwm-led.py

# Code to use MQTT with certs derived from:
# https://github.com/dschuurman/cs326/blob/main/lab10/mqtt-cam-led.py
# and
# https://github.com/dschuurman/cs326/blob/main/lab7/mqtt-button.py

# General Libraries
import requests
import time
import paho.mqtt.client as mqtt
from pathlib import Path
from dotenv import load_dotenv
import os
import json
from datetime import datetime
import math

# Pi I/O Libraries
import busio
import digitalio
import board
import adafruit_mcp3xxx.mcp3008 as MCP
from adafruit_mcp3xxx.analog_in import AnalogIn
import smbus
from gpiozero import PWMLED

# To request a reading from Raspberry Pi with PI_ID:
# mosquitto_pub -h <BROKER> -P <PASS> -u <USER> -t "emp/operations" -m '{"target": PI_ID}'

# Constants
env_path = Path("../.env")
load_dotenv()

# MQTT Broker settings
QOS = 1     # Deliver at least once
KEEPALIVE = 60
PUBLISH_TOPIC = "emp/environment"
SUBSCRIPTION_TOPIC = "emp/operations"
BROKER = os.getenv("BROKER")
PORT = int(os.getenv("PORT"))
BROKER_AUTHENTICATION = True
# Note: these constants must be set if broker requires authentication
USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")
CERTS = os.getenv("CERTS")

# Temperature sensor settings
BUS = 1            # I2C bus number
ADDRESS = 0x48     # TC74 I2C bus address

# Light sensor
LIGHT_SAMPLE_SIZE = 20  # Number of samples to take for each light reading
MIN_BRIGHTNESS = 0.01   # Minimum brightness for LED indicator
MAX_LOG_LIGHT = math.log10(65535)   # Maximum possible log-scaled light reading
LIGHT_FLOOR = 1     # Floor to avoid log of 0-values
MCP_CHANNEL = MCP.P0
MCP_PIN = board.D5

# LED settings
LED_PIN = 16

# Identifers
API_KEY = os.getenv("WEATHER_API_KEY")
PID = os.getenv("PID")  # Internal ID to distinguish from other Pis

# Original code restructured into a class by GitHub Copilot
class EnvironmentSensor:
    def __init__(self):
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

        if BROKER_AUTHENTICATION:
            self.client.username_pw_set(USERNAME, password=PASSWORD)
            self.client.tls_set(CERTS)
            print(f"Connecting to broker {BROKER} with authentication {USERNAME}:{PASSWORD}")

        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.connect(BROKER, PORT, KEEPALIVE)

        # Temperature bus setup
        self.bus = smbus.SMBus(BUS)

        # Light sensor setup
        self.spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)
        # Create the cs (chip select)
        self.cs = digitalio.DigitalInOut(MCP_PIN)
        # Create the mcp object
        self.mcp = MCP.MCP3008(self.spi, self.cs)
        # Create an analog input for CH0
        self.chan = AnalogIn(self.mcp, MCP_CHANNEL)

        # Set up LED
        self.led = PWMLED(LED_PIN)

        # MQTT payload attributes
        self.precipitation_status = None
        self.sunrise = None
        self.sunset = None
        self.timezone = None
        self.temperature = None
        self.light_level = None


    def on_connect(self, client, userdata, flags, reason_code, properties):
        if reason_code == 0:
            print(f'Connected to {BROKER} successfully.')

            # Listen for incoming requests for weather data
            client.subscribe(SUBSCRIPTION_TOPIC, QOS)
            print(f'Subscribed to {SUBSCRIPTION_TOPIC}')

        else:
            print(f'Connection to {BROKER} failed. Return code={reason_code}')


    def on_message(self, client, userdata, msg):
        # Parse message to determine if data is being requested from this Pi
        # JSON parsing/error handling generated with Copilot assistance
        try:
            msg_payload = json.loads(msg.payload.decode())

            # Publish weather data if msg has "discovery" flag or targets this Pi
            if msg_payload.get("discovery") or msg_payload.get("target") == PID:
                self.broadcast_weather()

        except json.JSONDecodeError:
            print("Failed to decode JSON message.")
            print(f"Message payload: {msg.payload.decode()}")


    def broadcast_weather(self):
        raw_light = self.chan.value

        # Scale light reading to logarithmic human perception
        # Log of value with floor avoids log(0) (suggestion from Copilot)
        log_light = math.log10(max(LIGHT_FLOOR, raw_light))

        # Normalize log brightness to proportion in range [0, 1]
        normalized_log_light = log_light / MAX_LOG_LIGHT

        # Turn on LED while getting/transmitting data
        # Use normalized log brightness if > MIN_BRIGHTNESS, else MIN_BRIGHTNESS
        self.led.value = max(normalized_log_light, MIN_BRIGHTNESS)

        # Get latitude and longitude based on IP
        location_url = "http://ip-api.com/json/?fields=lat,lon,query"
        location_response = requests.get(location_url)
        location_data = location_response.json()
        lat = location_data["lat"]
        lon = location_data["lon"]
        print(f"Location: {lat}, {lon}")

        print("\nChecking weather...")
        self.get_precipitation(lat, lon)

        print("\nChecking time data...")
        self.get_time_data(lat, lon)

        print("\nReading temperature...")
        self.get_temperature()

        print("\nReading light...")
        self.get_light()

        weather_payload = {
            "pid": PID,
            "precipitation_status": self.precipitation_status,
            "sunrise": self.sunrise,
            "sunset": self.sunset,
            "timezone": self.timezone,
            "temperature": self.temperature,
            "light_level": self.light_level,
            "timestamp": time.time()
        }
        self.client.publish(PUBLISH_TOPIC, json.dumps(weather_payload), QOS)

        # Turn off LED once data is transmitted
        self.led.value = 0

    def start(self):
        try:
            self.client.loop_forever()

        except KeyboardInterrupt:
            self.client.disconnect()
            print("Done")

    # The methods below were extracted from previous code with Copilot's help

    # Return precipitation state ∈ {"none", "drizzle", "hail", "rain", "snow"}
    # For given location lat, lon
    def get_precipitation(self, lat, lon):
        weather_url = f"https://api.weatherapi.com/v1/current.json?key={API_KEY}&q={lat},{lon}&aqi=no"
        weather_response = requests.get(weather_url)
        weather_data = weather_response.json()
        current_weather = weather_data["current"]["condition"]["text"]
        print(f"Current weather: {current_weather}")

        # The following checks were written with Copilot assistance
        if "rain" in current_weather.lower():
            print("It's raining!")
            self.precipitation_status = "rain"
        elif "snow" in current_weather.lower():
            print("It's snowing!")
            self.precipitation_status = "snow"
        elif "hail" in current_weather.lower():
            print("It's hailing!")
            self.precipitation_status = "hail"
        elif "drizzle" in current_weather.lower():
            print("It's drizzling!")
            self.precipitation_status = "drizzle"
        else:
            print("No precipitation detected.")
            self.precipitation_status = "none"

    # Retrieve sunrise, sunset, and timezone information for location lat, lon
    def get_time_data(self, lat, lon):
        sun_url = f"https://api.weatherapi.com/v1/astronomy.json?key={API_KEY}&q={lat},{lon}"
        astro_response = requests.get(sun_url)
        astro_json = astro_response.json()

        astro_data = astro_json["astronomy"]["astro"]

        # String formatting written with Copilot assistance
        sunrise = datetime.strptime(astro_data["sunrise"], "%I:%M %p")
        sunset = datetime.strptime(astro_data["sunset"], "%I:%M %p")

        self.sunrise = sunrise.strftime("%H:%M")
        self.sunset = sunset.strftime("%H:%M")

        self.timezone = astro_json["location"]["tz_id"]

        print(f"Sunrise: {self.sunrise}, Sunset: {self.sunset}")
        print(f"Timezone: {self.timezone}")

    # Retrieve temperature reading in °C
    def get_temperature(self):
        self.temperature = self.bus.read_byte(ADDRESS)
        print(f"Temperature: {self.temperature}°C")

    # Retrieve averaged lighting value
    def get_light(self):
        sensor_readings = []

        # Take LIGHT_SAMPLE_SIZE readings and average their values
        for i in range(LIGHT_SAMPLE_SIZE):
            raw_value = self.chan.value
            sensor_readings.append(raw_value)

        # Average the readings' values
        self.light_level = (sum(sensor_readings) / LIGHT_SAMPLE_SIZE)
        print(f"Light level: {self.light_level}")


# Initialize and start the EnvironmentSensor
sensor = EnvironmentSensor()
sensor.start()

