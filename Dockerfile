FROM python:3.14.8-slim-trixie AS base

COPY --from=ghcr.io/astral-sh/uv:0.13.0 /uv /bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv uv sync --frozen --no-dev --no-install-project

FROM base AS dev

COPY . .
RUN --mount=type=cache,target=/root/.cache/uv uv sync --frozen

CMD ["fastapi", "dev", "--host", "0.0.0.0"]

FROM base AS prod

COPY . .
RUN --mount=type=cache,target=/root/.cache/uv uv sync --frozen --no-dev

CMD ["fastapi", "run"]

EXPOSE 8000
