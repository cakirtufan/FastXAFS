"""Metadata for original beamline scripts kept as migration references."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ORIGINAL_DIR = ROOT / "original"


@dataclass(frozen=True, slots=True)
class LegacyTool:
    key: str
    title: str
    path: Path
    role: str
    third_party_dependencies: tuple[str, ...]
    local_dependencies: tuple[str, ...]


LEGACY_TOOLS: dict[str, LegacyTool] = {
    "main": LegacyTool(
        key="main",
        title="Aktuell_contGui_xanes_exafs_v2",
        path=ORIGINAL_DIR / "Aktuell_contGui_xanes_exafs_v2.py",
        role="Production acquisition workflow for transmission and XRF scans.",
        third_party_dependencies=("PyQt5", "epics", "numpy", "matplotlib", "scipy", "xraylib"),
        local_dependencies=("motorlist", "checkpitchbayes", "XrayEdgeSelector", "detectorlist"),
    ),
    "plot-xanes": LegacyTool(
        key="plot-xanes",
        title="GUIplot XANES 1.4",
        path=ORIGINAL_DIR / "GUIplot XANES 1.4.py",
        role="HDF5/XANES/XRF plotting and post-processing helper.",
        third_party_dependencies=("PyQt5", "h5py", "numpy", "matplotlib", "scipy", "xraylib"),
        local_dependencies=(),
    ),
    "stop-scan": LegacyTool(
        key="stop-scan",
        title="GUISTOPSCAN",
        path=ORIGINAL_DIR / "GUISTOPSCAN.py",
        role="Emergency/operational stop helper.",
        third_party_dependencies=("PyQt5", "epics"),
        local_dependencies=(),
    ),
    "spectra": LegacyTool(
        key="spectra",
        title="spectraplotter",
        path=ORIGINAL_DIR / "spectraplotter.py",
        role="Live spectrum display helper.",
        third_party_dependencies=("PyQt5", "epics", "pyqtgraph", "numpy"),
        local_dependencies=(),
    ),
}
