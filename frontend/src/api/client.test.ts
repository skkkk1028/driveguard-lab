import { describe, expect, it, vi } from "vitest";

import type {
  RegressionScenario,
  SimulationRequest,
  SimulationRunResponse,
  StrategyEvaluation,
  StrategyEvaluationRequest,
} from "./types";
import { ApiClientError, createApiClient, DEFAULT_API_BASE_URL } from "./client";

function jsonResponse(body: unknown, status = 200): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: vi.fn().mockResolvedValue(body),
  } as unknown as Response;
}

const simulationRequest: SimulationRequest = {
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
    strategy: "aeb",
  },
};

describe("DriveGuard API client", () => {
  it("uses the default API URL and lists regression scenarios", async () => {
    const catalog: RegressionScenario[] = [];
    const fetchMock = vi.fn<typeof fetch>().mockResolvedValue(jsonResponse(catalog));
    const client = createApiClient(undefined, fetchMock);

    await expect(client.listRegressionScenarios()).resolves.toEqual(catalog);
    expect(fetchMock).toHaveBeenCalledWith(
      `${DEFAULT_API_BASE_URL}/api/v1/regression-scenarios`,
      expect.objectContaining({ method: "GET" }),
    );
  });

  it("normalizes a custom base URL and posts a simulation request", async () => {
    const response = { thresholds: {}, result: {} } as SimulationRunResponse;
    const fetchMock = vi.fn<typeof fetch>().mockResolvedValue(jsonResponse(response));
    const client = createApiClient(" https://lab.example/api/ ", fetchMock);

    await expect(client.runSimulation(simulationRequest)).resolves.toBe(response);
    expect(fetchMock).toHaveBeenCalledWith(
      "https://lab.example/api/api/v1/simulations",
      expect.objectContaining({
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(simulationRequest),
      }),
    );
  });

  it("posts evaluation input without adding a strategy", async () => {
    const response = {} as StrategyEvaluation;
    const fetchMock = vi.fn<typeof fetch>().mockResolvedValue(jsonResponse(response));
    const client = createApiClient("http://localhost:9000", fetchMock);
    const request: StrategyEvaluationRequest = {
      baseline_scenario: {
        ...simulationRequest.scenario,
      },
      risk_thresholds: {
        emergency_ttc_s: 1,
        danger_ttc_s: 2,
        caution_ttc_s: 4,
        danger_thw_s: 1,
        caution_thw_s: 2,
      },
    };
    delete (request.baseline_scenario as Partial<typeof request.baseline_scenario> & {
      strategy?: string;
    }).strategy;

    await expect(client.evaluateStrategies(request)).resolves.toBe(response);
    const init = fetchMock.mock.calls[0][1];
    expect(fetchMock.mock.calls[0][0]).toBe(
      "http://localhost:9000/api/v1/evaluations",
    );
    expect(JSON.parse(String(init?.body))).toEqual(request);
    expect(JSON.parse(String(init?.body)).baseline_scenario).not.toHaveProperty(
      "strategy",
    );
  });

  it("exposes the stable API error code, status, and details", async () => {
    const fetchMock = vi.fn<typeof fetch>().mockResolvedValue(
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
    const client = createApiClient(undefined, fetchMock);

    const error = await client.runSimulation(simulationRequest).catch((reason) => reason);
    expect(error).toBeInstanceOf(ApiClientError);
    expect(error).toMatchObject({
      code: "validation_error",
      status: 422,
      details: [expect.objectContaining({ error_type: "greater_than" })],
    });
  });

  it("normalizes network and non-JSON HTTP failures", async () => {
    const networkFetch = vi.fn<typeof fetch>().mockRejectedValue(new TypeError("offline"));
    const httpFetch = vi.fn<typeof fetch>().mockResolvedValue({
      ok: false,
      status: 503,
      json: vi.fn().mockRejectedValue(new SyntaxError("not json")),
    } as unknown as Response);

    await expect(
      createApiClient(undefined, networkFetch).listRegressionScenarios(),
    ).rejects.toMatchObject({ code: "network_error", status: null });
    await expect(
      createApiClient(undefined, httpFetch).listRegressionScenarios(),
    ).rejects.toMatchObject({ code: "http_error", status: 503 });
  });

  it("treats a malformed error detail list as a generic HTTP failure", async () => {
    const fetchMock = vi.fn<typeof fetch>().mockResolvedValue(
      jsonResponse(
        {
          error: {
            code: "validation_error",
            message: "Request validation failed.",
            details: [{ message: "missing location" }],
          },
        },
        422,
      ),
    );

    await expect(
      createApiClient(undefined, fetchMock).runSimulation(simulationRequest),
    ).rejects.toMatchObject({ code: "http_error", status: 422, details: [] });
  });
});
