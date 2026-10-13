"""Seed-guard tests: empty / populated / partial-failure / repeat / peer-active.
Each test uses its own scratch SQLite file (never the suite test DB, never dev.db)."""
import os
import tempfile

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from backend.app.seed_all import ensure_seeded


def _fresh_engine(name: str):
    from backend.app.models import Base
    from backend.app.auth import Base as AuthBase
    path = os.path.join(tempfile.gettempdir(), f"edu_seedguard_{name}.db").replace("\\", "/")
    if os.path.exists(path):
        os.remove(path)
    eng = create_engine(f"sqlite:///{path}", future=True)
    Base.metadata.create_all(eng)
    AuthBase.metadata.create_all(eng)
    return eng


def _counts(eng):
    from backend.app.models import Lesson, Question, SyllabusNode, Topic
    with Session(eng) as s:
        from sqlalchemy import func
        return {k: s.query(func.count(m.id)).scalar()
                for k, m in (("nodes", SyllabusNode), ("questions", Question),
                             ("lessons", Lesson), ("topics", Topic))}


def test_empty_db_seeds_to_complete():
    from backend.app.seed_all import ensure_seeded, _expected_counts
    eng = _fresh_engine("empty")
    assert ensure_seeded(eng) == "seeded"
    assert _counts(eng) == _expected_counts()
    # production default path inserts zero test-fixture rows
    with Session(eng) as s:
        from backend.app.models import Lesson, Question
        assert s.query(Question).filter(Question.source == "test-fixture").count() == 0
        assert s.query(Lesson).filter(Lesson.source == "test-fixture").count() == 0


def test_populated_db_is_left_alone():
    from backend.app.models import SeedState
    from backend.app.seed_all import ensure_seeded
    eng = _fresh_engine("pop")
    assert ensure_seeded(eng) == "seeded"
    before = _counts(eng)
    with Session(eng) as s:
        attempts_before = s.get(SeedState, "v1").attempts
    assert ensure_seeded(eng) == "already-seeded"
    assert _counts(eng) == before
    with Session(eng) as s:
        assert s.get(SeedState, "v1").attempts == attempts_before  # no churn


def test_partial_failure_resumes_safely():
    from backend.app.models import SeedState
    import backend.app.seed_all as seed_all
    eng = _fresh_engine("partial")
    real = seed_all.migrate_one
    calls = []
    def boom(subject, topic, e=None):
        calls.append(1)
        if len(calls) == 1:
            raise RuntimeError("simulated outage")
        return real(subject, topic, e)
    seed_all.migrate_one = boom
    try:
        assert ensure_seeded(eng).startswith("failed")
        with Session(eng) as s:
            row = s.get(SeedState, "v1")
            assert row.status == "failed" and row.attempts == 1
        assert ensure_seeded(eng) == "seeded"  # resume completes (idempotent steps)
        assert _counts(eng) == seed_all._expected_counts()
    finally:
        seed_all.migrate_one = real


def test_peer_active_and_max_attempts():
    from datetime import datetime, timezone
    from backend.app.models import SeedState
    from backend.app.seed_all import ensure_seeded
    eng = _fresh_engine("peer")
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    with Session(eng) as s:
        s.add(SeedState(version="v1", status="running", attempts=1, updated_at=now))
        s.commit()
    assert ensure_seeded(eng) == "peer-active"  # fresh claim refused
    with Session(eng) as s:
        row = s.get(SeedState, "v1")
        row.status = "failed"
        row.attempts = 3
        s.commit()
    assert ensure_seeded(eng) == "needs-human"  # cap reached: no blind retry


def test_table_columns_uses_information_schema_on_postgres():
    from content.migrate_topic import _table_columns

    seen = []

    class FakeDialect:
        name = "postgresql"

    class FakeConn:
        dialect = FakeDialect()

        def execute(self, stmt, params=None):
            seen.append((str(stmt), params))
            class R:
                def fetchall(self):
                    return [("topic_id",), ("stem",)]
            return R()

    assert _table_columns(FakeConn(), "questions") == ["topic_id", "stem"]
    sql, params = seen[0]
    assert "information_schema.columns" in sql and "PRAGMA" not in sql.upper()
    assert params == {"t": "questions"}


def test_table_columns_sqlite_missing_table_is_empty():
    import sqlite3
    from content.migrate_topic import _table_columns

    class FakeDialect:
        name = "sqlite"

    class FakeConn:
        dialect = FakeDialect()
        def __init__(self, conn):
            self._conn = conn
        def execute(self, stmt, params=None):
            return self._conn.execute(str(stmt))

    con = sqlite3.connect(":memory:")
    assert _table_columns(FakeConn(con), "nope") == []
