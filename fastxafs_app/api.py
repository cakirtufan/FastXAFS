"""FastAPI app for the clean FastXAFS backend."""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .service import FastXAFSService


ROOT = Path(__file__).resolve().parent
STATIC_DIR = ROOT / "ui"

hardware_mode = os.environ.get("FASTXAFS_HARDWARE_MODE", "dry-run")
xrf_file_path = os.environ.get("FASTXAFS_XRF_FILE_PATH", "/mnt/raid-triglav/RFA-xspress3")
service = FastXAFSService(hardware_mode=hardware_mode, xrf_file_path=xrf_file_path)

app = FastAPI(title="FastXAFS Clean App", version="0.2.0")


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/status")
def status() -> dict:
    return service.get_status()


@app.get("/api/config")
def config() -> dict:
    return service.get_config()


@app.put("/api/config")
def update_config(payload: dict) -> dict:
    return service.update_config(payload)


@app.get("/api/samples")
def samples() -> list[dict]:
    return service.get_samples()


@app.put("/api/samples")
def set_samples(payload: list[dict]) -> list[dict]:
    return service.set_samples(payload)


@app.get("/api/plot")
def plot() -> dict:
    return service.get_plot()


@app.post("/api/scan/start")
def start() -> dict:
    return service.start()


@app.post("/api/scan/stop-all")
def stop_all() -> dict:
    return service.stop_all()


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
