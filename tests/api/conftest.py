from collections.abc import AsyncGenerator, Callable, Generator
from decimal import Decimal
from pathlib import Path

from alembic import command
from alembic.config import Config
import httpx
import pytest
from sqlalchemy import text

from delivery_service.config import settings
from delivery_service.db.session import engine, session_factory
from delivery_service.main import app
from delivery_service.services.delivery_cost import DeliveryCostService
from delivery_service.services.exceptions import ExchangeRateUnavailableError
from delivery_service.services.support import SupportAnswer, SupportService

type ClientFactory = Callable[[], httpx.AsyncClient]
type CostServiceInstaller = Callable[[Decimal | None], None]
type SupportServiceInstaller = Callable[[SupportAnswer | Exception], None]

ALEMBIC_INI = Path(__file__).resolve().parents[2] / "alembic.ini"


@pytest.fixture(scope="session", autouse=True)
def migrated_database() -> None:
    if not settings.postgres.db.endswith("_test"):
        pytest.exit(f"Not a test database: {settings.postgres.db!r}")
    command.upgrade(Config(str(ALEMBIC_INI)), "head")


@pytest.fixture(autouse=True)
async def clean_packages() -> AsyncGenerator[None]:
    yield
    async with engine.begin() as conn:
        await conn.execute(text("TRUNCATE packages RESTART IDENTITY"))
    await engine.dispose()


@pytest.fixture
async def make_client() -> AsyncGenerator[ClientFactory]:
    clients: list[httpx.AsyncClient] = []

    def factory() -> httpx.AsyncClient:
        client = httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test")
        clients.append(client)
        return client

    yield factory

    for client in clients:
        await client.aclose()


@pytest.fixture
async def client(make_client: ClientFactory) -> httpx.AsyncClient:
    return make_client()


class FakeRateService:
    def __init__(self, rate: Decimal | None) -> None:
        self._rate = rate

    async def get_usd_rate(self) -> Decimal:
        if self._rate is None:
            raise ExchangeRateUnavailableError()
        return self._rate


@pytest.fixture
def install_cost_service() -> Generator[CostServiceInstaller]:
    def install(rate: Decimal | None) -> None:
        app.state.delivery_cost_service = DeliveryCostService(
            session_factory=session_factory, rate_service=FakeRateService(rate)
        )

    yield install

    if hasattr(app.state, "delivery_cost_service"):
        del app.state.delivery_cost_service


class FakeSupportService:
    """Stands in for SupportService: RAG itself is covered by unit tests."""

    def __init__(self, outcome: SupportAnswer | Exception) -> None:
        self._outcome = outcome
        self.questions: list[str] = []

    async def answer(self, question: str) -> SupportAnswer:
        self.questions.append(question)
        if isinstance(self._outcome, Exception):
            raise self._outcome
        return self._outcome


@pytest.fixture
def install_support_service() -> Generator[SupportServiceInstaller]:
    def install(outcome: SupportAnswer | Exception) -> None:
        service: SupportService = FakeSupportService(outcome)  # type: ignore[assignment]
        app.state.support_service = service

    yield install

    if hasattr(app.state, "support_service"):
        del app.state.support_service
