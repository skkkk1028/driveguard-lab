# FastAPI Simulation API

Stage 11 exposes the deterministic simulation core through a synchronous,
stateless HTTP API. The API does not persist requests, assign run IDs, select a
best strategy, or change any domain calculation.

Start the backend from `backend/`:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Swagger UI is available at `http://127.0.0.1:8000/docs`, and the OpenAPI document
is available at `http://127.0.0.1:8000/openapi.json`. ReDoc remains disabled.

## Endpoints

| Method and path | Behavior | Successful response |
| --- | --- | --- |
| `POST /api/v1/simulations` | Run one No Assist, Warning Only, or AEB scenario | Threshold snapshot and `SimulationResult` |
| `POST /api/v1/evaluations` | Run the three strategies for one physical baseline | `StrategyEvaluation` |
| `GET /api/v1/regression-scenarios` | Read the six fixed scenarios in catalog order | Array of `RegressionScenario` |
| `POST /api/v1/regression-suites` | Evaluate all fixed scenarios | `RegressionSuiteResult` |

All successful requests return HTTP 200. A simulation request supplies the ten
fields of `LeadVehicleBrakingScenario`, including `strategy`, inside `scenario`.
An evaluation supplies the nine physical fields inside `baseline_scenario`; the
API constructs the required No Assist baseline rather than accepting a redundant
strategy field.

Example single-strategy request:

```json
{
  "scenario": {
    "ego_initial_speed_mps": 10.0,
    "lead_initial_speed_mps": 10.0,
    "initial_gap_m": 15.0,
    "lead_brake_start_s": 0.0,
    "lead_braking_deceleration_mps2": 5.0,
    "ego_reaction_time_s": 0.0,
    "ego_max_braking_deceleration_mps2": 8.0,
    "simulation_step_s": 0.5,
    "max_simulation_time_s": 5.0,
    "strategy": "aeb"
  }
}
```

The single-run response is `{ "thresholds": ..., "result": ... }`. This wrapper
records the thresholds without changing `SimulationResult` or schema version
`1.0`. Evaluation and regression-suite results already contain their threshold
snapshot and are returned directly. Domain tuples serialize as JSON arrays, enum
members use their stable string values, and unavailable metrics serialize as
`null`.

Since Stage 15, the Dashboard validates successful response structure, finite
numbers, stable enums, schema version, and playback ordering before storing a
result. Incompatible HTTP 200 payloads become `response_contract_error`; this
client-side boundary does not recalculate any simulation value. See
[`integration-hardening.md`](integration-hardening.md) for the shared fixture and
verification workflow.

## Risk thresholds

Each POST endpoint accepts an optional `risk_thresholds` object. When omitted,
`DEFAULT_RISK_THRESHOLDS` is used. An override must contain all five fields:

- `emergency_ttc_s`
- `danger_ttc_s`
- `caution_ttc_s`
- `danger_thw_s`
- `caution_thw_s`

Values must be finite and positive, with
`emergency_ttc_s < danger_ttc_s < caution_ttc_s` and
`danger_thw_s < caution_thw_s`. Partial overrides are rejected. A regression-suite
request may have no body, an empty object, or a complete threshold override.

## Validation and resource limit

Malformed JSON, missing or extra fields, invalid enum values, non-finite numbers,
domain-constraint violations, and invalid thresholds return HTTP 422:

```json
{
  "error": {
    "code": "validation_error",
    "message": "Request validation failed.",
    "details": [
      {
        "location": ["body", "scenario", "strategy"],
        "message": "Input should be 'no_assist', 'warning_only' or 'aeb'",
        "error_type": "enum"
      }
    ]
  }
}
```

One strategy run may contain at most 10,000 advancement intervals and therefore
at most 10,001 retained frames. Larger requests are rejected before the runner is
called with error code `simulation_limit_exceeded`. An evaluation applies the
same limit to each of its three runs.

## Browser access and safety boundary

Development CORS allows only `http://localhost:5173` and
`http://127.0.0.1:5173`, without credentials. This is a local-development setting,
not a production deployment policy. The endpoints expose a simplified educational
point-vehicle model; they are not safety-certified and must not control a real
vehicle.
