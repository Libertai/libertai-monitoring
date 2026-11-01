FROM python:3.12-slim AS builder

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=false \
    POETRY_INSTALLER_PARALLEL=false \
    VIRTUAL_ENV=/opt/venv \
    PATH=/opt/venv/bin:$PATH

WORKDIR /app

# Poetry lives in its own throwaway venv so its own dependencies never end up
# in the runtime virtualenv that gets copied to the final image.
RUN python -m venv /opt/poetry \
    && /opt/poetry/bin/pip install poetry==2.5.1 \
    && ln -s /opt/poetry/bin/poetry /usr/local/bin/poetry

COPY ./pyproject.toml ./poetry.lock ./

RUN python -m venv "$VIRTUAL_ENV" \
    && poetry install --without dev --no-root \
    && rm -rf /root/.cache /tmp/*

FROM python:3.12-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    VIRTUAL_ENV=/opt/venv \
    PATH=/opt/venv/bin:$PATH \
    HOME=/home/app

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv
COPY ./src ./src

RUN useradd --uid 10001 --create-home --shell /usr/sbin/nologin app \
    && chown -R app:app /app

USER app

EXPOSE 8000

CMD ["fastapi", "run", "src/main.py", "--host", "0.0.0.0"]
