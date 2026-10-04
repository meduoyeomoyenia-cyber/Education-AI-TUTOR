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

import pytest


@pytest.fixture(scope="session", autouse=True)
def _seed_test_db():
    """Deterministic seed mirroring dev.db content (nodes, vetted Qs/lessons,
    4 migrated topics, STEP 2 fixtures). Attempts/mastery start empty."""
    from backend.app import seed as seedmod
    from content.migrate_topic import migrate_schema, migrate_one
    from content.step2_fixtures import run as fixtures_run
    migrate_schema()
    seedmod.run()
    seedmod.seed_lessons()
    for pair in [("Mathematics", "Number Bases"),
                 ("Mathematics", "Algebra: Simultaneous Equations"),
                 ("Biology", "Photosynthesis"),
                 ("Chemistry", "Acids and Bases")]:
        migrate_one(*pair)
    fixtures_run()
    yield
