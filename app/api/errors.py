from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.errors import HarborError


def error_payload(
    code: str,
    message: str,
    details: list[dict[str, str]],
) -> dict[str, object]:
    return {"error": {"code": code, "message": message, "details": details}}


def stringify_details(details: list[dict[str, Any]]) -> list[dict[str, str]]:
    return [{str(key): str(value) for key, value in item.items()} for item in details]


async def harbor_error_handler(_request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, HarborError):
        raise exc
    return JSONResponse(
        status_code=exc.status_code,
        content=error_payload(exc.code, exc.message, stringify_details(exc.details)),
    )


async def http_exception_handler(_request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, StarletteHTTPException):
        raise exc
    code = "HTTP_ERROR"
    if exc.status_code == 401:
        code = "UNAUTHORIZED"
    elif exc.status_code == 404:
        code = "NOT_FOUND"
    elif exc.status_code == 413:
        code = "PAYLOAD_TOO_LARGE"
    message = str(exc.detail) if exc.detail else "Request failed"
    return JSONResponse(
        status_code=exc.status_code,
        content=error_payload(code, message, []),
    )


async def validation_error_handler(_request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, RequestValidationError):
        raise exc
    details = []
    for error in exc.errors():
        location = ".".join(str(part) for part in error.get("loc", []))
        details.append(
            {"field": location, "message": error.get("msg", "Invalid value")}
        )
    return JSONResponse(
        status_code=422,
        content=error_payload("VALIDATION_ERROR", "Invalid input", details),
    )


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(HarborError, harbor_error_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
