"""STEP 3 ingestion pipeline: validate -> topic-match -> stage -> review -> promote.
Deterministic only. No AI, no external services."""
import re
from sqlalchemy import select
from sqlalchemy.orm import Session
from .models import Question, QuestionImport, SyllabusNode, Topic

EXAMS = ("WAEC", "JAMB", "NECO")
STATUSES = ("IMPORTED", "NEEDS_REVIEW", "APPROVED", "REJECTED", "NEEDS_REVISION")
PROVENANCE_EXEMPT_SOURCES = {"step3-test-fixture", "step3-test", "test-fixture"}

PROVENANCE_EXEMPT_SOURCES = {"step3-test-fixture", "step3-test", "test-fixture"}
TEMPLATE_SOURCES = {"template-example"}
TEMPLATE_MARK = "[DO-NOT-IMPORT]"

def ensure_imports_schema():
    """Additive migrations for staging + production provenance columns."""
    from sqlalchemy import text
    from .main import engine
    from .models import Base
    Base.metadata.create_all(engine)
    with engine.begin() as conn:
        cols = [r[1] for r in conn.execute(text("PRAGMA table_info(question_imports)"))]
        if "license" not in cols:
            conn.execute(text("ALTER TABLE question_imports ADD COLUMN license VARCHAR(128)"))
        qcols = [r[1] for r in conn.execute(text("PRAGMA table_info(questions)"))]
        if "source_reference" not in qcols:
            conn.execute(text("ALTER TABLE questions ADD COLUMN source_reference VARCHAR(256)"))

def is_placeholder(item: dict) -> bool:
    """Draft/placeholder rows (e.g. questions.draft.json) must never be importable."""
    if (item.get("status") or "").strip().lower() == "draft":
        return True
    return (item.get("question_text") or "").strip().startswith("[DRAFT]")

def normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", (text or "").lower())

def match_topic(db: Session, subject: str, topic: str):
    """Exact (subject, title) match, case-insensitive. Never creates topics."""
    if not subject or not topic:
        return None
    rows = db.execute(select(Topic).where(Topic.subject == subject)).scalars().all()
    want = normalize(topic)
    for t in rows:
        if normalize(t.title) == want:
            return t
    return None

def known_subjects(db: Session) -> set:
    return {r for r in db.execute(select(SyllabusNode.subject).distinct()).scalars().all()}

def production_dup(db: Session, stem: str, exclude_id: int | None = None) -> bool:
    key = normalize(stem)
    for (s,) in db.execute(select(Question.stem)).all():
        if normalize(s) == key:
            return True
    return False

def validate(db: Session, item: dict, batch_keys: set) -> tuple[bool, str, object | None]:
    """Returns (ok, notes, topic). Never writes."""
    if is_placeholder(item):
        return False, "Draft/placeholder content cannot be imported.", None
    if TEMPLATE_MARK in (item.get("question_text") or "") or (item.get("source") or "").strip() in TEMPLATE_SOURCES:
        return False, "Template example content must never enter production.", None
    notes = []
    text = (item.get("question_text") or "").strip()
    if not text:
        notes.append("Missing question text.")
    answer = (item.get("answer") or "").strip()
    if not answer:
        notes.append("Missing answer.")
    subject = (item.get("subject") or "").strip()
    if not subject:
        notes.append("Missing subject.")
    elif subject not in known_subjects(db):
        notes.append(f"Unknown subject: {subject}.")
    if (item.get("source") or "").strip() not in PROVENANCE_EXEMPT_SOURCES:
        if not (item.get("source") or "").strip():
            notes.append("Missing source/provenance.")
        if not (item.get("source_reference") or "").strip():
            notes.append("Missing source_reference.")
        if not (item.get("license") or "").strip():
            notes.append("Missing license/provenance.")
    exam = (item.get("exam_style") or "").strip().upper()
    if exam not in EXAMS:
        notes.append(f"Invalid exam_style: {item.get('exam_style')}.")
    options = item.get("options") or []
    if options:
        if len(options) < 2:
            notes.append("Options must have at least 2 choices.")
        elif answer and answer not in options:
            notes.append("Answer does not match an available option.")
    key = normalize(text)
    if text and key in batch_keys:
        notes.append("Duplicate question text within the import.")
    topic = match_topic(db, subject, (item.get("topic") or "").strip())
    if not (item.get("topic") or "").strip():
        notes.append("No topic proposed; needs teacher topic assignment.")
    elif topic is None and subject in known_subjects(db):
        notes.append("Topic could not be matched to an existing topic.")
    if text and production_dup(db, text):
        notes.append("Likely duplicate of an existing production question.")
    ok = not notes
    return ok, ("Question text is present; answer is valid; topic matched." if ok else " ".join(notes)), topic

def import_batch(db: Session, items: list) -> list:
    rows = []
    seen = set()
    for item in items:
        ok, notes, topic = validate(db, item, seen)
        seen.add(normalize(item.get("question_text") or ""))
        from datetime import datetime, timezone
        now = lambda: datetime.now(timezone.utc).replace(tzinfo=None)
        rows.append(QuestionImport(
            question_text=(item.get("question_text") or "").strip(),
            options=item.get("options") or [],
            answer=(item.get("answer") or "").strip(),
            explanation=item.get("explanation") or "",
            subject=(item.get("subject") or "").strip(),
            topic=(item.get("topic") or "").strip(),
            topic_id=topic.id if topic else None,
            exam_style=(item.get("exam_style") or "").strip().upper(),
            difficulty=item.get("difficulty") or "Basic",
            source=item.get("source") or "",
            source_reference=item.get("source_reference") or "",
            license=item.get("license") or "",
            status="IMPORTED" if ok else "NEEDS_REVIEW",
            validation_status="PASS" if ok else "FAIL",
            validation_notes=notes,
            created_at=now(), updated_at=now(),
        ))
    db.add_all(rows)
    db.commit()
    return rows

def promote(db: Session, row: QuestionImport, reviewer_notes: str = "") -> Question:
    """Approve -> production Question. Re-checks topic link + duplicates."""
    if TEMPLATE_MARK in (row.question_text or "") or (row.source or "").strip() in TEMPLATE_SOURCES:
        raise ValueError("Cannot approve: template example content must never enter production.")
    if row.topic_id is None:
        raise ValueError("Cannot approve: topic not matched.")
    if production_dup(db, row.question_text):
        row.status = "NEEDS_REVIEW"
        row.validation_status = "FAIL"
        row.validation_notes = (row.validation_notes + " Likely duplicate of an existing production question.").strip()
        db.commit()
        raise ValueError("Cannot approve: likely duplicate of an existing production question.")
    node = db.execute(select(SyllabusNode).where(SyllabusNode.topic_id == row.topic_id).limit(1)).scalars().first()
    if node is None:
        raise ValueError("Cannot approve: no syllabus node for topic.")
    from datetime import datetime, timezone
    q = Question(node_id=node.id, topic_id=row.topic_id, stem=row.question_text, options=row.options,
                 answer=row.answer, difficulty=row.difficulty, exam_style=row.exam_style,
                 source=row.source or "teacher-approved", license=row.license or "proprietary",
                 source_reference=row.source_reference or "",
                 mistake_tags=[], lang_variants={})
    db.add(q)
    row.status = "APPROVED"
    row.reviewer_notes = reviewer_notes
    row.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
    db.commit()
    return q
