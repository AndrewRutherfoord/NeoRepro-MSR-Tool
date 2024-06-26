# Graph MSR Tool - Backend

## Creating a Database Migration

1. Activate a bash terminal inside the backend docker container:

```bash
docker compose exec -it backend bash
```

2. Inside the container bash terminal create the migration:

```bash
cd backend
alembic revision --autogenerate -m "<message>"
```

> Ensure that you change `<message>`.

3. Then apply the migrations

```bash
alembic upgrade head
```
