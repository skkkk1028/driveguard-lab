export type DrivingStrategy = "no_assist" | "warning_only" | "aeb";

export type RiskLevel = "safe" | "caution" | "danger" | "emergency";

export type ControlAction =
  | "none"
  | "warning"
  | "partial_braking"
  | "emergency_braking";

export type SimulationEventType =
  | "lead_braking_started"
  | "risk_level_changed"
  | "warning_triggered"
  | "partial_braking_triggered"
  | "emergency_braking_triggered"
  | "collision"
  | "simulation_completed";

export interface ScenarioParameters {
  ego_initial_speed_mps: number;
  lead_initial_speed_mps: number;
  initial_gap_m: number;
  lead_brake_start_s: number;
  lead_braking_deceleration_mps2: number;
  ego_reaction_time_s: number;
  ego_max_braking_deceleration_mps2: number;
  simulation_step_s: number;
  max_simulation_time_s: number;
}

export interface LeadVehicleBrakingScenario extends ScenarioParameters {
  strategy: DrivingStrategy;
}

export interface RiskThresholds {
  emergency_ttc_s: number;
  danger_ttc_s: number;
  caution_ttc_s: number;
  danger_thw_s: number;
  caution_thw_s: number;
}

export interface VehicleState {
  position_m: number;
  speed_mps: number;
  acceleration_mps2: number;
}

export interface RiskMetrics {
  gap_m: number;
  relative_speed_mps: number;
  ttc_s: number | null;
  thw_s: number | null;
  ego_stopping_distance_m: number;
  risk_level: RiskLevel;
}

export interface SimulationFrame {
  time_s: number;
  ego: VehicleState;
  lead: VehicleState;
  metrics: RiskMetrics;
  control_action: ControlAction;
}

export interface SimulationEvent {
  time_s: number;
  event_type: SimulationEventType;
  message: string;
}

export interface SimulationSummary {
  duration_s: number;
  collided: boolean;
  minimum_gap_m: number;
  minimum_ttc_s: number | null;
  final_gap_m: number;
  warning_trigger_time_s: number | null;
  aeb_trigger_time_s: number | null;
}

export interface SimulationResult {
  schema_version: "1.0";
  scenario: LeadVehicleBrakingScenario;
  frames: SimulationFrame[];
  events: SimulationEvent[];
  summary: SimulationSummary;
}

export interface SimulationRunResponse {
  thresholds: RiskThresholds;
  result: SimulationResult;
}

export interface StrategyOutcome {
  strategy: DrivingStrategy;
  result: SimulationResult;
  collision_time_s: number | null;
  final_ego_speed_mps: number;
  warning_command_duration_s: number;
  partial_braking_command_duration_s: number;
  emergency_braking_command_duration_s: number;
}

export interface StrategyEvaluation {
  schema_version: "1.0";
  baseline_scenario: LeadVehicleBrakingScenario;
  thresholds: RiskThresholds;
  no_assist: StrategyOutcome;
  warning_only: StrategyOutcome;
  aeb: StrategyOutcome;
  aeb_avoided_collision: boolean;
  aeb_collision_time_delta_s: number | null;
  aeb_minimum_gap_delta_m: number;
  aeb_final_gap_delta_m: number;
}

export interface RegressionScenario {
  scenario_id: string;
  description: string;
  baseline_scenario: LeadVehicleBrakingScenario;
}

export interface ApiErrorDetail {
  location: Array<string | number>;
  message: string;
  error_type: string;
}

export interface ApiErrorResponse {
  error: {
    code: string;
    message: string;
    details: ApiErrorDetail[];
  };
}

export interface SimulationRequest {
  scenario: LeadVehicleBrakingScenario;
  risk_thresholds?: RiskThresholds;
}

export interface StrategyEvaluationRequest {
  baseline_scenario: ScenarioParameters;
  risk_thresholds?: RiskThresholds;
}
