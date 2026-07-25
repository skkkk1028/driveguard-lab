# Dashboard Configuration Workflow

Phase 12 replaces the static frontend page with a Chinese research Dashboard for
configuring and running the existing deterministic simulation API. It is an input
and compact-summary workflow, not a driving control interface or a safety-certified
tool.

## Run locally

Start the FastAPI backend and then the Vite development server:

```powershell
cd backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload

cd ..\frontend
npm.cmd run dev
```

The frontend uses `http://127.0.0.1:8000` unless
`VITE_API_BASE_URL` is set in `frontend/.env.local`. The backend permits the
documented local Vite origins; a different browser origin requires a corresponding
CORS configuration change.

## Configuration flow

The initial form uses the `aeb_avoids_collision` physical parameters and selects
AEB for a single simulation. Inputs are grouped into vehicle initial state, lead
braking, ego behavior, and simulation settings, with SI units shown beside every
physical quantity.

Two run modes share the same physical form:

- **Single simulation** selects No Assist, Warning Only, or AEB and calls
  `POST /api/v1/simulations`.
- **Three-strategy evaluation** sends no strategy choice and calls
  `POST /api/v1/evaluations`; the backend evaluates No Assist, Warning Only, and
  AEB in its fixed order.

At startup, `GET /api/v1/regression-scenarios` supplies six named presets. A preset
replaces only physical parameters and does not alter the current mode or selected
single-run strategy. If the catalog cannot be loaded, the Dashboard reports a
non-blocking message and keeps manual configuration available. It does not call
the regression-suite endpoint.

Risk-threshold customization is disabled by default, so requests omit
`risk_thresholds` and the backend defaults remain authoritative. Enabling advanced
settings exposes the complete five-value override initialized to TTC `1/2/4 s`
and THW `1/2 s`; partial or non-increasing overrides are rejected.

## Validation and request state

Numeric fields remain strings while edited and are parsed only at submission. The
Dashboard rejects missing or non-finite values, invalid positive/non-negative
ranges, a lead brake start outside the simulation, a step larger than the maximum
duration, more than 10,000 advancement intervals, and incorrectly ordered
thresholds before making an API call.

Only one run request may be active at a time. Editing configuration clears the old
summary so that displayed results cannot be mistaken for the new inputs. Reset
restores the documented default configuration. API field errors are associated
with their form fields when possible; other validation, HTTP, and network failures
appear as a global Chinese error message.

## Result presentation

A single-run summary reports the strategy, collision state, duration, frame count,
minimum and final gap, minimum TTC, and Warning/AEB trigger times. An evaluation
summary places No Assist, Warning Only, and AEB outcomes side by side and reports
the existing signed AEB-minus-No-Assist comparison fields. It does not create a
score, ranking, or best-strategy conclusion.

The complete API response is retained in frontend state, and displayed physical
values come directly from that response without recomputation or rounding. Phase
12 does not provide frame playback, playback controls, event timelines, dynamic
charts, vehicle animation, persistence, or export; those remain later-phase work.
