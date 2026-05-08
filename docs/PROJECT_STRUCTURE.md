# Project Structure

## Original Beamline Scripts

All currently used production scripts are kept unchanged under `original/`.

### Main GUI

- `original/Aktuell_contGui_xanes_exafs_v2.py`

The primary XANES/EXAFS acquisition GUI. It currently owns both operator UI and hardware-control orchestration.

In the current workflow, transmission scans use Zebra data and write CSV output. XRF capture scans use XSPRESS3 HDF5 output as the data source for downstream display. Transmission plots derive sample as `-I0/I1` and reference as `-I2/I1` from the same scan.

### Helper UIs

- `original/GUIplot XANES 1.4.py`

Offline/analysis UI for loading XSPRESS3 HDF5 files, selecting ROI ranges, plotting processed XANES data, and exporting CSV data.

- `original/GUISTOPSCAN.py`

Small control UI for setting the `Rfa:Info.NIST` scan-control PV to `run`, `stop`, or `stopall`.

- `original/spectraplotter.py`

Live spectra display UI for XSPRESS3 MCA PV data, with X-ray line overlays and ROI markers.

### Support Modules

- `original/motorlist.py`

Beamline hardware definitions. Importing this module creates EPICS motor/device objects.

- `original/XrayEdgeSelector.py`

Reusable PyQt widget for selecting element/edge combinations and computing edge energies.

- `original/checkpitchbayes.py`

Pitch optimization routines using motor moves, ion chamber readings, and numerical optimization.

## Development and Documentation

- `TASK.md`: current modernization workflow.
- `docs/ARCHITECTURE.md`: target architecture and migration plan.
- `docs/LEGACY_INTEGRATION_ARCHITECTURE.md`: legacy-first integration architecture for the current PyQt tools.
- `requirements.txt`: Python dependency list.
- `tools/check_environment.py`: safe dependency check that avoids importing EPICS hardware modules.
- `tools/smoke_dry_run.py`: safe smoke test for the dry-run backend.
- `tools/beamline_preflight.py`: safe beamline dependency check that avoids hardware initialization.
- `tools/legacy_manifest_report.py`: prints the central legacy tool/dependency manifest without hardware imports.
- `run_clean_app.py`: launches the clean FastAPI/browser UI in dry-run or real hardware mode.
- `run_fastxafs.py`: launcher for the production main GUI and helper tools.
- `requirements-beamline.txt`: runtime dependencies for beamline use.
- `requirements-dev.txt`: beamline dependencies plus development/test tools.
- `docs/BEAMLINE_DEPLOYMENT.md`: beamline installation and launch guide.

## Clean Backend and UI

- `fastxafs_app/domain.py`: scan/sample/status domain models.
- `fastxafs_app/calculations.py`: EPICS-free calculations extracted from the production scripts.
- `fastxafs_app/hardware.py`: dry-run and EPICS hardware adapters.
- `fastxafs_app/scan_runner.py`: clean acquisition workflow orchestration.
- `fastxafs_app/service.py`: application service used by the API.
- `fastxafs_app/api.py`: FastAPI app.
- `fastxafs_app/ui/`: browser-based operator UI.
- `fastxafs_app/legacy_manifest.py`: metadata for original scripts and dependencies.
- `tests/test_calculations.py`: tests for pure calculations only.

## Missing Local Modules

The current code references these modules, but they are not present in the repository:

- `detectorlist.py`
- `checkbeamlinestate.py`

They are likely beamline-local modules and should be added or documented before a full runtime deployment.
