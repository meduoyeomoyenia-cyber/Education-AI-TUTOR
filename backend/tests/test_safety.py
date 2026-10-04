from fastapi.testclient import TestClient
from backend.app.main import app
c = TestClient(app)

def test_safety():
    assert c.post("/safety/check", json={"text": "call 08012345678"}).json()["flags"] == ["pii"]
    b = c.post("/safety/check", json={"text": "kill yourself"}).json()
    assert b["blocked"] is True
    assert c.post("/safety/report", json={"user_id": 1, "kind": "bullying", "ref": "msg1"}).json()["status"] == "queued"
