import array
import time
from enum import Enum
from pyrpio.i2c_register_device import I2CRegisterDevice
from pyrpio.i2c import I2C


# I2C Address
HDC1080_ADDRESS = (0x40)    # 1000000
# Registers
HDC1080_TEMPERATURE_REGISTER = (0x00)
HDC1080_HUMIDITY_REGISTER = (0x01)
HDC1080_CONFIGURATION_REGISTER = (0x02)
HDC1080_MANUFACTURERID_REGISTER = (0xFE)
HDC1080_DEVICEID_REGISTER = (0xFF)
HDC1080_SERIALIDHIGH_REGISTER = (0xFB)
HDC1080_SERIALIDMID_REGISTER = (0xFC)
HDC1080_SERIALIDBOTTOM_REGISTER = (0xFD)

# Configuration Register Bits

HDC1080_CONFIG_RESET_BIT = (0x8000)
HDC1080_CONFIG_HEATER_ENABLE = (0x2000)
HDC1080_CONFIG_ACQUISITION_MODE = (0x1000)
HDC1080_CONFIG_BATTERY_STATUS = (0x0800)
HDC1080_CONFIG_TEMPERATURE_RESOLUTION = (0x0400)
HDC1080_CONFIG_HUMIDITY_RESOLUTION_HBIT = (0x0200)
HDC1080_CONFIG_HUMIDITY_RESOLUTION_LBIT = (0x0100)

HDC1080_CONFIG_TEMPERATURE_RESOLUTION_14BIT = (0x0000)
HDC1080_CONFIG_TEMPERATURE_RESOLUTION_11BIT = (0x0400)

HDC1080_CONFIG_HUMIDITY_RESOLUTION_14BIT = (0x0000)
HDC1080_CONFIG_HUMIDITY_RESOLUTION_11BIT = (0x0100)
HDC1080_CONFIG_HUMIDITY_RESOLUTION_8BIT = (0x0200)


class HDC1080:
    class TempResolution(Enum):
        fourteen = 0
        eleven = 1

    class HumidityResolution(Enum):
        fourteen = 0
        eleven = 1
        eight = 2
    i2c: I2C
    i2c_reg: I2CRegisterDevice
    address: int

    def __init__(self, bus: I2C, address=HDC1080_ADDRESS):
        self.address = address
        self.i2c = bus
        self.i2c_reg = I2CRegisterDevice(
            bus, address, register_size=1, data_size=2)
        time.sleep(0.015)  # 15ms startup time

    def configure(self):
        """ configure for acquisition mode """
        config = HDC1080_CONFIG_ACQUISITION_MODE
        self.i2c.set_address(self.address)
        self.i2c_reg.write_register_bytes(HDC1080_CONFIGURATION_REGISTER,
                                          bytes(bytearray([config >> 8, 0x00])))
        time.sleep(0.015)

    def read_temperature(self) -> float:
        ''' read temperature and return a float '''
        s = bytes(bytearray([HDC1080_TEMPERATURE_REGISTER]))
        self.i2c.set_address(self.address)
        self.i2c.write(s)
        time.sleep(0.0625)              # Required delay

        self.i2c.set_address(self.address)
        data = self.i2c.read(2)  # read 2 byte temperature data
        buf = array.array('B', data)
        #print ( "Temp: %f 0x%X %X" % (  ((((buf[0]<<8) + (buf[1]))/65536.0)*165.0 ) - 40.0   ,buf[0],buf[1] )  )

        # Convert the data
        temp = (buf[0] * 256) + buf[1]
        cTemp = (temp / 65536.0) * 165.0 - 40
        return cTemp

    def read_humidity(self) -> float:
        ''' read humidity and return a float '''
        time.sleep(0.015)               # Required delay
        s = bytes(bytearray([HDC1080_HUMIDITY_REGISTER]))
        self.i2c.set_address(self.address)
        self.i2c.write(s)
        time.sleep(0.0625)              # Required delay

        data = self.i2c.read(2)  # read 2 byte humidity data
        buf = array.array('B', data)
        #print ( "Humidity: %f 0x%X %X " % (  ((((buf[0]<<8) + (buf[1]))/65536.0)*100.0 ),  buf[0], buf[1] ) )
        humidity = (buf[0] * 256) + buf[1]
        humidity = (humidity / 65536.0) * 100.0
        return humidity

    def read_config_register(self) -> int:
        ''' read configuration register and return integer value '''
        s = bytes(bytearray([HDC1080_CONFIGURATION_REGISTER]))
        self.i2c.set_address(self.address)
        self.i2c.write(s)
        time.sleep(0.0625)              # Required delay

        data = self.i2c.read(2)  # read 2 byte config data

        buf = array.array('B', data)

        # print("register={} {}".format(buf[0], buf[1]))
        return buf[0]*256+buf[1]

    def turn_heater_on(self):
        ''' turn heater on '''
        config = self.read_config_register()
        config = config | HDC1080_CONFIG_HEATER_ENABLE
        s = [HDC1080_CONFIGURATION_REGISTER, config >> 8, 0x00]
        s2 = bytes(bytearray(s))
        self.i2c.set_address(self.address)
        self.i2c.write(s2)  # sending config register bytes
        time.sleep(0.015)               # Required delay

    def turn_heater_off(self):
        ''' turn heater off '''
        config = self.read_config_register()
        config = config & ~HDC1080_CONFIG_HEATER_ENABLE
        s = [HDC1080_CONFIGURATION_REGISTER, config >> 8, 0x00]
        s2 = bytes(bytearray(s))
        self.i2c.set_address(self.address)
        self.i2c.write(s2)  # sending config register bytes
        time.sleep(0.015)               # Required delay

    def set_humidity_resolution(self, resolution: HumidityResolution):
        ''' set humidity resolution [0 - 14bit, 1 - 11bit, 2 - 8bit ] '''
        config = self.read_config_register()
        config = (config & ~0x0300) | resolution.value
        s = [HDC1080_CONFIGURATION_REGISTER, config >> 8, 0x00]
        s2 = bytes(bytearray(s))
        self.i2c.set_address(self.address)
        self.i2c.write(s2)  # sending config register bytes
        time.sleep(0.015)               # Required delay

    def set_temperature_resolution(self, resolution: TempResolution):
        ''' set temperature resolution [0 - 14bit, 1 - 11bit ] '''
        config = self.read_config_register()
        config = (config & ~0x0400) | resolution.value

        s = [HDC1080_CONFIGURATION_REGISTER, config >> 8, 0x00]
        s2 = bytes(bytearray(s))
        self.i2c.set_address(self.address)
        self.i2c.write(s2)  # sending config register bytes
        time.sleep(0.015)               # Required delay

    def read_battery_status(self) -> bool:
        ''' get battery status (bool) '''
        config = self.read_config_register()
        config = config & ~ HDC1080_CONFIG_HEATER_ENABLE

        return bool(config == 0)

    def read_manufacturer_id(self) -> int:
        ''' get manufacturuer id (int) '''
        s = [HDC1080_MANUFACTURERID_REGISTER]  # temp
        s2 = bytes(bytearray(s))
        self.i2c.set_address(self.address)
        self.i2c.write(s2)
        time.sleep(0.0625)              # Required delay

        data = self.i2c.read(2)  # read 2 byte config data

        buf = array.array('B', data)
        return buf[0] * 256 + buf[1]

    def read_device_id(self) -> int:
        ''' get device id (int) '''
        s = [HDC1080_DEVICEID_REGISTER]  # temp
        s2 = bytes(bytearray(s))
        self.i2c.set_address(self.address)
        self.i2c.write(s2)
        time.sleep(0.0625)              # Required delay

        data = self.i2c.read(2)  # read 2 byte config data

        buf = array.array('B', data)
        return buf[0] * 256 + buf[1]

    def read_serial_number(self) -> int:
        ''' get device serial number (int) '''
        serialNumber = 0

        s = [HDC1080_SERIALIDHIGH_REGISTER]  # temp
        s2 = bytes(bytearray(s))
        self.i2c.set_address(self.address)
        self.i2c.write(s2)
        time.sleep(0.0625)              # Required delay
        data = self.i2c.read(2)  # read 2 byte config data
        buf = array.array('B', data)
        serialNumber = buf[0]*256 + buf[1]

        s = [HDC1080_SERIALIDMID_REGISTER]  # temp
        s2 = bytes(bytearray(s))
        self.i2c.write(s2)
        time.sleep(0.0625)              # Required delay
        data = self.i2c.read(2)  # read 2 byte config data)
        buf = array.array('B', data)
        serialNumber = serialNumber*256 + buf[0]*256 + buf[1]

        s = [HDC1080_SERIALIDBOTTOM_REGISTER]  # temp
        s2 = bytes(bytearray(s))
        self.i2c.write(s2)
        time.sleep(0.0625)              # Required delay
        data = self.i2c.read(2)  # read 2 byte config data
        buf = array.array('B', data)
        serialNumber = serialNumber*256 + buf[0]*256 + buf[1]

        return serialNumber
