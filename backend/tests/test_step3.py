"""STEP 3 pipeline tests: import -> validate -> stage -> review -> promote."""
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session
from backend.app.main import app, engine
from backend.app.models import Question, QuestionImport, Topic
c = TestClient(app)
TAG = "STEP3TEST"

@pytest.fixture(scope="module", autouse=True)
def _cleanup_step3test_rows():
    yield
    with Session(engine) as s:  # remove only this suite's own artifacts; vetted data untouched
        for q in s.execute(select(Question).where(Question.stem.like(f"{TAG}%"))).scalars().all():
            s.delete(q)
        for r in s.execute(select(QuestionImport).where(QuestionImport.source == "step3-test")).scalars().all():
            s.delete(r)
        s.commit()

def _staged(stem):
    with Session(engine) as s:
        return s.execute(select(QuestionImport).where(QuestionImport.question_text == stem)).scalars().first()

def _ensure_import(payload):
    r = _staged(payload["question_text"])
    if r: return r.id
    out = c.post("/question-imports/batch", json={"items": [payload]}).json()
    return out[0]["id"]

def test_1_import_valid():
    iid = _ensure_import({"question_text": f"{TAG} valid simultaneous?", "options": ["1", "2"],
                          "answer": "2", "subject": "Mathematics",
                          "topic": "Algebra: Simultaneous Equations", "exam_style": "JAMB",
                          "source": "step3-test"})
    r = c.get(f"/question-imports/{iid}").json()
    assert r["status"] in ("IMPORTED", "APPROVED") and r["topic_id"] is not None  # 4. topic matched

def test_2_invalid_needs_review():
    iid = _ensure_import({"question_text": "", "answer": "", "subject": "Nope",
                          "topic": "Nothing Here", "exam_style": "XXX", "source": "step3-test"})
    r = c.get(f"/question-imports/{iid}").json()
    assert r["status"] == "NEEDS_REVIEW" and r["validation_status"] == "FAIL"
    assert "Missing question text" in r["validation_notes"] and "Unknown subject" in r["validation_notes"]

def test_5_unknown_topic_creates_nothing():
    n_before = len(c.get("/topics").json())
    iid = _ensure_import({"question_text": f"{TAG} unknown topic?", "options": ["1", "2"], "answer": "1",
                          "subject": "Mathematics", "topic": "Quantum underwater basket", "exam_style": "WAEC",
                          "source": "step3-test"})
    r = c.get(f"/question-imports/{iid}").json()
    assert r["status"] == "NEEDS_REVIEW" and r["topic_id"] is None
    assert "could not be matched" in r["validation_notes"]
    assert len(c.get("/topics").json()) == n_before  # no auto-created topic

def test_7_duplicate_in_batch():
    stem = f"{TAG} dup within batch?"
    out = c.post("/question-imports/batch", json={"items": [
        {"question_text": stem, "options": ["1", "2"], "answer": "1", "subject": "Biology",
         "topic": "Photosynthesis", "exam_style": "WAEC", "source": "step3-test"},
        {"question_text": stem, "options": ["1", "2"], "answer": "1", "subject": "Biology",
         "topic": "Photosynthesis", "exam_style": "WAEC", "source": "step3-test"}]}).json()
    assert out[1]["status"] == "NEEDS_REVIEW" and "Duplicate" in out[1]["validation_notes"]

def test_8_9_approve_promotes():
    stem = f"{TAG} approve me photosynthesis NECO?"
    iid = _ensure_import({"question_text": stem, "options": ["A", "B"], "answer": "B",
                          "subject": "Biology", "topic": "Photosynthesis", "exam_style": "NECO",
                          "source": "step3-test"})
    cur = c.get(f"/question-imports/{iid}").json()
    if cur["status"] != "APPROVED":
        r = c.post(f"/question-imports/{iid}/approve", json={"reviewer_notes": "looks good"}).json()
        assert r["status"] == "APPROVED"  # 8.
    with Session(engine) as s:
        q = s.execute(select(Question).where(Question.stem == stem)).scalars().one()  # 9.
        assert q.exam_style == "NECO" and q.topic_id is not None  # 6. exam preserved

def test_10_reject_stays_out():
    stem = f"{TAG} reject me?"
    iid = _ensure_import({"question_text": stem, "options": ["A", "B"], "answer": "A",
                          "subject": "Chemistry", "topic": "Acids and Bases", "exam_style": "WAEC",
                          "source": "step3-test"})
    c.post(f"/question-imports/{iid}/reject", json={"reviewer_notes": "bad"}).json()
    assert c.get(f"/question-imports/{iid}").json()["status"] == "REJECTED"
    with Session(engine) as s:
        assert s.execute(select(Question).where(Question.stem == stem)).scalars().first() is None

def test_11_revision_stays_staged():
    stem = f"{TAG} revise me?"
    iid = _ensure_import({"question_text": stem, "options": ["A", "B"], "answer": "A",
                          "subject": "Chemistry", "topic": "Acids and Bases", "exam_style": "WAEC",
                          "source": "step3-test"})
    c.post(f"/question-imports/{iid}/revision", json={"reviewer_notes": "fix wording"}).json()
    assert c.get(f"/question-imports/{iid}").json()["status"] == "NEEDS_REVISION"

def test_12_13_approved_in_practice_with_filter():
    slug = "biology/photosynthesis"
    all_q = c.get("/questions", params={"topic_slug": slug}).json()
    assert any(TAG in q["stem"] for q in all_q)  # 12.
    neco = c.get("/questions", params={"topic_slug": slug, "exam": "NECO"}).json()
    assert any(TAG in q["stem"] for q in neco)  # 13.
    jamb = c.get("/questions", params={"topic_slug": slug, "exam": "JAMB"}).json()
    assert not any(TAG in q["stem"] for q in jamb)

def test_15_existing_data_intact():
    with Session(engine) as s:
        assert s.query(Question).filter(Question.source == "original").count() == 8
        assert s.query(Topic).count() == 4

def test_draft_placeholder_rejected():
    out = c.post("/question-imports/batch", json={"items": [
        {"question_text": "[DRAFT] Generate Photosynthesis practice question.", "status": "draft",
         "subject": "Biology", "topic": "Photosynthesis", "exam_style": "WAEC", "source": "x",
         "source_reference": "y", "license": "z"}]}).json()
    assert out[0]["status"] == "NEEDS_REVIEW" and "placeholder" in out[0]["validation_notes"]
    with Session(engine) as s:
        assert s.execute(select(Question).where(Question.stem.like("[DRAFT]%"))).scalars().first() is None

def test_provenance_required_unless_exempt():
    bad = c.post("/question-imports/batch", json={"items": [
        {"question_text": f"{TAG} no provenance?", "options": ["A", "B"], "answer": "A",
         "subject": "Biology", "topic": "Photosynthesis", "exam_style": "WAEC", "source": "owner-file"}]}).json()
    assert bad[0]["status"] == "NEEDS_REVIEW" and "source_reference" in bad[0]["validation_notes"]
    good = c.post("/question-imports/batch", json={"items": [
        {"question_text": f"{TAG} provenance ok?", "options": ["A", "B"], "answer": "A",
         "subject": "Biology", "topic": "Photosynthesis", "exam_style": "WAEC",
         "source": "owner-file", "source_reference": "bio-pack-v1", "license": "licensed"}]}).json()
    assert good[0]["status"] == "IMPORTED" and good[0]["license"] == "licensed"

def test_template_examples_blocked_and_unpromotable():
    import json as _json, pathlib as _pl
    tpl = _json.loads((_pl.Path(__file__).resolve().parents[2] / "content" / "step4b_import_template.json").read_text(encoding="utf-8"))
    assert 2 <= len(tpl) <= 3
    out = c.post("/question-imports/batch", json={"items": tpl}).json()
    assert all(r["status"] == "NEEDS_REVIEW" and "Template example" in r["validation_notes"] for r in out)
    for r in out:
        denied = c.post(f"/question-imports/{r['id']}/approve", json={"reviewer_notes": "x"}).json()
        assert "template" in denied["error"].lower()
    with Session(engine) as s:
        assert s.execute(select(Question).where(Question.source == "template-example")).scalars().first() is None

def test_approval_preserves_full_provenance():
    stem = f"{TAG} full provenance?"
    iid = _ensure_import({"question_text": stem, "options": ["A", "B"], "answer": "A",
                          "subject": "Chemistry", "topic": "Acids and Bases", "exam_style": "JAMB",
                          "source": "owner-file", "source_reference": "chem-pack-v1", "license": "teacher-created"})
    cur = c.get(f"/question-imports/{iid}").json()
    assert cur["status"] == "IMPORTED"
    r = c.post(f"/question-imports/{iid}/approve", json={"reviewer_notes": "ok"}).json()
    assert r["status"] == "APPROVED"
    with Session(engine) as s:
        q = s.execute(select(Question).where(Question.stem == stem)).scalars().one()
        assert (q.source, q.source_reference, q.license, q.exam_style) == ("owner-file", "chem-pack-v1", "teacher-created", "JAMB")
        assert q.topic_id is not None
        # row left for module teardown (deletes STEP3TEST production rows); reruns re-import fresh
