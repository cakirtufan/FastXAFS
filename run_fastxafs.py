"""FastXAFS launcher for beamline and development workflows."""

from __future__ import annotations

import argparse
import runpy
from pathlib import Path


ROOT = Path(__file__).resolve().parent
ORIGINAL = ROOT / "original"

ENTRYPOINTS = {
    "main": ORIGINAL / "Aktuell_contGui_xanes_exafs_v2.py",
    "plot-xanes": ORIGINAL / "GUIplot XANES 1.4.py",
    "stop-scan": ORIGINAL / "GUISTOPSCAN.py",
    "spectra": ORIGINAL / "spectraplotter.py",
    "clean-app": ROOT / "run_clean_app.py",
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Launch FastXAFS tools.")
    parser.add_argument(
        "tool",
        choices=sorted(ENTRYPOINTS),
        help="Tool to launch. Use 'main' for real beamline acquisition.",
    )
    args = parser.parse_args()

    target = ENTRYPOINTS[args.tool]
    if not target.exists():
        raise FileNotFoundError(target)

    runpy.run_path(str(target), run_name="__main__")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
