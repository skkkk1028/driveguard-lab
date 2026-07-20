# Architecture

DriveGuard Lab v1.0 is planned as a deterministic, one-dimensional longitudinal
vehicle simulation and risk-assessment platform. Stage 1 establishes only the
engineering boundary; the domain components below do not exist yet.

```text
Scenario Configuration
        ↓
Simulation Runner
        ↓
Vehicle Dynamics
        ↓
Risk Metrics
        ↓
Driving Strategy
        ↓
Simulation Result
        ↓
FastAPI
        ↓
React Dashboard
```

## Boundaries and constraints

- Future domain simulation code will live in an independent backend module.
- The domain layer must not depend on FastAPI or any web-delivery concern.
- All internal physical quantities will use SI units.
- Simulations will use a fixed time step to support deterministic reproduction.
- The frontend will be responsible only for configuration, playback, and result
  presentation.
- SUMO may be introduced later as an adapter; it will not be the only execution
  environment for the core algorithms.

The current FastAPI application exposes only a process health check. The React
application is a static foundation page. Neither contains simulation behavior.
