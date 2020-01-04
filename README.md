# PyRPIIC

⚠️ **WARNING: This is a very early pre-release. Expect things to break.** ⚠️

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
from pyrpiic.clock import LMK612

# Create and open I2C bus
i2c_bus = I2C('/dev/i2c-3')
i2c_bus.open()

# Create clock
clock = LMK612(i2c_bus, 0x5A)

# Perform various clock operations
clock.set_frequency(156_250_000)
freq, regs = clock.get_frequency()
clock.regs2freq(regs)
clock.set_registers(regs)

# Close I2C bus
i2c_bus.close()
```
