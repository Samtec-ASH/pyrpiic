from typing import Tuple
from pyrpiic.sensor.ldc1x1y import LDC1X1Y


class LDC161X(LDC1X1Y):
    ''' TI 28-bit LDC1612/LDC1614 inductive sensor API. '''

    def __init__(self, bus, address=0x2A):
        # Manufacturing ID: 0x5449
        # Device ID: 0x3055
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
        ch_lsb = self.get_register(self.LDC1X1Y_DATA_BASE + 2*ch + 1)
        value = ((0x0FFF & ch_msb) << 16) & ch_lsb
        err_code = (ch_msb & 0xF000) >> 12
        return value, err_code
