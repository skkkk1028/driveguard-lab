# Lead-Braking Scenario Step

Stage 6 provides the minimum deterministic execution unit for a lead-vehicle
emergency-braking experiment: create the time-zero frame and advance an existing
frame by one time step. It supports only `DrivingStrategy.NO_ASSIST`; Warning Only
and AEB are rejected rather than silently ignored.

## Initial frame

The ego reference point starts at `0.0 m`, and the lead reference point starts at
`initial_gap_m`. Both speeds come directly from the scenario. This is a
one-dimensional point-vehicle model: `initial_gap_m` is the distance between two
longitudinal reference points, not an exact bumper-to-bumper clearance, and no
vehicle length is added.

The initial frame belongs to `t = 0.0 s`. Ego acceleration and control action are
`0.0 m/s²` and `ControlAction.NONE`. Lead braking configuration is a positive
magnitude, while the applied acceleration is its negative. If braking starts at
zero and the lead is moving, the initial lead acceleration is the negative braking
value. A stopped lead retains zero acceleration. Initial risk metrics are computed
from the initial states rather than filled with placeholders.

## Frame and step time

`SimulationFrame.time_s` is the simulation instant to which every state, metric,
and control-action field in that frame belongs. A returned frame therefore uses
the step end time and metrics recomputed from its end states.

The normal effective step is `simulation_step_s`. If less time remains before
`max_simulation_time_s`, the final step is shortened to land exactly on that
maximum. A frame already at or beyond the maximum cannot be advanced.

Under No Assist, ego always advances with zero applied acceleration, regardless of
risk level, old acceleration, or old control action. The lead follows these exact
time rules:

- If the step ends before braking starts, it coasts for the whole step.
- If the step starts at or after braking starts, braking applies for the whole
  step.
- If braking starts strictly inside the step, the lead first coasts to the boundary
  and then brakes for the remaining sub-step.

The boundary uses right-continuous acceleration semantics. A step ending exactly
at brake start contains no braking motion, but its returned moving-lead state shows
the negative acceleration that becomes effective at that instant. A stopped lead
always shows zero acceleration.

### Internal-boundary example

For a step from `1.9 s` to `2.1 s`, brake start at `2.0 s`, lead speed `20 m/s`,
and braking magnitude `4 m/s²`, the lead coasts for `0.1 s` and brakes at
`-4 m/s²` for `0.1 s`:

```text
displacement = 20 × 0.1 + 20 × 0.1 + 0.5 × (-4) × 0.1²
             = 3.98 m
end speed   = 20 - 4 × 0.1
             = 19.6 m/s
```

Each segment reuses `advance_vehicle`, including its stop-without-reversing
behavior. The brake start is not rounded to a step boundary and no average
acceleration or hidden epsilon is used.

## Current limits and safety

The returned risk metrics use the ending ego and lead states. Contact or overlap
may produce an Emergency classification, but this single-step function does not
locate an exact collision time, truncate the step, emit events, create a summary,
or stop a later run. It does not run a complete loop or assemble a
`SimulationResult`.

Warning Only, AEB, ACC, and real-vehicle control are not implemented. This model is
for software learning and simulation experiments only and must not control a real
vehicle.
