"""Check FastXAFS Python dependencies without touching EPICS hardware.

This script intentionally does not import local beamline modules such as
motorlist.py because those modules construct EPICS objects at import time.
"""

from __future__ import annotations

import importlib.util
import sys


REQUIRED_MODULES = {
    "PyQt5": "PyQt5",
    "pyepics": "epics",
    "numpy": "numpy",
    "matplotlib": "matplotlib",
    "scipy": "scipy",
    "h5py": "h5py",
    "xraylib": "xraylib",
    "pyqtgraph": "pyqtgraph",
    "fastapi": "fastapi",
    "uvicorn": "uvicorn",
}

LOCAL_BEAMLINE_MODULES = (
    "detectorlist",
    "checkbeamlinestate",
)


def is_importable(module_name: str) -> bool:
    return importlib.util.find_spec(module_name) is not None


def main() -> int:
    missing = []

    print("FastXAFS environment check")
    print("==========================")
    print("Third-party dependencies:")

    for package_name, module_name in REQUIRED_MODULES.items():
        available = is_importable(module_name)
        status = "OK" if available else "MISSING"
        print(f"  {package_name:<12} {status}")
        if not available:
            missing.append(package_name)

    print()
    print("Beamline-local modules:")
    for module_name in LOCAL_BEAMLINE_MODULES:
        status = "OK" if is_importable(module_name) else "MISSING"
        print(f"  {module_name:<18} {status}")

    print()
    print("Safety: motorlist.py was not imported.")

    if missing:
        print()
        print("Install missing third-party dependencies with:")
        print("  python -m pip install -r requirements.txt")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
