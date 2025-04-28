# Sensor Program (`get_environment.py`)
Retrieves environmental information for the current location and transmits it to an MQTT broker.

## Data Transmitted
- Pi ID (internal identifier to distinguish between multiple devices)
- Precipitation status (rain, snow, hail, or drizzle, based on weather readings at the IP-traced location)
- Sunrise time (based on the IP-traced location)
- Sunset time (based on the IP-traced location)
- Time zone (based on the IP-traced location)
- Temperature Reading (°C)
- Light level reading
- Timestamp
---
```mermaid
flowchart TD
    ES[Environment Sensor] 
    MQTT[MQTT Broker]
    TS[Temperature Sensor]
    LS[Light Sensor]
    LED[LED Indicator]
    IPAPI[IP Location API]
    WAPI[Weather API]
    
    MQTT -->|"Operation commands\n(emp/operations topic)"| ES
    ES -->|"Environment data\n(emp/environment topic)"| MQTT
    
    TS -->|"Temperature readings\n(°C)"| ES
    LS -->|"Light level values\n(analog readings)"| ES
    ES -->|"Brightness control\n(normalized log scale)"| LED
    
    ES -->|"IP-based location request"| IPAPI
    IPAPI -->|"Latitude & longitude"| ES
    
    ES -->|"Weather & precipitation request"| WAPI
    WAPI -->|"Weather condition, sunrise/sunset"| ES
```
