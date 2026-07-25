"""OpenAPI, documentation, health, and CORS delivery tests."""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_openapi_and_swagger_are_enabled_but_redoc_remains_disabled() -> None:
    swagger = client.get("/docs")
    openapi = client.get("/openapi.json")

    assert swagger.status_code == 200
    assert "swagger-ui" in swagger.text
    assert openapi.status_code == 200
    assert set(openapi.json()["paths"]) >= {
        "/health",
        "/api/v1/simulations",
        "/api/v1/evaluations",
        "/api/v1/regression-scenarios",
        "/api/v1/regression-suites",
    }
    assert client.get("/redoc").status_code == 404


def test_openapi_registers_domain_response_and_error_schemas() -> None:
    document = client.get("/openapi.json").json()
    simulation_post = document["paths"]["/api/v1/simulations"]["post"]

    assert simulation_post["responses"]["200"]["content"]["application/json"][
        "schema"
    ]["$ref"].endswith("/SimulationRunResponse")
    assert simulation_post["responses"]["422"]["content"]["application/json"][
        "schema"
    ]["$ref"].endswith("/ApiErrorResponse")
    assert set(document["components"]["schemas"]["DrivingStrategy"]["enum"]) == {
        "no_assist",
        "warning_only",
        "aeb",
    }


@pytest.mark.parametrize(
    "origin",
    ["http://localhost:5173", "http://127.0.0.1:5173"],
)
def test_local_frontend_origins_are_allowed(origin: str) -> None:
    response = client.options(
        "/api/v1/simulations",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == origin
    assert "POST" in response.headers["access-control-allow-methods"]
    assert "content-type" in response.headers["access-control-allow-headers"].lower()
    assert "access-control-allow-credentials" not in response.headers


def test_unlisted_cors_origin_is_rejected() -> None:
    response = client.options(
        "/api/v1/simulations",
        headers={
            "Origin": "https://example.com",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )

    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers


def test_health_contract_remains_unchanged() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "driveguard-api"}
