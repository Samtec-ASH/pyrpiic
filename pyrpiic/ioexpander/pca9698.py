from typing import Optional, Union
from enum import Enum
from pyrpio.i2c_register_device import I2CRegisterDevice
from pyrpio.i2c import I2C


class GPIODir(str, Enum):
    IN = 'IN'
    OUT = 'OUT'


class PCA9698:
    PORT0 = ['IO0_0', 'IO0_1', 'IO0_2', 'IO0_3', 'IO0_4', 'IO0_5', 'IO0_6', 'IO0_7']
    PORT1 = ['IO1_0', 'IO1_1', 'IO1_2', 'IO1_3', 'IO1_4', 'IO1_5', 'IO1_6', 'IO1_7']
    PORT2 = ['IO2_0', 'IO2_1', 'IO2_2', 'IO2_3', 'IO2_4', 'IO2_5', 'IO2_6', 'IO2_7']
    PORT3 = ['IO3_0', 'IO3_1', 'IO3_2', 'IO3_3', 'IO3_4', 'IO3_5', 'IO3_6', 'IO3_7']
    PORT4 = ['IO4_0', 'IO4_1', 'IO4_2', 'IO4_3', 'IO4_4', 'IO4_5', 'IO4_6', 'IO4_7']
    PCA9698_BASE_INPUT = 0x00
    PCA9698_PORT0_INPUT = 0x00
    PCA9698_PORT1_INPUT = 0x01
    PCA9698_PORT2_INPUT = 0x02
    PCA9698_PORT3_INPUT = 0x03
    PCA9698_PORT4_INPUT = 0x04
    PCA9698_BASE_OUTPUT = 0x08
    PCA9698_PORT0_OUTPUT = 0x08
    PCA9698_PORT1_OUTPUT = 0x09
    PCA9698_PORT2_OUTPUT = 0x0A
    PCA9698_PORT3_OUTPUT = 0x0B
    PCA9698_PORT4_OUTPUT = 0x0C
    PCA9698_BASE_POLARITY = 0x10
    PCA9698_PORT0_POLARITY = 0x10
    PCA9698_PORT1_POLARITY = 0x11
    PCA9698_PORT2_POLARITY = 0x12
    PCA9698_PORT3_POLARITY = 0x13
    PCA9698_PORT4_POLARITY = 0x14
    PCA9698_BASE_CONFIG = 0x18
    PCA9698_PORT0_CONFIG = 0x18
    PCA9698_PORT1_CONFIG = 0x19
    PCA9698_PORT2_CONFIG = 0x1A
    PCA9698_PORT3_CONFIG = 0x1B
    PCA9698_PORT4_CONFIG = 0x1C

    def __init__(self, bus: I2C, address=0x20):
        self.address = address
        self.i2c_reg = I2CRegisterDevice(bus, address, register_size=1, data_size=1)

    def close(self):
        ''' Close up access. '''
        return 0

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        self.close()

    def get_register(self, register: int, mask: Optional[int] = None) -> int:
        ''' Get single byte register. '''
        value = self.i2c_reg.read_register(register)
        if mask is not None:
            value = value & mask
        return value

    def set_register(self, register, value: int, mask: Optional[int] = None):
        ''' Set single byte register. '''
        if mask is not None:
            pvalue = self.get_register(register, ~mask)  # pylint: disable=invalid-unary-operand-type
            value = pvalue | (value & mask)
        self.i2c_reg.write_register(register, value)

    def get_register_bit(self, register: int, bit: int):
        ''' Get single bit from register. '''
        mask = 1 << bit
        value = self.get_register(register, mask)
        return bool(value >> bit)

    def set_register_bit(self, register: int, bit: int, on: bool):
        ''' Set single bit of a register. '''
        mask = 1 << bit
        pvalue = self.get_register(register, ~mask)
        self.set_register(register, pvalue | (int(on) << bit))

    def get_port_index(self, gpio: Union[str, int]) -> int:
        ''' Get port index for given gpio. '''
        if isinstance(gpio, str):
            if gpio in PCA9698.PORT0:
                return 0
            if gpio in PCA9698.PORT1:
                return 1
            if gpio in PCA9698.PORT2:
                return 2
            if gpio in PCA9698.PORT3:
                return 3
            if gpio in PCA9698.PORT4:
                return 4
        elif isinstance(gpio, int):
            return int(gpio / 8)
        raise ValueError(f'GPIO {gpio} is not a valid value')

    def get_gpio_bit_position(self, gpio: Union[str, int]) -> int:
        ''' Get register bit position for given gpio. '''
        if isinstance(gpio, str):
            if gpio in PCA9698.PORT0:
                return PCA9698.PORT0.index(gpio)
            if gpio in PCA9698.PORT1:
                return PCA9698.PORT1.index(gpio)
            if gpio in PCA9698.PORT2:
                return PCA9698.PORT2.index(gpio)
            if gpio in PCA9698.PORT3:
                return PCA9698.PORT3.index(gpio)
            if gpio in PCA9698.PORT4:
                return PCA9698.PORT4.index(gpio)
        elif isinstance(gpio, int):
            return int(gpio % 8)
        raise ValueError(f'GPIO {gpio} is not a valid value')

    def get_gpio_direction(self, gpio: Union[str, int]) -> GPIODir:
        ''' Get GPIO direction as either in or out. '''
        port_index = self.get_port_index(gpio)
        gpio_bit = self.get_gpio_bit_position(gpio)
        value = self.get_register_bit(self.PCA9698_BASE_CONFIG + port_index, gpio_bit)
        return GPIODir.IN if value else GPIODir.OUT

    def set_gpio_direction(self, gpio: Union[str, int], gpio_dir: GPIODir):
        ''' Set GPIO direction as either in or out. '''
        port_index = self.get_port_index(gpio)
        gpio_bit = self.get_gpio_bit_position(gpio)
        value = gpio_dir == GPIODir.IN
        self.set_register_bit(self.PCA9698_BASE_CONFIG + port_index, gpio_bit, value)

    def get_gpio_input(self, gpio: Union[str, int]) -> bool:
        ''' Read GPIO input value.'''
        port_index = self.get_port_index(gpio)
        gpio_bit = self.get_gpio_bit_position(gpio)
        return self.get_register_bit(self.PCA9698_BASE_INPUT + port_index, gpio_bit)

    def get_gpio_output(self, gpio: Union[str, int]) -> bool:
        ''' Get currently set GPIO output value.'''
        port_index = self.get_port_index(gpio)
        gpio_bit = self.get_gpio_bit_position(gpio)
        return self.get_register_bit(self.PCA9698_BASE_OUTPUT + port_index, gpio_bit)

    def set_gpio_output(self, gpio: Union[str, int], high: Union[bool, int]):
        ''' Pull GPIO output either active high or low.'''
        port_index = self.get_port_index(gpio)
        gpio_bit = self.get_gpio_bit_position(gpio)
        self.set_register_bit(self.PCA9698_BASE_OUTPUT + port_index, gpio_bit, bool(high))

    def get_gpio_polarity(self, gpio: Union[str, int]):
        ''' Get GPIO polarity setting. '''
        port_index = self.get_port_index(gpio)
        gpio_bit = self.get_gpio_bit_position(gpio)
        return self.get_register_bit(self.PCA9698_BASE_POLARITY + port_index, gpio_bit)

    def set_gpio_polarity(self, gpio: Union[str, int], flipped: bool):
        ''' Set GPIO polarity setting as either normal or flipped. '''
        port_index = self.get_port_index(gpio)
        gpio_bit = self.get_gpio_bit_position(gpio)
        self.set_register_bit(self.PCA9698_BASE_POLARITY + port_index, gpio_bit, flipped)
