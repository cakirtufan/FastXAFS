"""Smoke-test the dry-run backend without EPICS imports."""

from __future__ import annotations

import time
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastxafs_app.service import FastXAFSService


def main() -> int:
    service = FastXAFSService(hardware_mode="dry-run")
    assert service.get_status()["hardware_mode"] == "dry-run"
    assert service.get_samples()

    output_path = ROOT / "smoke-output"
    service.update_config({"repeat_queue": 1, "output_path": str(output_path)})
    status = service.start()
    assert status["state"] in {"preparing", "checking_pitch", "scanning", "finished"}

    deadline = time.monotonic() + 3.0
    saw_progress = False
    while time.monotonic() < deadline:
        status = service.get_status()
        frame = service.get_plot()
        if status["progress"] > 0 and frame["energy"]:
            saw_progress = True
            break
        time.sleep(0.05)

    assert saw_progress, "dry-run scan did not produce progress"
    service.stop_all()
    final_state = service.get_status()["state"]
    assert final_state in {"stopped", "finished"}
    print("Dry-run backend smoke test passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
