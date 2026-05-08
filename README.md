# FastXAFS

FastXAFS is an operator-facing XANES/EXAFS acquisition toolkit for an EPICS-controlled beamline environment.

## Main Application

The unchanged production scripts are kept under `original/`. `original/Aktuell_contGui_xanes_exafs_v2.py` is the main acquisition GUI. It manages scan setup, sample positions, energy-to-angle conversion, motor moves, Zebra trigger configuration, optional XSPRESS3 acquisition, plotting, and data export.

The acquisition has two data-flow modes:

- Transmission mode: when `XRF capture` is not selected, the scan uses Zebra captured encoder and ion chamber counter data. The result is written as CSV and displayed after the scan.
- XRF capture mode: when `XRF capture` is selected, the XSPRESS3 detector writes HDF5 data. XAS/XRF displays are derived from the detector data stream/file.

For transmission display, the legacy GUI derives both plotted curves from the same scan:

- sample curve: `-I0 / I1`
- reference curve: `-I2 / I1`

The reference curve is not a separate queue entry; it comes from a different ion chamber channel.

## Helper UIs

- `original/GUIplot XANES 1.4.py`: loads XSPRESS3 HDF5 files, plots XANES/XRF data, supports ROI selection, and exports processed CSV files.
- `original/GUISTOPSCAN.py`: sends run/stop/stopall commands through the `Rfa:Info.NIST` EPICS PV.
- `original/spectraplotter.py`: displays live XSPRESS3 MCA spectra and overlays X-ray emission line markers.

## Support Modules

- `original/motorlist.py`: defines EPICS motors, devices, ion chambers, and encoder devices.
- `original/XrayEdgeSelector.py`: provides element and edge selection using `xraylib`.
- `original/checkpitchbayes.py`: contains DCM pitch optimization routines.

## Safety Warning

This project can move real hardware and trigger detector acquisition. Do not run EPICS-connected scripts unless you are in the correct beamline environment and are authorized to operate the system.

Safe development checks should not import `original/motorlist.py`, because it creates EPICS motor objects at import time.

## Dependencies

Install Python dependencies with:

```bash
python -m pip install -r requirements.txt
```

For beamline runtime only:

```bash
python -m pip install -r requirements-beamline.txt
```

For development:

```bash
python -m pip install -r requirements-dev.txt
```

The project uses:

- PyQt5
- pyepics
- numpy
- matplotlib
- scipy
- h5py
- xraylib
- pyqtgraph

The beamline environment may also require local modules that are not currently in this repository:

- `detectorlist.py`
- `checkbeamlinestate.py`

## Running

Beamline launcher:

```bash
python run_fastxafs.py main
```

See `docs/BEAMLINE_DEPLOYMENT.md` before running at the beamline.

The intended next-generation architecture is described in `docs/LEGACY_INTEGRATION_ARCHITECTURE.md`: wrap the current PyQt tools and preserve their beamline behavior.

Clean dry-run web UI for development:

```bash
python run_clean_app.py --hardware-mode dry-run --host 127.0.0.1 --port 8770
```

Then open:

```text
http://127.0.0.1:8770
```

This starts only the simulated backend and does not import `motorlist.py` or connect to EPICS.

Main acquisition GUI:

```bash
python run_fastxafs.py main
```

XANES/XRF file plotting helper:

```bash
python run_fastxafs.py plot-xanes
```

Stop-scan helper:

```bash
python run_fastxafs.py stop-scan
```

Live spectra plotter:

```bash
python run_fastxafs.py spectra
```

The same tools can also be launched through:

```bash
python run_fastxafs.py plot-xanes
python run_fastxafs.py stop-scan
python run_fastxafs.py spectra
```

Only run these commands in a safe EPICS/beamline environment.

## Safe Checks

Syntax check:

```bash
python -m py_compile run_clean_app.py run_fastxafs.py fastxafs_app/*.py original/*.py tools/*.py
```

Dependency check without EPICS hardware imports:

```bash
python tools/check_environment.py
```

Legacy tool/dependency manifest:

```bash
python tools/legacy_manifest_report.py
```

Dry-run backend smoke test:

```bash
python tools/smoke_dry_run.py
```

Pure calculation tests:

```bash
python -m pytest -q tests
```
