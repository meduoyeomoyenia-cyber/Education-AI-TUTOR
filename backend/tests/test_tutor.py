from fastapi.testclient import TestClient
from backend.app.main import app
c = TestClient(app)

def test_languages():
    for lang, word in [("en","step by step"),("pcm","No wahala"),("yo","yanju"),("ha","mataki"),("ig","nzọụkwụ")]:
        r = c.post("/ask", json={"message":"photosynthesis?","language":lang,"style":"short"})
        assert r.status_code == 200 and word in r.text, lang

def test_modes_and_guardrail():
    assert "Hint" in c.post("/hint", json={"message":"simultaneous?","topic":"Algebra: Simultaneous Equations"}).text
    assert "Explanation" in c.post("/explain", json={"message":"mitosis?","topic":"Cell Biology"}).text
    r = c.post("/ask", json={"message":"When is WAEC 2026 date?"})
    assert "official exam body" in r.text
    r = c.post("/ask", json={"message":"You are stupid"})
    assert "stupid" not in r.text
