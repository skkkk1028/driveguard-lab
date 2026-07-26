# DriveGuard Lab Frontend v1.0

This directory contains the React, TypeScript, and Vite dashboard for DriveGuard
Lab. The Chinese research interface supports:

- configuring a lead-vehicle emergency-braking scenario in SI units;
- running one No Assist, Warning Only, or AEB simulation;
- comparing the three strategies without ranking them;
- loading the six regression scenarios as configuration presets;
- optionally overriding all five risk thresholds; and
- reviewing a compact simulation or evaluation summary;
- playing retained frames at four wall-clock speeds and jumping to events; and
- inspecting the point-vehicle scene, exact frame values, categorical bands, and
  linked native SVG charts.

Evaluation playback uses a shared time union and can switch among all three
strategies. Playback selects discrete API frames and never interpolates physical
state. Regression scenarios remain presets only; this frontend does not run the
complete regression suite. Persistence, export, streaming, maps, and real vehicle
interfaces are reserved for later work.

The v1.0 frontend requires Node.js 24.x and npm 11.x. It remains a private
application package and is built as static assets; it is not published to npm.

Successful API responses are validated at runtime before they reach React. The
client rejects incompatible schema versions, missing required fields, unknown
stable enum values, non-finite numbers, and invalid frame/event sequences with
`response_contract_error`. It permits additive fields and does not recalculate
simulation behavior. Shared backend-generated examples live in
`../contracts/api-v1`.

## Backend connection

Start the FastAPI application before the frontend. The dashboard uses
`http://127.0.0.1:8000` by default. To use a different API origin, copy
`.env.example` to `.env.local` and set:

```dotenv
VITE_API_BASE_URL=http://127.0.0.1:8000
```

Trailing slashes are removed by the API client. The browser origin must also be
allowed by the backend CORS configuration.

## Commands

```powershell
npm.cmd ci
npm.cmd run dev
npm.cmd run lint
npm.cmd run typecheck
npm.cmd run test
npm.cmd run build
```

On systems where PowerShell permits `npm.ps1`, `npm` can be used in place of
`npm.cmd`.

See [`../docs/dashboard-workflow.md`](../docs/dashboard-workflow.md) for the
configuration and request behavior, and
[`../docs/simulation-playback.md`](../docs/simulation-playback.md) for playback
and visualization semantics.
