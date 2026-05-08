# TASK: Redesign FastXAFS into a Maintainable Operator Application

## Context

FastXAFS is currently a Python/PyQt/EPICS-based beamline control project.

Primary acquisition script:

- `Aktuell_contGui_xanes_exafs_v2.py`

Helper UIs:

- `GUIplot XANES 1.4.py`
- `GUISTOPSCAN.py`
- `spectraplotter.py`

Support modules:

- `motorlist.py`
- `XrayEdgeSelector.py`
- `checkpitchbayes.py`

The software controls EPICS motors, Zebra triggering, ion chambers, and XSPRESS3 acquisition. It is used as an operator-facing beamline experiment tool.

## Goal

Turn FastXAFS into a maintainable, robust operator application with a cleaner architecture and substantially better UI/UX.

The UI does not have to remain PyQt if there is a better architecture. The backend may remain Python/EPICS, while the frontend may be implemented separately.

## Key Principle

Separate experiment control from user interface.

The acquisition/backend layer should expose clear operations such as:

- configure scan
- add/update/remove sample
- start scan
- stop current scan
- stop all scans
- query scan status
- stream or fetch detector/spectrum data
- save/load sample table
- export processed data

The UI should call these operations rather than directly mixing layout code with motor/PV logic.

## Hard Safety Constraints

This software may move real beamline hardware.

Do not change EPICS PV names.
Do not change motor movement sequence.
Do not change scan timing constants.
Do not change energy-angle conversion formulas.
Do not change Zebra gate/pulse semantics.
Do not change detector acquisition semantics.
Do not run live EPICS-connected code during development unless explicitly allowed.
Do not call `.move()`, `.put()`, `caput`, detector acquire, or scan commands during tests.

## Required Deliverables

1. Architecture proposal in `ARCHITECTURE.md`.
2. Project documentation in `README.md` and `PROJECT_STRUCTURE.md`.
3. Dependency metadata in `requirements.txt`.
4. Safe environment check in `tools/check_environment.py`.
5. Dry-run/mock hardware design that enables UI work without EPICS hardware.
6. A staged migration path from the current scripts to a separated backend/frontend application.

## Verification

Run only safe checks by default:

```bash
python -m py_compile *.py
python tools/check_environment.py
git status --short
```

Do not launch real EPICS-connected UIs unless explicitly allowed.
