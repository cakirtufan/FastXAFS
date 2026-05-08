# Beamline Deployment

This document describes how to run FastXAFS at the beamline without changing the current production acquisition behavior.

## Supported Beamline Runtime

Real beamline acquisition should use the production acquisition script through the launcher:

```bash
python run_fastxafs.py main
```

This launches:

```text
original/Aktuell_contGui_xanes_exafs_v2.py
```

The clean web UI can run in dry-run mode and has a real EPICS adapter, but the unchanged original PyQt acquisition script remains the safest production entry point until the clean workflow has been commissioned at the beamline.

The correct next-generation architecture is legacy-first: wrap the existing PyQt tools and load hardware-connected tools lazily. See `docs/LEGACY_INTEGRATION_ARCHITECTURE.md` from the repository root.

## Install Dependencies

Create or activate the beamline Python environment, then install:

```bash
python -m pip install -r requirements-beamline.txt
```

Beamline-local modules must also be available on `PYTHONPATH` or in the working directory:

- `detectorlist.py`
- `checkbeamlinestate.py`

## Preflight Check

Run:

```bash
python tools/beamline_preflight.py
```

The preflight check does not import `motorlist.py`, does not connect to EPICS, and does not move hardware.

To inspect the central tool/dependency manifest:

```bash
python tools/legacy_manifest_report.py
```

## Launch Commands

Main acquisition GUI:

```bash
python run_fastxafs.py main
```

XSPRESS3 HDF5/XANES processing helper:

```bash
python run_fastxafs.py plot-xanes
```

Stop-scan helper:

```bash
python run_fastxafs.py stop-scan
```

Live XSPRESS3 spectra plotter:

```bash
python run_fastxafs.py spectra
```

Clean dry-run web UI:

```bash
python run_clean_app.py --hardware-mode dry-run --host 127.0.0.1 --port 8770
```

Open:

```text
http://127.0.0.1:8770/
```

## Preserved Production Behavior

- one table row is one physical sample position
- transmission data source is ion chambers/Zebra
- transmission CSV columns are `Ene I0 I1 I2 ENC`
- sample plot is `-I0/I1`
- reference plot is `-I2/I1`
- XRF capture configures XSPRESS3 HDF5 capture
- helper UI processes HDF5 data after capture
- `Check Pitch` calls `checkpitchbayes.checkpitch()` before acquisition when selected

## Not Yet Real-Hardware Ready

The `fastxafs_app` real adapter still needs beamline commissioning. The next real-hardware step is comparing its EPICS call order against `original/Aktuell_contGui_xanes_exafs_v2.py` during a controlled test.
