# GIA Learning App — Project Spec (CLAUDE.md)
> Last updated: 2026-04-30 — Parent Dashboard 6-tab redesign + Settings 4-section + Weekly Report wiring + Home today_by_subject + math UNIQUE migration 017

## Overview
- **Product**: 9세 여아(Gia)를 위한 AI 학습 앱 — English vocabulary, Math Academy, Diary, Arcade, US Academy, CKLA
- **GitHub**: https://github.com/giafather0225-bit/NSS_Word_Master
- **Working directory**: `/Users/markjhlee/Documents/GitHub/NSS_Word_Master`
- **DB**: `~/NSS_Learning/database/voca.db` (SQLite WAL)
- **Server**: `python3 app.py` → http://localhost:8000 (uvicorn `backend.main:app`)
- **Entry HTML**: `/`, `/child` → `child.html` · `/ingest` → `parent_ingest.html`

---

## Tech Stack
- **Backend**: Python / FastAPI — `backend/main.py` mounts **45 routers** (`backend/routers/`, ~204 endpoints).
- **Frontend**: HTML + CSS + Vanilla JS (no framework). 83 JS source + 57 CSS files. Pre-built into `bundle-{a,b,c}.min.js` via `build.sh` (esbuild). Auto-rebuilt at server startup.
- **Database**: SQLite WAL · ORM: SQLAlchemy. Models split by domain in `backend/models/`.
- **AI**: Ollama (`gemma2:2b`, local, lazy-start via `services/ollama_manager.py`) → Gemini fallback (`GEMINI_API_KEY`).
- **TTS**: edge-tts → BytesIO in-memory (no temp files) — `backend/tts_edge.py`, `routers/tts.py`.
- **Speech (STT)**: Web Speech API (browser) + server fallback `routers/speech.py`.
- **OCR**: `backend/ocr_pipeline.py` + `ocr_vision.py` (Gemini Vision).
- **Icons**: Lucide (CDN, stroke-width 1.5). 이모지 사용 금지.
- **PWA**: `service-worker.js` + `manifest.json` (root scope).

---

## Work Principles (MUST FOLLOW)

1. 수정 전 반드시 기존 코드 읽기. 기존 기능 절대 파괴 금지.
2. 파일당 최대 ~300줄. 초과 시 모듈 분리 (예: `child.js` → `child-{calendar,exam,keyboard,text}.js`).
3. CSS: `theme.css` 변수만 사용. 컴포넌트 CSS에 hex 직접 사용 금지.
4. 모든 API: 적절한 에러 핸들링 + HTTP 상태코드. `RequestValidationError` 는 `main.py` 에서 child-friendly 422 JSON 으로 자동 변환됨.
5. DB 스키마 변경: `backend/migrations/`에 idempotent 마이그레이션 추가 (현재 001~017).
6. Python: type hints + docstrings. JS: JSDoc `@tag` comments.
7. async/await 일관성. N+1 쿼리 금지.
8. 모든 사용자 입력 sanitize. SQL injection / XSS / prompt injection 방어. Pydantic 길이 제한 = `schemas_common.py` (Str80/Str200/Str500).
9. JS 변경 후 `build.sh` 가 lifespan startup 시 자동 재빌드. 수동 빌드: `bash build.sh`.
10. 변경 후 스모크 테스트: 5-Stage 학습 / Review / Final Test / Unit Test / Word Manager / Diary / Math Academy.
11. UI 텍스트: 영어만. 이모지 금지 — Lucide 아이콘 (`<i data-lucide="...">`) + JS 에서 `lucide.createIcons()`.
12. class/ID 변경 시 모든 참조 동시 업데이트 (3 bundles 모두 영향).
13. 응답 마지막에 수정된 파일 목록 기재.

---

## Repository Layout

```
NSS_Word_Master/
├── app.py                       # uvicorn entry
├── build.sh                     # esbuild → bundle-a/b/c
├── update.sh                    # git pull + restart helper
├── requirements.txt
├── pytest.ini
├── CLAUDE.md  PROJECT_SPEC.md  MATH_SPEC.md  API_INDEX.md  README.md
├── backend/
│   ├── main.py                  # FastAPI app, lifespan, validation handler
│   ├── database.py              # engine, get_db, LEARNING_ROOT
│   ├── ai_service.py            # Ollama → Gemini fallback wrapper
│   ├── ai_tutor.py              # Tutor / sentence-eval prompts
│   ├── ocr_pipeline.py / ocr_vision.py
│   ├── tts_edge.py
│   ├── sm2.py                   # SM-2 spaced repetition
│   ├── voca_sync.py / file_storage.py / folder_watcher.py / utils.py
│   ├── schemas_common.py        # Str80 / Str200 / Str500 etc.
│   ├── models/                  # SQLAlchemy ORM (11 files, by domain)
│   │   ├── _base.py  __init__.py
│   │   ├── lessons.py  system.py  gamification.py  learning.py
│   │   ├── diary.py    math.py   assistant.py
│   │   ├── us_academy.py  ckla.py  goals.py
│   ├── services/                # 11 engines / managers
│   │   ├── xp_engine.py         # XP rules + award (config-overridable)
│   │   ├── streak_engine.py     # 3-subject streak (english/math/game)
│   │   ├── academy_session.py   # active session tracking
│   │   ├── daily_words_engine.py
│   │   ├── ckla_grader.py
│   │   ├── report_engine.py     # parent weekly report (661 lines)
│   │   ├── email_sender.py
│   │   ├── pin_guard.py / pin_hash.py
│   │   ├── ollama_manager.py    # auto-start, healthcheck
│   │   └── backup_engine.py     # auto-snapshot (7-day rolling)
│   ├── routers/                 # 47 FastAPI routers (see table below)
│   ├── migrations/              # 016_weekly_goals.py latest
│   ├── data/                    # static content (math/, daily_words/)
│   │   └── math/{G3,G4,G5,G6,glossary,kangaroo,placement}/
│   ├── DB_INDEX.md  API_INDEX.md
│   └── tests/
├── frontend/
│   ├── templates/               # child.html, parent_ingest.html
│   └── static/
│       ├── css/                 # 57 files (theme.css = single source of truth)
│       └── js/                  # 83 source files + bundle-a/b/c.min.js
├── tests/                       # 14 test files (pytest)
│   ├── conftest.py
│   ├── test_ai_service.py  test_file_storage.py  test_manual_api.py
│   ├── test_streak_engine.py  test_xp_engine.py
│   └── test_math_{academy,daily,fluency,glossary,kangaroo,placement,problems}.py
├── migrations/                  # root-level migration (separate from backend/migrations)
│   └── 002_fix_learning_log_columns.py
├── handoff/                     # design + spec docs
│   ├── 01-design-system.md  02-dashboard-spec.md  02b-diary-spec.md
│   ├── 03-data-contracts.md  04-implementation-guide.md
│   ├── 05-claude-code-prompt.md  README.md  reference/
├── launcher/                    # macOS app launchers
│   ├── create-app.sh  gia-launch.sh  gia-stop.sh
├── scripts/                     # CLI utilities
│   ├── ckla_parser.py  ckla_view.py  import_ckla.py
│   ├── enrich_missing.py  enrich_mw.py
│   ├── generate_kangaroo_solutions.py  validate_kangaroo_phase1.py
│   ├── setup_daughter_mac.sh  com.gia.learning.plist
├── tools/nss_ocr/               # OCR helper tooling
├── logs/                        # runtime logs
├── data/                        # academy/, raw_json/ (parsed content)
├── English/Voca_8000/           # source vocabulary content (Lesson_01 … per-lesson assets)
├── SKILL.md                     # ⚠️ outdated — says Flask; ignore (FastAPI is canonical)
└── project_core.txt             # concatenated specs snapshot
```

---

## Backend Routers (45)

> Order in `main.py` matters — `diary_photo` must be registered **before** `diary_sentences` so literal `/photo` wins over `/{subject}/{textbook}` matching.

### Core English / Lessons
| Router | Purpose | Key endpoints |
|---|---|---|
| `lessons` | Lesson catalog, ingest from disk | GET/POST `/api/lessons/*` |
| `study` | Study items per lesson | GET `/api/study/{subject}/{textbook}/{lesson}` |
| `progress` | Stage progress, sparta reset, challenge | POST `/api/progress/{verify,challenge_complete,sparta_reset}` |
| `words` | My Words CRUD + AI enrich | POST `/api/words/lesson/{id}`, PATCH `/api/words/lesson/{id}/{word_id}` |
| `files` | Per-lesson asset storage + OCR | `/api/storage/lessons/...`, `/api/files/upload`, `/api/ocr/vocab_image` |
| `tts` | edge-tts variants | `/api/tts/{example_full,preview_sequence,word_meaning,...}` |
| `speech` | Server STT helper | POST `/api/speech/recognize` |
| `review` | SM-2 review queue | GET `/api/review/today`, POST `/api/review/{result,register-*}` |
| `daily_words` | Daily 5-word routine + weekly test | `/api/daily-words/{today,status,complete,weekly-test,...}` |
| `collocation` | Daily collocation bonus stage | GET/POST `/api/collocation/{today,submit}` |
| `tutor_sentence` | AI tutor + sentence eval + practice store | `/api/{tutor,evaluate-sentence,practice/sentence}` |
| `starred` | Star/favourite study items | PATCH `/api/study-items/{id}/star`, GET `/api/study-items/starred` |

### Diary / Free Writing / Calendar
| Router | Purpose |
|---|---|
| `diary` | Diary entry CRUD + AI title suggest |
| `diary_photo` | Photo upload (multi) for diary |
| `diary_sentences` | "My Sentences" — Step-5 sentences over time |
| `free_writing` | Free writing entries |
| `calendar_api` | Monthly calendar markers |
| `day_off` | Day-off requests (pending → email parent → approved/denied) |
| `growth_theme` | Growth Theme selection + advance |

### Home / Gamification
| Router | Purpose |
|---|---|
| `dashboard` | Home stats / analytics / textbook overview |
| `ai_coach` | Daily motivational message (Ollama → canned fallback) |
| `reminder` | Home banner reminders (review due, streak risk, etc.) |
| `xp` | XP award + summary + weekly XP |
| `arcade` | Arcade score submit + best-score |
| `rewards` | Legacy rewards (kept for back-compat) |
| `reward_shop` | Items, my-rewards, buy/use/equip, PIN |
| `schedules` | Weekly schedule CRUD |

### Parent Dashboard
| Router | Purpose |
|---|---|
| `parent` | Overview, summary, activity, task-settings, config, PIN verify |
| `parent_stats` | Overview (`today_by_subject`), summary, activity, word stats, stage stats |
| `parent_math` | Math summary |
| `parent_streak` | Streak detail + recalc + rule |
| `parent_xp` | XP rules edit/reset, XP report |
| `parent_report` | Weekly email report (preview / send / schedule) |
| `goals` | Weekly goals (PIN-gated edit) |
| `system` | Backup CRUD, ollama restart |

### Math
| Router | Purpose |
|---|---|
| `math_academy` | G3-G6 lesson flow (CPA), unit tests, learning path |
| `math_placement` | Placement test (start/check/next/save/results) |
| `math_fluency` | Fact fluency rounds (catalog/start-round/submit/summary) |
| `math_daily` | Daily challenge |
| `math_kangaroo` | Math Kangaroo sets (100+, IKMC/KSF/USA) |
| `math_glossary` | Math vocab per grade |
| `math_problems` | "My Problems" wrong-review queue |

### US Academy / CKLA
| Router | Purpose |
|---|---|
| `us_academy` | Word-first SM-2 system, sessions, mini-quiz, unit tests, passages |
| `ckla` | CKLA G3 reading curriculum (Read / Words / Q&A / Word Work) |
| `ckla_review` | CKLA review queue |

---

## Frontend Modules

### HTML
- `child.html` — main learner shell (loads ~50 CSS files + 3 bundles)
- `parent_ingest.html` — parent OCR upload UI

### JS Bundles (`build.sh` → esbuild minify, 83 source files)
- **bundle-a.min.js** — feature modules (preview, wordmatch, fillblank, spelling, sentence, home, growth-theme, parent-*, reward-shop, diary*, free-writing, calendar, daily-words, ckla*, child + child-*, sentence_ai, collocation, finaltest, unittest, review)
- **bundle-b.min.js** — math modules (depends on KaTeX CDN — manipulatives, 3read, problem-types/ui, learn-visuals/cards, academy-ui/shell/feedback/main, review, fluency, placement, daily, kangaroo*, glossary, navigation)
- **bundle-c.min.js** — word-manager + arcade (sfx, word-invaders, definition-match, spell-rush, crossword, math-invaders, sudoku, make24)

### Key JS modules (not exhaustive)
| File(s) | Purpose |
|---|---|
| `child.js` (682) + `child-{calendar,exam,keyboard,text}.js` | Main learner shell, split by concern |
| `home.js` | Home dashboard (today's tasks, AI coach, reminders) |
| `navigation.js` | Top-level navigation + sidebar routing |
| `core.js` | Shared utils, fetch wrapper, toast bridge |
| `splash.js` | Splash screen (day-of-week bg color) |
| `offline-indicator.js` | Online/offline pill |
| `tts-client.js` / `sound.js` / `arcade-sfx.js` | Audio layer |
| `analytics.js` | Local activity logging |
| `parent-{panel,overview,settings,textbooks,math,streak,xp,ingest}.js` | Parent dashboard split |
| `diary-{home,write,entry,calendar}.js` + `diary.js` | Diary section split |
| `math-academy{,-shell,-ui,-feedback}.js` | Math academy split |

### CSS files (57)
- `theme.css` — global tokens (single source of truth, 449 lines)
- Layout: `main-shell`, `main-layout`, `main-stage`, `main-topbar`, `main-idle`, `main-responsive`, `base`, `layout`, `components`, `utilities`, `legacy-app`
- Stage CSS: `preview`, `wordmatch`, `fillblank`, `spelling`, `sentence`, `finaltest`, `unittest`, `review`, `word-manager`
- Home / sub: `home`, `daily-words`, `reward-shop`, `parent`, `parent-ingest`, `splash`, `xp`, `toast`
- Diary: `diary`, `diary-home`, `diary-write`, `diary-entry`, `diary-calendar`, `diary-sub`, `calendar`
- Math: `math-home` + `math-academy-{shell,sidebar,learn,problems,stages,results,fluency,manip,daily,modes,kangaroo,glossary,content,anim,responsive}` + `math-kangaroo`, `math-learn-visuals`
- CKLA / Arcade: `ckla`, `arcade`, `collocation`

---

## Design System (theme.css — single source of truth)

**Palette B — "Pinterest Schoolgirl Diary" (2026-04, current):**

Concept: warm cream page + milk-tea pastel 6-section palette. Stationery feel (soft shadow, generous radius, Nunito/Quicksand/Caveat trio). Brand anchor = Diary Pink `#E09AAE`.

```css
:root {
  /* ═══ Section palette — 5 tones each: primary · hover · light · soft · ink ═══ */
  --english-primary: #7FA8CC; --english-hover: #6994BC;
  --english-light:   #EEF4FA; --english-soft:  #CFE0EE; --english-ink: #345A80;

  --math-primary:    #8AC4A8; --math-hover:    #73AE92;
  --math-light:      #EEF7F2; --math-soft:     #CFE6D9; --math-ink:    #3A6A54;

  --diary-primary:   #E09AAE; --diary-hover:   #CB8199;
  --diary-light:     #FBEEF2; --diary-soft:    #F3D2DC; --diary-ink:   #84425A;

  --arcade-primary:  #EEC770; --arcade-hover:  #D8AE55;
  --arcade-light:    #FBF3DE; --arcade-soft:   #F1DCA5; --arcade-ink:  #7A5A1E;

  --rewards-primary: #B8A4DC; --rewards-hover: #9F8BC5;
  --rewards-light:   #F2ECFA; --rewards-soft:  #DCCFEE; --rewards-ink: #5A4883;

  --review-primary:  #EBA98C; --review-hover:  #D69074;
  --review-light:    #FBEBE0; --review-soft:   #F4D2BE; --review-ink:  #844A30;

  /* Brand aliases */
  --color-primary:        var(--diary-primary);   /* app brand = Diary Pink */
  --color-secondary:      var(--arcade-primary);  /* XP / gamification */
  --color-accent:         var(--rewards-primary); /* shop / premium */

  /* Warm cream neutrals */
  --bg-page:    #FAF6EF;  --bg-card:    #FFFFFF;
  --bg-sidebar: #F4EEE4;  --bg-surface: #EFE8DB;

  /* Text */
  --text-primary:   #2B2722;
  --text-secondary: #706659;
  --text-hint:      #A79A89;
  --text-on-primary: #FFFFFF;

  /* Borders */
  --border-default: #DCD2C2;
  --border-strong:  #C9BDA9;
  --border-subtle:  #EBE3D5;
  --border-card:    rgba(43, 39, 34, 0.06);

  /* Shadows — soft stationery */
  --shadow-soft:        0 2px 10px rgba(120, 90, 60, 0.06);
  --shadow-modal:       0 10px 30px rgba(90, 65, 40, 0.12);
  --shadow-input-focus: 0 0 0 3px var(--color-primary-glow);

  /* Radius — generous */
  --radius-sm: 8px; --radius-md: 12px; --radius-lg: 16px;
  --radius-xl: 20px; --radius-2xl: 28px; --radius-full: 9999px;

  /* Sidebar */
  --sidebar-width: 240px;

  /* Fonts (Google Fonts must be loaded) */
  --font-family:         'Nunito', sans-serif;       /* body */
  --font-family-display: 'Quicksand', sans-serif;    /* headlines / card titles */
  --font-family-hand:    'Caveat', cursive;          /* handwritten accents */

  --font-size-xs: 12px; --font-size-sm: 14px; --font-size-md: 16px;
  --font-size-lg: 18px; --font-size-xl: 24px; --font-size-2xl: 32px; --font-size-3xl: 44px;

  /* Motion */
  --transition-fast: 0.12s ease;
  --transition-normal: 0.18s ease;
  --transition-slow: 0.3s ease;
  --ease-calm: cubic-bezier(0.25, 0.1, 0.25, 1.0);

  /* Z-index scale: sidebar 100 · topbar 200 · overlay 1000-1150 · modal 2000 · toast 5000 · splash 9999 */
}
```

**Rules**
- Component CSS: `var(--token)` only — no hex.
- Icons: Lucide (`<i data-lucide="...">`) — no emoji. JS init: `lucide.createIcons()`.
- Headlines (`.h1` ~ `.h3`): Quicksand auto-applied + `letter-spacing: -0.02em`.
- UPPERCASE labels: `letter-spacing: 0.08em`, weight 700, 10.5–11px.
- Card baseline: `bg-card + border-subtle + radius-lg + shadow-soft`.
- Splash: per-day-of-week bg colors via `--splash-day-{0..6}` tokens.

### Dark Mode (tokens ready, UI toggle not yet implemented)

`[data-theme="dark"]` block in `theme.css` provides a warm dark variant (brown base + pastel accents) for all section tones, semantic states, and shadows. Theme is preserved via `localStorage["gia-theme"]` and applied pre-DOM in `child.html` to avoid flash.

### Email HTML Palette (CSS variables 미지원 — hex 직접 사용)

| Token | hex | Use |
|---|---|---|
| `--bg-page` | `#FAF6EF` | Email body bg |
| `--bg-card` | `#FFFFFF` | Card / section box |
| `--bg-surface` | `#EFE8DB` | Quote / divider bg |
| `--bg-sidebar` | `#F4EEE4` | Sub section bg |
| `--text-primary` | `#2B2722` | Body text |
| `--text-secondary` | `#706659` | Labels |
| `--text-hint` | `#A79A89` | Captions |
| `--border-default` | `#DCD2C2` | Card borders |
| `--border-subtle` | `#EBE3D5` | Light dividers |

**Section colors (primary / light / soft / ink):**
- English: `#7FA8CC` / `#EEF4FA` / `#CFE0EE` / `#345A80`
- Math:    `#8AC4A8` / `#EEF7F2` / `#CFE6D9` / `#3A6A54`
- Diary:   `#E09AAE` / `#FBEEF2` / `#F3D2DC` / `#84425A`
- Arcade:  `#EEC770` / `#FBF3DE` / `#F1DCA5` / `#7A5A1E`
- Rewards: `#B8A4DC` / `#F2ECFA` / `#DCCFEE` / `#5A4883`
- Review:  `#EBA98C` / `#FBEBE0` / `#F4D2BE` / `#844A30`

**Email guide:** soft shadow `0 2px 8px rgba(120,90,60,0.08)`, border `1px solid #DCD2C2 / radius 16px`, left 4px section bar instead of icons, max width 600px, font `-apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif`. No emoji.

---

## Learning Flow (English)

```
Home Dashboard → English → Lesson Select
→ Preview (Step 1) → Word Match (Step 2) → Fill Blank (Step 3)
→ Spelling (Step 4) → Make Sentence (Step 5) → Final Test → Complete
```

### Step Specs

**Step 1 — Preview**
4×5 card grid → click → popup modal. Flow: POS pill → Word (32px 700) → Definition → Example (italic) → Listen (TTS) → Shadow ×2 (mic, Web Speech API, ≥80%) → Spell ×2 → Sentence Reading ×2 (TTS → mic ≥90%).

**Step 2 — Word Match**
7 words / round, two columns. word ↔ definition matching.
Selected `--color-primary` border+bg / Matched `--color-success` opacity 0.6 / Wrong shake 0.3s.

**Step 3 — Fill the Blank**
Sentence + word-tag pills → pick correct word.
Correct `--color-success` / Wrong `--color-error` + shake.

**Step 4 — Spelling Master**
Wordle-style 48×48 boxes. 3 passes (hint → first letter → blank). Wrong → retryQueue (clear all before progressing).

**Step 5 — Make a Sentence**
Stage 1 drag-and-drop word scramble. Stage 2 free writing → AI grade (grammar+spelling, Ollama → Gemini fallback).

**Final Test (Perfect Challenge)**
MC 20 + Fill-in 20. 30-min timer. Pass = 90%. Pass → XP +10 + GrowthEvent("lesson_pass"). Fail → re-learn required. Retry pass = +10. Implementation: `child-exam.js` (extracted from `child.js`).

---

## XP Rules (`services/xp_engine.py XP_RULES_DEFAULT`)

> Parent can override any rule via `app_config` key `xp_rule_<action>`. Defaults below.

| Action | XP | Limit |
|---|---:|---|
| `word_correct` | +1 | per attempt |
| `stage_complete` | +2 | once / stage / lesson |
| `final_test_pass` | +10 | once; retry pass = +10 |
| `unit_test_pass` | +5 | once |
| `daily_words_complete` | +5 | once / day |
| `weekly_test_pass` | +10 | once / week |
| `mywords_weekly_test_pass` | +10 | once / week |
| `review_complete` | +2 | once / day |
| `journal_complete` | +10 | once / day |
| `must_do_bonus` | +5 | once / day (all must-do done) |
| `all_complete_bonus` | +15 | once / day (all tasks done) |
| `streak_7_bonus` | +30 | per occurrence |
| `streak_30_bonus` | +200 | per occurrence |
| `math_lesson_complete` | +10 | per lesson |
| `math_unit_test_pass` | +25 | per unit test pass |
| `math_kangaroo_complete` | +5 | per set |
| `math_kangaroo_80` | +5 | per set ≥80% |
| `math_kangaroo_perfect` | +10 | per set 100% |
| `ckla_reading_done` | +2 | per lesson (dedup by lesson_id) |
| `ckla_vocab_done` | +3 | per lesson |
| `ckla_lesson_complete` | +5 | per lesson |
| Arcade round | +1/+2/+3 | thresholds 500/1000/2000 score; daily cap = `arcade_daily_cap` (default 10) |

Failed tests / re-learn after fail: 0 XP.

---

## Streak Rules (`services/streak_engine.py`)

- Tracks **3 subjects**: `english` / `math` / `game`. (Configurable via `app_config` keys `streak_subjects`, `streak_mode`.)
- Mode `all` (default): every selected subject must show activity that day. Mode `any`: at least one suffices.
- Approved Day-Off freezes streak (maintains count).
- 7-day / 30-day milestones trigger XP bonuses (+30 / +200).

---

## Diary Sections

| Section | Description | File(s) |
|---|---|---|
| Today | Dashboard (4 stats + week calendar + milestones) | `diary-home.js` |
| Daily Journal | Writing + AI feedback (2-column) | `diary-write.js` |
| Free Writing | Free-form journaling | `free-writing.js` |
| My Sentences | Step-5 sentence collection; 2-week-old → Rewrite prompt | `diary-sentences` router |
| My Worlds | Completed Growth Theme collection | `growth-theme.js` |
| Growth Timeline | GrowthEvent log (reverse chrono) | in `diary-home.js` |
| Calendar | Monthly view (streak / day-off / journal markers) | `diary-calendar.js` |
| Day Off | Reason form → email parent → pending/approved/denied | `day_off` router |
| Photo | Multi-photo upload bound to entries | `diary_photo` router |

---

## Reward Shop

Default items: YouTube 30min (300), Roblox 30min (300), Family Movie (500), Dinner Out (500), Custom Reward (300).

- **Buy**: card click → confirm → XP debit → `PurchasedReward` row.
- **Use**: My Rewards → [Use] → 4-digit PIN → `is_used=True`.
- PIN flow: `/api/shop/{set-pin,pin-status}` + `/api/shop/use-reward/{purchase_id}`.
- Files: `reward-shop.js` + `reward-shop-use.js` + `reward-shop.css`.

---

## Parent Dashboard

Access: Home banner "···" → 4-digit PIN (`services/pin_guard.py`).

**Layout**: `#pp-body` is centered with `max-width: 1080px` and `padding: 24px 32px`. The body uses a `.pp-grid-2` utility (1fr 1fr, collapses to 1-col under 720px) for two-column rows. All emoji icons have been replaced with Lucide.

**6-tab structure** (redesigned 2026-04-29 → 30) — `parent-panel.js` shell routes to one renderer per tab:

| Tab | Renderer | Content |
|---|---|---|
| **Home** | `parent-overview.js _ppHome` | Hero (status icon + 3 stats, color-coded green/amber/red) → Week Calendar (7 cells) → 2-col row: Today's Progress (per-subject XP from `today_by_subject`) \| vs Last Week (words/XP/days with ↑↓→ trends) → Alerts (pending day-offs, streak-at-risk, **goals lagging** when Thu-Sun & active goal pct < 50%). |
| **English** | `parent-panel.js _ppEnglish` | Top 3-stat summary (Tracked Words / Overall Accuracy / Stage Completions) → 2-col: Most Missed Words (sticky-header table-wrap) \| Stage Performance (Lucide icon per stage + accuracy chip green/amber/red). |
| **Math** | `parent-math.js _ppMathSummary` | 4-stat grid → 2-col: Weak Concepts (humanized lesson names) \| Fact Fluency (Phase pill + accuracy chip) → Daily Challenge bar chart (7d) → Kangaroo Sets table. Lucide section-title icons throughout (`calculator`/`alert-triangle`/`zap`/`calendar-days`/`award`). |
| **Habits** | `parent-panel.js _ppHabits` | Streak detail (`parent-streak.js`: 3 stat cards + Streak Rule editor + Last 30 Days grid 15-col on desktop) + Day-Off approvals. Subjects render with Lucide (`book-open`/`calculator`/`gamepad-2`); calendar cells use `flame`/`umbrella`/`x`. |
| **Goals** | `parent-goals.js _ppGoals` | Summary banner + 2x2 progress card grid + inline Edit Targets form (PIN-gated PUT). |
| **Settings** | `parent-panel.js _ppSettings` | 4 sections: Task Settings (full, 2-col task list) → 2-col row: Academy Schedule \| Account (PIN + parent email) → Weekly Report (`parent-report.js` — enable toggle, day-of-week select, child-name, Save Schedule / Send Now / Preview Data; gracefully degraded when PIN not yet verified) → Textbooks (`parent-textbooks.js` accordion + Add Textbook entry point linking to `/ingest`). |

**Backend feed** (key endpoints):
- `/api/parent/overview` returns `today_by_subject: {english,math,diary}→{xp,count}` (XPLog action prefix → subject) plus `recent_logs[].subject` and the original totals. Used by Home.
- `/api/parent/summary`, `/api/parent/activity?days=14`, `/api/parent/word-stats`, `/api/parent/stage-stats`, `/api/parent/math-summary`, `/api/parent/streak`, `/api/parent/day-off-requests`, `/api/goals/weekly` — see `API_INDEX.md`.
- `/api/parent/report/{schedule,send,preview}` — Weekly Report (PIN-gated).

**Removed standalone tabs** (functionality merged into the 6 above): Overview/Activity/Word-stats/Stage-stats/Streak/XP/Day-off/Tasks/Schedule/Pin/Textbooks — all consolidated.

Auxiliary modules still bundled but not direct tabs:
- `parent-xp.js` — XP rules edit (separate flow; can be invoked from Settings when surfaced).
- `parent-textbooks.js` + `parent-ingest.js` — embedded inside Settings; Add Textbook still uses the standalone `/ingest` UI in a new tab.

**CSS keys added for the redesign** (in `frontend/static/css/parent.css`):
- Layout: `.pp-grid-2`
- Home: `.pp-hero` (+ `--green/amber/red`, `-head`, `-icon`, `-msg`, `-stats`, `-stat`, `-num`, `-label`), `.pp-today-list/-row/-subject/-badge` (+ `--active/done/none/sub`), `.pp-week-grid/-cell/-day/-dot/-xp` (+ `--active`), `.pp-compare-grid/-row/-label/-val`, `.pp-trend` (+ `--up/down/same`), `.pp-alert-list/-alert` (+ `--warn/info`).
- Goals: `.pp-goals-summary/-grid/-edit-box/-edit-row`, `.pp-goal-card/-header/-label/-val/-track/-fill/-footer/-pct/-achieved` (+ `--done`).
- English/Math shared: `.pp-stage-list/-head/-acc` (+ `--good/ok/low`), `.pp-table-wrap` (sticky header), `.pp-section-title--icon`, `.pp-phase-pill`.
- Settings: `.pp-form-row`, `.pp-toggle-row`, `.pp-rep-preview`.

Cache busters in `child.html`: `parent.css?v=12`, `bundle-a.min.js?v=9` (bump on every parent-* / CSS change so service worker re-fetches).

---

## Math Module

### Math Academy
- **Grades**: G3, G4, G5, G6 (data in `backend/data/math/G{3..6}/`)
- **Approach**: CPA (Concrete → Pictorial → Abstract)
- **Learning Path view** (added 2026-04, commit `62be6da`): unit/lesson tree
- **Visual error states** (commit `9b743ca`): no more blank cream screen on failure
- Routers: `math_academy`, `math_daily`, `math_fluency`, `math_glossary`, `math_placement`, `math_problems`
- JS: `math-academy.js` + `math-academy-{shell,ui,feedback}.js` + `math-manipulatives{,-2}.js` + `math-3read.js` + `math-learn-{cards,visuals}.js` + `math-problem-{types,ui}.js` + `math-katex-utils.js`

### Math Kangaroo
- 103 sets in `backend/data/math/kangaroo/`: IKMC 2012-2023, KSF (Lebanon, India), USA 2003-2025
- Levels: Pre-Ecolier (1-2), Ecolier (3-4), Benjamin (5-6), Cadet, Junior, Student
- Modes: Practice (instant grade) / Test (timer + final grade)
- XP: complete +5, ≥80% +5, perfect +10
- Files: `math-kangaroo.js`, `-exam.js`, `-pdf-exam.js`, `-result.js`

### Other Math
- **Placement** (`math_placement`) — adaptive level finder
- **Daily Challenge** (`math_daily`)
- **Fluency** (`math_fluency`) — fact rounds with daily cap
- **Glossary** (`math_glossary`) — per-grade vocab
- **My Problems** (`math_problems`) — wrong-answer review queue

---

## Arcade

| Game | File |
|---|---|
| Word Invaders | `arcade-word-invaders.js` |
| Spell Rush | `arcade-spell-rush.js` |
| Definition Match | `arcade-definition-match.js` |
| Crossword | `arcade-crossword.js` |
| Sudoku | `arcade-sudoku.js` |
| Make 24 | `arcade-make24.js` |
| Math Invaders | `arcade-math-invaders.js` |

Hub UI is calm (`bg-page` + cards only). Energy/SFX (`arcade-sfx.js`) only inside games. Daily XP cap configurable.

---

## US Academy (word-first SM-2)

New module for US-school vocab prep.
- Models: `USAcademyWord`, `USAcademyWordProgress`, `USAcademyPassage`, `USAcademySession`, `USAcademyUnitResult`
- Flow: level select → word study (definition / example / synonym / etymology) → mini quiz → unit test → SM-2 review queue
- Endpoints: `/api/us-academy/{words,session,step/complete,quiz/result,review/{due,result},passage/{id},stats}`
- Migration: `010_us_academy_tables.py`

---

## CKLA Academy (Grade 3 reading)

- **Tabs**: Read / Words / Q&A / Word Work
- Article rendering: `_parsePassage()` handles PDF line-break artefacts → prose
- Models: `CKLADomain`, `CKLALesson`, `CKLAQuestion`, `CKLAWordLesson`, `CKLALessonProgress`, `CKLAQuestionResponse`
- Routers: `ckla`, `ckla_review`
- Service: `services/ckla_grader.py`
- Frontend: `ckla.js`, `ckla-lesson.js`, `ckla-review.js`, `ckla.css`
- Migration: `011_ckla_tables.py`

---

## AI Coach (Home dashboard)

`routers/ai_coach.py` provides `GET /api/ai-coach/today` — daily motivational message.
- Builds prompt from XP totals + streak with **prompt-injection defence** (stats wrapped in `[STATS]` block prefixed with ignore instruction).
- Tries Ollama (`gemma2:2b` at `127.0.0.1:11434`) → falls back to canned messages on failure.

> ⚠️ Note: previous CLAUDE.md mentioned an "AI Assistant (Shadow)" panel with `ai-assistant-stt.js` / `-tts.js` / `ai_assistant_*.py`. Those files **do not currently exist** in the codebase. The Home AI Coach is the only AI-driven coaching surface today. Speech (mic) is handled per-stage via Web Speech API directly.

---

## System Services

| Feature | File | Status |
|---|---|---|
| Ollama lazy-start (auto-launch on first AI call) | `services/ollama_manager.py` | ✅ |
| Auto-backup (rolling, 7-day) | `services/backup_engine.py` | ✅ |
| Folder watcher (auto-ingest dropped images) | `backend/folder_watcher.py` | ✅ |
| Voca disk sync | `backend/voca_sync.py` | ✅ |
| Offline indicator | `offline-indicator.js` | ✅ |
| Service worker / PWA | `static/service-worker.js` + `manifest.json` | ✅ |
| Splash screen (per-day-of-week colors) | `splash.js` + `splash.css` | ✅ |
| JS bundle auto-rebuild on startup | `build.sh` (run from `lifespan`) | ✅ |
| Dark mode toggle UI | tokens ready, no UI control | 🟡 |
| macOS LaunchAgent | see `README.md` | ✅ |

---

## Database Models (`backend/models/`)

> Full schema reference: `backend/DB_INDEX.md`

### `lessons.py`
`Lesson`, `StudyItem`, `Progress`, `UserPracticeSentence`, `Word`, `WordReview`

### `system.py`
`Reward` (legacy), `Schedule`, `AppConfig`

### `gamification.py`
`XPLog`, `StreakLog`, `TaskSetting`, `RewardItem`, `PurchasedReward`, `GrowthThemeProgress`

### `learning.py`
`DailyWordsProgress`, `AcademySession`, `LearningLog`, `WordAttempt`, `AcademySchedule`

### `diary.py`
`DiaryEntry`, `FreeWriting`, `GrowthEvent`, `DayOffRequest`

### `math.py`
`MathPlacementResult`, `MathProblem`, `MathProgress`, `MathAttempt`, `MathWrongReview`, `MathFactFluency`, `MathDailyChallenge`, `MathKangarooProgress`

### `assistant.py`
`AssistantLog`

### `us_academy.py`
`USAcademyWord`, `USAcademyWordProgress`, `USAcademyPassage`, `USAcademySession`, `USAcademyUnitResult`

### `ckla.py`
`CKLADomain`, `CKLALesson`, `CKLAQuestion`, `CKLAWordLesson`, `CKLALessonProgress`, `CKLAQuestionResponse`

### `goals.py`
`WeeklyGoal`

### Migrations (`backend/migrations/`)
001 base · 002 shop columns · 003 math tables · 004 review_source · 005 practice_sentence created_at · 006 academy_session active · 007 free_writings · 008 streak 3-subjects · 009 kangaroo columns · 010 us_academy · 011 ckla · 012 kangaroo rename set_ids · 013 diary_entry columns · 014 report schedule · 015 study_item starred · 016 weekly goals · 017 math_progress UNIQUE(grade,unit,lesson).

---

## Code Annotation Rules

### File header (all JS / CSS / Python files)

```
/* ================================================================
   [filename] — [one-line description]
   Section: [Home / English / Math / Diary / Arcade / Shop / Parent /
             Academy / CKLA / System]
   Dependencies: [list]
   API endpoints: [list or "none"]
   ================================================================ */
```

### Function tag

```js
/** @tag XP @tag AWARD */
async function awardXP(action, detail) { ... }
```

### Available `@tag` values

```
HOME_DASHBOARD  TODAY_TASKS    REMINDER     AI_COACH
SIDEBAR         ACCORDION      NAVIGATION   PAGES
ENGLISH         ACADEMY        DAILY_WORDS  MY_WORDS       READING
CKLA            COLLOCATION    US_ACADEMY   STARRED
PREVIEW         SHADOW         SENTENCE_READ  SPELL
WORD_MATCH      FILL_BLANK     SPELLING     SENTENCE
FINAL_TEST      UNIT_TEST      WEEKLY_TEST
REVIEW          SM2            ACTIVE_RECALL
DIARY           JOURNAL        FREE_WRITING MY_SENTENCES   PHOTO
MY_WORLDS       GROWTH_TIMELINE  GROWTH_THEME  CALENDAR    DAY_OFF
MATH            MATH_ACADEMY   MATH_DAILY   MATH_FLUENCY
MATH_KANGAROO   MATH_GLOSSARY  MATH_PLACEMENT  MATH_PROBLEMS
ARCADE
XP              STREAK         AWARD        BONUS
SHOP            REWARD         PURCHASE     PIN
PARENT          SETTINGS       WORD_STATS   SCHEDULE       NOTIFICATION
GOALS           REPORT
TTS             AI             OLLAMA       GEMINI         OCR
BACKUP          SYSTEM         THEME        BUILD
```
# CLAUDE.md — Island System Section
> Add this entire section to the existing CLAUDE.md file
> Insert after the existing system sections (after Math/English/Diary sections)

---

## 🏝️ ISLAND SYSTEM (Gia's Island)

### Overview
Tamagotchi + island-building + Pokémon collection hybrid. Replaces the legacy Growth Theme system entirely. Three pillars: **Raising** (central) + **Decorating** + **Collecting**.

**Full spec:** See `ISLAND_SPEC.md` for complete details.

---

### Key Rules for Claude Code

1. **Language:** All UI text, notifications, and messages in **English only**
2. **No growth_theme references** — completely removed, replaced by island system
3. **No 조개 (shell/clam) references** — replaced by Lumi currency
4. **Config-first design** — all animation values, thresholds, UI text in config files
5. **Performance:** decay and lumi production run as batch on app open, never background scheduler
6. **Single-user app** — island_currency always id=1 (upsert pattern)

---

### Currency System

| Currency | Earn | Spend |
|---------|------|-------|
| XP | Study | Real rewards (Reward Shop - existing) |
| Lumi 💎 | Study + streak + completed char production | Evolution stones, food, decorations, exchange |
| Legend Lumi ✨ | 100 Lumi = 1 Legend Lumi | Legend zone items only |

**Lumi cannot go negative** → disable purchase buttons when insufficient.

---

### Zone Structure

```
        🚀 Space
   🌳 Forest  ✨Legend  🌊 Ocean
        🦁 Savanna
```

| Zone | Subject | Characters (5 each) |
|------|---------|---------------------|
| Forest | English | Sprout, Clover, Mossy, Fernlie, Blossie |
| Ocean | Math | Axie, Finn, Delphi, Bubbles, Starla |
| Savanna | Diary | Mane, Ellie, Leo, Zuri, Rhino |
| Space | Review | Lumie, Twinkle, Orbee, Nova, Cosmo |
| Legend | All | Dragon, Unicorn, Phoenix, Gumiho, Qilin |

**Zone unlock chain:** Zone 1 (chosen at onboarding) → complete 1 char → Zone 2 → ... → all 4 zones each have 1 first-evolution → Legend Zone.

---

### Character Growth

```
baby (Lv1~5) → [1st Evo Stone A or B] → mid_a or mid_b (Lv6~10) → [2nd Evo Stone] → final_a or final_b
```

**Level XP:** 100 / 150 / 200 / 300 (baby) | 100 / 150 / 200 / 300 / 400 (mid)
**Target:** ~3~4 weeks per character completion

**XP multiplier by gauge:**
- Normal (both 60+): 100%
- One below 60: 80%
- One below 20: 60%
- Both below 20: 20%
- Evolution blocked if any gauge < 20

---

### Care System

- **Hunger decay:** -15 every midnight
- **Happiness decay:** -20 if no study 2 consecutive days
- **Completed characters:** No gauge needed — permanent residents
- **Legend characters:** No hunger/happiness — uses consecutive_days instead

---

### Legend Characters

- Unlock condition: 4 zones each have 1 character with 1st evolution complete
- Evolution: 14 consecutive days + Legend Stone (1st) → 30 consecutive days + Legend Stone (2nd)
- Streak breaks → reset to 0 + character sad animation + happiness -10
- 4 subjects all completed in one day = +1 legend gauge

---

### Database (10 New Tables — migration 018)

New tables:
1. `island_characters` — catalog (30 chars)
2. `island_character_progress` — Gia's raising progress
3. `island_care_log` — gauge history (30-day auto-delete)
4. `island_shop_items` — shop catalog (55 items)
5. `island_inventory` — owned items
6. `island_placed_items` — placed decorations
7. `island_currency` — lumi balance (id=1 always)
8. `island_lumi_log` — transactions (90-day auto-delete)
9. `island_legend_progress` — legend streak tracking
10. `island_zone_status` — unlock status (5 rows)

**Tables DELETED in migration 018:** `rewards`, `schedules`, `growth_theme_progress`

---

### New Backend Files

| File | Purpose |
|------|---------|
| `routers/island.py` | All island API (34 endpoints) |
| `services/lumi_engine.py` | Lumi earn/spend/exchange |
| `services/island_care_engine.py` | Decay + gauge logic |
| `services/island_production_engine.py` | Daily lumi batch |
| `services/island_service.py` | Evolution branch validation |

### Modified Files

| File | Change |
|------|--------|
| `services/xp_engine.py` | Add lumi award on study complete |
| `services/streak_engine.py` | Add streak lumi award |
| `backend/main.py` | App start: decay + lumi production batch |
| `routers/diary.py` | Diary complete → island_care_engine |
| `routers/study.py` | English complete → island_care_engine |
| `routers/math_academy.py` | Math complete → island_care_engine |
| `routers/review.py` | Review complete → island_care_engine |
| `frontend/static/js/reward-shop.js` | Add Island tabs |
| `frontend/static/js/parent-panel.js` | Remove growth_theme, add island toggle |

### Deleted Files

| File | Reason |
|------|--------|
| `routers/growth_theme.py` | Replaced by island |
| `models/gamification.py` (growth_theme parts) | Removed |

---

### Frontend Config Files

- `frontend/src/config/animations.config.js` — All animation timings (edit here, not in components)
- `frontend/src/config/island.config.js` — Zone config, UI text, error messages, thresholds

---

### Shop Integration

Reward Shop now has 5 tabs: **Rewards** (XP) | **Evolution** (Lumi) | **Food** (Lumi) | **Decor** (Lumi) | **Exchange**

---

### Phase 2 (Do Not Implement Now)

Parent Dashboard Island widget, BGM, AI chat (Ollama), Arcade integration, Character accessories

---

### Entry Point

Home screen → Right column → OceanWorldCard replaced with Island card → Island main screen

---

### app_config Keys

```
island_initialized, lumi_exchange_rate, lumi_rule_*, lumi_boost_*, island_on
```
(Full list in ISLAND_SPEC.md Section 11.3)
