"""Validate DriveGuard Lab v1.0 release metadata and local documentation links."""

from __future__ import annotations

import argparse
import json
import re
import sys
import tarfile
import tomllib
import urllib.parse
import zipfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = PROJECT_ROOT / "backend"
RELEASE_VERSION = "1.0.0"
SCHEMA_VERSION = "1.0"
MARKDOWN_LINK = re.compile(r"!?\[[^]]*]\(([^)]+)\)")


def _read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def _expect(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def _check_versions(errors: list[str]) -> None:
    pyproject = tomllib.loads(
        (BACKEND_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    )
    frontend = _read_json(PROJECT_ROOT / "frontend" / "package.json")
    lockfile = _read_json(PROJECT_ROOT / "frontend" / "package-lock.json")
    if not isinstance(frontend, dict) or not isinstance(lockfile, dict):
        errors.append("frontend package metadata must be JSON objects")
        return

    _expect(
        errors,
        pyproject["project"]["version"] == RELEASE_VERSION,
        "backend project version is not 1.0.0",
    )
    _expect(
        errors,
        pyproject["project"]["license"] == "Apache-2.0",
        "backend license metadata is not Apache-2.0",
    )
    _expect(
        errors,
        frontend.get("version") == RELEASE_VERSION,
        "frontend package version is not 1.0.0",
    )
    _expect(
        errors,
        frontend.get("license") == "Apache-2.0",
        "frontend license metadata is not Apache-2.0",
    )
    _expect(
        errors,
        lockfile.get("version") == RELEASE_VERSION,
        "frontend lockfile version is not 1.0.0",
    )
    packages = lockfile.get("packages")
    root_package = packages.get("") if isinstance(packages, dict) else None
    _expect(
        errors,
        isinstance(root_package, dict)
        and root_package.get("version") == RELEASE_VERSION,
        "frontend lockfile root package version is not 1.0.0",
    )

    sys.path.insert(0, str(BACKEND_ROOT))
    from app import APP_VERSION
    from app.domain import SIMULATION_SCHEMA_VERSION
    from app.main import app

    _expect(
        errors,
        APP_VERSION == RELEASE_VERSION,
        "backend APP_VERSION is not 1.0.0",
    )
    _expect(
        errors,
        app.openapi()["info"]["version"] == RELEASE_VERSION,
        "OpenAPI info.version is not 1.0.0",
    )
    _expect(
        errors,
        SIMULATION_SCHEMA_VERSION == SCHEMA_VERSION,
        "simulation schema version changed from 1.0",
    )


def _markdown_files() -> tuple[Path, ...]:
    roots = [
        PROJECT_ROOT / "README.md",
        PROJECT_ROOT / "CHANGELOG.md",
        PROJECT_ROOT / "THIRD_PARTY_NOTICES.md",
        BACKEND_ROOT / "README.md",
        PROJECT_ROOT / "frontend" / "README.md",
    ]
    roots.extend(sorted((PROJECT_ROOT / "docs").glob("*.md")))
    return tuple(path for path in roots if path.is_file())


def _local_link_target(raw_target: str) -> str | None:
    target = raw_target.strip()
    if target.startswith("<") and ">" in target:
        target = target[1 : target.index(">")]
    else:
        target = target.split(maxsplit=1)[0]
    if not target or target.startswith("#"):
        return None
    parsed = urllib.parse.urlsplit(target)
    if parsed.scheme or parsed.netloc:
        return None
    return urllib.parse.unquote(parsed.path)


def _check_markdown_links(errors: list[str]) -> None:
    for source in _markdown_files():
        content = source.read_text(encoding="utf-8")
        for match in MARKDOWN_LINK.finditer(content):
            target = _local_link_target(match.group(1))
            if target is None:
                continue
            resolved = (source.parent / target).resolve()
            if not resolved.exists():
                relative_source = source.relative_to(PROJECT_ROOT)
                errors.append(f"broken local link in {relative_source}: {target}")


def _check_release_files(errors: list[str], *, require_ready: bool) -> None:
    license_path = PROJECT_ROOT / "LICENSE"
    _expect(errors, license_path.is_file(), "LICENSE is missing")
    if license_path.is_file():
        license_text = license_path.read_text(encoding="utf-8")
        _expect(
            errors,
            "Apache License" in license_text and "Version 2.0" in license_text,
            "LICENSE is not Apache License 2.0 text",
        )
    for name in ("CHANGELOG.md", "THIRD_PARTY_NOTICES.md"):
        _expect(errors, (PROJECT_ROOT / name).is_file(), f"{name} is missing")
    readiness_path = PROJECT_ROOT / "docs" / "release-readiness.md"
    _expect(errors, readiness_path.is_file(), "release readiness document is missing")
    if require_ready:
        roadmap = (PROJECT_ROOT / "docs" / "roadmap.md").read_text(encoding="utf-8")
        _expect(
            errors,
            "| 16 | v1.0 documentation and release readiness | Complete |" in roadmap,
            "roadmap does not mark Stage 16 complete",
        )
    if readiness_path.is_file() and require_ready:
        readiness = readiness_path.read_text(encoding="utf-8")
        _expect(
            errors,
            "Status: ready for repository review." in readiness,
            "release readiness status is not ready for repository review",
        )
        _expect(
            errors,
            "- [ ]" not in readiness,
            "release readiness checklist still has incomplete items",
        )


def _check_workflows(errors: list[str]) -> None:
    workflow_root = PROJECT_ROOT / ".github" / "workflows"
    ci_path = workflow_root / "ci.yml"
    sumo_path = workflow_root / "sumo.yml"
    _expect(errors, ci_path.is_file(), "base CI workflow is missing")
    _expect(errors, sumo_path.is_file(), "strict SUMO workflow is missing")
    if not ci_path.is_file() or not sumo_path.is_file():
        return
    ci = ci_path.read_text(encoding="utf-8")
    sumo = sumo_path.read_text(encoding="utf-8")
    combined = ci + sumo
    for action in (
        "actions/checkout@v6",
        "actions/setup-python@v6",
        "actions/setup-node@v6",
    ):
        _expect(errors, action in combined, f"workflow action is missing: {action}")
    _expect(
        errors,
        'python-version: ["3.11", "3.14"]' in ci,
        "base CI Python matrix is not 3.11 and 3.14",
    )
    _expect(errors, 'node-version: "24"' in ci, "base CI does not use Node 24")
    _expect(
        errors,
        "workflow_dispatch:" in sumo and 'python-version: "3.14"' in sumo,
        "strict SUMO workflow is not a manual Python 3.14 gate",
    )
    _expect(
        errors,
        "contents: write" not in combined
        and "packages: write" not in combined
        and "id-token: write" not in combined,
        "workflow requests release or publication permissions",
    )
    _expect(
        errors,
        "docker build --tag driveguard-lab:ci ." in ci,
        "base CI does not build the production deployment image",
    )


def _check_deployment(errors: list[str]) -> None:
    dockerfile_path = PROJECT_ROOT / "Dockerfile"
    dockerignore_path = PROJECT_ROOT / ".dockerignore"
    render_path = PROJECT_ROOT / "render.yaml"
    for path in (dockerfile_path, dockerignore_path, render_path):
        _expect(errors, path.is_file(), f"deployment file is missing: {path.name}")
    if not dockerfile_path.is_file() or not render_path.is_file():
        return
    dockerfile = dockerfile_path.read_text(encoding="utf-8")
    render = render_path.read_text(encoding="utf-8")
    for fragment in (
        "FROM node:24-alpine AS frontend-build",
        "FROM python:3.14-slim AS runtime",
        "DRIVEGUARD_STATIC_DIR=/opt/driveguard/static",
        "USER 10001",
        "--host 0.0.0.0",
        "${PORT:-10000}",
    ):
        _expect(errors, fragment in dockerfile, f"Dockerfile is missing: {fragment}")
    for fragment in (
        "type: web",
        "runtime: docker",
        "plan: free",
        "region: singapore",
        "healthCheckPath: /health",
        "autoDeployTrigger: checksPass",
    ):
        _expect(errors, fragment in render, f"render.yaml is missing: {fragment}")


def _check_artifacts(errors: list[str], artifact_root: Path) -> None:
    wheels = tuple(artifact_root.glob("driveguard_api-1.0.0-*.whl"))
    sdists = tuple(artifact_root.glob("driveguard_api-1.0.0.tar.gz"))
    _expect(errors, len(wheels) == 1, "expected one driveguard-api 1.0.0 wheel")
    _expect(errors, len(sdists) == 1, "expected one driveguard-api 1.0.0 sdist")
    if len(wheels) == 1:
        with zipfile.ZipFile(wheels[0]) as archive:
            names = archive.namelist()
            metadata_name = next(
                (name for name in names if name.endswith(".dist-info/METADATA")),
                None,
            )
            _expect(errors, metadata_name is not None, "wheel METADATA is missing")
            if metadata_name is not None:
                metadata = archive.read(metadata_name).decode("utf-8")
                _expect(errors, "Version: 1.0.0" in metadata, "wheel version is wrong")
                _expect(
                    errors,
                    "License-Expression: Apache-2.0" in metadata,
                    "wheel license expression is wrong",
                )
            _expect(
                errors,
                not any(
                    "__pycache__" in name or name.startswith("tests/")
                    for name in names
                ),
                "wheel contains tests or Python caches",
            )
            _expect(
                errors,
                "app/py.typed" in names,
                "wheel does not contain the PEP 561 marker",
            )
    if len(sdists) == 1:
        with tarfile.open(sdists[0], mode="r:gz") as archive:
            _expect(
                errors,
                any(name.endswith("/PKG-INFO") for name in archive.getnames()),
                "sdist PKG-INFO is missing",
            )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--artifacts",
        type=Path,
        help="also validate a directory containing built wheel and sdist artifacts",
    )
    parser.add_argument(
        "--allow-pending",
        action="store_true",
        help="skip only the final Ready/Complete status assertions",
    )
    arguments = parser.parse_args(argv)
    errors: list[str] = []
    _check_versions(errors)
    _check_release_files(errors, require_ready=not arguments.allow_pending)
    _check_markdown_links(errors)
    _check_workflows(errors)
    _check_deployment(errors)
    if arguments.artifacts is not None:
        _check_artifacts(errors, arguments.artifacts.resolve())
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("DriveGuard Lab v1.0 release metadata and documentation checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
