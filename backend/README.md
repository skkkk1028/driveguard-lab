# DriveGuard Lab Backend

This directory contains the FastAPI application and the pure Python domain
contracts for DriveGuard Lab. In addition to `GET /health`, the versioned API can
run one strategy, evaluate all three strategies, list the standard regression
catalog, and run the complete regression suite. The simulation
package provides deterministic vehicle advancement, metrics, heuristic risk
classification, and point-vehicle collision-state checking. Lead-braking scenarios
can be initialized, advanced one step, or run to completion under No Assist,
Warning Only, and baseline AEB. The runner returns ordered frame and event tuples,
an aggregate summary, and a versioned `SimulationResult`. Warning is non-braking.
Baseline AEB applies half maximum braking at Danger and full maximum braking at
Emergency, with no action latching or actuation delay. A strategy evaluator runs
all three strategies for one No Assist baseline and returns serializable safety
and intervention metrics. Six deterministic standard regression scenarios are
available individually or through a batch suite runner.

An optional, isolated SUMO adapter supports trajectory-replay and controlled
native-probe experiments. It neither changes the FastAPI contract nor replaces
the internal point-vehicle simulation. See
[`../docs/sumo-adapter-exploration.md`](../docs/sumo-adapter-exploration.md).

The interactive API documentation is available at `http://127.0.0.1:8000/docs`.
See [`../docs/simulation-api.md`](../docs/simulation-api.md) for endpoint contracts,
validation, resource limits, and local-development CORS behavior.

## Local setup

From this directory in PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

## Optional SUMO experiments

Install the headless Eclipse SUMO runtime only when running Stage 14 experiments:

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[dev,sumo]"
.\.venv\Scripts\python.exe -m app.adapters.sumo doctor
.\.venv\Scripts\python.exe -m app.adapters.sumo replay --scenario-id stable_following --strategy aeb
```

`replay` requires `1e-9` coordinate/state round-trip tolerance. `probe` reports
deterministic SUMO-to-internal differences without declaring either model more
accurate. The adapter is a headless research tool and does not expose an API
endpoint or a production vehicle interface.

## Verification

```powershell
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m mypy app tests
.\.venv\Scripts\python.exe -m pytest -m "not sumo"
```

The repository-level `scripts/verify.ps1` also checks shared API fixtures and the
frontend without exercising an optional SUMO installation. Use
`scripts/verify-sumo.ps1` from the repository root for a fail-closed live SUMO
gate.
