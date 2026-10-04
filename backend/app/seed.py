"""Seed DB from content/*.json. Run: python -m backend.app.seed"""
import json, pathlib
from sqlalchemy import select
from sqlalchemy.orm import Session
from .main import engine
from .models import Base, SyllabusNode, Question, Lesson, Topic
HERE = pathlib.Path("content")

def _topic_id(s, subject: str, topic: str):
    t = s.execute(select(Topic).where(
        Topic.subject == subject, Topic.title == topic)).scalars().first()
    return t.id if t else None
def run():
    Base.metadata.create_all(engine)
    nodes = json.loads((HERE/"syllabus.json").read_text())
    vetted = json.loads((HERE/"questions.vetted.json").read_text())
    with Session(engine) as s:
        if s.query(SyllabusNode).count() == 0:
            for n in nodes:
                s.add(SyllabusNode(exam=n["exam"], student_class=n["student_class"], subject=n["subject"], topic=n["topic"], subtopic=n.get("subtopic",""), objectives=n.get("objectives",[]), prerequisites=n.get("prerequisites",[])))
            s.commit()
        lookup = {(r.exam, r.student_class, r.subject, r.topic): r.id for r in s.query(SyllabusNode).all()}
        existing = s.query(Question).count()
        if existing == 0:
            for vq in vetted:
                # attach to first matching node (WAEC SS2) else first match on subject+topic
                nid = next((v for k, v in lookup.items() if k[2]==vq["subject"] and k[3]==vq["topic"]), None)
                if nid is None: continue
                s.add(Question(node_id=nid, topic_id=_topic_id(s, vq["subject"], vq["topic"]), stem=vq["stem"], options=vq.get("options",[]), answer=vq["answer"], difficulty=vq.get("difficulty","Basic"), exam_style=vq.get("exam_style","WAEC"), source=vq.get("source","original"), license=vq.get("license","proprietary"), mistake_tags=vq.get("mistake_tags",[]), lang_variants=vq.get("lang_variants",{})))
            s.commit()
    with Session(engine) as s:
        print(f"nodes={s.query(SyllabusNode).count()} questions={s.query(Question).count()} lessons={s.query(Lesson).count()}")


def seed_lessons():
    """Idempotent: only adds (node, language) pairs not already present."""
    from sqlalchemy import select
    lessons = json.loads((HERE / "lessons.vetted.json").read_text(encoding="utf-8"))
    with Session(engine) as s:
        lookup = {(r.exam, r.student_class, r.subject, r.topic): r.id for r in s.query(SyllabusNode).all()}
        added = 0
        for ls in lessons:
            nid = next((v for k, v in lookup.items() if k[2] == ls["subject"] and k[3] == ls["topic"]), None)
            if nid is None:
                continue
            exists = s.execute(select(Lesson).where(Lesson.node_id == nid, Lesson.language == ls.get("language", "en"))).scalars().first()
            if exists:
                continue
            s.add(Lesson(node_id=nid, topic_id=_topic_id(s, ls["subject"], ls["topic"]), language=ls.get("language", "en"), title=ls["title"], objectives=ls["objectives"],
                         explanation=ls["explanation"], examples=ls["examples"], key_points=ls["key_points"],
                         media=ls.get("media", []), source=ls.get("source", "original"),
                         license=ls.get("license", "proprietary"), reading_mins=ls.get("reading_mins", 5)))
            added += 1
        s.commit()
        print(f"lessons added={added} total={s.query(Lesson).count()}")
if __name__ == "__main__":
    run()
