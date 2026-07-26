"""Headless checks against the optional, supported Eclipse SUMO runtime."""

from dataclasses import replace

import pytest

from app.adapters.sumo import (
    REPLAY_ABSOLUTE_TOLERANCE,
    inspect_sumo_runtime,
    probe_scenario_in_sumo,
    replay_scenario_in_sumo,
)
from app.adapters.sumo.serialization import to_sumo_json_compatible
from app.domain import DrivingStrategy, LeadVehicleBrakingScenario, RegressionScenario
from app.simulation import REGRESSION_SCENARIOS

pytestmark = pytest.mark.sumo


@pytest.fixture(scope="module", autouse=True)
def supported_sumo_runtime() -> None:
    runtime = inspect_sumo_runtime()
    if not runtime.available:
        pytest.skip(runtime.reason or "supported SUMO runtime is unavailable")


def _scenario(
    catalog_entry: RegressionScenario,
    strategy: DrivingStrategy,
) -> LeadVehicleBrakingScenario:
    return replace(catalog_entry.baseline_scenario, strategy=strategy)


@pytest.mark.parametrize("catalog_entry", REGRESSION_SCENARIOS)
@pytest.mark.parametrize("strategy", list(DrivingStrategy))
def test_live_replay_has_near_zero_state_error(
    catalog_entry: RegressionScenario,
    strategy: DrivingStrategy,
) -> None:
    report = replay_scenario_in_sumo(_scenario(catalog_entry, strategy))

    assert report.maximum_absolute_position_delta_m <= REPLAY_ABSOLUTE_TOLERANCE
    assert report.maximum_absolute_speed_delta_mps <= REPLAY_ABSOLUTE_TOLERANCE
    assert report.maximum_absolute_gap_delta_m <= REPLAY_ABSOLUTE_TOLERANCE


@pytest.mark.parametrize(
    "scenario_id,strategy",
    (
        ("stable_following", DrivingStrategy.NO_ASSIST),
        ("aeb_avoids_collision", DrivingStrategy.AEB),
        ("initial_emergency_and_boundaries", DrivingStrategy.AEB),
    ),
)
def test_live_native_probe_is_deterministic(
    scenario_id: str,
    strategy: DrivingStrategy,
) -> None:
    catalog_entry = next(
        item for item in REGRESSION_SCENARIOS if item.scenario_id == scenario_id
    )
    first = probe_scenario_in_sumo(_scenario(catalog_entry, strategy))
    second = probe_scenario_in_sumo(_scenario(catalog_entry, strategy))

    assert to_sumo_json_compatible(first) == to_sumo_json_compatible(second)


def test_live_no_assist_and_warning_only_have_the_same_native_motion() -> None:
    catalog_entry = next(
        item
        for item in REGRESSION_SCENARIOS
        if item.scenario_id == "warning_without_motion_change"
    )
    no_assist = probe_scenario_in_sumo(
        _scenario(catalog_entry, DrivingStrategy.NO_ASSIST)
    )
    warning_only = probe_scenario_in_sumo(
        _scenario(catalog_entry, DrivingStrategy.WARNING_ONLY)
    )

    assert tuple((frame.ego, frame.lead) for frame in no_assist.frames) == tuple(
        (frame.ego, frame.lead) for frame in warning_only.frames
    )
