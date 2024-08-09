FROM python:3.10


ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV POETRY_VERSION=1.8.3

RUN pip install --upgrade pip --no-cache-dir && \
  pip install poetry==$POETRY_VERSION

ENV POETRY_NO_INTERACTION=1 \
  POETRY_VIRTUALENVS_IN_PROJECT=1 \
  POETRY_VIRTUALENVS_CREATE=0 \
  POETRY_CACHE_DIR=/tmp/poetry_cache

WORKDIR /app/driller

RUN git config --global --add safe.directory '*'

COPY ./driller/poetry.lock ./driller/pyproject.toml ./
COPY ./common/ ../common/

RUN poetry install --with test && rm -rf $POETRY_CACHE_DIR

COPY ./driller/src ./driller
COPY ./driller/tests ./tests

CMD [ "poetry", "run", "python3", "-m", "src.main" ]