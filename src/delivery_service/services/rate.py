from datetime import timedelta
from decimal import Decimal

from loguru import logger
from redis.asyncio import Redis, RedisError

from delivery_service.clients.cbr import CbrClient
from delivery_service.clients.exceptions import ClientError

from .exceptions import RateUnevaluateError


class RateService:
    _KEY = "usd_rate"

    def __init__(self, cbr: CbrClient, redis: Redis, ttl: timedelta) -> None:
        self._redis = redis
        self._cbr = cbr
        self._ttl = int(ttl.total_seconds())

    async def get_usd_rate(self) -> Decimal:
        try:
            cached = await self._redis.get(self._KEY)
            if cached is not None:
                logger.debug("Rate is received from cache")
                return Decimal(str(cached))
        except RedisError as exc:
            logger.warning("Cache is unavailable: {}", exc)

        try:
            usd_rate = await self._cbr.fetch_usd_rate()
            logger.debug("Rate is received from CBR")
        except ClientError:
            logger.error("CBR exchanger service and redis cache is unavailable")
            raise RateUnevaluateError() from None

        try:
            await self._redis.setex(self._KEY, self._ttl, str(usd_rate))
        except RedisError as exc:
            logger.warning("Fail to update cache: {}", exc)

        return usd_rate
