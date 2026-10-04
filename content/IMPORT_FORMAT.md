# Real Question Import Format (Step 4B)

Local JSON batch import only: `POST /question-imports/batch` with `{"items": [...]}`.
Template with fictional examples: `content/step4b_import_template.json` — **never import it**
(rows carry `[DO-NOT-IMPORT]` + `source=template-example`; the importer stages them as
NEEDS_REVIEW and the approval endpoint refuses them).

## Required fields per item

| Field | Required | Rule |
|---|---|---|
| question_text | yes | Non-empty. `[DRAFT]`/draft rows rejected. |
| options | for MCQ | ≥2 choices; omit/empty only for theory. |
| answer | yes | Must match one option when options given. |
| explanation | recommended | Stored and shown to teachers; optional. |
| subject | yes | Must exactly match one of `GET /subjects` (16 subjects). |
| topic | yes | Must match an existing reusable Topic title within that subject (see `GET /topics?subject=`). Never auto-created; unmatched → NEEDS_REVIEW. |
| exam_style | yes | Exactly `WAEC`, `JAMB`, or `NECO` (case-insensitive on import, stored upper-case). Never altered beyond case. |
| difficulty | no | Defaults `Basic`. Use Beginner/Basic/Intermediate/Advanced/Exam. |
| source | yes | Who supplied it, e.g. `st-austins-maths-dept`. Test fixtures (`step3-test-fixture`, `step3-test`, `test-fixture`) exempt. |
| source_reference | yes | File/batch reference, e.g. `maths-batch-01`. |
| license | yes | Provenance, e.g. `teacher-created`, `licensed: XYZ Letras 2026`. Never invented by the system. |

## Importer guarantees

- Never creates topics (unmatched → NEEDS_REVIEW with note).
- Never auto-approves (best outcome is `IMPORTED`; only a teacher sets `APPROVED`).
- Never changes exam_style beyond upper-casing.
- Never touches attempts/mastery (only `question_imports` + — on approval — one `Question` row).
- Duplicate detection: normalized stem vs production bank + within batch; re-checked at approval.
- Approval (`POST /question-imports/{id}/approve`) copies stem, options, answer, difficulty, exam_style, source, source_reference, license, topic_id into the existing `Question` model. Rejections/revision requests stay staged.

## Workflow

1. Teacher supplies JSON file in the format above.
2. `POST /question-imports/batch` → rows staged as IMPORTED or NEEDS_REVIEW with validation notes.
3. Teacher opens `/teacher/review` → Approve / Needs Revision / Reject + reviewer notes, one by one.
4. Approved rows appear in Practice under their topic + exam filter.
