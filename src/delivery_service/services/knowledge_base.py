from langchain_core.documents import Document
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter

SECTION_KEY = "section"


def split_knowledge_base(
    text: str, source: str, chunk_size: int, chunk_overlap: int
) -> list[Document]:
    by_section = MarkdownHeaderTextSplitter(
        headers_to_split_on=[("##", SECTION_KEY)],
        strip_headers=False,
    ).split_text(text)

    chunks = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " "],
    ).split_documents(by_section)

    for chunk in chunks:
        chunk.metadata["source"] = source
    return chunks
