import random
import time

from pyrpio.i2c import I2C

i2c = I2C('/dev/i2c-3')

i2c.open()

i2c.set_address(0x70)

i2c.write(0x1.to_bytes(length=1, byteorder='big'))


i2c.set_address(0x57)

print(i2c.read_register_sequential(0x0, 10))

time.sleep(0)
# i2c.write_register(0x0, 0x10)
i2c.write_register_sequential(0xF, [0xF] * 16)
time.sleep(0.1)
print(i2c.read_register_sequential(0x0, 256))
