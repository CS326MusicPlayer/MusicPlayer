# Environmental Music Player
> Jason Chew, Daniel Kim
- [Web UI](https://github.com/CS326MusicPlayer/EMP_UI)

---
## Description:
This project adaptively plays different soundtracks depending on the current state of precipitation, sunrise/sunset times, lighting conditions, and/or temperature, based on a Raspberry Pi’s location. The music plays in a web frontend, through which the user can also specify what environmental factors should play a role in the tracks played.

Our system has two base tracks, one for “daytime” and one for “nighttime.” The base tracks are chosen based on time or light level. Each track has three variations: one for clear weather, one for rainy weather, and one for snowy weather. The variations are chosen based on local weather conditions or temperature.

---
## Diagrams:
![Circuit Diagram](/diagrams/emp_bb.png)

---
## Installation:
- Clone the repository to your Raspberry Pi
  - Set up environment variable in the root directory
  ```
  BROKER=<your_broker>
  PORT=<your_port>
  PID=<your_pi_id>
  WEATHER_API_KEY=<your_weather_api_key>
  USERNAME=<your_username(optional)>
  PASSWORD=<your_password(optional)>
  CERTS=<your_certs(optional)>
  ```
- Activate the virtual environment:
```bash
python3 -m venv --system-site-packages emp
source emp/bin/activate
```
- `pip3 install -r requirements.txt`
- `sudo apt install mosquitto-clients`
- `sudo apt-get install i2c-tools`
- `sudo apt-get install python3-smbus`


---
## Usage:
- To run the [sensor](/sensor/README.md), run: `cd sensor` and `python3 get_environment.py`
- If you want to test the [receiver](/actuator/README.md) using Pi, run: `cd actuator` and `python3 receiver.py`
