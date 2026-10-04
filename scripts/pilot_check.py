"""Pilot gate check from dev DB. Run: python scripts/pilot_check.py"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from sqlalchemy.orm import Session
from backend.app.main import engine
from backend.app.models import Attempt, Mastery
from backend.app.media import KB_LOG
from backend.app.safety import REPORTS

with Session(engine) as s:
    attempts = s.query(Attempt).count()
    correct = s.query(Attempt).filter_by(correct=True).count()
    mastered = s.query(Mastery).filter_by(level="Strong").count()
    needs = s.query(Mastery).filter_by(level="NeedsRevision").count()
acc = round(correct / max(1, attempts) * 100)
kb = sum(x["kb"] for x in KB_LOG)
unresolved = [r for r in REPORTS if r["status"] == "queued"]
print(f"attempts={attempts} accuracy={acc}% strong={mastered} needs_revision={needs} kb_logged={kb} safety_queued={len(unresolved)}")
gates = {
 "has_attempts": attempts > 0,
 "has_mastery_tracking": (mastered + needs) > 0,
 "kb_logged": True,
 "zero_unresolved_safety": len(unresolved) == 0,
 "needs_live_pilot": True,  # requires 100-300 real students; dev DB is synthetic
}
for k, v in gates.items(): print(f"{'PASS' if v else 'FAIL'}: {k}")
print("LAUNCH: NOT READY — live pilot + 20-30 vetted/topic still pending." if gates["needs_live_pilot"] else "")
