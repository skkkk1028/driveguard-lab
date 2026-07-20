# Vehicle Dynamics

Stage 3 implements a deterministic, one-dimensional state-advancement primitive
for one vehicle and one fixed time step. It is not a scenario runner or a complete
vehicle simulation.

## Coordinates and units

- Increasing `position_m` is the forward road direction; any finite starting
  position, including a negative value, is valid.
- `speed_mps` is longitudinal speed in meters per second and has a lower bound of
  zero. Reverse motion is not supported.
- `acceleration_mps2` is signed longitudinal acceleration in meters per second
  squared. Positive values accelerate, zero maintains speed, and negative values
  decelerate or brake.
- `dt_s` is a strictly positive time step in seconds.

## One-step model

`advance_vehicle(state, applied_acceleration_mps2, dt_s)` advances exactly one
vehicle through exactly one time step. The applied acceleration is constant within
that step and overrides the acceleration stored in the input state.

When the vehicle remains in motion for the full step, the model uses:

```text
v_next = v_current + a × dt
x_next = x_current + v_current × dt + 0.5 × a × dt²
```

The returned `acceleration_mps2` is the acceleration applied during the step.
Calculations use standard Python floating-point values and are not rounded for
display.

## Stopping inside a time step

For negative applied acceleration, the model calculates:

```text
time_to_stop = current_speed / abs(applied_acceleration)
```

If this time is less than or equal to `dt_s`, integration ends at the stopping
instant:

```text
stopping_displacement =
    current_speed × time_to_stop
    + 0.5 × applied_acceleration × time_to_stop²
```

Position remains fixed for the rest of the time step. The returned speed and
acceleration are both zero because the speed floor is active and the vehicle is
stationary at the end of the step. A stopped vehicle under zero or negative
acceleration likewise remains at its current position with zero speed and zero
acceleration. A stopped vehicle under positive acceleration uses the normal
constant-acceleration equations.

Computing a full-step displacement and then merely clamping a negative speed would
be incorrect: the equations would continue integrating after the stopping instant
and could move the vehicle forward too far or backwards. Piecewise integration
ensures speed never becomes negative and reverse displacement is not introduced.

## Determinism

The function is pure and stateless. It does not mutate its input, and every call
returns a new `VehicleState`. Identical inputs produce identical outputs. The
implementation uses no cache, randomness, wall-clock time, environment state,
file access, or network access.

## Model limitations

This simplified point-mass model does not account for:

- Vehicle mass
- Aerodynamic drag
- Rolling resistance
- Road gradient
- Tire adhesion limits
- Brake-system delay
- Jerk
- Lateral motion

It advances only one vehicle for one time step. It does not implement multiple
vehicles, scenarios, collisions, risk metrics, control strategies, or a simulation
loop. It does not represent real vehicle dynamics and must not be used to control a
real vehicle.
