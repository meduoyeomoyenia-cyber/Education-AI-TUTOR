"""Migrate selected topics to the reusable Topic architecture.
Run: python content/migrate_topic.py [Subject/topic ...]
Default (no args): Mathematics / Number Bases only. Idempotent. Never deletes data.
"""
import re
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from sqlalchemy import select
from sqlalchemy.orm import Session
from backend.app.main import engine
from backend.app.models import Base, Topic, SyllabusNode, Lesson, Question

DEFAULT_TOPICS = [("Mathematics", "Number Bases")]

def slugify(subject: str, topic: str) -> str:
    def clean(part: str) -> str:
        s = re.sub(r"[^a-z0-9]+", "-", part.lower()).strip("-")
        return re.sub(r"-+", "-", s)
    return f"{clean(subject)}/{clean(topic)}"

def migrate_schema():
    """create_all cannot ALTER existing tables, so add topic_id columns explicitly."""
    from sqlalchemy import text
    with engine.begin() as conn:
        for tbl in ("syllabus_nodes", "lessons", "questions", "mastery"):
            cols = [r[1] for r in conn.execute(text(f"PRAGMA table_info({tbl})"))]
            if "topic_id" not in cols:
                conn.execute(text(f"ALTER TABLE {tbl} ADD COLUMN topic_id INTEGER"))
                print(f"migrated: {tbl}.topic_id added")
    Base.metadata.create_all(engine)  # creates topics table if missing

def migrate_one(subject: str, topic: str):
    slug = slugify(subject, topic)
    with Session(engine) as s:
        t = s.execute(select(Topic).where(Topic.subject == subject, Topic.title == topic)).scalars().first()
        if t is None:
            t = Topic(subject=subject, slug=slug, title=topic)
            s.add(t)
            s.commit()
            s.refresh(t)
        elif t.slug != slug:
            t.slug = slug  # align legacy slug to canonical form
            s.commit()
        nodes = s.execute(select(SyllabusNode).where(
            SyllabusNode.subject == subject, SyllabusNode.topic == topic)).scalars().all()
        nids = [n.id for n in nodes]
        for n in nodes:
            n.topic_id = t.id
        n_lessons = s.execute(select(Lesson).where(Lesson.node_id.in_(nids))).scalars().all() if nids else []
        for ls in n_lessons:
            ls.topic_id = t.id
        n_questions = s.execute(select(Question).where(Question.node_id.in_(nids))).scalars().all() if nids else []
        for q in n_questions:
            q.topic_id = t.id  # exam_style untouched
        s.commit()
        print(f"topic={t.slug} id={t.id} nodes={len(nids)} lessons={len(n_lessons)} questions={len(n_questions)}")

def run(pairs=None):
    migrate_schema()
    for subject, topic in (pairs or DEFAULT_TOPICS):
        migrate_one(subject, topic)

if __name__ == "__main__":
    args = sys.argv[1:]
    pairs = []
    for a in args:
        if "/" in a:
            subj, top = a.split("/", 1)
            pairs.append((subj.strip(), top.strip()))
    run(pairs or None)
