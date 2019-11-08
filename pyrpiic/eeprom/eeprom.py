from typing import List, Union

from pyrpio.i2c import I2C


class EEPROM:
    def __init__(self, bus: Union[str, I2C], pages=8, pointer_bytes: int = 1, page_bytes: int = 16, write_time_ms=5):
        '''
        [summary]

        Args:
            bus (Union[str, I2C]): [description]
            pointer_bytes (int, optional): [description]. Defaults to 1.
            page_bytes (int, optional): [description]. Defaults to 16.
            write_time_ms (int, optional): [description]. Defaults to 5.
        '''
        self.__pointer_bytes = pointer_bytes
        self.__page_bytes = page_bytes
        self.__write_time_ms = write_time_ms
        self.__pages = pages
        if isinstance(bus, I2C):
            self.bus: I2C = bus
        else:
            self.bus = I2C(path=bus)

    def read_byte(self, address: int) -> int:
        return self.bus.read_register(address, reg_nbytes=self.__pointer_bytes, val_nbytes=1)

    def write_byte(self, address: int, value: int):
        self.bus.write_register(address, value, reg_nbytes=self.__pointer_bytes, val_nbytes=1)

    def read_sequential_bytes(self, start_address: int, num_bytes: int) -> List[int]:
        return self.bus.read_register_sequential(start_address, num_bytes, reg_nbytes=self.__pointer_bytes)
