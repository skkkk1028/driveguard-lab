"""Generate or verify deterministic API v1 contract fixtures."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = PROJECT_ROOT / "backend"
FIXTURE_ROOT = PROJECT_ROOT / "contracts" / "api-v1"


def _json_text(value: object) -> str:
    return json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    ) + "\n"


def _build_fixtures() -> dict[str, str]:
    sys.path.insert(0, str(BACKEND_ROOT))

    from fastapi.testclient import TestClient

    from app.domain import to_json_compatible
    from app.main import app
    from app.simulation import REGRESSION_SCENARIOS

    client = TestClient(app)
    catalog_response = client.get("/api/v1/regression-scenarios")

    catalog = {
        scenario.scenario_id: scenario for scenario in REGRESSION_SCENARIOS
    }
    simulation_scenario = catalog["aeb_avoids_collision"].baseline_scenario
    simulation_body = {
        "scenario": {
            **to_json_compatible(simulation_scenario),
            "strategy": "aeb",
        }
    }
    simulation_response = client.post(
        "/api/v1/simulations",
        json=simulation_body,
    )

    boundary_scenario = to_json_compatible(
        catalog["initial_emergency_and_boundaries"].baseline_scenario
    )
    if not isinstance(boundary_scenario, dict):
        raise TypeError("serialized regression scenario must be an object")
    boundary_scenario.pop("strategy")
    evaluation_response = client.post(
        "/api/v1/evaluations",
        json={"baseline_scenario": boundary_scenario},
    )

    limit_scenario: dict[str, Any] = {
        **simulation_body["scenario"],
        "simulation_step_s": 0.001,
        "max_simulation_time_s": 10.001,
    }
    limit_response = client.post(
        "/api/v1/simulations",
        json={"scenario": limit_scenario},
    )

    responses = {
        "regression-scenarios.json": catalog_response,
        "simulation-aeb.json": simulation_response,
        "evaluation-boundary.json": evaluation_response,
        "simulation-limit-error.json": limit_response,
    }
    unexpected = {
        name: response.status_code
        for name, response in responses.items()
        if response.status_code != (422 if name.endswith("error.json") else 200)
    }
    if unexpected:
        raise RuntimeError(f"unexpected fixture response status: {unexpected}")
    return {name: _json_text(response.json()) for name, response in responses.items()}


def _write(fixtures: dict[str, str]) -> int:
    FIXTURE_ROOT.mkdir(parents=True, exist_ok=True)
    for name, content in fixtures.items():
        (FIXTURE_ROOT / name).write_text(content, encoding="utf-8", newline="\n")
    print(f"Wrote {len(fixtures)} API contract fixtures to {FIXTURE_ROOT}")
    return 0


def _check(fixtures: dict[str, str]) -> int:
    mismatches = []
    for name, expected in fixtures.items():
        path = FIXTURE_ROOT / name
        actual = path.read_text(encoding="utf-8") if path.is_file() else None
        if actual != expected:
            mismatches.append(name)
    if mismatches:
        print(
            "API contract fixtures are missing or stale: " + ", ".join(mismatches),
            file=sys.stderr,
        )
        print(
            "Run scripts/api_contract_fixtures.py --write after an explicit "
            "contract review.",
            file=sys.stderr,
        )
        return 1
    print(f"Verified {len(fixtures)} API contract fixtures.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true", help="write the fixtures")
    mode.add_argument("--check", action="store_true", help="check for drift")
    arguments = parser.parse_args(argv)
    fixtures = _build_fixtures()
    return _write(fixtures) if arguments.write else _check(fixtures)


if __name__ == "__main__":
    raise SystemExit(main())
