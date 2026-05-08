"""Beamline dependency preflight without EPICS hardware initialization."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
ORIGINAL = ROOT / "original"
if str(ORIGINAL) not in sys.path:
    sys.path.insert(0, str(ORIGINAL))

from fastxafs_app.legacy_manifest import LEGACY_TOOLS


REQUIRED = {
    "numpy": "numpy",
    "matplotlib": "matplotlib",
    "scipy": "scipy",
    "h5py": "h5py",
    "PyQt5": "PyQt5",
    "pyepics": "epics",
    "xraylib": "xraylib",
    "pyqtgraph": "pyqtgraph",
    "detectorlist": "detectorlist",
    "checkbeamlinestate": "checkbeamlinestate",
}


def is_available(module_name: str) -> bool:
    return importlib.util.find_spec(module_name) is not None


def main() -> int:
    missing = []
    print("FastXAFS beamline preflight")
    print("===========================")
    for label, module_name in REQUIRED.items():
        available = is_available(module_name)
        print(f"{label:<20} {'OK' if available else 'MISSING'}")
        if not available:
            missing.append(label)

    print()
    print("Safety: motorlist.py was not imported.")
    print("Safety: no EPICS PVs were opened and no motors were moved.")

    print()
    print("Legacy tools:")
    for tool in LEGACY_TOOLS.values():
        missing_for_tool = [
            dependency
            for dependency in (*tool.third_party_dependencies, *tool.local_dependencies)
            if not is_available(dependency)
        ]
        status = "OK" if not missing_for_tool else "MISSING: " + ", ".join(missing_for_tool)
        print(f"- {tool.key:<10} {status}")
        if not tool.path.exists():
            print(f"  missing file: {tool.path}")

    if missing:
        print()
        print("Missing requirements:")
        for item in missing:
            print(f"- {item}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
