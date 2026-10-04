"""STEP 2 minimal test fixtures. Run: python content/step2_fixtures.py
Inserts ONLY: 1 NECO Simultaneous Equations question + 2 stub test lessons
(Photosynthesis, Acids and Bases). All rows source='test-fixture'.
Idempotent. Reversible: DELETE FROM questions/lessons WHERE source='test-fixture'.
Does NOT touch real content.
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from sqlalchemy import select
from sqlalchemy.orm import Session
from backend.app.main import engine
from backend.app.models import Topic, SyllabusNode, Lesson, Question

NECO_Q = {"subject": "Mathematics", "topic": "Algebra: Simultaneous Equations",
          "stem": "[TEST] If 2x + 3y = 16 and x + y = 6, find y.",
          "options": ["2", "3", "4", "5"], "answer": "4",
          "difficulty": "Intermediate", "exam_style": "NECO"}

TEST_LESSONS = [
    {"subject": "Biology", "topic": "Photosynthesis", "title": "Photosynthesis",
     "objectives": ["[TEST] State where photosynthesis occurs."],
     "explanation": "[TEST] Stub lesson for architecture verification only.",
     "examples": [{"title": "[TEST] Example", "steps": ["Chloroplasts trap light."], "answer": "Chloroplast"}],
     "key_points": ["[TEST] Photosynthesis occurs in the chloroplast."], "reading_mins": 1},
    {"subject": "Chemistry", "topic": "Acids and Bases", "title": "Acids and Bases",
     "objectives": ["[TEST] State the pH of a neutral solution."],
     "explanation": "[TEST] Stub lesson for architecture verification only.",
     "examples": [{"title": "[TEST] Example", "steps": ["Pure water at 25C is neutral."], "answer": "7"}],
     "key_points": ["[TEST] Neutral pH is 7 at 25C."], "reading_mins": 1},
]

def run():
    with Session(engine) as s:
        topics = {t.slug: t for t in s.execute(select(Topic)).scalars().all()}
        # 1. NECO question on simultaneous topic
        slug = "mathematics/algebra-simultaneous-equations"
        t = topics[slug]
        exists = s.execute(select(Question).where(Question.topic_id == t.id, Question.source == "test-fixture")).scalars().first()
        if exists is None:
            node = s.execute(select(SyllabusNode).where(SyllabusNode.topic_id == t.id).limit(1)).scalars().first()
            s.add(Question(node_id=node.id, topic_id=t.id, stem=NECO_Q["stem"], options=NECO_Q["options"],
                           answer=NECO_Q["answer"], difficulty=NECO_Q["difficulty"], exam_style="NECO",
                           source="test-fixture", license="test", mistake_tags=[], lang_variants={}))
            print("fixture question added: NECO simultaneous")
        # 2. stub lessons
        for ls in TEST_LESSONS:
            t = next(x for x in topics.values() if x.subject == ls["subject"] and x.title == ls["topic"])
            exists = s.execute(select(Lesson).where(Lesson.topic_id == t.id, Lesson.source == "test-fixture")).scalars().first()
            if exists is None:
                node = s.execute(select(SyllabusNode).where(SyllabusNode.topic_id == t.id).limit(1)).scalars().first()
                s.add(Lesson(node_id=node.id, topic_id=t.id, language="en", title=ls["title"],
                             objectives=ls["objectives"], explanation=ls["explanation"], examples=ls["examples"],
                             key_points=ls["key_points"], media=[], source="test-fixture",
                             license="test", reading_mins=ls["reading_mins"]))
                print(f"fixture lesson added: {t.slug}")
        s.commit()

if __name__ == "__main__":
    run()
