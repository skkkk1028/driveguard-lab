# Warning Only Strategy

Stage 8 adds a stateless mapping from an already classified `RiskLevel` to a frame
control action:

| Risk level | Control action |
| --- | --- |
| `Safe` | `NONE` |
| `Caution` | `NONE` |
| `Danger` | `WARNING` |
| `Emergency` | `WARNING` |

The selector consumes only `RiskLevel`. It does not inspect TTC, THW, gap,
stopping distance, or thresholds, and it does not reclassify risk.

## Frame behavior

Each frame action is selected independently after that frame's `RiskMetrics` are
calculated. The action is not latched: when risk returns to Safe or Caution, the
action returns to `NONE`; a later Danger or Emergency frame selects `WARNING`
again.

`WARNING` is a simulation warning marker, not a braking command. Ego applied
acceleration remains `0.0 m/s²`, exactly as under No Assist. It cannot alter either
vehicle trajectory, metrics, collision outcome, or stop time.

## Event and summary

The first frame whose action is `WARNING` emits one `WARNING_TRIGGERED` event. Its
time is that discrete frame's `time_s`, including `0.0` when the initial frame
already qualifies. The event is emitted at most once even if the frame action
later returns to `NONE` and then becomes `WARNING` again.

`SimulationSummary.warning_trigger_time_s` records that first event time, or
`None` when no warning occurs. `aeb_trigger_time_s` remains `None`.

## Limitations and safety

The mapping and its upstream risk levels are DriveGuard Lab teaching and
simulation heuristics. They are not an industry warning standard, a real driver
notification system, a braking command, or a safety guarantee. AEB remains
unimplemented. This strategy must not be used to control a real vehicle.
