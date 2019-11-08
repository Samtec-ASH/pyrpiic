import os
import math
import json
from typing import List, Union

def read_byte_data(i2cbus, slave_addr, reg_addr):
    data = [I2C.Message([reg_addr]), I2C.Message([0x00], read=True)]
    i2cbus.transfer(slave_addr, data)
    return data[1].data[0]

def write_byte_data(i2cbus, slave_addr, reg_addr, reg_value):
    data = [I2C.Message([reg_addr, reg_value])]
    i2cbus.transfer(slave_addr, data)

def write_i2c_block_data(i2cbus: int, slave_addr: int, reg_addr, block_data: Union[bytearray,List,bytes]):
    for i,v in enumerate(block_data):
        write_byte_data(i2cbus, slave_addr, reg_addr+i, v)

def float2frac(x, error=1e-9):
    n = int(math.floor(x))
    x -= n
    if x < error:
        return (n, 1)
    elif 1 - error < x:
        return (n+1, 1)

    # The lower fraction is 0/1
    lower_n = 0
    lower_d = 1
    # The upper fraction is 1/1
    upper_n = 1
    upper_d = 1
    while True:
        # The middle fraction is (lower_n + upper_n) / (lower_d + upper_d)
        middle_n = lower_n + upper_n
        middle_d = lower_d + upper_d
        # If x + error < middle
        if middle_d * (x + error) < middle_n:
            # middle is our new upper
            upper_n = middle_n
            upper_d = middle_d
        # Else If middle < x - error
        elif middle_n < (x - error) * middle_d:
            # middle is our new lower
            lower_n = middle_n
            lower_d = middle_d
        # Else middle is our best fraction
        else:
            return n * middle_d + middle_n, middle_d