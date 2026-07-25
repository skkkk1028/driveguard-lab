"""Stable HTTP error handling for invalid API requests."""

from collections.abc import Sequence
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from .schemas import ApiError, ApiErrorDetail, ApiErrorResponse

VALIDATION_ERROR_CODE = "validation_error"
SIMULATION_LIMIT_ERROR_CODE = "simulation_limit_exceeded"
_VALIDATION_ERROR_MESSAGE = "Request validation failed."


class ApiInputError(Exception):
    """Expected API-boundary error with a stable public representation."""

    def __init__(
        self,
        *,
        code: str,
        message: str,
        details: Sequence[ApiErrorDetail],
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = tuple(details)


def _error_response(
    *,
    code: str,
    message: str,
    details: Sequence[ApiErrorDetail],
) -> JSONResponse:
    payload = ApiErrorResponse(
        error=ApiError(
            code=code,
            message=message,
            details=list(details),
        )
    )
    return JSONResponse(status_code=422, content=payload.model_dump(mode="json"))


def _validation_detail(error: dict[str, Any]) -> ApiErrorDetail:
    location = [part for part in error.get("loc", ()) if isinstance(part, (str, int))]
    return ApiErrorDetail(
        location=location,
        message=str(error.get("msg", "Invalid value.")),
        error_type=str(error.get("type", "value_error")),
    )


async def request_validation_error_handler(
    request: Request,
    exception: Exception,
) -> JSONResponse:
    """Normalize FastAPI and Pydantic request errors into one envelope."""

    del request
    if not isinstance(exception, RequestValidationError):
        raise TypeError("exception must be RequestValidationError")
    return _error_response(
        code=VALIDATION_ERROR_CODE,
        message=_VALIDATION_ERROR_MESSAGE,
        details=[_validation_detail(error) for error in exception.errors()],
    )


async def api_input_error_handler(
    request: Request,
    exception: Exception,
) -> JSONResponse:
    """Serialize expected domain and simulation-limit input failures."""

    del request
    if not isinstance(exception, ApiInputError):
        raise TypeError("exception must be ApiInputError")
    return _error_response(
        code=exception.code,
        message=exception.message,
        details=exception.details,
    )


def register_error_handlers(app: FastAPI) -> None:
    """Register stable request-error handlers on the application."""

    app.add_exception_handler(RequestValidationError, request_validation_error_handler)
    app.add_exception_handler(ApiInputError, api_input_error_handler)
