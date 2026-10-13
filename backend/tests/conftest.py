"""STEP 4A.1: tests run against an isolated SQLite DB via DATABASE_URL.
Set BEFORE any backend import so the app engine binds to the test DB.
dev.db is never touched by the suite."""
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

_TEST_DB = os.path.join(tempfile.gettempdir(), "edu_tutor_test.db").replace("\\", "/")
if os.path.exists(_TEST_DB):
    os.remove(_TEST_DB)
os.environ["DATABASE_URL"] = f"sqlite:///{_TEST_DB}"
os.environ["AUTH_DISABLED"] = "1"  # gate covered by test_auth_gate.py with the flag off

import pytest


@pytest.fixture(scope="session", autouse=True)
def _seed_test_db():
    """Suite DB mirrors dev.db content via the real ensure_seeded path, WITH
    fixtures (tests assert on fixture rows). Attempts/mastery start empty.
    Production uses the default include_fixtures=False path."""
    from backend.app.seed_all import ensure_seeded
    assert ensure_seeded(include_fixtures=True) == "seeded"
    yield
