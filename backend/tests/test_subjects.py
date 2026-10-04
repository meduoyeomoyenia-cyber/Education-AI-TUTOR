from fastapi.testclient import TestClient
from backend.app.main import app
c = TestClient(app)

def test_subjects_slice():
    ss = c.get("/subjects").json()
    assert len(ss) == 16 and "Mathematics" in ss and ss == sorted(ss)
    assert c.get("/subjects", params={"exam": "WAEC"}).json() == ss
    for subj, n in [("Mathematics", 15), ("Biology", 15), ("Chemistry", 15), ("Physics", 15)]:
        rows = c.get("/syllabus", params={"exam": "WAEC", "subject": subj}).json()
        assert len(rows) == n, subj
        assert all(r["subject"] == subj for r in rows)
    # default dashboard query unchanged
    assert len(c.get("/syllabus", params={"exam": "WAEC", "subject": "Mathematics"}).json()) == 15

def test_dashboard_fallback_source():
    # Dashboard merges /topics with distinct /syllabus topics for unmigrated subjects
    for subj in ("Biology", "Chemistry", "Physics"):
        rows = c.get("/syllabus", params={"subject": subj}).json()
        assert len({r["topic"] for r in rows}) == 5, subj
