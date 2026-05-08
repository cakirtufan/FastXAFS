"""Run the clean FastXAFS app."""

from __future__ import annotations

import argparse
import os

import uvicorn


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the clean FastXAFS app.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8770)
    parser.add_argument("--hardware-mode", choices=["dry-run", "real"], default="dry-run")
    parser.add_argument("--xrf-file-path", default="/mnt/raid-triglav/RFA-xspress3")
    args = parser.parse_args()

    os.environ["FASTXAFS_HARDWARE_MODE"] = args.hardware_mode
    os.environ["FASTXAFS_XRF_FILE_PATH"] = args.xrf_file_path
    uvicorn.run("fastxafs_app.api:app", host=args.host, port=args.port, reload=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
