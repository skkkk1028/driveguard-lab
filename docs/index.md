# DriveGuard Lab Documentation

This index separates end-user workflow, public contracts, implementation
semantics, optional experiments, and release evidence.

## Start here

- [Chinese user guide](user-guide.md): installation, Dashboard workflow, result
  interpretation, API use, SUMO experiments, and troubleshooting.
- [Architecture](architecture.md): subsystem boundaries and dependency direction.
- [v1.0 release readiness](release-readiness.md): compatibility, verification,
  artifacts, known limits, and deferred publication actions.
- [Public deployment](public-deployment.md): one-domain container delivery,
  Render deployment, custom domains, updates, and operational limits.

## Simulation model and contracts

- [Domain data contracts](data-contracts.md)
- [Vehicle dynamics](vehicle-dynamics.md)
- [Risk metrics](risk-metrics.md)
- [Risk classification](risk-classification.md)
- [Lead-braking scenario](lead-braking-scenario.md)
- [Complete simulation runner](simulation-runner.md)

## Strategies and evaluation

- [Warning Only strategy](warning-only-strategy.md)
- [Baseline AEB strategy](aeb-strategy.md)
- [Strategy evaluation and regression scenarios](strategy-evaluation.md)

## Delivery and experiments

- [FastAPI simulation API](simulation-api.md)
- [Public Docker/Render deployment](public-deployment.md)
- [Dashboard workflow](dashboard-workflow.md)
- [Playback and visualization](simulation-playback.md)
- [Integration hardening](integration-hardening.md)
- [Optional SUMO adapter exploration](sumo-adapter-exploration.md)
- [Development roadmap](roadmap.md)

The application release version is `1.0.0`. Serialized simulation and evaluation
responses continue to use schema version `1.0`; these versions are deliberately
independent.
