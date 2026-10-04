# Phase 1 — Design System

Source: `IMPLEMENTATION_PLAN.md` Phase 1 + `design-system-preview.html`.
Frontend: Next.js + React + Tailwind. Range 360px → 1280px+. Low-bandwidth everywhere.

## Tokens
- brand #0E7C5B, brand-dark #0A5C44, info #1D5BD8, accent #E85D04, ink #14211C, muted #5F6F68, bg #F6F8F7, card #FFFFFF, line #E3E9E6
- Body 16-18px / 1.6, title 20px/700, small 13-14px. System fonts only. 4pt spacing. Radius 8-12px.
- Layout: 360px single col + BottomNav; >=768px 2-col; >=1280px content max-w-6xl + Sidebar.

## Components (each with loading/empty/error/offline)
Button, Input, LessonCard, QuestionCard MCQ/theory, HintBox, ProgressRing, SyllabusTree, MockTimer, AudioPlayerLite, LanguageToggle EN/Pidgin/YO/HA/IG, VoiceInputButton optional, DataSaverToggle, BottomNav+Sidebar, StateSkeletons, ErrorRetry, OfflineBanner.

## State rules
- loading: skeleton, no blank screen
- empty: illustration + CTA (e.g. No revision items → Start practice)
- error: message + Retry button, preserve input
- offline: serve cached lesson/questions from service worker, queue attempts POST to /attempts/sync when online

## i18n rule
Academic terms stay in English. UI strings + explanations localizable. Voice input optional on every text field.

## Checklist
- [ ] tokens.json matches preview
- [ ] 360/768/1280 no overflow, tap targets >=44px
- [ ] Every async view implements 4 states
- [ ] Data Saver verified: no autoplay, compressed R2 images
