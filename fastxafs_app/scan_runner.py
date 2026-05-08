"""Clean scan runner preserving the production acquisition order."""

from __future__ import annotations

import threading
import time
from datetime import datetime
from pathlib import Path

from .calculations import add_constant_if_decreasing, angle_to_energy, compute_transmission_arrays, energy_to_angle, scan_energy_range
from .data_writer import write_transmission_csv
from .domain import AcquisitionMode, PlotData, QueueConfig, RunState, RunStatus, Sample, ScanMode, ScanPoint
from .hardware import BeamlineHardware


class ScanRunner:
    def __init__(self, hardware: BeamlineHardware, samples: list[Sample] | None = None, config: QueueConfig | None = None) -> None:
        self.hardware = hardware
        self.samples = samples or [
            Sample(
                name="Sample 1",
                x=0.0,
                y=0.0,
                edge_energy_kev=8.333,
                element_edge="Ni K",
                acquisition_time_s=12.0,
                npoints=800,
                mode=ScanMode.XANES,
            )
        ]
        self.config = config or QueueConfig()
        self.status = RunStatus(queue_length=len(self.samples))
        self.plot = PlotData()
        self._lock = threading.RLock()
        self._stop_requested = threading.Event()
        self._worker: threading.Thread | None = None

    def set_samples(self, samples: list[Sample]) -> None:
        with self._lock:
            self.samples = samples
            self.status.queue_length = len(samples)

    def set_config(self, config: QueueConfig) -> None:
        with self._lock:
            self.config = config
            self._sync_status_mode()

    def start(self) -> RunStatus:
        with self._lock:
            if self.status.state in {RunState.PREPARING, RunState.CHECKING_PITCH, RunState.SCANNING}:
                return self.status
            self._stop_requested.clear()
            self.status = RunStatus(
                state=RunState.PREPARING,
                message="Starting queue",
                queue_length=len(self.samples) * max(1, self.config.repeat_queue),
                can_start=False,
                can_stop=True,
            )
            self._sync_status_mode()
            self.plot = PlotData()
            self._worker = threading.Thread(target=self._run_queue, daemon=True, name="fastxafs-scan-runner")
            self._worker.start()
            return self.status

    def stop_all(self) -> RunStatus:
        self._stop_requested.set()
        self.hardware.stop_all()
        with self._lock:
            self.status.state = RunState.STOPPED
            self.status.message = "Stop all requested"
            self.status.can_start = True
            self.status.can_stop = False
            return self.status

    def _run_queue(self) -> None:
        try:
            total = len(self.samples) * max(1, self.config.repeat_queue)
            completed = 0
            for queue_repeat in range(max(1, self.config.repeat_queue)):
                for sample in self.samples:
                    if self._stop_requested.is_set():
                        self._mark_stopped()
                        return
                    for sample_repeat in range(max(1, sample.repeat)):
                        self._run_sample(sample, queue_repeat, sample_repeat, completed, total, direction=1)
                        completed += 1
                        if self.config.both_directions:
                            self._run_sample(sample, queue_repeat, sample_repeat, completed, total, direction=0)
            with self._lock:
                self.status.state = RunState.FINISHED
                self.status.message = "Queue finished"
                self.status.progress = 1.0
                self.status.can_start = True
                self.status.can_stop = False
        except Exception as exc:
            with self._lock:
                self.status.state = RunState.ERROR
                self.status.message = str(exc)
                self.status.can_start = True
                self.status.can_stop = False

    def _run_sample(self, sample: Sample, queue_repeat: int, sample_repeat: int, completed: int, total: int, direction: int) -> None:
        start_energy, stop_energy = scan_energy_range(sample.edge_energy_kev, sample.mode)
        if direction == 0:
            start_energy, stop_energy = stop_energy, start_energy

        with self._lock:
            self.status.state = RunState.PREPARING
            self.status.active_sample = sample.name
            self.status.queue_index = completed
            self.status.queue_length = total
            self.status.message = f"Preparing {sample.name}"

        self.hardware.prepare_sample(sample.x, sample.y, sample.element_edge, min(start_energy, stop_energy))
        self.hardware.set_zebra_encoder_reference()

        if self.config.check_pitch:
            with self._lock:
                self.status.state = RunState.CHECKING_PITCH
                self.status.message = f"Checking pitch for {sample.name}"
            self.hardware.check_pitch()

        theta_start = energy_to_angle(start_energy)
        theta_stop = energy_to_angle(stop_energy)
        theta_delta = theta_start - theta_stop
        velocity = theta_delta / sample.acquisition_time_s
        unique = datetime.now().strftime("%Y%m%d%H%M%S")
        xrf_name = f"{sample.name}{unique}"

        if self.config.acquisition_mode == AcquisitionMode.XRF:
            self.hardware.start_xrf_capture(xrf_name, sample.npoints)

        with self._lock:
            self.status.state = RunState.SCANNING
            self.status.message = f"Scanning {sample.name}"

        capture = self.hardware.run_theta_scan(theta_start, theta_stop, theta_delta, sample.npoints, velocity, direction)

        if self.config.acquisition_mode == AcquisitionMode.XRF:
            self.hardware.stop_xrf_capture()

        points = self._build_points(capture)
        with self._lock:
            self.plot.energy = [point.energy_kev for point in points]
            self.plot.sample = [point.sample_ratio for point in points]
            self.plot.reference = [point.reference_ratio for point in points]
            self.status.current_energy_kev = points[-1].energy_kev if points else None
            self.status.progress = min(1.0, (completed + 1) / max(1, total))

        if self.config.acquisition_mode == AcquisitionMode.TRANSMISSION:
            suffix = "back" if direction == 0 else str(sample_repeat)
            filename = f"{sample.name}_{queue_repeat}_{suffix}_{unique}.csv"
            write_transmission_csv(Path(self.config.output_path) / filename, sample, points)

    def _build_points(self, capture) -> list[ScanPoint]:
        ioni1 = add_constant_if_decreasing(capture.ioni1, capture.div_max)
        ioni2 = add_constant_if_decreasing(capture.ioni2, capture.div_max)
        ioni3 = add_constant_if_decreasing(capture.ioni3, capture.div_max)
        i0, i1, i2, _, _ = compute_transmission_arrays(ioni1, ioni2, ioni3)
        energies = angle_to_energy(capture.encoder)
        return [
            ScanPoint(float(energy), float(a), float(b), float(c), float(enc))
            for energy, a, b, c, enc in zip(energies, i0, i1, i2, capture.encoder)
        ]

    def _mark_stopped(self) -> None:
        with self._lock:
            self.status.state = RunState.STOPPED
            self.status.message = "Queue stopped"
            self.status.can_start = True
            self.status.can_stop = False

    def _sync_status_mode(self) -> None:
        self.status.acquisition_mode = self.config.acquisition_mode
        self.status.data_source = self.config.data_source
        self.status.output_format = self.config.output_format
