from datetime import UTC, datetime, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from loguru import logger

from delivery_service.clients.exceptions import RateUnavailableError
from delivery_service.services.delivery_cost import DeliveryCostService


async def fill_missing_cost_job(service: DeliveryCostService) -> None:
    try:
        await service.fill_missing_costs()
    except RateUnavailableError:
        logger.warning("Delivery cost calculation skipped: USD rate unavailable")


def create_scheduler(service: DeliveryCostService, interval: timedelta) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone=UTC)
    scheduler.add_job(
        fill_missing_cost_job,
        trigger=IntervalTrigger(seconds=int(interval.total_seconds())),
        args=[service],
        id="fill_missing_costs",
        max_instances=1,
        coalesce=True,
        next_run_time=datetime.now(UTC),
    )

    return scheduler
