"""Lists every instrument connected to this PC and asks each for its name.

Run:  python -m station.find_instruments
Copy the addresses into station/config.py.
"""
import pyvisa


def main():
    rm = pyvisa.ResourceManager()
    found = rm.list_resources()
    if not found:
        print("No instruments found. Check the USB/LAN cable and that NI-VISA or Keysight IO Libraries is installed.")
    for addr in found:
        try:
            inst = rm.open_resource(addr)
            inst.timeout = 2000
            print(f"{addr}\n    -> {inst.query('*IDN?').strip()}")
            inst.close()
        except Exception as e:  # some ports (e.g. serial) don't answer *IDN?
            print(f"{addr}\n    -> no reply ({e.__class__.__name__})")


if __name__ == "__main__":
    main()
