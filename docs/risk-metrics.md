# Kinematic Risk Metrics

Stage 4 implements independent, deterministic functions for longitudinal gap,
relative speed, time to collision (TTC), time headway (THW), and theoretical ego
stopping distance. Stage 5 can assemble these values into a complete `RiskMetrics`
object, whose `risk_level` is assigned by the separate risk classifier. The base
metric functions remain independent of thresholds and do not classify risk,
generate collision events, select a driving strategy, or execute a scenario.

## Point-vehicle model

DriveGuard Lab currently treats each vehicle as a point on a one-dimensional road.
`VehicleState.position_m` is a longitudinal reference coordinate, not a bumper
location. Vehicle length, axle position, geometry, and lateral position are not
modeled, so calculated gap is not a real bumper-to-bumper clearance.

All inputs and outputs use SI units and must be finite. Calculations use standard
Python floating point without internal rounding or arbitrary epsilon thresholds.
Finite inputs that produce a non-finite result are rejected.

## Longitudinal gap

```text
gap_m = lead.position_m - ego.position_m
```

- Positive: the lead reference point is ahead.
- Zero: the reference points coincide.
- Negative: the reference points overlap longitudinally or ego has passed lead.

The result is not clamped to zero and does not account for vehicle length.

## Relative speed

```text
relative_speed_mps = ego.speed_mps - lead.speed_mps
```

- Positive: ego is closing on lead.
- Zero: speeds are equal.
- Negative: the longitudinal gap is increasing.

Acceleration is not used to predict future speed.

## TTC

TTC estimates time until the longitudinal reference points meet while current
relative speed remains constant.

```text
gap_m <= 0                              → 0.0
gap_m > 0 and relative_speed_mps > 0    → gap_m / relative_speed_mps
gap_m > 0 and relative_speed_mps <= 0   → None
```

Any strictly positive relative speed counts as closing; no epsilon is applied.
`None` means TTC is currently not applicable because the vehicles are not closing.
`0.0` means the reference points have already reached or passed the zero-gap state.
It does not mean a collision event has been generated. TTC zero and collision
state are distinct engineering concepts, although the current point-vehicle model
uses the same `gap_m <= 0` contact boundary for both.

## THW

THW estimates the time for ego to reach lead's current longitudinal reference
position while ego speed remains constant.

```text
ego_speed_mps == 0                      → None
ego_speed_mps > 0 and gap_m <= 0        → 0.0
ego_speed_mps > 0 and gap_m > 0         → gap_m / ego_speed_mps
```

`None` means THW is not applicable while ego is stationary, even at zero or
negative gap. `0.0` means a moving ego vehicle is already at or past the zero-gap
reference state. Ego speed cannot be negative.

## Theoretical ego stopping distance

Total stopping distance is the sum of reaction distance and idealized braking
distance:

```text
reaction_distance_m = ego_speed_mps × reaction_time_s

braking_distance_m =
    ego_speed_mps² / (2 × braking_deceleration_mps2)

ego_stopping_distance_m =
    reaction_distance_m + braking_distance_m
```

`braking_deceleration_mps2` is a strictly positive deceleration magnitude. The
function does not convert a negative input to a positive value. Zero ego speed
produces zero stopping distance after all inputs have been validated.

This theoretical distance does not include safety margins, vehicle length, tire
adhesion, road gradient, aerodynamic or rolling resistance, brake-system buildup,
or the current acceleration stored in `VehicleState`. It is not equivalent to a
measured real-vehicle stopping distance.

## Scope and safety

NaN and positive or negative infinity are prohibited in both inputs and results.
The functions do not return sentinel values and do not round for UI display.

Risk thresholds and heuristic classification are implemented outside these
formulas, together with a Boolean point-vehicle collision-state check. Collision
events, AEB, and complete scenario execution remain unimplemented. These values
are simulation research quantities, not safety-certified vehicle data, and must
not be used for real-vehicle control.
