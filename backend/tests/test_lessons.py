from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.seed import seed_lessons
c = TestClient(app)

def test_lessons_slice():
    seed_lessons()
    seed_lessons()  # idempotent
    r = c.get("/lessons", params={"topic": "Algebra: Simultaneous Equations"}).json()
    assert r["title"] == "Algebra: Simultaneous Equations"
    assert len(r["objectives"]) >= 3 and len(r["examples"]) == 2 and len(r["key_points"]) >= 4
    assert r["explanation"] and r["bytes"] > 0
    b = c.get("/lessons", params={"topic": "Number Bases", "brief": 1}).json()
    assert "explanation" not in b and b["key_points"]
    yo = c.get("/lessons", params={"topic": "Number Bases", "language": "yo"}).json()
    assert yo["language"] == "en" and yo["fallback_to_en"] is True
    assert c.get("/lessons", params={"topic": "No Such Topic"}).json()["error"] == "lesson not found"
    assert c.get("/lessons").json()["error"] == "provide topic_slug, topic or node_id"
    # question system: vetted originals present regardless of later approvals
    rows = c.get("/questions", params={"topic": "Algebra: Simultaneous Equations"}).json()
    stems = {q["stem"] for q in rows}
    assert {"Solve: 2x + y = 7, x - y = 2. Find x.", "If 3x + 2y = 12 and x + 2y = 8, find x."} <= stems
    assert len(rows) >= 2 and all(q["exam_style"] in ("WAEC", "JAMB", "NECO") for q in rows)
