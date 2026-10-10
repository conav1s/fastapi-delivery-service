from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import timedelta

from fastapi import FastAPI
from redis.asyncio import Redis
from httpx import AsyncClient
from loguru import logger

from .config import settings
from .logging_setup import setup_logging
from .scheduler import create_scheduler
from .db.session import session_factory
from delivery_service.api.router import router, router_debug
from delivery_service.api.exceptions import register_exception_handler
from delivery_service.clients.cbr import CbrClient
from delivery_service.services.rate import RateService
from delivery_service.services.delivery_cost import DeliveryCostService


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    setup_logging()
    logger.info("Starting delivery service")

    httpx_client = AsyncClient()
    redis = Redis.from_url(settings.redis.url, decode_responses=True)

    app.state.http = httpx_client
    app.state.redis = redis

    delivery_cost_service = DeliveryCostService(
        session_factory=session_factory,
        rate_service=RateService(
            cbr=CbrClient(url=str(settings.exchanger.source_url), http_client=httpx_client),
            redis=redis,
            ttl=timedelta(hours=settings.exchanger.refresh_hours),
        ),
    )

    app.state.delivery_cost_service = delivery_cost_service

    scheduler = create_scheduler(
        service=delivery_cost_service,
        interval=timedelta(minutes=settings.app.delivery_cost_update_interval_min),
    )

    scheduler.start()

    yield

    scheduler.shutdown()
    await app.state.redis.aclose()
    await app.state.http.aclose()
    logger.info("Shutting down")


app = FastAPI(lifespan=lifespan)


register_exception_handler(app)
app.include_router(router)

if settings.app.debug:
    app.include_router(router_debug)
