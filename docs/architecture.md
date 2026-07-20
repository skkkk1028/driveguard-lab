# Architecture

DriveGuard Lab v1.0 is planned as a deterministic, one-dimensional longitudinal
vehicle simulation and risk-assessment platform.

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

## Current implementation status

Implemented:

- Stable, immutable domain enumerations and data contracts
- SI speed-unit conversion and JSON-compatible in-memory serialization
- Vehicle Dynamics: deterministic one-dimensional state advancement for one
  vehicle and one time step
- Kinematic Metrics: gap, relative speed, TTC, THW, and theoretical ego stopping
  distance
- Risk Classification using centralized, validated heuristic thresholds
- Basic Point-Vehicle Collision State using the `gap_m <= 0` boundary
- RiskMetrics Assembly from the existing metric functions and classifier

Not implemented:

- Scenario Execution
- Driving Strategy
- Simulation Runner or multi-step loop
- Events
- Summary Generation
- API or frontend simulation features

These implemented pieces are not a complete risk engine and do not make an AEB
decision.

## Boundaries and constraints

- Domain contracts live in `backend/app/domain` as a pure Python module.
- Future domain simulation behavior will live in independent backend modules.
- The domain layer must not depend on FastAPI or any web-delivery concern.
- All internal physical quantities use SI units.
- Simulations will use a fixed time step to support deterministic reproduction.
- The frontend will be responsible only for configuration, playback, and result
  presentation.
- SUMO may be introduced later as an adapter; it will not be the only execution
  environment for the core algorithms.

The FastAPI application still exposes only a process health check. The React
application remains a static foundation page. Neither contains simulation
behavior, and the domain contracts are not registered as API request models.
