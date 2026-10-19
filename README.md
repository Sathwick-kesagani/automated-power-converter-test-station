# Automated Power Converter Test Station

[![Converter test suite](https://github.com/Sathwick-kesagani/automated-power-converter-test-station/actions/workflows/ci.yml/badge.svg)](https://github.com/Sathwick-kesagani/automated-power-converter-test-station/actions/workflows/ci.yml)

Python test automation that drives lab instruments (bench power supply, digital multimeter,
oscilloscope and an optional electronic load) over SCPI/PyVISA to characterize a DC-DC buck
converter: output accuracy, efficiency, line and load regulation, ripple, and start-up.
Every run produces a CSV log, plots, and a pass/fail test report. A simulated bench lets the
full suite run in CI with no hardware.

> **Status:** the full suite passes on the simulated bench (see [sample report](docs/sample-report)).
> Runs on real lab instruments with an LM2596 buck module are in progress; hardware results,
> photos and wiring will be added here when done.

---

## What it tests

| # | Test | What it checks | Default limit |
|---|---|---|---|
| 1 | Output voltage | Vout at 12 V in, half load | 5.0 V ±4% |
| 2 | Efficiency | Pout / Pin at light, half, full load | ≥60% / 75% / 75% |
| 3 | Line regulation | Vout change while Vin sweeps 7–20 V | ≤2% |
| 4 | Load regulation | Vout change from light to full load | ≤3% |
| 5 | Ripple | Output ripple at full load (scope, AC coupled) | ≤80 mVpp |
| 6 | Start-up | Time for Vout to settle after power-on | ≤1 s |

Limits live in `station/config.py`. Replace them with values from your converter's datasheet.

## Project layout

```
station/
  config.py            # instrument addresses, DUT settings, pass/fail limits
  instruments.py       # SCPI drivers: PowerSupply, Multimeter, Oscilloscope, ElectronicLoad
  simulated.py         # realistic simulated converter + instruments (used by default and in CI)
  bench.py             # opens the bench, measurement helpers, CSV logging
  report.py            # plots + Markdown report from the CSV
  find_instruments.py  # lists connected instruments and their VISA addresses
tests/
  conftest.py          # pytest fixture; --hw switches to real instruments
  test_converter.py    # the 6 characterization tests
.github/workflows/ci.yml  # runs the suite on the simulated bench on every push
```

---

## Step-by-step build guide

### Phase 1 – On your laptop (no hardware needed, day 1)

1. **Install Python 3.10+** from python.org (tick "Add Python to PATH" on Windows).
2. **Get the code:** unzip this folder, open a terminal inside it.
3. **Create a virtual environment and install packages:**
   ```bash
   python -m venv .venv
   # Windows: .venv\Scripts\activate     macOS/Linux: source .venv/bin/activate
   pip install -r requirements.txt
   ```
4. **Run the suite on the simulated bench:**
   ```bash
   pytest
   python -m station.report
   ```
   Open `results/report.md` to see the report and plots.
5. **Read every file once** so you can explain it in interviews. Start with `tests/test_converter.py`,
   then `station/bench.py`, then `station/instruments.py`.
6. **Make it yours:** try changing a limit in `config.py` so a test fails, and watch the report show FAIL.
   Interviewers love asking "how would you know if your test is wrong?" This is the answer.

### Phase 2 – Parts and lab access (week 1)

7. **Buy the board:** an LM2596 or MP1584 buck converter module (about $10 for a 3-pack on Amazon).
   Set its output to 5.0 V with the trimmer screw, using a multimeter, before testing.
8. **Buy loads (if your lab has no electronic load):** power resistors of about 33 Ω, 10 Ω and 5 Ω,
   each rated **10 W or more**. They get hot, so mount them on a heat-safe surface.
9. **Ask your lab manager** for bench time with:
   - a programmable power supply (Rigol DP832 or Keysight E36xx)
   - a digital multimeter (Keysight 34461A or similar)
   - an oscilloscope with USB or LAN (Rigol DS1000Z or Keysight InfiniiVision)
   - optional: an electronic load (Rigol DL3021)

   Tell them it's for a test-automation portfolio project. Most labs say yes.

### Phase 3 – Connect the real instruments (week 2)

10. **Install VISA on the lab PC:** Keysight IO Libraries Suite or NI-VISA (both free).
11. **Wire the bench** (power supply OFF while wiring):
    - Power supply + / − → converter **IN+ / IN−**
    - Load (resistor or electronic load) → converter **OUT+ / OUT−**
    - Multimeter (DC volts) → directly on **OUT+ / OUT−** at the board
    - Scope probe → OUT+, ground spring (not the long ground lead) → OUT−, as close to the board as possible
12. **Set a current limit** on the supply (2 A by default in `config.py`) before turning anything on.
13. **Find the instrument addresses:**
    ```bash
    python -m station.find_instruments
    ```
    Copy each address into `station/config.py`, and set `PSU_MODEL`, `SCOPE_MODEL` and `LOAD_TYPE`
    (`"eload"` or `"manual"`).
14. **Run against the real bench:**
    ```bash
    pytest --hw
    python -m station.report
    ```
    With `LOAD_TYPE = "manual"`, the script pauses and tells you which resistor to connect.
15. **Debug like a test engineer:** if a reading looks wrong, compare it with the instrument's
    front panel. Write down each problem and fix in a `NOTES.md`. These are great interview stories.

### Phase 4 – Polish and publish (week 3)

16. **Run 3 boards** (BOARD-001, 002, 003) by changing `DUT_SERIAL`, and compare results.
    This turns it into a small production-test study.
17. **Take photos** of the bench setup and record a 1-minute video of a run.
18. **Push your hardware results** to this repo (it is already on GitHub). Commit the CSV, the
    report and the plots from `results/` into a `docs/hardware-run-1/` folder. GitHub Actions keeps
    running the simulated suite on every push.
19. **Update this README:** replace the Status note with your real results table, photos, a wiring
    diagram and the video link.
20. **Send the repo link to Claude** to add the project to your resumes and LinkedIn.

---

## SCPI commands used

| Instrument | Command | Meaning |
|---|---|---|
| Rigol DP800 | `:APPL CH1,12,2` | set 12 V, 2 A limit |
| Rigol DP800 | `:OUTP CH1,ON` | output on |
| Rigol DP800 | `:MEAS:CURR? CH1` | measure input current |
| Keysight 34461A | `MEAS:VOLT:DC?` | measure DC voltage |
| Rigol DS1000Z | `:MEAS:ITEM? VPP,CHAN1` | peak-to-peak ripple |
| Rigol DL3021 | `:SOUR:CURR:LEV:IMM 1` | sink 1 A |

## Safety

- Stay below the converter's input rating (usually 24–28 V for LM2596 modules).
- Always set the supply's current limit before turning the output on.
- Power resistors get hot. Don't touch them during or right after a test.

## Ideas to extend

- Add an efficiency map across Vin × load (heatmap).
- Add a transient-response test using the electronic load's dynamic mode.
- Save results to SQLite and track boards over time.
- Add a thermal test with a thermocouple logger.
