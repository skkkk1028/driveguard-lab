"""Tests for SUMO time representability and resource boundaries."""

from dataclasses import replace

import pytest

from app.adapters.sumo import SumoConfigurationError
from app.adapters.sumo.schedule import calculate_sumo_step_s

from .support import scenario


def test_calculates_boundary_aligned_step_for_short_tail_scenario() -> None:
    assert calculate_sumo_step_s(
        scenario("initial_emergency_and_boundaries")
    ) == pytest.approx(0.05)


def test_rejects_main_steps_above_one_second() -> None:
    with pytest.raises(SumoConfigurationError, match="must not exceed 1 s"):
        calculate_sumo_step_s(replace(scenario(), simulation_step_s=1.001))


def test_rejects_durations_above_sixty_seconds() -> None:
    with pytest.raises(SumoConfigurationError, match="must not exceed 60 s"):
        calculate_sumo_step_s(replace(scenario(), max_simulation_time_s=60.001))


def test_rejects_times_not_representable_to_one_millisecond() -> None:
    with pytest.raises(SumoConfigurationError, match="exactly representable"):
        calculate_sumo_step_s(replace(scenario(), lead_brake_start_s=0.0005))


def test_accepts_the_largest_millisecond_schedule_within_the_limit() -> None:
    constrained = replace(
        scenario(),
        simulation_step_s=1.0,
        lead_brake_start_s=0.001,
        max_simulation_time_s=60.0,
    )
    assert calculate_sumo_step_s(constrained) == 0.001
