FROM ubuntu:24.04

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    libsqlite3-0 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY pyproject.toml uv.lock .python-version ./
RUN uv sync --frozen --no-dev --no-install-project

COPY . .
RUN uv sync --frozen --no-dev

ENV PATH="/app/.venv/bin:$PATH"
# Switch to prod for a real application
ENV DJANGO_SETTINGS_MODULE=config.settings.local

EXPOSE 8000

CMD ["sh", "-c", "python manage.py migrate && python manage.py load_restaurants && gunicorn config.wsgi:application --bind 0.0.0.0:8000"]
