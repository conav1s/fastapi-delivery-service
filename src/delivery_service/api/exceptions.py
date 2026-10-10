from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from delivery_service.services.exceptions import PackageNotFoundError
from delivery_service.clients.exceptions import RateUnavailableError


async def package_not_found_handler(request: Request, exc: PackageNotFoundError) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": exc.message})


async def rate_unavailable_handler(request: Request, exc: RateUnavailableError) -> JSONResponse:
    return JSONResponse(status_code=503, content={"detail": exc.message})


def register_exception_handler(app: FastAPI) -> None:
    app.add_exception_handler(
        PackageNotFoundError,
        package_not_found_handler,  # type: ignore[arg-type]
    )

    app.add_exception_handler(
        RateUnavailableError,
        rate_unavailable_handler, # type: ignore[arg-type]
    )
