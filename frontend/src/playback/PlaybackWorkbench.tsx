import { useEffect, useMemo, useRef, useState } from "react";

import type {
  ControlAction,
  DrivingStrategy,
  RiskLevel,
  SimulationEvent,
  SimulationFrame,
} from "../api/types";
import type { DashboardResult } from "../dashboard/result";
import { categoricalBandPaths, linearScale } from "./chart";
import { MetricChart, type ChartSeries, type ReferenceLine } from "./MetricChart";
import {
  buildPlaybackModel,
  frameIndexAtOrAfter,
  frameIndexAtOrBefore,
  indexAtOrAfter,
  STRATEGY_LABELS,
  trackForStrategy,
} from "./model";
import { PLAYBACK_SPEEDS, usePlayback } from "./usePlayback";
import "./playback.css";

const RISK_LABELS: Record<RiskLevel, string> = {
  safe: "Safe",
  caution: "Caution",
  danger: "Danger",
  emergency: "Emergency",
};

const ACTION_LABELS: Record<ControlAction, string> = {
  none: "None",
  warning: "Warning",
  partial_braking: "Partial Braking",
  emergency_braking: "Emergency Braking",
};

const EVENT_LABELS: Record<SimulationEvent["event_type"], string> = {
  lead_braking_started: "前车制动开始",
  risk_level_changed: "风险等级变化",
  warning_triggered: "Warning 触发",
  partial_braking_triggered: "部分制动触发",
  emergency_braking_triggered: "紧急制动触发",
  collision: "碰撞",
  simulation_completed: "仿真完成",
};

const STRATEGY_COLORS: Record<DrivingStrategy, string> = {
  no_assist: "#708487",
  warning_only: "#d18a36",
  aeb: "#087f75",
};

function value(value: number | null, unit: string): string {
  return value === null ? "不适用" : `${String(value)} ${unit}`;
}

function points(
  frames: readonly SimulationFrame[],
  selector: (frame: SimulationFrame) => number | null,
) {
  return frames.map((frame) => ({ time: frame.time_s, value: selector(frame) }));
}

function RoadScene({ frame }: { frame: SimulationFrame }) {
  const leadOffset = Math.tanh(frame.metrics.gap_m / 20) * 52;
  return (
    <section className="road-panel" aria-labelledby="road-heading">
      <div className="panel-title-row">
        <div>
          <p className="panel-kicker">Point-vehicle scene</p>
          <h3 id="road-heading">道路位置示意</h3>
        </div>
        <span>Gap {value(frame.metrics.gap_m, "m")}</span>
      </div>
      <div className="road-scene" role="img" aria-label={`自车固定参考，前车间距 ${String(frame.metrics.gap_m)} 米`}>
        <div className="road-markings" aria-hidden="true" />
        <div className="scene-vehicle ego-vehicle" style={{ left: "28%" }}>
          <span>自车</span>
          <i />
        </div>
        <div className="scene-vehicle lead-vehicle" style={{ left: `calc(28% + ${String(leadOffset)}%)` }}>
          <span>前车</span>
          <i />
        </div>
      </div>
      <p className="scene-note">车辆外形仅为位置示意；碰撞仍按点车辆帧状态 gap_m ≤ 0 判定。</p>
    </section>
  );
}

function CurrentFramePanel({
  frame,
  frameIndex,
  frameCount,
  terminated,
}: {
  frame: SimulationFrame;
  frameIndex: number;
  frameCount: number;
  terminated: boolean;
}) {
  const metrics = [
    ["自车位置", value(frame.ego.position_m, "m")],
    ["自车速度", value(frame.ego.speed_mps, "m/s")],
    ["自车加速度", value(frame.ego.acceleration_mps2, "m/s²")],
    ["前车位置", value(frame.lead.position_m, "m")],
    ["前车速度", value(frame.lead.speed_mps, "m/s")],
    ["前车加速度", value(frame.lead.acceleration_mps2, "m/s²")],
    ["Gap", value(frame.metrics.gap_m, "m")],
    ["相对速度", value(frame.metrics.relative_speed_mps, "m/s")],
    ["TTC", value(frame.metrics.ttc_s, "s")],
    ["THW", value(frame.metrics.thw_s, "s")],
    ["理论停车距离", value(frame.metrics.ego_stopping_distance_m, "m")],
  ];
  return (
    <section className="frame-panel" aria-labelledby="frame-heading">
      <div className="panel-title-row">
        <div>
          <p className="panel-kicker">Retained frame</p>
          <h3 id="frame-heading">当前帧详情</h3>
        </div>
        {terminated ? <strong className="terminated-badge">已终止</strong> : null}
      </div>
      <div className="frame-status-row">
        <span>t = {value(frame.time_s, "s")}</span>
        <span>帧 {String(frameIndex + 1)} / {String(frameCount)}</span>
        <span className={`risk-chip risk-${frame.metrics.risk_level}`}>{RISK_LABELS[frame.metrics.risk_level]}</span>
        <span className={`action-chip action-${frame.control_action}`}>{ACTION_LABELS[frame.control_action]}</span>
      </div>
      <dl className="frame-metrics">
        {metrics.map(([label, metricValue]) => (
          <div key={label}>
            <dt>{label}</dt>
            <dd>{metricValue}</dd>
          </div>
        ))}
      </dl>
    </section>
  );
}

function ClassificationBands({
  frames,
  duration,
  currentTime,
}: {
  frames: readonly SimulationFrame[];
  duration: number;
  currentTime: number;
}) {
  const paths = useMemo(() => {
    const effectiveDuration = duration === 0 ? 1 : duration;
    const x = linearScale(0, effectiveDuration, 0, 1000);
    const segments = frames.map((frame, index) => ({
      start: frame.time_s,
      end: frames[index + 1]?.time_s ?? frame.time_s,
      risk: frame.metrics.risk_level,
      action: frame.control_action,
    }));
    return {
      x,
      risk: categoricalBandPaths(
        segments.map((segment) => ({ ...segment, category: segment.risk })),
        ["safe", "caution", "danger", "emergency"] as const,
        x,
        8,
        24,
      ),
      action: categoricalBandPaths(
        segments.map((segment) => ({ ...segment, category: segment.action })),
        ["none", "warning", "partial_braking", "emergency_braking"] as const,
        x,
        48,
        24,
      ),
    };
  }, [duration, frames]);
  return (
    <section className="classification-panel" aria-labelledby="classification-heading">
      <div className="panel-title-row">
        <div>
          <p className="panel-kicker">Categorical state</p>
          <h3 id="classification-heading">风险与控制动作带</h3>
        </div>
      </div>
      <svg viewBox="0 0 1000 82" role="img" aria-label="风险等级和控制动作随时间变化">
        <title>上带表示风险等级，下带表示控制动作；竖线表示当前时间。</title>
        {Object.entries(paths.risk).map(([category, path]) => (
          <path key={category} className={`band risk-${category}`} d={path} />
        ))}
        {Object.entries(paths.action).map(([category, path]) => (
          <path key={category} className={`band action-${category}`} d={path} />
        ))}
        <line className="band-cursor" x1={paths.x(currentTime)} x2={paths.x(currentTime)} y1={3} y2={77} />
      </svg>
      <div className="band-legends">
        <span><b>风险</b> Safe / Caution / Danger / Emergency</span>
        <span><b>动作</b> None / Warning / Partial / Emergency Braking</span>
      </div>
    </section>
  );
}

export function PlaybackWorkbench({ result }: { result: DashboardResult }) {
  const headingRef = useRef<HTMLHeadingElement>(null);
  const model = useMemo(() => buildPlaybackModel(result), [result]);
  const [activeStrategy, setActiveStrategy] = useState<DrivingStrategy>(
    result.kind === "simulation" ? result.data.result.scenario.strategy : "aeb",
  );
  const playback = usePlayback(model.timeline);
  const activeTrack = trackForStrategy(model, activeStrategy);
  const activeFrameIndex = frameIndexAtOrBefore(activeTrack.result.frames, playback.time);
  const activeFrame = activeTrack.result.frames[Math.max(activeFrameIndex, 0)];
  const activeEnd = activeTrack.result.frames.at(-1)?.time_s ?? 0;
  const duration = model.timeline.at(-1) ?? 0;
  const terminated = playback.time >= activeEnd;

  useEffect(() => {
    headingRef.current?.focus();
  }, [result]);

  const speedSeries = useMemo<ChartSeries[]>(() => {
    const egoSeries = model.tracks.map((track) => ({
      id: `${track.strategy}-ego-speed`,
      label: `${STRATEGY_LABELS[track.strategy]} 自车`,
      color: STRATEGY_COLORS[track.strategy],
      emphasized: track.strategy === activeStrategy,
      points: points(track.result.frames, (frame) => frame.ego.speed_mps),
    }));
    return [
      ...egoSeries,
      {
        id: "shared-lead-speed",
        label: "前车（最长轨迹）",
        color: "#684aa8",
        dashed: true,
        emphasized: false,
        points: points(model.leadTrack.result.frames, (frame) => frame.lead.speed_mps),
      },
    ];
  }, [activeStrategy, model.leadTrack.result.frames, model.tracks]);

  const gapSeries = useMemo<ChartSeries[]>(() => [
    ...model.tracks.map((track) => ({
      id: `${track.strategy}-gap`,
      label: `${STRATEGY_LABELS[track.strategy]} Gap`,
      color: STRATEGY_COLORS[track.strategy],
      emphasized: track.strategy === activeStrategy,
      points: points(track.result.frames, (frame) => frame.metrics.gap_m),
    })),
    {
      id: "active-stopping-distance",
      label: `${STRATEGY_LABELS[activeStrategy]} 自车理论停车距离`,
      color: "#b35c82",
      dashed: true,
      emphasized: false,
      points: points(activeTrack.result.frames, (frame) => frame.metrics.ego_stopping_distance_m),
    },
  ], [activeStrategy, activeTrack.result.frames, model.tracks]);

  const riskSeries = useMemo<ChartSeries[]>(() => [
    {
      id: "ttc",
      label: "TTC",
      color: "#087f75",
      emphasized: true,
      points: points(activeTrack.result.frames, (frame) => frame.metrics.ttc_s),
    },
    {
      id: "thw",
      label: "THW",
      color: "#d18a36",
      dashed: true,
      emphasized: false,
      points: points(activeTrack.result.frames, (frame) => frame.metrics.thw_s),
    },
  ], [activeTrack.result.frames]);

  const riskReferences = useMemo<ReferenceLine[]>(() => [
    { id: "emergency-ttc", label: "Emergency TTC", value: model.thresholds.emergency_ttc_s, color: "#a83d35" },
    { id: "danger-ttc", label: "Danger TTC", value: model.thresholds.danger_ttc_s, color: "#c1663c" },
    { id: "caution-ttc", label: "Caution TTC", value: model.thresholds.caution_ttc_s, color: "#cf9e36" },
    { id: "danger-thw", label: "Danger THW", value: model.thresholds.danger_thw_s, color: "#7856a8" },
    { id: "caution-thw", label: "Caution THW", value: model.thresholds.caution_thw_s, color: "#536ea8" },
  ], [model.thresholds]);

  function chooseStrategy(strategy: DrivingStrategy) {
    playback.pause();
    setActiveStrategy(strategy);
  }

  function jumpToEvent(event: SimulationEvent) {
    const frameIndex = frameIndexAtOrAfter(activeTrack.result.frames, event.time_s);
    const targetTime = activeTrack.result.frames[Math.max(frameIndex, 0)]?.time_s ?? 0;
    playback.seekIndex(indexAtOrAfter(model.timeline, targetTime));
  }

  if (!activeFrame) {
    return null;
  }

  return (
    <section className="playback-workbench" aria-labelledby="playback-heading">
      <header className="workbench-header">
        <div>
          <p className="panel-kicker">Stage 13 · Simulation playback</p>
          <h2 id="playback-heading" ref={headingRef} tabIndex={-1}>仿真逐帧播放与结果可视化</h2>
          <p>游标只选择 API 返回的真实保留帧，不插值车辆状态或碰撞时刻。</p>
        </div>
        <div className="workbench-clock" aria-live="polite">
          <span>共享时间</span>
          <strong>{value(playback.time, "s")}</strong>
        </div>
      </header>

      {model.isEvaluation ? (
        <fieldset className="playback-strategies">
          <legend>当前检查策略</legend>
          {model.tracks.map((track) => (
            <button
              type="button"
              key={track.strategy}
              className={activeStrategy === track.strategy ? "selected" : ""}
              aria-pressed={activeStrategy === track.strategy}
              onClick={() => chooseStrategy(track.strategy)}
            >
              {STRATEGY_LABELS[track.strategy]}
            </button>
          ))}
        </fieldset>
      ) : null}

      <div className="playback-controls" aria-label="播放控制">
        <button type="button" onClick={playback.first} aria-label="跳到首帧">|◀</button>
        <button type="button" onClick={playback.previous} aria-label="前一帧">◀</button>
        <button
          type="button"
          className="play-button"
          onClick={playback.playing ? playback.pause : playback.play}
          aria-label={playback.playing ? "暂停播放" : "开始播放"}
        >
          {playback.playing ? "暂停" : "播放"}
        </button>
        <button type="button" onClick={playback.next} aria-label="后一帧">▶</button>
        <button type="button" onClick={playback.last} aria-label="跳到末帧">▶|</button>
        <label className="time-scrubber">
          <span>时间拖动：{value(playback.time, "s")}</span>
          <input
            type="range"
            min={0}
            max={Math.max(model.timeline.length - 1, 0)}
            step={1}
            value={playback.index}
            aria-label={`仿真时间，当前 ${String(playback.time)} 秒`}
            onChange={(event) => playback.seekIndex(Number(event.target.value))}
          />
        </label>
        <label className="speed-control">
          <span>播放速度</span>
          <select
            value={playback.speed}
            aria-label="播放速度"
            onChange={(event) => playback.setSpeed(Number(event.target.value) as (typeof PLAYBACK_SPEEDS)[number])}
          >
            {PLAYBACK_SPEEDS.map((speed) => <option key={speed} value={speed}>{String(speed)}×</option>)}
          </select>
        </label>
      </div>

      <div className="inspection-grid">
        <RoadScene frame={activeFrame} />
        <CurrentFramePanel
          frame={activeFrame}
          frameIndex={activeFrameIndex}
          frameCount={activeTrack.result.frames.length}
          terminated={terminated}
        />
      </div>

      <ClassificationBands frames={activeTrack.result.frames} duration={duration} currentTime={playback.time} />

      <section className="charts-panel" aria-labelledby="charts-heading">
        <div className="panel-title-row">
          <div>
            <p className="panel-kicker">Linked SVG plots</p>
            <h3 id="charts-heading">联动曲线</h3>
          </div>
          <span>点击任一图表跳到最近保留时刻</span>
        </div>
        <div className="charts-grid">
          <MetricChart
            title="自车与前车速度"
            unit="m/s"
            summary="展示自车策略速度与最长结果的前车速度轨迹。"
            duration={duration}
            currentTime={playback.time}
            series={speedSeries}
            onSeek={playback.seekNearestTime}
          />
          <MetricChart
            title="Gap 与自车理论停车距离"
            unit="m"
            summary="展示策略间距及当前策略的理论停车距离。"
            duration={duration}
            currentTime={playback.time}
            series={gapSeries}
            onSeek={playback.seekNearestTime}
          />
          <MetricChart
            title="TTC 与 THW"
            unit="s"
            summary="空值形成断线；参考线为本次运行实际使用的五项阈值。"
            duration={duration}
            currentTime={playback.time}
            series={riskSeries}
            references={riskReferences}
            onSeek={playback.seekNearestTime}
          />
        </div>
      </section>

      <section className="events-panel" aria-labelledby="events-heading">
        <div className="panel-title-row">
          <div>
            <p className="panel-kicker">Discrete events</p>
            <h3 id="events-heading">{STRATEGY_LABELS[activeStrategy]} 事件</h3>
          </div>
          <span>{String(activeTrack.result.events.length)} 项</span>
        </div>
        {activeTrack.result.events.length === 0 ? (
          <p className="empty-events">本结果没有事件。</p>
        ) : (
          <ol className="event-list">
            {activeTrack.result.events.map((event, index) => (
              <li key={`${event.event_type}-${String(event.time_s)}-${String(index)}`}>
                <button type="button" onClick={() => jumpToEvent(event)} aria-label={`跳到 ${String(event.time_s)} 秒的${EVENT_LABELS[event.event_type]}`}>
                  <time>{value(event.time_s, "s")}</time>
                  <strong>{EVENT_LABELS[event.event_type]}</strong>
                  <span>{event.message}</span>
                </button>
              </li>
            ))}
          </ol>
        )}
      </section>
    </section>
  );
}
