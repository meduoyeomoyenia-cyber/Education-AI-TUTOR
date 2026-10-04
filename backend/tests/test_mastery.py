from fastapi.testclient import TestClient
from backend.app.main import app
c = TestClient(app)

def test_mastery_plan():
    c.post("/attempts", json={"question_id": 1, "answer": "wrong"})
    m = c.get("/mastery/1").json()
    assert isinstance(m, list) and m[0]["level"] in ("Strong", "Developing", "NeedsRevision")
    a = c.get("/analysis/1").json()
    assert "score" in a and "recommendations" in a
    p = c.get("/plan/today/1").json()
    assert len(p["items"]) == 4
    n = c.get("/notifications/1").json()
    assert "throttle" in n
