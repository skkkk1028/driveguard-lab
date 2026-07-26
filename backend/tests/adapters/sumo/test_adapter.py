"""Unit tests for both SUMO exploration modes through a session fake."""

from dataclasses import FrozenInstanceError

import pytest

import app.adapters.sumo.adapter as adapter_module
from app.adapters.sumo import (
    SumoAdapterMode,
    SumoExecutionError,
    probe_scenario_in_sumo,
    replay_scenario_in_sumo,
)
from app.adapters.sumo.serialization import to_sumo_json_compatible
from app.domain import ControlAction, DrivingStrategy, RegressionScenario
from app.simulation import REGRESSION_SCENARIOS

from .support import AVAILABLE_RUNTIME, FakeSessionFactory, scenario


@pytest.fixture(autouse=True)
def available_runtime(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        adapter_module,
        "inspect_sumo_runtime",
        lambda binary=None: AVAILABLE_RUNTIME,
    )


@pytest.mark.parametrize("catalog_entry", REGRESSION_SCENARIOS)
@pytest.mark.parametrize("strategy", list(DrivingStrategy))
def test_replay_round_trips_every_regression_scenario_and_strategy(
    catalog_entry: RegressionScenario,
    strategy: DrivingStrategy,
) -> None:
    scenario_id = catalog_entry.scenario_id
    report = replay_scenario_in_sumo(
        scenario(scenario_id, strategy),
        _session_factory=FakeSessionFactory(),
    )

    assert report.mode is SumoAdapterMode.TRAJECTORY_REPLAY
    assert report.maximum_absolute_position_delta_m == 0.0
    assert report.maximum_absolute_speed_delta_mps == 0.0
    assert report.maximum_absolute_gap_delta_m == 0.0
    assert report.frames[-1].time_s == report.reference_result.frames[-1].time_s


def test_report_is_immutable_and_serializes_without_domain_whitelist_changes() -> None:
    report = replay_scenario_in_sumo(
        scenario(),
        _session_factory=FakeSessionFactory(),
    )
    with pytest.raises(FrozenInstanceError):
        report.sumo_step_s = 2.0  # type: ignore[misc]
    serialized = to_sumo_json_compatible(report)
    assert isinstance(serialized, dict)
    assert serialized["adapter_schema_version"] == "0.1"
    assert serialized["mode"] == "trajectory_replay"
    reference_result = serialized["reference_result"]
    assert isinstance(reference_result, dict)
    assert reference_result["schema_version"] == "1.0"


def test_replay_rejects_a_state_round_trip_outside_tolerance() -> None:
    with pytest.raises(SumoExecutionError, match="tolerance"):
        replay_scenario_in_sumo(
            scenario(),
            _session_factory=FakeSessionFactory(observation_offset_m=1e-6),
        )


def test_native_probe_reuses_initial_action_and_exact_boundary_schedule() -> None:
    factory = FakeSessionFactory()
    report = probe_scenario_in_sumo(
        scenario("initial_emergency_and_boundaries", DrivingStrategy.AEB),
        _session_factory=factory,
    )

    assert report.mode is SumoAdapterMode.CONTROLLED_NATIVE_PROBE
    assert [frame.time_s for frame in report.frames] == [0.0, 0.5, 1.0, 1.1]
    assert report.frames[0].control_action is ControlAction.EMERGENCY_BRAKING
    commands = factory.sessions[0].acceleration_commands
    assert commands[0][1] == -8.0
    boundary_command = next(
        command for command in commands if abs(command[0] - 0.75) < 1e-12
    )
    assert boundary_command[2] == -4.0
    assert commands[-1][3] == pytest.approx(0.05)


def test_native_no_assist_and_warning_only_keep_identical_motion() -> None:
    no_assist = probe_scenario_in_sumo(
        scenario("warning_without_motion_change", DrivingStrategy.NO_ASSIST),
        _session_factory=FakeSessionFactory(),
    )
    warning = probe_scenario_in_sumo(
        scenario("warning_without_motion_change", DrivingStrategy.WARNING_ONLY),
        _session_factory=FakeSessionFactory(),
    )
    assert tuple((frame.ego, frame.lead) for frame in no_assist.frames) == tuple(
        (frame.ego, frame.lead) for frame in warning.frames
    )


def test_point_and_physical_collision_semantics_are_reported_separately() -> None:
    report = probe_scenario_in_sumo(
        scenario("aeb_unavoidable_collision", DrivingStrategy.NO_ASSIST),
        _session_factory=FakeSessionFactory(physical_collision_gap_m=3.0),
    )
    assert report.sumo_physical_collided
    assert report.driveguard_point_collided
    assert report.sumo_physical_collision_time_s is not None
    assert report.driveguard_point_collision_time_s is not None
    assert (
        report.sumo_physical_collision_time_s
        <= report.driveguard_point_collision_time_s
    )


def test_session_is_closed_when_native_step_fails() -> None:
    factory = FakeSessionFactory(fail_on_step=True)
    with pytest.raises(SumoExecutionError, match="fake SUMO step failed"):
        probe_scenario_in_sumo(scenario(), _session_factory=factory)
    assert factory.sessions[0].closed
