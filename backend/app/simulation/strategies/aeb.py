"""Stateless baseline AEB action selection and braking commands."""

from math import isfinite

from app.domain import ControlAction, RiskLevel

AEB_PARTIAL_BRAKING_FRACTION = 0.5


def select_aeb_action(risk_level: RiskLevel) -> ControlAction:
    """Map a preclassified risk level to a baseline AEB action."""

    if risk_level is RiskLevel.DANGER:
        return ControlAction.PARTIAL_BRAKING
    if risk_level is RiskLevel.EMERGENCY:
        return ControlAction.EMERGENCY_BRAKING
    return ControlAction.NONE


def calculate_aeb_acceleration_mps2(
    control_action: ControlAction,
    max_braking_deceleration_mps2: float,
) -> float:
    """Return the signed acceleration command for a baseline AEB action."""

    if not isfinite(max_braking_deceleration_mps2):
        raise ValueError("max_braking_deceleration_mps2 must be finite")
    if max_braking_deceleration_mps2 <= 0:
        raise ValueError("max_braking_deceleration_mps2 must be greater than zero")

    if control_action is ControlAction.NONE:
        return 0.0
    if control_action is ControlAction.PARTIAL_BRAKING:
        return -(
            AEB_PARTIAL_BRAKING_FRACTION * max_braking_deceleration_mps2
        )
    if control_action is ControlAction.EMERGENCY_BRAKING:
        return -max_braking_deceleration_mps2
    raise ValueError(
        "control_action must be NONE, PARTIAL_BRAKING, or EMERGENCY_BRAKING"
    )
