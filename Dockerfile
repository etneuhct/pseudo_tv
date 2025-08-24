FROM python:3.10-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    PYSETUP_PATH="/opt/pysetup" \
    POETRY_HOME="/opt/poetry" \
    POETRY_VERSION=1.2.0 \
    PATH="$POETRY_HOME/bin:$PATH"

RUN apt-get update \
 && apt-get install --no-install-recommends -y curl ca-certificates \
 && rm -rf /var/lib/apt/lists/*

RUN curl -sSL https://install.python-poetry.org | python3 - \
 && ln -s /opt/poetry/bin/poetry /usr/local/bin/poetry

WORKDIR /usr/src/app

COPY pyproject.toml poetry.lock* ./
RUN poetry config virtualenvs.create false \
 && poetry install --no-interaction --no-ansi --no-root \
 && rm -rf /root/.cache/pypoetry

RUN poetry run playwright install --with-deps chromium

COPY . .

CMD ["sh", "./runme.sh"]
