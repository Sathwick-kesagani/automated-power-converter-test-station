import json
import os

import pytest

from station.bench import RESULTS_DIR, Bench


def pytest_addoption(parser):
    parser.addoption("--hw", action="store_true", help="Run against real lab instruments (default: simulated bench)")


@pytest.fixture(scope="session")
def bench(request):
    b = Bench(hardware=request.config.getoption("--hw"))
    yield b
    path = b.save_csv()
    os.makedirs(RESULTS_DIR, exist_ok=True)
    with open(os.path.join(RESULTS_DIR, "run_info.json"), "w") as f:
        json.dump({"mode": "hardware" if b.hardware else "simulated", "instruments": b.instrument_ids()}, f, indent=2)
    b.close()
    print(f"\nResults saved to {path}")
