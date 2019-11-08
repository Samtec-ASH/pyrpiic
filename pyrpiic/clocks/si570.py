import math
from bitarray import bitarray
from .utils import read_byte_data, write_i2c_block_data, write_byte_data
from .defs import SI570Registers


def freq2reg(freq_hz: float) -> SI570Registers:
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
    regs.n1 = min_n1
    if not found:
        raise Exception("Frequency not achievable- Fdco must be 4.85-5.67 GHz")
    # Step 2: Determine f_dco and therefore f_req
    f_dco = f_out * out_div
    regs.f_req = float(f_out * regs.hs_div * regs.n1)/f_xtal
    if f_dco < 4.85E9 or f_dco > 5.67E9:
        raise Exception("Frequency not achievable- Fdco must be 4.85-5.67 GHz")
    return regs


def regs2freq(regs: SI570Registers) -> float:
    f_xtal = 114.285*1.0E6
    freq_hz = float(f_xtal*regs.f_req)/float(regs.hs_div*regs.n1)
    # freq_hz /= 1E6
    return freq_hz


def set_registers(i2cbus, slave_addr, regs: SI570Registers, nonvolatile=False):
    # Binarize data
    #  First 3 bits hs, Next 7 bits N1,
    #  Following 38 bits Frequency (freq is in 10.28 fixed-point format)
    #  Append all for 48 bits total]
    fxp_freq = int(regs.f_req*2.0**28)
    reg_data = bitarray(format(regs.hs_div-4, '03b') + format(regs.n1-1, '07b') + format(fxp_freq, '038b'))
    regs_data = [int(reg_data[i:i+8].to01(), 2) for i in range(0, len(reg_data), 8)]
    try:
        # Read current registers
        resReg = read_byte_data(i2cbus, slave_addr, 135)
        frzReg = read_byte_data(i2cbus, slave_addr, 137)
        # Freeze DCO
        write_byte_data(i2cbus, slave_addr, 137, frzReg ^ 0x10)
        # Write to all registers (No need to chunk since less than 8)
        i2cbus.write_i2c_block_data(slave_addr, regs.reg_addr, regs_data)
        # Unfreeze DCO
        write_byte_data(i2cbus, slave_addr, 137, frzReg & 0xEF)
        # Set NewFreq - New Frequency bit
        write_byte_data(i2cbus, slave_addr, 135, resReg ^ 0x40)
    except IOError:
        raise


def get_registers(i2cbus, slave_addr, reg_addr=0x07):
    regs = SI570Registers()
    regs.reg_addr = reg_addr
    # Read raw bytes from registers
    data_in = bytearray()
    try:
        for i in range(6):
            chunk = read_byte_data(i2cbus, slave_addr, reg_addr + i)
            data_in.append(chunk)
    except IOError:
        raise
    # Extract values from data
    raw_bits = bitarray(''.join([format(b, '08b') for b in data_in]))
    # First 3 bits hs, Next 7 bits N1, Following 38 bits Frequency
    regs.hs_div = int(raw_bits[:3].to01(), 2) + 4
    regs.n1 = int(raw_bits[3:10].to01(), 2) + 1
    fxp_f_req = int(raw_bits[10:].to01(), 2)
    regs.f_req = float(fxp_f_req)/(2.**28)
    return regs


def set_frequency(i2cbus, slave_addr: int, freq_hz: float, reg_addr: int = 0x07, nonvolatile=False):
    regs = freq2reg(freq_hz)
    set_registers(i2cbus, slave_addr, regs, nonvolatile=nonvolatile)


def get_frequency(i2cbus, slave_addr: int, reg_addr: int = 0x07, nonvolatile=False):
    regs = get_registers(i2cbus, slave_addr, reg_addr=reg_addr)
    freq_hz = regs2freq(regs)
    return freq_hz, regs
