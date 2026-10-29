from typing import Any

import groq
import httpx
from langchain_core.documents import Document
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from pydantic import Field
import pytest
from qdrant_client.http.exceptions import ResponseHandlingException

from delivery_service.services.exceptions import (
    KnowledgeBaseUnavailableError,
    LlmUnavailableError,
    SupportNotConfiguredError,
)
from delivery_service.services.support import NO_ANSWER, SupportService

ELECTRONICS = Document(
    "## Электроника\n\nНоутбуки принимаются к отправке.", metadata={"section": "Электроника"}
)
CUSTOMS = Document("## Таможня\n\nДо 200 долларов без пошлины.", metadata={"section": "Таможня"})


class FakeKnowledgeBase:
    def __init__(self, found: list[tuple[Document, float]], fail: bool = False) -> None:
        self._found = found
        self._fail = fail
        self.calls: list[tuple[str, int]] = []

    async def asimilarity_search_with_score(
        self, query: str, k: int = 4
    ) -> list[tuple[Document, float]]:
        self.calls.append((query, k))
        if self._fail:
            raise ResponseHandlingException(ConnectionError("refused"))
        return self._found[:k]


class RecordingChatModel(BaseChatModel):
    """Chat model stub: remembers the messages it got and answers with a fixed text."""

    answer: str = "Да, ноутбуки можно отправлять."
    error: Exception | None = None
    calls: list[list[BaseMessage]] = Field(default_factory=list)

    def _generate(self, messages: list[BaseMessage], *args: Any, **kwargs: Any) -> ChatResult:
        self.calls.append(messages)
        if self.error is not None:
            raise self.error
        return ChatResult(generations=[ChatGeneration(message=AIMessage(self.answer))])

    @property
    def _llm_type(self) -> str:
        return "recording"


def make_service(knowledge_base: FakeKnowledgeBase, llm: BaseChatModel | None) -> SupportService:
    return SupportService(knowledge_base=knowledge_base, llm=llm, top_k=3, min_score=0.2)


async def test_answers_from_relevant_chunks() -> None:
    llm = RecordingChatModel()
    service = make_service(FakeKnowledgeBase([(ELECTRONICS, 0.6), (CUSTOMS, 0.4)]), llm)

    result = await service.answer("Можно ли отправить ноутбук?")

    assert result.answer == "Да, ноутбуки можно отправлять."
    assert result.sources == ["Электроника", "Таможня"]
    prompt = llm.calls[0][-1].content
    assert isinstance(prompt, str)
    assert "Ноутбуки принимаются к отправке." in prompt
    assert "Можно ли отправить ноутбук?" in prompt


async def test_chunks_below_threshold_are_not_sent_to_llm() -> None:
    llm = RecordingChatModel()
    service = make_service(FakeKnowledgeBase([(ELECTRONICS, 0.6), (CUSTOMS, 0.1)]), llm)

    result = await service.answer("Можно ли отправить ноутбук?")

    assert result.sources == ["Электроника"]
    prompt = llm.calls[0][-1].content
    assert isinstance(prompt, str)
    assert "пошлины" not in prompt


async def test_unrelated_question_is_answered_without_llm() -> None:
    llm = RecordingChatModel()
    service = make_service(FakeKnowledgeBase([(CUSTOMS, 0.05)]), llm)

    result = await service.answer("Какая завтра погода?")

    assert result.answer == NO_ANSWER
    assert result.sources == []
    assert llm.calls == []


async def test_requests_top_k_chunks() -> None:
    knowledge_base = FakeKnowledgeBase([])
    service = make_service(knowledge_base, RecordingChatModel())

    await service.answer("Вопрос")

    assert knowledge_base.calls == [("Вопрос", 3)]


async def test_without_llm_service_is_not_configured() -> None:
    service = make_service(FakeKnowledgeBase([(ELECTRONICS, 0.6)]), llm=None)

    with pytest.raises(SupportNotConfiguredError):
        await service.answer("Можно ли отправить ноутбук?")


async def test_vector_db_failure_is_domain_error() -> None:
    service = make_service(FakeKnowledgeBase([], fail=True), RecordingChatModel())

    with pytest.raises(KnowledgeBaseUnavailableError):
        await service.answer("Можно ли отправить ноутбук?")


async def test_llm_failure_is_domain_error() -> None:
    request = httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions")
    llm = RecordingChatModel(error=groq.APIConnectionError(request=request))
    service = make_service(FakeKnowledgeBase([(ELECTRONICS, 0.6)]), llm)

    with pytest.raises(LlmUnavailableError):
        await service.answer("Можно ли отправить ноутбук?")
