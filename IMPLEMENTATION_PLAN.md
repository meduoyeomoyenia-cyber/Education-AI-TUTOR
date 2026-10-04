# Education AI Tutor — Implementation Plan (Phased)

Source: `EDUCATION AI TUTOR .md` (PRD, 43 sections) + `README.md`.
Status: docs-only, v0.1-initial saved in `versions/`. No code yet.
Goal: Ship a low-data, Nigerian-first MVP first, then expand to full vision.

---

## Phase 0 — Product Groundwork (Week 1-2)

**Objective:** Lock scope so MVP is shippable.

1. Cut MVP to: onboarding + Learn/Practice/Exam + text AI tutor (English/Pidgin/Yoruba/Hausa/Igbo, voice input optional) + progress + Data Saver. Defer: live Q&A scale, groups, parent portal, AI video scale to v2.
2. Define mastery: e.g. topic = mastered after 80%+ on mixed set + no repeat mistake in 7 days. Progress = meaningful learning, not lesson opens.
3. Define data budget: e.g. text lesson <50KB, 30-min session <2MB with Data Saver on.
4. Content legality: only original + teacher-created + licensed WAEC/NECO/JAMB-style questions. No scraping past papers without authorization.
5. Success gates: retention D7/D30, score delta, mistake-repeat rate, KB/session.

**Exit:** MVP scope doc + metrics + risks signed off.

---

## Phase 1 — Design System (Week 2-4)

**Objective:** Simple, readable, low-data UI from 360px phones through desktop/laptop. Low-bandwidth on every device.

1. **Principles:** mobile-first 360px → responsive to tablet/desktop (max-width content column + adaptive grid), large type (16-18px body), high contrast, one primary action per screen, works on 2G text-first. No layout breakage at 360px, 768px, 1280px.
2. **Tokens:** colors (primary green/blue for trust + accent for exam urgency), spacing 4pt, rounded 8-12px, system fonts first (no heavy webfonts), icon-only where possible.
3. **Components (Next.js + Tailwind, build once, reuse):** Button, Input, LessonCard, QuestionCard (MCQ/theory), HintBox, ProgressRing, SyllabusTree, MockTimer, AudioPlayerLite, LanguageToggle (English/Pidgin/Yoruba/Hausa/Igbo), VoiceInputButton (optional, never required), DataSaverToggle, BottomNav (mobile) + Sidebar (desktop) for Learn/Practice/Exam/Ask/Revision.
4. **Modes:** Learn | Practice | Exam | Ask AI | Revision. Dashboard answers “What next?” in <3 sec.
5. **Accessibility/i18n:** Language support = English (default academic) + Nigerian Pidgin + Yoruba + Hausa + Igbo. Academic terms stay in English even when explanation is in Pidgin/local language. Voice input optional everywhere text input exists. Minimal animation, offline-friendly skeletons.
6. **State patterns (required for every async view):** loading (skeleton), empty (no data + CTA), error (retry), offline (cached content + queue actions). Add to component checklist.
7. **Prototype:** Figma wireframes for onboarding → dashboard → lesson → practice → mock result at 360px + desktop. Test with 5 students.

**Exit:** Figma library + clickable prototype + component checklist including responsive + state coverage.

---

## Phase 2 — Architectural Decision (Week 3-5)

**Locked stack:**

- **Frontend:** Next.js + React + Tailwind, mobile-first PWA. Installable, <200KB initial JS, image-lazy, service-worker cache for lessons.
- **Backend:** Python + FastAPI. REST + SSE for tutor streaming. Auth: phone OTP (Termii/Africa’s Talking) + JWT.
- **Database:** PostgreSQL (system of record for profiles, syllabus, attempts, mastery, plans). Redis only as optional ephemeral cache for sessions/rate-limit, not required for MVP.
- **Files:** Cloudflare R2 (audio, images, low-bitrate video, OCR uploads) via presigned URLs + CDN cache. No lesson/video download requirement; stream + cache only.
- **AI layer:** LLM gateway (provider-agnostic) + guardrails + RAG over own syllabus/lessons/question bank. Never answer from parametric memory for syllabus rules. System prompt enforces “teach, don’t just answer” + difficulty + language mode.
- **Voice:** Optional voice input (mic → STT) + TTS playback, audio capped at 32-48kbps in Data Saver. Text always works without voice.
- **Image:** OCR + vision model → topic classify → guided solution + similar practice.
- **Analytics:** PostHog/Mixpanel-lite + custom learning events.
- **Hosting:** Single region close to Nigeria (EU-West) + CDN cache. Cost per active student tracked.

**Key ADRs to record in `docs/adr/`:**
1. PWA (Next.js) over native for MVP (data/install friction)
2. FastAPI backend + PostgreSQL as system of record
3. Cloudflare R2 for all files (presigned URLs + CDN)
4. Text-first, video optional
5. Postgres + RAG over fine-tune (accuracy + copyright safety)
6. LLM gateway to swap models for cost
7. No lesson download in v1 (stream + cache only)

**Data model v1 (PostgreSQL):** User, Enrollment (class/exams/subjects/career), Syllabus (exam→subject→topic→subtopic), Lesson, Question (topic/difficulty/exam-style/source), Attempt (answer/mistake-type/hint-used), Assessment/Mock, Mastery (topic→level), LearningPlan, Notification.

**Exit:** `docs/architecture.md` + ERD + API spec + ADR log.

---

## Phase 3 — Content & Curriculum Engine (Week 4-8, parallel)

**Objective:** WAEC/NECO/JAMB structure live across ALL target subjects SS1–SS3 at launch, with pipeline + vetted bank.

1. Syllabus JSON schema: `{exam, subject, topic, objectives, prerequisites, difficulty}` for WAEC/NECO/JAMB. Coverage matrix required: every subject × SS1-SS3 × exam mapped, no gaps.
2. Full subject list for launch (not 2-subject seed):
   - Science/General: Mathematics, English, Physics, Chemistry, Biology, Geography, Civic Education, Computer/ICT
   - Commercial: Economics, Commerce, Financial Accounting, Government, Mathematics, English
   - Arts: Literature-in-English, Government, History, Economics, Geography, Religious Studies, Civic Education, English
3. Question-generation → review → import pipeline: AI draft → teacher review queue (approve/reject/edit) → schema validation → import script → PostgreSQL + R2 for assets. Every question carries source/license, exam-style tag, difficulty Beginner→Exam, mistake tags.
4. Multilingual memory: Pidgin + Yoruba + Hausa + Igbo explanation variants (academic terms stay in English).
5. Launch gate: 100% syllabus structure present + initial vetted bank per subject/topic (e.g. minimum 20-30 vetted questions per core topic) before public MVP.

**Exit:** All-subject structure implemented + pipeline working + vetted bank ready for launch.

---

## Phase 4 — AI Tutor Core (Week 5-9)

1. System prompts: tutor persona (patient teacher), teaching-style controls (“hint not answer”, “harder”, “Pidgin / Yoruba / Hausa / Igbo”, “step-by-step”, “WAEC-style”).
2. Adaptive loop: identify error → hint/retry → re-teach → simpler example → prerequisite → add to revision.
3. Context assembly: profile + syllabus node + last 5 mistakes + mastery + language preference → prompt (token-capped for cost).
4. Guardrails: no invented exam dates/rules, cite content source type (curriculum/teacher/AI/student), Nigerian context. Academic terms stay in English across all languages.
5. Cost control: small model default, larger only for complex explanations; cache common answers.

**Exit:** Tutor API `/ask`, `/explain`, `/hint` working with streaming + style flags.

---

## Phase 5 — Frontend MVP Build (Week 7-11, Next.js + React + Tailwind)

1. Onboarding: class/exams/subjects/style/language (English/Pidgin/Yoruba/Hausa/Igbo)/confidence/career → career guidance blurb.
2. Dashboard: today’s priority, % per subject, weak topics, recent mistakes, streak. Responsive: stacked cards on 360px, grid on desktop.
3. Learn view: lesson text + examples + Ask follow-up inline. R2 assets lazy-load with low-res placeholder.
4. Practice view: adaptive queue, instant feedback per mistake taxonomy.
5. Exam view: timed/untimed, auto-submit on time.
6. Revision view: weak list + retry.
7. Global: Data Saver toggle (disables autoplay, compresses images, prefers text/audio). Low-bandwidth budgets enforced on every device.
8. States checklist (every async screen): loading skeleton, empty (with CTA), error (with retry), offline (serve cached lesson/questions from service worker + queue attempts to sync to FastAPI/PostgreSQL when back online).

**Exit:** Responsive PWA usable on 3G + Data Saver from 360px to desktop, with full state coverage.

---

## Phase 6 — Assessment, Mastery & Plan (Week 9-12)

1. Scoring + analysis: Score + Strong + Needs attention + Recommendation → updates LearningPlan.
2. Mastery engine + syllabus % (Strong/Developing/Needs revision).
3. Daily plan generator: exam date + time available + weak topics → “Today’s 4 items”.
4. Notifications (opt-in, throttled): revision nudge, improvement, live Q&A alert.

**Exit:** Student can go Learn → Practice → Mock → improved plan loop.

---

## Phase 7 — Voice, Image, Video-Lite (Week 11-14, files on R2)

1. Voice (optional, never blocking): mic → STT → tutor → TTS playback. Text path always available. Essential for English/Literature/revision. Audio stored/served via R2.
2. Image help: upload/photo → R2 presigned upload → OCR → guided steps → check + similar question.
3. Video: teacher uploads to R2 (720p max, compressed) + short AI clips (<3 min) for hard topics only. Never required path. R2 + CDN delivery.
4. Data instrumentation: log KB per session by media type.

**Exit:** All three work under Data Saver with degraded-but-usable quality.

---

## Phase 8 — Safety, Trust, Ops (throughout, harden Week 12-14)

1. Minor safety: profanity/PII/bullying filters, report/block, teacher vetting, study-group moderation queue, no DM between strangers.
2. Accuracy: RAG citations, “verify with official guide” disclaimer for exam rules, human review for flagged answers.
3. Privacy: minimal data, OTP auth, parent view = support not surveillance.
4. DevOps: CI (lint/test/build), staging → prod, backups, cost alerts, uptime + LLM fallback.

---

## Phase 9 — Pilot, Measure, Iterate (Week 14-18)

1. Closed pilot: 100-300 SS1-SS3 students, 2-3 schools.
2. Track: return rate, lessons/topics mastered, assessment delta, repeat-mistake drop, KB/session, tutor engagement, satisfaction.
3. Fix top 3 drop-offs, content gaps, multilingual clarity (Pidgin/Yoruba/Hausa/Igbo), data overruns.
4. Load test mocks (concurrent timers).

**Exit criteria for public MVP:** D7 >30%, mock improvement measurable, session < budget, zero safety incidents.

---

## Phase 10 — v2 Expansion (post-MVP)

- Demand-based Live Q&A (AI + teacher scheduling when many stuck on same topic)
- Study groups (SS2 Maths, JAMB Chem, etc. with AI assistant labels: AI/Teacher/Student)
- Teacher dashboard + Class Assistant (“class struggled with simultaneous equations”)
- Parent reports, school partnerships, scholarships, career/university prep, more languages/exams.

---

## Build Order Checklist

- [ ] Phase 0 scope + metrics
- [ ] Phase 1 design tokens + prototype (360px→desktop + loading/empty/error/offline states)
- [ ] Phase 2 arch (Next.js/FastAPI/PostgreSQL/R2) + API spec
- [ ] Phase 3 all-subject syllabus SS1-SS3 + pipeline + vetted bank launch-ready
- [ ] Phase 4 tutor prompts (EN/Pidgin/Yoruba/Hausa/Igbo) + guardrails
- [ ] Phase 5 PWA onboarding/dashboard/learn/practice/exam + state coverage
- [ ] Phase 6 mastery + plan + analysis
- [ ] Phase 7 optional voice/image/video-lite on R2
- [ ] Phase 8 safety + DevOps
- [ ] Phase 9 pilot + launch

Next file to create: `docs/architecture.md` + `docs/data-model.md`.
