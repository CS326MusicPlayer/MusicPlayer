import paho.mqtt.client as mqtt
import json
from pathlib import Path
from dotenv import load_dotenv
import os

import pygame
import time
from datetime import datetime

# To test:
# mosquitto_pub -h <BROKER> -P <PASS> -u <USER> -p 8883 -t "emp/environment" -m '{"precipitation_status": "snow", "sunrise": "hh:mm", "sunset": "hh:mm", "temperature: 25", "light_level": 0.5}' 

# Constants
SLEEP_TIME = 5
QOS = 0
KEEPALIVE = 60
BROKER_AUTHENTICATION = True
PORT = 1883

# Note: these constants must be set if broker requires authentication
env_path = Path("../.env")
load_dotenv()
BROKER = os.getenv("BROKER")
USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")

class WeatherReceiver:
    def __init__(self):
        self.precipitation_state = None
        self.sun_state = None
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        if BROKER_AUTHENTICATION:
            self.client.username_pw_set(USERNAME, password=PASSWORD)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.connect(BROKER, PORT, KEEPALIVE)

    def on_connect(self, client, userdata, flags, reason_code, properties=None):
        if reason_code == 0:
            print(f'Connected to {BROKER} successfully.')
            client.subscribe("emp/environment", qos=QOS)
        else:
            print(f'Connection to {BROKER} failed. Return code={reason_code}')

    def on_message(self, client, userdata, msg):
        # In seconds
        FADE_OUT_TIME = 5
        FADE_IN_TIME = 1

        try:
            # Decode the message payload
            msg_payload = json.loads(msg.payload.decode())
            current_precipitation_status = msg_payload["precipitation_status"]
            sunrise = datetime.strptime(msg_payload["sunrise"], "%H:%M").time()
            sunset = datetime.strptime(msg_payload["sunset"], "%H:%M").time()
            current_time = datetime.now().time()
            current_sun_status = "day" if sunrise <= current_time <= sunset else "night"
            
            print(f"Sunrise: {sunrise}, Sunset: {sunset}, Current time: {current_time}")

            current_precipitation_status = "rain" if current_precipitation_status in ["rain", "hail", "drizzle"] else current_precipitation_status


            print(f"Received message: {msg.payload.decode()}")

            # Initialize pygame mixer if not already initialized
            if pygame.mixer.get_init() is None:
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=4096)

            # If the precipitation state has changed, change the music
            if (self.precipitation_state != current_precipitation_status or
                self.sun_state != current_sun_status):
                self.precipitation_state = current_precipitation_status
                self.sun_state = current_sun_status

                # Fade out any currently playing music
                if pygame.mixer.music.get_busy():
                    pygame.mixer.music.fadeout(FADE_OUT_TIME * 1000)
                    time.sleep(FADE_OUT_TIME + 1)
                
                # Load and play the new track
                pygame.mixer.music.load(f"./music/{self.get_track()}")
                pygame.mixer.music.play(loops=-1, fade_ms=FADE_IN_TIME * 1000)
        except json.JSONDecodeError:
            print("Failed to decode JSON message.")
            print(f"Message payload: {msg.payload.decode()}")

    def get_track(self):
        if self.sun_state == "day":
            if self.precipitation_state == "rain":
                return "day_rainy.mp3"
            elif self.precipitation_state == "snow":
                return "day_snowy.mp3"
            elif self.precipitation_state == "none":
                return "day_sunny.mp3"
            else:
                print("Unknown weather condition. Defaulting to day_sunny...")
                return "day_sunny.mp3"
            
        elif self.sun_state == "night":
            if self.precipitation_state == "rain":
                return "night_rainy.mp3"
            elif self.precipitation_state == "snow":
                return "night_snowy.mp3"
            elif self.precipitation_state == "none":
                return "night_sunny.mp3"
            else:
                print("Unknown weather condition. Defaulting to night_sunny...")
                return "night_sunny.mp3"

    def start(self):
        try:
            self.client.loop_forever()
        except KeyboardInterrupt:
            self.client.disconnect()
            print('Done')


# Initialize and start the WeatherReceiver
receiver = WeatherReceiver()
receiver.start()

