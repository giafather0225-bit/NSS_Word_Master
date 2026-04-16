# GIA Learning App — Database Index

> SQLite database at `~/NSS_Learning/database/voca.db`  
> ORM: SQLAlchemy — models defined in `backend/models.py`  
> Migrations: `backend/migrations/`

---

## Existing Tables (Phase 1 — DO NOT MODIFY SCHEMA)

### lessons
Core lesson metadata.

| Column | Type | Notes |
|--------|------|-------|
| id | Integer PK | |
| subject | String | "English" / "Math" |
| textbook | String | e.g., "Voca_8000" |
| lesson_name | String | e.g., "Lesson_09" |
| source_type | String | "ocr" / "manual" / "file" |
| description | String | |
| created_at | String | ISO 8601 |

**Index:** (subject, textbook, lesson_name)  
**Related API:** GET /api/lessons, GET /api/subjects, GET /api/textbooks/{subject}

---

### study_items
Individual vocabulary items per lesson.

| Column | Type | Notes |
|--------|------|-------|
| id | Integer PK | |
| subject | String | |
| textbook | String | |
| lesson | String | |
| lesson_id | Integer FK → lessons.id | nullable |
| source_type | String | "ocr" / "manual" |
| question | String | definition or prompt |
| answer | String | correct spelling |
| hint | String | example sentence with blank |
| extra_data | String | JSON: {pos, image, definition, example} |

**Index:** (subject, textbook, lesson)  
**Related API:** GET /api/study/{subject}/{textbook}/{lesson}

---

### progress
Stage progress per lesson.

| Column | Type | Notes |
|--------|------|-------|
| id | Integer PK | |
| subject | String | |
| textbook | String | |
| lesson | String | |
| current_index | Integer | default 0 |
| best_streak | Integer | default 0 |

**Index:** (subject, textbook, lesson)  
**Related API:** POST /api/progress/verify

---

### rewards (Legacy)
Old reward system — superseded by reward_items + purchased_rewards.

| Column | Type | Notes |
|--------|------|-------|
| id | Integer PK | |
| title | String | |
| description | String | |
| is_earned | Boolean | |

**Related API:** GET /api/rewards

---

### schedules (Legacy)
Old schedule system — superseded by academy_schedules.

| Column | Type | Notes |
|--------|------|-------|
| id | Integer PK | |
| test_date | String | YYYY-MM-DD |
| memo | String | |

**Related API:** GET /api/schedules

---

### user_practice_sentences
Sentences created by the user in Step 5 (Make a Sentence).

| Column | Type | Notes |
|--------|------|-------|
| id | Integer PK | |
| subject | String | |
| textbook | String | |
| lesson | String | |
| item_id | Integer | study_items.id |
| sentence | String | user's sentence |

**Related API:** POST /api/practice/sentence

---

### words
Word metadata with OCR source info.

| Column | Type | Notes |
|--------|------|-------|
| id | Integer PK | |
| word | String | |
| definition | String | |
| example | String | |
| pos | String | part of speech |
| lesson_id | Integer FK → lessons.id | nullable |
| study_item_id | Integer FK → study_items.id | nullable |
| source_type | String | "ocr" / "manual" |
| ocr_engine | String | "tesseract" / "vision" / "" |
| created_at | String | |

**Related API:** POST /api/words/lesson/{lesson_id}

---

### word_reviews
SM-2 spaced repetition review records.

| Column | Type | Notes |
|--------|------|-------|
| id | Integer PK | |
| study_item_id | Integer FK → study_items.id | |
| word | String | |
| subject | String | |
| textbook | String | |
| lesson | String | |
| easiness | String | SM-2 factor, default "2.5" |
| interval | Integer | days until next review |
| repetitions | Integer | total correct streak |
| next_review | String | YYYY-MM-DD |
| last_review | String | |
| total_reviews | Integer | |
| total_correct | Integer | |

**Indexes:** (next_review), (subject, textbook)  
**Related API:** GET /api/review/today, POST /api/review/result

---

## New Tables (Phase 1 Migration — 001_add_new_tables.py)

### app_config
Key-value store for app settings (PIN, email, theme, etc.)

| Column | Type | Notes |
|--------|------|-------|
| id | Integer PK | |
| key | String UNIQUE | "pin", "parent_email", "growth_theme" |
| value | String | |
| updated_at | String | ISO 8601 |

**Related API:** POST /api/parent/config (Phase 7)

---

### xp_logs
XP award history with daily dedup support.

| Column | Type | Notes |
|--------|------|-------|
| id | Integer PK | |
| action | String | "review_complete", "stage_complete", "final_test_pass", etc. |
| xp_amount | Integer | |
| detail | String | JSON: {"lesson": "Lesson_05", "stage": "PREVIEW"} |
| earned_date | String | YYYY-MM-DD (daily dedup key) |
| created_at | String | |

**Related API:** GET /api/xp/summary, POST /api/xp/award (Phase 3)

---

### streak_logs
Daily study streak tracking.

| Column | Type | Notes |
|--------|------|-------|
| id | Integer PK | |
| date | String UNIQUE | YYYY-MM-DD |
| review_done | Boolean | |
| daily_words_done | Boolean | |
| streak_maintained | Boolean | |

**Related API:** GET /api/streak/status (Phase 3)

---

### task_settings
Parent-configurable Today's Tasks list.

| Column | Type | Notes |
|--------|------|-------|
| id | Integer PK | |
| task_key | String UNIQUE | "review", "daily_words", "academy", "journal", "creative_writing" |
| is_required | Boolean | ★ marked tasks |
| xp_value | Integer | XP awarded on completion |
| is_active | Boolean | whether to show task |

**Seeded defaults:** 5 tasks (review=required, others=optional)  
**Related API:** GET /api/tasks/today (Phase 2)

---

### reward_items
Reward shop catalog.

| Column | Type | Notes |
|--------|------|-------|
| id | Integer PK | |
| name | String | "YouTube 30min" |
| icon | String | emoji "📺" |
| price | Integer | XP cost |
| discount_pct | Integer | 0–100 |
| is_active | Boolean | |
| created_at | String | |

**Seeded defaults:** 5 items  
**Related API:** GET /api/shop/items (Phase 5)

---

### purchased_rewards
User reward purchase history.

| Column | Type | Notes |
|--------|------|-------|
| id | Integer PK | |
| reward_item_id | Integer FK → reward_items.id | |
| xp_spent | Integer | actual XP charged (after discount) |
| is_used | Boolean | |
| purchased_at | String | |
| used_at | String | nullable |

**Related API:** POST /api/shop/buy, POST /api/shop/use-reward (Phase 5)

---

### daily_words_progress
Daily Words 7-day cycle tracking.

| Column | Type | Notes |
|--------|------|-------|
| id | Integer PK | |
| grade | String | "grade_3" through "grade_9" |
| cycle_start | String | YYYY-MM-DD (7-day cycle start) |
| word_index | Integer | current position in grade word list |
| test_words_json | String | JSON array of words failed on Day 1 test |
| daily_learned | Integer | words studied today |
| last_study_date | String | |

**Related API:** GET /api/daily-words/today (Phase 4)

---

### diary_entries
Daily Journal entries.

| Column | Type | Notes |
|--------|------|-------|
| id | Integer PK | |
| entry_date | String | YYYY-MM-DD |
| content | String | journal text |
| photo_path | String | nullable, relative path |
| ai_feedback | String | nullable, AI grammar/spell feedback |
| created_at | String | |

**Related API:** POST /api/diary/entries (Phase 6)

---

### growth_events
Growth Timeline automatic event log.

| Column | Type | Notes |
|--------|------|-------|
| id | Integer PK | |
| event_type | String | "lesson_pass", "streak_7", "milestone_100", "theme_complete", "lesson_reset", etc. |
| title | String | display message |
| detail | String | JSON extra data |
| event_date | String | YYYY-MM-DD |
| created_at | String | |

**Related API:** GET /api/growth/timeline (Phase 6)

---

### day_off_requests
Student day-off excuse requests.

| Column | Type | Notes |
|--------|------|-------|
| id | Integer PK | |
| request_date | String | YYYY-MM-DD |
| reason | String | student's reason |
| status | String | "pending" / "approved" / "denied" |
| parent_response | String | nullable |
| created_at | String | |

**Related API:** POST /api/day-off/request (Phase 6)

---

### academy_sessions
Academy lesson session tracking (2-day limit enforcement).

| Column | Type | Notes |
|--------|------|-------|
| id | Integer PK | |
| subject | String | |
| textbook | String | |
| lesson | String | |
| started_date | String | YYYY-MM-DD |
| current_stage | String | "PREVIEW" / "A" / "B" / "C" / "D" / "EXAM" |
| is_completed | Boolean | |
| is_reset | Boolean | auto-reset on day 3 |

**Related API:** checked by reminder engine (Phase 2)

---

### learning_logs
Detailed session-level learning history.

| Column | Type | Notes |
|--------|------|-------|
| id | Integer PK | |
| subject | String | |
| textbook | String | |
| lesson | String | |
| stage | String | "PREVIEW" / "A" / "B" / "C" / "D" |
| word_count | Integer | |
| correct_count | Integer | |
| wrong_words_json | String | JSON array |
| started_at | String | |
| completed_at | String | |
| duration_sec | Integer | |

**Related API:** GET /api/parent/word-stats (Phase 7)

---

### word_attempts
Per-word attempt records for error pattern analysis.

| Column | Type | Notes |
|--------|------|-------|
| id | Integer PK | |
| study_item_id | Integer FK → study_items.id | nullable |
| subject | String | |
| textbook | String | |
| lesson | String | |
| word | String | |
| stage | String | |
| is_correct | Boolean | |
| user_answer | String | what the user typed |
| attempted_at | String | |

**Related API:** GET /api/parent/word-stats (Phase 7)

---

### academy_schedules
Parent-configured academy test days.

| Column | Type | Notes |
|--------|------|-------|
| id | Integer PK | |
| day_of_week | Integer | 0=Mon … 6=Sun |
| memo | String | |
| is_active | Boolean | |

**Related API:** POST /api/parent/academy-schedule (Phase 7)

---

### growth_theme_progress
5-theme × 6-step × 3-variation growth illustration progress.

| Column | Type | Notes |
|--------|------|-------|
| id | Integer PK | |
| theme | String | "space" / "tree" / "city" / "animal" / "ocean" |
| variation | Integer | 1, 2, or 3 |
| current_step | Integer | 0–5 |
| is_completed | Boolean | |
| is_active | Boolean | currently selected theme |
| started_at | String | |
| completed_at | String | nullable |

**Related API:** GET /api/growth/theme (Phase 8)

---

## Quick Search

```bash
# Find all models
grep -n "class.*Base" backend/models.py

# Check table exists in DB
sqlite3 ~/NSS_Learning/database/voca.db ".tables"

# Run migrations
cd backend && python migrations/001_add_new_tables.py
```
