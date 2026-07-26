# Integration Hardening and Expanded Validation

Stage 15 strengthens the existing API, Dashboard, simulation, and optional SUMO
boundaries. It does not add a strategy, endpoint, domain field, or schema version.

## Successful-response validation

The Dashboard API client validates every successful response before returning it
to React. The decoder covers the regression catalog, single-strategy response,
and three-strategy evaluation. It requires the documented fields, stable enum
values, finite numbers, schema `1.0`, at least one retained frame, strictly
increasing frame times, ordered events, and exactly one final completion event.

Unknown additional fields are allowed so an additive server change does not break
an older Dashboard. A missing or incompatible value raises `ApiClientError` with
code `response_contract_error` and the HTTP status. The error does not include the
raw payload. Validation is limited to the transport and playback contract: the
frontend does not recalculate motion, metrics, risk, collision, or summaries.

## Shared API v1 fixtures

Representative endpoint responses live in `contracts/api-v1`. They cover the
regression catalog, an AEB simulation, a boundary-focused evaluation, and the
simulation interval-limit error. Backend endpoint execution and frontend client
tests consume the same JSON.

Check the committed fixtures without changing them:

```powershell
.\backend\.venv\Scripts\python.exe .\scripts\api_contract_fixtures.py --check
```

After an explicitly reviewed API contract change, regenerate them with `--write`
and review the resulting diff. Normal verification never rewrites fixtures.

## Validation profiles

The deterministic base profile excludes optional live SUMO tests and therefore
has the same coverage on every development machine:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify.ps1
```

The strict SUMO profile is separate and fail-closed. It first requires the
supported headless SUMO 1.27.1 runtime, then runs every live replay and native
probe test. An unavailable runtime is a failure rather than a skip:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify-sumo.ps1
```

The expanded backend matrix covers every numeric request field, malformed and
top-level request shapes, the exact 10,000-interval boundary, extreme finite
inputs, all six regression scenarios, all three strategies, and default plus
custom thresholds. Whole-result checks enforce serialization finiteness,
determinism, frame/event ordering, summary consistency, strategy identity, and
documented cross-strategy trajectory invariants.
