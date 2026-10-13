"""One-command production seed. Run once against the live DB, e.g. Render Shell:
    python -m app.seed_all
Builds: schema + syllabus/questions/lessons + 4 reusable topics + fixtures.
Idempotent: safe to re-run (existing rows are kept, never duplicated)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.app import seed as seedmod  # noqa: E402
from content.migrate_topic import migrate_schema, migrate_one  # noqa: E402
from content.step2_fixtures import run as fixtures_run  # noqa: E402

TOPICS = [
    ("Mathematics", "Number Bases"),
    ("Mathematics", "Algebra: Simultaneous Equations"),
    ("Biology", "Photosynthesis"),
    ("Chemistry", "Acids and Bases"),
]


SEED_VERSION = "v1"
STALE_SECS = 900
MAX_ATTEMPTS = 3


def _utcnow():
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _expected_counts():
    """Derived from the actual seed files, never hardcoded."""
    import json
    from pathlib import Path
    content = Path(__file__).resolve().parents[2] / "content"
    nodes = json.loads((content / "syllabus.json").read_text())
    vetted = json.loads((content / "questions.vetted.json").read_text())
    lessons = json.loads((content / "lessons.vetted.json").read_text(encoding="utf-8"))
    return {"nodes": len(nodes), "questions": len(vetted) + 1, "lessons": len(lessons) + 2, "topics": len(TOPICS)}


def _checklist(s):
    """True only when every stage's output is fully present (partial seeds fail)."""
    from sqlalchemy import func
    from backend.app.models import Lesson, Mastery, Question, SyllabusNode, Topic
    exp = _expected_counts()
    got = {
        "nodes": s.query(func.count(SyllabusNode.id)).scalar(),
        "questions": s.query(func.count(Question.id)).scalar(),
        "lessons": s.query(func.count(Lesson.id)).scalar(),
        "topics": s.query(func.count(Topic.id)).scalar(),
    }
    return all(got[k] >= exp[k] for k in exp), got


def _claim(s, version=SEED_VERSION):
    """Returns True if this process owns the seed run. Concurrent starters and
    repeatedly-failed versions are refused (caller must not proceed)."""
    from sqlalchemy.exc import IntegrityError
    from backend.app.models import SeedState
    row = s.get(SeedState, version)
    if row is None:
        try:
            s.add(SeedState(version=version, status="running", attempts=1, updated_at=_utcnow()))
            s.commit()
            return True
        except IntegrityError:  # lost a race with a peer starter
            s.rollback()
            return False
    if row.status == "complete":
        return False
    age = (_utcnow() - (row.updated_at or _utcnow())).total_seconds()
    if row.status == "running" and age < STALE_SECS:
        return False  # peer actively seeding
    if row.status == "failed" and row.attempts >= MAX_ATTEMPTS:
        return False  # needs a human; stop retrying
    row.status = "running"
    row.attempts = (row.attempts or 0) + 1
    row.updated_at = _utcnow()
    s.commit()
    return True


def _finish(s, ok: bool, detail: str = "", version=SEED_VERSION):
    from backend.app.models import SeedState
    row = s.get(SeedState, version)
    if row is None:
        return
    row.status = "complete" if ok else "failed"
    row.detail = detail[:500]
    row.updated_at = _utcnow()
    s.commit()


def ensure_seeded(engine=None):
    """Seed iff needed. Returns: already-seeded | seeded | peer-active |
    needs-human | failed:<step>. Never raises, never deletes."""
    from sqlalchemy.orm import Session
    from backend.app.main import engine as _default
    from backend.app.models import Base, SeedState
    eng = engine or _default
    Base.metadata.create_all(eng)  # ensures seed_state itself exists
    with Session(eng) as s:
        if not _claim(s):
            row = s.get(SeedState, SEED_VERSION)
            if row is None or row.status == "complete":
                return "already-seeded"
            if row.status == "running":
                return "peer-active"
            return "needs-human"
        try:
            migrate_schema(eng)
            seedmod.run(eng)
            seedmod.seed_lessons(eng)
            for subject, topic in TOPICS:
                migrate_one(subject, topic, eng)
            fixtures_run(eng)
        except Exception as e:
            _finish(s, False, f"failed: {type(e).__name__}: {e}")
            return f"failed:{type(e).__name__}"
        complete, got = _checklist(s)
        _finish(s, complete, f"counts={got}" if complete else f"incomplete counts={got}")
        return "seeded" if complete else "failed:checklist"


def run(engine=None):
    from backend.app.main import engine as _default
    eng = engine or _default
    migrate_schema(eng)
    seedmod.run(eng)
    seedmod.seed_lessons(eng)
    for subject, topic in TOPICS:
        migrate_one(subject, topic, eng)
    fixtures_run(eng)
    print("seed_all complete")


if __name__ == "__main__":
    run()
