import smbus
import time

# constants
BUS = 1            # I2C bus number
ADDRESS = 0x48     # TC74 I2C bus address
DELAY = 0.5        # delay between reads

# Connect to I2C bus
bus = smbus.SMBus(BUS)

try:
    while True:
        temp = bus.read_byte(ADDRESS)
        print(f'{temp} degrees C')
        time.sleep(DELAY)
except KeyboardInterrupt:
    bus.close()
    print('Done')