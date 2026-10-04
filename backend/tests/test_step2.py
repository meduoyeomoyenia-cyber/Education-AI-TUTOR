"""STEP 2 proof: reusable Topic -> one Lesson -> multi-exam Question Bank (3 subjects)."""
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session
from backend.app.main import app, engine
from backend.app.models import Lesson, Question, Topic, Attempt, SyllabusNode
from backend.app.mastery import topic_id_for_node
c = TestClient(app)

SIM = "mathematics/algebra-simultaneous-equations"
PHO = "biology/photosynthesis"
ACI = "chemistry/acids-and-bases"

def test_1_2_3_reusable_lessons():
    for slug, title in [(SIM, "Algebra: Simultaneous Equations"), (PHO, "Photosynthesis"), (ACI, "Acids and Bases")]:
        r = c.get("/lessons", params={"topic_slug": slug}).json()
        assert r["title"] == title, slug  # exactly ONE lesson resolves per topic
        with Session(engine) as s:
            t = s.execute(select(Topic).where(Topic.slug == slug)).scalars().one()
            n = s.query(Lesson).filter(Lesson.topic_id == t.id, Lesson.language == "en").count()
            assert n == 1, (slug, n)  # no WAEC/JAMB/NECO duplicate lessons

def test_4_same_topic_regardless_of_exam():
    for slug in (SIM, PHO, ACI):
        styles = {q["exam_style"] for q in c.get("/questions", params={"topic_slug": slug}).json()}
        assert styles and styles <= {"WAEC", "JAMB", "NECO"}, (slug, styles)

def test_5_mixed_bank():
    rows = c.get("/questions", params={"topic_slug": SIM}).json()
    assert {q["exam_style"] for q in rows} >= {"WAEC", "JAMB", "NECO"} and len(rows) >= 3

def test_6_7_8_exam_filters():
    waec = c.get("/questions", params={"topic_slug": SIM, "exam": "WAEC"}).json()
    jamb = c.get("/questions", params={"topic_slug": SIM, "exam": "JAMB"}).json()
    neco = c.get("/questions", params={"topic_slug": SIM, "exam": "NECO"}).json()
    assert len(waec) >= 1 and all(q["exam_style"] == "WAEC" for q in waec)
    assert len(jamb) >= 1 and all(q["exam_style"] == "JAMB" for q in jamb)
    assert len(neco) >= 1 and all(q["exam_style"] == "NECO" for q in neco)
    pho = c.get("/questions", params={"topic_slug": PHO}).json()
    assert {q["exam_style"] for q in pho} == {"WAEC", "NECO"}
    assert all(q["exam_style"] == "WAEC" for q in c.get("/questions", params={"topic_slug": PHO, "exam": "WAEC"}).json())

def test_9_no_per_exam_topics():
    with Session(engine) as s:
        slugs = [t.slug for t in s.execute(select(Topic)).scalars().all()]
    assert len(slugs) == len(set(slugs)) == 4  # NB + 3 step-2 topics, none exam-suffixed
    assert not any(x in s_.upper() for s_ in slugs for x in ("WAEC", "JAMB", "NECO"))

def test_10_topic_alias_still_works():
    assert c.get("/lessons", params={"topic": "Photosynthesis"}).json()["title"] == "Photosynthesis"
    ids = {q["id"] for q in c.get("/questions", params={"topic": "Photosynthesis"}).json()}
    assert {3, 4} <= ids  # vetted originals present regardless of later approvals

def test_mastery_topic_compatible():
    with Session(engine) as s:
        sim = s.execute(select(Topic).where(Topic.slug == SIM)).scalars().one()
        node_ids = [n.id for n in s.execute(
            select(SyllabusNode).where(SyllabusNode.topic_id == sim.id)).scalars().all()]
        assert len(node_ids) == 9
        assert {topic_id_for_node(s, n) for n in node_ids} == {sim.id}  # all 9 nodes -> ONE topic
        before = s.query(Attempt).count()
    assert c.get("/mastery/1").status_code == 200
    with Session(engine) as s:
        assert s.query(Attempt).count() == before
