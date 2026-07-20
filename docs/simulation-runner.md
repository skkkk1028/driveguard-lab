# Simulation Runner

The deterministic lead-braking runner supports `DrivingStrategy.NO_ASSIST` and
`DrivingStrategy.WARNING_ONLY`. It composes the existing initializer and
single-step primitive into a complete `SimulationResult`; AEB is rejected.

## Run flow and frames

The runner stores the `t = 0` frame, repeatedly calls
`advance_lead_braking_scenario_step`, and stores each returned frame. It does not
reimplement vehicle motion, brake-boundary segmentation, metrics, or risk
classification.

Frames are an immutable tuple in non-decreasing time order. No Assist frames always
use `ControlAction.NONE`. Warning Only frames select `NONE` for Safe/Caution and
`WARNING` for Danger/Emergency. Selection is per-frame and non-latching.

For identical physical parameters, No Assist and Warning Only have identical frame
times, ego and lead trajectories, `RiskMetrics`, collision result, and stop time.
Only strategy, frame action, Warning event, and warning summary time may differ;
Warning never changes motion.

The final retained frame is the first discrete frame with non-positive gap or the
frame at `max_simulation_time_s`. The loop has a deterministic upper bound, and a
shortened final step prevents exceeding maximum time:

```text
frame.metrics.gap_m <= 0
frame.time_s >= max_simulation_time_s
```

Collision time is the discrete frame-end observation. The runner does not solve
exact contact time inside a step, clamp positions, or discard the collision frame.

## Events

Events have stable messages and form a time-ordered tuple:

| Event | Time and condition |
| --- | --- |
| `lead_braking_started` | Once at `lead_brake_start_s` when that time enters the executed interval |
| `risk_level_changed` | At the newer frame when adjacent risk levels differ |
| `warning_triggered` | Once at the first frame whose action is `WARNING`; possibly `0.0` |
| `collision` | Once at the first frame with `gap_m <= 0` |
| `simulation_completed` | Always at the final frame |

No Assist emits no Warning event. Warning Only emits at most one even when its
frame action later recovers and rises again. Events sharing a time use this order:

```text
LEAD_BRAKING_STARTED
RISK_LEVEL_CHANGED
WARNING_TRIGGERED
COLLISION
SIMULATION_COMPLETED
```

No partial-braking or emergency-braking trigger event is generated.

## Summary and result

`SimulationSummary` aggregates all retained frames without rounding:

- `duration_s`: final frame time
- `collided`: whether any frame has a non-positive gap
- `minimum_gap_m`: smallest gap across all frames
- `minimum_ttc_s`: smallest applicable TTC, or `None` if all are `None`
- `final_gap_m`: final frame gap
- `warning_trigger_time_s`: first Warning event time for Warning Only, otherwise
  `None`
- `aeb_trigger_time_s`: always `None`

The result carries schema version `1.0`, the immutable input scenario, frame and
event tuples, and the summary. Identical inputs and thresholds produce identical
results. No files are exported, and wall-clock time and randomness are unused.

## Current limits

This discrete point-vehicle simulation does not provide exact continuous collision
timing, AEB, ACC, an API, or a frontend workflow. Warning is not a real vehicle
command or safety guarantee. The project is not safety certified and must not
control a real vehicle.
