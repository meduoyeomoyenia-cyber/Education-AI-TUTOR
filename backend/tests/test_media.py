from fastapi.testclient import TestClient
from backend.app.main import app
c = TestClient(app)

def test_phase7():
    p = c.post("/uploads/presign", params={"filename": "q.jpg"}).json()
    assert "presigned=1" in p["url"] or "http" in p["url"]
    assert "text" in c.post("/voice/transcribe", json={"language": "yo"}).json()
    assert "48kbps" in c.post("/voice/speak", json={"text": "hello"}).json()["bitrate"]
    assert "Step 1" in c.post("/image/help", json={"image_key": "k", "caption": "2x+y=7", "topic": "Algebra: Simultaneous Equations"}).text
    assert c.post("/media/log", json={"session": "s1", "kb": 40, "media": "text"}).json()["total_kb"] == 40
