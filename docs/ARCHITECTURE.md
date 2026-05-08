# FastXAFS Architecture

## Current State

FastXAFS is a collection of Python scripts for XANES/EXAFS acquisition and supporting operator tools. The unchanged original scripts are kept under `original/`. The main script, `original/Aktuell_contGui_xanes_exafs_v2.py`, combines UI layout, sample queue management, EPICS motor control, Zebra trigger configuration, detector acquisition, plotting, and data writing in one process.

The helper scripts provide focused operator utilities:

- `original/GUIplot XANES 1.4.py`: load XSPRESS3 HDF5 files, choose ROI, plot/export XANES and XRF data.
- `original/GUISTOPSCAN.py`: send `run`, `stop`, and `stopall` commands through EPICS.
- `original/spectraplotter.py`: show live MCA/XRF spectra from XSPRESS3 PVs.

The main acquisition path has two distinct data flows:

- Transmission mode, selected when XRF capture is off: Zebra provides captured encoder and ion chamber counter data, written as CSV and plotted after the scan.
- XRF capture mode, selected when XRF capture is on: XSPRESS3 writes HDF5 data, and the displayed XAS/XRF data comes from detector output rather than the Zebra CSV path.

In the legacy transmission plot, `Sample` is calculated as `-I0/I1` and `Reference` as `-I2/I1`. Reference is a derived channel ratio from the same scan, not a separate sample position.

Support modules define beamline hardware and utility widgets:

- `original/motorlist.py`: EPICS motors, ion chamber devices, and encoder devices.
- `original/XrayEdgeSelector.py`: element/edge selector using `xraylib`.
- `original/checkpitchbayes.py`: DCM pitch optimization logic.

## Current Problems

- Hardware access is created at import time, especially in `motorlist.py`.
- UI code and hardware-control code are tightly coupled.
- The main GUI performs long-running acquisition operations on the UI thread.
- There is no dry-run mode for UI development away from the beamline.
- Several paths and constants are embedded directly in UI logic.
- The project lacks dependency metadata and operator/developer documentation.
- Missing local modules such as `detectorlist.py` and `checkbeamlinestate.py` are not documented.

## Recommended Target Architecture

Use a Python backend with a local web UI.

The backend should remain Python because EPICS, existing acquisition logic, detector processing, and beamline-specific modules are already Python-based. A local web UI gives a cleaner operator interface, better plotting/table ergonomics, easier status streaming, and a natural path to a future packaged desktop shell if needed.

Recommended shape:

```text
fastxafs_app/
  domain.py
  scan_runner.py
  hardware.py
  data_writer.py
  service.py
  api.py
  ui/
    web application
  legacy_manifest.py
original/
  unchanged production scripts retained during migration
```

## Backend and Frontend Boundary

The frontend should not call EPICS directly. It should call backend operations:

- configure scan
- add/update/remove sample positions
- save/load sample table
- start queued scan
- stop current scan
- stop all scans
- query current hardware/scan status
- stream scan progress and spectra
- export processed XANES/XRF data

The backend boundary must preserve the distinction between transmission CSV output and XRF HDF5 detector output.

The backend owns all calls to `epics`, `motorlist`, detector devices, Zebra PVs, and XSPRESS3 PVs.

## Safety Model

The backend should have explicit hardware modes:

- `real`: uses EPICS and can move hardware.
- `dry-run`: simulates motors, detector counts, spectra, status, and stop commands.

Dry-run mode must be visible in the UI at all times. Real mode should require explicit configuration and should never be used by tests.

Test and environment-check scripts must not import `original/motorlist.py`, because importing it constructs EPICS motor objects.

## Dry-Run Design

`DryRunHardware` should simulate:

- motor positions for X, Y, reference filter, DCM theta, and DCM energy
- scan progress over time
- Zebra captured encoder positions
- ion chamber counts
- XRF spectra
- stop and stopall behavior

The simulation does not need to be physically exact at first. It should be stable enough for UI development, screenshots, and regression tests.

## Migration Plan

Phase 1: Stabilize the repository.

- Add documentation, dependency metadata, `.gitignore`, and a safe environment check.
- Document missing beamline-local modules.
- Fix low-risk file handling bugs.

Current implementation status:

- A clean backend exists under `fastxafs_app/`.
- A FastAPI app exists in `fastxafs_app/api.py`.
- A local browser operator UI exists under `fastxafs_app/ui/`.
- `run_clean_app.py` launches dry-run mode without importing EPICS hardware modules.

Phase 2: Extract pure models.

- Introduce `ScanConfig`, `SamplePosition`, `ScanStatus`, and data-export helpers.
- Keep acquisition behavior unchanged.

Phase 3: Introduce hardware interface.

- Define a hardware protocol or base class.
- Implement `EpicsHardware` as a wrapper around current `motorlist`/EPICS calls.
- Implement `DryRunHardware`.

Phase 4: Move acquisition orchestration.

- Extract scan execution from the GUI into `ScanRunner`.
- Preserve EPICS PV names, movement order, Zebra settings, detector semantics, and timing constants.

Phase 5: Build the new UI.

- Start with a local web UI against dry-run backend.
- Include scan setup, sample queue, live status, output path, start/stop controls, XANES plot, XRF view, and helper-tool tabs.

Phase 6: Real hardware review.

- Review the extracted `EpicsHardware` behavior against the original script.
- Only then connect the new UI to real EPICS mode.

## Architecture Options Considered

Improved PyQt monolith: lowest migration cost, but it keeps UI and hardware logic too close unless significant discipline is added.

Python backend plus local web UI: best balance of preserving EPICS/Python control while enabling modern operator UI and dry-run development.

Python backend plus desktop shell: useful later if a single desktop executable is required, but premature now.

Separated Qt frontend and Python services: viable, but it keeps the project in Qt without gaining as much UI velocity as a web frontend.

## Risks

- Beamline behavior can change accidentally during refactor. Mitigation: isolate behavior-preserving changes and review PV/motor sequences line by line.
- Dry-run simulation can diverge from real behavior. Mitigation: keep it explicit and use it only for UI and development checks.
- Missing local modules may hide runtime behavior. Mitigation: document them and avoid replacing them without beamline validation.
