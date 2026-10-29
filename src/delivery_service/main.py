from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import timedelta

from fastapi import FastAPI
from httpx import AsyncClient
from langchain_groq import ChatGroq
from langchain_qdrant import QdrantVectorStore
from loguru import logger
from qdrant_client import QdrantClient
from redis.asyncio import Redis

from delivery_service.api.exceptions import register_exception_handler
from delivery_service.api.router import router, router_debug, router_support
from delivery_service.clients.cbr import CbrClient
from delivery_service.clients.embeddings import FastEmbedEmbeddings
from delivery_service.services.delivery_cost import DeliveryCostService
from delivery_service.services.rate import RateService
from delivery_service.services.support import SupportService

from .config import settings
from .db.session import session_factory
from .logging_setup import setup_logging
from .scheduler import create_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
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

    qdrant = QdrantClient(url=settings.qdrant.url, trust_env=False)
    groq_http = AsyncClient(proxy=settings.groq.proxy_url, timeout=settings.groq.timeout_s)

    app.state.support_service = SupportService(
        knowledge_base=QdrantVectorStore(
            client=qdrant,
            collection_name=settings.qdrant.collection,
            embedding=FastEmbedEmbeddings(
                settings.knowledge_base.embedding_model,
                cache_dir=settings.knowledge_base.embedding_cache_dir,
            ),
            validate_collection_config=False,
        ),
        llm=_create_llm(groq_http),
        top_k=settings.knowledge_base.top_k,
        min_score=settings.knowledge_base.min_score,
    )

    yield

    scheduler.shutdown()
    qdrant.close()
    await groq_http.aclose()
    await app.state.redis.aclose()
    await app.state.http.aclose()
    logger.info("Shutting down")


def _create_llm(http_client: AsyncClient) -> ChatGroq | None:
    if settings.groq.api_key is None:
        logger.warning("GROQ_API_KEY is not set: support answers are disabled")
        return None

    return ChatGroq(
        model_name=settings.groq.model,
        api_key=settings.groq.api_key,
        temperature=0,
        reasoning_format=(
            None if settings.groq.reasoning_format == "none" else settings.groq.reasoning_format
        ),
        max_retries=2,
        http_async_client=http_client,
    )


app = FastAPI(lifespan=lifespan)


register_exception_handler(app)
app.include_router(router)
app.include_router(router_support)

if settings.app.debug:
    app.include_router(router_debug)
