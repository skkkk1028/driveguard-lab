# No Assist Simulation Runner

Stage 7 composes the existing lead-braking initializer and single-step primitive
into a complete deterministic `SimulationResult`. It supports only
`DrivingStrategy.NO_ASSIST`; Warning Only and AEB configurations are rejected.

## Run flow and frames

The runner initializes and stores the `t = 0` frame, repeatedly calls
`advance_lead_braking_scenario_step`, and stores each returned frame. It does not
reimplement vehicle motion, brake-boundary segmentation, risk metrics, or risk
classification.

The immutable result uses a tuple of frames in non-decreasing time order. Every
frame has `ControlAction.NONE`. The final frame is retained and is either the first
frame whose point-vehicle gap is non-positive or the frame at
`max_simulation_time_s`. A shortened final step may be used by the stage 6
primitive, so the run never exceeds the configured maximum.

The loop has a deterministic upper bound derived from maximum time and step size.
It stops when either condition is met:

```text
frame.metrics.gap_m <= 0
frame.time_s >= max_simulation_time_s
```

A collision is observed only at a discrete frame end. The runner does not solve
the exact contact time inside a step, clamp positions, or discard the collision
frame.

## Events

Events have stable, non-empty messages and are stored as an ordered tuple:

| Event | Time and condition |
| --- | --- |
| `lead_braking_started` | Once at `lead_brake_start_s` when that time enters the executed interval; at `0.0` when braking starts immediately |
| `risk_level_changed` | At the newer frame time when adjacent frame risk levels differ |
| `collision` | Once at the first discrete frame with `gap_m <= 0` |
| `simulation_completed` | Always at the final frame time |

If collision occurs before brake start, no lead-braking event is emitted. At one
frame time, risk change precedes collision, which precedes completion. No warning,
partial-braking, or emergency-braking trigger event is generated under No Assist.

## Summary and result

`SimulationSummary` is aggregated from all retained frames without rounding:

- `duration_s`: final frame time
- `collided`: whether any frame has a non-positive gap
- `minimum_gap_m`: smallest gap across all frames
- `minimum_ttc_s`: smallest applicable TTC, or `None` when every TTC is `None`
- `final_gap_m`: final frame gap
- `warning_trigger_time_s`: `None`
- `aeb_trigger_time_s`: `None`

The returned `SimulationResult` carries schema version `1.0`, the original
immutable scenario, frame and event tuples, and the summary. Identical inputs and
thresholds produce identical results. The runner performs no file export and does
not use wall-clock time or randomness.

## Current limits

This is a discrete, one-dimensional point-vehicle research simulation. It does not
provide exact continuous collision timing, Warning Only, AEB, ACC, an API, or a
frontend workflow. It is not safety certified and must not control a real vehicle.
