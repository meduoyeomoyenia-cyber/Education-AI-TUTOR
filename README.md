# Education AI Tutor & Class Assistant

> **Your AI Tutor. Your Class Assistant. Your Exam Coach.**
> **Learn better. Practice smarter. Prepare with confidence.**

An affordable, personalized AI tutoring platform for Nigerian Senior Secondary School students (SS1–SS3), built around the real WAEC, NECO, and JAMB/UTME curriculum and examination journey.

This repo currently holds the Product Requirements Document (PRD) as `EDUCATION AI TUTOR .md` plus this README as the project entry point.

---

## 1. Users

### Primary Users: SS1–SS3 Students in Nigeria

- **Class levels:** SS1, SS2, SS3
- **Goals:**
  - Learn normal school curriculum topics
  - Prepare for WAEC, NECO, JAMB/UTME, and school exams
  - Fix weak subjects and revise before exams
  - Get help outside classroom hours without a private tutor

### Secondary Users (v2+)

- Teachers (classes, assignments, live Q&A, class weakness insights)
- Schools / education orgs
- Parents / guardians (progress view, support not surveillance)
- Private tutors

**Design constraints for users:**
- Affordable smartphones, low digital literacy ok
- Very little mobile data
- Prefers simple navigation, large readable text, voice input/output
- Speaks Nigerian English and Nigerian Pidgin

---

## 2. Problem

1. **No access to personal tutors:** Most students cannot afford 1:1 tutoring. Classroom ratios are high, help stops when school closes.
2. **Generic study tools don't fit Nigeria:** Existing apps and chatbots are not mapped to WAEC/NECO/JAMB syllabi, lack Nigerian context, and give answers instead of teaching.
3. **Exam failure is conceptual, not just practice:** Students memorize answers, repeat the same mistakes, and have no system that finds *why* they are wrong and re-teaches the prerequisite.
4. **Data and language barriers:** Video-heavy platforms consume too much data. English-only explanations leave many students behind.
5. **No clear study path:** Students don't know *what to study next*, how much syllabus they have covered, or whether they are exam-ready.

**Core promise:** Give every student a personal teacher that knows what they understand, what they don't, what to study next, and how to help them improve — with very little mobile data.

---

## 3. Solution Overview

A Nigerian-first, low-data, AI-powered platform combining:

- AI tutor (patient, adaptive, Socratic, not just answer-giving)
- WAEC / NECO / JAMB syllabus-based Learn Mode + Exam Mode
- Real teacher lessons + short AI teaching videos
- Live AI and teacher Q&A (demand-based, not rigid timetable)
- Practice questions, topic assessments, timed mocks
- Personalized learning plan + syllabus progress tracking
- Voice learning + image-based question help
- Nigerian English + Nigerian Pidgin support
- Student study groups with AI assistant
- Data Saver mode (text-first, audio second, video optional)

**Product principles:**
- Learning before answering
- Every mistake is a learning opportunity (hint → retry → re-teach → simpler example → extra practice)
- Personalized learning from topics, attempts, mistakes, strengths/weaknesses
- Low-data first, video as enrichment
- Trust and accuracy: distinguish curriculum / teacher / AI / student content, never invent syllabus rules

---

## 4. Subjects (Initial)

**Science & General:** Mathematics, English Language, Physics, Chemistry, Biology, Geography, Civic Education, Computer/ICT

**Commercial:** Economics, Commerce, Financial Accounting, Government, Mathematics, English

**Arts/Humanities:** Literature-in-English, Government, History, Economics, Geography, Religious Studies, Civic Education, English

Catalog expands over time.

---

## 5. Main Journey (Core Student Journey)

Ideal end-to-end flow:

```
Join
 ↓
Select SS1 / SS2 / SS3
 ↓
Choose WAEC / NECO / JAMB / School prep
 ↓
Select subjects
 ↓
Optionally provide intended course/career (e.g. Medicine, Engineering, Law)
 ↓
Take initial assessment
 ↓
AI identifies strengths and weaknesses
 ↓
Personalized learning plan (exam date, syllabus coverage, study time, weak topics)
 ↓
Learn topic (read / listen / optional short video)
 ↓
Ask AI questions (text / voice / photo of question)
 ↓
Practice (adaptive, exam-style, difficulty: Beginner → Basic → Intermediate → Advanced → Exam level)
 ↓
Make mistakes → AI responds intelligently:
  Minor mistake = hint + retry
  Conceptual gap = re-explain concept
  Repeated mistake = back to prerequisite
  Persistent difficulty = add to revision plan
 ↓
Master topic
 ↓
Take assessment → AI exam analysis:
  Score + Strong areas + Needs attention + Recommendation
 ↓
Learning plan updates
 ↓
Mock examination (timed/untimed, topic/subject/full)
 ↓
Exam-readiness preparation
```

**Example dashboard answers:** “What should I do next?”
> Good morning! Today's priority: Chemistry — Acids and Bases. Math 74%, Biology 61%, Chemistry 82%. AI Tutor: “You struggled with inheritance yesterday. Let's practice.”

**Core modes:** Learn | Practice | Exam | Ask AI | Live Q&A | Study Groups | Revision

---

## 6. Key Features (from PRD)

- **Onboarding:** class, exams, subjects, learning style, language, confidence, target course/career + course guidance
- **AI Tutor:** explains, exemplifies, breaks down steps, quizzes, hints, corrects, summarizes, revises, exam tips, recommends next topic
- **Teaching styles (student-controlled):** “Explain like beginner”, “Give hint not answer”, “Ask me questions”, “Harder questions”, “In Pidgin”, “Step-by-step”, “WAEC-style”
- **Voice:** speak question → AI responds, listen to explanations
- **Image help:** photo of Math/Physics/Chemistry/Biology question → method walkthrough + similar practice, not just answer
- **Video:** real teacher lessons + short AI videos for difficult concepts, revision, common mistakes
- **Data Saver:** text-first, lightweight lessons, low-bitrate audio/video, no download requirement
- **Mock & analysis:** timed mocks, weakness analysis, updated revision plan, syllabus % (e.g. WAEC Biology 64%: 8 strong, 5 developing, 3 need revision)
- **Motivation:** streaks, mastery, milestones — “Improve understanding” over “Beat others”
- **Safety:** safeguards for minors — groups, live, teacher interaction, anti-bullying/harassment, privacy

---

## 7. MVP Scope (Recommended First Release)

Focus on pillars 1-6 first:

- [ ] SS1-SS3 profiles, subject + exam selection, course/career guidance
- [ ] AI tutor (text, adaptive, English + Pidgin)
- [ ] Voice input/output
- [ ] Image question assist
- [ ] Syllabus learning structure
- [ ] Practice + adaptive questions + topic assessments + mocks
- [ ] Personalized plan + progress tracking
- [ ] Data Saver
- [ ] Selected teacher lessons + basic AI videos

**Deferred to v2:** expanded Live Q&A, study groups, full teacher dashboard, parent portal.

---

## 8. Success Measures

Not just registrations. Are students improving at answering?

- Retention / return to study, lessons completed, topics mastered
- Score delta between assessments, reduction in repeated mistakes
- Syllabus coverage, practice completion, mock improvement
- AI tutor engagement, satisfaction, teacher/live participation
- Data per session, goal achievement rate

---

## 9. Repo Structure

```
.
├── README.md                # This file - project overview
├── EDUCATION AI TUTOR .md   # Full PRD (43 sections, product source of truth)
```

Planned (not yet added):
```
├── docs/                    # architecture, data-model, api-spec
├── app/ | web/ | mobile/    # client
├── server/                  # api + AI orchestration
├── content/                 # syllabus maps, question banks (licensed/original)
└── .github/workflows/       # CI
```

---

## 10. Getting Started (Docs Only for Now)

No code yet. To review:

1. Read this README for overview
2. Read `EDUCATION AI TUTOR .md` for full spec
3. Next step: add `docs/architecture.md` + prototype AI tutor prompts

---

## 11. Roadmap

- **v0.1 (current):** PRD + README committed
- **v0.2:** Tech stack decision, data model, syllabus JSON schema
- **v0.3:** AI tutor prototype (Learn + Practice + Exam analysis)
- **v1.0 MVP:** Full MVP checklist above
- **v2.0:** Live Q&A scale, groups, teacher + parent experiences, scholarships/career/university prep

---

## 12. Positioning

**Simple:** Your AI Tutor. Your Class Assistant. Your Exam Coach.

**Philosophy:**
> Every student learns differently.
> Every mistake can teach something.
> Every student deserves a personal tutor.

Personalized. Affordable. Nigerian. Exam-focused. Teacher-supported. AI-powered. Low-data. Student-centered.
