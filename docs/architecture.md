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
- Lead Braking Scenario Initialization for the time-zero frame
- Single Scenario Step for the No Assist strategy
- Sub-step Handling at Brake Start Boundary
- SimulationFrame Assembly from end-of-step states and metrics
- Bounded No Assist Full Simulation Loop composed from scenario steps
- Basic Simulation Events for lead braking, risk changes, collision, and completion
- Simulation Summary aggregation across retained frames
- SimulationResult Assembly with schema version, frame tuple, and event tuple

Not implemented:

- Warning Only Strategy
- AEB Strategy
- ACC
- API Simulation Endpoint
- API or frontend simulation features

The complete runner applies only No Assist. It does not make warning or AEB
decisions, and collision time remains a discrete frame-end observation.

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
