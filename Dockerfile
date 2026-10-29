FROM python:3.14.8-slim-trixie AS base

COPY --from=ghcr.io/astral-sh/uv:0.13.0 /uv /bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv uv sync --frozen --no-dev --no-install-project

# Bake the embedding model into the image: containers start without downloading
# it, and the layer stays cached until the model name changes.
ARG EMBEDDING_MODEL=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
ENV KNOWLEDGE_BASE_EMBEDDING_MODEL=${EMBEDDING_MODEL} \
    KNOWLEDGE_BASE_EMBEDDING_CACHE_DIR=/app/models
RUN python -c "from fastembed import TextEmbedding; TextEmbedding('${EMBEDDING_MODEL}', cache_dir='/app/models')"

FROM base AS dev

COPY . .
RUN --mount=type=cache,target=/root/.cache/uv uv sync --frozen

CMD ["fastapi", "dev", "--host", "0.0.0.0"]

FROM base AS prod

COPY . .
RUN --mount=type=cache,target=/root/.cache/uv uv sync --frozen --no-dev

CMD ["fastapi", "run"]

EXPOSE 8000
