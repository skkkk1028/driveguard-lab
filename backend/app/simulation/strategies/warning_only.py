"""Stateless Warning Only action selection from a classified risk level."""

from app.domain import ControlAction, RiskLevel


def select_warning_only_action(risk_level: RiskLevel) -> ControlAction:
    """Map a preclassified risk level to a non-braking warning action."""

    if risk_level in (RiskLevel.DANGER, RiskLevel.EMERGENCY):
        return ControlAction.WARNING
    return ControlAction.NONE
