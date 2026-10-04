"""Provider architecture tests: registry, ALOC adapter (mocked HTTP), import gating."""
import os
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.providers.base import QuestionProvider, get_provider, provider_names, register
from backend.app.providers.aloc import AlocProvider, NotConfigured
c = TestClient(app)


class _Resp:
    def __init__(self, payload):
        self._payload = payload
    def raise_for_status(self):
        pass
    def json(self):
        return self._payload


class _Client:
    def __init__(self, payload, seen):
        self._payload = payload
        self.seen = seen
    def get(self, url, params=None, headers=None):
        self.seen.append({"url": url, "params": params, "headers": headers})
        return _Resp(self._payload)
    def close(self):
        pass


def _aloc(payload=None, **kw):
    seen = []
    payload = payload if payload is not None else {"data": []}
    kw.setdefault("api_key", "test-key")
    kw.setdefault("base_url", "https://dev.aloc.com.ng")
    return AlocProvider(client=_Client(payload, seen), **kw), seen


def test_registry_lists_aloc():
    assert "aloc" in provider_names()
    assert c.get("/providers").json() == provider_names()


def test_unknown_provider_errors():
    r = c.post("/providers/nope/import", json={"subject": "Mathematics", "exam": "WAEC"}).json()
    assert "Unknown provider" in r["error"]


def test_aloc_requires_config():
    p, _ = _aloc(api_key="", base_url="")
    with pytest.raises(NotConfigured):
        p.fetch("Mathematics", "WAEC")


def test_aloc_header_auth_and_normalize():
    raw = {"id": "A1", "question": "  What is 2+2? ",
           "options": {"A": "3", "B": "4", "C": "5", "D": "6"},
           "answer": "4", "solution": "Because.", "topic": "Number Bases"}
    p, seen = _aloc({"data": [raw]})
    rows = p.fetch_normalized("Mathematics", "WAEC")
    assert seen[0]["url"] == "https://dev.aloc.com.ng/api/v1/questions"
    assert "/questions/questions" not in seen[0]["url"]
    assert seen[0]["headers"] == {"X-API-Key": "test-key"}  # header auth only
    assert "test-key" not in seen[0]["url"]
    assert "Authorization" not in seen[0]["headers"] and "access-token" not in seen[0]["headers"]
    n = rows[0]
    assert n["question_text"] == "What is 2+2?" and n["options"] == ["3", "4", "5", "6"]
    assert (n["subject"], n["exam_style"]) == ("Mathematics", "WAEC")
    assert n["source"] == "aloc" and n["source_reference"] == "A1"


def test_letter_resolution_abcd():
    p = AlocProvider(api_key="k", base_url="https://dev.aloc.com.ng")
    opts = ["A text", "B text", "C text", "D text"]
    for letter, want in [("A", "A text"), ("B", "B text"), ("C", "C text"), ("D", "D text"),
                         ("a", "A text"), ("b", "B text"), ("c", "C text"), ("d", "D text")]:
        n = p.normalize({"text": "S?", "options": list(opts), "correctAnswer": letter}, "Biology", "NECO")
        assert n["answer"] == want, letter


def test_letter_resolution_safe_fallbacks():
    p = AlocProvider(api_key="k", base_url="https://dev.aloc.com.ng")
    assert p.normalize({"text": "S?", "options": ["P", "Q"], "correctAnswer": "E"},
                       "Biology", "NECO")["answer"] == "E"  # out of range: unresolved
    assert p.normalize({"text": "S?", "options": [], "correctAnswer": "A"},
                       "Biology", "NECO")["answer"] == "A"  # missing option: unresolved
    assert p.normalize({"text": "S?", "options": ["P", "Q"], "correctAnswer": "Q"},
                       "Biology", "NECO")["answer"] == "Q"  # full text untouched


def test_provider_import_stages_for_review_not_production():
    raw = {"id": "B7", "question": "Provider staged Q?", "options": ["X", "Y"],
           "answer": "Y", "topic": "Photosynthesis"}
    p, _ = _aloc({"data": [raw]})
    from backend.app.providers import base as _base
    _base._PROVIDERS["aloc-test"] = p
    try:
        r = c.post("/providers/aloc-test/import",
                   json={"subject": "Biology", "exam": "NECO", "limit": 5}).json()
        assert r["provider"] == "aloc-test" and r["fetched"] == 1
        staged = r["staged"][0]
        assert staged["status"] in ("IMPORTED", "NEEDS_REVIEW")  # never auto-approved
        assert staged["topic"] == "Photosynthesis"
        assert staged["status"] == "NEEDS_REVIEW"  # no ALOC_LICENSE set: provenance gate holds
    finally:
        del _base._PROVIDERS["aloc-test"]
