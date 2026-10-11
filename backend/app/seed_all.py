"""One-command production seed. Run once against the live DB, e.g. Render Shell:
    python -m app.seed_all
Builds: schema + syllabus/questions/lessons + 4 reusable topics + fixtures.
Idempotent: safe to re-run (existing rows are kept, never duplicated)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.app import seed as seedmod  # noqa: E402
from content.migrate_topic import migrate_schema, migrate_one  # noqa: E402
from content.step2_fixtures import run as fixtures_run  # noqa: E402

TOPICS = [
    ("Mathematics", "Number Bases"),
    ("Mathematics", "Algebra: Simultaneous Equations"),
    ("Biology", "Photosynthesis"),
    ("Chemistry", "Acids and Bases"),
]


def run():
    migrate_schema()
    seedmod.run()
    seedmod.seed_lessons()
    for subject, topic in TOPICS:
        migrate_one(subject, topic)
    fixtures_run()
    print("seed_all complete")


if __name__ == "__main__":
    run()
