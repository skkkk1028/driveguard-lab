import { useEffect, useMemo, useRef, useState } from "react";

import { ApiClientError, createApiClient } from "./api/client";
import type {
  DrivingStrategy,
  RegressionScenario,
  SimulationRequest,
  StrategyEvaluationRequest,
} from "./api/types";
import "./App.css";
import {
  DEFAULT_PRESET_ID,
  DEFAULT_SCENARIO_VALUES,
  DEFAULT_STRATEGY,
  DEFAULT_THRESHOLD_VALUES,
  type FormErrorKey,
  type FormErrors,
  type RunMode,
  type ScenarioField,
  type ScenarioFormValues,
  scenarioValuesFromPreset,
  type ThresholdField,
  type ThresholdFormValues,
  validateForm,
} from "./dashboard/form";
import { ResultSummary } from "./dashboard/ResultSummary";
import type { DashboardResult } from "./dashboard/result";
import { ScenarioForm } from "./dashboard/ScenarioForm";
import { PlaybackWorkbench } from "./playback/PlaybackWorkbench";

const FORM_ERROR_KEYS = new Set<FormErrorKey>([
  ...Object.keys(DEFAULT_SCENARIO_VALUES),
  ...Object.keys(DEFAULT_THRESHOLD_VALUES),
  "strategy",
] as FormErrorKey[]);

function mappedApiErrors(error: ApiClientError): FormErrors {
  const mapped: FormErrors = {};
  for (const detail of error.details) {
    const field = [...detail.location]
      .reverse()
      .find((part): part is FormErrorKey =>
        typeof part === "string" && FORM_ERROR_KEYS.has(part as FormErrorKey),
      );
    if (field) {
      mapped[field] = "该字段未通过后端校验。";
    }
  }
  return mapped;
}

function apiErrorMessage(error: unknown): string {
  if (!(error instanceof ApiClientError)) {
    return "运行过程中发生未知错误，请稍后重试。";
  }
  if (error.code === "simulation_limit_exceeded") {
    return "仿真规模超过每个策略 10,000 个推进区间的限制。";
  }
  if (error.code === "validation_error") {
    return "请求参数未通过后端校验，请检查标记的字段。";
  }
  return error.message;
}

function App() {
  const api = useMemo(() => createApiClient(), []);
  const [mode, setMode] = useState<RunMode>("simulation");
  const [strategy, setStrategy] = useState<DrivingStrategy>(DEFAULT_STRATEGY);
  const [scenarioValues, setScenarioValues] = useState<ScenarioFormValues>({
    ...DEFAULT_SCENARIO_VALUES,
  });
  const [thresholdValues, setThresholdValues] = useState<ThresholdFormValues>({
    ...DEFAULT_THRESHOLD_VALUES,
  });
  const [customThresholdsEnabled, setCustomThresholdsEnabled] = useState(false);
  const [errors, setErrors] = useState<FormErrors>({});
  const [presets, setPresets] = useState<RegressionScenario[]>([]);
  const [selectedPresetId, setSelectedPresetId] = useState("");
  const [presetLoading, setPresetLoading] = useState(true);
  const [presetError, setPresetError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [result, setResult] = useState<DashboardResult | null>(null);
  const [resultRevision, setResultRevision] = useState(0);
  const scenarioEditedRef = useRef(false);
  const activeRunRef = useRef<AbortController | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    let active = true;
    void api
      .listRegressionScenarios(controller.signal)
      .then((loadedPresets) => {
        if (!active) {
          return;
        }
        setPresets(loadedPresets);
        const defaultPreset = loadedPresets.find(
          (preset) => preset.scenario_id === DEFAULT_PRESET_ID,
        );
        if (defaultPreset && !scenarioEditedRef.current) {
          setScenarioValues(scenarioValuesFromPreset(defaultPreset));
          setSelectedPresetId(defaultPreset.scenario_id);
        }
      })
      .catch((error: unknown) => {
        if (!active) {
          return;
        }
        if (error instanceof DOMException && error.name === "AbortError") {
          return;
        }
        setPresetError("标准场景暂时无法读取；仍可使用当前默认参数或手工配置。");
      })
      .finally(() => {
        if (active) {
          setPresetLoading(false);
        }
      });
    return () => {
      active = false;
      controller.abort();
    };
  }, [api]);

  useEffect(
    () => () => {
      activeRunRef.current?.abort();
    },
    [],
  );

  function clearPreviousRun() {
    setResult(null);
    setSubmitError(null);
  }

  function clearFieldError(field: FormErrorKey) {
    setErrors((current) => {
      if (!(field in current)) {
        return current;
      }
      const next = { ...current };
      delete next[field];
      return next;
    });
  }

  function handleModeChange(nextMode: RunMode) {
    setMode(nextMode);
    clearPreviousRun();
  }

  function handleStrategyChange(nextStrategy: DrivingStrategy) {
    setStrategy(nextStrategy);
    clearFieldError("strategy");
    clearPreviousRun();
  }

  function handleScenarioChange(field: ScenarioField, value: string) {
    scenarioEditedRef.current = true;
    setScenarioValues((current) => ({ ...current, [field]: value }));
    setSelectedPresetId("");
    clearFieldError(field);
    clearPreviousRun();
  }

  function handleThresholdChange(field: ThresholdField, value: string) {
    setThresholdValues((current) => ({ ...current, [field]: value }));
    clearFieldError(field);
    clearPreviousRun();
  }

  function handleThresholdToggle(enabled: boolean) {
    setCustomThresholdsEnabled(enabled);
    if (!enabled) {
      setErrors((current) => {
        const next = { ...current };
        for (const field of Object.keys(DEFAULT_THRESHOLD_VALUES) as ThresholdField[]) {
          delete next[field];
        }
        return next;
      });
    }
    clearPreviousRun();
  }

  function handlePresetChange(scenarioId: string) {
    setSelectedPresetId(scenarioId);
    const preset = presets.find((item) => item.scenario_id === scenarioId);
    if (preset) {
      setScenarioValues(scenarioValuesFromPreset(preset));
      scenarioEditedRef.current = false;
      setErrors({});
    }
    clearPreviousRun();
  }

  function handleReset() {
    const defaultPreset = presets.find(
      (preset) => preset.scenario_id === DEFAULT_PRESET_ID,
    );
    setMode("simulation");
    setStrategy(DEFAULT_STRATEGY);
    setScenarioValues(
      defaultPreset
        ? scenarioValuesFromPreset(defaultPreset)
        : { ...DEFAULT_SCENARIO_VALUES },
    );
    setSelectedPresetId(defaultPreset?.scenario_id ?? "");
    setThresholdValues({ ...DEFAULT_THRESHOLD_VALUES });
    setCustomThresholdsEnabled(false);
    setErrors({});
    scenarioEditedRef.current = false;
    clearPreviousRun();
  }

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (submitting) {
      return;
    }
    const validation = validateForm(
      scenarioValues,
      thresholdValues,
      customThresholdsEnabled,
    );
    if (!validation.valid) {
      setErrors(validation.errors);
      setSubmitError("请修正表单中标记的配置后再运行。");
      const firstField = Object.keys(validation.errors)[0];
      if (firstField) {
        window.setTimeout(() => {
          document.getElementById(`field-${firstField}`)?.focus();
        });
      }
      return;
    }

    setErrors({});
    setSubmitError(null);
    setResult(null);
    setSubmitting(true);
    const controller = new AbortController();
    activeRunRef.current = controller;
    try {
      if (mode === "simulation") {
        const request: SimulationRequest = {
          scenario: { ...validation.data.scenario, strategy },
          ...(validation.data.thresholds
            ? { risk_thresholds: validation.data.thresholds }
            : {}),
        };
        const response = await api.runSimulation(request, controller.signal);
        setResult({ kind: "simulation", data: response });
        setResultRevision((current) => current + 1);
      } else {
        const request: StrategyEvaluationRequest = {
          baseline_scenario: validation.data.scenario,
          ...(validation.data.thresholds
            ? { risk_thresholds: validation.data.thresholds }
            : {}),
        };
        const response = await api.evaluateStrategies(request, controller.signal);
        setResult({ kind: "evaluation", data: response });
        setResultRevision((current) => current + 1);
      }
    } catch (error) {
      if (error instanceof DOMException && error.name === "AbortError") {
        return;
      }
      if (error instanceof ApiClientError) {
        setErrors(mappedApiErrors(error));
      }
      setSubmitError(apiErrorMessage(error));
    } finally {
      if (activeRunRef.current === controller) {
        activeRunRef.current = null;
        setSubmitting(false);
      }
    }
  }

  return (
    <main className="dashboard-shell">
      <header className="site-header">
        <div className="brand-lockup">
          <span className="brand-mark" aria-hidden="true">
            DG
          </span>
          <div>
            <p className="eyebrow">DriveGuard Research Platform</p>
            <h1>危险场景仿真实验台</h1>
          </div>
        </div>
        <div
          className={presetError ? "system-status unavailable" : "system-status"}
          aria-label="系统状态"
        >
          <span aria-hidden="true" />
          {presetLoading
            ? "Checking simulation API"
            : presetError
              ? "Simulation API unavailable"
              : "Simulation API connected"}
        </div>
      </header>

      <section className="intro-panel" aria-labelledby="intro-heading">
        <div>
          <p className="panel-kicker">Stage 15 · Integration hardened</p>
          <h2 id="intro-heading">配置一次可重复的前车急刹实验</h2>
          <p>
            使用同一组物理参数研究 No Assist、Warning Only 与基线 AEB。
            所有结果来自确定性一维点车辆模型。
          </p>
        </div>
        <dl className="model-facts">
          <div>
            <dt>模型</dt>
            <dd>1D point vehicle</dd>
          </div>
          <div>
            <dt>单位</dt>
            <dd>SI</dd>
          </div>
          <div>
            <dt>输出</dt>
            <dd>schema 1.0</dd>
          </div>
        </dl>
      </section>

      <div className="dashboard-grid">
        <section className="configuration-card" aria-label="仿真配置">
          <ScenarioForm
            mode={mode}
            strategy={strategy}
            scenarioValues={scenarioValues}
            thresholdValues={thresholdValues}
            customThresholdsEnabled={customThresholdsEnabled}
            errors={errors}
            presets={presets}
            selectedPresetId={selectedPresetId}
            presetLoading={presetLoading}
            presetError={presetError}
            submitting={submitting}
            submitError={submitError}
            onModeChange={handleModeChange}
            onStrategyChange={handleStrategyChange}
            onScenarioChange={handleScenarioChange}
            onThresholdChange={handleThresholdChange}
            onThresholdToggle={handleThresholdToggle}
            onPresetChange={handlePresetChange}
            onReset={handleReset}
            onSubmit={handleSubmit}
          />
        </section>

        <aside className="results-column" aria-label="仿真结果">
          {result ? (
            <ResultSummary result={result} />
          ) : (
            <section className="empty-result-card" aria-labelledby="empty-result-heading">
              <div className="empty-result-icon" aria-hidden="true">
                <span />
              </div>
              <p className="panel-kicker">Awaiting run</p>
              <h2 id="empty-result-heading">结果摘要将在这里出现</h2>
              <p>
                完成场景配置并运行后，可查看碰撞、Gap、TTC 与策略触发摘要。
                完整响应会在下方展开逐帧播放、事件跳转与联动曲线。
              </p>
            </section>
          )}

          <aside className="safety-notice" aria-labelledby="safety-heading">
            <span className="notice-label">Safety boundary</span>
            <h2 id="safety-heading">仅限教学仿真研究</h2>
            <p>
              默认阈值和 AEB 策略不是行业标定或安全保证。不得使用本项目控制真实车辆。
            </p>
          </aside>
        </aside>
      </div>
      {result ? <PlaybackWorkbench key={resultRevision} result={result} /> : null}
    </main>
  );
}

export default App;
