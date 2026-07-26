# DriveGuard Lab Development Rules

- Complete only the phase explicitly requested; do not implement later phases in
  advance.
- Use SI units for every physical calculation and data contract.
- Do not reference FastAPI or React from the domain layer.
- Do not scatter magic thresholds. Name, document, and centralize justified domain
  constants when they are introduced.
- Every addition of business logic must include corresponding tests.
- After changes, run tests, type checks, lint checks, and the production build.
- Do not automatically create, configure, or push to a remote repository.
- Do not integrate with real-vehicle control hardware.
- Do not describe this simulation project as a safety-certified product.
- Floating-point inputs and outputs must not contain NaN or infinity.
- Use `None` when a risk metric is not applicable.
- Braking deceleration configuration uses a positive magnitude.
- `VehicleState.acceleration_mps2` is a signed value.
- Stable enum values and the schema version are public data contracts; do not
  change them without an explicit migration.
- Keep domain objects immutable.
- Keep Python code compatible with Python 3.11.
- Vehicle speed must never fall below zero, and the one-dimensional model does not
  support reversing.
- When braking stops a vehicle inside a time step, integrate only to the stopping
  instant; never compute full-step displacement and then clamp negative speed.
- The acceleration passed to `advance_vehicle` overrides acceleration stored in the
  prior state.
- Do not round physical calculations for UI display.
- Identical simulation inputs must produce identical outputs.
- Calculate gap as `lead.position_m - ego.position_m`.
- Calculate relative speed as `ego.speed_mps - lead.speed_mps`.
- TTC returns `None` when it is not applicable and `0.0` when reference points are
  already in contact or overlapping.
- THW returns `None` while ego is stationary.
- Braking-distance calculations use a positive deceleration magnitude.
- Do not introduce arbitrary epsilon thresholds or UI rounding into kinematic
  calculations.
- Base metric functions must not infer a risk level.
- Fail when finite inputs produce a non-finite calculation result.
- Centralize all risk thresholds in `RiskThresholds`; do not scatter TTC or THW
  magic numbers across other modules.
- Do not change the risk-classification priority without an explicitly requested
  contract change.
- Risk-threshold boundaries use inclusive `<=` comparisons.
- Apply the stopping-distance danger condition only while
  `relative_speed_mps > 0`.
- In the point-vehicle model, `gap_m <= 0` represents collision state.
- The classifier consumes precomputed metrics and must not recalculate them.
- Base metric functions must not call back into the risk classifier.
- Do not describe default risk thresholds as industry standards or certified
  safety values.
- Risk classification must not directly produce a control action.
- A scenario frame time identifies the time of its already-advanced states and
  metrics.
- Split a scenario step into sub-steps when lead braking starts inside it; never
  round brake start to a time-step boundary.
- Use right-continuous acceleration semantics at the lead brake-start boundary.
- Under No Assist, ego applied acceleration is always zero.
- Risk level must not directly alter vehicle motion.
- Scenario code must reuse `advance_vehicle` instead of copying its integration.
- A final scenario step must not exceed `max_simulation_time_s`.
- A single-step scenario function must not run a complete simulation loop.
- Stage 6 collision state must not automatically create events or summaries.
- A complete runner must compose scenario initialization and single-step functions;
  it must not copy their motion, metric, or risk logic.
- Full simulation loops must have a deterministic upper bound.
- All supported strategy runs stop at the first collision frame or maximum
  simulation time and retain that final frame.
- Collision event time is the discrete collision-frame time; do not infer an exact
  within-step collision instant.
- Emit lead-braking start and collision events at most once per run.
- At one time, order lead braking, risk change, warning, collision, then completion.
- Every completed run emits `SIMULATION_COMPLETED` at its final frame time.
- Aggregate summaries from all retained frames without rounding; ignore `None`
  values when finding minimum TTC.
- Store result frames and events as immutable tuples.
- No Assist runners must not emit assisted-control trigger events.
- Warning Only maps only a preclassified `RiskLevel`; it must not recompute TTC,
  THW, or risk.
- Warning Only maps Safe/Caution to `NONE` and Danger/Emergency to `WARNING` on
  every frame without action latching.
- A Warning action must not alter ego acceleration, either vehicle trajectory,
  metrics, collision outcome, or stop time.
- Emit `WARNING_TRIGGERED` at most once at the first Warning frame; No Assist emits
  none.
- Derive `warning_trigger_time_s` from the first Warning event.
- Baseline AEB maps Safe/Caution to `NONE`, Danger to `PARTIAL_BRAKING`, and
  Emergency to `EMERGENCY_BRAKING` without latching.
- An AEB action stored at time `t` applies to the following simulation interval.
- Partial AEB braking uses exactly half the configured maximum braking magnitude;
  emergency braking uses the full magnitude.
- `ego_reaction_time_s` affects stopping-distance risk metrics, not AEB actuation
  delay.
- Emit each AEB braking trigger event at most once, derive `aeb_trigger_time_s`
  from the first such event, and emit no Warning event for AEB.
- Strategy evaluation must require a No Assist baseline and run No Assist,
  Warning Only, then AEB with identical physical parameters and risk thresholds.
- Record the actual evaluation thresholds in an immutable serializable snapshot.
- Command duration is the sum of following frame intervals selected by an action;
  a terminal-frame action contributes no duration.
- Evaluation comparisons use signed AEB-minus-No-Assist deltas and must not infer
  a best strategy or composite safety score.
- Keep the standard regression catalog deterministic, immutable, and reusable;
  runtime suite execution returns data rather than pass/fail judgments.
- Keep simulation HTTP endpoints synchronous and stateless; they must delegate
  motion, risk, strategy, evaluation, and regression behavior to the simulation
  core rather than copy it.
- Keep versioned simulation endpoints under `/api/v1` and preserve `GET /health`.
- API request models must reject non-finite values, unknown fields, incomplete
  threshold overrides, and violations of existing domain constraints.
- Reject API requests exceeding 10,000 advancement intervals per strategy before
  calling a complete simulation runner.
- Keep API validation failures in the stable HTTP 422 error envelope; do not add
  transport error fields to simulation domain contracts.
- Local-development CORS must use explicit origins and must not enable credentials
  or wildcard origins.
- Keep Dashboard simulation behavior in the backend; frontend validation must not
  duplicate motion, risk classification, strategy, or summary calculations.
- Keep Dashboard physical inputs in SI units and preserve numeric form values as
  strings until submission validation and conversion.
- Read the frontend API base from `VITE_API_BASE_URL`, defaulting to
  `http://127.0.0.1:8000`, and centralize HTTP calls in the API client.
- When custom risk thresholds are disabled, omit `risk_thresholds` from requests;
  when enabled, send all five finite, strictly ordered values.
- Regression scenarios in the phase 12 Dashboard are configuration presets only;
  selecting one must not change the current run mode or single-run strategy.
- Clear a displayed result when its configuration changes, and block duplicate
  submissions while a request is active.
- Do not recalculate or round API result values for Dashboard display.
- Keep complete API responses in client state; configuration changes must remove
  both stale summaries and playback views.
- Playback must select existing retained frames without interpolating physical
  state or inferring within-step collision time.
- At `1×`, playback advances by wall-clock simulation time and uses binary lookup;
  update React state only when the selected retained frame changes.
- Evaluation playback uses the sorted union of all strategy frame times and holds
  an already-terminated strategy at its final frame.
- Event seeking selects the first retained frame not earlier than the event time.
- Keep chart coordinates as presentation-only values; textual physical values
  must remain unrounded API values, and `null` metrics must render as line breaks.
- Do not create one React DOM node per frame for large plots or categorical bands;
  use memoized SVG paths.
- Frontend playback must not add endpoints, duplicate simulation calculations,
  score strategies, or imply a safety guarantee.
- Keep SUMO optional and isolated beneath `app.adapters.sumo`; it must not alter
  FastAPI, Dashboard, domain contracts, internal `SimulationResult`, or schema
  `1.0`.
- SUMO trajectory replay uses a named `1e-9` absolute state tolerance. Native
  probes report deterministic differences only and never claim either simulator
  is more accurate.
- Keep DriveGuard point-reference collision state and SUMO physical collision
  state separate in adapter reports. SUMO may not replace the internal runner.
- SUMO experiments use headless `sumo`, a unique TraCI connection, fixed seed,
  and cleanup in all success and failure paths; do not launch `sumo-gui`.
- Validate successful Dashboard API responses before storing them. Reject missing
  required fields, non-finite values, unknown stable enums, incompatible schema
  versions, and invalid frame/event ordering with `response_contract_error`.
- Successful-response validation may accept additive fields but must not
  recalculate motion, metrics, risk, collision, or summaries in the frontend.
- Keep committed API v1 fixtures deterministic. Verification checks fixture drift
  and must never rewrite fixtures automatically.
- Keep the default verification profile independent of optional SUMO. Strict SUMO
  verification must fail rather than skip when the supported runtime is absent.
- Keep application/package release version `1.0.0` separate from simulation data
  schema version `1.0`; a release metadata change must not silently migrate data.
- Stage 16 release checks may build temporary artifacts, but must not commit build
  output, create tags, publish packages, configure a remote, or claim hosted CI ran.
