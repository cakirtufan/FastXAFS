"""Application service layer used by the JavaScript UI."""

from __future__ import annotations

from .domain import AcquisitionMode, QueueConfig, Sample, ScanMode
from .hardware import DryRunHardware, EpicsHardware
from .scan_runner import ScanRunner


class FastXAFSService:
    def __init__(self, hardware_mode: str = "dry-run", xrf_file_path: str = "/mnt/raid-triglav/RFA-xspress3") -> None:
        if hardware_mode == "real":
            hardware = EpicsHardware(xrf_file_path=xrf_file_path)
        else:
            hardware = DryRunHardware()
        self.hardware_mode = hardware_mode
        self.runner = ScanRunner(hardware=hardware)

    def get_config(self) -> dict:
        return self.runner.config.to_dict()

    def update_config(self, payload: dict) -> dict:
        config = QueueConfig(
            output_path=str(payload.get("output_path", self.runner.config.output_path)),
            repeat_queue=int(payload.get("repeat_queue", self.runner.config.repeat_queue)),
            both_directions=bool(payload.get("both_directions", self.runner.config.both_directions)),
            acquisition_mode=AcquisitionMode(str(payload.get("acquisition_mode", self.runner.config.acquisition_mode.value))),
            check_pitch=bool(payload.get("check_pitch", self.runner.config.check_pitch)),
        )
        self.runner.set_config(config)
        return self.get_config()

    def get_samples(self) -> list[dict]:
        return [sample.to_dict() for sample in self.runner.samples]

    def set_samples(self, payload: list[dict]) -> list[dict]:
        samples = [self._parse_sample(item, index) for index, item in enumerate(payload)]
        self.runner.set_samples(samples)
        return self.get_samples()

    def get_status(self) -> dict:
        status = self.runner.status.to_dict()
        status["hardware_mode"] = self.hardware_mode
        return status

    def get_plot(self) -> dict:
        return self.runner.plot.to_dict()

    def start(self) -> dict:
        return self.runner.start().to_dict() | {"hardware_mode": self.hardware_mode}

    def stop_all(self) -> dict:
        return self.runner.stop_all().to_dict() | {"hardware_mode": self.hardware_mode}

    @staticmethod
    def _parse_sample(payload: dict, index: int) -> Sample:
        return Sample(
            name=str(payload.get("name") or f"Sample {index + 1}"),
            x=float(payload.get("x", 0.0)),
            y=float(payload.get("y", 0.0)),
            edge_energy_kev=float(payload.get("edge_energy_kev", 8.333)),
            element_edge=str(payload.get("element_edge") or "Ni K"),
            acquisition_time_s=float(payload.get("acquisition_time_s", 30.0)),
            npoints=int(payload.get("npoints", 2000)),
            mode=ScanMode(str(payload.get("mode", ScanMode.XANES.value))),
            repeat=max(1, int(payload.get("repeat", 1))),
        )
