import httpx

from delivery_service.services.exceptions import LlmUnavailableError, SupportNotConfiguredError
from delivery_service.services.support import SupportAnswer

from .conftest import SupportServiceInstaller

URL = "/support/questions"


async def test_returns_answer_with_sources(
    client: httpx.AsyncClient, install_support_service: SupportServiceInstaller
) -> None:
    install_support_service(SupportAnswer(answer="Да, можно.", sources=["Электроника"]))

    response = await client.post(URL, json={"question": "  Можно ли отправить ноутбук?  "})

    assert response.status_code == 200
    assert response.json() == {"answer": "Да, можно.", "sources": ["Электроника"]}


async def test_rejects_too_short_question(
    client: httpx.AsyncClient, install_support_service: SupportServiceInstaller
) -> None:
    install_support_service(SupportAnswer(answer="", sources=[]))

    response = await client.post(URL, json={"question": " ? "})

    assert response.status_code == 422
    assert response.json()["details"][0]["loc"] == ["body", "question"]


async def test_not_configured_support_is_503(
    client: httpx.AsyncClient, install_support_service: SupportServiceInstaller
) -> None:
    install_support_service(SupportNotConfiguredError())

    response = await client.post(URL, json={"question": "Можно ли отправить ноутбук?"})

    assert response.status_code == 503
    assert response.json()["code"] == "support_not_configured"


async def test_llm_failure_is_503(
    client: httpx.AsyncClient, install_support_service: SupportServiceInstaller
) -> None:
    install_support_service(LlmUnavailableError())

    response = await client.post(URL, json={"question": "Можно ли отправить ноутбук?"})

    assert response.status_code == 503
    assert response.json()["code"] == "llm_unavailable"
