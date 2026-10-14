from datetime import timedelta
from decimal import Decimal

import pytest
from redis import RedisError

from delivery_service.services.rate import RateService


class FakeRedis:
    def __init__(self, to_fail: bool = False) -> None:
        self._to_fail = to_fail
        self.data: dict[str, str] = {}

    async def get(self, key: str) -> str | None:
        if self._to_fail:
            raise RedisError
        return self.data.get(key)

    async def setex(self, key: str, ttl: int, value: str) -> None:
        if self._to_fail:
            raise RedisError
        self.data[key] = value


class FakeCbrClient:
    def __init__(self, usd_rate_str: str) -> None:
        self._usd_rate = Decimal(usd_rate_str)
        self.calls = 0

    async def fetch_usd_rate(self) -> Decimal:
        self.calls += 1
        return self._usd_rate


KEY_RATE = "usd_rate"
VALUE_RATE = "81.9230"


@pytest.fixture
def redis_good() -> FakeRedis:
    return FakeRedis(to_fail=False)


@pytest.fixture
def redis_fail() -> FakeRedis:
    return FakeRedis(to_fail=True)


@pytest.fixture
def cbr() -> FakeCbrClient:
    return FakeCbrClient(VALUE_RATE)


async def test_get_usd_rate_without_cache(cbr: FakeCbrClient, redis_good: FakeRedis) -> None:

    service = RateService(cbr, redis_good, ttl=timedelta(minutes=30))

    usd_rate = await service.get_usd_rate()

    assert usd_rate == Decimal(VALUE_RATE)
    assert redis_good.data[KEY_RATE] == VALUE_RATE
    assert cbr.calls == 1


async def test_get_usd_rate_with_cache(cbr: FakeCbrClient, redis_good: FakeRedis) -> None:

    service = RateService(cbr, redis_good, ttl=timedelta(minutes=30))

    redis_good.data[KEY_RATE] = VALUE_RATE

    usd_rate = await service.get_usd_rate()

    assert usd_rate == Decimal(VALUE_RATE)
    assert redis_good.data[KEY_RATE] == VALUE_RATE
    assert cbr.calls == 0


async def test_get_usd_rate_redis_fail(cbr: FakeCbrClient, redis_fail: FakeRedis) -> None:

    service = RateService(cbr, redis_fail, ttl=timedelta(minutes=30))

    usd_rate = await service.get_usd_rate()

    assert usd_rate == Decimal(VALUE_RATE)
    assert cbr.calls == 1
