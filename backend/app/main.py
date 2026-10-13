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
from .auth import Base as AuthBase

def normalize_db_url(url: str) -> str:
    """Render's older Postgres URLs use the postgres:// scheme, which
    SQLAlchemy 2.x rejects. Normalize to postgresql://. Pure function."""
    if url.startswith("postgres://"):
        return "postgresql://" + url[len("postgres://"):]
    return url


DATABASE_URL = normalize_db_url(os.getenv("DATABASE_URL", "sqlite:///./dev.db"))


def _engine_options(url: str) -> dict:
    """Finite connect timeout for PostgreSQL only. SQLite takes no options."""
    if url.startswith("postgresql"):
        return {"connect_args": {"connect_timeout": 10}}
    return {}


engine = create_engine(DATABASE_URL, future=True, **_engine_options(DATABASE_URL))
if DATABASE_URL.startswith("sqlite:"):
    import logging
    logging.getLogger("uvicorn.error").warning(
        "DATABASE_URL is not set: using ephemeral local SQLite. "
        + ("On Render this means data is LOST on restart: set DATABASE_URL to Postgres." if os.getenv("RENDER") else "Set DATABASE_URL for a persistent database.")
    )

from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app):
    """Schema setup runs here (not at import) so the server binds its port
    immediately even if the database is slow. A failing DB never blocks boot.
    First boot on an empty DB also seeds content once (guarded, idempotent)."""
    import logging
    log = logging.getLogger("uvicorn.error")
    try:
        Base.metadata.create_all(engine)
        AuthBase.metadata.create_all(engine)
    except Exception as e:
        log.warning(f"DB schema setup failed at startup: {type(e).__name__}")
    try:
        from .seed_all import ensure_seeded
        result = ensure_seeded()
        if result not in ("already-seeded", "seeded"):
            log.warning(f"Content seed status at startup: {result}")
    except Exception as e:
        log.warning(f"Content seed check failed at startup: {type(e).__name__}")
    yield


def db_is_ready() -> tuple:
    """Real check per call: True only if a query succeeds right now."""
    from sqlalchemy import text
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True, ""
    except Exception as e:
        return False, type(e).__name__


app = FastAPI(title="Education AI Tutor API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in os.getenv("FRONTEND_ORIGINS", "http://localhost:3000").split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PUBLIC_PATHS = ("/health", "/subjects", "/topics", "/openapi.json", "/docs")
PUBLIC_PREFIXES = ("/auth/", "/openapi", "/docs")


@app.middleware("http")
async def auth_gate(request, call_next):
    """Sign-in gate: everything except health/auth/browse-subjects-topics needs a token.
    Teacher staging (/question-imports, /providers) and safety reports stay public (prototype).
    AUTH_DISABLED=1 (tests only) bypasses the gate; never set in production."""
    from fastapi.responses import JSONResponse
    from .auth import check_token
    path = request.url.path
    if (request.method == "OPTIONS" or path in PUBLIC_PATHS
            or any(path.startswith(p) for p in PUBLIC_PREFIXES)
            or os.getenv("AUTH_DISABLED") == "1"):
        return await call_next(request)
    auth = (request.headers.get("authorization") or "")
    if auth.lower().startswith("bearer ") and check_token(auth[7:]) is not None:
        return await call_next(request)
    return JSONResponse(status_code=401, content={"error": "Sign in required.", "signin": "/signin"})

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
    ready, error = db_is_ready()
    body = {"ok": True, "db": DATABASE_URL.split("://")[0], "db_ready": ready}
    if not ready:
        body["db_error"] = error
    try:
        from sqlalchemy.orm import Session as _Session
        from .models import SeedState as _SeedState
        with _Session(engine) as _s:
            _row = _s.get(_SeedState, "v1")
            body["seed_status"] = _row.status if _row else "unknown"
    except Exception:
        body["seed_status"] = "unknown"
    return body

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
            "source_reference": r.source_reference, "license": r.license,
            "provider_meta": r.provider_meta, "status": r.status,
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

class OtpRequestIn(BaseModel):
    phone: str

@app.post("/auth/request")
def auth_request(v: OtpRequestIn):
    from .auth import request_code
    with Session(engine) as s:
        try:
            return request_code(s, v.phone)
        except ValueError as e:
            return {"error": str(e)}

class OtpVerifyIn(BaseModel):
    phone: str
    code: str
    name: str = ""

@app.post("/auth/verify")
def auth_verify(v: OtpVerifyIn):
    from .auth import verify_code
    with Session(engine) as s:
        try:
            out = verify_code(s, v.phone, v.code)
            if v.name.strip():
                from .models import User
                user = s.get(User, out["profile"]["id"])
                if user and not user.full_name:
                    user.full_name = v.name.strip()[:128]
                    s.commit()
                    out["profile"]["name"] = user.full_name
            return out
        except ValueError as e:
            return {"error": str(e)}

class LoginIn(BaseModel):
    phone: str
    name: str = ""

@app.post("/auth/login")
def auth_login(v: LoginIn):
    """One-step sign-in (name + phone, no OTP). Issues the same token."""
    from .auth import simple_login
    with Session(engine) as s:
        try:
            return simple_login(s, v.phone, v.name)
        except ValueError as e:
            return {"error": str(e)}

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
