# External Question Providers

Providers fetch third-party questions into **staging** (`question_imports`).
They can never write to the production `Question` table — every row goes
through validation + teacher review + approval first.

## Adding a provider

1. Subclass `backend/app/providers/base.py::QuestionProvider`.
2. Implement `fetch(subject, exam, topic, limit)` (raw records) and
   `normalize(raw, subject, exam)` (ingestion-schema dict with `source` set).
3. `register()` it and add `GET /providers` visibility automatically.
4. Import endpoint: `POST /providers/{name}/import`
   `{subject, exam, topic?, limit}` → `{provider, fetched, staged[]}`.

## ALOC (first provider)

Config via environment (see `backend/.env.example`):
`ALOC_API_KEY`, `ALOC_BASE_URL`, optional `ALOC_KEY_HEADER` (default
`access-token`), optional `ALOC_LICENSE`.
Key travels in a request header, never in URLs. Without key/URL the adapter
fails closed with setup instructions instead of fetching.

`SUBJECT_MAP` / `EXAM_MAP` in `aloc.py` translate provider labels to ours —
confirm against the owner's endpoint details and sample response before
live use. Unmapped labels pass through; unknown topics land in NEEDS_REVIEW
for a teacher to resolve (taxonomy stays teacher-controlled).
