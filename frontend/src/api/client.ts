import type {
  ApiErrorDetail,
  ApiErrorResponse,
  RegressionScenario,
  SimulationRequest,
  SimulationRunResponse,
  StrategyEvaluation,
  StrategyEvaluationRequest,
} from "./types";

export const DEFAULT_API_BASE_URL = "http://127.0.0.1:8000";

export class ApiClientError extends Error {
  readonly code: string;
  readonly details: ApiErrorDetail[];
  readonly status: number | null;

  constructor(
    message: string,
    options: {
      code: string;
      details?: ApiErrorDetail[];
      status?: number | null;
    },
  ) {
    super(message);
    this.name = "ApiClientError";
    this.code = options.code;
    this.details = options.details ?? [];
    this.status = options.status ?? null;
  }
}

export interface DriveGuardApiClient {
  listRegressionScenarios(signal?: AbortSignal): Promise<RegressionScenario[]>;
  runSimulation(
    request: SimulationRequest,
    signal?: AbortSignal,
  ): Promise<SimulationRunResponse>;
  evaluateStrategies(
    request: StrategyEvaluationRequest,
    signal?: AbortSignal,
  ): Promise<StrategyEvaluation>;
}

function normalizeBaseUrl(value: string | undefined): string {
  const trimmed = value?.trim().replace(/\/+$/, "");
  return trimmed || DEFAULT_API_BASE_URL;
}

function isApiErrorResponse(value: unknown): value is ApiErrorResponse {
  if (typeof value !== "object" || value === null || !("error" in value)) {
    return false;
  }
  const error = value.error;
  if (
    typeof error === "object" &&
    error !== null &&
    "code" in error &&
    typeof error.code === "string" &&
    "message" in error &&
    typeof error.message === "string" &&
    "details" in error &&
    Array.isArray(error.details)
  ) {
    return (error.details as unknown[]).every(
      (detail: unknown) =>
        typeof detail === "object" &&
        detail !== null &&
        "location" in detail &&
        Array.isArray(detail.location) &&
        detail.location.every(
          (part: unknown) =>
            typeof part === "string" || typeof part === "number",
        ) &&
        "message" in detail &&
        typeof detail.message === "string" &&
        "error_type" in detail &&
        typeof detail.error_type === "string",
    );
  }
  return false;
}

export function createApiClient(
  baseUrl = import.meta.env.VITE_API_BASE_URL,
  fetchImplementation: typeof fetch = fetch,
): DriveGuardApiClient {
  const normalizedBaseUrl = normalizeBaseUrl(baseUrl);

  async function request<T>(
    path: string,
    init: RequestInit,
  ): Promise<T> {
    let response: Response;
    try {
      response = await fetchImplementation(`${normalizedBaseUrl}${path}`, init);
    } catch (error) {
      if (error instanceof DOMException && error.name === "AbortError") {
        throw error;
      }
      throw new ApiClientError("无法连接仿真 API，请确认后端服务已经启动。", {
        code: "network_error",
      });
    }

    let payload: unknown;
    try {
      payload = await response.json();
    } catch {
      payload = null;
    }

    if (!response.ok) {
      if (isApiErrorResponse(payload)) {
        throw new ApiClientError(payload.error.message, {
          code: payload.error.code,
          details: payload.error.details,
          status: response.status,
        });
      }
      throw new ApiClientError(`仿真 API 请求失败（HTTP ${response.status}）。`, {
        code: "http_error",
        status: response.status,
      });
    }

    return payload as T;
  }

  return {
    listRegressionScenarios(signal) {
      return request<RegressionScenario[]>("/api/v1/regression-scenarios", {
        method: "GET",
        signal,
      });
    },
    runSimulation(simulationRequest, signal) {
      return request<SimulationRunResponse>("/api/v1/simulations", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(simulationRequest),
        signal,
      });
    },
    evaluateStrategies(evaluationRequest, signal) {
      return request<StrategyEvaluation>("/api/v1/evaluations", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(evaluationRequest),
        signal,
      });
    },
  };
}
