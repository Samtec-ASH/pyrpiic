import json
from pyrpio.i2c import I2C

from pyrpiic.eeprom import EEPROM

i2c = I2C('/dev/i2c-3')

i2c.open()


eeprom = EEPROM(bus=i2c, address=0x57)

print(eeprom.write_sequential_bytes(0x0, bytes(256)))

test = dict(val=2, cool=4, test='ç‡Ó\0dsf', me=dict(nathan=True))

x = json.dumps(test)

eeprom.write_string(0x0, x)

print(eeprom.read_sequential_bytes(0x0, 256))

print(json.loads(eeprom.read_string(0x0)))
