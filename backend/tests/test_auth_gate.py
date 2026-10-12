"""Auth gate tests: run with AUTH_DISABLED off to prove the real behavior."""
import os
import importlib
import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def gated_client(monkeypatch):
    monkeypatch.delenv("AUTH_DISABLED", raising=False)
    import backend.app.main as main
    importlib.reload(main)
    try:
        yield TestClient(main.app)
    finally:
        importlib.reload(main)


def _token(c):
    code = c.post("/auth/request", json={"phone": "08039998888"}).json()["dev_code"]
    return c.post("/auth/verify", json={"phone": "08039998888", "code": code}).json()["token"]


def test_protected_without_token_401(gated_client):
    for path in ["/syllabus", "/questions", "/lessons", "/mastery/1", "/ask", "/attempts"]:
        if path == "/ask":
            r = gated_client.post(path, json={"message": "hi"})
        elif path == "/attempts":
            r = gated_client.post(path, json={"question_id": 1, "answer": "x"})
        else:
            r = gated_client.get(path)
        assert r.status_code == 401, path


def test_public_without_token_ok(gated_client):
    assert gated_client.get("/health").status_code == 200
    assert gated_client.get("/subjects").status_code == 200
    assert gated_client.get("/topics").status_code == 200
    assert gated_client.post("/auth/request", json={"phone": "08039998888"}).status_code == 200


def test_protected_with_token_ok(gated_client):
    h = {"Authorization": f"Bearer {_token(gated_client)}"}
    assert gated_client.get("/syllabus", headers=h).status_code == 200
    assert gated_client.get("/questions", headers=h).status_code == 200
    assert gated_client.get("/health", headers={"Authorization": "Bearer bogus.token.here"}).status_code == 200


def test_bad_token_401(gated_client):
    assert gated_client.get("/syllabus", headers={"Authorization": "Bearer bogus"}).status_code == 401
