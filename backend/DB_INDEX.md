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
| easiness | Float | SM-2 factor, default 2.5 (migration 056) |
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

## CKLA Tables

### ckla_domains / ckla_lessons / ckla_lesson_progress (migration 011 + 018 수정)

#### CKLADomain (수정)
| Column | Type | Notes |
|--------|------|-------|
| id | Integer PK | |
| domain_num | Integer | 1–11 |
| title | String | |
| grade | Integer NOT NULL DEFAULT 3 | **신규 (018)** — G3~G8 확장용 |

#### CKLALesson (수정)
| Column | Type | Notes |
|--------|------|-------|
| id | Integer PK | |
| domain_id | Integer FK → ckla_domains.id | |
| lesson_num | Integer | |
| title | String | |
| grade | Integer NOT NULL DEFAULT 3 | **신규 (018)** |

#### CKLALessonProgress (수정)
| Column | Type | Notes |
|--------|------|-------|
| id | Integer PK | |
| lesson_id | Integer FK → ckla_lessons.id | |
| read_done | Boolean | |
| words_done | Boolean | |
| qa_done | Boolean | |
| wordwork_done | Boolean | |
| completed_at | String | nullable |
| grade | Integer NOT NULL DEFAULT 3 | **신규 (018)** |
| started_at | String | **신규 (018)** — 학습 시작 시간 |
| difficulty_rating | String | **신규 (018)** — easy/neutral/hard |

#### xp_logs (수정)
| Column | Type | Notes |
|--------|------|-------|
| ... | ... | 기존 컬럼 유지 |
| source | String | **신규 (018)** — "ckla" / "dux" / "math" / etc. |

---

### ckla_badges (신규 — migration 019)

| Column | Type | Notes |
|--------|------|-------|
| id | Integer PK | |
| badge_key | String UNIQUE | e.g. "domain_1_complete", "grade_3_master" |
| badge_name | String | display name |
| description | String | unlock condition text |
| condition_type | String | "domain_complete" / "grade_complete" |
| condition_value | Integer | domain_num or grade |
| image_path | String | nullable, relative path |
| created_at | String | ISO 8601 |

---

### ckla_user_badges (신규 — migration 019)

| Column | Type | Notes |
|--------|------|-------|
| id | Integer PK | |
| badge_key | String FK → ckla_badges.badge_key | |
| earned_at | String | ISO 8601 |

**Index:** (badge_key) UNIQUE — 중복 지급 방지

---

## Island System Tables (`backend/models/island.py` — migration 018)

### island_characters

| Column | Type | Notes |
|--------|------|-------|
| id | Integer PK | |
| name | String | e.g. "Clover", "Axie" |
| zone | String | forest/ocean/savanna/space/legend |
| subject | String | english/math/diary/review/all |
| order_index | Integer | display order within zone |
| description | String | flavor text |
| images | String | JSON map stage→path |
| lumi_production | Integer | Lumi/day when completed |
| xp_boost_pct | Float | base XP boost % for active char |
| xp_boost_a_pct | Float | A-form XP bonus % |
| xp_boost_b_pct | Float | B-form extra lumi/day |
| is_legend | Boolean | true for legend zone chars |
| unlock_requires_character_id | Integer FK → island_characters.id | nullable |
| is_available | Boolean | seeded false; set true when adoption unlocks |
| evo_first_xp | Integer | cumulative XP threshold for 1st evolution |
| evo_second_xp | Integer | cumulative XP threshold for 2nd evolution |

### island_character_progress

| Column | Type | Notes |
|--------|------|-------|
| id | Integer PK | |
| character_id | Integer FK → island_characters.id | |
| nickname | String | player-set nickname |
| stage | String | baby/mid_a/mid_b/final_a/final_b |
| level | Integer | 1–10 |
| current_xp | Integer | cumulative XP |
| hunger | Integer | 0–100 |
| happiness | Integer | 0–100 |
| is_completed | Boolean | reached final stage |
| is_active | Boolean | currently being raised |
| is_legend_type | Boolean | mirrors is_legend from catalog |
| boost_active | Boolean | study boost in effect |
| boost_subject | String | english/math/diary/review |
| last_production_date | String | ISO date, dedup guard |
| last_decay_date | String | ISO date |
| pos_x / pos_y | Integer | island position |
| adopted_at | DateTime | server default now() |
| completed_at | DateTime | nullable |

### island_care_log

| Column | Type | Notes |
|--------|------|-------|
| id | Integer PK | |
| character_progress_id | Integer FK → island_character_progress.id | |
| action | String | feed/play/decay |
| hunger_change | Integer | delta |
| happiness_change | Integer | delta |
| source | String | english/math/diary/review/food_item/auto_decay |
| logged_at | DateTime | server default now() |

**Note:** auto-deleted after 30 days by daily batch.

### island_shop_items

| Column | Type | Notes |
|--------|------|-------|
| id | Integer PK | |
| name | String | |
| category | String | evolution/decoration/food |
| sub_category | String | nullable; prop/building/nature/landscape/special/common/… |
| zone | String | target zone or "all" |
| evolution_type | String | nullable; first_a/first_b/second/legend_first_a/legend_first_b/legend_second |
| price | Integer | in Lumi (or Legend Lumi if is_legend_currency) |
| is_legend_currency | Boolean | uses Legend Lumi instead of Lumi |
| image | String | relative path |
| is_active | Boolean | |
| description | String | |

**Seeded:** 55 items by migration 018.

### island_inventory

| Column | Type | Notes |
|--------|------|-------|
| id | Integer PK | |
| shop_item_id | Integer FK → island_shop_items.id | |
| item_type | String | evolution/decoration/food |
| quantity | Integer | |
| used_on_character_progress_id | Integer FK → island_character_progress.id | nullable |
| purchased_at | DateTime | server default now() |

### island_placed_items

| Column | Type | Notes |
|--------|------|-------|
| id | Integer PK | |
| shop_item_id | Integer FK → island_shop_items.id | UNIQUE — one instance per item |
| zone | String | |
| pos_x / pos_y | Integer | placement coordinates |
| is_placed | Boolean | false = recalled to inventory |
| placed_at | DateTime | server default now() |

### island_currency

| Column | Type | Notes |
|--------|------|-------|
| id | Integer PK | always id=1 (upsert) |
| lumi | Integer | CHECK ≥ 0 |
| legend_lumi | Integer | CHECK ≥ 0 |
| total_earned | Integer | lifetime earned |
| updated_at | DateTime | auto-updated |

### island_lumi_log

| Column | Type | Notes |
|--------|------|-------|
| id | Integer PK | |
| currency_type | String | lumi/legend_lumi |
| action | String | earn/spend/exchange |
| amount | Integer | |
| source | String | english/math/diary/review/shop/exchange/production |
| balance_after | Integer | lumi balance after transaction |
| legend_balance_after | Integer | legend_lumi balance after transaction |
| character_progress_id | Integer FK → island_character_progress.id | nullable |
| earned_date | Date | nullable; dedup guard for production logs |
| created_at | DateTime | server default now() |

**Note:** auto-deleted after 90 days by daily batch.

### island_legend_progress

| Column | Type | Notes |
|--------|------|-------|
| id | Integer PK | |
| character_id | Integer FK → island_characters.id | |
| consecutive_days | Integer | resets on streak break |
| total_days | Integer | lifetime count |
| last_completed_date | Date | nullable |
| is_unlocked | Boolean | |
| is_completed | Boolean | |
| completed_at | DateTime | nullable |

### island_zone_status

| Column | Type | Notes |
|--------|------|-------|
| id | Integer PK | |
| zone | String UNIQUE | forest/ocean/savanna/space/legend |
| is_unlocked | Boolean | |
| unlocked_at | DateTime | nullable |
| first_completed_at | DateTime | nullable |

**Seeded:** 5 rows (one per zone) by migration 018.

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
