FROM python:3.14-slim

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Copy project files
COPY pyproject.toml uv.lock* ./

# Install dependencies using uv
RUN uv sync --no-dev

# Copy bot source code
COPY . .

# Ensure handlers/__init__.py exists (implicit via copy)

ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1

CMD ["uv", "run", "bot.py"]
