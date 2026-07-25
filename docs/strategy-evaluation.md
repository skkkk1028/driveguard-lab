# Strategy Evaluation and Regression Scenarios

Stage 10 provides a deterministic comparison layer for No Assist, Warning Only,
and baseline AEB. It is an in-memory research capability and performs no API,
file, database, or frontend I/O.

## Evaluation flow

`evaluate_strategies` requires a validated No Assist baseline. It retains every
physical field, applies one shared `RiskThresholds` instance, and runs the three
strategies in this fixed order:

```text
No Assist → Warning Only → AEB
```

The result includes each complete `SimulationResult`, the exact threshold
snapshot, discrete collision time, final ego speed, and command durations for
Warning, partial braking, and emergency braking. Command duration uses the action
on a frame for its following interval; the final frame contributes no duration.

Comparison fields use signed AEB-minus-No-Assist values. Collision-time difference
is available only when both strategies collide. A separate Boolean reports when
No Assist collides and AEB does not. The evaluator does not rank strategies or
claim that AEB always prevents collision.

## Standard catalog

`REGRESSION_SCENARIOS` is an immutable ordered tuple:

| ID | Primary behavior |
| --- | --- |
| `stable_following` | No collision or intervention |
| `caution_only` | Caution without Warning or AEB |
| `warning_without_motion_change` | Warning with No Assist-equivalent motion |
| `aeb_avoids_collision` | No Assist/Warning collide; AEB avoids collision |
| `aeb_unavoidable_collision` | AEB delays but does not avoid collision |
| `initial_emergency_and_boundaries` | Initial Emergency, internal brake boundary, shortened final step |

`run_regression_suite` evaluates the full catalog and returns an immutable ordered
result. It accepts custom thresholds and records them, but runtime execution does
not decide pass/fail. Tests lock the default-threshold expectations because custom
thresholds may intentionally change classification and outcomes.

## Interpretation boundary

The reported quantities belong to the existing discrete point-vehicle model.
They do not include comfort, energy, sensor uncertainty, actuator fidelity, or
functional-safety evidence. Positive gap improvement and collision delay are
observations for a specific simulated input, not proof that one strategy is
universally safer or suitable for real-vehicle control.
