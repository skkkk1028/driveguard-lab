import type { DrivingStrategy, RegressionScenario } from "../api/types";
import type {
  FormErrors,
  RunMode,
  ScenarioField,
  ScenarioFormValues,
  ThresholdField,
  ThresholdFormValues,
} from "./form";
import { PRESET_LABELS } from "./form";

interface NumberFieldDefinition<T extends string> {
  name: T;
  label: string;
  unit: string;
  minimum: number;
}

const INITIAL_FIELDS: Array<NumberFieldDefinition<ScenarioField>> = [
  {
    name: "ego_initial_speed_mps",
    label: "自车初始速度",
    unit: "m/s",
    minimum: 0,
  },
  {
    name: "lead_initial_speed_mps",
    label: "前车初始速度",
    unit: "m/s",
    minimum: 0,
  },
  {
    name: "initial_gap_m",
    label: "初始间距",
    unit: "m",
    minimum: 0,
  },
];

const BRAKING_FIELDS: Array<NumberFieldDefinition<ScenarioField>> = [
  {
    name: "lead_brake_start_s",
    label: "前车制动起点",
    unit: "s",
    minimum: 0,
  },
  {
    name: "lead_braking_deceleration_mps2",
    label: "前车制动减速度",
    unit: "m/s²",
    minimum: 0,
  },
];

const SIMULATION_FIELDS: Array<NumberFieldDefinition<ScenarioField>> = [
  {
    name: "ego_reaction_time_s",
    label: "自车反应时间",
    unit: "s",
    minimum: 0,
  },
  {
    name: "ego_max_braking_deceleration_mps2",
    label: "自车最大制动减速度",
    unit: "m/s²",
    minimum: 0,
  },
  {
    name: "simulation_step_s",
    label: "仿真步长",
    unit: "s",
    minimum: 0,
  },
  {
    name: "max_simulation_time_s",
    label: "最大仿真时长",
    unit: "s",
    minimum: 0,
  },
];

const THRESHOLD_FIELDS: Array<NumberFieldDefinition<ThresholdField>> = [
  {
    name: "emergency_ttc_s",
    label: "紧急 TTC 阈值",
    unit: "s",
    minimum: 0,
  },
  {
    name: "danger_ttc_s",
    label: "危险 TTC 阈值",
    unit: "s",
    minimum: 0,
  },
  {
    name: "caution_ttc_s",
    label: "谨慎 TTC 阈值",
    unit: "s",
    minimum: 0,
  },
  {
    name: "danger_thw_s",
    label: "危险 THW 阈值",
    unit: "s",
    minimum: 0,
  },
  {
    name: "caution_thw_s",
    label: "谨慎 THW 阈值",
    unit: "s",
    minimum: 0,
  },
];

const STRATEGY_LABELS: Record<DrivingStrategy, string> = {
  no_assist: "No Assist",
  warning_only: "Warning Only",
  aeb: "AEB",
};

interface ScenarioFormProps {
  mode: RunMode;
  strategy: DrivingStrategy;
  scenarioValues: ScenarioFormValues;
  thresholdValues: ThresholdFormValues;
  customThresholdsEnabled: boolean;
  errors: FormErrors;
  presets: RegressionScenario[];
  selectedPresetId: string;
  presetLoading: boolean;
  presetError: string | null;
  submitting: boolean;
  submitError: string | null;
  onModeChange: (mode: RunMode) => void;
  onStrategyChange: (strategy: DrivingStrategy) => void;
  onScenarioChange: (field: ScenarioField, value: string) => void;
  onThresholdChange: (field: ThresholdField, value: string) => void;
  onThresholdToggle: (enabled: boolean) => void;
  onPresetChange: (scenarioId: string) => void;
  onReset: () => void;
  onSubmit: (event: React.FormEvent<HTMLFormElement>) => void;
}

interface NumericInputProps<T extends ScenarioField | ThresholdField> {
  definition: NumberFieldDefinition<T>;
  value: string;
  error: string | undefined;
  disabled: boolean;
  onChange: (field: T, value: string) => void;
}

function NumericInput<T extends ScenarioField | ThresholdField>({
  definition,
  value,
  error,
  disabled,
  onChange,
}: NumericInputProps<T>) {
  const inputId = `field-${definition.name}`;
  const errorId = `${inputId}-error`;
  return (
    <div className="field-control">
      <label htmlFor={inputId}>{definition.label}</label>
      <div className="number-input-shell">
        <input
          id={inputId}
          name={definition.name}
          type="number"
          inputMode="decimal"
          min={definition.minimum}
          step="any"
          value={value}
          disabled={disabled}
          aria-invalid={Boolean(error)}
          aria-describedby={error ? errorId : undefined}
          onChange={(event) => onChange(definition.name, event.target.value)}
        />
        <span aria-hidden="true">{definition.unit}</span>
      </div>
      {error ? (
        <p className="field-error" id={errorId}>
          {error}
        </p>
      ) : null}
    </div>
  );
}

function PresetPicker({
  presets,
  selectedPresetId,
  loading,
  error,
  disabled,
  onChange,
}: {
  presets: RegressionScenario[];
  selectedPresetId: string;
  loading: boolean;
  error: string | null;
  disabled: boolean;
  onChange: (scenarioId: string) => void;
}) {
  return (
    <div className="preset-panel">
      <div className="preset-copy">
        <label htmlFor="scenario-preset">标准场景预设</label>
        <p>加载预设只替换物理参数，不改变当前策略或运行模式。</p>
      </div>
      <select
        id="scenario-preset"
        value={selectedPresetId}
        disabled={disabled || loading}
        onChange={(event) => onChange(event.target.value)}
      >
        <option value="">自定义参数</option>
        {presets.map((preset) => (
          <option key={preset.scenario_id} value={preset.scenario_id}>
            {PRESET_LABELS[preset.scenario_id] ?? preset.scenario_id}
          </option>
        ))}
      </select>
      {loading ? <p className="inline-status">正在读取标准场景…</p> : null}
      {error ? (
        <p className="inline-warning" role="status">
          {error}
        </p>
      ) : null}
    </div>
  );
}

export function ScenarioForm({
  mode,
  strategy,
  scenarioValues,
  thresholdValues,
  customThresholdsEnabled,
  errors,
  presets,
  selectedPresetId,
  presetLoading,
  presetError,
  submitting,
  submitError,
  onModeChange,
  onStrategyChange,
  onScenarioChange,
  onThresholdChange,
  onThresholdToggle,
  onPresetChange,
  onReset,
  onSubmit,
}: ScenarioFormProps) {
  return (
    <form className="configuration-form" noValidate onSubmit={onSubmit}>
      <section className="form-section" aria-labelledby="workflow-heading">
        <div className="section-heading">
          <span className="section-index">01</span>
          <div>
            <h2 id="workflow-heading">选择研究工作流</h2>
            <p>运行一个指定策略，或在完全相同的物理条件下比较三种策略。</p>
          </div>
        </div>
        <fieldset className="mode-options" disabled={submitting}>
          <legend className="visually-hidden">运行模式</legend>
          <label className={mode === "simulation" ? "mode-card selected" : "mode-card"}>
            <input
              type="radio"
              name="run-mode"
              value="simulation"
              checked={mode === "simulation"}
              onChange={() => onModeChange("simulation")}
            />
            <span>
              <strong>单策略仿真</strong>
              <small>选择 No Assist、Warning Only 或 AEB</small>
            </span>
          </label>
          <label className={mode === "evaluation" ? "mode-card selected" : "mode-card"}>
            <input
              type="radio"
              name="run-mode"
              value="evaluation"
              checked={mode === "evaluation"}
              onChange={() => onModeChange("evaluation")}
            />
            <span>
              <strong>三策略评估</strong>
              <small>按固定顺序比较三种策略，不生成排名</small>
            </span>
          </label>
        </fieldset>

        {mode === "simulation" ? (
          <fieldset className="strategy-options" disabled={submitting}>
            <legend>驾驶策略</legend>
            {Object.entries(STRATEGY_LABELS).map(([value, label]) => (
              <label key={value}>
                <input
                  id={value === "aeb" ? "field-strategy" : undefined}
                  type="radio"
                  name="strategy"
                  value={value}
                  checked={strategy === value}
                  onChange={() => onStrategyChange(value as DrivingStrategy)}
                />
                <span>{label}</span>
              </label>
            ))}
          </fieldset>
        ) : (
          <p className="evaluation-note">
            评估模式固定运行 No Assist → Warning Only → AEB，策略字段不会发送给评估接口。
          </p>
        )}
      </section>

      <section className="form-section" aria-labelledby="scenario-heading">
        <div className="section-heading">
          <span className="section-index">02</span>
          <div>
            <h2 id="scenario-heading">配置前车急刹场景</h2>
            <p>所有物理量使用 SI 单位，表单不会改变后端仿真精度。</p>
          </div>
        </div>

        <PresetPicker
          presets={presets}
          selectedPresetId={selectedPresetId}
          loading={presetLoading}
          error={presetError}
          disabled={submitting}
          onChange={onPresetChange}
        />

        <fieldset className="parameter-group" disabled={submitting}>
          <legend>车辆初始状态</legend>
          <div className="field-grid">
            {INITIAL_FIELDS.map((definition) => (
              <NumericInput
                key={definition.name}
                definition={definition}
                value={scenarioValues[definition.name]}
                error={errors[definition.name]}
                disabled={submitting}
                onChange={onScenarioChange}
              />
            ))}
          </div>
        </fieldset>

        <fieldset className="parameter-group" disabled={submitting}>
          <legend>前车制动</legend>
          <div className="field-grid">
            {BRAKING_FIELDS.map((definition) => (
              <NumericInput
                key={definition.name}
                definition={definition}
                value={scenarioValues[definition.name]}
                error={errors[definition.name]}
                disabled={submitting}
                onChange={onScenarioChange}
              />
            ))}
          </div>
        </fieldset>

        <fieldset className="parameter-group" disabled={submitting}>
          <legend>自车与仿真</legend>
          <div className="field-grid">
            {SIMULATION_FIELDS.map((definition) => (
              <NumericInput
                key={definition.name}
                definition={definition}
                value={scenarioValues[definition.name]}
                error={errors[definition.name]}
                disabled={submitting}
                onChange={onScenarioChange}
              />
            ))}
          </div>
        </fieldset>
      </section>

      <section className="form-section" aria-labelledby="threshold-heading">
        <div className="section-heading compact-heading">
          <span className="section-index">03</span>
          <div>
            <h2 id="threshold-heading">风险阈值</h2>
            <p>默认由后端使用教学仿真阈值；需要研究敏感性时再显式覆盖。</p>
          </div>
        </div>
        <label className="advanced-toggle">
          <input
            type="checkbox"
            checked={customThresholdsEnabled}
            disabled={submitting}
            onChange={(event) => onThresholdToggle(event.target.checked)}
          />
          <span>
            <strong>启用自定义风险阈值</strong>
            <small>开启后必须完整提供五项阈值</small>
          </span>
        </label>
        {customThresholdsEnabled ? (
          <fieldset className="threshold-panel" disabled={submitting}>
            <legend className="visually-hidden">自定义风险阈值</legend>
            <div className="field-grid">
              {THRESHOLD_FIELDS.map((definition) => (
                <NumericInput
                  key={definition.name}
                  definition={definition}
                  value={thresholdValues[definition.name]}
                  error={errors[definition.name]}
                  disabled={submitting}
                  onChange={onThresholdChange}
                />
              ))}
            </div>
          </fieldset>
        ) : null}
      </section>

      {submitError ? (
        <div className="submit-error" role="alert">
          <strong>无法运行</strong>
          <span>{submitError}</span>
        </div>
      ) : null}

      <div className="form-actions">
        <button
          className="secondary-button"
          type="button"
          disabled={submitting}
          onClick={onReset}
        >
          重置默认场景
        </button>
        <button className="primary-button" type="submit" disabled={submitting}>
          {submitting
            ? "正在运行…"
            : mode === "simulation"
              ? "运行单策略仿真"
              : "运行三策略评估"}
        </button>
      </div>
    </form>
  );
}
