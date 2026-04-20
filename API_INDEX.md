# Math API Index

Full reference for the 7 Math routers under `backend/routers/math_*.py`.
All paths are prefixed with the server root (default `http://localhost:8000`).

## Table of Contents

- [Math Academy](#math-academy) — grades, units, lessons, stages, submit, unit test
- [Math Daily Challenge](#math-daily-challenge) — today's 5-problem challenge
- [Math Fluency](#math-fluency) — fact fluency rounds (add/sub/mul/div)
- [Math Placement](#math-placement) — bulk + adaptive placement test
- [Math Kangaroo](#math-kangaroo) — Kangaroo competition practice
- [Math Glossary](#math-glossary) — grade-level term definitions
- [Math Problems (My Problems)](#math-problems-my-problems) — spaced-repetition wrong review
- [Common Conventions](#common-conventions) — auth, errors, caching

---

## Math Academy

Source: `backend/routers/math_academy.py`
Data: `backend/data/math/{grade}/{unit}/{lesson}.json`
Stages: `pretest → learn → try → practice_r1 → practice_r2 → practice_r3`

### `GET /api/math/academy/grades`
List available grade folders.
- **Response**: `{"grades": ["G3", "G4", "G5", "G6"]}`

### `GET /api/math/academy/{grade}/units`
List units for a grade.
- **Path**: `grade` — e.g. `G3`
- **Response**: `{"grade": "G3", "units": ["U1_add_sub_1000", ...]}`

### `GET /api/math/academy/{grade}/{unit}/lessons`
List lessons with progress + unit-test unlock status.
- **Response**:
  ```json
  {
    "grade": "G3", "unit": "U9_compare_fractions",
    "lessons": [{"name": "L1_...", "is_completed": false, "stage": "pretest", "pretest_skipped": false}, ...],
    "unit_test_unlocked": false
  }
  ```

### `GET /api/math/academy/{grade}/{unit}/{lesson}/{stage}`
Return problems for one lesson stage.
- **Path**: `stage` ∈ `{pretest, learn, try, practice_r1, practice_r2, practice_r3}`
- **Response**: `{"grade", "unit", "lesson", "stage", "problems": [...], "count"}`
- **Errors**: `400` invalid stage, `404` lesson data not found

### `GET /api/math/academy/{grade}/{unit}/unit-test`
Return the unit test problem set.
- **Response**: `{"grade", "unit", "problems": [...], "count"}`
- **Errors**: `404` if `unit_test.json` missing

### `POST /api/math/academy/submit-answer`
Grade one answer, persist attempt, update progress, schedule wrong review.
- **Body**:
  ```json
  {"problem_id": "c9_l1_pre_01", "grade": "G3", "unit": "U9_...",
   "lesson": "L1_...", "stage": "pretest",
   "user_answer": "Sara", "time_spent_sec": 12}
  ```
- **Response**: `{"is_correct": bool, "correct_answer": str, "feedback": str, "solution_steps": [...]}`
- **Side effects**: `MathAttempt` insert; `MathProgress` upsert; `MathWrongReview` on incorrect (non-pretest); XP `math_problem_correct` (+1) on correct.

### `POST /api/math/academy/unit-test/submit`
Legacy unit-test submission (query params).
- **Query**: `grade, unit, score, total`
- **Response**: `{"passed", "score", "total", "percentage", "weak_lesson"}`
- **Pass threshold**: 90% (`MATH_UNIT_TEST_PASS_RATIO`)
- **XP on pass**: `math_unit_test_pass` (+15); streak `mark_math_done`.

### `POST /api/math/academy/unit-test/submit-v2`
Preferred JSON-body variant (Phase-0 fix).
- **Body**: `{"grade": str, "unit": str, "score": int, "total": int}`
- **Response**: `{"status", "passed", "score", "total", "pct", "weak_lesson"?}`
- **Pass threshold**: 70%

### `GET /api/math/academy/progress/{grade}`
Aggregate progress for all unit/lesson pairs in a grade.
- **Response**: `{"grade", "progress": {"{unit}/{lesson}": {stage, is_completed, pretest_skipped, best_score_r1/r2/r3, unit_test_passed}}}`

### `POST /api/math/academy/complete-lesson`
Mark a lesson complete + award XP + streak.
- **Body**: `{"grade", "unit", "lesson"}`
- **Response**: `{"status": "ok", "is_completed": true}`

---

## Math Daily Challenge

Source: `backend/routers/math_daily.py`
Composition: 50% current unit + 30% spaced review + 20% spiral (backfill if empty).
Pool cached by date to avoid rescanning ~435 lesson JSONs per request.

### `GET /api/math/daily/today`
Fetch (or generate) today's 5-problem challenge. Problems persisted in `MathDailyChallenge`.
- **Response**: `{"date", "exists", "completed", "score", "total", "problems": [{"index", "id", "type", "question", "options", "concept"}, ...]}`
- **Note**: Answers stripped client-side.

### `POST /api/math/daily/submit-answer`
Grade one answer against the persisted day's set.
- **Body**: `{"index": int, "answer": str}`
- **Response**: `{"is_correct", "correct_answer", "feedback"}`
- **Errors**: `400` not started / invalid index, `404` problem not found, `500` corrupt data.

### `POST /api/math/daily/complete`
Finalize today's challenge, award XP, mark streak.
- **Body**: `{"score": int, "total": int}`
- **Response**: `{"status": "completed", "score", "total", "xp"}`
- **XP**: `math_daily_complete` (+5); `math_daily_perfect` (+3) if score == total.

---

## Math Fluency

Source: `backend/routers/math_fluency.py`
Fact sets: 8 (add/sub within 10/20, mul 0–5/6–10/0–12, div 0–10).
Phases: A (untimed) → B (10s/problem) → C (5s/problem). Promote on perfect round of ≥10 questions.

### `GET /api/math/fluency/catalog`
List all fact sets with per-set progress.
- **Response**: `{"fact_sets": [{"fact_set", "label", "op", "grade", "current_phase", "best_score", "best_time_sec", "accuracy_pct", "total_rounds"}, ...]}`

### `GET /api/math/fluency/status`
Progress-only view (excludes spec labels).
- **Response**: `{"fact_sets": [{"fact_set", "current_phase", "best_score", "best_time_sec", "accuracy_pct", "total_rounds", "last_played"}, ...]}`

### `GET /api/math/fluency/start-round`
Generate a new round (not persisted until submit).
- **Query**: `fact_set` (required), `count` (default 10, clamped to [5, 20])
- **Response**: `{"fact_set", "label", "op", "phase", "sec_per_problem", "time_limit_sec", "questions": [{"question", "answer"}, ...]}`
- **Errors**: `404` unknown fact_set.

### `POST /api/math/fluency/submit-round`
Record a round result, progress phase if earned.
- **Body**: `{"fact_set": str, "score": int, "total": int, "time_sec": int}`
- **Response**: `{"accuracy", "new_best", "current_phase", "total_rounds", "mastered"}`
- **XP**: `math_fluency_best` (+2) on personal best; streak mark on every submit.
- **Mastery**: Phase C AND accuracy ≥ 95%.

### `GET /api/math/fluency/summary`
Aggregate view.
- **Response**: `{"total_sets", "mastered_sets", "today_rounds", "daily_target": 3}`

---

## Math Placement

Source: `backend/routers/math_placement.py`
Data: `backend/data/math/placement/bank.json`
Supports bulk (ship all questions) and adaptive CAT-lite (one at a time) flows.

### `GET /api/math/placement/status`
Has the user taken the placement test?
- **Response**: `{"taken": bool, "domains_tested": int}`

### `GET /api/math/placement/start`
Return the full bank with answers stripped (bulk flow).
- **Response**: `{"version", "domains": [{"domain", "label", "questions": [{"id", "grade", "type", "question", "options"}, ...]}, ...]}`

### `POST /api/math/placement/save`
Score all domains server-side, replace prior results, return estimates.
- **Body**: `{"results": [{"domain": str, "answers": {"{qid}": "user_answer"}}, ...]}`
- **Response**: `{"saved_domains": [str], "results": [{"domain", "label", "estimated_grade", "raw_score", "total_questions", "by_grade"}, ...], "suggested_grade": str}`
- **Suggested grade**: min (weakest) of per-domain estimates.

### `POST /api/math/placement/next` (adaptive)
Return next question given history; step up on correct, down on wrong. Max 5 per domain.
- **Body**: `{"domain": str, "history": [{"id", "grade", "correct"}, ...]}`
- **Response**: `{"done": bool, "asked": int, "target_grade"?, "question"?: {"id", "grade", "type", "question", "options"}}`
- **Errors**: `404` unknown domain.

### `POST /api/math/placement/check` (adaptive)
Grade a single answer server-side.
- **Body**: `{"domain": str, "question_id": str, "answer": str}`
- **Response**: `{"is_correct": bool, "grade": str}`
- **Errors**: `404` unknown domain or question.

### `GET /api/math/placement/results`
Return all stored placement results.
- **Response**: `{"results": [{"domain", "estimated_grade", "rit_estimate", "raw_score", "total_questions", "test_date"}, ...]}`
- **Errors**: `404` if no results on file.

---

## Math Kangaroo

Source: `backend/routers/math_kangaroo.py`
Data: `backend/data/math/kangaroo/*.json`
Scoring: weighted by section `points_per_question` (typically 3/4/5).

### `GET /api/math/kangaroo/sets`
List all sets with per-set progress.
- **Response**: `{"sets": [{"set_id", "title", "level", "level_label", "grade_range", "total_questions", "time_limit_minutes", "max_score", "category", "drill_topic", "best_score", "completed"}, ...]}`

### `GET /api/math/kangaroo/set/{set_id}`
Return the full set with answers and solutions stripped.
- **Response**: `{"set_id", "title", "level", "level_label", "grade_range", "total_questions", "time_limit_minutes", "max_score", "category", "disclaimer", "sections": [{"name", "points_per_question", "questions": [{"id", "number", "points", "topic", "question_text", "image_svg", "image_description", "options": {"A"..."E"}}, ...]}, ...]}`
- **Errors**: `404` set not found, `500` corrupt JSON.

### `POST /api/math/kangaroo/submit-answer` (Practice mode)
Grade one question; return correctness, solution, weighted points.
- **Body**: `{"set_id": str, "question_id": str, "answer": str}`
- **Response**: `{"is_correct", "correct_answer", "solution", "points_earned"}`
- **Errors**: `404` question not found.

### `POST /api/math/kangaroo/submit` (Test mode)
Grade entire set; save best; award XP + streak.
- **Body**:
  ```json
  {"set_id": str, "answers": [{"question_id": str, "answer": str|null}, ...],
   "time_spent_seconds": int|null}
  ```
- **Response**: `{"score", "max_score", "percentage", "correct", "total_questions", "time_spent_seconds", "time_spent_formatted", "grade_label", "sections": [...], "topic_breakdown": [...], "questions_review": [...], "xp_earned", "perfect", "is_new_best"}`
- **XP**: `math_kangaroo_complete` (+5), `math_kangaroo_80` (+5) if ≥80%, `math_kangaroo_perfect` (+10) if perfect. Dedup per-day per-set via direct `XPLog` insert.

---

## Math Glossary

Source: `backend/routers/math_glossary.py`
Data: `backend/data/math/glossary/{grade}.json`

### `GET /api/math/glossary/grades`
List glossary grades with term counts.
- **Response**: `{"grades": [{"grade", "title", "term_count"}, ...]}`

### `GET /api/math/glossary/{grade}`
Return all terms for a grade, grouped by category.
- **Path**: `grade` — case-insensitive (lowercased for file lookup).
- **Response**: `{"grade", "title", "categories": [{"name", "terms": [{"id", "term", "kid_friendly"}, ...]}, ...], "total"}`
- **Errors**: `404` grade not found.

### `GET /api/math/glossary/{grade}/{term_id}`
Full details for one term.
- **Response**: the raw term object (fields vary per data file).
- **Errors**: `404` term not found.

---

## Math Problems (My Problems)

Source: `backend/routers/math_problems.py`
Spaced repetition: intervals `[1, 3, 7, 21]` days. Phase 1 rule — 1 correct review = mastered.

### `GET /api/math/my-problems/summary`
Counts for the My-Problems dashboard.
- **Response**: `{"total_pending", "due_today", "mastered"}`

### `GET /api/math/my-problems/review`
Up to 20 items due today with full problem payload.
- **Response**: `{"items": [{"review_id", "problem_id", "times_reviewed", "interval_days", "grade", "unit", "lesson", "original_stage", "problem": {...}}, ...], "count"}`
- Items whose originating attempt or lesson file cannot be resolved are skipped (not errored).

### `POST /api/math/my-problems/submit-answer`
Grade a review answer; master on correct, bump interval on wrong.
- **Body**: `{"review_id": int, "user_answer": str}`
- **Response**: `{"is_correct", "correct_answer", "is_mastered", "next_review_date"|null, "feedback"}`
- **Error fallback**: `{"error": str}` (200 with error key; no HTTP error) for missing review/problem.

---

## Common Conventions

### Authentication
No per-user auth — this is a single-user local app. The FastAPI server at `http://localhost:8000` trusts all clients on loopback.

### Error format
FastAPI default: `{"detail": "<message>"}` with HTTP status code (`400`, `404`, `500`).

### Content type
All POST bodies are JSON (`application/json`). All responses are JSON.

### Caching
All routers use `functools.lru_cache` keyed by `(path, mtime)` for JSON data files — file edits auto-invalidate. `math_daily.py` uses a date-keyed dict cache for the practice pool. Each module exposes `clear_caches()` for manual flushing.

### Side effects
XP, streak, and progress writes go through `services/xp_engine.py` + `services/streak_engine.py`. The `MathWrongReview` table is populated by Academy `submit-answer` on incorrect non-pretest answers.

### Related docs
- `backend/API_INDEX.md` — all endpoints (English + Math + System) in table form.
- `backend/DB_INDEX.md` — SQLAlchemy model reference.
- `MATH_SPEC.md` — math module spec (Daily Challenge composition, Fluency phases, etc.).
- `CLAUDE.md` — overall project spec.
