"""Hardware interfaces and implementations for FastXAFS."""

from __future__ import annotations

import math
import random
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

import numpy as np

from .beamline_constants import FILTER_POSITIONS, ZEBRA_PVS, XSPRESS3_PVS


ORIGINAL_DIR = Path(__file__).resolve().parents[1] / "original"


def ensure_original_on_path() -> None:
    original = str(ORIGINAL_DIR)
    if original not in sys.path:
        sys.path.insert(0, original)


@dataclass(slots=True)
class ZebraCapture:
    ioni1: np.ndarray
    ioni2: np.ndarray
    ioni3: np.ndarray
    encoder: np.ndarray
    div_max: float


class BeamlineHardware(Protocol):
    def prepare_sample(self, x: float, y: float, element_edge: str, start_energy_kev: float) -> None:
        ...

    def set_zebra_encoder_reference(self) -> None:
        ...

    def check_pitch(self) -> None:
        ...

    def start_xrf_capture(self, file_name: str, npoints: int) -> None:
        ...

    def stop_xrf_capture(self) -> None:
        ...

    def run_theta_scan(self, theta_start: float, theta_stop: float, theta_delta: float, npoints: int, velocity: float, direction: int) -> ZebraCapture:
        ...

    def stop_all(self) -> None:
        ...


class DryRunHardware:
    def __init__(self) -> None:
        self.current_theta = 8.0

    def prepare_sample(self, x: float, y: float, element_edge: str, start_energy_kev: float) -> None:
        time.sleep(0.05)

    def set_zebra_encoder_reference(self) -> None:
        time.sleep(0.02)

    def check_pitch(self) -> None:
        time.sleep(0.5)

    def start_xrf_capture(self, file_name: str, npoints: int) -> None:
        time.sleep(0.05)

    def stop_xrf_capture(self) -> None:
        time.sleep(0.02)

    def run_theta_scan(self, theta_start: float, theta_stop: float, theta_delta: float, npoints: int, velocity: float, direction: int) -> ZebraCapture:
        count = max(10, min(npoints, 2000))
        encoder = np.linspace(theta_start, theta_stop, count)
        phase = np.linspace(0, math.pi * 2, count)
        base = np.linspace(0, count * 100.0, count)
        ioni1 = base + 15 * np.sin(phase) + random.random()
        ioni2 = base * 0.65 + 9 * np.sin(phase + 0.5) + 50
        ioni3 = base * 0.35 + 7 * np.sin(phase + 1.0) + 25
        return ZebraCapture(ioni1=ioni1, ioni2=ioni2, ioni3=ioni3, encoder=encoder, div_max=1_000_000.0)

    def stop_all(self) -> None:
        return None


class EpicsHardware:
    """Real EPICS hardware adapter.

    Imports EPICS-connected modules lazily so importing this file is safe.
    """

    def __init__(self, xrf_file_path: str) -> None:
        ensure_original_on_path()
        import epics
        import motorlist as ml

        self.epics = epics
        self.ml = ml
        self.xrf_file_path = xrf_file_path

    def prepare_sample(self, x: float, y: float, element_edge: str, start_energy_kev: float) -> None:
        self.epics.caput("Energ:25002000selectMotors", 1)
        self.ml.DCM_THETA.VELO = 0.2
        self.ml.DCM_ENERGY.move(start_energy_kev + 0.2)
        self.ml.XANES_X.move(x)
        self.ml.XANES_Y.move(y)
        reference_position = FILTER_POSITIONS.get(element_edge, 16)
        self.ml.XANES_Reference.move(reference_position)
        self.ml.XANES_X.move(x, wait=True)
        self.ml.XANES_Y.move(y, wait=True)
        self.ml.XANES_Reference.move(reference_position, wait=True)
        while not self.epics.caget("Energ:25002000dmov"):
            time.sleep(0.1)

    def set_zebra_encoder_reference(self) -> None:
        realtheta = self.ml.DCM_THETA.get_position()
        self.epics.caput(ZEBRA_PVS["m2_eres"], 0.0000037464974)
        time.sleep(0.1)
        self.epics.caput(ZEBRA_PVS["pos2_set"], realtheta)
        time.sleep(0.1)

    def check_pitch(self) -> None:
        ensure_original_on_path()
        import checkpitchbayes as checkpitch

        checkpitch.checkpitch()

    def start_xrf_capture(self, file_name: str, npoints: int) -> None:
        self.epics.caput(XSPRESS3_PVS["file_path"], self.xrf_file_path)
        self.epics.caput(XSPRESS3_PVS["capture"], 0)
        self.epics.caput(XSPRESS3_PVS["acquire"], 0)
        self.epics.caput(XSPRESS3_PVS["num_images"], npoints)
        self.epics.caput(XSPRESS3_PVS["erase"], 1)
        self.epics.caput(XSPRESS3_PVS["update"], 1)
        self.epics.caput(XSPRESS3_PVS["file_name"], file_name)
        self.epics.caput(XSPRESS3_PVS["trigger_mode"], 3)
        self.epics.caput(XSPRESS3_PVS["acquire"], 1)
        self.epics.caput(XSPRESS3_PVS["capture"], 1)

    def stop_xrf_capture(self) -> None:
        self.epics.caput(XSPRESS3_PVS["capture"], 0)
        self.epics.caput(XSPRESS3_PVS["acquire"], 0)

    def run_theta_scan(self, theta_start: float, theta_stop: float, theta_delta: float, npoints: int, velocity: float, direction: int) -> ZebraCapture:
        theta_delta_step = theta_delta / npoints
        self.epics.caput(ZEBRA_PVS["pc_dir"], direction)
        self.epics.caput(ZEBRA_PVS["gate_start"], theta_start)
        self.epics.caput(ZEBRA_PVS["gate_width"], theta_delta + 0.1)
        self.epics.caput(ZEBRA_PVS["gate_step"], theta_delta + 0.2)
        self.epics.caput(ZEBRA_PVS["gate_ngate"], 1)
        self.epics.caput(ZEBRA_PVS["pulse_start"], 0)
        self.epics.caput(ZEBRA_PVS["pulse_step"], theta_delta_step)
        self.epics.caput(ZEBRA_PVS["pulse_width"], theta_delta_step * 0.9)
        self.epics.caput(ZEBRA_PVS["pulse_max"], npoints)
        time.sleep(1)

        self.ml.DCM_THETA.VELO = 0.2
        if direction:
            self.ml.DCM_THETA.move(theta_start + 0.03, wait=True)
        else:
            self.ml.DCM_THETA.move(theta_start - 0.03, wait=True)

        time.sleep(0.2)
        self.epics.caput(ZEBRA_PVS["sys_reset"], 1)
        self.epics.caput(ZEBRA_PVS["pc_arm"], 1)
        self.ml.DCM_THETA.VELO = min(velocity, 0.2)
        self.ml.DCM_THETA.BVEL = min(velocity, 0.2)
        if direction:
            self.ml.DCM_THETA.move(theta_stop - 0.02, wait=True)
        else:
            self.ml.DCM_THETA.move(theta_stop + 0.02, wait=True)

        time.sleep(2)
        self.epics.caput(ZEBRA_PVS["pc_disarm"], 1)
        self.ml.DCM_THETA.VELO = 0.2
        self.ml.DCM_THETA.BVEL = 0.2

        npoints_real = int(self.epics.caget(ZEBRA_PVS["num_captured"]))
        ioni1 = self.epics.caget(ZEBRA_PVS["div1"], count=npoints)[: npoints_real - 1]
        ioni2 = self.epics.caget(ZEBRA_PVS["div2"], count=npoints)[: npoints_real - 1]
        ioni3 = self.epics.caget(ZEBRA_PVS["div3"], count=npoints)[: npoints_real - 1]
        encoder = self.epics.caget(ZEBRA_PVS["encoder"], count=npoints)[: npoints_real - 1]
        div_max = self.epics.caget(ZEBRA_PVS["div_max"])
        return ZebraCapture(ioni1=ioni1, ioni2=ioni2, ioni3=ioni3, encoder=encoder, div_max=div_max)

    def stop_all(self) -> None:
        self.epics.caput("Rfa:Info.NIST", "stopall")
