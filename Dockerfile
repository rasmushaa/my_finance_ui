# syntax=docker/dockerfile:1.7
FROM python:3.13-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

ARG ENV=dev
ENV ENV=${ENV}

# Keep the project virtualenv inside the app directory
ENV UV_PROJECT_ENVIRONMENT=/app/.venv
ENV PATH="/app/.venv/bin:${PATH}"

# Copy dependency metadata first for better caching
COPY pyproject.toml /app/
COPY uv.lock* /app/
COPY src /app/src/

# Install only dependencies first, not the local project itself
RUN uv sync --no-dev


RUN useradd --create-home --shell /bin/bash appuser \
    && chown -R appuser:appuser /app

USER appuser

EXPOSE 8080

CMD ["uv", "run", "streamlit", "run", "src/app.py", "--server.port=8080"]
