"""Representability checks and exact millisecond SUMO schedules."""

from decimal import Decimal
from math import gcd

from app.domain import LeadVehicleBrakingScenario

from .exceptions import SumoConfigurationError

MILLISECONDS_PER_SECOND = 1_000
MAX_SUMO_MAIN_STEP_S = 1.0
MAX_SUMO_DURATION_S = 60.0
MAX_SUMO_SUBSTEPS = 100_000


def _exact_milliseconds(field_name: str, value: float) -> int:
    milliseconds = Decimal(str(value)) * MILLISECONDS_PER_SECOND
    integral = milliseconds.to_integral_value()
    if milliseconds != integral:
        raise SumoConfigurationError(
            f"{field_name} must be exactly representable to 0.001 s"
        )
    return int(integral)


def calculate_sumo_step_s(scenario: LeadVehicleBrakingScenario) -> float:
    """Return a millisecond-aligned step dividing every scenario boundary."""

    if scenario.simulation_step_s > MAX_SUMO_MAIN_STEP_S:
        raise SumoConfigurationError("simulation_step_s must not exceed 1 s")
    if scenario.max_simulation_time_s > MAX_SUMO_DURATION_S:
        raise SumoConfigurationError("max_simulation_time_s must not exceed 60 s")

    step_ms = _exact_milliseconds("simulation_step_s", scenario.simulation_step_s)
    brake_start_ms = _exact_milliseconds(
        "lead_brake_start_s", scenario.lead_brake_start_s
    )
    duration_ms = _exact_milliseconds(
        "max_simulation_time_s", scenario.max_simulation_time_s
    )
    quantum_ms = gcd(gcd(step_ms, brake_start_ms), duration_ms)
    if quantum_ms <= 0:
        quantum_ms = gcd(step_ms, duration_ms)
    substeps = duration_ms // quantum_ms
    if substeps > MAX_SUMO_SUBSTEPS:
        raise SumoConfigurationError(
            f"SUMO experiment exceeds {MAX_SUMO_SUBSTEPS} substeps"
        )
    return quantum_ms / MILLISECONDS_PER_SECOND
