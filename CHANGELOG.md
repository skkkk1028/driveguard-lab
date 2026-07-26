# Changelog

All notable changes to DriveGuard Lab are documented in this file. The project
uses semantic versioning for application releases; simulation response contracts
retain their own independent schema version.

## [1.0.0] - 2026-07-26

### Added

- Deterministic one-dimensional vehicle dynamics, collision-risk metrics, and
  centralized heuristic risk classification.
- Lead-vehicle emergency-braking scenarios with No Assist, Warning Only, and
  baseline AEB strategies.
- Three-strategy evaluation, six deterministic regression scenarios, immutable
  results, ordered events, and raw intervention comparisons.
- Versioned synchronous FastAPI endpoints with strict request validation and a
  stable 422 error envelope.
- Chinese React Dashboard for configuration, summaries, discrete playback,
  event seeking, and linked SVG charts.
- Optional isolated Eclipse SUMO 1.27.1 replay and native-probe experiments.
- Runtime successful-response validation, shared API v1 fixtures, expanded
  integration invariants, and separate base/SUMO verification profiles.
- Apache-2.0 licensing, release documentation, package-build checks, and CI-ready
  Python/Node validation workflows.
- Same-origin Dashboard/API static delivery, a non-root multi-stage production
  container, and a Render Blueprint for a fixed public HTTPS endpoint.

### Changed

- Switched playback from an ego-fixed relative road view to a fixed
  ground-coordinate view where both vehicles follow their absolute positions,
  anchored illustrative bodies outward from point-vehicle contact references so
  positive gaps remain visibly separated, and separated coincident TTC/THW
  threshold labels to keep SVG annotations readable.

### Safety and modeling boundary

- DriveGuard Lab is a teaching and research simulator, not a safety-certified
  product or real-vehicle controller.
- Application version `1.0.0` does not change simulation response schema `1.0`.
