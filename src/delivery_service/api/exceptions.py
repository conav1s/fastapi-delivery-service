from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

from delivery_service.clients.exceptions import (
    ExchangerServiceJSONKeyNotFoundError,
    ExchangerServiceRateValueError,
    ExchangerServiceUnavailableError,
)
from delivery_service.exceptions import DomainError
from delivery_service.services.exceptions import (
    ExchangeRateUnavailableError,
    PackageNotFoundError,
    PackageTypeNotFoundError,
)

STATUS_BY_ERROR: dict[type[DomainError], int] = {
    ExchangerServiceUnavailableError: 503,
    ExchangerServiceJSONKeyNotFoundError: 502,
    ExchangerServiceRateValueError: 502,
    PackageNotFoundError: 404,
    PackageTypeNotFoundError: 422,
    ExchangeRateUnavailableError: 503,
}


async def domain_errors_handler(request: Request, exc: DomainError) -> JSONResponse:
    return JSONResponse(
        status_code=STATUS_BY_ERROR.get(type(exc), 500),
        content={
            "code": exc.code,
            "message": exc.message,
            "details": None,
        },
    )


async def request_validation_errors_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={
            "code": "validation_error",
            "message": "Invalid request",
            "details": exc.errors(),
        },
    )


async def starlette_http_errors_handler(request: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": "api_using_error",
            "message": exc.detail,
            "details": None,
        },
    )


async def uncaught_exceptions_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={
            "code": "internal_error",
            "message": "Server got uncaught exception. We are sorry!",
            "details": None,
        },
    )


def register_exception_handler(app: FastAPI) -> None:
    clients_exc_types = [
        ExchangerServiceUnavailableError,
        ExchangerServiceJSONKeyNotFoundError,
        ExchangerServiceRateValueError,
    ]

    services_exc_types = [
        PackageNotFoundError,
        PackageTypeNotFoundError,
    ]

    domain_exc_types = clients_exc_types + services_exc_types

    for exc_type in domain_exc_types:
        app.add_exception_handler(
            exc_type,
            domain_errors_handler,  # type: ignore[arg-type]
        )

    app.add_exception_handler(
        RequestValidationError,
        request_validation_errors_handler,  # type: ignore[arg-type]
    )
    app.add_exception_handler(
        HTTPException,
        starlette_http_errors_handler,  # type: ignore[arg-type]
    )
    app.add_exception_handler(
        Exception,
        uncaught_exceptions_handler,
    )
