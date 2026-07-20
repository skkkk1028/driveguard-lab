"""Tests for the stateless Warning Only action selector."""

import pytest

from app.domain import ControlAction, RiskLevel
from app.simulation import select_warning_only_action


@pytest.mark.parametrize(
    ("risk_level", "expected_action"),
    [
        (RiskLevel.SAFE, ControlAction.NONE),
        (RiskLevel.CAUTION, ControlAction.NONE),
        (RiskLevel.DANGER, ControlAction.WARNING),
        (RiskLevel.EMERGENCY, ControlAction.WARNING),
    ],
)
def test_warning_only_maps_preclassified_risk_to_action(
    risk_level: RiskLevel,
    expected_action: ControlAction,
) -> None:
    assert select_warning_only_action(risk_level) is expected_action


def test_warning_only_selector_is_deterministic_and_stateless() -> None:
    risk_level = RiskLevel.DANGER

    first = select_warning_only_action(risk_level)
    recovered = select_warning_only_action(RiskLevel.SAFE)
    second = select_warning_only_action(risk_level)

    assert first is ControlAction.WARNING
    assert recovered is ControlAction.NONE
    assert second is first
    assert risk_level is RiskLevel.DANGER
