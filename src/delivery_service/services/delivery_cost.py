from decimal import Decimal

from loguru import logger
from sqlalchemy import update, SQLColumnExpression
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from delivery_service.db.models import Package
from .rate import RateService

K_WEIGHT = Decimal("0.5")
K_CONTENT = Decimal("0.01")


def calc_delivery_cost[T: (Decimal, SQLColumnExpression[Decimal])](
    weight: T, content_cost: T, usd_rate: Decimal
) -> T:
    """Delivery cost in RUB: (weight * K_WEIGHT + content_cost * K_CONTENT) * usd_rate."""
    return (K_WEIGHT * weight + K_CONTENT * content_cost) * usd_rate


class DeliveryCostService:
    def __init__(
        self, session_factory: async_sessionmaker[AsyncSession], rate_service: RateService
    ) -> None:
        self._session_factory = session_factory
        self._rate_service = rate_service

    async def fill_missing_costs(self) -> int:
        usd_rate = await self._rate_service.get_usd_rate()

        async with self._session_factory() as session, session.begin():
            stmt = (
                update(Package)
                .where(Package.delivery_cost_rub.is_(None))
                .values(
                    exchange_rate=usd_rate,
                    delivery_cost_rub=calc_delivery_cost(
                        Package.weight, Package.content_cost_usd, usd_rate
                    ),
                )
            )

            conn = await session.connection()
            result = await conn.execute(stmt)

            updated = result.rowcount

        logger.info("Priced {} packages at rate {}", updated, usd_rate)

        return updated
