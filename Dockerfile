FROM ghcr.io/astral-sh/uv:0.12.15 AS uv
FROM python:3.12-slim-bookworm AS build
COPY --from=uv /uv /uvx /bin/
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=never
WORKDIR /app
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --locked --no-dev --extra neural --no-install-project
COPY src ./src
RUN uv sync --locked --no-dev --extra neural
COPY models.lock.json /app/models/manifest.json
ENV POLICYTIME_MODEL_CACHE=/app/models
RUN /app/.venv/bin/policytime download-models

FROM python:3.12-slim-bookworm AS runtime
RUN groupadd --gid 10001 policytime && useradd --uid 10001 --gid 10001 --no-create-home policytime
WORKDIR /app
COPY --from=build --chown=10001:10001 /app /app
COPY --chown=10001:10001 corpus ./corpus
COPY --chown=10001:10001 evaluation ./evaluation
COPY --chown=10001:10001 migrations ./migrations
COPY --chown=10001:10001 alembic.ini ./
ENV PATH="/app/.venv/bin:$PATH" PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 \
    POLICYTIME_MODEL_CACHE=/app/models HF_HOME=/tmp/huggingface \
    HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 LANGSMITH_TRACING=false \
    OMP_NUM_THREADS=2 MKL_NUM_THREADS=2
USER 10001:10001
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=90s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/readyz', timeout=4)"
CMD ["uvicorn", "policytime.delivery.web:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--no-access-log"]
