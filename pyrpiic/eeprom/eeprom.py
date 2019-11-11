import time

from pyrpio.i2c import I2C


class EEPROM:
    def __init__(
            self, bus: I2C,
            address: int, pages=8, pointer_bytes: int = 1, page_bytes: int = 16, write_time_ms: int = 5):
        '''
        [summary]

        Args:
            bus (I2C): I2C bus of the eeprom
            address (int): I2C address of the eerpom
            pages (int, optional):  Page count of the eeprom. Defaults to 8.
            pointer_bytes (int, optional): How many bytes for register addressing. Defaults to 1.
            page_bytes (int, optional): How many bytes in a page. Defaults to 16.
            write_time_ms (int, optional): Delay time after writing. Defaults to 5.
        '''
        self.__i2c_address = address
        self.__pointer_bytes = pointer_bytes
        self.__page_bytes = page_bytes
        self.__write_time = write_time_ms / 1000.0
        self.__pages = pages
        self.bus = bus

    def read_byte(self, address: int) -> bytes:
        '''
        Read byte at memory address

        Args:
            address (int): Memory address to read

        Returns:
            bytes: A single byte at memory address
        '''
        self.bus.set_address(self.__i2c_address)
        return self.bus.read_write(address.to_bytes(length=1, byteorder='big'))

    def write_byte(self, address: int, value: bytes):
        '''
        Write byte at memory address

        Args:
            address (int): memory address to write
            value (int): byte to write
        '''
        self.bus.set_address(self.__i2c_address)
        self.bus.write(
            address.to_bytes(length=self.__pointer_bytes, byteorder='big') +
            value
        )
        time.sleep(self.__write_time)

    def read_sequential_bytes(self, start_address: int, num_bytes: int) -> bytes:
        '''
        Read sequential bytes

        Args:
            start_address (int): start address to read
            num_bytes (int): number of bytes to read

        Returns:
            bytes: bytes read
        '''
        self.bus.set_address(self.__i2c_address)
        return self.bus.read_write(start_address.to_bytes(length=self.__pointer_bytes, byteorder='big'), num_bytes)

    def write_sequential_bytes(self, start_address: int, data: bytes):
        '''
        Write bytes sequentially with paging algorithm

        Args:
            start_address (int): start address to write
            data (bytes): data to write
        '''
        self.bus.set_address(self.__i2c_address)
        sent_data = 0

        while sent_data < len(data):
            current_start_address = start_address + sent_data
            next_page_aligned_address = (current_start_address + self.__page_bytes) & (~(self.__page_bytes - 1))
            data_to_send = min(next_page_aligned_address - current_start_address, len(data) - sent_data)
            self.bus.write(current_start_address.to_bytes(
                length=self.__pointer_bytes, byteorder='big') + data[sent_data: sent_data + data_to_send])
            time.sleep(self.__write_time)
            sent_data += data_to_send

    def write_string(self, start_address: int, value: str, encoding: str = 'ascii'):
        '''
        [summary]

        Args:
            start_address (int): [description]
            value (str): [description]
            encoding (str, optional): [description]. Defaults to 'ascii'.
        '''
        self.write_sequential_bytes(start_address, (value + '\0').encode(encoding))

    def read_string(self, start_address: int, encoding: str = 'ascii'):
        '''
        [summary]

        Args:
            start_address (int): [description]
            encoding (str, optional): [description]. Defaults to 'ascii'.

        Returns:
            [type]: [description]
        '''
        value = ""
        offset = 0
        while True:
            sub_value = self.read_sequential_bytes(start_address + offset, self.__page_bytes).decode(encoding)
            if '\0' in sub_value:
                return value + sub_value[:sub_value.index('\0')]
            value += sub_value
            offset += self.__page_bytes
