"""Pure FastXAFS calculations."""

from __future__ import annotations

import math

import numpy as np

from .beamline_constants import D_SPACING
from .domain import ScanMode


def add_constant_if_decreasing(values, constant):
    corrected = np.array(values, dtype=float)
    for index in range(1, len(corrected)):
        if corrected[index] < corrected[index - 1]:
            corrected[index:] += constant
    return corrected


def angle_to_energy(angles):
    angles_rad = np.radians(angles)
    wavelengths = 2 * D_SPACING * np.sin(angles_rad)
    return 1.239843 / wavelengths


def energy_to_angle(energy):
    wavelength = 1.239843 / energy
    sin_theta = wavelength / (2 * D_SPACING)
    if sin_theta > 1 or sin_theta < -1:
        raise ValueError("Energy is too high/low to result in a valid angle.")
    return math.degrees(math.asin(sin_theta))


def scan_energy_range(edge_energy_kev: float, mode: ScanMode) -> tuple[float, float]:
    if mode == ScanMode.XANES:
        return edge_energy_kev - 0.3, edge_energy_kev + 0.4
    return edge_energy_kev - 0.25, edge_energy_kev + 0.75


def compute_transmission_arrays(ioni1, ioni2, ioni3):
    i0 = np.gradient(np.asarray(ioni1, dtype=float))
    i1 = np.gradient(np.asarray(ioni2, dtype=float))
    i2 = np.gradient(np.asarray(ioni3, dtype=float))
    sample = -i0 / i1
    reference = -i2 / i1
    return i0, i1, i2, sample, reference
