"""Versioned FastAPI routes for deterministic simulation capabilities."""

from typing import Any

from fastapi import APIRouter

from app.domain import (
    DrivingStrategy,
    JsonValue,
    LeadVehicleBrakingScenario,
    RegressionScenario,
    RegressionSuiteResult,
    RiskThresholdSnapshot,
    StrategyEvaluation,
    to_json_compatible,
)
from app.simulation import (
    DEFAULT_RISK_THRESHOLDS,
    REGRESSION_SCENARIOS,
    RiskThresholds,
    evaluate_strategies,
    run_lead_braking_scenario,
    run_regression_suite,
)

from .errors import (
    SIMULATION_LIMIT_ERROR_CODE,
    VALIDATION_ERROR_CODE,
    ApiInputError,
)
from .schemas import (
    ApiErrorDetail,
    ApiErrorResponse,
    RegressionSuiteRequest,
    RiskThresholdsInput,
    ScenarioParametersInput,
    SimulationRequest,
    SimulationRunResponse,
    StrategyEvaluationRequest,
)

MAX_SIMULATION_INTERVALS = 10_000
_ERROR_RESPONSES: dict[int | str, dict[str, Any]] = {
    422: {"model": ApiErrorResponse}
}

router = APIRouter(prefix="/api/v1")


def _risk_thresholds_from_input(
    value: RiskThresholdsInput | None,
) -> RiskThresholds:
    if value is None:
        return DEFAULT_RISK_THRESHOLDS
    return RiskThresholds(
        emergency_ttc_s=value.emergency_ttc_s,
        danger_ttc_s=value.danger_ttc_s,
        caution_ttc_s=value.caution_ttc_s,
        danger_thw_s=value.danger_thw_s,
        caution_thw_s=value.caution_thw_s,
    )


def _threshold_snapshot(thresholds: RiskThresholds) -> RiskThresholdSnapshot:
    return RiskThresholdSnapshot(
        emergency_ttc_s=thresholds.emergency_ttc_s,
        danger_ttc_s=thresholds.danger_ttc_s,
        caution_ttc_s=thresholds.caution_ttc_s,
        danger_thw_s=thresholds.danger_thw_s,
        caution_thw_s=thresholds.caution_thw_s,
    )


def _scenario_from_input(
    value: ScenarioParametersInput,
    *,
    strategy: DrivingStrategy,
) -> LeadVehicleBrakingScenario:
    return LeadVehicleBrakingScenario(
        ego_initial_speed_mps=value.ego_initial_speed_mps,
        lead_initial_speed_mps=value.lead_initial_speed_mps,
        initial_gap_m=value.initial_gap_m,
        lead_brake_start_s=value.lead_brake_start_s,
        lead_braking_deceleration_mps2=value.lead_braking_deceleration_mps2,
        ego_reaction_time_s=value.ego_reaction_time_s,
        ego_max_braking_deceleration_mps2=(
            value.ego_max_braking_deceleration_mps2
        ),
        simulation_step_s=value.simulation_step_s,
        max_simulation_time_s=value.max_simulation_time_s,
        strategy=strategy,
    )


def _enforce_simulation_limit(
    value: ScenarioParametersInput,
    *,
    location_field: str,
) -> None:
    maximum_representable_duration_s = (
        value.simulation_step_s * MAX_SIMULATION_INTERVALS
    )
    if value.max_simulation_time_s <= maximum_representable_duration_s:
        return

    raise ApiInputError(
        code=SIMULATION_LIMIT_ERROR_CODE,
        message=(
            f"Simulation exceeds the limit of {MAX_SIMULATION_INTERVALS} "
            "advancement intervals."
        ),
        details=(
            ApiErrorDetail(
                location=["body", location_field, "max_simulation_time_s"],
                message=(
                    "max_simulation_time_s must not exceed simulation_step_s "
                    f"multiplied by {MAX_SIMULATION_INTERVALS}"
                ),
                error_type=SIMULATION_LIMIT_ERROR_CODE,
            ),
        ),
    )


def _domain_validation_error(location: list[str | int], error: ValueError) -> None:
    raise ApiInputError(
        code=VALIDATION_ERROR_CODE,
        message="Request validation failed.",
        details=(
            ApiErrorDetail(
                location=location,
                message=str(error),
                error_type="value_error",
            ),
        ),
    ) from error


@router.post(
    "/simulations",
    response_model=SimulationRunResponse,
    responses=_ERROR_RESPONSES,
)
def create_simulation(request: SimulationRequest) -> JsonValue:
    """Run one deterministic lead-vehicle braking simulation."""

    _enforce_simulation_limit(request.scenario, location_field="scenario")
    try:
        scenario = _scenario_from_input(
            request.scenario,
            strategy=request.scenario.strategy,
        )
        thresholds = _risk_thresholds_from_input(request.risk_thresholds)
        result = run_lead_braking_scenario(scenario, thresholds=thresholds)
    except ValueError as error:
        _domain_validation_error(["body", "scenario"], error)

    return {
        "thresholds": to_json_compatible(_threshold_snapshot(thresholds)),
        "result": to_json_compatible(result),
    }


@router.post(
    "/evaluations",
    response_model=StrategyEvaluation,
    responses=_ERROR_RESPONSES,
)
def create_strategy_evaluation(request: StrategyEvaluationRequest) -> JsonValue:
    """Evaluate No Assist, Warning Only, and AEB for one baseline."""

    _enforce_simulation_limit(
        request.baseline_scenario,
        location_field="baseline_scenario",
    )
    try:
        baseline = _scenario_from_input(
            request.baseline_scenario,
            strategy=DrivingStrategy.NO_ASSIST,
        )
        thresholds = _risk_thresholds_from_input(request.risk_thresholds)
        result = evaluate_strategies(baseline, thresholds=thresholds)
    except ValueError as error:
        _domain_validation_error(["body", "baseline_scenario"], error)

    return to_json_compatible(result)


@router.get(
    "/regression-scenarios",
    response_model=list[RegressionScenario],
)
def list_regression_scenarios() -> JsonValue:
    """Return the immutable standard regression catalog in stable order."""

    return to_json_compatible(REGRESSION_SCENARIOS)


@router.post(
    "/regression-suites",
    response_model=RegressionSuiteResult,
    responses=_ERROR_RESPONSES,
)
def create_regression_suite(
    request: RegressionSuiteRequest | None = None,
) -> JsonValue:
    """Run every standard regression scenario with shared thresholds."""

    try:
        thresholds = _risk_thresholds_from_input(
            request.risk_thresholds if request is not None else None
        )
        result = run_regression_suite(thresholds=thresholds)
    except ValueError as error:
        _domain_validation_error(["body", "risk_thresholds"], error)

    return to_json_compatible(result)
