from decimal import Decimal, InvalidOperation

from httpx import AsyncClient, HTTPError
from loguru import logger

from .exceptions import (
    ExchangerServiceJSONKeyNotFoundError,
    ExchangerServiceRateValueError,
    ExchangerServiceUnavailableError,
)


class CbrClient:
    def __init__(self, url: str, http_client: AsyncClient) -> None:
        self._url = url
        self._client = http_client

    async def fetch_usd_rate(self) -> Decimal:
        try:
            response = await self._client.get(self._url)
            response.raise_for_status()
            data = response.json()

            json_value = data["Valute"]["USD"]["Value"]
            usd_rate = Decimal(str(json_value))
        except HTTPError as err:
            logger.warning("Failed to fetch USD rate from {}: {!r}", self._url, err)
            raise ExchangerServiceUnavailableError(self._url) from err
        except KeyError as err:
            logger.warning("Failed to extract rate from JSON by key: {}", err.args[0])
            raise ExchangerServiceJSONKeyNotFoundError("USD") from err
        except InvalidOperation as err:
            logger.warning("Rate value {} is not a number", json_value)
            raise ExchangerServiceRateValueError(json_value) from err

        return usd_rate
