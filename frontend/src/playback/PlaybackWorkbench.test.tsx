import { fireEvent, render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import type {
  ControlAction,
  DrivingStrategy,
  RiskLevel,
  SimulationFrame,
  SimulationResult,
  StrategyOutcome,
} from "../api/types";
import type { DashboardResult } from "../dashboard/result";
import { PlaybackWorkbench } from "./PlaybackWorkbench";

const thresholds = {
  emergency_ttc_s: 1,
  danger_ttc_s: 2,
  caution_ttc_s: 4,
  danger_thw_s: 1,
  caution_thw_s: 2,
};

function frame(
  time: number,
  risk: RiskLevel = "safe",
  action: ControlAction = "none",
): SimulationFrame {
  return {
    time_s: time,
    ego: { position_m: time * 10, speed_mps: 10 - time, acceleration_mps2: 0 },
    lead: { position_m: 15 + time * 8, speed_mps: 8, acceleration_mps2: -5 },
    metrics: {
      gap_m: 15 - time * 2,
      relative_speed_mps: 2 - time,
      ttc_s: time === 0 ? null : 3 - time,
      thw_s: 1.5 - time / 10,
      ego_stopping_distance_m: 6.25 - time,
      risk_level: risk,
    },
    control_action: action,
  };
}

function simulationResult(
  strategy: DrivingStrategy,
  frames: SimulationFrame[],
  collided = false,
): SimulationResult {
  return {
    schema_version: "1.0",
    scenario: {
      ego_initial_speed_mps: 10,
      lead_initial_speed_mps: 8,
      initial_gap_m: 15,
      lead_brake_start_s: 0.75,
      lead_braking_deceleration_mps2: 5,
      ego_reaction_time_s: 0,
      ego_max_braking_deceleration_mps2: 8,
      simulation_step_s: 0.5,
      max_simulation_time_s: 2,
      strategy,
    },
    frames,
    events: [
      { time_s: 0.75, event_type: "lead_braking_started", message: "Lead braking started." },
      ...(collided
        ? [{ time_s: frames.at(-1)?.time_s ?? 0, event_type: "collision" as const, message: "Collision." }]
        : []),
    ],
    summary: {
      duration_s: frames.at(-1)?.time_s ?? 0,
      collided,
      minimum_gap_m: collided ? -1 : 5,
      minimum_ttc_s: collided ? 0 : 1,
      final_gap_m: collided ? -1 : 5,
      warning_trigger_time_s: null,
      aeb_trigger_time_s: strategy === "aeb" ? 0.5 : null,
    },
  };
}

function singleResult(frames?: SimulationFrame[], collided = false): DashboardResult {
  return {
    kind: "simulation",
    data: {
      thresholds,
      result: simulationResult(
        "aeb",
        frames ?? [
          frame(0),
          frame(0.5, "danger", "partial_braking"),
          frame(1, "emergency", "emergency_braking"),
        ],
        collided,
      ),
    },
  };
}

function outcome(strategy: DrivingStrategy, result: SimulationResult): StrategyOutcome {
  return {
    strategy,
    result,
    collision_time_s: result.summary.collided ? result.summary.duration_s : null,
    final_ego_speed_mps: result.frames.at(-1)?.ego.speed_mps ?? 0,
    warning_command_duration_s: 0,
    partial_braking_command_duration_s: 0,
    emergency_braking_command_duration_s: 0,
  };
}

function evaluationResult(): DashboardResult {
  const noAssist = simulationResult("no_assist", [frame(0), frame(1)], true);
  const warning = simulationResult("warning_only", [frame(0), frame(0.5), frame(1.5)]);
  const aeb = simulationResult("aeb", [frame(0), frame(2)]);
  return {
    kind: "evaluation",
    data: {
      schema_version: "1.0",
      baseline_scenario: noAssist.scenario,
      thresholds,
      no_assist: outcome("no_assist", noAssist),
      warning_only: outcome("warning_only", warning),
      aeb: outcome("aeb", aeb),
      aeb_avoided_collision: true,
      aeb_collision_time_delta_s: null,
      aeb_minimum_gap_delta_m: 1,
      aeb_final_gap_delta_m: 2,
    },
  };
}

describe("PlaybackWorkbench", () => {
  it("starts at the first retained frame and supports frame and scrub controls", () => {
    render(<PlaybackWorkbench result={singleResult()} />);
    expect(screen.getByRole("heading", { name: "仿真逐帧播放与结果可视化" })).toHaveFocus();
    expect(screen.getByText("t = 0 s")).toBeInTheDocument();
    expect(screen.getByText("Safe")).toBeInTheDocument();
    expect(screen.getByText("None")).toBeInTheDocument();
    expect(screen.getByText(/绝对 position_m/)).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "后一帧" }));
    expect(screen.getByText("t = 0.5 s")).toBeInTheDocument();
    expect(screen.getByText("Danger")).toBeInTheDocument();
    expect(screen.getByText("Partial Braking")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "跳到末帧" }));
    expect(screen.getByText("t = 1 s")).toBeInTheDocument();
    fireEvent.change(screen.getByRole("slider"), { target: { value: "0" } });
    expect(screen.getByText("t = 0 s")).toBeInTheDocument();
  });

  it("moves both vehicles against one fixed ground-coordinate scale", () => {
    render(<PlaybackWorkbench result={singleResult()} />);
    const road = screen.getByRole("img", { name: /固定地面坐标/ });
    const ego = road.querySelector<HTMLElement>(".ego-vehicle");
    const lead = road.querySelector<HTMLElement>(".lead-vehicle");
    expect(ego).not.toBeNull();
    expect(lead).not.toBeNull();
    const initialEgoLeft = ego?.style.left;
    const initialLeadLeft = lead?.style.left;

    fireEvent.click(screen.getByRole("button", { name: "后一帧" }));

    expect(ego?.style.left).not.toBe(initialEgoLeft);
    expect(lead?.style.left).not.toBe(initialLeadLeft);
    expect(screen.getByText("自车 · 5 m")).toBeInTheDocument();
    expect(screen.getByText("前车 · 19 m")).toBeInTheDocument();
  });

  it("keeps illustrative vehicle bodies separated while point-vehicle gap is positive", () => {
    const closeFrame = frame(1);
    closeFrame.ego.position_m = 23.84;
    closeFrame.lead.position_m = 25;
    closeFrame.metrics.gap_m = 1.16;
    render(<PlaybackWorkbench result={singleResult([frame(0), closeFrame])} />);
    fireEvent.click(screen.getByRole("button", { name: "跳到末帧" }));

    const road = screen.getByRole("img", { name: /间距 1.16 米/ });
    const ego = road.querySelector<HTMLElement>(".ego-vehicle");
    const lead = road.querySelector<HTMLElement>(".lead-vehicle");
    expect(Number.parseFloat(ego?.style.left ?? "NaN")).toBeLessThan(
      Number.parseFloat(lead?.style.left ?? "NaN"),
    );
    expect(ego).toHaveStyle({ transform: "translate(-100%, -50%)" });
    expect(lead).toHaveStyle({ transform: "translate(0, -50%)" });
    expect(screen.getByText(/Gap > 0 时分离/)).toBeInTheDocument();
  });

  it("jumps a between-frame event to the following retained frame", () => {
    render(<PlaybackWorkbench result={singleResult()} />);
    fireEvent.click(screen.getByRole("button", { name: "跳到 0.75 秒的前车制动开始" }));
    expect(screen.getByText("t = 1 s")).toBeInTheDocument();
  });

  it("uses a chart click to jump to the nearest shared time", () => {
    render(<PlaybackWorkbench result={singleResult()} />);
    const chart = screen.getByRole("img", { name: /自车与前车速度/ });
    Object.defineProperty(chart, "getBoundingClientRect", {
      value: () => ({ left: 0, width: 760, top: 0, height: 250, right: 760, bottom: 250, x: 0, y: 0, toJSON: () => ({}) }),
    });
    fireEvent.click(chart, { clientX: 400 });
    expect(screen.getByText("t = 0.5 s")).toBeInTheDocument();
  });

  it("places coincident TTC and THW threshold labels on opposite chart sides", () => {
    render(<PlaybackWorkbench result={singleResult()} />);
    const chart = screen.getByRole("img", { name: /TTC 与 THW/ });
    const emergencyTtc = within(chart).getByText("Emergency TTC");
    const dangerThw = within(chart).getByText("Danger THW");
    const dangerTtc = within(chart).getByText("Danger TTC");
    const cautionThw = within(chart).getByText("Caution THW");

    expect(emergencyTtc).toHaveAttribute("text-anchor", "end");
    expect(dangerTtc).toHaveAttribute("text-anchor", "end");
    expect(dangerThw).toHaveAttribute("text-anchor", "start");
    expect(cautionThw).toHaveAttribute("text-anchor", "start");
    expect(emergencyTtc).toHaveAttribute("y", dangerThw.getAttribute("y"));
    expect(dangerTtc).toHaveAttribute("y", cautionThw.getAttribute("y"));
    expect(emergencyTtc.getAttribute("x")).not.toBe(dangerThw.getAttribute("x"));
    expect(dangerTtc.getAttribute("x")).not.toBe(cautionThw.getAttribute("x"));
  });

  it("supports a single-frame result and marks a collision result terminated", () => {
    const { rerender } = render(<PlaybackWorkbench result={singleResult([frame(0)])} />);
    fireEvent.click(screen.getByRole("button", { name: "开始播放" }));
    expect(screen.getByText("帧 1 / 1")).toBeInTheDocument();
    expect(screen.getByText("已终止")).toBeInTheDocument();

    rerender(<PlaybackWorkbench result={singleResult(undefined, true)} />);
    fireEvent.click(screen.getByRole("button", { name: "跳到末帧" }));
    expect(screen.getByText("已终止")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "跳到 1 秒的碰撞" })).toBeInTheDocument();
  });

  it("uses a shared evaluation timeline, overlays strategies and holds an early final frame", () => {
    render(<PlaybackWorkbench result={evaluationResult()} />);
    const speedChart = screen.getByRole("img", { name: /自车与前车速度/ });
    expect(speedChart.querySelectorAll(".chart-line")).toHaveLength(4);
    expect(screen.getByRole("button", { name: "AEB" })).toHaveAttribute("aria-pressed", "true");

    fireEvent.click(screen.getByRole("button", { name: "跳到末帧" }));
    expect(screen.getByText("共享时间").nextElementSibling).toHaveTextContent("2 s");
    fireEvent.click(screen.getByRole("button", { name: "No Assist" }));
    expect(screen.getByRole("button", { name: "No Assist" })).toHaveAttribute("aria-pressed", "true");
    expect(screen.getByText("t = 1 s")).toBeInTheDocument();
    expect(screen.getByText("已终止")).toBeInTheDocument();
    expect(within(screen.getByLabelText("播放控制")).getByRole("button", { name: "开始播放" })).toBeInTheDocument();
  });
});
