# FastXAFS Migration Plan

This plan preserves current production behavior while making the system maintainable.

## Stage 1: Freeze Current Behavior

Deliverables:

- `docs/CURRENT_WORKFLOW.md`
- `docs/TARGET_WORKFLOW.md`
- `docs/MIGRATION_PLAN.md`
- dependency/environment checks

Rules:

- Do not change EPICS calls.
- Do not change motor order.
- Do not change Zebra settings.
- Do not change XSPRESS3 settings.
- Do not change transmission formulas.

## Stage 2: Extract Pure Logic

Extract functions that do not touch EPICS:

- `angle_to_energy`
- `energy_to_angle`
- `add_constant_if_decreasing`
- ion chamber signal processing:
  - gradients for I0/I1/I2
  - sample ratio `-I0/I1`
  - reference ratio `-I2/I1`
- scan range calculation for XANES/EXAFS
- CSV row formatting

Add tests for these functions.

## Stage 3: Extract Data Writing

Move CSV writing into a dedicated module while preserving format:

```text
Ene I0 I1 I2 ENC
```

The writer should preserve metadata header behavior from the existing sample table.

## Stage 4: Extract Sample Queue Model

Introduce a plain data model for one sample row:

- sample name
- X
- Y
- edge energy
- time
- number of points
- element/edge
- mode
- repeat

Keep compatibility with existing `table.csv` save/load.

## Stage 5: Extract Scan Runner

Move the acquisition sequence out of the GUI into a runner class, preserving call order.

The runner should still use the same EPICS PV names and motor objects at first.

Only after behavior is verified should hardware abstraction be introduced.

## Stage 6: Add Hardware Boundary

Introduce:

- `EpicsHardware`
- `DryRunHardware`

The first implementation of `EpicsHardware` should be a thin wrapper around the existing calls.

`DryRunHardware` is for UI development and tests only.

## Stage 7: Build Improved UI

The first improved UI should be a legacy-first Qt shell, not a generic rewrite.

It should wrap:

- `MainWindow` from `Aktuell_contGui_xanes_exafs_v2.py`
- `App` from `GUIplot XANES 1.4.py`
- `EPICSControlApp` from `GUISTOPSCAN.py`
- `SpectraPlotter` from `spectraplotter.py`

Hardware-connected modules must be loaded lazily, as described in `docs/LEGACY_INTEGRATION_ARCHITECTURE.md`.

Build the improved UI around the preserved workflow.

The UI may be web-based or desktop-based, but it must keep:

- one queue row per physical sample
- reference curve as `-I2/I1`
- transmission/XRF mode distinction
- stop/stopall access
- explicit output path/status

## Stage 8: Integrate Helper Workflows

Fold helper workflows into the target app or keep them as separate tools with shared processing modules:

- XSPRESS3 HDF5 processing
- ROI selection
- XRF spectrum export
- live MCA spectra
- stop-scan control

## Verification Gates

Every stage should run:

```bash
python -m py_compile *.py
python tools/check_environment.py
```

For pure logic:

```bash
python -m pytest -q tests
```

Real EPICS verification must be manual and explicitly approved.
