#%%
import time
import math
from bitarray import bitarray
from .utils import read_byte_data, write_i2c_block_data, float2frac
from .defs import LMK61E2Registers, LMK61E2ClockMode

def get_registers(i2cbus, slave_addr: int) -> LMK61E2Registers:
    """" Read registers from device. """
    # Read registers
    data_in = bytearray()
    for i in range(11):
        data_in.append(read_byte_data(i2cbus, slave_addr, 22 + i))
    # REGISTER 33
    mash_ctrl_byte = read_byte_data(i2cbus, slave_addr, 33)
    mash_ctrl_bits = bitarray(format(mash_ctrl_byte, '08b'))
    # REGISTER 34
    pll_ctrl0_byte = read_byte_data(i2cbus, slave_addr, 34)
    pll_ctrl0_bits = bitarray(format(pll_ctrl0_byte, '08b'))
    # REGISTER 35
    pll_ctrl1_byte = read_byte_data(i2cbus, slave_addr, 35)
    pll_ctrl1_bits = bitarray(format(pll_ctrl1_byte, '08b'))
    # REGISTER 21
    diffctrl_byte = read_byte_data(i2cbus, slave_addr, 21)
    diffctrl_bits = bitarray(format(diffctrl_byte, '08b'))
    # Extract values from data
    regs = LMK61E2Registers()
    regs.pll_d = int(pll_ctrl0_bits[2])
    regs.cp = int(pll_ctrl0_bits[4:8].to01(), 2)
    regs.ps = int(pll_ctrl1_bits[1:4].to01(), 2)
    regs.c3 = int(pll_ctrl1_bits[5])
    regs.dmc = int(mash_ctrl_bits[4:6].to01(), 2)
    regs.meo = int(mash_ctrl_bits[6:8].to01(), 2)
    regs.odf = LMK61E2ClockMode(int(diffctrl_bits[6:8].to01(), 2))
    raw_bits = bitarray(''.join([format(b, '08b') for b in data_in]))
    regs.out_div = int(raw_bits[7:16].to01(), 2)
    regs.int_div = int(raw_bits[28:40].to01(), 2)
    regs.frac_num = int(raw_bits[42:64].to01(), 2)
    regs.frac_den = int(raw_bits[66:88].to01(), 2)
    return regs

def regs2freq(regs: LMK61E2Registers) -> float:
    """ Compute frequency (Hz) from registers. """
    # Compute target frequency
    f_ref = 50.0*1E6
    frac_float = regs.frac_num/regs.frac_den if (regs.frac_den > 0 and regs.meo > 0) else 0
    freq_hz = f_ref*(2*regs.pll_d)*(regs.int_div + frac_float)
    freq_hz = freq_hz / regs.out_div
    # freq /= 1.0E6 # Put in megahertz
    return freq_hz

def freq2regs(freq_hz, odf: LMK61E2ClockMode = LMK61E2ClockMode.LVDS) -> LMK61E2Registers:
    """ Compute registers from frequency (Hz). ODF is clock mode (2 = LVDS). """
    regs = LMK61E2Registers()
    f_out = freq_hz # *1.0E6
    # Fixed values (Enable doubler by default)
    f_ref = 50.0*1.0E6
    regs.odf = LMK61E2ClockMode.LVDS.value
    regs.pll_d = 1
    # Step 1: Assume f_vco is in middle and determine out_div
    f_vco_middle = 5.0*1E9
    regs.out_div = int(round(f_vco_middle/f_out, 0))
    regs.out_div = max(min(regs.out_div, 511), 5) # [5, 511]
    f_vco_desired = f_out * regs.out_div
    if f_vco_desired < 4.6E9 or f_vco_desired > 5.6E9:
        raise Exception('Frequency not achievable- Fvco must be in range [4.6 GHz, 5.6 GHz]')
    # Step 2: Assume fractional portion is just 0 to determine int_div
    regs.int_div = int(math.floor(f_vco_desired/(f_ref * (2*regs.pll_d)) - (0/1)))
    regs.int_div = max(min(regs.int_div, 4095), 1)
    f_vco_approx = f_ref * (2*regs.pll_d) * (regs.int_div + 0/1)
    # Step 3: If f_vco still off then adjust fractional portion
    if abs(f_vco_approx - f_vco_desired) < 1E-9:
        regs.frac_num = int(0)
        regs.frac_den = int(1)
        regs.ps = 0  # No phase shift
        regs.dmc = 3  # Disabled
        regs.meo = 0  # Integer mode
        regs.cp = 8  # 6.4 mA
        # NOTE: 3rd order filter should be ENABLED when doubler is enabled.
        # However, chip default has it disabled for int mode w/ doubler enabled
        # c3 = 1 if regs.pll_d is 1 else 0
        regs.c3 = 0
    else:
        frac_float = f_vco_desired/(f_ref * (2*regs.pll_d)) - regs.int_div
        frac_num, frac_den = float2frac(frac_float)
        regs.frac_num = int(frac_num)
        regs.frac_den = int(frac_den)
        regs.ps = 2  # 1 ns for 100 MHz fPD phase shift
        regs.dmc = 0  # Weak
        regs.meo = 3  # 3rd order
        regs.cp = 4  # 1.6 mA
        regs.c3 = 1  # 3rd order filter enabled
    return regs

def set_registers(i2cbus, slave_addr: int, regs: LMK61E2Registers, nonvolatile=False):
    # Binarize data
    reg_data = bitarray(format(regs.out_div, '016b')  + # (7-bit 0 w/  9-bit OUTDIV)
                        format(0, '08b')         + # (Skip register 24)
                        format(regs.int_div, '016b')  + # (4-bit 0 w/ 12-bit INT)
                        format(regs.frac_num, '024b') + # (2-bit 0 w/ 22-bit NUM)
                        format(regs.frac_den, '024b'))  # (2-bit 0 w/ 22-bit DEN)

    #Turn this into a byte array of bytes to send
    regs_pll_data = [int(reg_data[i:i+8].to01(), 2) for i in range(0, len(reg_data), 8)]

    # Write to main block of registers
    write_i2c_block_data(i2cbus, slave_addr, 22, regs_pll_data)
    # Write mash engine data
    mash_ctrl_bits = bitarray(format(regs.dmc, '06b') + format(regs.meo, '02b'))
    write_i2c_block_data(i2cbus, slave_addr, 33, [int(mash_ctrl_bits[0:8].to01(), 2)])
    # Write pll_d and cp register data
    pll_ctrl0_bits = bitarray(format(regs.pll_d, '03b') + format(regs.cp, '05b'))
    write_i2c_block_data(i2cbus, slave_addr, 34, [int(pll_ctrl0_bits[0:8].to01(), 2)])
    pll_ctrl1_bits = bitarray(format(regs.ps, '04b') + '0' + format(regs.c3, '01b') + '11')
    write_i2c_block_data(i2cbus, slave_addr, 35, [int(pll_ctrl1_bits[0:8].to01(), 2)])
    diffctrl_bits = bitarray(format(regs.odf, '08b'))
    write_i2c_block_data(i2cbus, slave_addr, 21, [int(diffctrl_bits[0:8].to01(), 2)])

    # Save register data to EEPROM (via SRAM)
    if nonvolatile:
        write_i2c_block_data(i2cbus, slave_addr, 49, [0x50]) # Copy regs to sram
        # Check register R49.6 bit to see when done (== 0)
        done = False
        while not done:
            nvmctrlByte = read_byte_data(i2cbus, slave_addr, 49)
            nvmctrlBits = bitarray(format(nvmctrlByte, '08b'))
            done = int(nvmctrlBits[1]) == 0
            time.sleep(0.1)
        # Enable EEPROM write
        write_i2c_block_data(i2cbus, slave_addr, 56, [0xBE])
        # Perform EEPROM write
        write_i2c_block_data(i2cbus, slave_addr, 49, [0x11])
        time.sleep(0.1)
        done = False
        while not done:
            nvmctrlByte = read_byte_data(i2cbus, slave_addr, 49)
            nvmctrlBits = bitarray(format(nvmctrlByte, '08b'))
            done = int(nvmctrlBits[5]) == 0
        # Disable EEPROM write
        write_i2c_block_data(i2cbus, slave_addr, 56, [0x00])


def set_frequency(i2cbus, slave_addr: int, freq_hz: float,
                  odf: LMK61E2ClockMode=LMK61E2ClockMode.LVDS, nonvolatile: bool = False):
    regs = freq2regs(freq_hz, odf=odf)
    set_registers(i2cbus, slave_addr, regs, nonvolatile=nonvolatile)

def get_frequency(i2cbus, slave_addr):
    regs = get_registers(i2cbus, slave_addr)
    freq = regs2freq(regs)
    return freq, regs

