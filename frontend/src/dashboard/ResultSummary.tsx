import { useEffect, useRef } from "react";

import type {
  DrivingStrategy,
  SimulationRunResponse,
  StrategyEvaluation,
  StrategyOutcome,
} from "../api/types";

export type DashboardResult =
  | { kind: "simulation"; data: SimulationRunResponse }
  | { kind: "evaluation"; data: StrategyEvaluation };

const STRATEGY_LABELS: Record<DrivingStrategy, string> = {
  no_assist: "No Assist",
  warning_only: "Warning Only",
  aeb: "AEB",
};

function valueWithUnit(value: number | null, unit: string): string {
  return value === null ? "不适用" : `${String(value)} ${unit}`;
}

function collisionLabel(collided: boolean): string {
  return collided ? "发生碰撞" : "未发生碰撞";
}

function SingleSimulationSummary({ data }: { data: SimulationRunResponse }) {
  const { result } = data;
  const { summary } = result;
  const items = [
    ["运行策略", STRATEGY_LABELS[result.scenario.strategy]],
    ["仿真时长", valueWithUnit(summary.duration_s, "s")],
    ["保留帧数", String(result.frames.length)],
    ["最小 Gap", valueWithUnit(summary.minimum_gap_m, "m")],
    ["最终 Gap", valueWithUnit(summary.final_gap_m, "m")],
    ["最小 TTC", valueWithUnit(summary.minimum_ttc_s, "s")],
    ["Warning 首次触发", valueWithUnit(summary.warning_trigger_time_s, "s")],
    ["AEB 首次触发", valueWithUnit(summary.aeb_trigger_time_s, "s")],
  ];
  return (
    <>
      <div className={summary.collided ? "outcome-banner collision" : "outcome-banner clear"}>
        <span className="outcome-dot" aria-hidden="true" />
        <div>
          <span>离散碰撞结果</span>
          <strong>{collisionLabel(summary.collided)}</strong>
        </div>
      </div>
      <dl className="metric-grid">
        {items.map(([label, value]) => (
          <div key={label}>
            <dt>{label}</dt>
            <dd>{value}</dd>
          </div>
        ))}
      </dl>
    </>
  );
}

function outcomeRows(evaluation: StrategyEvaluation): StrategyOutcome[] {
  return [evaluation.no_assist, evaluation.warning_only, evaluation.aeb];
}

function EvaluationSummary({ data }: { data: StrategyEvaluation }) {
  return (
    <>
      <div className="table-scroll">
        <table>
          <caption className="visually-hidden">三策略评估摘要</caption>
          <thead>
            <tr>
              <th scope="col">策略</th>
              <th scope="col">碰撞</th>
              <th scope="col">碰撞时刻</th>
              <th scope="col">最终自车速度</th>
              <th scope="col">最小 Gap</th>
              <th scope="col">最终 Gap</th>
            </tr>
          </thead>
          <tbody>
            {outcomeRows(data).map((outcome) => (
              <tr key={outcome.strategy}>
                <th scope="row">{STRATEGY_LABELS[outcome.strategy]}</th>
                <td>{collisionLabel(outcome.result.summary.collided)}</td>
                <td>{valueWithUnit(outcome.collision_time_s, "s")}</td>
                <td>{valueWithUnit(outcome.final_ego_speed_mps, "m/s")}</td>
                <td>{valueWithUnit(outcome.result.summary.minimum_gap_m, "m")}</td>
                <td>{valueWithUnit(outcome.result.summary.final_gap_m, "m")}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="comparison-panel">
        <div>
          <span>AEB 是否避免基线碰撞</span>
          <strong>{data.aeb_avoided_collision ? "是" : "否"}</strong>
        </div>
        <div>
          <span>碰撞时间差</span>
          <strong>{valueWithUnit(data.aeb_collision_time_delta_s, "s")}</strong>
        </div>
        <div>
          <span>最小 Gap 差值</span>
          <strong>{valueWithUnit(data.aeb_minimum_gap_delta_m, "m")}</strong>
        </div>
        <div>
          <span>最终 Gap 差值</span>
          <strong>{valueWithUnit(data.aeb_final_gap_delta_m, "m")}</strong>
        </div>
      </div>
      <p className="comparison-note">
        差值均为 AEB 减 No Assist，仅描述当前输入下的离散仿真结果，不构成策略排名。
      </p>
    </>
  );
}

export function ResultSummary({ result }: { result: DashboardResult }) {
  const headingRef = useRef<HTMLHeadingElement>(null);
  useEffect(() => {
    headingRef.current?.focus();
  }, [result]);

  return (
    <section className="result-card" aria-labelledby="result-heading">
      <div className="result-heading-row">
        <div>
          <p className="panel-kicker">Run complete</p>
          <h2 id="result-heading" ref={headingRef} tabIndex={-1}>
            {result.kind === "simulation" ? "单策略运行摘要" : "三策略评估摘要"}
          </h2>
        </div>
        <span className="schema-badge">schema 1.0</span>
      </div>
      {result.kind === "simulation" ? (
        <SingleSimulationSummary data={result.data} />
      ) : (
        <EvaluationSummary data={result.data} />
      )}
      <div className="phase-boundary-note">
        完整响应已保留。本阶段不提供逐帧播放、事件时间轴或动态图表。
      </div>
    </section>
  );
}
