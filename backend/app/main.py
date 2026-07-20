"""FastAPI entry point for DriveGuard Lab."""

from typing import Literal, TypedDict

from fastapi import FastAPI


class HealthResponse(TypedDict):
    """Shape of the health-check response."""

    status: Literal["ok"]
    service: Literal["driveguard-api"]


app = FastAPI(
    title="DriveGuard Lab API",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)


@app.get("/health")
def health() -> HealthResponse:
    """Report that the API process is available."""

    return {"status": "ok", "service": "driveguard-api"}
