"""Standard deterministic regression scenarios and batch evaluation."""

from app.domain import (
    SIMULATION_SCHEMA_VERSION,
    DrivingStrategy,
    LeadVehicleBrakingScenario,
    RegressionCaseResult,
    RegressionScenario,
    RegressionSuiteResult,
)

from .evaluation import _snapshot_risk_thresholds, evaluate_strategies
from .risk import DEFAULT_RISK_THRESHOLDS, RiskThresholds


def _baseline_scenario(
    *,
    ego_initial_speed_mps: float,
    lead_initial_speed_mps: float,
    initial_gap_m: float,
    lead_brake_start_s: float,
    lead_braking_deceleration_mps2: float,
    ego_reaction_time_s: float,
    ego_max_braking_deceleration_mps2: float,
    simulation_step_s: float,
    max_simulation_time_s: float,
) -> LeadVehicleBrakingScenario:
    return LeadVehicleBrakingScenario(
        ego_initial_speed_mps=ego_initial_speed_mps,
        lead_initial_speed_mps=lead_initial_speed_mps,
        initial_gap_m=initial_gap_m,
        lead_brake_start_s=lead_brake_start_s,
        lead_braking_deceleration_mps2=lead_braking_deceleration_mps2,
        ego_reaction_time_s=ego_reaction_time_s,
        ego_max_braking_deceleration_mps2=ego_max_braking_deceleration_mps2,
        simulation_step_s=simulation_step_s,
        max_simulation_time_s=max_simulation_time_s,
        strategy=DrivingStrategy.NO_ASSIST,
    )


REGRESSION_SCENARIOS = (
    RegressionScenario(
        scenario_id="stable_following",
        description="Stable following with no strategy intervention.",
        baseline_scenario=_baseline_scenario(
            ego_initial_speed_mps=10.0,
            lead_initial_speed_mps=10.0,
            initial_gap_m=50.0,
            lead_brake_start_s=1.0,
            lead_braking_deceleration_mps2=1.0,
            ego_reaction_time_s=0.5,
            ego_max_braking_deceleration_mps2=8.0,
            simulation_step_s=0.5,
            max_simulation_time_s=2.0,
        ),
    ),
    RegressionScenario(
        scenario_id="caution_only",
        description="Caution risk without Warning or AEB intervention.",
        baseline_scenario=_baseline_scenario(
            ego_initial_speed_mps=10.0,
            lead_initial_speed_mps=10.0,
            initial_gap_m=30.0,
            lead_brake_start_s=0.0,
            lead_braking_deceleration_mps2=5.0,
            ego_reaction_time_s=0.0,
            ego_max_braking_deceleration_mps2=100.0,
            simulation_step_s=0.5,
            max_simulation_time_s=1.5,
        ),
    ),
    RegressionScenario(
        scenario_id="warning_without_motion_change",
        description="Warning activation without changing the No Assist trajectory.",
        baseline_scenario=_baseline_scenario(
            ego_initial_speed_mps=10.0,
            lead_initial_speed_mps=10.0,
            initial_gap_m=30.0,
            lead_brake_start_s=0.0,
            lead_braking_deceleration_mps2=5.0,
            ego_reaction_time_s=0.0,
            ego_max_braking_deceleration_mps2=100.0,
            simulation_step_s=0.5,
            max_simulation_time_s=3.0,
        ),
    ),
    RegressionScenario(
        scenario_id="aeb_avoids_collision",
        description="Baseline AEB avoids a collision seen without assistance.",
        baseline_scenario=_baseline_scenario(
            ego_initial_speed_mps=10.0,
            lead_initial_speed_mps=10.0,
            initial_gap_m=15.0,
            lead_brake_start_s=0.0,
            lead_braking_deceleration_mps2=5.0,
            ego_reaction_time_s=0.0,
            ego_max_braking_deceleration_mps2=8.0,
            simulation_step_s=0.5,
            max_simulation_time_s=5.0,
        ),
    ),
    RegressionScenario(
        scenario_id="aeb_unavoidable_collision",
        description="Baseline AEB delays but does not avoid the collision.",
        baseline_scenario=_baseline_scenario(
            ego_initial_speed_mps=20.0,
            lead_initial_speed_mps=15.0,
            initial_gap_m=30.0,
            lead_brake_start_s=0.0,
            lead_braking_deceleration_mps2=4.0,
            ego_reaction_time_s=0.0,
            ego_max_braking_deceleration_mps2=8.0,
            simulation_step_s=0.5,
            max_simulation_time_s=5.0,
        ),
    ),
    RegressionScenario(
        scenario_id="initial_emergency_and_boundaries",
        description=(
            "Initial Emergency with an internal brake boundary and shortened step."
        ),
        baseline_scenario=_baseline_scenario(
            ego_initial_speed_mps=20.0,
            lead_initial_speed_mps=10.0,
            initial_gap_m=10.0,
            lead_brake_start_s=0.75,
            lead_braking_deceleration_mps2=4.0,
            ego_reaction_time_s=0.0,
            ego_max_braking_deceleration_mps2=8.0,
            simulation_step_s=0.5,
            max_simulation_time_s=1.1,
        ),
    ),
)


def run_regression_suite(
    *,
    thresholds: RiskThresholds = DEFAULT_RISK_THRESHOLDS,
) -> RegressionSuiteResult:
    """Evaluate the ordered standard regression catalog without pass/fail logic."""

    cases = tuple(
        RegressionCaseResult(
            scenario=scenario,
            evaluation=evaluate_strategies(
                scenario.baseline_scenario,
                thresholds=thresholds,
            ),
        )
        for scenario in REGRESSION_SCENARIOS
    )
    return RegressionSuiteResult(
        schema_version=SIMULATION_SCHEMA_VERSION,
        thresholds=_snapshot_risk_thresholds(thresholds),
        cases=cases,
    )
