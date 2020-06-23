import time

from pyrpio.i2c import I2C


class EEPROMException(Exception):
    pass


class EEPROM:
    '''
    An i2c eeprom reader. Based upon https://www.i2cchip.com/pdfs/I2C_EEProm_Reading_and_Programming.pdf for
    description of how these IC chips work and typical values to use. This only works with a single address,
    so for multi-block / address chips you must create multiple instances for each address.
    '''

    def __init__(
            self, bus: I2C,
            address: int, pages: int = 16, pointer_bytes: int = 1, page_bytes: int = 16, write_time_ms: int = 5):
        '''
        [summary]

        Args:
            bus (I2C): I2C bus of the eeprom
            address (int): I2C address of the eerpom
            pages (int, optional):  Page count of the eeprom. Defaults to 16.
            pointer_bytes (int, optional): How many bytes for register addressing. Defaults to 1.
            page_bytes (int, optional): How many bytes in a page. Defaults to 16.
            write_time_ms (int, optional): Delay time after writing. Defaults to 5.
        '''
        self.__bus = bus
        self.__i2c_address = address
        self.__pointer_bytes = pointer_bytes
        self.__page_bytes = page_bytes
        self.__max_bytes = pages * page_bytes
        self.__write_time = write_time_ms / 1000.0

    def read_byte(self, address: int) -> bytes:
        '''
        Read byte at memory address

        Args:
            address (int): Memory address to read

        Returns:
            bytes: A single byte at memory address
        '''
        if address > self.__max_bytes:
            raise OverflowError(f'Overflows memory max is {self.__max_bytes} Bytes')
        self.__bus.set_address(self.__i2c_address)
        return self.__bus.read_write(address.to_bytes(length=1, byteorder='big'))

    def write_byte(self, address: int, value: bytes):
        '''
        Write byte at memory address

        Args:
            address (int): memory address to write
            value (int): byte to write
        '''
        if address > self.__max_bytes:
            raise EEPROMException(f'Overflows memory max is {self.__max_bytes} Bytes')
        self.__bus.set_address(self.__i2c_address)
        self.__bus.write(
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
        if start_address + num_bytes > self.__max_bytes:
            raise EEPROMException(f'Overflows memory max is {self.__max_bytes} Bytes')
        self.__bus.set_address(self.__i2c_address)
        return self.__bus.read_write(start_address.to_bytes(length=self.__pointer_bytes, byteorder='big'), num_bytes)

    def write_sequential_bytes(self, start_address: int, data: bytes):
        '''
        Write bytes sequentially with paging algorithm

        Args:
            start_address (int): start address to write
            data (bytes): data to write
        '''

        if start_address + len(data) > self.__max_bytes:
            raise EEPROMException(f'Overflows memory max is {self.__max_bytes} Bytes')
        self.__bus.set_address(self.__i2c_address)
        sent_data = 0

        while sent_data < len(data):
            current_start_address = start_address + sent_data
            next_page_aligned_address = (current_start_address + self.__page_bytes) & (~(self.__page_bytes - 1))
            data_to_send = min(next_page_aligned_address - current_start_address, len(data) - sent_data)
            self.__bus.write(current_start_address.to_bytes(
                length=self.__pointer_bytes, byteorder='big') + data[sent_data: sent_data + data_to_send])
            time.sleep(self.__write_time)
            sent_data += data_to_send

    def write_string(self, start_address: int, value: str, encoding: str = 'ascii'):
        '''
        Encode and write string to eeprom

        Args:
            start_address (int): address to start writing
            value (str): string with no null character to encode and write
            encoding (str, optional): What encoding to use for the string. Defaults to 'ascii'.
        '''
        if '\0' in value:
            index = value.index('\0')
            raise ValueError(f'Value contains null character at index: {index}')
        self.write_sequential_bytes(start_address, (value + '\0').encode(encoding))

    def read_string(self, start_address: int, encoding: str = 'ascii'):
        '''
        Read and decode string from eeprom. Keeps reading pages until it finds null-terminating string

        Args:
            start_address (int): [description]
            encoding (str, optional): [description]. Defaults to 'ascii'.

        Returns:
            [type]: [description]
        '''
        value = ""
        offset = 0
        while True:
            address = start_address + offset
            if address > self.__max_bytes:
                value = None
                raise EOFError('No null character found. Possibly unterminated string or uninitialized memory.')
            data = self.read_sequential_bytes(start_address + offset, self.__page_bytes)
            sub_value = data.decode(encoding, errors='ignore')
            if '\0' in sub_value:
                return value + sub_value[:sub_value.index('\0')]
            value += sub_value
            offset += self.__page_bytes

    def dump(self) -> bytes:
        '''
        Dump all data of the eeprom

        Returns:
            bytes: all eeproms block data
        '''
        return self.read_sequential_bytes(start_address=0x0, num_bytes=self.__max_bytes)

    def erase_all(self):
        '''
        Erase (set bytes to 0x00) all data on the eeprom
        '''
        self.write_sequential_bytes(start_address=0x0, data=bytes(self.__max_bytes))
