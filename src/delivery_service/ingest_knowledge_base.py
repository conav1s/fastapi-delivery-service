from langchain_qdrant import QdrantVectorStore
from loguru import logger

from .clients.embeddings import FastEmbedEmbeddings
from .config import settings
from .logging_setup import setup_logging
from .services.knowledge_base import split_knowledge_base


def main() -> None:
    setup_logging()
    kb = settings.knowledge_base

    text = kb.path.read_text(encoding="utf-8")
    chunks = split_knowledge_base(
        text, source=kb.path.name, chunk_size=kb.chunk_size, chunk_overlap=kb.chunk_overlap
    )
    logger.info("Split {} into {} chunks", kb.path, len(chunks))

    QdrantVectorStore.from_documents(
        chunks,
        FastEmbedEmbeddings(kb.embedding_model, cache_dir=kb.embedding_cache_dir),
        url=settings.qdrant.url,
        collection_name=settings.qdrant.collection,
        force_recreate=True,
        trust_env=False,
    )
    logger.info("Knowledge base loaded into collection {!r}", settings.qdrant.collection)


if __name__ == "__main__":
    main()
