"""Tests for SUMO experiment command exit codes and JSON streams."""

import json

import pytest

import app.adapters.sumo.cli as cli_module
from app.adapters.sumo import SumoExecutionError, SumoRuntimeInfo
from app.adapters.sumo.cli import main
from app.domain import LeadVehicleBrakingScenario

from .support import AVAILABLE_RUNTIME


def test_doctor_returns_zero_and_json_for_supported_runtime(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(
        cli_module,
        "inspect_sumo_runtime",
        lambda binary=None: AVAILABLE_RUNTIME,
    )
    assert main(["doctor"]) == 0
    output = json.loads(capsys.readouterr().out)
    assert output["available"] is True
    assert output["version"] == "1.27.1"


def test_doctor_returns_two_when_runtime_is_unavailable(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(
        cli_module,
        "inspect_sumo_runtime",
        lambda binary=None: SumoRuntimeInfo(
            False,
            None,
            None,
            None,
            "SUMO binary was not found",
        ),
    )
    assert main(["doctor"]) == 2
    assert json.loads(capsys.readouterr().out)["available"] is False


def test_replay_command_selects_catalog_scenario_and_strategy(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    captured: list[tuple[LeadVehicleBrakingScenario, object]] = []

    def fake_replay(
        scenario: LeadVehicleBrakingScenario,
        *,
        binary: object = None,
    ) -> SumoRuntimeInfo:
        captured.append((scenario, binary))
        return AVAILABLE_RUNTIME

    monkeypatch.setattr(cli_module, "replay_scenario_in_sumo", fake_replay)
    assert (
        main(
            [
                "replay",
                "--scenario-id",
                "stable_following",
                "--strategy",
                "warning_only",
            ]
        )
        == 0
    )
    assert captured[0][0].strategy.value == "warning_only"
    assert json.loads(capsys.readouterr().out)["available"] is True


def test_execution_failure_returns_three(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def fail(*args: object, **kwargs: object) -> None:
        raise SumoExecutionError("probe failed")

    monkeypatch.setattr(cli_module, "probe_scenario_in_sumo", fail)
    assert (
        main(
            [
                "probe",
                "--scenario-id",
                "stable_following",
                "--strategy",
                "aeb",
            ]
        )
        == 3
    )
    assert json.loads(capsys.readouterr().err) == {"error": "probe failed"}
