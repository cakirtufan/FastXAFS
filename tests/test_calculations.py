from __future__ import annotations

import math

import numpy as np

from fastxafs_app.calculations import (
    add_constant_if_decreasing,
    angle_to_energy,
    compute_transmission_arrays,
    energy_to_angle,
    scan_energy_range,
)
from fastxafs_app.domain import ScanMode


def test_energy_angle_roundtrip():
    energy = 8.333
    angle = energy_to_angle(energy)
    assert math.isclose(float(angle_to_energy(angle)), energy, rel_tol=1e-12)


def test_add_constant_if_decreasing_matches_legacy_behavior():
    result = add_constant_if_decreasing([10, 12, 2, 4], 20)
    np.testing.assert_allclose(result, [10, 12, 22, 24])


def test_compute_transmission_curves_uses_legacy_ratios():
    i0, i1, i2, sample, reference = compute_transmission_arrays(
        [0, 2, 4, 6],
        [0, 1, 2, 3],
        [0, 3, 6, 9],
    )
    np.testing.assert_allclose(i0, [2, 2, 2, 2])
    np.testing.assert_allclose(i1, [1, 1, 1, 1])
    np.testing.assert_allclose(i2, [3, 3, 3, 3])
    np.testing.assert_allclose(sample, [-2, -2, -2, -2])
    np.testing.assert_allclose(reference, [-3, -3, -3, -3])


def test_scan_energy_range_preserves_legacy_modes():
    assert scan_energy_range(8.0, ScanMode.XANES) == (7.7, 8.4)
    assert scan_energy_range(8.0, ScanMode.EXAFS) == (7.75, 8.75)
