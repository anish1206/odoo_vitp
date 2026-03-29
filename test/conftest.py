import os
import shutil
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT_DIR / "backend"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Force a dedicated test database and deterministic test settings.
os.environ["RMS_DATABASE_URL"] = "sqlite:///./test.db"
os.environ["RMS_SECRET_KEY"] = "test-secret-key"
os.environ["RMS_ENVIRONMENT"] = "test"
os.environ["RMS_CORS_ORIGINS"] = "http://localhost:5173"
os.environ["RMS_UPLOADS_DIR"] = "./test_uploads"

from app.db.base import Base  # noqa: E402
from app.db.session import engine  # noqa: E402
from app.main import app  # noqa: E402

TEST_DB_PATH = ROOT_DIR / "test.db"
TEST_UPLOADS_PATH = ROOT_DIR / "test_uploads"


@pytest.fixture(scope="session", autouse=True)
def cleanup_test_db_file():
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()
    yield
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    if TEST_DB_PATH.exists():
        try:
            TEST_DB_PATH.unlink()
        except PermissionError:
            # On Windows, file handles can linger briefly after tests complete.
            pass

    if TEST_UPLOADS_PATH.exists():
        shutil.rmtree(TEST_UPLOADS_PATH, ignore_errors=True)


@pytest.fixture(autouse=True)
def reset_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture()
def client():
    with TestClient(app) as test_client:
        yield test_client
