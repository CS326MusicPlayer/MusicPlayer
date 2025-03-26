import requests
import time

# Replace with your location (or use GPS module if available)
LAT = 42.0971
LONG = -75.9117
SLEEP_TIME=5

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
    elif "snow" in current_weather.lower():
      print("It's snowing!")
    elif "hail" in current_weather.lower():
      print("It's hailing!")
    elif "drizzle" in current_weather.lower():
      print("It's drizzling!")
    else:
      print("No precipitation detected.")
    time.sleep(SLEEP_TIME)