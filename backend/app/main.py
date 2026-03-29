from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect, text

import app.models  # noqa: F401
from app.api.auth import router as auth_router
from app.api.users import router as users_router
from app.core.config import settings
from app.db.base import Base
from app.db.session import engine

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _patch_legacy_sqlite_schema() -> None:
    # Keep startup resilient for users with older Phase 1 SQLite files.
    if not engine.dialect.name.startswith("sqlite"):
        return

    with engine.begin() as conn:
        inspector = inspect(conn)
        tables = set(inspector.get_table_names())
        if "users" not in tables:
            return

        user_columns = {col["name"] for col in inspector.get_columns("users")}

        if "department_id" not in user_columns:
            conn.execute(text("ALTER TABLE users ADD COLUMN department_id INTEGER"))

        if "manager_id" not in user_columns:
            conn.execute(text("ALTER TABLE users ADD COLUMN manager_id INTEGER"))


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)
    _patch_legacy_sqlite_schema()


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(auth_router)
app.include_router(users_router)
