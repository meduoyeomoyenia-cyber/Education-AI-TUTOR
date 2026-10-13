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


def test_seed_inputs_exist_and_parse():
    import json
    from pathlib import Path
    content = Path(__file__).resolve().parents[2] / "content"
    nodes = json.loads((content / "syllabus.json").read_text())
    vetted = json.loads((content / "questions.vetted.json").read_text())
    lessons = json.loads((content / "lessons.vetted.json").read_text(encoding="utf-8"))
    assert len(nodes) == 720 and len(vetted) == 8 and len(lessons) == 3
    assert all({"exam", "student_class", "subject", "topic"} <= set(n) for n in nodes)
