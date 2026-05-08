# Current FastXAFS Workflow

This document describes the workflow implemented by the current production scripts. These scripts are the source of truth for behavior.

## Script Roles

`Aktuell_contGui_xanes_exafs_v2.py` is the main acquisition UI. It owns the sample queue, motor moves, Zebra configuration, optional XSPRESS3 capture, transmission plotting, and CSV writing.

`GUIplot XANES 1.4.py` is the offline XRF/XANES processing UI for XSPRESS3 HDF5 files.

`GUISTOPSCAN.py` is a small EPICS control UI for `Rfa:Info.NIST`.

`spectraplotter.py` is a live XSPRESS3 MCA display with element-line and ROI overlays.

`motorlist.py`, `XrayEdgeSelector.py`, and `checkpitchbayes.py` are support modules.

## Main Sample Queue

The main GUI uses one table row per physical sample position. A row contains:

- sample name
- X position
- Y position
- edge energy
- acquisition time
- number of points
- element/edge label
- scan mode
- repeat count

The reference curve is not a separate queue item. It is derived from ion chamber channels during the same scan.

## Queue Execution

For each queue repeat and each sample row, the main script:

1. Marks the row as active.
2. Reads sample name, X, Y, edge, mode, time, points, and repeat.
3. Computes the scan energy range:
   - mode `1`: edge - 0.3 keV to edge + 0.4 keV
   - other mode: edge - 0.25 keV to edge + 0.75 keV
4. Selects DCM motor mode with `Energ:25002000selectMotors`.
5. Sets DCM theta velocity to `0.2`.
6. Moves DCM energy near scan start.
7. Moves sample X and Y.
8. Looks up the reference/filter motor position from `filterpos`.
9. Moves `XANES_Reference` to that position.
10. Waits for X, Y, reference, and energy moves to complete.
11. Writes Zebra encoder setup values:
    - `BAMZEBRA:M2:ERES`
    - `BAMZEBRA:POS2_SET`
12. Optionally runs pitch check.
13. Converts start/stop energies to theta angles.
14. Computes scan velocity from theta delta and acquisition time.
15. Calls `run_acquisition(...)`.
16. Writes the resulting data file.
17. Optionally repeats the scan in the opposite direction.
18. Marks the row as completed.

## Energy and Angle Conversion

The script uses:

- `D_SPACING = 0.31355`
- `angle_to_energy(angle)`
- `energy_to_angle(energy)`

The conversion uses Bragg-law style wavelength calculation:

- wavelength = `2 * D_SPACING * sin(theta)`
- energy = `1.239843 / wavelength`

## Pitch Check

If `Check Pitch` is selected in the main GUI, the production script calls:

```python
checkpitchbayes.checkpitch()
```

This happens after the sample/reference moves and Zebra encoder position setup, before the scan angle range is calculated and before `run_acquisition(...)`.

`checkpitchbayes.checkpitch()` uses `DCM_PIEZO`, `ioni13`, and EPICS read/write calls. It can move hardware and is only valid in the real beamline environment.

## Transmission Mode

Transmission mode is used when `With XRF` is not checked.

The data source is ion chamber data captured through Zebra. After the scan, the script reads:

- `BAMZEBRA:PC_DIV1`
- `BAMZEBRA:PC_DIV2`
- `BAMZEBRA:PC_DIV3`
- `BAMZEBRA:PC_ENC2`

It also reads:

- `BAMZEBRA:PC_NUM_CAP`
- `BAMZEBRA:DIV2_DIV`

The DIV arrays are trimmed to the captured point count. `add_constant_if_decreasing(...)` corrects wraparound-like decreases by adding `DIV2_DIV` to subsequent values.

The displayed and saved signals are then calculated as:

- `i0 = gradient(ioni1)`
- `i1 = gradient(ioni2)`
- `i2 = gradient(ioni3)`
- `ene = angle_to_energy(encpos)`

The plot uses:

- sample curve: `-i0 / i1`
- reference curve: `-i2 / i1`

The CSV file contains:

```text
Ene I0 I1 I2 ENC
```

## XRF Capture Mode

XRF capture mode is used when `With XRF` is checked.

Before the DCM theta scan, the script configures XSPRESS3:

- `XSP3_4Chan:HDF1:FilePath`
- `XSP3_4Chan:HDF1:Capture`
- `XSP3_4Chan:det1:Acquire`
- `XSP3_4Chan:det1:NumImages`
- `XSP3_4Chan:det1:ERASE`
- `XSP3_4Chan:det1:UPDATE`
- `XSP3_4Chan:HDF1:FileName`
- `XSP3_4Chan:det1:TriggerMode`

The detector acquisition and HDF5 capture are started before the Zebra-armed scan and stopped after the scan.

The main script still reads the Zebra arrays after acquisition. XRF/XAS processing from detector data is handled by `GUIplot XANES 1.4.py`.

## Zebra Scan

`run_acquisition(...)` configures Zebra with:

- `BAMZEBRA:PC_DIR`
- `BAMZEBRA:PC_GATE_START`
- `BAMZEBRA:PC_GATE_WID`
- `BAMZEBRA:PC_GATE_STEP`
- `BAMZEBRA:PC_GATE_NGATE`
- `BAMZEBRA:PC_PULSE_START`
- `BAMZEBRA:PC_PULSE_STEP`
- `BAMZEBRA:PC_PULSE_WID`
- `BAMZEBRA:PC_PULSE_MAX`

It moves DCM theta to a pre-start offset, resets and arms Zebra, moves to the stop position at the scan velocity, then disarms Zebra.

## HDF5 Processing Helper

`GUIplot XANES 1.4.py` loads XSPRESS3 HDF5 files and reads:

- `entry/data/data`
- `entry/instrument/NDAttributes/ENERGYDCM`
- `entry/instrument/NDAttributes/Ioni13`
- `entry/instrument/NDAttributes/CHAN1REALTIME`
- `entry/instrument/NDAttributes/CHAN2REALTIME`
- `entry/instrument/NDAttributes/CHAN3REALTIME`
- `entry/instrument/NDAttributes/CHAN4REALTIME`

It normalizes detector channels by real time, sums the four channels, applies the ROI range, trims to scan start using minimum energy, and exports processed XANES CSV.

It can also sum all energy points and all channels to export an integrated XRF spectrum CSV.

## Stop Scan Helper

`GUISTOPSCAN.py` controls `Rfa:Info.NIST`.

It writes:

- `run`
- `stop`
- `stopall`

## Live Spectra Helper

`spectraplotter.py` reads live MCA data from:

- `XSP3_4Chan:MCA1:ArrayData`
- `XSP3_4Chan:MCA2:ArrayData`
- `XSP3_4Chan:MCA3:ArrayData`
- `XSP3_4Chan:MCA4:ArrayData`

It plots total and per-channel spectra, overlays emission lines from `xraylib`, and supports ROI marker overlays.
