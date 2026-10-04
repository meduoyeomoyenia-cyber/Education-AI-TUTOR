"""ALOC mapping verification (mocked only — no live requests)."""
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session
from backend.app.main import app, engine
from backend.app.models import Question, QuestionImport, Topic
from backend.app.providers.aloc import AlocProvider
c = TestClient(app)
TAG = "ALOCTEST"


def _stage(payload):
    return c.post("/question-imports/batch", json={"items": [payload]}).json()[0]


def _live_shape(stem, **kw):
    d = {"question_text": stem, "options": ["P", "Q"], "answer": "Q",
         "subject": "Biology", "exam_style": "NECO", "id": "AL1",
         "source": "aloc-blessed", "source_reference": "ref-1", "license": "licensed"}
    d.update(kw)
    return d


def test_1_2_3_4_field_mapping():
    n = AlocProvider(api_key="k", base_url="https://dev.aloc.com.ng").normalize(
        {"text": "Real stem?", "options": ["P", "Q"], "correctAnswer": "Q",
         "id": "Z9", "topic": "Photosynthesis"}, "Biology", "NECO")
    assert n["question_text"] == "Real stem?"  # 1.
    assert n["answer"] == "Q"  # 2.
    assert n["options"] == ["P", "Q"]  # 3.
    assert n["source_reference"] == "Z9"  # 4.


def test_5_missing_license_needs_review():
    r = _stage(_live_shape(f"{TAG} no license?", license=""))
    assert r["status"] == "NEEDS_REVIEW" and "license" in r["validation_notes"].lower()


def test_6_no_auto_topic_creation():
    before = len(c.get("/topics").json())
    r = _stage(_live_shape(f"{TAG} unknown?", topic="Xyzzy Unknown",
                           source="aloc-x", source_reference="r", license="licensed"))
    assert r["status"] == "NEEDS_REVIEW" and r["topic_id"] is None
    assert len(c.get("/topics").json()) == before


def test_7_exact_match_when_safe():
    r = _stage(_live_shape(f"{TAG} exact?", topic="Photosynthesis",
                           source="aloc-x", source_reference="r", license="licensed"))
    assert r["topic_id"] is not None and r["status"] == "IMPORTED"


def test_8_unmatched_goes_review():
    r = _stage(_live_shape(f"{TAG} section?", topic="", section="Some Section",
                           source="aloc-x", source_reference="r", license="licensed"))
    assert r["topic_id"] is None and r["status"] == "NEEDS_REVIEW"


def test_9_dup_still_caught():
    base = _live_shape(f"{TAG} dup?", topic="Photosynthesis", source="aloc-x", source_reference="r", license="licensed")
    out = c.post("/question-imports/batch", json={"items": [base, dict(base)]}).json()
    assert out[0]["status"] == "IMPORTED"
    assert out[1]["status"] == "NEEDS_REVIEW" and "uplicate" in out[1]["validation_notes"]


def test_10_production_untouched():
    with Session(engine) as s:
        assert s.execute(select(Question).where(Question.stem.like(f"{TAG}%"))).scalars().first() is None
        assert s.execute(select(Question).where(Question.source == "aloc")).scalars().first() is None
