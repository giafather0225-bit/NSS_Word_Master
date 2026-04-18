# GIA Learning App — Project Spec (CLAUDE.md)

## Overview
- **Product**: English vocabulary learning app for children — 5-stage lesson flow, AI scoring, XP/Streak system, Reward Shop, Parent Dashboard, and Growth Theme.
- **Status**: ✅ Phases 1–10 complete. All planned features shipped.
- **GitHub**: https://github.com/giafather0225-bit/NSS_Word_Master

---

## Tech Stack
- **Backend**: Python / FastAPI (`routers/` structure)
- **Frontend**: HTML, CSS, Vanilla JS (modular — no bundler)
- **Database**: SQLite WAL at `~/NSS_Learning/database/voca.db`
- **AI**: Ollama (gemma2:2b, http://localhost:11434) / Gemini fallback
- **Speech**: Web Speech API (browser-based)
- **TTS**: edge-tts → BytesIO in-memory → fetch → Blob → Audio (no temp files, no afplay)

---

## Work Principles (MUST FOLLOW — violations invalidate the task)

1. Read existing code before modifying. Never break existing functionality.
2. Max 300 lines per file. Split into modules when approaching limit.
3. `child.js` is already split into modules (Phase 1 done). Do not revert.
4. CSS: use `theme.css` variables only. No hard-coded hex colors in component CSS.
5. All API endpoints: proper error handling + correct HTTP status codes.
6. DB schema changes: write migration in `backend/migrations/`.
7. Python: type hints + docstrings. JS: JSDoc `@tag` comments on every function.
8. async/await consistently. No N+1 queries. Use indexes.
9. Security: sanitize all user input. SQL injection / XSS prevention. Prompt injection defense on AI inputs.
10. After any change: verify 5-Stage learning, Review, Final Test, Unit Test, Word Manager still work.
11. UI text in English only. Apple-minimal design (no gradients, no heavy shadows).
12. When changing element IDs/classes: update ALL references simultaneously.
13. List all modified files at the end of every response.

---

## File Structure

```
NSS_Word_Master/
├── CLAUDE.md
├── backend/
│   ├── main.py                    # FastAPI entry point + legacy routes pending extraction
│   ├── database.py                # SQLite WAL engine, get_db(), LEARNING_ROOT
│   ├── models.py                  # SQLAlchemy models (8 existing + 15 new = 23 total)
│   ├── API_INDEX.md               # All API endpoints index
│   ├── DB_INDEX.md                # All DB tables index
│   ├── routers/
│   │   ├── lessons.py             # /api/subjects, /api/textbooks, /api/lessons, /api/voca/*
│   │   ├── study.py               # /api/study, /api/learning/*
│   │   ├── progress.py            # /api/progress/*
│   │   ├── review.py              # /api/review/* (SM-2)
│   │   ├── words.py               # /api/words/*, /api/mywords/*
│   │   ├── files.py               # /api/files/*, /api/storage/*, /api/ocr/*
│   │   ├── tts.py                 # /api/tts/*
│   │   ├── ai_coach.py            # /api/ai-coach/today (stub → Phase 3)
│   │   ├── xp.py                  # ★ Phase 3: /api/xp/*, /api/streak/*, /api/tasks/today
│   │   ├── reward_shop.py         # ★ Phase 5: /api/shop/*
│   │   ├── daily_words.py         # ★ Phase 4: /api/daily-words/*
│   │   ├── diary.py               # ★ Phase 6: /api/diary/*, /api/growth/*, /api/day-off/*
│   │   ├── calendar_api.py        # ★ Phase 6: /api/calendar/*
│   │   ├── parent.py              # ★ Phase 7: /api/parent/*
│   │   └── reminder.py            # ★ Phase 2: /api/reminders/today
│   ├── services/
│   │   ├── sm2.py                 # SM-2 algorithm (existing)
│   │   ├── ai_service.py          # Ollama/Gemini unified (existing)
│   │   ├── tts_edge.py            # edge-tts BytesIO (existing)
│   │   ├── xp_engine.py           # ★ Phase 3
│   │   ├── streak_engine.py       # ★ Phase 3
│   │   ├── reminder_engine.py     # ★ Phase 2
│   │   ├── daily_words_engine.py  # ★ Phase 4
│   │   ├── backup_engine.py       # ★ Phase 10
│   │   └── ollama_manager.py      # ★ Phase 10
│   ├── data/
│   │   └── daily_words/           # ★ Phase 4: grade_2.json … grade_9.json
│   └── migrations/
│       └── 001_add_new_tables.py  # ✅ Phase 1: 15 new tables
├── frontend/
│   ├── COMPONENT_MAP.md           # Screen → JS/CSS/HTML/API map
│   └── static/
│       ├── css/
│       │   ├── theme.css          # ★ SINGLE SOURCE OF TRUTH for all CSS variables
│       │   ├── style.css          # Global styles (references theme.css vars)
│       │   ├── main.css           # Layout (references theme.css vars, alias vars only)
│       │   ├── home.css           # ★ Phase 2
│       │   ├── preview.css
│       │   ├── wordmatch.css
│       │   ├── fillblank.css
│       │   ├── spelling.css
│       │   ├── sentence.css
│       │   ├── finaltest.css
│       │   ├── unittest.css
│       │   ├── review.css
│       │   ├── word-manager.css
│       │   ├── reward-shop.css    # ★ Phase 5
│       │   ├── diary.css          # ★ Phase 6
│       │   ├── calendar.css       # ★ Phase 6
│       │   └── parent.css         # ★ Phase 7
│       └── js/
│           ├── core.js            # ★ CONF, STAGE, global state, utilities, audio FX
│           ├── tts-client.js      # ★ TTS fetch/play helpers
│           ├── analytics.js       # ★ Learning log + word attempt tracking
│           ├── navigation.js      # ★ Sidebar, dropdowns, roadmap UI
│           ├── preview.js         # ★ Step 1: Preview + Shadow + Spell
│           ├── wordmatch.js       # ★ Step 2: Word Match
│           ├── fillblank.js       # ★ Step 3: Fill the Blank
│           ├── spelling.js        # ★ Step 4: Spelling Master
│           ├── sentence.js        # ★ Step 5: Make a Sentence
│           ├── child.js           # App shell: renderStage, DEV, DOMContentLoaded
│           ├── sentence_ai.js     # AI sentence evaluation helpers
│           ├── finaltest.js
│           ├── unittest.js
│           ├── review.js
│           ├── word-manager.js
│           ├── home.js            # ★ Phase 2
│           ├── reward-shop.js     # ★ Phase 5
│           ├── diary.js           # ★ Phase 6
│           ├── calendar.js        # ★ Phase 6
│           ├── parent.js
│           ├── growth-theme.js    # ★ Phase 8
│           └── ai-coach.js        # ★ Phase 3
```

---

## Design System (theme.css — single source of truth)

```css
:root {
  --color-primary:        #D4619E;
  --color-primary-hover:  #C0508D;
  --color-primary-light:  #FAE8F3;
  --color-secondary:      #4A8E8E;
  --color-success:        #34C759;
  --color-error:          #FF3B30;
  --color-warning:        #FF9500;
  --bg-page:              #FDF2F8;
  --bg-card:              #FFFFFF;
  --text-primary:         #2D2D3F;
  --text-secondary:       #8B8BA0;
  --shadow-card:          0 2px 12px rgba(0,0,0,0.06);
  --radius-sm:            8px;
  --radius-md:            12px;
  --radius-lg:            20px;
  --radius-full:          9999px;
  --font-family:          -apple-system, BlinkMacSystemFont, "SF Pro Display", sans-serif;
}
```

Rules:
- All component CSS uses `var(--token)` only — no hard-coded hex values
- Apple-minimal: no gradients, box-shadow ≤ `0 2px 12px rgba(0,0,0,0.06)`
- Dark mode: reserved as `[data-theme="dark"]` in theme.css — not yet active

---

## Script Loading Order (child.html)

```html
<!-- Base modules (load first) -->
<script src="/static/js/core.js?v=1"></script>
<script src="/static/js/tts-client.js?v=1"></script>
<script src="/static/js/analytics.js?v=1"></script>
<script src="/static/js/navigation.js?v=1"></script>
<!-- Stage modules -->
<script src="/static/js/preview.js?v=1"></script>
<script src="/static/js/wordmatch.js?v=1"></script>
<script src="/static/js/fillblank.js?v=1"></script>
<script src="/static/js/spelling.js?v=1"></script>
<script src="/static/js/sentence.js?v=1"></script>
<!-- App shell (last) -->
<script src="/static/js/child.js?v=29"></script>
<!-- Feature overlays -->
<script src="/static/js/finaltest.js"></script>
<script src="/static/js/unittest.js"></script>
<script src="/static/js/review.js"></script>
<script src="/static/js/word-manager.js"></script>
<script src="/static/js/sentence_ai.js"></script>
```

All modules share global `window` scope — no ES module `import`/`export`.

---

## Dev Tools (child.js — do not modify)

```javascript
DEV.go(1)   // → Preview
DEV.go(2)   // → Word Match
DEV.go(3)   // → Fill the Blank
DEV.go(4)   // → Spelling Master
DEV.go(5)   // → Make a Sentence
DEV.go(6)   // → Final Test
DEV.skip()  // → skip current word
```

---

## Code Annotation Rules

### File Header (every JS/CSS/Python file)

```javascript
/* ================================================================
   [filename] — [one-line description]
   Section: [Home / English / Diary / Shop / Parent / System]
   Dependencies: [list]
   API endpoints: [list or "none"]
   ================================================================ */
```

```python
"""
routers/xp.py — XP system API
Section: System
Dependencies: services/xp_engine.py, models.py (XPLog)
API: GET /api/xp/summary, POST /api/xp/award
"""
```

### Function Tags (every function)

```javascript
/** @tag XP @tag AWARD */
async function awardXP(action, detail) { ... }
```

```python
# @tag XP @tag STREAK
def check_streak_bonus(user_date: str) -> int:
```

Available tags:
```
HOME_DASHBOARD  TODAY_TASKS   REMINDER      AI_COACH
SIDEBAR         ACCORDION     NAVIGATION
ENGLISH         ACADEMY       DAILY_WORDS   MY_WORDS      READING
PREVIEW         SHADOW        SENTENCE_READ SPELL
WORD_MATCH      FILL_BLANK    SPELLING      SENTENCE
FINAL_TEST      UNIT_TEST     WEEKLY_TEST
REVIEW          SM2           ACTIVE_RECALL
DIARY           JOURNAL       MY_SENTENCES  MY_WORLDS     GROWTH_TIMELINE
CALENDAR        DAY_OFF
XP              STREAK        AWARD         BONUS
SHOP            REWARD        PURCHASE      PIN
PARENT          SETTINGS      WORD_STATS    SCHEDULE      NOTIFICATION
TTS             AI            OLLAMA        GEMINI        OCR
BACKUP          SYSTEM        THEME         GROWTH_THEME
```

---

## Database Models

### Existing (Phase 0 — DO NOT modify schema)
`Lesson`, `StudyItem`, `Progress`, `Reward`, `Schedule`, `UserPracticeSentence`, `Word`, `WordReview`

### New (Phase 1 — migration 001_add_new_tables.py)
`AppConfig`, `XPLog`, `StreakLog`, `TaskSetting`, `RewardItem`, `PurchasedReward`,
`DailyWordsProgress`, `DiaryEntry`, `GrowthEvent`, `DayOffRequest`, `AcademySession`,
`LearningLog`, `WordAttempt`, `AcademySchedule`, `GrowthThemeProgress`

Full column specs: `backend/DB_INDEX.md`

---

## Learning Flow

```
Home Dashboard → English → Lesson Select
→ Preview (Step 1) → Word Match (Step 2) → Fill Blank (Step 3)
→ Spelling (Step 4) → Make Sentence (Step 5) → Final Test → Complete
```

---

## Step Specs

### Step 1 — Preview
4×5 card grid. Click → popup modal.
- POS pill → Word (32px 700) → Definition → Example (italic)
- Listen (TTS) → Shadow ×2 (mic → Web Speech → ≥80% pass) → Spell ×2 (input → correct/wrong)
- Phase 9 addition: Sentence Reading ×2 (TTS example → mic → ≥90% pass)

### Step 2 — Word Match
7 words/round, two columns. Match word ↔ definition.
- Selected: `--color-primary` border+bg. Matched: `--color-success` + opacity 0.6. Wrong: shake 0.3s.

### Step 3 — Fill the Blank
Sentence with blank + word tag pills. Select correct word.
- Correct: `--color-success`. Wrong: `--color-error` + shake.

### Step 4 — Spelling Master
Wordle-style 48×48px letter boxes. 3 passes (hint → first letter → blank).
Wrong → retryQueue (must clear all before advancing).

### Step 5 — Make a Sentence
Stage 1: drag-and-drop word scramble.
Stage 2: free writing → AI scores grammar+spelling (Ollama → Gemini fallback).

### Final Test
MC 20 + Fill-in 20. 30-minute timer. Pass = 90%.
Pass → XP +10 + `GrowthEvent("lesson_pass")`.
Fail → re-study required. Retry pass → XP +10.

---

## Sidebar Structure (English Mode — Phase 2)

```
← Home
VOCABULARY
  📕 Academy         ▼   (accordion — one open at a time)
    Textbook: [dropdown]
    Lesson:   [dropdown]
    ─────────────────
    Today's Review  [N]   (SM-2 due count badge; hidden when 0)
    Final Test  🔒
    Unit Test   ›
  📗 Daily Words      ▼
    This Week: 42/70
    Today: 3/10
    Weekly Test ›
  📘 My Words         ▼
    3 lists
    Weekly Test › (needs 50+ words)
READING
  📖 Articles  › (Coming Soon)
```

Settings (Parent Dashboard) access: Home banner "···" menu → 4-digit PIN.
Not duplicated in English sidebar.

---

## Home Dashboard Layout (Phase 2)

```
[AI Coach Message Card]           ← GET /api/ai-coach/today
[Reminder Banners (stackable)]    ← GET /api/reminders/today
[Today's Tasks]
  ★ Review (12 words) .......... +2 XP [Required]
    Daily Words (0/10) ......... +5 XP
    Academy Lesson 5 ........... +10 XP
    Daily Journal .............. +10 XP
  ─────────────────────────────
  Must Do bonus ................ +5 XP
  All complete bonus ........... +15 XP
[Section Cards: English | Math | Diary | Arcade (Coming Soon) | Reward Shop]
[Growth Theme Illustration (200×200 SVG)]
[Bottom Bar: Words I Know | ⭐ Total XP | 🔥 Streak | Reward Shop]
```

---

## XP Rules

| Action | XP | Limit |
|--------|-----|-------|
| Word correct | +1 | per attempt |
| Stage complete | +2 | once/stage/lesson |
| Final Test pass | +10 | once; retry pass = +10 |
| Unit Test pass | +5 | once |
| Daily Words daily complete | +5 | once/day |
| Weekly Test pass | +10 | once/week |
| Review complete | +2 | once/day |
| Daily Journal | +10 | once/day |
| Must Do all complete | +5 | once/day |
| All tasks complete | +15 | once/day |
| 7-day streak | +30 | per occurrence |
| 30-day streak | +200 | per occurrence |
| Arcade round (tiered) | +1 / +2 / +3 | 500 / 1000 / 2000 score; daily cap +10 |

No XP: test fail, re-study after fail.

---

## Streak Rules
- Review available day: Review + Daily Words → streak maintained
- No review due: Daily Words only → streak maintained
- Approved Day Off → streak frozen (maintained)

---

## Academy Session Rules (Phase 2+)
- Session starts on lesson select
- Max 2 days between stages; day 3 → auto-reset + `GrowthEvent("lesson_reset")` + home banner
- Tracked via `AcademySession` table

---

## GIA's Diary Sections (Phase 6)
- **Daily Journal**: write + optional photo + AI grammar feedback
- **Free Writing**: Coming Soon
- **My Sentences**: Step 5 sentences; 2-week-old → "Rewrite!" prompt
- **My Worlds**: completed theme collection
- **Growth Timeline**: `GrowthEvent` log (reverse-chron)
- **Calendar**: monthly view with 🔥⬜🏖️📝✅ markers
- **Day Off**: reason form → email to parent → pending/approved/denied

---

## Reward Shop (Phase 5)
Default items (seeded): YouTube 30min (300), Roblox 30min (300), Family Movie (500), Dinner Out (500), Custom Reward (300).

Buy flow: card click → confirm popup → XP deducted → `PurchasedReward` created.
Use flow: "My Rewards" → [Use] → 4-digit PIN → `is_used=True`.

---

## Parent Dashboard (Phase 7)
Access: Settings(⚙️) → 4-digit PIN.
Sections: Overview, Word Stats, Shop Management, Task Settings, Academy Schedule, Day Off Requests, Notifications, Change PIN, Add Textbook.

---

## Growth Theme (Phase 8)
5 themes × 6 steps × 3 variations = 90 SVGs in `frontend/static/img/themes/`.
XP milestones: 100→300→600→1000→1500 XP per step.
Complete → `GrowthEvent("theme_complete")` + added to My Worlds.

---

## System (Phase 10)
- **Ollama auto-start**: `services/ollama_manager.py` — subprocess `ollama serve` + ping + fallback UI
- **Auto-backup**: `services/backup_engine.py` — copy DB on startup, keep 7 days
- **macOS LaunchAgent**: plist example in README

---

## Implementation Phases

| Phase | Status | Description |
|-------|--------|-------------|
| 1 | ✅ DONE | Infra: JS modules, router split, CSS cleanup, DB migration |
| 2 | ✅ DONE | Home dashboard + sidebar accordion + section navigation |
| 3 | ✅ DONE | XP + Streak engines + AI coach |
| 4 | ✅ DONE | Daily Words G2–G9 |
| 5 | ✅ DONE | Reward Shop + PIN |
| 6 | ✅ DONE | GIA's Diary (Journal, Timeline, Calendar, Day Off) |
| 7 | ✅ DONE | Parent Dashboard |
| 8 | ✅ DONE | Growth Theme (90 SVGs) |
| 9 | ✅ DONE | Preview Sentence Reading (×2) |
| 10 | ✅ DONE | Ollama auto-start, auto-backup, macOS LaunchAgent |

Each phase: verify existing features still work before marking complete.

---

## Key HTML Element IDs (child.html)

**Sidebar:** `#sidebar`, `#sb-profile`, `#tab-eng`, `#tab-math`, `#star-count`, `#textbook-select`, `#lesson-select`, `#btn-review`, `#btn-exam`, `#btn-word-manager`, `#btn-parent`, `#sidebar-toggle`

**Top Bar:** `#roadmap`, `#stars-count`, `#top-progress-fill`, `#progress-pct`

**Main Content:** `#stage-area`, `#idle-wrapper`, `#btn-start`, `#stage-card`, `#stage`

**Modals:** `#preview-modal`, `#magic-overlay`, `#tutor-modal`, `#wm-overlay`, `#exam-overlay`, `#ut-overlay`

---

## Quick Reference

```bash
# Find functions by tag
grep -r "@tag XP" .
grep -r "@tag PREVIEW" frontend/static/js/

# Find API endpoint definitions
grep -rn "router\." backend/routers/

# Find API calls in frontend
grep -r "/api/xp" frontend/static/js/

# Component ownership lookup
grep -A 8 "Home Dashboard" frontend/COMPONENT_MAP.md

# DB status
sqlite3 ~/NSS_Learning/database/voca.db ".tables"

# Run migration
cd backend && python3 migrations/001_add_new_tables.py
```
