import type {
  ControlAction,
  DrivingStrategy,
  RegressionScenario,
  RiskLevel,
  SimulationEventType,
  SimulationRunResponse,
  StrategyEvaluation,
} from "./types";

type JsonRecord = Record<string, unknown>;

const DRIVING_STRATEGIES = ["no_assist", "warning_only", "aeb"] as const;
const RISK_LEVELS = ["safe", "caution", "danger", "emergency"] as const;
const CONTROL_ACTIONS = [
  "none",
  "warning",
  "partial_braking",
  "emergency_braking",
] as const;
const EVENT_TYPES = [
  "lead_braking_started",
  "risk_level_changed",
  "warning_triggered",
  "partial_braking_triggered",
  "emergency_braking_triggered",
  "collision",
  "simulation_completed",
] as const;

export class ResponseContractViolation extends Error {
  readonly path: string;

  constructor(path: string, message: string) {
    super(`${path}: ${message}`);
    this.name = "ResponseContractViolation";
    this.path = path;
  }
}

function fail(path: string, message: string): never {
  throw new ResponseContractViolation(path, message);
}

function record(value: unknown, path: string): JsonRecord {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    fail(path, "expected an object");
  }
  return value as JsonRecord;
}

function array(value: unknown, path: string): unknown[] {
  if (!Array.isArray(value)) {
    fail(path, "expected an array");
  }
  return value;
}

function string(value: unknown, path: string): string {
  if (typeof value !== "string") {
    fail(path, "expected a string");
  }
  return value;
}

function boolean(value: unknown, path: string): boolean {
  if (typeof value !== "boolean") {
    fail(path, "expected a boolean");
  }
  return value;
}

function finiteNumber(value: unknown, path: string): number {
  if (typeof value !== "number" || !Number.isFinite(value)) {
    fail(path, "expected a finite number");
  }
  return value;
}

function nonNegativeNumber(value: unknown, path: string): number {
  const parsed = finiteNumber(value, path);
  if (parsed < 0) {
    fail(path, "expected a non-negative number");
  }
  return parsed;
}

function positiveNumber(value: unknown, path: string): number {
  const parsed = finiteNumber(value, path);
  if (parsed <= 0) {
    fail(path, "expected a positive number");
  }
  return parsed;
}

function nullableFiniteNumber(value: unknown, path: string): number | null {
  return value === null ? null : finiteNumber(value, path);
}

function nullableNonNegativeNumber(value: unknown, path: string): number | null {
  return value === null ? null : nonNegativeNumber(value, path);
}

function enumValue<T extends string>(
  value: unknown,
  allowed: readonly T[],
  path: string,
): T {
  if (typeof value !== "string" || !allowed.includes(value as T)) {
    fail(path, `expected one of ${allowed.join(", ")}`);
  }
  return value as T;
}

function validateScenario(
  value: unknown,
  path: string,
  expectedStrategy?: DrivingStrategy,
): void {
  const scenario = record(value, path);
  nonNegativeNumber(scenario.ego_initial_speed_mps, `${path}.ego_initial_speed_mps`);
  nonNegativeNumber(scenario.lead_initial_speed_mps, `${path}.lead_initial_speed_mps`);
  positiveNumber(scenario.initial_gap_m, `${path}.initial_gap_m`);
  const brakeStart = nonNegativeNumber(
    scenario.lead_brake_start_s,
    `${path}.lead_brake_start_s`,
  );
  positiveNumber(
    scenario.lead_braking_deceleration_mps2,
    `${path}.lead_braking_deceleration_mps2`,
  );
  nonNegativeNumber(scenario.ego_reaction_time_s, `${path}.ego_reaction_time_s`);
  positiveNumber(
    scenario.ego_max_braking_deceleration_mps2,
    `${path}.ego_max_braking_deceleration_mps2`,
  );
  const step = positiveNumber(scenario.simulation_step_s, `${path}.simulation_step_s`);
  const maximumTime = positiveNumber(
    scenario.max_simulation_time_s,
    `${path}.max_simulation_time_s`,
  );
  const strategy = enumValue(
    scenario.strategy,
    DRIVING_STRATEGIES,
    `${path}.strategy`,
  );
  if (brakeStart >= maximumTime) {
    fail(path, "lead brake start must precede the maximum time");
  }
  if (step > maximumTime) {
    fail(path, "simulation step must not exceed the maximum time");
  }
  if (expectedStrategy !== undefined && strategy !== expectedStrategy) {
    fail(`${path}.strategy`, `expected ${expectedStrategy}`);
  }
}

function validateThresholds(value: unknown, path: string): void {
  const thresholds = record(value, path);
  const emergencyTtc = positiveNumber(
    thresholds.emergency_ttc_s,
    `${path}.emergency_ttc_s`,
  );
  const dangerTtc = positiveNumber(thresholds.danger_ttc_s, `${path}.danger_ttc_s`);
  const cautionTtc = positiveNumber(
    thresholds.caution_ttc_s,
    `${path}.caution_ttc_s`,
  );
  const dangerThw = positiveNumber(thresholds.danger_thw_s, `${path}.danger_thw_s`);
  const cautionThw = positiveNumber(
    thresholds.caution_thw_s,
    `${path}.caution_thw_s`,
  );
  if (!(emergencyTtc < dangerTtc && dangerTtc < cautionTtc)) {
    fail(path, "TTC thresholds are not strictly ordered");
  }
  if (!(dangerThw < cautionThw)) {
    fail(path, "THW thresholds are not strictly ordered");
  }
}

function validateVehicleState(value: unknown, path: string): void {
  const state = record(value, path);
  finiteNumber(state.position_m, `${path}.position_m`);
  nonNegativeNumber(state.speed_mps, `${path}.speed_mps`);
  finiteNumber(state.acceleration_mps2, `${path}.acceleration_mps2`);
}

function validateMetrics(value: unknown, path: string): void {
  const metrics = record(value, path);
  finiteNumber(metrics.gap_m, `${path}.gap_m`);
  finiteNumber(metrics.relative_speed_mps, `${path}.relative_speed_mps`);
  nullableFiniteNumber(metrics.ttc_s, `${path}.ttc_s`);
  nullableFiniteNumber(metrics.thw_s, `${path}.thw_s`);
  nonNegativeNumber(
    metrics.ego_stopping_distance_m,
    `${path}.ego_stopping_distance_m`,
  );
  enumValue(metrics.risk_level, RISK_LEVELS, `${path}.risk_level`) satisfies RiskLevel;
}

function validateSummary(value: unknown, path: string): void {
  const summary = record(value, path);
  nonNegativeNumber(summary.duration_s, `${path}.duration_s`);
  boolean(summary.collided, `${path}.collided`);
  finiteNumber(summary.minimum_gap_m, `${path}.minimum_gap_m`);
  nullableFiniteNumber(summary.minimum_ttc_s, `${path}.minimum_ttc_s`);
  finiteNumber(summary.final_gap_m, `${path}.final_gap_m`);
  nullableNonNegativeNumber(
    summary.warning_trigger_time_s,
    `${path}.warning_trigger_time_s`,
  );
  nullableNonNegativeNumber(summary.aeb_trigger_time_s, `${path}.aeb_trigger_time_s`);
}

function validateSimulationResult(
  value: unknown,
  path: string,
  expectedStrategy?: DrivingStrategy,
): void {
  const result = record(value, path);
  if (result.schema_version !== "1.0") {
    fail(`${path}.schema_version`, "expected schema version 1.0");
  }
  validateScenario(result.scenario, `${path}.scenario`, expectedStrategy);

  const frames = array(result.frames, `${path}.frames`);
  if (frames.length === 0) {
    fail(`${path}.frames`, "expected at least one retained frame");
  }
  let previousFrameTime = -Infinity;
  frames.forEach((frameValue, index) => {
    const framePath = `${path}.frames[${index}]`;
    const frame = record(frameValue, framePath);
    const time = nonNegativeNumber(frame.time_s, `${framePath}.time_s`);
    if (index === 0 && time !== 0) {
      fail(`${framePath}.time_s`, "the first retained frame must be at time zero");
    }
    if (time <= previousFrameTime) {
      fail(`${framePath}.time_s`, "retained frame times must be strictly increasing");
    }
    previousFrameTime = time;
    validateVehicleState(frame.ego, `${framePath}.ego`);
    validateVehicleState(frame.lead, `${framePath}.lead`);
    validateMetrics(frame.metrics, `${framePath}.metrics`);
    enumValue(frame.control_action, CONTROL_ACTIONS, `${framePath}.control_action`) satisfies ControlAction;
  });

  const events = array(result.events, `${path}.events`);
  let previousEventTime = -Infinity;
  let completionCount = 0;
  let completionTime: number | null = null;
  events.forEach((eventValue, index) => {
    const eventPath = `${path}.events[${index}]`;
    const event = record(eventValue, eventPath);
    const time = nonNegativeNumber(event.time_s, `${eventPath}.time_s`);
    if (time < previousEventTime) {
      fail(`${eventPath}.time_s`, "event times must be non-decreasing");
    }
    previousEventTime = time;
    const eventType = enumValue(
      event.event_type,
      EVENT_TYPES,
      `${eventPath}.event_type`,
    ) satisfies SimulationEventType;
    string(event.message, `${eventPath}.message`);
    if (eventType === "simulation_completed") {
      completionCount += 1;
      completionTime = time;
      if (index !== events.length - 1) {
        fail(`${eventPath}.event_type`, "the completion event must be last");
      }
    }
  });
  if (completionCount !== 1) {
    fail(`${path}.events`, "expected exactly one completion event");
  }
  if (completionTime !== previousFrameTime) {
    fail(`${path}.events`, "the completion event must use the final frame time");
  }

  validateSummary(result.summary, `${path}.summary`);
  const summary = record(result.summary, `${path}.summary`);
  if (summary.duration_s !== previousFrameTime) {
    fail(`${path}.summary.duration_s`, "expected the final frame time");
  }
}

function validateOutcome(
  value: unknown,
  path: string,
  expectedStrategy: DrivingStrategy,
): void {
  const outcome = record(value, path);
  const strategy = enumValue(
    outcome.strategy,
    DRIVING_STRATEGIES,
    `${path}.strategy`,
  );
  if (strategy !== expectedStrategy) {
    fail(`${path}.strategy`, `expected ${expectedStrategy}`);
  }
  validateSimulationResult(outcome.result, `${path}.result`, expectedStrategy);
  nullableNonNegativeNumber(outcome.collision_time_s, `${path}.collision_time_s`);
  nonNegativeNumber(outcome.final_ego_speed_mps, `${path}.final_ego_speed_mps`);
  nonNegativeNumber(
    outcome.warning_command_duration_s,
    `${path}.warning_command_duration_s`,
  );
  nonNegativeNumber(
    outcome.partial_braking_command_duration_s,
    `${path}.partial_braking_command_duration_s`,
  );
  nonNegativeNumber(
    outcome.emergency_braking_command_duration_s,
    `${path}.emergency_braking_command_duration_s`,
  );
}

export function decodeRegressionScenarios(value: unknown): RegressionScenario[] {
  const scenarios = array(value, "response");
  const identifiers = new Set<string>();
  scenarios.forEach((scenarioValue, index) => {
    const path = `response[${index}]`;
    const scenario = record(scenarioValue, path);
    const identifier = string(scenario.scenario_id, `${path}.scenario_id`);
    if (identifier.length === 0 || identifiers.has(identifier)) {
      fail(`${path}.scenario_id`, "expected a non-empty unique identifier");
    }
    identifiers.add(identifier);
    string(scenario.description, `${path}.description`);
    validateScenario(scenario.baseline_scenario, `${path}.baseline_scenario`, "no_assist");
  });
  return value as RegressionScenario[];
}

export function decodeSimulationRunResponse(
  value: unknown,
  expectedStrategy?: DrivingStrategy,
): SimulationRunResponse {
  const response = record(value, "response");
  validateThresholds(response.thresholds, "response.thresholds");
  validateSimulationResult(response.result, "response.result", expectedStrategy);
  return value as SimulationRunResponse;
}

export function decodeStrategyEvaluation(value: unknown): StrategyEvaluation {
  const evaluation = record(value, "response");
  if (evaluation.schema_version !== "1.0") {
    fail("response.schema_version", "expected schema version 1.0");
  }
  validateScenario(evaluation.baseline_scenario, "response.baseline_scenario", "no_assist");
  validateThresholds(evaluation.thresholds, "response.thresholds");
  validateOutcome(evaluation.no_assist, "response.no_assist", "no_assist");
  validateOutcome(evaluation.warning_only, "response.warning_only", "warning_only");
  validateOutcome(evaluation.aeb, "response.aeb", "aeb");
  boolean(evaluation.aeb_avoided_collision, "response.aeb_avoided_collision");
  nullableFiniteNumber(
    evaluation.aeb_collision_time_delta_s,
    "response.aeb_collision_time_delta_s",
  );
  finiteNumber(evaluation.aeb_minimum_gap_delta_m, "response.aeb_minimum_gap_delta_m");
  finiteNumber(evaluation.aeb_final_gap_delta_m, "response.aeb_final_gap_delta_m");
  return value as StrategyEvaluation;
}
