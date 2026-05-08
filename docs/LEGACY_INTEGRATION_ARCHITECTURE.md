# Legacy-First Integration Architecture

This is the correct target architecture for FastXAFS based on the current production scripts.

## Goal

Build one improved operator application around the existing tools without changing their beamline logic.

The application should integrate:

- main acquisition: `Aktuell_contGui_xanes_exafs_v2.py`
- HDF5/XANES/XRF processing: `GUIplot XANES 1.4.py`
- stop controls: `GUISTOPSCAN.py`
- live spectra: `spectraplotter.py`

The support modules remain part of the runtime model:

- `motorlist.py`
- `checkpitchbayes.py`
- `XrayEdgeSelector.py`
- beamline-local `detectorlist.py`
- beamline-local `checkbeamlinestate.py`

## Important Correction

The architecture must not start from a generic new backend. It must start from the current scripts.

The current scripts are not throwaway examples. They encode the production behavior:

- motor names
- EPICS PV names
- Zebra setup order
- XSPRESS3 setup order
- pitch check behavior
- transmission formulas
- HDF5 processing assumptions

## Recommended UI Architecture

Use a Qt application shell first.

Reason:

- all current tools are already PyQt/PyQtGraph/Matplotlib Qt applications
- `Aktuell_contGui_xanes_exafs_v2.py` exposes a `MainWindow`
- `GUIplot XANES 1.4.py` exposes an `App`
- `GUISTOPSCAN.py` exposes `EPICSControlApp`
- `spectraplotter.py` exposes `SpectraPlotter`
- reusing these classes avoids rewriting behavior too early

A web UI can still be useful later, but it should come after the scan runner and processing logic have been extracted safely.

## Application Shell

Target shell:

```text
FastXAFS Operator
  Acquisition tab
    wraps MainWindow from Aktuell_contGui_xanes_exafs_v2.py
  XRF/XANES Processing tab
    wraps App from GUIplot XANES 1.4.py
  Stop Control tab
    wraps EPICSControlApp from GUISTOPSCAN.py
  Live Spectra tab
    wraps SpectraPlotter from spectraplotter.py
```

Each tab must be loaded lazily. Do not import every hardware-connected module at startup.

## Lazy Import Rule

Some modules initialize hardware at import time:

- `motorlist.py` creates EPICS motor/device objects.
- `checkpitchbayes.py` imports `motorlist.py` and `detectorlist.py`.
- `GUISTOPSCAN.py` opens `Rfa:Info.NIST`.
- `spectraplotter.py` opens XSPRESS3 MCA PVs.
- `Aktuell_contGui_xanes_exafs_v2.py` imports `motorlist.py`, `checkpitchbayes.py`, and creates `Rfa:Info.NIST`.

Therefore:

- environment checks must not import hardware modules
- the operator shell must load a tool only when the user opens/starts that tool
- dry-run/development mode must not import hardware modules

## Dependency Map

### Main Acquisition

File:

- `Aktuell_contGui_xanes_exafs_v2.py`

Class:

- `MainWindow`

Dependencies:

- `epics`
- `motorlist`
- `XrayEdgeSelector`
- `checkpitchbayes`
- `PyQt5`
- `matplotlib`
- `numpy`

Hardware behavior:

- controls DCM motors
- moves sample X/Y
- moves reference/filter position
- configures Zebra
- optionally calls `checkpitchbayes.checkpitch()`
- optionally configures XSPRESS3 HDF5 capture
- reads Zebra ion chamber/encoder arrays

### HDF5/XANES/XRF Processing

File:

- `GUIplot XANES 1.4.py`

Class:

- `App`

Dependencies:

- `h5py`
- `numpy`
- `PyQt5`
- `matplotlib`

Hardware behavior:

- none for file processing

Data behavior:

- reads XSPRESS3 HDF5
- normalizes detector channels by real time
- applies ROI
- exports processed XANES CSV
- exports integrated XRF spectrum CSV

### Stop Control

File:

- `GUISTOPSCAN.py`

Class:

- `EPICSControlApp`

Dependencies:

- `epics`
- `PyQt5`

Hardware behavior:

- writes `run`, `stop`, `stopall` to `Rfa:Info.NIST`

### Live Spectra

File:

- `spectraplotter.py`

Class:

- `SpectraPlotter`

Dependencies:

- `epics`
- `pyqtgraph`
- `xraylib`
- `PyQt5`
- `numpy`

Hardware behavior:

- subscribes to XSPRESS3 MCA array PVs

### Pitch Check

File:

- `checkpitchbayes.py`

Entry function:

- `checkpitch()`

Dependencies:

- `motorlist`
- `detectorlist`
- `epics`
- `scipy`
- `numpy`

Hardware behavior:

- moves `DCM_PIEZO`
- reads and writes `ioni13`
- waits for raw data processing
- runs pitch optimization
- may recursively repeat if intensity drops

## Migration Strategy

### Phase 1: Legacy shell

Create a Qt shell that can launch the four existing tools without changing their code.

This phase proves integration and operator workflow.

### Phase 2: Shared workflow state

Only after the shell works, introduce shared concepts:

- current output path
- selected acquisition mode
- selected sample table file
- active beamline state

Do not rewrite scan logic yet.

### Phase 3: Extract pure processing

Move safe calculations into shared modules:

- energy-angle conversion
- transmission ratios
- HDF5 processing
- CSV writing

### Phase 4: Extract scan runner

Extract the scan sequence from `MainWindow.start_all()` and `MainWindow.run_acquisition()` while preserving call order.

### Phase 5: Hardware abstraction

Only after extraction, introduce real/dry-run hardware adapters.

## What The New Version Should Do At Beamline

For real scans, the new version should initially launch the existing main acquisition UI through the shell or launcher.

It should not use the dry-run web backend for real scans.

Beamline-ready means:

- all production scripts are present
- beamline dependencies are installed
- local modules `detectorlist.py` and `checkbeamlinestate.py` are available
- launch path is clear
- preflight can verify dependencies without moving hardware
