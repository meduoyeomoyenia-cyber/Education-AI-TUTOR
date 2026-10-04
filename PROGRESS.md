# Execution Progress

Locked stack: Next.js + React + Tailwind | Python + FastAPI | PostgreSQL | Cloudflare R2
Languages: English + Pidgin + Yoruba + Hausa + Igbo, voice optional.
Range: 360px phones → desktop. Text-first low-bandwidth.

- [x] Phase 0 — Scope, mastery, budgets, metrics (`docs/00-scope.md`)
- [x] Phase 1 — Design tokens + component checklist (`docs/01-design-system.md`, `web/tokens.json`)
- [x] Phase 2 — Architecture + data model + ADRs + backend scaffold (`docs/architecture.md`, `docs/data-model.md`, `backend/`) — VERIFIED: import-ok, /health ok, /ask pcm ok
- [x] Phase 3 — Syllabus SS1-SS3 all subjects + question pipeline (`content/`) — VERIFIED: 720 nodes, 8 vetted, 720 drafts, /syllabus 15 WAEC-Maths, attempt correct
- [x] Phase 3b — Lesson vertical slice (`Lesson` table, `GET /lessons`, `content/lessons.vetted.json` ×3, `/lesson` page) — VERIFIED: validator 3 ok, 6/6 pytest, build 6 routes
- [x] Phase 3c — Multi-subject dashboard (`GET /subjects`, dashboard selector default Mathematics) — VERIFIED: 7/7 pytest, build passes
- [x] Phase 3d — Reusable Topic architecture (Topic table, topic_id links, /topics + slug/exam params, slug flow, NB migrated) — VERIFIED: 13/13 pytest, build passes
- [x] Phase 3e — Multi-subject fallback (dashboard merges /topics + /syllabus, alias links, empty states) — VERIFIED: 14/14 pytest, build passes
- [x] STEP 2 — 3-topic proof (simultaneous/photosynthesis/acids migrated, 1 NECO + 2 stub fixtures, test_step2) — VERIFIED: 21/21 pytest, build passes
- [x] STEP 3 — ingestion + vetting prototype (QuestionImport, /question-imports/*, /teacher/review, 6 fixtures) — VERIFIED: 30/30 pytest, build passes
- [x] STEP 4A — content safety (isolated test DB, draft exclusion, provenance, stable assertions) — VERIFIED: 32/32 pytest ×2 runs, dev.db untouched, build passes
- [x] STEP 4B prep — real-import readiness (IMPORT_FORMAT.md, template, source_reference passthrough, template guard) — VERIFIED: 34/34 pytest, dev.db untouched, build passes
- [x] Providers — generic architecture + ALOC adapter (env key, header auth, staging-only import) — VERIFIED: 39/39 pytest, dev.db untouched, build passes
- [x] ALOC URL fix — base https://dev.aloc.com.ng + configurable path, X-API-Key, no doubled path — VERIFIED: 39/39 pytest, dev.db untouched, build passes
- [x] ALOC mapping fix — text/correctAnswer/options/id mapping, section/category candidates, topic-less rows flagged — VERIFIED: 46/46 pytest ×2 runs, dev.db untouched, build passes
- [x] ALOC live test #1 — 5 rows staged NEEDS_REVIEW, production/attempts/mastery untouched — VERIFIED: 48/48 pytest, build passes
- [x] Phase 4 — Tutor prompts + guardrails (`backend/app/tutor/`) — VERIFIED: 2 passed (5 langs, hint/explain/guardrail)
- [x] Phase 5 — Frontend MVP scaffold Next.js (`web/`) — VERIFIED: npm install + npm run build succeeds (5 routes, First Load ~88kB)
- [x] Phase 6 — Mastery + plan engine (`backend/app/mastery.py`) — VERIFIED: 3 passed
- [x] Phase 7 — Voice/image/video-lite on R2 (`backend/app/media.py`) — VERIFIED: 4 passed
- [x] Phase 8 — Safety + DevOps (`backend/app/safety.py`, `.github/workflows/ci.yml`) — VERIFIED: 5 passed
- [x] Phase 9 — Pilot checklist (`docs/09-pilot.md`, `scripts/pilot_check.py`) — GATES: dev data only, LAUNCH NOT READY (needs live pilot + bank + build)

Environment (2026-09-29): Python 3.12 OK, Node MISSING, psql MISSING.
Workaround: backend runs on SQLite dev / Postgres prod via DATABASE_URL. Frontend scaffold deferred until Node installed.
