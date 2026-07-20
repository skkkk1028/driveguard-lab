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
