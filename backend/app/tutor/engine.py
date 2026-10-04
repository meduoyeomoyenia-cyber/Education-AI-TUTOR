"""Offline-capable tutor engine: RAG over local DB + adaptive loop. LLM gateway stub for later."""
from sqlalchemy.orm import Session
from sqlalchemy import select, desc
from .prompts import SYSTEM, PREFIX, style_instruction
from . import guardrails
from ..models import SyllabusNode, Question, Attempt, Mastery

def context_for(db: Session, user_id: int, topic: str | None):
    node = None
    if topic:
        node = db.execute(select(SyllabusNode).where(SyllabusNode.topic == topic).limit(1)).scalars().first()
    last = db.execute(select(Attempt).where(Attempt.user_id == user_id).order_by(desc(Attempt.id)).limit(5)).scalars().all()
    mistakes = [a.mistake_type for a in last if not a.correct]
    return node, mistakes

def adaptive_next(mistakes: list) -> str:
    if mistakes.count("conceptual") >= 2: return "simpler"
    if mistakes and mistakes[-1] == "minor": return "hint-not-answer"
    return "step-by-step"

def respond(db: Session, user_id: int, message: str, language: str, style: str, topic: str | None, mode: str) -> str:
    language = language if language in PREFIX else "en"
    node, mistakes = context_for(db, user_id, topic)
    if style == "auto": style = adaptive_next(mistakes)
    ctx = f"Topic: {node.subject}/{node.topic} ({node.exam} {node.student_class})" if node else "Topic: general"
    weak = f"Weakness: {mistakes[-1]} — re-teaching." if mistakes else "No recent mistakes."
    if mode == "hint": body = f"{PREFIX[language]}\n{ctx}\nHint: try the first step, then retry. ({style_instruction(style)})"
    elif mode == "explain": body = f"{PREFIX[language]}\n{ctx}\nExplanation: key idea first, then one simple example. {weak}\nCheck: can you state step 1?"
    else: body = f"{PREFIX[language]}\n{ctx}\nYou asked: {message}\n{weak}\n{style_instruction(style)}\nTry now."
    note = guardrails.check(message, body)
    if note: body += f"\n{note}"
    return guardrails.clean(f"{body}\n{guardrails.sources()}\n[{SYSTEM[:0]}teaching, not answering]")
