# Phase 2 — Data model (PostgreSQL)

Tables: users, enrollments, syllabus_nodes, lessons, questions, attempts, assessments, mastery, learning_plans, notifications.
- syllabus_nodes: id, exam (WAEC/NECO/JAMB/school), class (SS1-SS3), subject, topic, subtopic, objectives[], prerequisites[], difficulty
- questions: id, syllabus_node_id, stem, options[] (nullable theory), answer, difficulty Beginner/Basic/Intermediate/Advanced/Exam, exam_style, source, license, mistake_tags[], lang_variants {pcm,yo,ha,ig}
- attempts: id, user_id, question_id, answer, correct, mistake_type minor/conceptual/repeated/careless/persistent, hint_used, offline_queued, created_at
- mastery: user_id, syllabus_node_id, level Strong/Developing/NeedsRevision, score, updated_at
- SQL in backend/app/models.py (SQLAlchemy, works on Postgres + SQLite dev).
