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
- Single Scenario Step for No Assist, Warning Only, and baseline AEB
- Sub-step Handling at Brake Start Boundary
- SimulationFrame Assembly from end-of-step states and metrics
- Bounded simulation loop for all three strategies, composed from scenario steps
- Stateless Warning Only mapping from classified risk to `NONE` or `WARNING`
- Stateless baseline AEB mapping to no, partial, or emergency braking
- Current-frame AEB action application during the following simulation interval
- First partial- and emergency-braking events and AEB trigger summary time
- Basic Simulation Events including the first Warning action
- Simulation Summary aggregation across retained frames
- SimulationResult Assembly with schema version, frame tuple, and event tuple
- Physical trajectory and risk-metric equivalence between No Assist and Warning Only

Not implemented:

- ACC
- API Simulation Endpoint
- API or frontend simulation features

The runner supports No Assist, a non-braking Warning Only action, and baseline AEB.
Warning does not alter vehicle motion. AEB uses 50% of configured maximum braking
at Danger and 100% at Emergency. All event times remain discrete frame
observations.

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
