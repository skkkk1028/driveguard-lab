# SUMO Adapter Exploration

Stage 14 adds an optional, backend-only experiment adapter in
`backend/app/adapters/sumo`. It does not change the FastAPI API, Dashboard,
domain contracts, `SimulationResult` schema `1.0`, or the deterministic
internal runner.

## Purpose and modes

The adapter keeps DriveGuard Lab's point-vehicle result and SUMO's physical
collision information separate. Neither is substituted for the other.

- **Trajectory replay** runs the existing internal scenario first, places each
  retained state into SUMO, and reads it back through TraCI. Its purpose is to
  verify the TraCI lifecycle and coordinate-reference mapping. Position, speed,
  and point-reference gap must each agree within the named `1e-9` absolute
  tolerance.
- **Controlled native probe** asks SUMO to advance the same two vehicles with
  its ballistic step method. DriveGuard Lab still supplies risk metrics, the
  Warning/AEB mapping, braking magnitudes, retained decision times, and lead
  braking boundary. The report records deterministic differences from the
  internal result; it does not assert numerical equivalence or call either
  model more accurate.

The adapter accepts only experiment inputs representable to `0.001 s`, with a
main step no greater than `1 s`, duration no greater than `60 s`, and at most
`100,000` SUMO substeps. These constraints deliberately do not narrow the API
or internal simulation contracts.

## Optional installation

Base development installation does not download SUMO. Install the optional
official Eclipse SUMO wheel only when running these experiments:

```powershell
cd backend
.\.venv\Scripts\python.exe -m pip install -e ".[dev,sumo]"
.\.venv\Scripts\python.exe -m app.adapters.sumo doctor
```

The optional dependency is pinned to `eclipse-sumo==1.27.1`. The wheel supplies
the headless binary and its bundled TraCI tools under its EPL-2.0 licensing;
the repository does not copy SUMO code or binaries. See the
[SUMO download documentation](https://sumo.dlr.de/docs/Downloads.php) and the
[pinned PyPI release](https://pypi.org/project/eclipse-sumo/1.27.1/).

Binary lookup is deterministic: an explicit argument, `SUMO_BINARY`, the
optional package's `SUMO_HOME`, `SUMO_HOME`, then system `PATH`. An explicitly
named but missing binary is an error; it is never silently ignored. The adapter
rejects `sumo-gui` and runs only headless `sumo` processes.

On Windows, SUMO can release its error-log handle shortly after TraCI closes.
The adapter retries cleanup of only its own temporary experiment directory for a
bounded one-second window before reporting a cleanup failure.

## Command line experiments

All commands emit a report using the adapter-local schema version `0.1` as JSON
on standard output:

```powershell
python -m app.adapters.sumo doctor
python -m app.adapters.sumo replay --scenario-id aeb_avoids_collision --strategy aeb
python -m app.adapters.sumo probe --scenario-id initial_emergency_and_boundaries --strategy aeb
```

The scenario identifier must be one of the six standard regression scenarios;
the strategy is `no_assist`, `warning_only`, or `aeb`. Exit status `0` means a
completed experiment, `2` means SUMO is unavailable or misconfigured, and `3`
means a SUMO execution failure.

## Modeling limits

The bundled network is an intentionally minimal straight, one-lane road. A
fixed lane-position offset maps DriveGuard's reference-point coordinates to
SUMO. Vehicle lengths, `minGap=0`, disabled automatic speed/lane controls, and
SUMO physical collision detection exist solely for diagnosis. DriveGuard's gap
remains the difference between its two reference points, and its collision rule
remains `gap_m <= 0` at retained frames.

This is a reproducible teaching and research experiment, not vehicle
calibration, safety evidence, a functional-safety claim, or a real-vehicle
control interface.
