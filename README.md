# Backend (Phase 1)

FastAPI backend implementing authentication and company bootstrap.

## Features

- POST /auth/signup
- POST /auth/login
- POST /auth/refresh
- GET /users/me
- GET /health

## Local Run

1. Activate virtual environment.
2. Install dependencies with pip install -r requirements.txt.
3. Copy .env.example to .env and adjust values if needed.
4. Run the API:

```
uvicorn app.main:app --reload --app-dir backend
```

The API starts at http://localhost:8000.

## Testing

From the repository root, run:

```
pip install -r backend/requirements.txt
pytest
```

Test layout:

- `test/unit` for unit tests (business logic and helpers).
- `test/api` for API tests (FastAPI endpoints with TestClient).

## Migrations (Phase 2)

Run migrations from the `backend` directory:

```
alembic upgrade head
```

Create a new migration revision:

```
alembic revision -m "your migration message"
```
