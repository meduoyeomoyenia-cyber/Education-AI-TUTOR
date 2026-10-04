"""Mastery + analysis + daily plan. Rule: >=80% on >=10 mixed AND no repeat mistake-tag in 7 days = Mastered."""
from sqlalchemy.orm import Session
from sqlalchemy import select
from datetime import datetime, timedelta, timezone
from .models import Attempt, Mastery, Question, SyllabusNode

def _utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)

def topic_id_for_node(db: Session, node_id: int):
    """Reusable-topic link for a node. None until the node's topic is migrated. Read-only."""
    node = db.get(SyllabusNode, node_id)
    return node.topic_id if node else None

def topic_stats(db: Session, user_id: int):
    rows = db.execute(select(Question, SyllabusNode, Attempt).join(SyllabusNode, Question.node_id == SyllabusNode.id).join(Attempt, Attempt.question_id == Question.id).where(Attempt.user_id == user_id)).all()
    by = {}
    for qu, node, at in rows:
        k = (node.subject, node.topic, node.id)
        d = by.setdefault(k, {"total": 0, "correct": 0, "tags": [], "recent_repeat": False})
        d["total"] += 1; d["correct"] += 1 if at.correct else 0
        if not at.correct: d["tags"].append((at.mistake_type, at.created_at))
    out = []
    for (subj, topic, nid), d in by.items():
        score = d["correct"] / max(1, d["total"])
        week = _utcnow() - timedelta(days=7)
        repeats = len([t for t, c in d["tags"] if c and c >= week]) >= 2
        level = "Strong" if (score >= 0.8 and d["total"] >= 10 and not repeats) else ("NeedsRevision" if score < 0.5 or repeats else "Developing")
        out.append({"subject": subj, "topic": topic, "node_id": nid, "score": round(score, 2), "attempts": d["total"], "level": level})
        row = db.execute(select(Mastery).where(Mastery.user_id == user_id, Mastery.node_id == nid)).scalars().first()
        tid = topic_id_for_node(db, nid)
        if row is None:
            db.add(Mastery(user_id=user_id, node_id=nid, topic_id=tid, level=level, score=score))
        else:
            row.level, row.score = level, score
            if tid is not None:
                row.topic_id = tid  # link history forward; attempts untouched
    db.commit()
    return out

def analyze(stats: list):
    strong = [s["topic"] for s in stats if s["level"] == "Strong"]
    weak = [s["topic"] for s in stats if s["level"] == "NeedsRevision"]
    score = round(sum(s["score"] for s in stats) / max(1, len(stats)) * 100)
    recs = [f"Review {w}" for w in weak[:3]] + ([f"Complete 15 {weak[0]} questions"] if weak else ["Take a full mock"])
    return {"score": score, "strong": strong, "weak": weak, "recommendations": recs}

def today_plan(stats: list, minutes: int = 30):
    weak = sorted([s for s in stats if s["level"] != "Strong"], key=lambda s: s["score"])[:2]
    items = [{"task": f"{s['subject']} — {s['topic']}", "mins": 10} for s in weak]
    items += [{"task": "10 practice questions", "mins": 10}, {"task": "Review yesterday's mistakes", "mins": 10}]
    while len(items) < 4:
        items.append({"task": "15-minute revision", "mins": 10})
    return {"minutes": minutes, "items": items[:4]}
