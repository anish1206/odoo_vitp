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

## OCR Configuration (Gemini)

Set the following values in `backend/.env` to enable Gemini-based receipt extraction:

- `RMS_GEMINI_API_KEY=your_gemini_key`
- `RMS_GEMINI_MODEL=gemini-2.0-flash`
- `RMS_GEMINI_OCR_TIMEOUT_SECONDS=20`

Notes:

- Image/PDF uploads use Gemini when `RMS_GEMINI_API_KEY` is set.
- Text receipts (`text/plain`) still use the local heuristic parser for deterministic demo/test behavior.
- If Gemini is unavailable or returns invalid JSON, the service automatically falls back to the local parser.

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
