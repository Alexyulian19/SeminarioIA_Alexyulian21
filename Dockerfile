FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN useradd --create-home --uid 10001 appuser
WORKDIR /app

COPY requirements-dev.txt .
RUN pip install --no-cache-dir -r requirements-dev.txt

COPY --chown=10001 pyproject.toml conftest.py ./
COPY --chown=10001 app ./app
COPY --chown=10001 tests ./tests
RUN chown 10001 /app

USER 10001
CMD ["pytest", "--cov"]