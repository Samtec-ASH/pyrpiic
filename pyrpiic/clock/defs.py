""" clock dataclass definitions """
from dataclasses import dataclass
from enum import Enum


class ClockType(str, Enum):
    LMK61E2 = 'LMK61E2'
    SI570 = 'SI570'


class LMK61E2ClockMode(int, Enum):
    TRISTATE = 0
    LVPECL = 1
    LVDS = 2
    HCSL = 3


@dataclass
class SI570Registers:
    hs_div: int = 0
    n1: int = 0
    f_req: float = 0
    reg_addr: int = 0x07


@dataclass
class LMK61E2Registers:
    pll_d: int = 1
    dmc: int = 0
    meo: int = 3
    cp: int = 4
    ps: int = 2
    c3: int = 1
    frac_num: int = 0
    frac_den: int = 1
    int_div: int = 0
    out_div: int = 1
    odf: LMK61E2ClockMode = LMK61E2ClockMode.LVDS
