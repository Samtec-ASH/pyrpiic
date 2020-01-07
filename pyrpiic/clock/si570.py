import math
from typing import Optional
from bitarray import bitarray
from pyrpio.i2c import I2C
from pyrpio.i2c_register_device import I2CRegisterDevice
from .defs import SI570Registers


class SI570:

    def __init__(self, bus: I2C, address: int):
        self.address = address
        self.i2c_reg = I2CRegisterDevice(bus, address, register_size=1, data_size=1)

    def get_registers(self, reg_addr: Optional[int] = 0x07):
        ''' Read registers from clock IC '''
        regs = SI570Registers()
        if reg_addr is not None:
            regs.reg_addr = reg_addr
        # Read raw bytes from registers
        data_in = bytearray()
        for i in range(6):
            chunk = self.i2c_reg.read_register(reg_addr + i)
            data_in.append(chunk)
        # Extract values from data
        raw_bits = bitarray(''.join([format(b, '08b') for b in data_in]))
        # First 3 bits hs, Next 7 bits N1, Following 38 bits Frequency
        regs.hs_div = int(raw_bits[:3].to01(), 2) + 4
        regs.n1 = int(raw_bits[3:10].to01(), 2) + 1
        fxp_f_req = int(raw_bits[10:].to01(), 2)
        regs.f_req = float(fxp_f_req)/(2.**28)
        return regs

    def freq2reg(self, freq_hz: float) -> SI570Registers:
        ''' Convert frequency to register dataclass '''
        regs = SI570Registers()
        f_out = freq_hz  # *1.0E6
        # Fixed values
        f_xtal = 114.285*1.0E6
        # Step 1: Assume f_dco = 5 GHz  (=f_xtal * f_req) to determine hs_div, n1
        f_dco = 5.0*1E9
        out_div = math.floor(f_dco/f_out)
        min_dist = float("inf")
        min_hs_div = 0
        min_n1 = 0
        found = False
        for hs_div in [4, 5, 6, 7, 9, 11]:
            n1 = out_div/hs_div
            n1 = n1 if n1 == 1 else 2*round(n1/2)
            new_dist = abs(n1*hs_div - out_div)
            if new_dist < min_dist and n1 <= 128:
                min_dist = new_dist
                min_hs_div = hs_div
                min_n1 = n1
                found = True
            #  if
        #  for
        regs.hs_div = min_hs_div
        regs.n1 = int(min_n1)
        if not found:
            raise Exception("Frequency not achievable- Fdco must be 4.85-5.67 GHz")
        # Step 2: Determine f_dco and therefore f_req
        f_dco = f_out * out_div
        regs.f_req = float(f_out * regs.hs_div * regs.n1)/f_xtal
        if f_dco < 4.85E9 or f_dco > 5.67E9:
            raise Exception("Frequency not achievable- Fdco must be 4.85-5.67 GHz")
        return regs

    def regs2freq(self, regs: SI570Registers) -> float:
        ''' Convert register dataclass to frequency '''
        f_xtal = 114.285*1.0E6
        freq_hz = float(f_xtal*regs.f_req)/float(regs.hs_div*regs.n1)
        # freq_hz /= 1E6
        return freq_hz

    def set_registers(self, regs: SI570Registers, nonvolatile=False):
        ''' Writes registers to clock IC '''
        # Binarize data
        #  First 3 bits hs, Next 7 bits N1,
        #  Following 38 bits Frequency (freq is in 10.28 fixed-point format)
        #  Append all for 48 bits total]
        fxp_freq = int(regs.f_req*2.0**28)
        reg_data = bitarray(format(regs.hs_div-4, '03b') + format(regs.n1-1, '07b') + format(fxp_freq, '038b'))
        regs_data = [int(reg_data[i:i+8].to01(), 2) for i in range(0, len(reg_data), 8)]
        # Read current registers
        res_reg = self.i2c_reg.read_register(135)
        frz_reg = self.i2c_reg.read_register(137)
        # Freeze DCO
        self.i2c_reg.write_register(137, frz_reg ^ 0x10)
        # Write to all registers (No need to chunk since less than 8)
        for i, v in enumerate(regs_data):
            self.i2c_reg.write_register(regs.reg_addr+i, v)
        # Unfreeze DCO
        self.i2c_reg.write_register(137, frz_reg & 0xEF)
        # Set NewFreq - New Frequency bit
        self.i2c_reg.write_register(135, res_reg ^ 0x40)

    def set_frequency(self, freq_hz: float, reg_addr: int = 0x07, nonvolatile=False):
        ''' Set clock IC to target frequency '''
        regs = self.freq2reg(freq_hz)
        self.set_registers(regs, nonvolatile=nonvolatile)

    def get_frequency(self, reg_addr: Optional[int] = 0x07):
        ''' Get frequency from clock IC '''
        regs = self.get_registers(reg_addr=reg_addr)
        freq_hz = self.regs2freq(regs)
        return freq_hz, regs
