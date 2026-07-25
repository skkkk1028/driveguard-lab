# DriveGuard Lab Frontend

This directory contains the React, TypeScript, and Vite dashboard for DriveGuard
Lab. The Chinese research interface supports:

- configuring a lead-vehicle emergency-braking scenario in SI units;
- running one No Assist, Warning Only, or AEB simulation;
- comparing the three strategies without ranking them;
- loading the six regression scenarios as configuration presets;
- optionally overriding all five risk thresholds; and
- reviewing a compact simulation or evaluation summary.

Full frame playback, event timelines, charts, vehicle animation, and export are
reserved for later phases. Regression scenarios are presets only; this frontend
does not run the complete regression suite.

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
npm.cmd install
npm.cmd run dev
npm.cmd run lint
npm.cmd run typecheck
npm.cmd run test
npm.cmd run build
```

On systems where PowerShell permits `npm.ps1`, `npm` can be used in place of
`npm.cmd`.

See [`../docs/dashboard-workflow.md`](../docs/dashboard-workflow.md) for the
configuration, validation, request, and result-display behavior.
