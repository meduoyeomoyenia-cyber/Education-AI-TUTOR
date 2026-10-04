"""FastAPI MVP: health, syllabus, questions, attempts(+offline sync), ask(SSE stub), R2 presign stub."""
import json
import os
from pathlib import Path
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parents[1] / ".env")  # backend/.env (git-ignored secrets)
except ImportError:
    pass
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from .models import Base, SyllabusNode, Question, Attempt, Mastery

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./dev.db")
engine = create_engine(DATABASE_URL, future=True)
Base.metadata.create_all(engine)

app = FastAPI(title="Education AI Tutor API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in os.getenv("FRONTEND_ORIGINS", "http://localhost:3000").split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AttemptIn(BaseModel):
    user_id: int = 1
    question_id: int
    answer: str
    hint_used: bool = False
    offline_queued: bool = False

def mistake_type_for(correct: bool, hint_used: bool) -> str:
    if correct: return "none"
    return "minor" if hint_used else "conceptual"

@app.get("/health")
def health():
    return {"ok": True, "db": DATABASE_URL.split("://")[0]}

@app.get("/syllabus")
def syllabus(exam: Optional[str] = None, subject: Optional[str] = None, student_class: Optional[str] = Query(None, alias="class")):
    with Session(engine) as s:
        q = select(SyllabusNode)
        if exam: q = q.where(SyllabusNode.exam == exam)
        if subject: q = q.where(SyllabusNode.subject == subject)
        if student_class: q = q.where(SyllabusNode.student_class == student_class)
        rows = s.execute(q.limit(200)).scalars().all()
        return [{"id": r.id, "exam": r.exam, "class": r.student_class, "subject": r.subject, "topic": r.topic, "subtopic": r.subtopic} for r in rows]

@app.get("/subjects")
def subjects(exam: Optional[str] = None):
    with Session(engine) as s:
        q = select(SyllabusNode.subject).distinct().order_by(SyllabusNode.subject)
        if exam: q = q.where(SyllabusNode.exam == exam)
        return [r for r in s.execute(q).scalars().all()]

@app.get("/topics")
def topics(subject: Optional[str] = None):
    from .models import Topic
    with Session(engine) as s:
        q = select(Topic).order_by(Topic.subject, Topic.title)
        if subject: q = q.where(Topic.subject == subject)
        return [{"id": t.id, "subject": t.subject, "slug": t.slug, "title": t.title}
                for t in s.execute(q).scalars().all()]

@app.get("/questions")
def questions(topic: Optional[str] = None, difficulty: Optional[str] = None, topic_slug: Optional[str] = None, exam: Optional[str] = None):
    """topic_slug preferred; ?topic= kept as alias. exam filters exam_style (omitted = mixed bank)."""
    from .models import Topic
    with Session(engine) as s:
        if topic_slug:
            t = s.execute(select(Topic).where(Topic.slug == topic_slug)).scalars().first()
            if t is None:
                return []
            q = select(Question, SyllabusNode).join(SyllabusNode, Question.node_id == SyllabusNode.id).where(Question.topic_id == t.id)
        else:
            q = select(Question, SyllabusNode).join(SyllabusNode, Question.node_id == SyllabusNode.id)
            if topic: q = q.where(SyllabusNode.topic == topic)
        if difficulty: q = q.where(Question.difficulty == difficulty)
        if exam: q = q.where(Question.exam_style == exam)
        out = []
        for qu, node in s.execute(q.limit(100)).all():
            out.append({"id": qu.id, "stem": qu.stem, "options": qu.options, "difficulty": qu.difficulty, "exam_style": qu.exam_style, "topic": node.topic, "subject": node.subject})
        return out

def _import_out(r):
    from .models import QuestionImport  # noqa
    return {"id": r.id, "question_text": r.question_text, "options": r.options, "answer": r.answer,
            "explanation": r.explanation, "subject": r.subject, "topic": r.topic, "topic_id": r.topic_id,
            "exam_style": r.exam_style, "difficulty": r.difficulty, "source": r.source,
            "source_reference": r.source_reference, "license": r.license, "status": r.status,
            "validation_status": r.validation_status, "validation_notes": r.validation_notes,
            "reviewer_notes": r.reviewer_notes}

class ImportBatchIn(BaseModel):
    items: list

@app.post("/question-imports/batch")
def import_batch_ep(b: ImportBatchIn):
    from .models import QuestionImport
    from .ingest import ensure_imports_schema, import_batch
    ensure_imports_schema()
    with Session(engine) as s:
        rows = import_batch(s, b.items)
        return [_import_out(r) for r in rows]

@app.get("/question-imports")
def list_imports(status: Optional[str] = None):
    from .models import QuestionImport
    with Session(engine) as s:
        q = select(QuestionImport).order_by(QuestionImport.id)
        if status: q = q.where(QuestionImport.status == status.upper())
        return [_import_out(r) for r in s.execute(q.limit(200)).scalars().all()]

@app.get("/question-imports/{imp_id}")
def get_import(imp_id: int):
    from .models import QuestionImport
    with Session(engine) as s:
        r = s.get(QuestionImport, imp_id)
        return _import_out(r) if r else {"error": "not found"}

class ReviewIn(BaseModel):
    reviewer_notes: str = ""

@app.post("/question-imports/{imp_id}/approve")
def approve_import(imp_id: int, v: ReviewIn):
    from .models import QuestionImport
    from .ingest import promote
    with Session(engine) as s:
        r = s.get(QuestionImport, imp_id)
        if r is None: return {"error": "not found"}
        try:
            q = promote(s, r, v.reviewer_notes)
            return {"status": "APPROVED", "question_id": q.id, "topic_id": q.topic_id, "exam_style": q.exam_style}
        except ValueError as e:
            return {"error": str(e), "status": r.status}

def _set_status(imp_id: int, status: str, notes: str):
    from .models import QuestionImport
    from datetime import datetime, timezone
    with Session(engine) as s:
        r = s.get(QuestionImport, imp_id)
        if r is None: return {"error": "not found"}
        r.status = status
        if notes: r.reviewer_notes = notes
        r.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
        s.commit()
        return _import_out(r)

@app.post("/question-imports/{imp_id}/reject")
def reject_import(imp_id: int, v: ReviewIn):
    return _set_status(imp_id, "REJECTED", v.reviewer_notes)

@app.post("/question-imports/{imp_id}/revision")
def revision_import(imp_id: int, v: ReviewIn):
    return _set_status(imp_id, "NEEDS_REVISION", v.reviewer_notes)

class ProviderImportIn(BaseModel):
    subject: str
    exam: str
    topic: Optional[str] = None
    limit: int = 20

@app.get("/providers")
def list_providers():
    from .providers.base import provider_names
    from .providers import aloc  # noqa: F401 (registers aloc)
    return provider_names()

@app.post("/providers/{name}/import")
def provider_import(name: str, b: ProviderImportIn):
    """Fetch via provider -> normalize -> STAGE for teacher review. Never writes to Question."""
    from .providers.base import get_provider
    from .providers import aloc  # noqa: F401 (registers aloc)
    from .ingest import ensure_imports_schema, import_batch
    ensure_imports_schema()
    try:
        provider = get_provider(name)
    except ValueError as e:
        return {"error": str(e)}
    try:
        items = provider.fetch_normalized(b.subject, b.exam, b.topic, max(1, min(b.limit, 100)))
    except Exception as e:
        return {"error": f"{name} fetch failed: {e}"}
    with Session(engine) as s:
        rows = import_batch(s, items)
        return {"provider": name, "fetched": len(items), "staged": [_import_out(r) for r in rows]}

@app.get("/lessons")
def lessons(topic: Optional[str] = None, node_id: Optional[int] = None, language: str = "en", brief: int = 0, topic_slug: Optional[str] = None):
    """Vetted lesson by topic_slug (preferred), node_id, or ?topic= alias. brief=1 omits body for Data Saver."""
    from .models import Lesson, Topic
    with Session(engine) as s:
        if topic_slug:
            t = s.execute(select(Topic).where(Topic.slug == topic_slug)).scalars().first()
            if t is None:
                return {"error": "lesson not found", "topic_slug": topic_slug}
            q = select(Lesson, SyllabusNode).join(SyllabusNode, Lesson.node_id == SyllabusNode.id).where(Lesson.topic_id == t.id)
        else:
            q = select(Lesson, SyllabusNode).join(SyllabusNode, Lesson.node_id == SyllabusNode.id)
            if node_id is not None:
                q = q.where(Lesson.node_id == node_id)
            elif topic:
                q = q.where(SyllabusNode.topic == topic)
            else:
                return {"error": "provide topic_slug, topic or node_id"}
        row = s.execute(q.where(Lesson.language == language).limit(1)).first()
        if row is None and language != "en":
            row = s.execute(q.where(Lesson.language == "en").limit(1)).first()
            fallback = True
        else:
            fallback = False
        if row is None:
            return {"error": "lesson not found", "topic": topic, "node_id": node_id, "topic_slug": topic_slug}
        ls, node = row
        tslug = None
        if ls.topic_id is not None:
            t = s.get(Topic, ls.topic_id)
            tslug = t.slug if t else None
        body = {"id": ls.id, "node_id": ls.node_id, "topic_slug": tslug, "language": ls.language, "fallback_to_en": fallback,
                "subject": node.subject, "topic": node.topic, "exam": node.exam, "class": node.student_class,
                "title": ls.title, "objectives": ls.objectives, "key_points": ls.key_points,
                "reading_mins": ls.reading_mins, "source": ls.source}
        if not brief:
            body.update({"explanation": ls.explanation, "examples": ls.examples, "media": ls.media})
        body["bytes"] = len(json.dumps(body))
        return body

@app.post("/attempts")
def submit_attempt(a: AttemptIn):
    with Session(engine) as s:
        qu = s.get(Question, a.question_id)
        if not qu: return {"error": "question not found"}
        correct = a.answer.strip().lower() == qu.answer.strip().lower()
        mt = mistake_type_for(correct, a.hint_used)
        s.add(Attempt(user_id=a.user_id, question_id=a.question_id, answer=a.answer, correct=correct, mistake_type=mt, hint_used=a.hint_used, offline_queued=a.offline_queued))
        s.commit()
        hint = None if correct else "Try again — add both equations to eliminate y." if "simultaneous" in (qu.stem or "").lower() else "Give it one more try, then ask for a hint."
        return {"correct": correct, "mistake_type": mt, "hint": hint}

@app.post("/attempts/sync")
def sync_attempts(items: List[AttemptIn]):
    return [submit_attempt(a) for a in items]

@app.get("/mastery/{user_id}")
def mastery(user_id: int):
    from .mastery import topic_stats
    with Session(engine) as s:
        return topic_stats(s, user_id)

@app.get("/analysis/{user_id}")
def analysis(user_id: int):
    from .mastery import topic_stats, analyze
    with Session(engine) as s:
        stats = topic_stats(s, user_id)
        return {"stats": stats, **analyze(stats)}

@app.get("/plan/today/{user_id}")
def plan_today(user_id: int, minutes: int = 30):
    from .mastery import topic_stats, today_plan
    with Session(engine) as s:
        return today_plan(topic_stats(s, user_id), minutes)

@app.get("/notifications/{user_id}")
def notifications(user_id: int):
    from .mastery import topic_stats
    with Session(engine) as s:
        stats = topic_stats(s, user_id)
        weak = [x for x in stats if x["level"] == "NeedsRevision"][:3]
        notes = [f"You have {len(weak)} topics that need revision."] if weak else ["You're on track. Keep your streak."]
        return {"items": notes, "throttle": "max 3/day, opt-in"}

class AskIn(BaseModel):
    message: str
    language: str = "en"
    style: str = "auto"
    topic: Optional[str] = None
    user_id: int = 1

def stream_text(text: str):
    return StreamingResponse(iter([text]), media_type="text/event-stream")

@app.post("/ask")
def ask(a: AskIn):
    from .tutor.engine import respond
    with Session(engine) as s:
        return stream_text(respond(s, a.user_id, a.message, a.language, a.style, a.topic, "ask"))

@app.post("/explain")
def explain(a: AskIn):
    from .tutor.engine import respond
    with Session(engine) as s:
        return stream_text(respond(s, a.user_id, a.message, a.language, a.style, a.topic, "explain"))

@app.post("/hint")
def hint(a: AskIn):
    from .tutor.engine import respond
    with Session(engine) as s:
        return stream_text(respond(s, a.user_id, a.message, a.language, a.style, a.topic, "hint"))

@app.post("/uploads/presign")
def presign(filename: str, content_type: str = "image/jpeg"):
    from .media import presign as r2presign
    return {**r2presign(filename, content_type), "content_type": content_type}

class VoiceIn(BaseModel):
    language: str = "en"
    audio_key: str = ""

@app.post("/voice/transcribe")
def voice_transcribe(v: VoiceIn):
    from .media import transcribe_stub
    return {"text": transcribe_stub(v.language), "note": "voice optional — text always works"}

class SpeakIn(BaseModel):
    text: str

@app.post("/voice/speak")
def voice_speak(v: SpeakIn):
    from .media import speak_stub
    return speak_stub(v.text)

class ImageHelpIn(BaseModel):
    image_key: str = ""
    caption: str = ""
    topic: Optional[str] = None
    language: str = "en"

@app.post("/image/help")
def image_help(v: ImageHelpIn):
    from .media import image_help_stub
    from .tutor.engine import respond
    with Session(engine) as s:
        guide = image_help_stub(v.caption, v.topic)
        return stream_text(respond(s, 1, f"Image task ({v.image_key}): {guide}", v.language, "step-by-step", v.topic, "ask"))

class KbIn(BaseModel):
    session: str = "demo"
    kb: int = 0
    media: str = "text"

@app.post("/media/log")
def media_log(v: KbIn):
    from .media import log_kb
    return log_kb(v.session, v.kb, v.media)

class SafetyIn(BaseModel):
    text: str = ""

@app.post("/safety/check")
def safety_check(v: SafetyIn):
    from .safety import scan
    return scan(v.text)

class ReportIn(BaseModel):
    user_id: int = 1
    kind: str = "bullying"
    ref: str = ""

@app.post("/safety/report")
def safety_report(v: ReportIn):
    from .safety import report
    return report(v.user_id, v.kind, v.ref)
