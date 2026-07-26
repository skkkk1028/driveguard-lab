import { StrictMode } from "react";

import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type {
  LeadVehicleBrakingScenario,
  SimulationResult,
  SimulationRunResponse,
} from "./api/types";
import App from "./App";
import evaluationFixture from "../../contracts/api-v1/evaluation-boundary.json";
import catalogFixture from "../../contracts/api-v1/regression-scenarios.json";
import simulationFixture from "../../contracts/api-v1/simulation-aeb.json";

function jsonResponse(body: unknown, status = 200): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: vi.fn().mockResolvedValue(body),
  } as unknown as Response;
}

const baseScenario: LeadVehicleBrakingScenario = {
  ego_initial_speed_mps: 10,
  lead_initial_speed_mps: 10,
  initial_gap_m: 15,
  lead_brake_start_s: 0,
  lead_braking_deceleration_mps2: 5,
  ego_reaction_time_s: 0,
  ego_max_braking_deceleration_mps2: 8,
  simulation_step_s: 0.5,
  max_simulation_time_s: 5,
  strategy: "no_assist",
};

const catalog = catalogFixture;

function simulationResult(
  strategy: LeadVehicleBrakingScenario["strategy"],
  collided = false,
): SimulationResult {
  const scenario = { ...baseScenario, strategy };
  return {
    schema_version: "1.0",
    scenario,
    frames: [
      {
        time_s: 0,
        ego: { position_m: 0, speed_mps: 10, acceleration_mps2: 0 },
        lead: { position_m: 15, speed_mps: 10, acceleration_mps2: -5 },
        metrics: {
          gap_m: 15,
          relative_speed_mps: 0,
          ttc_s: null,
          thw_s: 1.5,
          ego_stopping_distance_m: 6.25,
          risk_level: "safe",
        },
        control_action: "none",
      },
    ],
    events: [
      {
        time_s: 0,
        event_type: "simulation_completed",
        message: "Simulation completed at 0 seconds.",
      },
    ],
    summary: {
      duration_s: 0,
      collided,
      minimum_gap_m: collided ? -1 : 4,
      minimum_ttc_s: collided ? 0 : 1.5,
      final_gap_m: collided ? -1 : 4,
      warning_trigger_time_s: strategy === "warning_only" ? 2 : null,
      aeb_trigger_time_s: strategy === "aeb" ? 1.5 : null,
    },
  };
}

function simulationResponse(): SimulationRunResponse {
  return {
    thresholds: {
      emergency_ttc_s: 1,
      danger_ttc_s: 2,
      caution_ttc_s: 4,
      danger_thw_s: 1,
      caution_thw_s: 2,
    },
    result: simulationResult("aeb"),
  };
}

describe("Dashboard configuration workflow", () => {
  let fetchMock: ReturnType<typeof vi.fn<typeof fetch>>;

  beforeEach(() => {
    fetchMock = vi.fn<typeof fetch>();
    fetchMock.mockResolvedValueOnce(jsonResponse(catalog));
    vi.stubGlobal("fetch", fetchMock);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("loads the default regression preset and renders the safety boundary", async () => {
    render(<App />);

    expect(
      screen.getByRole("heading", { name: "危险场景仿真实验台" }),
    ).toBeInTheDocument();
    expect(screen.getByText("DriveGuard Lab · v1.0")).toBeInTheDocument();
    expect(await screen.findByRole("option", { name: "AEB 避免碰撞" })).toBeInTheDocument();
    expect(screen.getByLabelText("标准场景预设")).toHaveValue(
      "aeb_avoids_collision",
    );
    expect(screen.getByLabelText("自车初始速度")).toHaveValue(10);
    expect(screen.getByRole("radio", { name: "AEB" })).toBeChecked();
    expect(screen.getByText(/不得使用本项目控制真实车辆/)).toBeInTheDocument();
  });

  it("loads another preset without changing the selected strategy", async () => {
    render(<App />);
    await screen.findByRole("option", { name: "AEB 无法避免碰撞" });
    fireEvent.click(screen.getByRole("radio", { name: "Warning Only" }));

    fireEvent.change(screen.getByLabelText("标准场景预设"), {
      target: { value: "aeb_unavoidable_collision" },
    });

    expect(screen.getByLabelText("自车初始速度")).toHaveValue(20);
    expect(screen.getByRole("radio", { name: "Warning Only" })).toBeChecked();
  });

  it("runs one strategy without threshold overrides and shows its summary", async () => {
    fetchMock.mockResolvedValueOnce(jsonResponse(simulationFixture));
    render(<App />);
    await screen.findByRole("option", { name: "AEB 避免碰撞" });

    fireEvent.click(screen.getByRole("button", { name: "运行单策略仿真" }));

    expect(await screen.findByRole("heading", { name: "单策略运行摘要" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "仿真逐帧播放与结果可视化" })).toBeInTheDocument();
    expect(screen.getByText("未发生碰撞")).toBeInTheDocument();
    const request = JSON.parse(String(fetchMock.mock.calls[1][1]?.body));
    expect(fetchMock.mock.calls[1][0]).toBe(
      "http://127.0.0.1:8000/api/v1/simulations",
    );
    expect(request.scenario.strategy).toBe("aeb");
    expect(request).not.toHaveProperty("risk_thresholds");
  });

  it("sends all custom thresholds when the advanced setting is enabled", async () => {
    fetchMock.mockResolvedValueOnce(jsonResponse(simulationResponse()));
    render(<App />);
    await screen.findByRole("option", { name: "AEB 避免碰撞" });
    fireEvent.click(screen.getByRole("checkbox", { name: /启用自定义风险阈值/ }));

    fireEvent.click(screen.getByRole("button", { name: "运行单策略仿真" }));

    await screen.findByRole("heading", { name: "单策略运行摘要" });
    expect(JSON.parse(String(fetchMock.mock.calls[1][1]?.body)).risk_thresholds).toEqual({
      emergency_ttc_s: 1,
      danger_ttc_s: 2,
      caution_ttc_s: 4,
      danger_thw_s: 1,
      caution_thw_s: 2,
    });
  });

  it("runs evaluation without a strategy field and renders all outcomes", async () => {
    fetchMock.mockResolvedValueOnce(jsonResponse(evaluationFixture));
    render(<App />);
    await screen.findByRole("option", { name: "AEB 避免碰撞" });
    fireEvent.click(screen.getByRole("radio", { name: /三策略评估/ }));

    fireEvent.click(screen.getByRole("button", { name: "运行三策略评估" }));

    expect(await screen.findByRole("heading", { name: "三策略评估摘要" })).toBeInTheDocument();
    expect(screen.getByRole("table")).toBeInTheDocument();
    const request = JSON.parse(String(fetchMock.mock.calls[1][1]?.body));
    expect(fetchMock.mock.calls[1][0]).toBe(
      "http://127.0.0.1:8000/api/v1/evaluations",
    );
    expect(request.baseline_scenario).not.toHaveProperty("strategy");
    expect(screen.getByText(/差值均为 AEB 减 No Assist/)).toBeInTheDocument();
  });

  it("blocks invalid form submission and focuses the first invalid field", async () => {
    render(<App />);
    await screen.findByRole("option", { name: "AEB 避免碰撞" });
    const gapInput = screen.getByLabelText("初始间距");
    fireEvent.change(gapInput, { target: { value: "" } });

    fireEvent.click(screen.getByRole("button", { name: "运行单策略仿真" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(/请修正表单/);
    expect(screen.getByText("请输入数值。")).toBeInTheDocument();
    await waitFor(() => expect(gapInput).toHaveFocus());
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it("maps a backend field error into the form", async () => {
    fetchMock.mockResolvedValueOnce(
      jsonResponse(
        {
          error: {
            code: "validation_error",
            message: "Request validation failed.",
            details: [
              {
                location: ["body", "scenario", "initial_gap_m"],
                message: "Input should be greater than 0",
                error_type: "greater_than",
              },
            ],
          },
        },
        422,
      ),
    );
    render(<App />);
    await screen.findByRole("option", { name: "AEB 避免碰撞" });

    fireEvent.click(screen.getByRole("button", { name: "运行单策略仿真" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(/后端校验/);
    expect(screen.getByText("该字段未通过后端校验。")).toBeInTheDocument();
    expect(screen.getByLabelText("初始间距")).toHaveAttribute("aria-invalid", "true");
  });

  it("keeps manual configuration usable when preset loading fails", async () => {
    vi.unstubAllGlobals();
    fetchMock = vi.fn<typeof fetch>();
    fetchMock.mockRejectedValueOnce(new TypeError("offline"));
    fetchMock.mockResolvedValueOnce(jsonResponse(simulationResponse()));
    vi.stubGlobal("fetch", fetchMock);
    render(<App />);

    expect(await screen.findByText(/标准场景暂时无法读取/)).toBeInTheDocument();
    expect(screen.getByLabelText("系统状态")).toHaveTextContent(
      "Simulation API unavailable",
    );
    expect(screen.getByLabelText("自车初始速度")).toHaveValue(10);
    fireEvent.click(screen.getByRole("button", { name: "运行单策略仿真" }));
    expect(await screen.findByRole("heading", { name: "单策略运行摘要" })).toBeInTheDocument();
  });

  it("prevents duplicate submission while a request is pending and resets defaults", async () => {
    let resolveRun: ((response: Response) => void) | undefined;
    fetchMock.mockImplementationOnce(
      () =>
        new Promise<Response>((resolve) => {
          resolveRun = resolve;
        }),
    );
    render(<App />);
    await screen.findByRole("option", { name: "AEB 避免碰撞" });
    fireEvent.change(screen.getByLabelText("初始间距"), { target: { value: "22" } });
    const runButton = screen.getByRole("button", { name: "运行单策略仿真" });

    fireEvent.click(runButton);
    expect(screen.getByRole("button", { name: "正在运行…" })).toBeDisabled();
    fireEvent.click(screen.getByRole("button", { name: "正在运行…" }));
    expect(fetchMock).toHaveBeenCalledTimes(2);
    resolveRun?.(jsonResponse(simulationResponse()));
    await screen.findByRole("heading", { name: "单策略运行摘要" });

    fireEvent.click(screen.getByRole("button", { name: "重置默认场景" }));
    expect(screen.getByLabelText("初始间距")).toHaveValue(15);
    expect(screen.getByText("结果摘要将在这里出现")).toBeInTheDocument();
  });

  it("does not let a late preset response overwrite manual edits", async () => {
    let resolveCatalog: ((response: Response) => void) | undefined;
    vi.unstubAllGlobals();
    fetchMock = vi.fn<typeof fetch>();
    fetchMock.mockImplementationOnce(
      () =>
        new Promise<Response>((resolve) => {
          resolveCatalog = resolve;
        }),
    );
    vi.stubGlobal("fetch", fetchMock);
    render(<App />);
    const speedInput = screen.getByLabelText("自车初始速度");
    fireEvent.change(speedInput, { target: { value: "12" } });

    resolveCatalog?.(jsonResponse(catalog));

    await screen.findByRole("option", { name: "AEB 避免碰撞" });
    expect(speedInput).toHaveValue(12);
    expect(screen.getByLabelText("标准场景预设")).toHaveValue("");
  });

  it("clears a completed summary after a configuration change", async () => {
    fetchMock.mockResolvedValueOnce(jsonResponse(simulationResponse()));
    render(<App />);
    await screen.findByRole("option", { name: "AEB 避免碰撞" });
    fireEvent.click(screen.getByRole("button", { name: "运行单策略仿真" }));
    await screen.findByRole("heading", { name: "单策略运行摘要" });

    fireEvent.change(screen.getByLabelText("初始间距"), { target: { value: "16" } });

    expect(screen.queryByRole("heading", { name: "单策略运行摘要" })).not.toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "仿真逐帧播放与结果可视化" })).not.toBeInTheDocument();
    expect(screen.getByText("结果摘要将在这里出现")).toBeInTheDocument();
  });

  it("rejects incompatible success data without retaining the previous result", async () => {
    const incompatible = {
      ...simulationResponse(),
      result: {
        ...simulationResponse().result,
        schema_version: "2.0",
      },
    };
    fetchMock
      .mockResolvedValueOnce(jsonResponse(simulationResponse()))
      .mockResolvedValueOnce(jsonResponse(incompatible));
    render(<App />);
    await screen.findByRole("option", { name: "AEB 避免碰撞" });

    fireEvent.click(screen.getByRole("button", { name: "运行单策略仿真" }));
    await screen.findByRole("heading", { name: "单策略运行摘要" });
    fireEvent.click(screen.getByRole("button", { name: "运行单策略仿真" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      /API 返回了不兼容的数据/,
    );
    expect(
      screen.queryByRole("heading", { name: "单策略运行摘要" }),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("heading", { name: "仿真逐帧播放与结果可视化" }),
    ).not.toBeInTheDocument();
  });

  it("resets a newly completed playback to the first frame", async () => {
    const replayResponse = simulationResponse();
    replayResponse.result.frames.push({
      ...replayResponse.result.frames[0],
      time_s: 0.5,
      ego: { ...replayResponse.result.frames[0].ego, position_m: 5 },
      lead: { ...replayResponse.result.frames[0].lead, position_m: 19 },
      metrics: { ...replayResponse.result.frames[0].metrics, gap_m: 14 },
    });
    replayResponse.result.events[0].time_s = 0.5;
    replayResponse.result.summary.duration_s = 0.5;
    fetchMock
      .mockResolvedValueOnce(jsonResponse(replayResponse))
      .mockResolvedValueOnce(jsonResponse(replayResponse));
    render(<App />);
    await screen.findByRole("option", { name: "AEB 避免碰撞" });
    fireEvent.click(screen.getByRole("button", { name: "运行单策略仿真" }));
    await screen.findByRole("heading", { name: "仿真逐帧播放与结果可视化" });
    fireEvent.click(screen.getByRole("button", { name: "跳到末帧" }));
    expect(screen.getByText("t = 0.5 s")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "运行单策略仿真" }));

    await screen.findByRole("heading", { name: "仿真逐帧播放与结果可视化" });
    expect(screen.getByText("t = 0 s")).toBeInTheDocument();
  });

  it("loads presets correctly under the development StrictMode effect cycle", async () => {
    fetchMock.mockReset();
    fetchMock.mockResolvedValue(jsonResponse(catalog));
    render(
      <StrictMode>
        <App />
      </StrictMode>,
    );

    await screen.findByRole("option", { name: "AEB 避免碰撞" });
    expect(screen.getByLabelText("标准场景预设")).toHaveValue(
      "aeb_avoids_collision",
    );
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });
});
