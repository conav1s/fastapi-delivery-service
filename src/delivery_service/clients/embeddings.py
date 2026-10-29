from collections.abc import Sequence

from fastembed import TextEmbedding
from langchain_core.embeddings import Embeddings


class FastEmbedEmbeddings(Embeddings):
    """LangChain `Embeddings` on top of a local fastembed (ONNX) model.

    The ready-made adapter lives in `langchain-community`, which is being sunset,
    and the whole interface is two methods anyway.
    """

    def __init__(self, model_name: str, cache_dir: str | None = None) -> None:
        # Loads the model, downloading it on first use (the Docker image ships it).
        self._model = TextEmbedding(model_name, cache_dir=cache_dir)

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        return [[float(x) for x in vector] for vector in self._model.embed(list(texts))]

    def embed_query(self, text: str) -> list[float]:
        # The model does not use separate query/passage prefixes.
        return self.embed_documents([text])[0]
