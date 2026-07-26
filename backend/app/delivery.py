"""Optional same-origin delivery of the production Dashboard build."""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

STATIC_DIRECTORY_ENV = "DRIVEGUARD_STATIC_DIR"


def mount_dashboard(
    application: FastAPI,
    directory: str | Path | None = None,
) -> None:
    """Mount a validated Vite build at the root path when configured.

    API and health routes must be registered before this catch-all mount. Local
    development leaves the environment variable unset and continues to use the
    separate Vite service.
    """

    configured = directory if directory is not None else os.getenv(STATIC_DIRECTORY_ENV)
    if configured is None:
        return
    static_root = Path(configured).expanduser().resolve()
    index_path = static_root / "index.html"
    if not static_root.is_dir() or not index_path.is_file():
        raise RuntimeError(
            f"{STATIC_DIRECTORY_ENV} must contain a production index.html: "
            f"{static_root}"
        )
    application.mount(
        "/",
        StaticFiles(directory=static_root, html=True),
        name="dashboard",
    )
