"""Phase 8 safety: PII/bullying/profanity filters, report queue, teacher vetting stub."""
import re
PII = [re.compile(r"\b\d{11}\b"), re.compile(r"[\w.-]+@[\w.-]+\.\w+"), re.compile(r"\b\d{10,11}\b")]
BULLY = re.compile(r"\b(kill yourself|you are worthless|he go beat you|threat)\b", re.I)
PROFANITY = re.compile(r"\b(idiot|stupid|dumb|ode|mumu)\b", re.I)
REPORTS = []

def scan(text: str) -> dict:
    flags = []
    t = text or ""
    if any(p.search(t) for p in PII): flags.append("pii")
    if BULLY.search(t): flags.append("bullying")
    if PROFANITY.search(t): flags.append("profanity")
    safe = PROFANITY.sub("***", t)
    for p in PII: safe = p.sub("[redacted]", safe)
    return {"flags": flags, "blocked": "bullying" in flags, "clean": safe}

def report(user_id: int, kind: str, ref: str):
    REPORTS.append({"user_id": user_id, "kind": kind, "ref": ref, "status": "queued"})
    return {"status": "queued", "count": len(REPORTS)}
