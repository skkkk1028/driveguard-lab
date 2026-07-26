"""Command-line interface for explicitly requested SUMO experiments."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from dataclasses import replace
from typing import TextIO

from app.domain import DrivingStrategy
from app.simulation import REGRESSION_SCENARIOS

from .adapter import probe_scenario_in_sumo, replay_scenario_in_sumo
from .exceptions import (
    SumoConfigurationError,
    SumoExecutionError,
    SumoUnavailableError,
)
from .runtime import inspect_sumo_runtime
from .serialization import to_sumo_json_compatible


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m app.adapters.sumo")
    parser.add_argument("--sumo-binary", default=None)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("doctor", help="inspect the supported SUMO runtime")
    for command in ("replay", "probe"):
        runner = subparsers.add_parser(command)
        runner.add_argument(
            "--scenario-id",
            required=True,
            choices=[scenario.scenario_id for scenario in REGRESSION_SCENARIOS],
        )
        runner.add_argument(
            "--strategy",
            required=True,
            choices=[strategy.value for strategy in DrivingStrategy],
        )
    return parser


def _print_json(value: object, *, stream: TextIO | None = None) -> None:
    output = stream or sys.stdout
    print(
        json.dumps(
            to_sumo_json_compatible(value),
            ensure_ascii=False,
            sort_keys=True,
        ),
        file=output,
    )


def main(argv: Sequence[str] | None = None) -> int:
    """Run one diagnostic, replay, or probe command."""

    arguments = _parser().parse_args(argv)
    try:
        if arguments.command == "doctor":
            runtime = inspect_sumo_runtime(arguments.sumo_binary)
            _print_json(runtime)
            return 0 if runtime.available else 2

        catalog_entry = next(
            scenario
            for scenario in REGRESSION_SCENARIOS
            if scenario.scenario_id == arguments.scenario_id
        )
        scenario = replace(
            catalog_entry.baseline_scenario,
            strategy=DrivingStrategy(arguments.strategy),
        )
        if arguments.command == "replay":
            report = replay_scenario_in_sumo(
                scenario,
                binary=arguments.sumo_binary,
            )
        else:
            report = probe_scenario_in_sumo(
                scenario,
                binary=arguments.sumo_binary,
            )
        _print_json(report)
        return 0
    except (SumoConfigurationError, SumoUnavailableError) as error:
        _print_json({"error": str(error)}, stream=sys.stderr)
        return 2
    except SumoExecutionError as error:
        _print_json({"error": str(error)}, stream=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
