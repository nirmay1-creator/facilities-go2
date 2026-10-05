# Shared test configuration for pytest.
# Sets PROVIDER_MODE=mock and DATABASE_PATH to a temp file so tests
# are fully isolated and never touch LM Studio.

import os
import tempfile

import pytest
from fastapi.testclient import TestClient

# ── Force mock provider and in-memory/temp DB for all tests ─────────────────
os.environ["PROVIDER_MODE"] = "mock"
os.environ["DATABASE_PATH"] = os.path.join(tempfile.gettempdir(), "test_facilities.db")


@pytest.fixture(scope="session", autouse=True)
def _init_test_db():
    """Initialise a fresh SQLite DB for the test session."""
    from facilities.database import init_db
    init_db()


@pytest.fixture(scope="session")
def api_client():
    """FastAPI TestClient (session-scoped for speed)."""
    from facilities.api import app
    return TestClient(app)
