import type {
  DrivingStrategy,
  RiskThresholds,
  SimulationFrame,
  SimulationResult,
} from "../api/types";
import type { DashboardResult } from "../dashboard/result";

export const STRATEGY_ORDER: readonly DrivingStrategy[] = [
  "no_assist",
  "warning_only",
  "aeb",
];

export const STRATEGY_LABELS: Record<DrivingStrategy, string> = {
  no_assist: "No Assist",
  warning_only: "Warning Only",
  aeb: "AEB",
};

export interface PlaybackTrack {
  strategy: DrivingStrategy;
  result: SimulationResult;
}

export interface PlaybackModel {
  isEvaluation: boolean;
  tracks: PlaybackTrack[];
  timeline: number[];
  thresholds: RiskThresholds;
  leadTrack: PlaybackTrack;
}

export function sortedUniqueTimeline(results: readonly SimulationResult[]): number[] {
  return [...new Set(results.flatMap((result) => result.frames.map((frame) => frame.time_s)))].sort(
    (left, right) => left - right,
  );
}

export function indexAtOrBefore(values: readonly number[], target: number): number {
  if (values.length === 0) {
    return -1;
  }
  let low = 0;
  let high = values.length;
  while (low < high) {
    const middle = Math.floor((low + high) / 2);
    if (values[middle] <= target) {
      low = middle + 1;
    } else {
      high = middle;
    }
  }
  return Math.max(0, low - 1);
}

export function indexAtOrAfter(values: readonly number[], target: number): number {
  if (values.length === 0) {
    return -1;
  }
  let low = 0;
  let high = values.length;
  while (low < high) {
    const middle = Math.floor((low + high) / 2);
    if (values[middle] < target) {
      low = middle + 1;
    } else {
      high = middle;
    }
  }
  return Math.min(low, values.length - 1);
}

export function nearestIndex(values: readonly number[], target: number): number {
  const after = indexAtOrAfter(values, target);
  if (after <= 0) {
    return Math.max(after, 0);
  }
  const before = after - 1;
  return target - values[before] <= values[after] - target ? before : after;
}

export function clampIndex(index: number, length: number): number {
  return Math.min(Math.max(index, 0), Math.max(length - 1, 0));
}

export function frameIndexAtOrBefore(
  frames: readonly SimulationFrame[],
  time: number,
): number {
  if (frames.length === 0) {
    return -1;
  }
  let low = 0;
  let high = frames.length;
  while (low < high) {
    const middle = Math.floor((low + high) / 2);
    if (frames[middle].time_s <= time) {
      low = middle + 1;
    } else {
      high = middle;
    }
  }
  return Math.max(0, low - 1);
}

export function frameIndexAtOrAfter(
  frames: readonly SimulationFrame[],
  time: number,
): number {
  if (frames.length === 0) {
    return -1;
  }
  let low = 0;
  let high = frames.length;
  while (low < high) {
    const middle = Math.floor((low + high) / 2);
    if (frames[middle].time_s < time) {
      low = middle + 1;
    } else {
      high = middle;
    }
  }
  return Math.min(low, frames.length - 1);
}

export function buildPlaybackModel(result: DashboardResult): PlaybackModel {
  const tracks: PlaybackTrack[] =
    result.kind === "simulation"
      ? [
          {
            strategy: result.data.result.scenario.strategy,
            result: result.data.result,
          },
        ]
      : STRATEGY_ORDER.map((strategy) => ({
          strategy,
          result: result.data[strategy].result,
        }));
  const leadTrack = tracks.reduce((longest, track) => {
    const longestEnd = longest.result.frames.at(-1)?.time_s ?? 0;
    const trackEnd = track.result.frames.at(-1)?.time_s ?? 0;
    return trackEnd > longestEnd ? track : longest;
  });
  return {
    isEvaluation: result.kind === "evaluation",
    tracks,
    timeline: sortedUniqueTimeline(tracks.map((track) => track.result)),
    thresholds: result.data.thresholds,
    leadTrack,
  };
}

export function trackForStrategy(
  model: PlaybackModel,
  strategy: DrivingStrategy,
): PlaybackTrack {
  return model.tracks.find((track) => track.strategy === strategy) ?? model.tracks[0];
}
