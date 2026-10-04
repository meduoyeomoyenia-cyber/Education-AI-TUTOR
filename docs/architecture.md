# Phase 2 — Architecture (Locked)

Frontend: Next.js + React + Tailwind PWA (`web/`). Backend: Python + FastAPI (`backend/`). DB: PostgreSQL prod, SQLite dev via DATABASE_URL. Files: Cloudflare R2 presigned URLs.

```
[ PWA 360px→desktop ] --REST/SSE--> [ FastAPI ] --> [ PostgreSQL ]
        |                               |---> [ R2 presigned ] --> [ R2 + CDN ]
        |--> service-worker cache (lessons/questions) + queued attempts
[ FastAPI ] --> LLM gateway (RAG over syllabus/lessons/bank, teach-don't-answer, lang mode)
```

API v1: GET /health, GET /syllabus?exam&subject&class, GET /questions?topic&difficulty, POST /attempts, POST /attempts/sync (offline queue), POST /ask (SSE tutor), POST /uploads/presign (R2).
Auth: phone OTP + JWT (stubbed in MVP dev).
ADRs in docs/adr/: 01-pwa, 02-fastapi-postgres, 03-r2, 04-text-first, 05-rag-over-finetune, 06-llm-gateway, 07-no-download.
