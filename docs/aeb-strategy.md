# Baseline AEB Strategy

Stage 9 adds a deterministic, stateless baseline AEB strategy for the existing
lead-braking simulation. It consumes an already classified `RiskLevel` and maps it
to one frame action:

| Risk level | Control action | Braking magnitude |
| --- | --- | ---: |
| Safe | `NONE` | 0% |
| Caution | `NONE` | 0% |
| Danger | `PARTIAL_BRAKING` | 50% of configured maximum |
| Emergency | `EMERGENCY_BRAKING` | 100% of configured maximum |

The 50% fraction is a named DriveGuard Lab teaching and simulation heuristic. It
is not an industry calibration, legal requirement, OEM value, or safety guarantee.
Both scenario braking configuration values remain positive magnitudes; the applied
ego acceleration is signed and therefore negative while braking.

## Timing and state

The action recorded on the frame at time `t` applies to the following simulation
interval. The initial frame is classified before the first step, so an initially
Danger or Emergency scenario begins braking at `t = 0`. A returned step frame
records the action selected from that frame's newly calculated risk; the action
does not retroactively change the interval that just ended.

Actions are not latched. Every frame is classified independently, so braking can
escalate, de-escalate, or return to `NONE`. `ego_reaction_time_s` remains an input
to theoretical stopping distance and does not delay automatic braking. Vehicle
motion continues to use the shared stopping-aware dynamics primitive, so strong
braking cannot create negative speed or reverse motion.

## Events and summary

The first partial-braking frame emits one `PARTIAL_BRAKING_TRIGGERED` event, and
the first emergency-braking frame emits one `EMERGENCY_BRAKING_TRIGGERED` event.
Each event type is emitted at most once even when its action later recurs.
`SimulationSummary.aeb_trigger_time_s` is the earlier of those first events, or
`None` when AEB never brakes. AEB emits no `WARNING_TRIGGERED` event, and its
`warning_trigger_time_s` remains `None`.

Collision detection retains the existing discrete point-vehicle rule. A collision
is observed only on a retained frame with `gap_m <= 0`; the runner does not infer
an exact contact time inside a step.

## Safety boundary

This strategy omits sensing uncertainty, actuator dynamics, tire-road limits,
vehicle geometry, brake buildup, and functional-safety mechanisms. It is intended
only for reproducible software simulation experiments and must not control a real
vehicle.
