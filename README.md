# Environmental Music Player
> Jason Chew, Daniel Kim
- [Web UI](https://github.com/CS326MusicPlayer/EMP_UI): [Click here](https://emp-webui.web.app/)
---
## Description:
TBA

---
## Installation:
- Clone the repository to your Raspberry Pi
  - Set up environment variable in the root directory
  ```
  BROKER=<your_broker>
  PORT=<your_port>
  PID=<your_pi_id>
  USERNAME=<your_username(optional)>
  PASSWORD=<your_password(optional)>
  WEATHER_API_KEY=<your_weather_api_key>
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

