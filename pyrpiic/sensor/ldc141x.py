from typing import Tuple
from pyrpiic.sensor.ldc1x1y import LDC1X1Y


class LDC141X(LDC1X1Y):
    ''' TI 14-bit LDC1412/LDC1414 inductive sensor API. '''

    def __init__(self, bus, address=0x2A):
        # Manufacturing ID: 0x5449
        # Device ID: 0x3054
        super().__init__(bus, address=address)

    def get_channel_data(self, ch: int) -> Tuple[int, int]:
        ''' Get channel data and error flags.
            Returns:
                int: Channel computed conversion value
                int: Error code
                    0x8: Under range error bit
                    0x4: Over range error bit
                    0x2: Watchdog timeout error bit
                    0x1: Amplitude error bit
        '''
        ch_msb = self.get_register(self.LDC1X1Y_DATA_BASE + 2*ch)
        value = 0x0FFF & ch_msb
        err_code = (ch_msb & 0xF000) >> 12
        return value, err_code

    def get_output_gain(self):
        ''' Get output gain control.
            ---------------------------------------
            | BITS | GAIN | SHIFT  | RES. | RANGE |
            |------+------+--------+------+-------|
            |  00  |   1  | 0 bits |  12  | 100%  |
            |  01  |   4  | 2 bits |  14  | 25%   |
            |  10  |   8  | 3 bits |  15  | 12.5% |
            |  11  |  16  | 4 bits |  16  | 6.25% |
            ---------------------------------------
            Returns:
                int: Gain register value
        '''
        return self.get_register(self.LDC1X1Y_RESET_DEV, mask=0x0600) >> 9

    def set_output_gain(self, value: int):
        ''' Set output gain control.
            ---------------------------------------
            | BITS | GAIN | SHIFT  | RES. | RANGE |
            |------+------+--------+------+-------|
            |  00  |   1  | 0 bits |  12  | 100%  |
            |  01  |   4  | 2 bits |  14  | 25%   |
            |  10  |   8  | 3 bits |  15  | 12.5% |
            |  11  |  16  | 4 bits |  16  | 6.25% |
            ---------------------------------------
            Args:
                value (int): Gain register value
        '''
        return self.set_register(self.LDC1X1Y_RESET_DEV, value << 9, mask=0x0600)
