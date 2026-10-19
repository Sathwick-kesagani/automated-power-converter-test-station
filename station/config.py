"""Bench configuration. Edit this file once you know your lab's instruments.

Find each VISA address by running:  python -m station.find_instruments
"""

# ---- Instrument addresses (only used with --hw) ----
PSU_ADDRESS = "USB0::0x1AB1::0x0E11::DP8C000000000::INSTR"     # bench power supply
PSU_MODEL = "rigol_dp800"      # "rigol_dp800" or "keysight_e36xx"
PSU_CHANNEL = 1

DMM_ADDRESS = "USB0::0x2A8D::0x1301::MY00000000::INSTR"        # digital multimeter (Keysight 34461A style)

SCOPE_ADDRESS = "USB0::0x1AB1::0x04CE::DS1ZA000000000::INSTR"  # oscilloscope
SCOPE_MODEL = "rigol_ds1000z"  # "rigol_ds1000z" or "keysight_infiniivision"
SCOPE_CHANNEL = 1

# Load: "eload" = programmable electronic load (Rigol DL3021 style),
#       "manual" = power resistors you swap by hand (the script pauses and tells you which one).
LOAD_TYPE = "manual"
ELOAD_ADDRESS = "USB0::0x1AB1::0x0E11::DL3A000000000::INSTR"
MANUAL_RESISTORS_OHM = {"light": 33.0, "half": 10.0, "full": 5.0}   # resistors you own

# ---- Device under test: buck converter set to 5 V output ----
DUT_NAME = "LM2596 buck module"
DUT_SERIAL = "BOARD-001"
VIN_NOMINAL = 12.0                 # V
VIN_SWEEP = [7.0, 9.0, 12.0, 15.0, 20.0]   # V, line regulation sweep (stay inside the module's rating)
VOUT_TARGET = 5.0                  # V, set with the module's trimmer before testing
INPUT_CURRENT_LIMIT = 2.0          # A, protects the board

# Load points as output current (A) when using an electronic load
LOAD_POINTS_A = {"light": 0.15, "half": 0.5, "full": 1.0}

# ---- Pass/fail limits (take these from the converter datasheet) ----
LIMITS = {
    "vout_tolerance_pct": 4.0,      # output within +/-4% of target
    "line_regulation_pct": 2.0,     # max Vout change across the Vin sweep
    "load_regulation_pct": 3.0,     # max Vout change from light to full load
    "efficiency_min_pct": {"light": 60.0, "half": 75.0, "full": 75.0},
    "ripple_max_mvpp": 80.0,        # output ripple, peak-to-peak
    "startup_settle_max_s": 1.0,    # time for Vout to settle after power-on
}
