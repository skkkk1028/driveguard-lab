"""Validated FastAPI request and response contracts."""

from typing import Annotated, Self

from pydantic import (
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    model_validator,
)

from app.domain import (
    DrivingStrategy,
    RiskThresholdSnapshot,
    SimulationResult,
)


def _require_json_number(value: object) -> object:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("value must be a JSON number")
    return value


FiniteNonNegativeFloat = Annotated[
    float,
    BeforeValidator(_require_json_number),
    Field(ge=0, allow_inf_nan=False),
]
FinitePositiveFloat = Annotated[
    float,
    BeforeValidator(_require_json_number),
    Field(gt=0, allow_inf_nan=False),
]


class _RequestModel(BaseModel):
    """Shared strict and immutable request-model configuration."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class ScenarioParametersInput(_RequestModel):
    """Physical parameters shared by simulation and evaluation requests."""

    ego_initial_speed_mps: FiniteNonNegativeFloat
    lead_initial_speed_mps: FiniteNonNegativeFloat
    initial_gap_m: FinitePositiveFloat
    lead_brake_start_s: FiniteNonNegativeFloat
    lead_braking_deceleration_mps2: FinitePositiveFloat
    ego_reaction_time_s: FiniteNonNegativeFloat
    ego_max_braking_deceleration_mps2: FinitePositiveFloat
    simulation_step_s: FinitePositiveFloat
    max_simulation_time_s: FinitePositiveFloat

    @model_validator(mode="after")
    def validate_time_relationships(self) -> Self:
        """Reject time configurations the domain contract cannot represent."""

        if self.lead_brake_start_s >= self.max_simulation_time_s:
            raise ValueError(
                "lead_brake_start_s must be less than max_simulation_time_s"
            )
        if self.simulation_step_s > self.max_simulation_time_s:
            raise ValueError(
                "simulation_step_s must be less than or equal to "
                "max_simulation_time_s"
            )
        return self


class SimulationScenarioInput(ScenarioParametersInput):
    """Complete scenario input for one supported strategy."""

    strategy: DrivingStrategy


class RiskThresholdsInput(_RequestModel):
    """Complete optional override for heuristic risk thresholds."""

    emergency_ttc_s: FinitePositiveFloat
    danger_ttc_s: FinitePositiveFloat
    caution_ttc_s: FinitePositiveFloat
    danger_thw_s: FinitePositiveFloat
    caution_thw_s: FinitePositiveFloat

    @model_validator(mode="after")
    def validate_threshold_order(self) -> Self:
        """Require the same strict ordering as the simulation core."""

        if not self.emergency_ttc_s < self.danger_ttc_s < self.caution_ttc_s:
            raise ValueError(
                "threshold order must satisfy emergency_ttc_s < danger_ttc_s "
                "< caution_ttc_s"
            )
        if not self.danger_thw_s < self.caution_thw_s:
            raise ValueError(
                "threshold order must satisfy danger_thw_s < caution_thw_s"
            )
        return self


class SimulationRequest(_RequestModel):
    """Request for one complete strategy simulation."""

    scenario: SimulationScenarioInput
    risk_thresholds: RiskThresholdsInput | None = None


class StrategyEvaluationRequest(_RequestModel):
    """Request for fixed-order evaluation of all supported strategies."""

    baseline_scenario: ScenarioParametersInput
    risk_thresholds: RiskThresholdsInput | None = None


class RegressionSuiteRequest(_RequestModel):
    """Optional threshold override for the standard regression suite."""

    risk_thresholds: RiskThresholdsInput | None = None


class SimulationRunResponse(BaseModel):
    """Threshold snapshot and result for one simulation request."""

    model_config = ConfigDict(frozen=True, from_attributes=True)

    thresholds: RiskThresholdSnapshot
    result: SimulationResult


class ApiErrorDetail(BaseModel):
    """One machine-addressable request validation error."""

    model_config = ConfigDict(frozen=True)

    location: list[str | int]
    message: str
    error_type: str


class ApiError(BaseModel):
    """Stable error payload nested inside the API error envelope."""

    model_config = ConfigDict(frozen=True)

    code: str
    message: str
    details: list[ApiErrorDetail]


class ApiErrorResponse(BaseModel):
    """Stable response envelope for invalid API requests."""

    model_config = ConfigDict(frozen=True)

    error: ApiError
