"""Builds plots and a Markdown test report from results/results.csv.

Run:  python -m station.report
"""
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from . import config
from .bench import RESULTS_DIR


def main():
    df = pd.read_csv(os.path.join(RESULTS_DIR, "results.csv"))
    info = json.load(open(os.path.join(RESULTS_DIR, "run_info.json")))
    plots = []

    eff = df[df.test == "efficiency"]
    if len(eff):
        plt.figure(figsize=(5, 3.2))
        plt.plot(eff.iout, eff.value, "o-")
        plt.xlabel("Output current (A)"); plt.ylabel("Efficiency (%)"); plt.title("Efficiency vs load")
        plt.grid(alpha=.3); plt.tight_layout()
        plt.savefig(os.path.join(RESULTS_DIR, "efficiency.png"), dpi=150); plt.close()
        plots.append(("Efficiency vs load", "efficiency.png"))

    line = df[df.test == "line_sweep"]
    if len(line):
        plt.figure(figsize=(5, 3.2))
        plt.plot(line.vin, line.value, "o-")
        plt.axhline(config.VOUT_TARGET, ls="--", c="gray")
        plt.xlabel("Input voltage (V)"); plt.ylabel("Output voltage (V)"); plt.title("Line regulation")
        plt.grid(alpha=.3); plt.tight_layout()
        plt.savefig(os.path.join(RESULTS_DIR, "line_regulation.png"), dpi=150); plt.close()
        plots.append(("Line regulation", "line_regulation.png"))

    load = df[df.test == "load_sweep"]
    if len(load):
        plt.figure(figsize=(5, 3.2))
        plt.plot(load.iout, load.value, "o-")
        plt.axhline(config.VOUT_TARGET, ls="--", c="gray")
        plt.xlabel("Output current (A)"); plt.ylabel("Output voltage (V)"); plt.title("Load regulation")
        plt.grid(alpha=.3); plt.tight_layout()
        plt.savefig(os.path.join(RESULTS_DIR, "load_regulation.png"), dpi=150); plt.close()
        plots.append(("Load regulation", "load_regulation.png"))

    checks = df[~df.test.isin(["line_sweep", "load_sweep"])]
    passed = (checks.result == "PASS").sum()
    lines = [f"# Test report: {config.DUT_NAME}", "",
             f"- Board serial: **{config.DUT_SERIAL}**",
             f"- Run date: {df.timestamp.iloc[0]}",
             f"- Mode: **{info['mode']}**",
             f"- Overall: **{'PASS' if passed == len(checks) else 'FAIL'}** ({passed}/{len(checks)} checks passed)", "",
             "## Instruments", ""]
    lines += [f"- {k}: `{v}`" for k, v in info["instruments"].items()]
    lines += ["", "## Results", "", "| Test | Measurement | Value | Unit | Low | High | Result |",
              "|---|---|---|---|---|---|---|"]
    for _, r in checks.iterrows():
        lo = "" if pd.isna(r.low) else r.low
        hi = "" if pd.isna(r.high) else r.high
        lines.append(f"| {r.test} | {r.measurement} | {r.value:.3f} | {r.unit} | {lo} | {hi} | {r.result} |")
    lines += [""] + [f"## {t}\n\n![{t}]({p})\n" for t, p in plots]
    out = os.path.join(RESULTS_DIR, "report.md")
    open(out, "w").write("\n".join(lines))
    print(f"Report written to {out}")


if __name__ == "__main__":
    main()
