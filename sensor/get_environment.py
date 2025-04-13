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

# To enable sensing:
# mosquitto_pub -h <BROKER> -P <PASS> -u <USER> -t "emp/operations" -m '{"target": PI_ID}'

# To disable sensing:
# mosquitto_pub -h <BROKER> -P <PASS> -u <USER> -t "emp/operations" -m '{"target": -1}'

# Constants
PI_ID = 1
SLEEP_TIME = 5
LIGHT_SAMPLE_SIZE = 20

# MQTT Broker settings
QOS = 1
KEEPALIVE = 60
PUBLISH_TOPIC = "emp/environment"
SUBSCRIBE_TOPIC = "emp/operations"
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

class EnvironmentSensor:
    def __init__(self):
        self.enabled = False
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        if BROKER_AUTHENTICATION:
            self.client.username_pw_set(USERNAME, password=PASSWORD)
            print(f"Connecting to broker {BROKER} with authentication {USERNAME}:{PASSWORD}")
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message 
        self.client.connect(BROKER, PORT, KEEPALIVE)

        # Initialize sensors
        self.bus = smbus.SMBus(BUS)
        self.spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)
        self.cs = digitalio.DigitalInOut(board.D5)
        self.mcp = MCP.MCP3008(self.spi, self.cs)
        self.chan = AnalogIn(self.mcp, MCP.P0)

        self.precipitation_status = None
        self.sunrise = None
        self.sunset = None
        self.timezone = None
        self.temperature = None
        self.light_level = None

    def on_connect(self, client, userdata, flags, reason_code, properties):
        if reason_code == 0:
            print(f'Connected to {BROKER} successfully.')
            # Subscribe to operations topic after successful connection
            client.subscribe(SUBSCRIBE_TOPIC, QOS)
            print(f'Subscribed to {SUBSCRIBE_TOPIC}')
        else:
            print(f'Connection to {BROKER} failed. Return code={reason_code}')

    def on_message(self, client, userdata, msg):
        # Handle received messages
        msg_payload = json.loads(msg.payload.decode())
        if msg_payload["target"] == PI_ID:
            self.enabled = True
            print("Sensor enabled.")
        else:
            self.enabled = False
            print("Sensor disabled.")

    def start(self):
        try:
            self.client.loop_start()
            while True:
                if not self.enabled:
                    continue
                else:
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
                        "precipitation_status": self.precipitation_status,
                        "sunrise": self.sunrise,
                        "sunset": self.sunset,
                        "timezone": self.timezone,
                        "temperature": self.temperature,
                        "light_level": self.light_level,
                    }
                    self.client.publish(PUBLISH_TOPIC, json.dumps(weather_payload), QOS)

                    time.sleep(SLEEP_TIME)

        except KeyboardInterrupt:
            self.client.disconnect()
            print("Done")

    def get_precipitation(self, lat, lon):
        weather_url = f"https://api.weatherapi.com/v1/current.json?key={API_KEY}&q={lat},{lon}&aqi=no"
        weather_response = requests.get(weather_url)
        weather_data = weather_response.json()
        current_weather = weather_data["current"]["condition"]["text"]
        print(f"Current weather: {current_weather}")
        
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

    def get_time_data(self, lat, lon):
        sun_url = f"https://api.weatherapi.com/v1/astronomy.json?key={API_KEY}&q={lat},{lon}"
        astro_response = requests.get(sun_url)
        astro_json = astro_response.json()

        astro_data = astro_json["astronomy"]["astro"]
        sunrise = datetime.strptime(astro_data["sunrise"], "%I:%M %p")
        sunset = datetime.strptime(astro_data["sunset"], "%I:%M %p")

        self.sunrise = sunrise.strftime("%H:%M")
        self.sunset = sunset.strftime("%H:%M")

        self.timezone = astro_json["location"]["tz_id"]
        
        print(f"Sunrise: {self.sunrise}, Sunset: {self.sunset}")
        print(f"Timezone: {self.timezone}")

    def get_temperature(self):
        self.temperature = self.bus.read_byte(ADDRESS)
        print(f"Temperature: {self.temperature}°C")

    def get_light(self):
        sensor_readings = []
        for i in range(LIGHT_SAMPLE_SIZE):
            raw_value = self.chan.value >> 6
            sensor_readings.append(raw_value)
        
        self.light_level = sum(sensor_readings) / LIGHT_SAMPLE_SIZE
        print(f"Light level: {self.light_level}")


# Initialize and start the EnvironmentSensor
sensor = EnvironmentSensor()
sensor.start()

