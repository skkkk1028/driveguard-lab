import { describe, expect, it } from "vitest";

import type { SimulationFrame, SimulationResult } from "../api/types";
import {
  buildPlaybackModel,
  clampIndex,
  frameIndexAtOrAfter,
  frameIndexAtOrBefore,
  indexAtOrAfter,
  indexAtOrBefore,
  nearestIndex,
  sortedUniqueTimeline,
} from "./model";

function frame(time: number): SimulationFrame {
  return {
    time_s: time,
    ego: { position_m: time, speed_mps: 10, acceleration_mps2: 0 },
    lead: { position_m: time + 10, speed_mps: 8, acceleration_mps2: 0 },
    metrics: {
      gap_m: 10,
      relative_speed_mps: 2,
      ttc_s: 5,
      thw_s: 1,
      ego_stopping_distance_m: 6.25,
      risk_level: "safe",
    },
    control_action: "none",
  };
}

function result(times: number[], strategy: SimulationResult["scenario"]["strategy"]): SimulationResult {
  return {
    schema_version: "1.0",
    scenario: {
      ego_initial_speed_mps: 10,
      lead_initial_speed_mps: 8,
      initial_gap_m: 10,
      lead_brake_start_s: 0,
      lead_braking_deceleration_mps2: 5,
      ego_reaction_time_s: 0,
      ego_max_braking_deceleration_mps2: 8,
      simulation_step_s: 0.5,
      max_simulation_time_s: 2,
      strategy,
    },
    frames: times.map(frame),
    events: [],
    summary: {
      duration_s: times.at(-1) ?? 0,
      collided: false,
      minimum_gap_m: 10,
      minimum_ttc_s: 5,
      final_gap_m: 10,
      warning_trigger_time_s: null,
      aeb_trigger_time_s: null,
    },
  };
}

const thresholds = {
  emergency_ttc_s: 1,
  danger_ttc_s: 2,
  caution_ttc_s: 4,
  danger_thw_s: 1,
  caution_thw_s: 2,
};

describe("playback timeline model", () => {
  it("sorts and de-duplicates the union of retained frame times", () => {
    expect(
      sortedUniqueTimeline([
        result([0, 0.5, 1], "no_assist"),
        result([0, 0.25, 0.5, 1.1], "aeb"),
      ]),
    ).toEqual([0, 0.25, 0.5, 1, 1.1]);
  });

  it("finds previous, next and nearest retained times with clamping", () => {
    const times = [0, 0.5, 1, 1.1];
    expect(indexAtOrBefore(times, 0.75)).toBe(1);
    expect(indexAtOrBefore(times, -1)).toBe(0);
    expect(indexAtOrAfter(times, 0.75)).toBe(2);
    expect(indexAtOrAfter(times, 9)).toBe(3);
    expect(nearestIndex(times, 0.74)).toBe(1);
    expect(nearestIndex(times, 0.76)).toBe(2);
    expect(clampIndex(-2, times.length)).toBe(0);
    expect(clampIndex(99, times.length)).toBe(3);
  });

  it("jumps an event between frames to the following frame", () => {
    const frames = result([0, 0.5, 1], "aeb").frames;
    expect(frameIndexAtOrBefore(frames, 0.75)).toBe(1);
    expect(frameIndexAtOrAfter(frames, 0.75)).toBe(2);
  });

  it("builds a fixed-order evaluation model through the longest result", () => {
    const noAssist = result([0, 0.5, 1], "no_assist");
    const warning = result([0, 0.5, 1.5], "warning_only");
    const aeb = result([0, 0.25, 2], "aeb");
    const model = buildPlaybackModel({
      kind: "evaluation",
      data: {
        schema_version: "1.0",
        baseline_scenario: noAssist.scenario,
        thresholds,
        no_assist: {
          strategy: "no_assist",
          result: noAssist,
          collision_time_s: null,
          final_ego_speed_mps: 10,
          warning_command_duration_s: 0,
          partial_braking_command_duration_s: 0,
          emergency_braking_command_duration_s: 0,
        },
        warning_only: {
          strategy: "warning_only",
          result: warning,
          collision_time_s: null,
          final_ego_speed_mps: 10,
          warning_command_duration_s: 1,
          partial_braking_command_duration_s: 0,
          emergency_braking_command_duration_s: 0,
        },
        aeb: {
          strategy: "aeb",
          result: aeb,
          collision_time_s: null,
          final_ego_speed_mps: 0,
          warning_command_duration_s: 0,
          partial_braking_command_duration_s: 0.5,
          emergency_braking_command_duration_s: 1,
        },
        aeb_avoided_collision: false,
        aeb_collision_time_delta_s: null,
        aeb_minimum_gap_delta_m: 0,
        aeb_final_gap_delta_m: 0,
      },
    });
    expect(model.tracks.map((track) => track.strategy)).toEqual([
      "no_assist",
      "warning_only",
      "aeb",
    ]);
    expect(model.timeline).toEqual([0, 0.25, 0.5, 1, 1.5, 2]);
    expect(model.leadTrack.strategy).toBe("aeb");
  });
});
