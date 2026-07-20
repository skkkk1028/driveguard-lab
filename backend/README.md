# DriveGuard Lab Backend

This directory contains the minimal FastAPI application and the pure Python domain
contracts for DriveGuard Lab. The API exposes only `GET /health`. The simulation
package provides deterministic, single-vehicle, single-step state advancement but
does not implement a scenario runner. Independent kinematic metric functions,
heuristic risk classification, point-vehicle collision-state checking, and
`RiskMetrics` assembly are available. A No Assist lead-braking scenario can be
initialized and advanced by one time step, including a brake-start boundary inside
that step. No assisted-driving strategy or collision event is implemented. There
is no full scenario loop, event generation, summary, Warning Only behavior, or AEB
behavior.

## Local setup

From this directory in PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

## Verification

```powershell
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m mypy app tests
.\.venv\Scripts\python.exe -m pytest
```
