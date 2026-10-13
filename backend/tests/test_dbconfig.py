"""DB configuration tests: URL normalization, fallback warning, seed safety."""
from backend.app.main import normalize_db_url


def test_postgres_scheme_normalized():
    assert normalize_db_url("postgres://u:p@h:5432/db") == "postgresql://u:p@h:5432/db"
    assert normalize_db_url("postgresql://u:p@h:5432/db") == "postgresql://u:p@h:5432/db"


def test_sqlite_and_other_urls_untouched():
    assert normalize_db_url("sqlite:///./dev.db") == "sqlite:///./dev.db"
    assert normalize_db_url("sqlite:////tmp/x.db") == "sqlite:////tmp/x.db"


def test_health_reports_db_type():
    from fastapi.testclient import TestClient
    from backend.app.main import app
    body = TestClient(app).get("/health").json()
    assert body["ok"] is True and body["db"] in ("sqlite", "postgresql")


def test_health_db_ready_is_real():
    from fastapi.testclient import TestClient
    from backend.app.main import app, db_is_ready
    ready, _ = db_is_ready()
    assert ready is True  # test SQLite DB answers SELECT 1
    assert TestClient(app).get("/health").json()["db_ready"] is True


def test_lifespan_initializes_schema():
    import sqlite3
    from fastapi.testclient import TestClient
    from backend.app.main import app, DATABASE_URL
    path = DATABASE_URL.split("sqlite:///")[-1]
    with TestClient(app):
        pass
    tables = {r[0] for r in sqlite3.connect(path).execute(
        "SELECT name FROM sqlite_master WHERE type='table'")}
    assert {"users", "syllabus_nodes", "questions", "lessons", "topics", "otp_codes"} <= tables


def test_engine_options_postgres_only():
    from backend.app.main import _engine_options
    assert _engine_options("postgresql://u:p@h/db") == {"connect_args": {"connect_timeout": 10}}
    assert _engine_options("sqlite:///./dev.db") == {}


def test_seed_inputs_exist_and_parse():
    import json
    from pathlib import Path
    content = Path(__file__).resolve().parents[2] / "content"
    nodes = json.loads((content / "syllabus.json").read_text())
    vetted = json.loads((content / "questions.vetted.json").read_text())
    lessons = json.loads((content / "lessons.vetted.json").read_text(encoding="utf-8"))
    assert len(nodes) == 720 and len(vetted) == 8 and len(lessons) == 3
    assert all({"exam", "student_class", "subject", "topic"} <= set(n) for n in nodes)
