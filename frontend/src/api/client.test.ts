import { describe, expect, it, vi } from "vitest";

import type {
  SimulationRequest,
  StrategyEvaluationRequest,
} from "./types";
import { ApiClientError, createApiClient, DEFAULT_API_BASE_URL } from "./client";
import evaluationFixture from "../../../contracts/api-v1/evaluation-boundary.json";
import catalogFixture from "../../../contracts/api-v1/regression-scenarios.json";
import simulationFixture from "../../../contracts/api-v1/simulation-aeb.json";
import simulationLimitErrorFixture from "../../../contracts/api-v1/simulation-limit-error.json";

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
    const fetchMock = vi
      .fn<typeof fetch>()
      .mockResolvedValue(jsonResponse(catalogFixture));
    const client = createApiClient(undefined, fetchMock);

    await expect(client.listRegressionScenarios()).resolves.toEqual(catalogFixture);
    expect(fetchMock).toHaveBeenCalledWith(
      `${DEFAULT_API_BASE_URL}/api/v1/regression-scenarios`,
      expect.objectContaining({ method: "GET" }),
    );
  });

  it("normalizes a custom base URL and posts a simulation request", async () => {
    const fetchMock = vi
      .fn<typeof fetch>()
      .mockResolvedValue(jsonResponse(simulationFixture));
    const client = createApiClient(" https://lab.example/api/ ", fetchMock);

    await expect(client.runSimulation(simulationRequest)).resolves.toBe(
      simulationFixture,
    );
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
    const fetchMock = vi
      .fn<typeof fetch>()
      .mockResolvedValue(jsonResponse(evaluationFixture));
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

    await expect(client.evaluateStrategies(request)).resolves.toBe(
      evaluationFixture,
    );
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
      jsonResponse(simulationLimitErrorFixture, 422),
    );
    const client = createApiClient(undefined, fetchMock);

    const error = await client.runSimulation(simulationRequest).catch((reason) => reason);
    expect(error).toBeInstanceOf(ApiClientError);
    expect(error).toMatchObject({
      code: "simulation_limit_exceeded",
      status: 422,
      details: [
        expect.objectContaining({ error_type: "simulation_limit_exceeded" }),
      ],
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

  it("preserves request cancellation instead of normalizing it", async () => {
    const abort = new DOMException("cancelled", "AbortError");
    const fetchMock = vi.fn<typeof fetch>().mockRejectedValue(abort);

    await expect(
      createApiClient(undefined, fetchMock).listRegressionScenarios(),
    ).rejects.toBe(abort);
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

  it.each([
    ["schema version", (value: typeof simulationFixture) => {
      value.result.schema_version = "2.0";
    }],
    ["request strategy", (value: typeof simulationFixture) => {
      value.result.scenario.strategy = "no_assist";
    }],
    ["risk enum", (value: typeof simulationFixture) => {
      value.result.frames[0].metrics.risk_level = "unknown";
    }],
    ["finite number", (value: typeof simulationFixture) => {
      value.result.frames[0].metrics.gap_m = Number.POSITIVE_INFINITY;
    }],
    ["required nested field", (value: typeof simulationFixture) => {
      delete (value.result.summary as Partial<typeof value.result.summary>).duration_s;
    }],
    ["frame ordering", (value: typeof simulationFixture) => {
      value.result.frames[1].time_s = 0;
    }],
    ["completion event", (value: typeof simulationFixture) => {
      value.result.events = value.result.events.filter(
        (event) => event.event_type !== "simulation_completed",
      );
    }],
    ["completion time", (value: typeof simulationFixture) => {
      const completion = value.result.events.find(
        (event) => event.event_type === "simulation_completed",
      );
      if (completion) {
        completion.time_s = 4.5;
      }
    }],
  ])("rejects a successful response with an invalid %s", async (_name, mutate) => {
    const malformed = structuredClone(simulationFixture);
    mutate(malformed);
    const fetchMock = vi
      .fn<typeof fetch>()
      .mockResolvedValue(jsonResponse(malformed));

    const error = await createApiClient(undefined, fetchMock)
      .runSimulation(simulationRequest)
      .catch((reason: unknown) => reason);

    expect(error).toBeInstanceOf(ApiClientError);
    expect(error).toMatchObject({
      code: "response_contract_error",
      status: 200,
      details: [],
    });
  });

  it("rejects endpoint-specific catalog and evaluation contract drift", async () => {
    const malformedCatalog = structuredClone(catalogFixture);
    malformedCatalog[0].baseline_scenario.strategy = "aeb";
    const malformedEvaluation = structuredClone(evaluationFixture);
    malformedEvaluation.aeb.strategy = "warning_only";

    await expect(
      createApiClient(
        undefined,
        vi.fn<typeof fetch>().mockResolvedValue(jsonResponse(malformedCatalog)),
      ).listRegressionScenarios(),
    ).rejects.toMatchObject({ code: "response_contract_error", status: 200 });
    await expect(
      createApiClient(
        undefined,
        vi.fn<typeof fetch>().mockResolvedValue(jsonResponse(malformedEvaluation)),
      ).evaluateStrategies({ baseline_scenario: simulationRequest.scenario }),
    ).rejects.toMatchObject({ code: "response_contract_error", status: 200 });
  });

  it("accepts additive response fields and never includes raw payload values in errors", async () => {
    const extended = structuredClone(simulationFixture);
    (extended.result as typeof extended.result & { future_field?: string }).future_field =
      "future-compatible";
    const acceptedClient = createApiClient(
      undefined,
      vi.fn<typeof fetch>().mockResolvedValue(jsonResponse(extended)),
    );
    await expect(acceptedClient.runSimulation(simulationRequest)).resolves.toBe(
      extended,
    );

    const malformed = structuredClone(simulationFixture);
    malformed.result.schema_version = "secret-response-value";
    const error = await createApiClient(
      undefined,
      vi.fn<typeof fetch>().mockResolvedValue(jsonResponse(malformed)),
    )
      .runSimulation(simulationRequest)
      .catch((reason: unknown) => reason);
    expect(error).toBeInstanceOf(ApiClientError);
    expect(String(error)).not.toContain("secret-response-value");
  });
});
