from loguru import logger
from httpx import AsyncClient, HTTPError

from .exceptions import RateUnavailableError


class CbrClient:
    def __init__(self, url: str, http_client: AsyncClient) -> None:
        self._url = url
        self._client = http_client

    async def fetch_usd_rate(self) -> str:
        try:
            response = await self._client.get(self._url)
            response.raise_for_status()
            data = response.json()

            usd_rate = data["Valute"]["USD"]["Value"]
        except (HTTPError, ValueError, KeyError) as err:
            logger.warning("Failed to fetch USD rate from {}: {!r}", self._url, err)
            raise RateUnavailableError("Failed to obtain CBR rate") from err

        return str(usd_rate)
