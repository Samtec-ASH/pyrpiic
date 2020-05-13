# PyRPIIC

![./icon.png](./icon.png)

#### A [Py]thon 3 addon for [R]aspberry [Pi] that enables [i]nterfacing w/ a variety of low-level board [IC]s.

![PyPI](https://img.shields.io/pypi/v/pyrpiic)

# Compatibility

- Raspberry Pi Models: A, B (revisions 1.0 and 2.0), A+, B+, 2, 3, 3+, 3 A+, 4, Compute Module 3, Zero.
- Python 3.7+

# Install

Install the latest from PyPi:

`pip install pyrpiic`

_-OR-_ using **pipenv**:

`pipenv install pyrpiic`

Install from source:

`python3 setup.py install`

# Modules

## Clocks

- LMK612
- SI570

## EEPROMs

- Generic
- M24C02

## I2C-GPIO Expanders

- TCA6416A

## Sensors

- LDC1412
- LDC1414
- LDC1612
- LDC1614

# Examples

## Clocks (Programmable Oscillators)

```python

from pyrpio.i2c import I2C
from pyrpiic.clock.lmk61e2 import LMK61E2

# Create and open I2C-3 bus
i2c3 = I2C('/dev/i2c-3')
i2c3.open()

# Create clock
clock = LMK61E2(i2c3, 0x5A)

# Perform various clock operations
clock.set_frequency(156_250_000)
freq, regs = clock.get_frequency()
clock.regs2freq(regs)
clock.set_registers(regs)

# Close I2C-3 bus
i2c3.close()
```

## I2C-GPIO Expanders

```python

from pyrpio.i2c import I2C
from pyrpiic.ioexpander.tca6416a import TCA6416A

# Create and open I2C-3 bus
i2c3 = I2C('/dev/i2c-3')
i2c3.open()

# Create gpio expander
gpio_exp = TCA6416A(i2c3, 0x21)

# Set GPIO P00 as output pulled high
gpio_exp.set_gpio_direction('P00', 'OUT')
gpio_exp.set_gpio_output('P00', high=True)

# Set GPIO P01 as input w/ flipped polarity and read value
gpio_exp.set_gpio_direction('P01', 'IN')
gpio_exp.set_gpio_polarity('P01', flipped=True)
gpio_exp.get_gpio_input('P01')

# Close I2C-3 bus
i2c3.close()
```
