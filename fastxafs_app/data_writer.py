"""Data writers for FastXAFS outputs."""

from __future__ import annotations

from pathlib import Path

from .domain import Sample, ScanPoint


def write_transmission_csv(path: str | Path, sample: Sample, points: list[ScanPoint]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8", newline="") as handle:
        handle.write("#Sample_Name X Y Edge Time N-Points Element Mode Repeat\n")
        handle.write(
            f"#{sample.name} {sample.x} {sample.y} {sample.edge_energy_kev} "
            f"{sample.acquisition_time_s} {sample.npoints} {sample.element_edge} "
            f"{sample.mode.value} {sample.repeat}\n"
        )
        handle.write("Ene I0 I1 I2 ENC\n")
        for point in points:
            handle.write(f"{point.energy_kev} {point.i0} {point.i1} {point.i2} {point.encoder}\n")
