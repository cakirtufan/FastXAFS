# Target FastXAFS Workflow

The target workflow keeps the current beamline behavior but makes the operator flow clearer and the code easier to maintain.

## Operator Flow

1. Open FastXAFS.
2. Confirm hardware mode:
   - real EPICS mode at the beamline
   - dry-run mode for development/testing
3. Select acquisition mode:
   - Transmission
   - XRF capture
4. Build the sample queue.
5. Confirm output paths.
6. Start the queue.
7. Watch active row, scan status, energy, progress, and plots.
8. Stop current scan or stop all when needed.
9. Review saved output.

## Sample Queue

The sample queue remains central. One row means one physical sample position.

Each row should include:

- sample name
- X
- Y
- element
- edge
- edge energy
- time
- number of points
- XANES/EXAFS mode
- repeat count

Reference display must not become a separate row. It remains a channel ratio from the same scan.

## Transmission Workflow

Transmission mode should clearly show:

- acquisition mode: Transmission
- data source: Ion chambers
- output: CSV

During and after the scan, the system should preserve the current calculations:

- `i0 = gradient(ioni1)`
- `i1 = gradient(ioni2)`
- `i2 = gradient(ioni3)`
- sample: `-i0/i1`
- reference: `-i2/i1`

The CSV output should preserve the current columns:

```text
Ene I0 I1 I2 ENC
```

The plot should label curves explicitly:

- `Sample -I0/I1`
- `Reference -I2/I1`

## Pitch Check Workflow

`Check Pitch` should remain an optional per-queue-run setting.

When enabled in real beamline mode, the preserved behavior is:

1. Move sample X/Y and reference/filter position.
2. Set Zebra encoder position reference.
3. Call `checkpitchbayes.checkpitch()`.
4. Continue to angle calculation and scan acquisition.

Dry-run mode should never import or call `checkpitchbayes.py`; it may only simulate the status step.

## XRF Capture Workflow

XRF capture mode should clearly show:

- acquisition mode: XRF capture
- data source: XSPRESS3 HDF5
- output: HDF5 plus processed exports

The XSPRESS3 configuration and trigger behavior should preserve the current sequence. XRF spectrum and HDF5-derived XANES views should be shown only when XRF capture is enabled or when an HDF5 file is loaded.

## Status Model

The operator UI should always show:

- hardware mode
- acquisition mode
- active sample
- queue position
- current energy
- elapsed time
- scan state
- output target
- whether stop/stopall is available

## Stop Behavior

Stop and stop-all controls should remain visible and easy to reach.

The target backend should preserve the existing `Rfa:Info.NIST` command semantics:

- `run`
- `stop`
- `stopall`

## Helper Tools

The helper tools can remain separate initially, but their workflows should be represented in the target application:

- XSPRESS3 HDF5 file processing
- ROI selection
- processed XANES export
- integrated XRF spectrum export
- live MCA spectrum view
- stop/stopall control

## Development Mode

Dry-run mode should simulate:

- sample queue execution
- ion chamber transmission data
- sample/reference ratios
- optional XRF spectrum data
- stop/stopall behavior

Dry-run must never import `motorlist.py`, connect to EPICS, move motors, or start detector acquisition.
