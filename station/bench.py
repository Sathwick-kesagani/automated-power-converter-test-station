"""Opens the bench (real or simulated) and provides the measurement helpers the tests use."""
import csv
import datetime as dt
import os
import time

from . import config

RESULTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "results")


class ManualLoad:
    """For labs without an electronic load: pauses so you can swap power resistors."""

    def __init__(self, psu, dmm):
        self.psu, self.dmm, self.current_point = psu, dmm, None

    def idn(self):
        return "MANUAL,ResistorLoad," + ",".join(f"{k}={v}ohm" for k, v in config.MANUAL_RESISTORS_OHM.items())

    def set_point(self, name):
        if name != self.current_point:
            self.psu.output(False)
            input(f"\n>>> Connect the '{name}' resistor ({config.MANUAL_RESISTORS_OHM[name]} ohm) "
                  "to the converter output, then press Enter...")
            self.psu.output(True)
            time.sleep(0.5)
            self.current_point = name

    def output_current(self, vout):
        return vout / config.MANUAL_RESISTORS_OHM[self.current_point]

    def close(self):
        pass


class Bench:
    def __init__(self, hardware=False):
        self.hardware = hardware
        if hardware:
            import pyvisa
            from .instruments import ElectronicLoad, Multimeter, Oscilloscope, PowerSupply
            rm = pyvisa.ResourceManager()
            self.psu = PowerSupply(rm, config.PSU_ADDRESS, config.PSU_MODEL, config.PSU_CHANNEL)
            self.dmm = Multimeter(rm, config.DMM_ADDRESS)
            self.scope = Oscilloscope(rm, config.SCOPE_ADDRESS, config.SCOPE_MODEL, config.SCOPE_CHANNEL)
            self.load = (ElectronicLoad(rm, config.ELOAD_ADDRESS) if config.LOAD_TYPE == "eload"
                         else ManualLoad(self.psu, self.dmm))
        else:
            from .simulated import make_sim_bench
            sim = make_sim_bench()
            self.psu, self.dmm, self.scope, self.load = sim["psu"], sim["dmm"], sim["scope"], sim["load"]
        self.rows = []

    # ---- helpers used by the tests ----
    def power_on(self, vin=config.VIN_NOMINAL):
        self.psu.set(vin, config.INPUT_CURRENT_LIMIT)
        self.psu.output(True)
        time.sleep(0.3 if self.hardware else 0)

    def power_off(self):
        self.psu.output(False)

    def set_load(self, name):
        if isinstance(self.load, ManualLoad):
            self.load.set_point(name)
        else:
            self.load.set_current(config.LOAD_POINTS_A[name])
            self.load.input(True)
        time.sleep(0.3 if self.hardware else 0)

    def measure_point(self):
        """Returns one operating point: Vin, Iin, Vout, Iout, Pin, Pout, efficiency."""
        vin = self.psu.measure_voltage()
        iin = self.psu.measure_current()
        vout = self.dmm.measure_dc_voltage()
        iout = (self.load.output_current(vout) if isinstance(self.load, ManualLoad)
                else self.load.measure_current())
        pin, pout = vin * iin, vout * iout
        eff = 100.0 * pout / pin if pin > 0 else 0.0
        return dict(vin=vin, iin=iin, vout=vout, iout=iout, pin=pin, pout=pout, eff_pct=eff)

    def record(self, test, measurement, value, unit, low, high, passed, **extra):
        self.rows.append(dict(timestamp=dt.datetime.now().isoformat(timespec="seconds"),
                              test=test, measurement=measurement, value=round(value, 5), unit=unit,
                              low="" if low is None else low, high="" if high is None else high,
                              result="PASS" if passed else "FAIL",
                              **{k: round(v, 5) if isinstance(v, float) else v for k, v in extra.items()}))

    def instrument_ids(self):
        return {k: getattr(self, k).idn() for k in ("psu", "dmm", "scope", "load")}

    def save_csv(self):
        os.makedirs(RESULTS_DIR, exist_ok=True)
        path = os.path.join(RESULTS_DIR, "results.csv")
        keys = sorted({k for r in self.rows for k in r},
                      key=lambda k: ["timestamp", "test", "measurement", "value", "unit", "low", "high", "result"].index(k)
                      if k in ["timestamp", "test", "measurement", "value", "unit", "low", "high", "result"] else 99)
        with open(path, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=keys)
            w.writeheader()
            w.writerows(self.rows)
        return path

    def close(self):
        try:
            self.power_off()
        finally:
            for inst in (self.psu, self.dmm, self.scope, self.load):
                inst.close()
