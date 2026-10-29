import asyncio
from collections.abc import Callable, Mapping
import os

import pytest

_TEST_ENV = {
    "APP_DEBUG": "true",
    "POSTGRES_HOST": "localhost",
    "POSTGRES_PORT": "55432",
    "POSTGRES_USER": "test",
    "POSTGRES_PASSWORD": "test",
    "POSTGRES_DB": "delivery_test",
    "REDIS_HOST": "localhost",
    "REDIS_PORT": "6379",
    "REDIS_DB": "0",
}

for key, value in _TEST_ENV.items():
    os.environ.setdefault(key, value)


def pytest_asyncio_loop_factories(
    config: pytest.Config, item: pytest.Item
) -> Mapping[str, Callable[[], asyncio.AbstractEventLoop]]:
    """psycopg async mode does not work with ProactorEventLoop (the Windows default)."""
    return {"selector": asyncio.SelectorEventLoop}
