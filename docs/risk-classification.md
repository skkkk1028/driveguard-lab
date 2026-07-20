# Risk Classification

Stage 5 adds a deterministic classifier that converts precomputed kinematic
metrics into a `RiskLevel`. The result is intended for simulation experiments and
later dashboard presentation; it does not select or execute a driving action.

## Thresholds

All `RiskThresholds` fields use seconds:

| Field | Default |
| --- | ---: |
| `emergency_ttc_s` | 1.0 |
| `danger_ttc_s` | 2.0 |
| `caution_ttc_s` | 4.0 |
| `danger_thw_s` | 1.0 |
| `caution_thw_s` | 2.0 |

Every threshold must be finite and strictly positive. TTC thresholds must satisfy
`emergency_ttc_s < danger_ttc_s < caution_ttc_s`, and THW thresholds must satisfy
`danger_thw_s < caution_thw_s`. Invalid values are rejected rather than reordered
or repaired. `RiskThresholds` instances are immutable.

## Decision table

Rules are evaluated from top to bottom. The first matching row determines the
result, so a higher-risk match always overrides lower-risk matches. Every
threshold boundary is inclusive (`<=`); no hidden epsilon is used.

| Priority | Level | Match when any condition is true |
| ---: | --- | --- |
| 1 | Emergency | `gap_m <= 0`, or applicable TTC `<= emergency_ttc_s` |
| 2 | Danger | applicable TTC `<= danger_ttc_s`; or `relative_speed_mps > 0` and `gap_m <= ego_stopping_distance_m`; or applicable THW `<= danger_thw_s` |
| 3 | Caution | applicable TTC `<= caution_ttc_s`, or applicable THW `<= caution_thw_s` |
| 4 | Safe | no preceding rule matches |

`ttc_s=None` skips only TTC conditions, and `thw_s=None` skips only THW
conditions. Other available metrics are still evaluated. The stopping-distance
condition applies only while ego is closing on lead (`relative_speed_mps > 0`),
because a large theoretical ego stopping distance alone does not imply that two
vehicles with a constant or increasing gap are on a collision course.

## Collision state and limitations

`is_collision` reports a basic collision state when `gap_m <= 0`. Under the
current point-vehicle model this means the two longitudinal reference points touch
or overlap. It does not account for bumpers, vehicle dimensions, lateral geometry,
or collision events.

The default thresholds and decision rules are DriveGuard Lab v1.0 teaching and
simulation heuristics. They are not an industry standard, legal threshold, OEM
calibration, AEB guarantee, road-tested result, or functional-safety certification.
Neither `Safe` nor `Emergency` is a real-vehicle control instruction. These results
must not be used to control a real vehicle.
