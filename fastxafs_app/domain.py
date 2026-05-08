"""Domain models for the clean FastXAFS application."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class ScanMode(str, Enum):
    XANES = "XANES"
    EXAFS = "EXAFS"


class AcquisitionMode(str, Enum):
    TRANSMISSION = "transmission"
    XRF = "xrf"


class RunState(str, Enum):
    IDLE = "idle"
    PREPARING = "preparing"
    CHECKING_PITCH = "checking_pitch"
    SCANNING = "scanning"
    STOPPING = "stopping"
    STOPPED = "stopped"
    FINISHED = "finished"
    ERROR = "error"


@dataclass(slots=True)
class Sample:
    name: str
    x: float
    y: float
    edge_energy_kev: float
    element_edge: str
    acquisition_time_s: float = 30.0
    npoints: int = 2000
    mode: ScanMode = ScanMode.XANES
    repeat: int = 1

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["mode"] = self.mode.value
        return payload


@dataclass(slots=True)
class QueueConfig:
    output_path: str = r"E:\ContXANES"
    repeat_queue: int = 1
    both_directions: bool = False
    acquisition_mode: AcquisitionMode = AcquisitionMode.TRANSMISSION
    check_pitch: bool = False

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["acquisition_mode"] = self.acquisition_mode.value
        payload["data_source"] = self.data_source
        payload["output_format"] = self.output_format
        return payload

    @property
    def data_source(self) -> str:
        return "XSPRESS3 HDF5" if self.acquisition_mode == AcquisitionMode.XRF else "Ion chambers"

    @property
    def output_format(self) -> str:
        return "HDF5" if self.acquisition_mode == AcquisitionMode.XRF else "CSV"


@dataclass(slots=True)
class ScanPoint:
    energy_kev: float
    i0: float
    i1: float
    i2: float
    encoder: float

    @property
    def sample_ratio(self) -> float:
        return -self.i0 / self.i1

    @property
    def reference_ratio(self) -> float:
        return -self.i2 / self.i1

    def to_dict(self) -> dict[str, float]:
        payload = asdict(self)
        payload["sample_ratio"] = self.sample_ratio
        payload["reference_ratio"] = self.reference_ratio
        return payload


@dataclass(slots=True)
class PlotData:
    energy: list[float] = field(default_factory=list)
    sample: list[float] = field(default_factory=list)
    reference: list[float] = field(default_factory=list)
    spectrum: list[float] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class RunStatus:
    state: RunState = RunState.IDLE
    message: str = "Ready"
    active_sample: str | None = None
    queue_index: int = 0
    queue_length: int = 0
    progress: float = 0.0
    current_energy_kev: float | None = None
    acquisition_mode: AcquisitionMode = AcquisitionMode.TRANSMISSION
    data_source: str = "Ion chambers"
    output_format: str = "CSV"
    can_start: bool = True
    can_stop: bool = False

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["state"] = self.state.value
        payload["acquisition_mode"] = self.acquisition_mode.value
        return payload
