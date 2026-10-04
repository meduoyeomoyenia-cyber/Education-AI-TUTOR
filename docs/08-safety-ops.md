# Phase 8 — Safety + Ops

Safety: `/safety/check` flags pii/bullying/profanity, redacts PII, blocks bullying. `/safety/report` queues mod review. No DMs between strangers. Teacher vetting: manual approve before publish.
Accuracy: RAG citations on tutor answers, exam-rule disclaimer, flagged answers routed to review queue.
Privacy: phone OTP + JWT (stub dev), minimal PII, parent view support-only.
Ops: CI `.github/workflows/ci.yml` (validate + pytest + next build). Staging → prod, daily Postgres backup, R2 versioning, cost alert per active student, LLM fallback to cached + small model.
