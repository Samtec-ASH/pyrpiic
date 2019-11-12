'''
Implement a fake eeprom i2c bus. Every device created will 
'''

from dataclasses import dataclass, field
from typing import Dict
from pyrpio.i2c import I2C as I2CBase


class I2CException(Exception):
    '''
    Exceptions that occur during i2c operations. (before OS level ops)
    '''
    ...


@dataclass
class EERPOM:
    pages: int
    pointer_bytes: int
    page_bytes: int
    current_address: int = 0x0
    data: Dict[int, int] = field(default_factory=dict)


class I2C(I2CBase):
    def __init__(self, path: str = '/dev/i2c-1'):
        self.path: str = path
        self.__address = 0x0
        self
        # data stored in each eeprom i2c address
        self.__bus: Dict[int, EERPOM] = {}
        self.__open = False

    def open(self):
        if not self.__open:
            self.__address = 0x0
            self.__open = True

    def configure_eeprom(self, address: int, pages: int = 16, pointer_bytes: int = 1, page_bytes: int = 16):
        self.__bus[address] = EERPOM(pages=pages, pointer_bytes=pointer_bytes, page_bytes=page_bytes)

    def close(self):
        self.__open = False

    def set_address(self, address: int):
        if not self.__open:
            raise I2CException(f'Bus: {self.path} is not open')
        self.__address = address & 0x7F

    def read(self, length: int = 1) -> bytes:
        if not self.__open:
            raise I2CException(f'Bus: {self.path} is not open')
        eeprom = self.__bus[self.__address]
        response = bytes()
        for idx in range(length):
            response += eeprom.data.get(eeprom.current_address + idx, 0x0).to_bytes(length=1, byteorder='big')
        return response

    def write(self, data: bytes):
        if not self.__open:
            raise I2CException(f'Bus: {self.path} is not open')
        eeprom = self.__bus[self.__address]
        mem_address = int.from_bytes(data[:eeprom.pointer_bytes], byteorder='big')
        mem_page_address = mem_address & (~(eeprom.page_bytes - 1))

        data_values = data[eeprom.pointer_bytes:]
        for idx, value in enumerate(data_values):
            # simulate wrapping if too many writes done to a page
            address = mem_address + idx
            if address > mem_page_address + eeprom.page_bytes:
                address = mem_page_address + ((address - mem_page_address) % eeprom.page_bytes)
            eeprom.data[mem_address + idx] = value

        eeprom.current_address = mem_address + len(data_values)

    def read_write(self, data: bytes, length: int = 1) -> bytes:
        eeprom = self.__bus[self.__address]
        mem_address = int.from_bytes(data[:eeprom.pointer_bytes], byteorder='big')
        response = bytes()
        for idx in range(length):
            response += eeprom.data.get(mem_address + idx, 0x0).to_bytes(length=1, byteorder='big')

        eeprom.current_address = mem_address + length
        return response
