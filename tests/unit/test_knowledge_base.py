from delivery_service.services.knowledge_base import split_knowledge_base

RULES = """# Правила

## Вес

Максимальный вес посылки 30 кг.

## Сроки

Доставка занимает от 7 до 21 дня.
"""


def test_every_section_is_its_own_chunk() -> None:
    chunks = split_knowledge_base(RULES, source="rules.md", chunk_size=500, chunk_overlap=0)

    assert [chunk.metadata["section"] for chunk in chunks] == ["Вес", "Сроки"]
    assert all(chunk.metadata["source"] == "rules.md" for chunk in chunks)
    # The heading stays in the text: it helps the embedding find the chunk.
    assert chunks[1].page_content.startswith("## Сроки")
    assert "30 кг" not in chunks[1].page_content


def test_long_section_is_split_but_keeps_its_section() -> None:
    long_section = "## Вес\n\n" + "\n\n".join(f"Правило номер {i} про вес." for i in range(20))

    chunks = split_knowledge_base(long_section, source="rules.md", chunk_size=100, chunk_overlap=0)

    assert len(chunks) > 1
    assert all(len(chunk.page_content) <= 100 for chunk in chunks)
    assert {chunk.metadata["section"] for chunk in chunks} == {"Вес"}
