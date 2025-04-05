import paho.mqtt.client as mqtt
from pathlib import Path
from dotenv import load_dotenv
import os

import pygame
import time
import datetime

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

class WeatherReceiver:
    def __init__(self):
        self.precipitation_state = None
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        if BROKER_AUTHENTICATION:
            self.client.username_pw_set(USERNAME, password=PASSWORD)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.connect(BROKER, PORT, KEEPALIVE)

    def on_connect(self, client, userdata, flags, reason_code, properties=None):
        if reason_code == 0:
            print(f'Connected to {BROKER} successfully.')
            client.subscribe(TOPIC, qos=QOS)
            print(f'Subscribed to {TOPIC}')
        else:
            print(f'Connection to {BROKER} failed. Return code={reason_code}')

    def on_message(self, client, userdata, msg):
        # In seconds
        FADE_OUT_TIME = 5
        FADE_IN_TIME = 1

        print(f"Received message: {msg.payload.decode()}")
        current_precipitation = msg.payload.decode()
        current_precipitation = "rain" if current_precipitation in ["rain", "hail", "drizzle"] else current_precipitation

        # Initialize pygame mixer if not already initialized
        if pygame.mixer.get_init() is None:
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=4096)

        # If the precipitation state has changed, change the music
        if self.precipitation_state != current_precipitation:
            self.precipitation_state = current_precipitation

            # Fade out any currently playing music
            if pygame.mixer.music.get_busy():
                pygame.mixer.music.fadeout(FADE_OUT_TIME * 1000)
                time.sleep(FADE_OUT_TIME + 1)
            
            # Load and play the new track
            pygame.mixer.music.load(f"./music/{self.get_track()}")
            pygame.mixer.music.play(loops=-1, fade_ms=FADE_IN_TIME * 1000)

    def get_track(self):
        day_time = self.get_daytime()

        if self.precipitation_state == "rain":
            return f"{day_time}_rainy.mp3"
        elif self.precipitation_state == "snow":
            return f"{day_time}_snowy.mp3"
        elif self.precipitation_state == "none":
            return f"{day_time}_sunny.mp3"
        else:
            print("Unknown weather condition. Defaulting to day_sunny...")
            return f"{day_time}_sunny.mp3"

    def get_daytime(self):
        current_time = datetime.datetime.now()
        if current_time.hour >= 6 and current_time.hour < 20:
            return "day"
        else:
            return "night"


    def start(self):
        try:
            self.client.loop_forever()
        except KeyboardInterrupt:
            self.client.disconnect()
            print('Done')


# Initialize and start the WeatherReceiver
receiver = WeatherReceiver()
receiver.start()

