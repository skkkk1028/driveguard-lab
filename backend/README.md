# DriveGuard Lab Backend

This directory contains the minimal FastAPI application and the pure Python domain
contracts for DriveGuard Lab. The API exposes only `GET /health`. The simulation
package provides deterministic vehicle advancement, metrics, heuristic risk
classification, and point-vehicle collision-state checking. Lead-braking scenarios
can be initialized, advanced one step, or run to completion under No Assist,
Warning Only, and baseline AEB. The runner returns ordered frame and event tuples,
an aggregate summary, and a versioned `SimulationResult`. Warning is non-braking.
Baseline AEB applies half maximum braking at Danger and full maximum braking at
Emergency, with no action latching or actuation delay.

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
