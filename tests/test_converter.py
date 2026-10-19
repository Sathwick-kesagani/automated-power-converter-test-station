"""Characterization tests for a buck converter. Limits live in station/config.py."""
import time

import pytest

from station import config

L = config.LIMITS


def test_01_output_voltage_at_nominal(bench):
    bench.power_on(config.VIN_NOMINAL)
    bench.set_load("half")
    vout = bench.measure_point()["vout"]
    lo = config.VOUT_TARGET * (1 - L["vout_tolerance_pct"] / 100)
    hi = config.VOUT_TARGET * (1 + L["vout_tolerance_pct"] / 100)
    ok = lo <= vout <= hi
    bench.record("output_voltage", "vout", vout, "V", round(lo, 3), round(hi, 3), ok)
    assert ok, f"Vout {vout:.3f} V outside {lo:.3f}-{hi:.3f} V"


@pytest.mark.parametrize("load", ["light", "half", "full"])
def test_02_efficiency(bench, load):
    bench.power_on(config.VIN_NOMINAL)
    bench.set_load(load)
    p = bench.measure_point()
    lo = L["efficiency_min_pct"][load]
    ok = p["eff_pct"] >= lo
    bench.record("efficiency", f"eff_{load}", p["eff_pct"], "%", lo, None, ok,
                 vin=p["vin"], iin=p["iin"], vout=p["vout"], iout=p["iout"])
    assert ok, f"Efficiency {p['eff_pct']:.1f}% at {load} load is below {lo}%"


def test_03_line_regulation(bench):
    bench.set_load("half")
    vouts = []
    for vin in config.VIN_SWEEP:
        bench.power_on(vin)
        p = bench.measure_point()
        vouts.append(p["vout"])
        bench.record("line_sweep", "vout_vs_vin", p["vout"], "V", None, None, True, vin=vin)
    reg = 100 * (max(vouts) - min(vouts)) / config.VOUT_TARGET
    ok = reg <= L["line_regulation_pct"]
    bench.record("line_regulation", "line_reg", reg, "%", None, L["line_regulation_pct"], ok)
    bench.power_on(config.VIN_NOMINAL)
    assert ok, f"Line regulation {reg:.2f}% exceeds {L['line_regulation_pct']}%"


def test_04_load_regulation(bench):
    bench.power_on(config.VIN_NOMINAL)
    v = {}
    for load in ["light", "half", "full"]:
        bench.set_load(load)
        p = bench.measure_point()
        v[load] = p["vout"]
        bench.record("load_sweep", "vout_vs_iout", p["vout"], "V", None, None, True, iout=p["iout"])
    reg = 100 * (v["light"] - v["full"]) / config.VOUT_TARGET
    ok = abs(reg) <= L["load_regulation_pct"]
    bench.record("load_regulation", "load_reg", reg, "%", None, L["load_regulation_pct"], ok)
    assert ok, f"Load regulation {reg:.2f}% exceeds {L['load_regulation_pct']}%"


def test_05_output_ripple(bench):
    bench.power_on(config.VIN_NOMINAL)
    bench.set_load("full")
    bench.scope.setup_ripple()
    mv = 1000 * bench.scope.ripple_vpp()
    ok = mv <= L["ripple_max_mvpp"]
    bench.record("ripple", "ripple_full_load", mv, "mVpp", None, L["ripple_max_mvpp"], ok)
    assert ok, f"Ripple {mv:.1f} mVpp exceeds {L['ripple_max_mvpp']} mVpp"


def test_06_startup_settling(bench):
    bench.set_load("half")
    bench.power_off()
    time.sleep(1.0 if bench.hardware else 0)
    lo = config.VOUT_TARGET * (1 - L["vout_tolerance_pct"] / 100)
    t0 = time.monotonic()
    bench.power_on(config.VIN_NOMINAL)
    settled = None
    while time.monotonic() - t0 < 3.0:
        if bench.dmm.measure_dc_voltage() >= lo:
            settled = time.monotonic() - t0
            break
    settled = 99.0 if settled is None else settled
    ok = settled <= L["startup_settle_max_s"]
    bench.record("startup", "settle_time", settled, "s", None, L["startup_settle_max_s"], ok)
    assert ok, f"Output took {settled:.2f} s to settle"
