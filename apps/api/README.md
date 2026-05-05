# API

Django + DRF backend for the recommendation quiz.

```bash
poetry install
poetry run python manage.py migrate
poetry run python manage.py seed_catalog
poetry run python manage.py runserver
```

OpenAPI schema: `GET /api/schema/`. Swagger UI: `GET /api/docs/`.
