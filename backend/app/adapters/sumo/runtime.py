"""Supported SUMO binary discovery and version inspection."""

from __future__ import annotations

import importlib.util
import os
import re
import shutil
import subprocess
import sys
from collections.abc import Mapping
from importlib import import_module
from pathlib import Path
from types import ModuleType

from .contracts import SUPPORTED_SUMO_VERSION, SumoRuntimeInfo
from .exceptions import SumoConfigurationError

_VERSION_PATTERN = re.compile(
    r"\b(?:Version\s+|sumo\s+)([0-9]+(?:\.[0-9]+)+)",
    re.IGNORECASE,
)


def _binary_in_home(home: str) -> Path:
    name = "sumo.exe" if os.name == "nt" else "sumo"
    return Path(home) / "bin" / name


def _optional_package_home() -> str | None:
    if importlib.util.find_spec("sumo") is None:
        return None
    package = import_module("sumo")
    value = getattr(package, "SUMO_HOME", None)
    return value if isinstance(value, str) and value else None


def load_traci_client() -> ModuleType:
    """Load TraCI from either a standalone install or eclipse-sumo's tools."""

    if importlib.util.find_spec("traci") is not None:
        return import_module("traci")

    package_home = _optional_package_home()
    if package_home is not None:
        tools_directory = Path(package_home) / "tools"
        if tools_directory.is_dir() and str(tools_directory) not in sys.path:
            sys.path.append(str(tools_directory))
        if importlib.util.find_spec("traci") is not None:
            return import_module("traci")
    raise ModuleNotFoundError("the optional TraCI Python client is not installed")


def _resolve_binary(
    explicit_binary: str | os.PathLike[str] | None,
    environment: Mapping[str, str],
) -> tuple[Path | None, str | None, str | None]:
    if explicit_binary is not None:
        path = Path(explicit_binary)
        if not path.is_file():
            raise SumoConfigurationError(f"explicit SUMO binary does not exist: {path}")
        return path.resolve(), "explicit", None

    configured_binary = environment.get("SUMO_BINARY")
    if configured_binary:
        path = Path(configured_binary)
        if not path.is_file():
            raise SumoConfigurationError(
                f"SUMO_BINARY does not identify a file: {configured_binary}"
            )
        return path.resolve(), "SUMO_BINARY", None

    package_home = _optional_package_home()
    if package_home:
        path = _binary_in_home(package_home)
        if path.is_file():
            return path.resolve(), "eclipse-sumo", None

    configured_home = environment.get("SUMO_HOME")
    if configured_home:
        path = _binary_in_home(configured_home)
        if path.is_file():
            return path.resolve(), "SUMO_HOME", None

    located = shutil.which("sumo")
    if located:
        return Path(located).resolve(), "PATH", None
    return None, None, "SUMO binary was not found"


def inspect_sumo_runtime(
    binary: str | os.PathLike[str] | None = None,
    *,
    environment: Mapping[str, str] | None = None,
) -> SumoRuntimeInfo:
    """Inspect the supported headless SUMO runtime without starting TraCI."""

    resolved, source, reason = _resolve_binary(
        binary,
        os.environ if environment is None else environment,
    )
    if resolved is None:
        return SumoRuntimeInfo(False, None, None, None, reason)
    if resolved.stem.lower() == "sumo-gui":
        raise SumoConfigurationError("sumo-gui is outside the headless adapter scope")
    try:
        load_traci_client()
    except ModuleNotFoundError:
        return SumoRuntimeInfo(
            False,
            None,
            str(resolved),
            source,
            "the optional TraCI Python client is not installed",
        )
    try:
        completed = subprocess.run(
            [str(resolved), "--version"],
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError) as error:
        return SumoRuntimeInfo(
            False,
            None,
            str(resolved),
            source,
            f"SUMO version inspection failed: {error}",
        )
    match = _VERSION_PATTERN.search(f"{completed.stdout}\n{completed.stderr}")
    if match is None:
        return SumoRuntimeInfo(
            False,
            None,
            str(resolved),
            source,
            "SUMO version output was not recognized",
        )
    version = match.group(1)
    if version != SUPPORTED_SUMO_VERSION:
        return SumoRuntimeInfo(
            False,
            version,
            str(resolved),
            source,
            f"SUMO {version} is unsupported; expected {SUPPORTED_SUMO_VERSION}",
        )
    return SumoRuntimeInfo(True, version, str(resolved), source, None)
