FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1
WORKDIR /app
COPY pyproject.toml ./
COPY app ./app
COPY alembic.ini ./
COPY migrations ./migrations
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint
RUN pip install .
RUN useradd --create-home --uid 10001 appuser && chmod +x /usr/local/bin/docker-entrypoint
EXPOSE 8000
ENTRYPOINT ["/usr/local/bin/docker-entrypoint"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
