import type { SimulationRunResponse, StrategyEvaluation } from "../api/types";

export type DashboardResult =
  | { kind: "simulation"; data: SimulationRunResponse }
  | { kind: "evaluation"; data: StrategyEvaluation };
