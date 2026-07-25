import { describe, expect, it } from "vitest";

import type { RegressionScenario } from "../api/types";
import {
  DEFAULT_SCENARIO_VALUES,
  DEFAULT_THRESHOLD_VALUES,
  scenarioValuesFromPreset,
  validateForm,
} from "./form";

describe("dashboard form validation", () => {
  it("parses the default scenario without sending threshold overrides", () => {
    const result = validateForm(
      DEFAULT_SCENARIO_VALUES,
      DEFAULT_THRESHOLD_VALUES,
      false,
    );

    expect(result).toEqual({
      valid: true,
      data: {
        scenario: {
          ego_initial_speed_mps: 10,
          lead_initial_speed_mps: 10,
          initial_gap_m: 15,
          lead_brake_start_s: 0,
          lead_braking_deceleration_mps2: 5,
          ego_reaction_time_s: 0,
          ego_max_braking_deceleration_mps2: 8,
          simulation_step_s: 0.5,
          max_simulation_time_s: 5,
        },
      },
    });
  });

  it("includes all five ordered thresholds only when enabled", () => {
    const result = validateForm(
      DEFAULT_SCENARIO_VALUES,
      DEFAULT_THRESHOLD_VALUES,
      true,
    );

    expect(result.valid).toBe(true);
    if (result.valid) {
      expect(result.data.thresholds).toEqual({
        emergency_ttc_s: 1,
        danger_ttc_s: 2,
        caution_ttc_s: 4,
        danger_thw_s: 1,
        caution_thw_s: 2,
      });
    }
  });

  it.each([
    ["empty", { initial_gap_m: "" }, "initial_gap_m"],
    ["non-finite", { initial_gap_m: "Infinity" }, "initial_gap_m"],
    ["negative", { ego_initial_speed_mps: "-1" }, "ego_initial_speed_mps"],
    ["zero positive field", { initial_gap_m: "0" }, "initial_gap_m"],
    ["late brake start", { lead_brake_start_s: "5" }, "lead_brake_start_s"],
    ["oversized step", { simulation_step_s: "6" }, "simulation_step_s"],
  ])("rejects %s input", (_, replacement, errorField) => {
    const result = validateForm(
      { ...DEFAULT_SCENARIO_VALUES, ...replacement },
      DEFAULT_THRESHOLD_VALUES,
      false,
    );

    expect(result.valid).toBe(false);
    if (!result.valid) {
      expect(result.errors).toHaveProperty(errorField);
    }
  });

  it("accepts exactly 10,000 intervals and rejects 10,001", () => {
    const boundary = {
      ...DEFAULT_SCENARIO_VALUES,
      simulation_step_s: "0.001",
      max_simulation_time_s: "10",
    };
    const overLimit = { ...boundary, max_simulation_time_s: "10.001" };

    expect(
      validateForm(boundary, DEFAULT_THRESHOLD_VALUES, false).valid,
    ).toBe(true);
    const rejected = validateForm(overLimit, DEFAULT_THRESHOLD_VALUES, false);
    expect(rejected.valid).toBe(false);
    if (!rejected.valid) {
      expect(rejected.errors.max_simulation_time_s).toMatch(/10,000/);
    }
  });

  it("rejects invalid TTC and THW threshold ordering", () => {
    const result = validateForm(
      DEFAULT_SCENARIO_VALUES,
      {
        ...DEFAULT_THRESHOLD_VALUES,
        danger_ttc_s: "1",
        caution_thw_s: "1",
      },
      true,
    );

    expect(result.valid).toBe(false);
    if (!result.valid) {
      expect(result.errors.caution_ttc_s).toMatch(/紧急 < 危险 < 谨慎/);
      expect(result.errors.caution_thw_s).toMatch(/危险 < 谨慎/);
    }
  });

  it("copies only physical fields from a regression preset", () => {
    const preset = {
      scenario_id: "custom",
      description: "test",
      baseline_scenario: {
        ego_initial_speed_mps: 20,
        lead_initial_speed_mps: 15,
        initial_gap_m: 30,
        lead_brake_start_s: 0,
        lead_braking_deceleration_mps2: 4,
        ego_reaction_time_s: 0,
        ego_max_braking_deceleration_mps2: 8,
        simulation_step_s: 0.5,
        max_simulation_time_s: 5,
        strategy: "no_assist",
      },
    } satisfies RegressionScenario;

    const values = scenarioValuesFromPreset(preset);

    expect(values.ego_initial_speed_mps).toBe("20");
    expect(values.lead_initial_speed_mps).toBe("15");
    expect(values).not.toHaveProperty("strategy");
  });
});
