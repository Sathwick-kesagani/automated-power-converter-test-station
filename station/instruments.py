"""Instrument drivers. Each class wraps the SCPI commands for one instrument.

Only this file knows instrument-specific commands, so swapping a Rigol for a
Keysight means changing one class, not the tests.
"""
import time


class Instrument:
    def __init__(self, rm, address, timeout_ms=5000):
        self.res = rm.open_resource(address)
        self.res.timeout = timeout_ms

    def write(self, cmd):
        self.res.write(cmd)

    def query(self, cmd):
        return self.res.query(cmd).strip()

    def idn(self):
        return self.query("*IDN?")

    def close(self):
        self.res.close()


class PowerSupply(Instrument):
    """Bench supply feeding the converter input. Also measures input current."""

    def __init__(self, rm, address, model="rigol_dp800", channel=1):
        super().__init__(rm, address)
        self.model, self.ch = model, channel

    def set(self, volts, amps):
        if self.model == "rigol_dp800":
            self.write(f":APPL CH{self.ch},{volts:.3f},{amps:.3f}")
        else:  # keysight_e36xx
            self.write(f"VOLT {volts:.3f}")
            self.write(f"CURR {amps:.3f}")

    def output(self, on):
        if self.model == "rigol_dp800":
            self.write(f":OUTP CH{self.ch},{'ON' if on else 'OFF'}")
        else:
            self.write(f"OUTP {'ON' if on else 'OFF'}")

    def measure_voltage(self):
        cmd = f":MEAS:VOLT? CH{self.ch}" if self.model == "rigol_dp800" else "MEAS:VOLT?"
        return float(self.query(cmd))

    def measure_current(self):
        cmd = f":MEAS:CURR? CH{self.ch}" if self.model == "rigol_dp800" else "MEAS:CURR?"
        return float(self.query(cmd))


class Multimeter(Instrument):
    """Measures converter output voltage accurately (DMM at the output terminals)."""

    def measure_dc_voltage(self):
        return float(self.query("MEAS:VOLT:DC?"))


class Oscilloscope(Instrument):
    """Measures output ripple (AC coupled, 20 MHz bandwidth limit)."""

    def __init__(self, rm, address, model="rigol_ds1000z", channel=1):
        super().__init__(rm, address)
        self.model, self.ch = model, channel

    def setup_ripple(self):
        if self.model == "rigol_ds1000z":
            for c in (f":CHAN{self.ch}:COUP AC", f":CHAN{self.ch}:BWL 20M",
                      f":CHAN{self.ch}:SCAL 0.02", ":TIM:SCAL 0.00001", ":RUN"):
                self.write(c)
        else:
            for c in (f":CHANnel{self.ch}:COUPling AC", f":CHANnel{self.ch}:BWLimit ON",
                      f":CHANnel{self.ch}:SCALe 0.02", ":TIMebase:SCALe 10E-6", ":RUN"):
                self.write(c)
        time.sleep(1.0)

    def ripple_vpp(self):
        if self.model == "rigol_ds1000z":
            return float(self.query(f":MEAS:ITEM? VPP,CHAN{self.ch}"))
        return float(self.query(f":MEASure:VPP? CHANnel{self.ch}"))


class ElectronicLoad(Instrument):
    """Programmable DC load in constant-current mode (Rigol DL3021 style)."""

    def set_current(self, amps):
        self.write(":SOUR:FUNC CURR")
        self.write(f":SOUR:CURR:LEV:IMM {amps:.3f}")

    def input(self, on):
        self.write(f":SOUR:INP:STAT {'ON' if on else 'OFF'}")

    def measure_current(self):
        return float(self.query(":MEAS:CURR?"))
