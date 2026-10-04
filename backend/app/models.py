"""Tables work on PostgreSQL (prod) and SQLite (dev). Set DATABASE_URL, default sqlite."""
from sqlalchemy import Column, Integer, String, Text, Boolean, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import declarative_base
from datetime import datetime, timezone
Base = declarative_base()

class Topic(Base):
    """Reusable canonical topic. NOT exam-specific. One row per (subject, topic)."""
    __tablename__ = "topics"
    id = Column(Integer, primary_key=True)
    subject = Column(String(64), index=True)
    slug = Column(String(128), unique=True, index=True)
    title = Column(String(128))

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    phone = Column(String(32), unique=True, index=True)
    full_name = Column(String(128), default="")
    student_class = Column(String(8))
    language = Column(String(8), default="en")

class SyllabusNode(Base):
    __tablename__ = "syllabus_nodes"
    id = Column(Integer, primary_key=True)
    exam = Column(String(16), index=True)
    student_class = Column(String(8), index=True)
    subject = Column(String(64), index=True)
    topic = Column(String(128), index=True)
    subtopic = Column(String(128), default="")
    objectives = Column(JSON, default=list)
    prerequisites = Column(JSON, default=list)
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=True, index=True)

class Question(Base):
    __tablename__ = "questions"
    id = Column(Integer, primary_key=True)
    node_id = Column(Integer, ForeignKey("syllabus_nodes.id"), index=True)
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=True, index=True)
    stem = Column(Text)
    options = Column(JSON, default=list)
    answer = Column(Text)
    difficulty = Column(String(16), index=True)
    exam_style = Column(String(16))
    source = Column(String(128), default="original")
    license = Column(String(64), default="proprietary")
    source_reference = Column(String(256), default="")
    mistake_tags = Column(JSON, default=list)
    lang_variants = Column(JSON, default=dict)

class Attempt(Base):
    __tablename__ = "attempts"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, index=True, default=1)
    question_id = Column(Integer, index=True)
    answer = Column(Text)
    correct = Column(Boolean, default=False)
    mistake_type = Column(String(16), default="minor")
    hint_used = Column(Boolean, default=False)
    offline_queued = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

class Mastery(Base):
    __tablename__ = "mastery"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, index=True, default=1)
    node_id = Column(Integer, index=True)
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=True, index=True)
    level = Column(String(16), default="Developing")
    score = Column(Float, default=0.0)

class Lesson(Base):
    """Vetted curriculum lesson. One row per (syllabus node, language)."""
    __tablename__ = "lessons"
    id = Column(Integer, primary_key=True)
    node_id = Column(Integer, ForeignKey("syllabus_nodes.id"), index=True)
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=True, index=True)
    language = Column(String(8), default="en", index=True)
    title = Column(String(256))
    objectives = Column(JSON, default=list)
    explanation = Column(Text)
    examples = Column(JSON, default=list)  # [{title, steps[], answer}]
    key_points = Column(JSON, default=list)
    media = Column(JSON, default=list)  # [{kind: image|audio|video, r2_key, caption}]
    source = Column(String(128), default="original")
    license = Column(String(64), default="proprietary")
    reading_mins = Column(Integer, default=5)

class QuestionImport(Base):
    """Staging for ingested questions. Never served to students; only APPROVED
    rows are promoted into Question by teacher review."""
    __tablename__ = "question_imports"
    id = Column(Integer, primary_key=True)
    question_text = Column(Text)
    options = Column(JSON, default=list)
    answer = Column(Text)
    explanation = Column(Text, default="")
    subject = Column(String(64), default="", index=True)
    topic = Column(String(128), default="")  # proposed topic title (raw)
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=True, index=True)
    exam_style = Column(String(16), default="")
    difficulty = Column(String(16), default="Basic")
    source = Column(String(128), default="")
    source_reference = Column(String(256), default="")
    license = Column(String(128), default="")
    status = Column(String(16), default="IMPORTED", index=True)
    validation_status = Column(String(8), default="FAIL")
    validation_notes = Column(Text, default="")
    reviewer_notes = Column(Text, default="")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
