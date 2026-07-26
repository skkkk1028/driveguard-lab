"""Tests for deterministic SUMO runtime discovery."""

import subprocess
from pathlib import Path

import pytest

import app.adapters.sumo.runtime as runtime_module
from app.adapters.sumo import SumoConfigurationError, inspect_sumo_runtime


def _mock_supported_runtime(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(runtime_module, "load_traci_client", lambda: object())
    monkeypatch.setattr(
        "app.adapters.sumo.runtime.subprocess.run",
        lambda *args, **kwargs: subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout="Eclipse SUMO sumo Version 1.27.1\n",
            stderr="",
        ),
    )


def test_reports_unavailable_when_no_binary_is_found(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(runtime_module, "_optional_package_home", lambda: None)
    monkeypatch.setattr("app.adapters.sumo.runtime.shutil.which", lambda name: None)
    runtime = inspect_sumo_runtime(environment={})
    assert not runtime.available
    assert runtime.reason == "SUMO binary was not found"


def test_explicit_binary_has_priority(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _mock_supported_runtime(monkeypatch)
    binary = tmp_path / "sumo.exe"
    binary.touch()
    runtime = inspect_sumo_runtime(binary, environment={"SUMO_BINARY": "ignored"})
    assert runtime.available
    assert runtime.source == "explicit"
    assert runtime.version == "1.27.1"


def test_sumo_binary_environment_has_priority_over_home(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _mock_supported_runtime(monkeypatch)
    binary = tmp_path / "configured-sumo.exe"
    binary.touch()
    runtime = inspect_sumo_runtime(
        environment={"SUMO_BINARY": str(binary), "SUMO_HOME": "ignored"}
    )
    assert runtime.source == "SUMO_BINARY"
    assert runtime.binary_path == str(binary.resolve())


def test_invalid_explicit_binary_is_not_silently_ignored(tmp_path: Path) -> None:
    with pytest.raises(SumoConfigurationError, match="does not exist"):
        inspect_sumo_runtime(tmp_path / "missing-sumo.exe")


def test_rejects_gui_and_unsupported_versions(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    gui = tmp_path / "sumo-gui.exe"
    gui.touch()
    with pytest.raises(SumoConfigurationError, match="headless"):
        inspect_sumo_runtime(gui)

    _mock_supported_runtime(monkeypatch)
    binary = tmp_path / "sumo.exe"
    binary.touch()
    monkeypatch.setattr(
        "app.adapters.sumo.runtime.subprocess.run",
        lambda *args, **kwargs: subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout="Eclipse SUMO sumo Version 1.26.0\n",
            stderr="",
        ),
    )
    runtime = inspect_sumo_runtime(binary)
    assert not runtime.available
    assert runtime.version == "1.26.0"
    assert runtime.reason == "SUMO 1.26.0 is unsupported; expected 1.27.1"


def test_requires_optional_traci_client(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    binary = tmp_path / "sumo.exe"
    binary.touch()
    monkeypatch.setattr(
        "app.adapters.sumo.runtime.importlib.util.find_spec",
        lambda name: None,
    )
    runtime = inspect_sumo_runtime(binary)
    assert not runtime.available
    assert runtime.reason == "the optional TraCI Python client is not installed"


def test_recognizes_current_windows_wheel_version_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _mock_supported_runtime(monkeypatch)
    binary = tmp_path / "sumo.exe"
    binary.touch()
    monkeypatch.setattr(
        "app.adapters.sumo.runtime.subprocess.run",
        lambda *args, **kwargs: subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout="Eclipse SUMO sumo 1.27.1\n",
            stderr="",
        ),
    )

    runtime = inspect_sumo_runtime(binary)

    assert runtime.available
    assert runtime.version == "1.27.1"
