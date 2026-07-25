# Simulation Playback and Visualization

Phase 13 adds a browser-side research workbench for inspecting the complete
responses produced by the existing simulation and evaluation endpoints. It does
not change the backend runner, API contracts, or schema version `1.0`.

## Discrete playback model

The workbench starts paused at `t = 0` after a successful run. Its controls move
only among retained `SimulationFrame` objects: first, last, previous, next, a time
scrubber, and playback at `0.5×`, `1×`, `2×`, or `4×`. At `1×`, one second of wall
clock animation advances one second of simulation time. A
`requestAnimationFrame` clock and binary search select the latest retained frame
not later than the advancing time. Fine time steps may therefore skip an
intermediate render, but never create an interpolated state.

Manual seeking and strategy changes pause playback. Playing from the final frame
restarts at the first frame. Event selection uses the first retained frame not
earlier than the event time; this is important when lead braking begins within a
simulation step.

For a single simulation, the time axis is that result's frame sequence. For a
three-strategy evaluation, it is the sorted, de-duplicated union of all three
frame sequences and ends with the longest result. A strategy is inspected using
its newest frame not later than the shared cursor. If it has already collided or
completed, its final frame remains visible and is marked `已终止`.

## Research views

The active strategy controls the road schematic, exact frame values, categorical
risk/action bands, event list, and TTC/THW chart. The schematic keeps ego at a
fixed visual reference and maps the current API-provided gap to the lead marker;
vehicle outlines do not change the point-vehicle collision rule `gap_m <= 0`.

Three linked native SVG charts show:

- ego and lead speed;
- gap and active-ego theoretical stopping distance; and
- TTC and THW with the five thresholds actually returned for the run.

In evaluation mode, the speed and gap charts overlay No Assist, Warning Only, and
AEB, with the selected strategy emphasized. The common lead trace comes from the
longest result. Clicking a chart seeks the nearest shared retained time. `null`
TTC or THW breaks a line instead of being plotted as zero. SVG paths and scales
are memoized, and classification segments are combined into a small fixed number
of paths rather than creating one React element per frame.

All textual physical values are the unrounded values received from the API. Scale
and road-coordinate calculations affect drawing positions only and are not
presented as simulation results.

## Boundaries

Playback is local presentation of an already completed response. It does not add
continuous interpolation, exact within-step collision timing, persistence,
export, WebSocket streaming, maps, or real vehicle interfaces. The visualization,
thresholds, and baseline AEB behavior are teaching and research aids, not
calibration data, functional-safety evidence, or a real vehicle controller.
