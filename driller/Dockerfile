FROM python:3.10


ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV POETRY_VERSION=1.8.3

RUN pip install poetry==$POETRY_VERSION

ENV POETRY_NO_INTERACTION=1 \
POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache
    
WORKDIR /driller

RUN git config --global --add safe.directory '*'

COPY ./poetry.lock ./pyproject.toml ./

RUN poetry install && rm -rf $POETRY_CACHE_DIR

COPY ./driller ./driller

CMD ["poetry", "run", "python3","-m","driller.main"]

