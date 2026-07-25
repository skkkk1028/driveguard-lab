"""Tests for the stateless baseline AEB strategy."""

import pytest

from app.domain import ControlAction, RiskLevel
from app.simulation import (
    AEB_PARTIAL_BRAKING_FRACTION,
    calculate_aeb_acceleration_mps2,
    select_aeb_action,
)


@pytest.mark.parametrize(
    ("risk_level", "expected_action"),
    [
        (RiskLevel.SAFE, ControlAction.NONE),
        (RiskLevel.CAUTION, ControlAction.NONE),
        (RiskLevel.DANGER, ControlAction.PARTIAL_BRAKING),
        (RiskLevel.EMERGENCY, ControlAction.EMERGENCY_BRAKING),
    ],
)
def test_aeb_maps_preclassified_risk_to_action(
    risk_level: RiskLevel,
    expected_action: ControlAction,
) -> None:
    assert select_aeb_action(risk_level) is expected_action


def test_aeb_selector_is_deterministic_stateless_and_releasable() -> None:
    first = select_aeb_action(RiskLevel.DANGER)
    escalated = select_aeb_action(RiskLevel.EMERGENCY)
    released = select_aeb_action(RiskLevel.SAFE)
    second = select_aeb_action(RiskLevel.DANGER)

    assert first is ControlAction.PARTIAL_BRAKING
    assert escalated is ControlAction.EMERGENCY_BRAKING
    assert released is ControlAction.NONE
    assert second is first


@pytest.mark.parametrize(
    ("control_action", "expected_acceleration_mps2"),
    [
        (ControlAction.NONE, 0.0),
        (ControlAction.PARTIAL_BRAKING, -4.0),
        (ControlAction.EMERGENCY_BRAKING, -8.0),
    ],
)
def test_aeb_action_uses_signed_fraction_of_maximum_deceleration(
    control_action: ControlAction,
    expected_acceleration_mps2: float,
) -> None:
    assert AEB_PARTIAL_BRAKING_FRACTION == 0.5
    assert (
        calculate_aeb_acceleration_mps2(control_action, 8.0)
        == expected_acceleration_mps2
    )


def test_aeb_acceleration_rejects_warning_action() -> None:
    with pytest.raises(ValueError, match="control_action"):
        calculate_aeb_acceleration_mps2(ControlAction.WARNING, 8.0)


@pytest.mark.parametrize(
    "max_braking_deceleration_mps2",
    [0.0, -1.0, float("nan"), float("inf"), float("-inf")],
)
def test_aeb_acceleration_rejects_invalid_maximum_deceleration(
    max_braking_deceleration_mps2: float,
) -> None:
    with pytest.raises(ValueError, match="max_braking_deceleration_mps2"):
        calculate_aeb_acceleration_mps2(
            ControlAction.PARTIAL_BRAKING,
            max_braking_deceleration_mps2,
        )
