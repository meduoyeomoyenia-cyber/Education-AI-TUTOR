from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session
from backend.app.main import app, engine
from backend.app.models import Attempt, Mastery
from backend.app.mastery import topic_id_for_node
c = TestClient(app)
SLUG = "mathematics/number-bases"

def test_topic_lookup():
    ts = c.get("/topics", params={"subject": "Mathematics"}).json()
    nb = [t for t in ts if t["slug"] == SLUG]
    assert len(nb) == 1 and nb[0]["title"] == "Number Bases" and nb[0]["subject"] == "Mathematics"

def test_lesson_lookup_by_slug():
    r = c.get("/lessons", params={"topic_slug": SLUG}).json()
    assert r["title"] == "Number Bases" and len(r["examples"]) == 2 and r["key_points"]

def test_mixed_bank_empty_but_shaped():
    r = c.get("/questions", params={"topic_slug": SLUG}).json()
    assert r == []  # no Number Bases questions exist yet; none created by migration

def test_exam_filter_mechanics():
    # Simultaneous Equations: WAEC+JAMB vetted rows + 1 NECO STEP 2 fixture; exercises the generic filter
    base = {"topic": "Algebra: Simultaneous Equations"}
    styles = {q["exam_style"] for q in c.get("/questions", params=base).json()}
    assert {"WAEC", "JAMB"} <= styles
    waec = c.get("/questions", params={**base, "exam": "WAEC"}).json()
    jamb = c.get("/questions", params={**base, "exam": "JAMB"}).json()
    neco = c.get("/questions", params={**base, "exam": "NECO"}).json()
    assert len(waec) >= 1 and all(q["exam_style"] == "WAEC" for q in waec)
    assert len(jamb) >= 1 and all(q["exam_style"] == "JAMB" for q in jamb)
    assert all(q["exam_style"] == "NECO" for q in neco) and any(q["stem"].startswith("[TEST]") for q in neco)
    assert c.get("/questions", params={"topic_slug": SLUG, "exam": "WAEC"}).json() == []
    assert c.get("/questions", params={"topic_slug": SLUG, "exam": "NECO"}).json() == []

def test_old_topic_alias():
    assert c.get("/lessons", params={"topic": "Number Bases"}).json()["title"] == "Number Bases"
    assert c.get("/questions", params={"topic": "Number Bases"}).json() == []

def test_mastery_linked_to_topic():
    with Session(engine) as s:
        assert topic_id_for_node(s, 1) == 1  # node 1 -> topic 1
        assert topic_id_for_node(s, 999999) is None
        before = s.query(Attempt).count()
    assert c.get("/mastery/1").status_code == 200
    with Session(engine) as s:
        assert s.query(Attempt).count() == before  # history untouched
        rows = s.query(Mastery).all()
        assert all(r.topic_id is None or isinstance(r.topic_id, int) for r in rows)
