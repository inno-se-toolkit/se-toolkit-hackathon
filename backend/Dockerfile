# Backend — Restaurant Allergen Advisor API

# Build stage using uv (fast, reproducible)
FROM python:3.14-slim AS builder

# Install uv
ENV UV_VERSION=0.6.8
RUN pip install "uv==${UV_VERSION}"

WORKDIR /app

# Copy dependency files
COPY backend/pyproject.toml ./
# If a uv.lock exists at repo root, copy it too; otherwise uv will resolve
COPY uv.lock* ./ 2>/dev/null || true

# Create venv and install deps
RUN uv sync --no-dev --frozen || uv sync --no-dev

# Copy application source
COPY backend ./backend

# Final stage — slim runtime
FROM python:3.14-slim

# Non-root user
RUN groupadd --system --gid 999 appuser && useradd --system --gid 999 --uid 999 --create-home appuser

WORKDIR /app
COPY --from=builder --chown=appuser:appuser /app/.venv /app/.venv
COPY --from=builder --chown=appuser:appuser /app/backend ./backend

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

USER appuser
EXPOSE 8000

CMD ["uv", "run", "backend/app/run.py"]
