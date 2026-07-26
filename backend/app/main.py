"""FastAPI entry point for DriveGuard Lab."""

from typing import Literal

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing_extensions import TypedDict

from app import APP_VERSION
from app.api import router as simulation_router
from app.api.errors import register_error_handlers
from app.delivery import mount_dashboard


class HealthResponse(TypedDict):
    """Shape of the health-check response."""

    status: Literal["ok"]
    service: Literal["driveguard-api"]


app = FastAPI(
    title="DriveGuard Lab API",
    version=APP_VERSION,
    description=(
        "Deterministic one-dimensional collision-risk simulation API for "
        "teaching and research. Not a safety-certified vehicle controller."
    ),
    docs_url="/docs",
    redoc_url=None,
    openapi_url="/openapi.json",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)
register_error_handlers(app)
app.include_router(simulation_router)


@app.get("/health")
def health() -> HealthResponse:
    """Report that the API process is available."""

    return {"status": "ok", "service": "driveguard-api"}


mount_dashboard(app)
