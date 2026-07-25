# DriveGuard Lab Data Contracts

This document defines the stable domain data exchanged by future DriveGuard Lab
simulation components. Stage 2 defines representation and validation only: it does
not implement vehicle motion, risk formulas, collision detection, or driving
strategy behavior.

## Units and naming

All internal physical values use SI units.

| Quantity | Internal unit | Field suffix |
| --- | --- | --- |
| Time | second | `_s` |
| Distance and position | meter | `_m` |
| Speed | meter per second | `_mps` |
| Acceleration | meter per second squared | `_mps2` |

`VehicleState.acceleration_mps2` is signed: positive means acceleration, zero
means constant speed, and negative means deceleration or braking. In contrast,
`lead_braking_deceleration_mps2` and
`ego_max_braking_deceleration_mps2` are positive magnitudes. For example, `8.0`
represents a braking deceleration magnitude of `8.0 m/s²`; callers do not provide
`-8.0`.

The relative-speed direction for future risk calculations is fixed as:

```text
relative_speed_mps = ego_speed_mps - lead_speed_mps
```

A positive value means the ego vehicle is closing on the lead vehicle, zero means
equal speeds, and a negative value means the gap is increasing. This stage records
the convention but does not calculate relative speed.

When TTC or THW is not applicable, its value is `None`, which becomes JSON `null`.
NaN, positive infinity, negative infinity, sentinel magnitudes, and `-1` must not
represent unavailable metrics. No JSON-compatible domain output may contain NaN
or infinity.

## Stable enumerations

Enum values are public serialized data and are independent of display text.

| Enum | Stable values |
| --- | --- |
| `DrivingStrategy` | `no_assist`, `warning_only`, `aeb` |
| `RiskLevel` | `safe`, `caution`, `danger`, `emergency` |
| `ControlAction` | `none`, `warning`, `partial_braking`, `emergency_braking` |
| `SimulationEventType` | `lead_braking_started`, `risk_level_changed`, `warning_triggered`, `partial_braking_triggered`, `emergency_braking_triggered`, `collision`, `simulation_completed` |

The presence of strategy and action values does not mean their behavior or any
decision mapping has been implemented.

## Configuration input

`LeadVehicleBrakingScenario` has no implicit operating-condition generator and
requires every field explicitly.

| Field | Type | Rule |
| --- | --- | --- |
| `ego_initial_speed_mps` | `float` | finite and `>= 0` |
| `lead_initial_speed_mps` | `float` | finite and `>= 0` |
| `initial_gap_m` | `float` | finite and `> 0` |
| `lead_brake_start_s` | `float` | finite, `>= 0`, and less than `max_simulation_time_s` |
| `lead_braking_deceleration_mps2` | `float` | finite positive magnitude |
| `ego_reaction_time_s` | `float` | finite and `>= 0` |
| `ego_max_braking_deceleration_mps2` | `float` | finite positive magnitude |
| `simulation_step_s` | `float` | finite, `> 0`, and no greater than `max_simulation_time_s` |
| `max_simulation_time_s` | `float` | finite and `> 0` |
| `strategy` | `DrivingStrategy` | explicit strategy enum |

The fixed `simulation_step_s` is part of the deterministic simulation contract.
The simulation clock and runner are not implemented in this stage.

## Single-frame state

`VehicleState` contains `position_m`, non-negative `speed_mps`, and signed
`acceleration_mps2`. All three values are finite. Position may be negative. The
object is a snapshot and exposes no movement, braking, or step method.

`SimulationFrame` contains:

| Field | Type | Rule |
| --- | --- | --- |
| `time_s` | `float` | finite and `>= 0` |
| `ego` | `VehicleState` | ego snapshot |
| `lead` | `VehicleState` | lead snapshot |
| `metrics` | `RiskMetrics` | supplied metrics container |
| `control_action` | `ControlAction` | supplied action value |

The frame constructor does not advance state or derive metrics or actions.

## Risk metrics container

`RiskMetrics` stores values calculated elsewhere in a future phase.

| Field | Type | Rule |
| --- | --- | --- |
| `gap_m` | `float` | finite; zero and negative overlap values allowed |
| `relative_speed_mps` | `float` | finite signed value |
| `ttc_s` | `float | None` | finite and `>= 0` when present |
| `thw_s` | `float | None` | finite and `>= 0` when present |
| `ego_stopping_distance_m` | `float` | finite and `>= 0` |
| `risk_level` | `RiskLevel` | supplied classification |

The container calculates no formula and does not infer `risk_level`.

## Events

`SimulationEvent` contains a finite non-negative `time_s`, a structured
`SimulationEventType`, and a `message` that must not be blank after trimming for
validation. It has no unstructured metadata dictionary.

## Summary

`SimulationSummary` contains supplied aggregate values; it computes none of them.

| Field | Type | Rule |
| --- | --- | --- |
| `duration_s` | `float` | finite and `>= 0` |
| `collided` | `bool` | supplied collision outcome |
| `minimum_gap_m` | `float` | finite; negative overlap allowed |
| `minimum_ttc_s` | `float | None` | finite and `>= 0` when present |
| `final_gap_m` | `float` | finite; negative overlap allowed |
| `warning_trigger_time_s` | `float | None` | finite and `>= 0` when present |
| `aeb_trigger_time_s` | `float | None` | finite and `>= 0` when present |

## Complete result

`SimulationResult` is the versioned result envelope.

| Field | Type | Rule |
| --- | --- | --- |
| `schema_version` | `str` | exactly `"1.0"` |
| `scenario` | `LeadVehicleBrakingScenario` | original validated configuration |
| `frames` | `tuple[SimulationFrame, ...]` | non-decreasing `time_s` order |
| `events` | `tuple[SimulationEvent, ...]` | non-decreasing `time_s` order |
| `summary` | `SimulationSummary` | supplied summary |

Empty frame and event tuples are valid so a future runner can represent a failure
before its first frame. The contract validates ordering but never sorts input,
calculates the summary, generates an ID, or records wall-clock time.

## Immutability and serialization

All domain classes are frozen, slotted dataclasses. Collection fields use tuples,
and domain objects contain no mutable dictionaries. Stable enum values and
`schema_version = "1.0"` require an explicit data migration before they can change.

`to_json_compatible` creates detached structures containing only `None`, booleans,
integers, finite floats, strings, lists, and string-keyed dictionaries. Enums become
their stable string values, tuples become lists, and dataclasses are represented by
field name. Unsupported objects, non-string dictionary keys, NaN, and infinity are
rejected. The serializer performs no file or network I/O.

DriveGuard Lab's planned longitudinal model is a simplified one-dimensional
simulation. These contracts do not represent real vehicle dynamics and are not a
real-vehicle control or safety-certified interface.

## Strategy evaluation contracts

Stage 10 adds immutable, JSON-compatible evaluation containers without changing
the existing simulation schema version or stable enum values.

- `RiskThresholdSnapshot` records the five finite, positive, correctly ordered
  thresholds actually used by an evaluation.
- `StrategyOutcome` contains one complete `SimulationResult`, its discrete
  collision time, final ego speed, and Warning/partial/emergency command durations.
- `StrategyEvaluation` contains named No Assist, Warning Only, and AEB outcomes,
  plus signed AEB-minus-No-Assist collision and gap comparisons. Its baseline must
  use `DrivingStrategy.NO_ASSIST`.
- `RegressionScenario` associates a stable ID and description with a No Assist
  baseline. `RegressionCaseResult` and `RegressionSuiteResult` carry ordered batch
  results and the threshold snapshot.

Command duration sums only frame-to-frame intervals whose starting frame selects
the action. A terminal-frame action has no following interval and contributes no
duration. Evaluation contracts store supplied values and validate representation;
the simulation evaluation layer performs calculations. No contract provides a
composite score or a best-strategy judgment.
