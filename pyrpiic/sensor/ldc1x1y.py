from typing import Tuple, Optional
from pyrpio.i2c_register_device import I2CRegisterDevice
from pyrpio.i2c import I2C


class LDC1X1Y:
    ''' TI LDC1X1Y base class. This class should be subclassed only. '''

    # LDC1X1Y register addresses (do not change)
    LDC1X1Y_DATA_BASE = 0x00
    LDC1X1Y_DATA_MSB_CH0 = 0x00
    LDC1X1Y_DATA_LSB_CH0 = 0x01
    LDC1X1Y_DATA_MSB_CH1 = 0x02
    LDC1X1Y_DATA_LSB_CH1 = 0x03
    LDC1X1Y_DATA_MSB_CH2 = 0x04
    LDC1X1Y_DATA_LSB_CH2 = 0x05
    LDC1X1Y_DATA_MSB_CH3 = 0x06
    LDC1X1Y_DATA_LSB_CH3 = 0x07

    LDC1X1Y_REF_COUNT_BASE = 0x08
    LDC1X1Y_REF_COUNT_CH0 = 0x08
    LDC1X1Y_REF_COUNT_CH1 = 0x09
    LDC1X1Y_REF_COUNT_CH2 = 0x0A
    LDC1X1Y_REF_COUNT_CH3 = 0x0B

    LDC1X1Y_OFFSET_BASE = 0x0C
    LDC1X1Y_OFFSET_CH0 = 0x0C
    LDC1X1Y_OFFSET_CH1 = 0x0D
    LDC1X1Y_OFFSET_CH2 = 0x0E
    LDC1X1Y_OFFSET_CH3 = 0x0F

    LDC1X1Y_SETTLE_COUNT_BASE = 0x10
    LDC1X1Y_SETTLE_COUNT_CH0 = 0x10
    LDC1X1Y_SETTLE_COUNT_CH1 = 0x11
    LDC1X1Y_SETTLE_COUNT_CH2 = 0x12
    LDC1X1Y_SETTLE_COUNT_CH3 = 0x13

    LDC1X1Y_CLOCK_DIVIDERS_BASE = 0x14
    LDC1X1Y_CLOCK_DIVIDERS_CH0 = 0x14
    LDC1X1Y_CLOCK_DIVIDERS_CH1 = 0x15
    LDC1X1Y_CLOCK_DIVIDERS_CH2 = 0x16
    LDC1X1Y_CLOCK_DIVIDERS_CH3 = 0x17

    LDC1X1Y_STATUS = 0x18
    LDC1X1Y_ERROR_CONFIG = 0x19
    LDC1X1Y_CONFIG = 0x1A
    LDC1X1Y_MUX_CONFIG = 0x1B
    LDC1X1Y_RESET_DEV = 0x1C

    LDC1X1Y_DRIVE_CURRENT_BASE = 0x1E
    LDC1X1Y_DRIVE_CURRENT_CH0 = 0x1E
    LDC1X1Y_DRIVE_CURRENT_CH1 = 0x1F
    LDC1X1Y_DRIVE_CURRENT_CH2 = 0x20
    LDC1X1Y_DRIVE_CURRENT_CH3 = 0x21

    LDC1X1Y_MANUFACTURER_ID = 0x7E
    LDC1X1Y_DEVICE_ID = 0x7F

    def __init__(self, bus: I2C, address=0x2A):
        self.address = address
        self.i2c_reg = I2CRegisterDevice(bus, address, register_size=1, data_size=2)

    def close(self):
        ''' Close up access. '''
        return 0

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        self.close()

    def get_register(self, register: int, mask: Optional[int] = None) -> int:
        ''' Get single word length register. '''
        value = self.i2c_reg.read_register(register)
        if mask is not None:
            value = value & mask
        return value

    def set_register(self, register, value: int, mask: Optional[int] = None):
        ''' Set single word length register. '''
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
        ''' Set single bit of register. '''
        mask = 1 << bit
        pvalue = self.get_register(register, ~mask)
        self.set_register(register, pvalue | (int(on) << bit))

    def get_manufacturer_id(self) -> int:
        ''' Get manufacturer ID. '''
        return self.get_register(self.LDC1X1Y_MANUFACTURER_ID)

    def get_device_id(self):
        ''' Get device ID. '''
        return self.get_register(self.LDC1X1Y_DEVICE_ID)

    def get_channel_data(self, ch: int) -> Tuple[int, int]:
        ''' Get channel data and error flags. '''
        raise NotImplementedError()

    def get_channel_drive_current(self, ch: int) -> Tuple[int, int]:
        ''' Get channel L-C sensor drive current and computed sensor drive current
            Returns:
                int: Sensor drive current used during the settling + conversion time of channel.
                int: Initial and computed sensor drive current updated after each phase correction
        '''
        value = self.get_register(self.LDC1X1Y_DRIVE_CURRENT_BASE + ch)
        idrive = (value & 0xF800) >> 11
        init_idrive = (value & 0x07C0) >> 6
        return idrive, init_idrive

    def set_channel_drive_current(self, ch: int, value: int):
        ''' Set channel sensor drive current used during the settling +
            conversion time of channel.
            NOTE: RP_OVERRIDE_EN bit must be set to 1.
        '''
        self.set_register(self.LDC1X1Y_DRIVE_CURRENT_BASE + ch, (value & 0x001F) << 11)

    def get_channel_reference_count(self, ch: int) -> int:
        ''' Get channel reference clock count.
            0x0000-0x0004: Reserved
            0x0005-0xFFFF: Conversion Time (tC) = (RCOUNT x 16) / ƒREF
        '''
        return self.get_register(self.LDC1X1Y_REF_COUNT_BASE + ch)

    def set_channel_reference_count(self, ch: int, value: int):
        ''' Set channel reference clock count.
            0x0000-0x0004: Reserved
            0x0005-0xFFFF: Conversion Time (tC) = (RCOUNT x 16) / ƒREF
        '''
        if value <= 4:
            raise ValueError('Reference clock count must be > 4')
        return self.set_register(self.LDC1X1Y_REF_COUNT_BASE + ch, value)

    def get_channel_conversion_interval_time(self, ch: int, fref: float) -> float:
        ''' Derive conversion interval time from ƒCLK and ƒREF
            Conversion Time (tC) = (RCOUNT × 16) / ƒREF
        '''
        return 16*self.get_channel_reference_count(ch=ch)/fref

    def get_channel_reference_offset(self, ch: int) -> int:
        ''' Get channel reference clock offset.
            fOFFSET = (OFFSET ÷ 2^16) × ƒREF
        '''
        return self.get_register(self.LDC1X1Y_OFFSET_BASE + ch)

    def set_channel_reference_offset(self, ch: int, value: int):
        ''' Set channel reference clock offset.
            ƒOFFSET = (OFFSET ÷ 2^16) × ƒREF
        '''
        return self.set_register(self.LDC1X1Y_OFFSET_BASE + ch, value)

    def get_channel_reference_settling_count(self, ch: int) -> int:
        ''' Get channel reference settling count.
            0x0000: Settle Time (tS)= 32 ÷ ƒREF
            0x0001: Settle Time (tS)= 32 ÷ ƒREF
            0x0002 - 0xFFFF: Settle Time (tS)= (SETTLECOUNT x 16) ÷ ƒREF
            NOTE: If the amplitude has not settled prior to the conversion start,
            an Amplitude error will be generated if reporting of this type of error is enabled.
        '''
        return self.get_register(self.LDC1X1Y_SETTLE_COUNT_BASE + ch)

    def set_channel_reference_settling_count(self, ch: int, value: int):
        ''' Set channel reference settling count.
            0x0000: Settle Time (tS) = 32 ÷ ƒREF
            0x0001: Settle Time (tS) = 32 ÷ ƒREF
            0x0002 - 0xFFFF: Settle Time (tS) = (SETTLECOUNT x 16) ÷ ƒREF
            NOTE: If the amplitude has not settled prior to the conversion start,
            an Amplitude error will be generated if reporting of this type of error is enabled.
        '''
        return self.set_register(self.LDC1X1Y_SETTLE_COUNT_BASE + ch, value)

    def get_channel_clock_dividers(self, ch: int) -> Tuple[int, int]:
        ''' Get clock dividers: ƒIN_DIV and ƒREF_DIV
            ƒIN_DIV must be set to ≥ 2 if the Sensor frequency is ≥ 8.75MHz
            ƒIN_DIV ≥ b0001:  ƒin0 = ƒSENSOR/ƒIN_DIV
            ƒREF_DIV is used to scale the maximum conversion frequency.
            ƒREF_DIV ≥ 0x001:  ƒREF = ƒCLK/ƒREF_DIV
        '''
        reg = self.get_register(self.LDC1X1Y_CLOCK_DIVIDERS_BASE + ch)
        fin_dev = (reg & 0xF000) >> 12
        fref_dev = (reg & 0x03FF) >> 0
        return fin_dev, fref_dev

    def set_channel_clock_dividers(self, ch: int, fin_dev: int, fref_dev: int):
        ''' Get clock dividers: fIN_DIV and fREF_DIV
            ƒIN_DIV must be set to ≥ 2 if the Sensor frequency is ≥ 8.75MHz
            ƒIN_DIV ≥ b0001: ƒin0 = ƒSENSOR/ƒIN_DIV
            ƒREF_DIV is used to scale the maximum conversion frequency.
            ƒREF_DIV ≥ 0x001:
            ƒREF0 = ƒCLK/ƒREF_DIV
        '''
        value = ((fin_dev & 0x000F) << 12) | (fref_dev & 0x03FF)
        self.set_register(self.LDC1X1Y_CLOCK_DIVIDERS_BASE + ch, value)

    def get_status_errors(self):
        ''' Get errors reported in status register.
            0xC0 - Channel bits CH0:0b00, CH1:0b01, CH2:0b10, CH3:0b11
            0x20: Under range error bit
            0x10: Over range error bit
            0x08: Watchdog timeout error bit
            0x04: Amplitude high error bit
            0x02: Amplitude low error bit
            0x01: Zero crossing error bit
        '''
        value = self.get_register(self.LDC1X1Y_STATUS) >> 8
        return value

    def device_reset(self):
        ''' Resets entire device to default values. '''
        self.set_register_bit(self.LDC1X1Y_RESET_DEV, 15, True)

    @property
    def high_current_drive(self):
        ''' High Current Sensor Drive
            b0: The LDC will drive all channels with normal sensor current (1.5mA max).
            b1: The LDC will drive channel 0 with current >1.5mA.
            NOTE: This mode is not supported if AUTOSCAN_EN = b1 (multi-channel mode).
        '''
        return self.get_register_bit(self.LDC1X1Y_CONFIG, 6)

    @high_current_drive.setter
    def high_current_drive(self, enable: bool):
        self.set_register_bit(self.LDC1X1Y_CONFIG, 6, enable)

    @property
    def status_update_interrupt_enable(self):
        ''' Enables status updates triggering interrupt pin. '''
        return self.get_register_bit(self.LDC1X1Y_CONFIG, 7)

    @status_update_interrupt_enable.setter
    def status_update_interrupt_enable(self, enable: bool):
        ''' Enable/disable status updates triggering interrupt pin. '''
        self.set_register_bit(self.LDC1X1Y_CONFIG, 7, enable)

    @property
    def reference_clock_external(self):
        ''' Enable external reference clock instead of internal oscillator. '''
        return self.get_register_bit(self.LDC1X1Y_CONFIG, 9)

    @reference_clock_external.setter
    def reference_clock_external(self, enable: bool):
        ''' Enable external reference clock or use internal oscillator. '''
        self.set_register_bit(self.LDC1X1Y_CONFIG, 9, enable)

    @property
    def automatic_amplitude_correction(self):
        ''' Use automatic amplitude correction.
            NOTE: Disable automatic correction for high precision applications.
        '''
        return not self.get_register_bit(self.LDC1X1Y_CONFIG, 10)

    @automatic_amplitude_correction.setter
    def automatic_amplitude_correction(self, enable: bool):
        return self.set_register_bit(self.LDC1X1Y_CONFIG, 10, not enable)

    @property
    def low_power_activation_mode(self):
        ''' Use low power sense mode- the LDC uses the value programmed in
            DRIVE_CURRENTx during sensor activation to minimize power consumption.
        '''
        return self.get_register_bit(self.LDC1X1Y_CONFIG, 11)

    @low_power_activation_mode.setter
    def low_power_activation_mode(self, enable: bool):
        self.set_register_bit(self.LDC1X1Y_CONFIG, 11, enable)

    @property
    def current_override_enable(self):
        ''' Provides control over sensor current drive used during the conversion time
            for Ch. x, based on the programmed value in the IDRIVEx field
        '''
        return self.get_register_bit(self.LDC1X1Y_CONFIG, 12)

    @current_override_enable.setter
    def current_override_enable(self, enable: bool):
        self.set_register_bit(self.LDC1X1Y_CONFIG, 12, enable)

    @property
    def sleep_mode(self):
        ''' Sleep mode or active mode. '''
        return self.get_register_bit(self.LDC1X1Y_CONFIG, 13)

    @sleep_mode.setter
    def sleep_mode(self, enable: bool):
        self.set_register_bit(self.LDC1X1Y_CONFIG, 13, enable)

    @property
    def data_ready(self):
        ''' A new conversion result is ready.
            When in Single Channel Conversion, this indicates a single conversion
            is available. When in sequential mode, this indicates that a new
            conversion result for all active channels is now available.
        '''
        return self.get_register_bit(self.LDC1X1Y_STATUS, 6)

    def channel_data_ready(self, ch: int):
        ''' New channel conversion result is ready. '''
        reg = self.get_register(self.LDC1X1Y_STATUS)
        return bool(reg & 0x000F & (1 << (3-ch)))

    def configure_single_active_channel(self, ch: int):
        ''' Configure single active channel for continuous sampling. '''
        self.set_register(self.LDC1X1Y_CONFIG, ch << 14, 0xC000)
        self.set_register(self.LDC1X1Y_MUX_CONFIG, 0, 0xE000)

    def configure_sequential_channels(self, num_chs: int):
        ''' Configure sequential channels for continuous sampling.
            b00: Ch0, Ch1
            b01: Ch0, Ch1, Ch2 (LDC1X14 only)
            b10: Ch0, Ch1, Ch2, Ch3 (LDC1X14 only)
            b11: Ch0, Ch1
            Args:
                num_chs (int): Number of sequential channels
        '''
        seq_ch_map = {2: 0b100, 3: 0b101, 4: 0b110}
        seq_val = seq_ch_map[num_chs]
        self.set_register(self.LDC1X1Y_MUX_CONFIG, seq_val, 0xE000)

    def get_deglitch_filter_value(self) -> int:
        ''' Input Deglitch Filter Bandwidth
            0b001: 1.0 MHz | 0b100: 3.3 MHz | 0b101: 10 MHz | 0b111: 33 MHz
            Returns:
                int: raw register value
        '''
        value = self.get_register(self.LDC1X1Y_MUX_CONFIG, mask=0x0007)
        return value

    def get_deglitch_filter_frequency(self) -> float:
        ''' Input Deglitch Filter Bandwidth
            0b001: 1.0 MHz | 0b100: 3.3 MHz | 0b101: 10 MHz | 0b111: 33 MHz
            Returns:
                float: frequency in Hz
        '''
        bwid_val = self.get_deglitch_filter_value()
        bwid_map = {0b001: 1.0e6, 0b100: 3.3e6, 0b101: 10e6, 0b111: 33e6}
        bwid_freq = bwid_map[bwid_val]
        return bwid_freq

    def set_deglitch_filter_value(self, value: int):
        ''' Input Deglitch Filter Bandwidth
            Select the lowest setting that exceeds the maximum
            sensor oscillation frequency.
            0b001: 1.0 MHz | 0b100: 3.3 MHz | 0b101: 10 MHz | 0b111: 33 MHz
            Args:
                value (int): raw register value
        '''
        self.set_register(self.LDC1X1Y_MUX_CONFIG, value, mask=0x007)

    def set_deglitch_filter_frequency(self, freq: float):
        ''' Input Deglitch Filter Bandwidth
            Select the lowest setting that exceeds the maximum
            sensor oscillation frequency.
            0b001: 1.0 MHz | 0b100: 3.3 MHz | 0b101: 10 MHz | 0b111: 33 MHz
            Args:
                freq (float): Bandwidth frequency
        '''
        bwid_map = {1.0e6: 0b001, 3.3e6: 0b100, 10e6: 0b101, 33e6: 0b111}
        min_dist = freq
        bwid_freq = None
        bwid_val = 0b111
        for mf, mv in bwid_map.items():
            dist = abs(freq - mf)
            if dist < min_dist:
                min_dist = dist
                bwid_val = mv
                bwid_freq = mf
        print(f'Using closest frequency: {bwid_freq}')
        self.set_deglitch_filter_value(bwid_val)
