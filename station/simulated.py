"""Simulated bench: a realistic buck-converter model behind the same methods as the
real drivers. Lets the whole suite run on a laptop or in GitHub Actions with no hardware.
"""
import random

from . import config


class _Converter:
    """Shared electrical state of the simulated board."""

    def __init__(self, seed=42):
        self.rng = random.Random(seed)
        self.vin = 0.0
        self.on = False
        self.load_a = config.LOAD_POINTS_A["light"]

    def vout(self):
        if not self.on or self.vin < config.VOUT_TARGET + 1.5:   # dropout
            return 0.0
        v = config.VOUT_TARGET
        v += 0.004 * (self.vin - config.VIN_NOMINAL)             # small line sensitivity
        v -= 0.035 * self.load_a                                  # small load droop
        return v + self.rng.gauss(0, 0.002)

    def efficiency(self):
        i = max(self.load_a, 0.01)
        eff = 0.88 - 0.10 / (1 + 12 * i) - 0.004 * (self.vin - config.VIN_NOMINAL)
        return max(0.3, min(eff, 0.95))

    def iin(self):
        vout = self.vout()
        if vout == 0 or self.vin == 0:
            return 0.0
        pout = vout * self.load_a
        return pout / self.efficiency() / self.vin + 0.004       # plus quiescent current

    def ripple(self):
        return 0.018 + 0.03 * self.load_a + self.rng.gauss(0, 0.002)


class SimPowerSupply:
    def __init__(self, board):
        self.b = board

    def idn(self):
        return "SIMULATED,PowerSupply,0,1.0"

    def set(self, volts, amps):
        self.b.vin = volts

    def output(self, on):
        self.b.on = on

    def measure_voltage(self):
        return self.b.vin if self.b.on else 0.0

    def measure_current(self):
        return self.b.iin()

    def close(self):
        pass


class SimMultimeter:
    def __init__(self, board):
        self.b = board

    def idn(self):
        return "SIMULATED,Multimeter,0,1.0"

    def measure_dc_voltage(self):
        return self.b.vout()

    def close(self):
        pass


class SimOscilloscope:
    def __init__(self, board):
        self.b = board

    def idn(self):
        return "SIMULATED,Oscilloscope,0,1.0"

    def setup_ripple(self):
        pass

    def ripple_vpp(self):
        return self.b.ripple()

    def close(self):
        pass


class SimElectronicLoad:
    def __init__(self, board):
        self.b = board

    def idn(self):
        return "SIMULATED,ElectronicLoad,0,1.0"

    def set_current(self, amps):
        self.b.load_a = amps

    def input(self, on):
        pass

    def measure_current(self):
        return self.b.load_a

    def close(self):
        pass


def make_sim_bench():
    board = _Converter()
    return {
        "psu": SimPowerSupply(board),
        "dmm": SimMultimeter(board),
        "scope": SimOscilloscope(board),
        "load": SimElectronicLoad(board),
    }
