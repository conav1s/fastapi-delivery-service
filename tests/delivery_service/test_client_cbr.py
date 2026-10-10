import httpx
import pytest

from delivery_service.clients.cbr import CbrClient
from delivery_service.clients.exceptions import RateUnavailableError


def handler_success(request: httpx.Request) -> httpx.Response:
    return httpx.Response(200, json={"Valute": {"USD": {"Value": 84.9048}}})


def handler_fail(request: httpx.Request) -> httpx.Response:
    return httpx.Response(500, json={})


def handler_unavailable(request: httpx.Request) -> httpx.Response:
    raise httpx.ConnectError("")


def handler_empty_json(request: httpx.Request) -> httpx.Response:
    return httpx.Response(200, json={})


async def test_fetch_usd_rate_success() -> None:
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler_success)) as http:
        client = CbrClient(
            url="https://cbr.test/daily.js",
            http_client=http,
        )

        assert await client.fetch_usd_rate() == "84.9048"


async def test_fetch_usd_rate_fail() -> None:
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler_fail)) as http:
        client = CbrClient(
            url="https://cbr.test/daily.js",
            http_client=http,
        )

        with pytest.raises(RateUnavailableError):
            await client.fetch_usd_rate()


async def test_fetch_usd_rate_unavailable() -> None:
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler_unavailable)) as http:
        client = CbrClient(
            url="https://cbr.test/daily.js",
            http_client=http,
        )

        with pytest.raises(RateUnavailableError):
            await client.fetch_usd_rate()


async def test_fetch_usd_rate_empty_json() -> None:
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler_empty_json)) as http:
        client = CbrClient(
            url="https://cbr.test/daily.js",
            http_client=http,
        )

        with pytest.raises(RateUnavailableError):
            await client.fetch_usd_rate()