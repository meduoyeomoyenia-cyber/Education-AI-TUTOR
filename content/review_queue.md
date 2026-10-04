# Question pipeline: draft → review → import

1. AI drafts to `content/questions.draft.json` with status=draft (never served).
2. Teacher reviews in queue: approve / edit / reject. Approved rows move to `content/questions.vetted.json` with source+license filled.
3. Validate: `python content/validate.py` (schema + answer-in-options + license present).
4. Import: `python -m backend.app.seed` → PostgreSQL (prod) / SQLite (dev). R2 holds any image assets via presigned URLs.
5. Launch gate: 100% syllabus structure + min 20-30 vetted per core topic. Current seed boots the loop; teachers expand per subject.
