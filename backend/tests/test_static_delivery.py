"""Tests for optional same-origin production Dashboard delivery."""

from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.delivery import mount_dashboard


def test_mounts_dashboard_without_shadowing_registered_routes(tmp_path: Path) -> None:
    (tmp_path / "index.html").write_text(
        "<h1>DriveGuard Dashboard</h1>",
        encoding="utf-8",
    )
    assets = tmp_path / "assets"
    assets.mkdir()
    (assets / "app.js").write_text("console.log('driveguard')", encoding="utf-8")
    application = FastAPI()

    @application.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    mount_dashboard(application, tmp_path)
    client = TestClient(application)

    assert client.get("/health").json() == {"status": "ok"}
    assert "DriveGuard Dashboard" in client.get("/").text
    assert "driveguard" in client.get("/assets/app.js").text


def test_rejects_a_configured_directory_without_vite_index(tmp_path: Path) -> None:
    with pytest.raises(RuntimeError, match="production index.html"):
        mount_dashboard(FastAPI(), tmp_path)
