# Architecture

DriveGuard Lab v1.0 is planned as a deterministic, one-dimensional longitudinal
vehicle simulation and risk-assessment platform. Stage 2 establishes the pure
Python domain vocabulary and data boundaries. It does not implement the simulation
engine shown in the planned flow below.

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

- Stable domain enumerations
- Validated input and output data contracts
- SI speed unit conversion
- JSON-compatible in-memory serialization

Not implemented:

- Vehicle Dynamics
- Risk Metrics Calculation
- Driving Strategy
- Simulation Runner

## Boundaries and constraints

- Domain contracts live in `backend/app/domain` as a pure Python module.
- Future domain simulation behavior will remain independent of delivery code.
- The domain layer must not depend on FastAPI or any web-delivery concern.
- All internal physical quantities will use SI units.
- Simulations will use a fixed time step to support deterministic reproduction.
- The frontend will be responsible only for configuration, playback, and result
  presentation.
- SUMO may be introduced later as an adapter; it will not be the only execution
  environment for the core algorithms.

The current FastAPI application still exposes only a process health check. The
React application remains a static foundation page. Neither contains simulation
behavior, and the domain contracts are not registered as API request models.
