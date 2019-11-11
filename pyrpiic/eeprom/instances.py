from pyrpio.i2c import I2C

from .eeprom import EEPROM


class M24C02(EEPROM):
    '''
    Wrapper for EEPROM M24C02. Uses data sheet https://www.mouser.com/datasheet/2/389/m24c01-r-954990.pdf
    '''

    def __init__(self, bus: I2C, address: int):
        super().__init__(bus=bus, address=address)
