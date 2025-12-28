# TN-OA-008: Omega Standard Dockerfile (Multi-Stage Poetry)

# ------------------------------------------------------------------------------
# Stage 1: Builder (Compiles dependencies)
# ------------------------------------------------------------------------------
FROM python:3.12-slim-bookworm As builder

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_VERSION=2.0.0 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1

# Install System Deps (curl for poetry, build-essential for extensions)
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="$POETRY_HOME/bin:$PATH"

WORKDIR /app

# Copy Dependency Files
COPY pyproject.toml poetry.lock ./

# Install Runtime Dependencies (No Dev)
RUN poetry install --only main --no-root

# ------------------------------------------------------------------------------
# Stage 2: Runtime (Slim Image)
# ------------------------------------------------------------------------------
FROM python:3.12-slim-bookworm As runtime

ENV PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

# Install Neo4j Driver System Dependencies (if any required specifically, usually none for pure python)
# Keeping slim.

# Copy Virtual Environment from Builder
COPY --from=builder /app/.venv /app/.venv

# Copy Application Code
COPY src ./src

# Create Non-Root User for Security
RUN useradd -m -u 1000 omega \
    && chown -R omega:omega /app
USER omega

# Create volume mount points for multiple databases
VOLUME ["/data/sqlite", "/data/postgres", "/data/neo4j"]

# Expose MCP Port
EXPOSE 8768

# Entrypoint: Launch memOS Server via Poetry
CMD ["poetry", "run", "python", "src/memos_mcp/server.py"]
