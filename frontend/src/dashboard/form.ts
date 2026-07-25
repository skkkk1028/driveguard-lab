import type {
  DrivingStrategy,
  RegressionScenario,
  RiskThresholds,
  ScenarioParameters,
} from "../api/types";

export const MAX_SIMULATION_INTERVALS = 10_000;
export const DEFAULT_PRESET_ID = "aeb_avoids_collision";
export const DEFAULT_STRATEGY: DrivingStrategy = "aeb";

export type RunMode = "simulation" | "evaluation";
export type ScenarioField = keyof ScenarioParameters;
export type ThresholdField = keyof RiskThresholds;
export type FormErrorKey = ScenarioField | ThresholdField | "strategy";
export type FormErrors = Partial<Record<FormErrorKey, string>>;
export type ScenarioFormValues = Record<ScenarioField, string>;
export type ThresholdFormValues = Record<ThresholdField, string>;

export const DEFAULT_SCENARIO_VALUES: ScenarioFormValues = {
  ego_initial_speed_mps: "10",
  lead_initial_speed_mps: "10",
  initial_gap_m: "15",
  lead_brake_start_s: "0",
  lead_braking_deceleration_mps2: "5",
  ego_reaction_time_s: "0",
  ego_max_braking_deceleration_mps2: "8",
  simulation_step_s: "0.5",
  max_simulation_time_s: "5",
};

export const DEFAULT_THRESHOLD_VALUES: ThresholdFormValues = {
  emergency_ttc_s: "1",
  danger_ttc_s: "2",
  caution_ttc_s: "4",
  danger_thw_s: "1",
  caution_thw_s: "2",
};

export const PRESET_LABELS: Record<string, string> = {
  stable_following: "稳定跟车",
  caution_only: "仅谨慎风险",
  warning_without_motion_change: "告警但不改变运动",
  aeb_avoids_collision: "AEB 避免碰撞",
  aeb_unavoidable_collision: "AEB 无法避免碰撞",
  initial_emergency_and_boundaries: "初始紧急与边界步长",
};

interface ValidFormData {
  scenario: ScenarioParameters;
  thresholds?: RiskThresholds;
}

export type FormValidationResult =
  | { valid: true; data: ValidFormData }
  | { valid: false; errors: FormErrors };

const NON_NEGATIVE_SCENARIO_FIELDS: ScenarioField[] = [
  "ego_initial_speed_mps",
  "lead_initial_speed_mps",
  "lead_brake_start_s",
  "ego_reaction_time_s",
];

const POSITIVE_SCENARIO_FIELDS: ScenarioField[] = [
  "initial_gap_m",
  "lead_braking_deceleration_mps2",
  "ego_max_braking_deceleration_mps2",
  "simulation_step_s",
  "max_simulation_time_s",
];

const THRESHOLD_FIELDS: ThresholdField[] = [
  "emergency_ttc_s",
  "danger_ttc_s",
  "caution_ttc_s",
  "danger_thw_s",
  "caution_thw_s",
];

function parseNumber(
  value: string,
  field: FormErrorKey,
  errors: FormErrors,
): number | undefined {
  if (value.trim() === "") {
    errors[field] = "请输入数值。";
    return undefined;
  }
  const parsed = Number(value);
  if (!Number.isFinite(parsed)) {
    errors[field] = "请输入有限数值。";
    return undefined;
  }
  return parsed;
}

export function scenarioValuesFromPreset(
  preset: RegressionScenario,
): ScenarioFormValues {
  const scenario = preset.baseline_scenario;
  return {
    ego_initial_speed_mps: String(scenario.ego_initial_speed_mps),
    lead_initial_speed_mps: String(scenario.lead_initial_speed_mps),
    initial_gap_m: String(scenario.initial_gap_m),
    lead_brake_start_s: String(scenario.lead_brake_start_s),
    lead_braking_deceleration_mps2: String(
      scenario.lead_braking_deceleration_mps2,
    ),
    ego_reaction_time_s: String(scenario.ego_reaction_time_s),
    ego_max_braking_deceleration_mps2: String(
      scenario.ego_max_braking_deceleration_mps2,
    ),
    simulation_step_s: String(scenario.simulation_step_s),
    max_simulation_time_s: String(scenario.max_simulation_time_s),
  };
}

export function validateForm(
  scenarioValues: ScenarioFormValues,
  thresholdValues: ThresholdFormValues,
  customThresholdsEnabled: boolean,
): FormValidationResult {
  const errors: FormErrors = {};
  const parsedScenario = {} as Record<ScenarioField, number | undefined>;

  for (const field of NON_NEGATIVE_SCENARIO_FIELDS) {
    const value = parseNumber(scenarioValues[field], field, errors);
    if (value !== undefined && value < 0) {
      errors[field] = "数值必须大于或等于 0。";
    }
    parsedScenario[field] = value;
  }
  for (const field of POSITIVE_SCENARIO_FIELDS) {
    const value = parseNumber(scenarioValues[field], field, errors);
    if (value !== undefined && value <= 0) {
      errors[field] = "数值必须大于 0。";
    }
    parsedScenario[field] = value;
  }

  const brakeStart = parsedScenario.lead_brake_start_s;
  const simulationStep = parsedScenario.simulation_step_s;
  const maximumTime = parsedScenario.max_simulation_time_s;
  if (
    brakeStart !== undefined &&
    maximumTime !== undefined &&
    brakeStart >= maximumTime
  ) {
    errors.lead_brake_start_s = "前车制动起点必须小于最大仿真时长。";
  }
  if (
    simulationStep !== undefined &&
    maximumTime !== undefined &&
    simulationStep > maximumTime
  ) {
    errors.simulation_step_s = "仿真步长不能大于最大仿真时长。";
  }
  if (
    simulationStep !== undefined &&
    simulationStep > 0 &&
    maximumTime !== undefined &&
    maximumTime > simulationStep * MAX_SIMULATION_INTERVALS
  ) {
    errors.max_simulation_time_s = `每个策略最多允许 ${MAX_SIMULATION_INTERVALS.toLocaleString("en-US")} 个推进区间。`;
  }

  let thresholds: RiskThresholds | undefined;
  if (customThresholdsEnabled) {
    const parsedThresholds = {} as Record<ThresholdField, number | undefined>;
    for (const field of THRESHOLD_FIELDS) {
      const value = parseNumber(thresholdValues[field], field, errors);
      if (value !== undefined && value <= 0) {
        errors[field] = "阈值必须大于 0。";
      }
      parsedThresholds[field] = value;
    }
    const emergencyTtc = parsedThresholds.emergency_ttc_s;
    const dangerTtc = parsedThresholds.danger_ttc_s;
    const cautionTtc = parsedThresholds.caution_ttc_s;
    if (
      emergencyTtc !== undefined &&
      dangerTtc !== undefined &&
      cautionTtc !== undefined &&
      !(emergencyTtc < dangerTtc && dangerTtc < cautionTtc)
    ) {
      errors.caution_ttc_s = "TTC 阈值必须满足紧急 < 危险 < 谨慎。";
    }
    const dangerThw = parsedThresholds.danger_thw_s;
    const cautionThw = parsedThresholds.caution_thw_s;
    if (
      dangerThw !== undefined &&
      cautionThw !== undefined &&
      dangerThw >= cautionThw
    ) {
      errors.caution_thw_s = "THW 阈值必须满足危险 < 谨慎。";
    }
    if (THRESHOLD_FIELDS.every((field) => parsedThresholds[field] !== undefined)) {
      thresholds = parsedThresholds as RiskThresholds;
    }
  }

  const scenarioFields = [
    ...NON_NEGATIVE_SCENARIO_FIELDS,
    ...POSITIVE_SCENARIO_FIELDS,
  ];
  if (
    Object.keys(errors).length > 0 ||
    !scenarioFields.every((field) => parsedScenario[field] !== undefined)
  ) {
    return { valid: false, errors };
  }

  return {
    valid: true,
    data: {
      scenario: parsedScenario as ScenarioParameters,
      ...(thresholds ? { thresholds } : {}),
    },
  };
}
