import pytest

from pyrpiic.eeprom import EEPROM
from pyrpiic.eeprom.tests.fake_i2c import I2C

bus = I2C('/dev/i2c-3')
bus.open()
bus.configure_eeprom(0x57, 16, 1, 16)
eeprom = EEPROM(bus, 0x57)


def test_eeprom_clear():

    eeprom.write_sequential_bytes(0x0, bytes(256))
    # eeprom.write_string(0x0, 'this is crazy'*18)
    print(eeprom.read_string(0x0))
    assert eeprom.dump() == bytes(256)


def test_eeprom_write():
    eeprom.write_string(0x0, 'hello world how is it'*10)
    assert eeprom.read_string(0x0) == 'hello world how is it'*10


def test_eeprom_write_null_character():
    with pytest.raises(ValueError):
        eeprom.write_string(0x0, 'hello world \0 how is it'*10)
