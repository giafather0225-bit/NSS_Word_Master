# GIA Learning App — Project Spec (CLAUDE.md)
> Last updated: 2026-05-16 — Growth Theme 시스템 완전 제거 · 마이그레이션 001~056 반영 · 라우터 46개 · JS 93개 · CSS 63개 · Island 시스템 서비스/프론트엔드 추가

## Overview
- **Product**: 9세 여아(Gia)를 위한 AI-driven learning app — CKLA G3 (메인 영어 학습), DUX English (보조), Math Academy, Diary, Arcade
- **GitHub**: https://github.com/giafather0225-bit/NSS_Word_Master
- **Working directory**: `/Users/markjhlee/Documents/GitHub/NSS_Word_Master`
- **DB**: `~/NSS_Learning/database/voca.db` (SQLite WAL)
- **Server**: `python3 app.py` → http://localhost:8000 (uvicorn `backend.main:app`)
- **Entry HTML**: `/`, `/child` → `child.html` · `/ingest` → `parent_ingest.html`

---

## Tech Stack
- **Backend**: Python / FastAPI — `backend/main.py` mounts **46 routers** (`backend/routers/`, ~204 endpoints).
- **Frontend**: HTML + CSS + Vanilla JS (no framework). 93 JS source + 63 CSS files. Pre-built into `bundle-{a,b,c}.min.js` via `build.sh` (esbuild). Auto-rebuilt at server startup. Island UI uses JSX React components (`frontend/src/island/*.jsx`, 17 files — built separately, not bundled with esbuild).
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
2. 파일당 최대 ~500줄. 초과 시 모듈 분리 (예: `child.js` → `child-{calendar,exam,keyboard,text}.js`).
3. CSS: `theme.css` 변수만 사용. 컴포넌트 CSS에 hex 직접 사용 금지.
4. 모든 API: 적절한 에러 핸들링 + HTTP 상태코드. `RequestValidationError` 는 `main.py` 에서 child-friendly 422 JSON 으로 자동 변환됨.
5. DB 스키마 변경: `backend/migrations/`에 idempotent 마이그레이션 추가 (현재 001~056, 중복 prefix 파일 5쌍 있음 — filename으로 추적하므로 안전).
6. Python: type hints + docstrings. JS: JSDoc `@tag` comments.
7. async/await 일관성. N+1 쿼리 금지.
8. 모든 사용자 입력 sanitize. SQL injection / XSS / prompt injection 방어. Pydantic 길이 제한 = `schemas_common.py` (Str80/Str200/Str500).
9. JS 변경 후 `build.sh` 가 lifespan startup 시 자동 재빌드. 수동 빌드: `bash build.sh`.
   → 테스트 전에 항상 `bash build.sh`를 수동 실행하여 bundle-a/b/c.min.js를 재생성할 것.
10. 변경 후 스모크 테스트: 5-Stage 학습 / Review / Final Test / Unit Test / Word Manager / Diary / Math Academy.
11. UI 텍스트: 영어만. 이모지 금지 — Lucide 아이콘 (`<i data-lucide="...">`) + JS 에서 `lucide.createIcons()`.
    → Confirmed fixes applied 2026-04-30: spelling.js / sentence.js / fillblank.js 이모지 전체 제거, sentence.js 한국어 로딩 텍스트 영문화, fillblank.js retry 카운터 UX 개선.
12. class/ID 변경 시 모든 참조 동시 업데이트 (3 bundles 모두 영향).
13. 응답 마지막에 수정된 파일 목록 기재.
14. DUX freeze 해제 (2026-05-14). 기존 "절대 수정 금지" 정책은 폐지됨.
    아래 DUX 학습 플로우 파일들도 이제 수정 가능 — 단 규칙 #1(수정 전 기존 코드
    읽기, 기존 기능 파괴 금지) + #10(스모크 테스트)를 반드시 준수:
    `routers/lessons.py`, `routers/study.py`, `routers/finaltest.py`,
    `routers/unittest.py`, `routers/daily_words.py`, `routers/collocation.py`,
    `static/js/child.js`, `static/js/navigation.js`, `static/js/preview.js`,
    `static/js/wordmatch.js`, `static/js/fillblank.js`, `static/js/spelling.js`,
    `static/js/sentence.js`, `static/js/finaltest.js`, `static/js/unittest.js`,
    `static/js/home.js`
    → `routers/review.py`는 범용 SM-2 인프라 (영어+CKLA 공용).
15. CKLA는 DUX와 분리된 독립 모듈이다. 모듈 경계를 존중하되, 공용
    인프라(`review.py` 등) 수정은 양쪽 영향도를 함께 검토한다.

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
│   │   ├── us_academy.py  ckla.py  goals.py  island.py
│   ├── services/                # 13 engines / managers
│   │   ├── xp_engine.py         # XP rules + award (config-overridable)
│   │   ├── streak_engine.py     # 3-subject streak (ckla/math/game)
│   │   ├── academy_session.py   # active session tracking
│   │   ├── daily_words_engine.py
│   │   ├── ckla_grader.py
│   │   ├── report_engine.py     # parent weekly report
│   │   ├── report_engine_html.py # HTML email rendering
│   │   ├── math_diagnostic.py   # Math placement diagnostics
│   │   ├── lumi_engine.py       # Island Lumi earn/spend/exchange
│   │   ├── island_care_engine.py # Island gauge decay + care logic
│   │   ├── island_production_engine.py # Daily lumi batch (completed chars)
│   │   ├── island_service.py    # Evolution branch validation
│   │   ├── email_sender.py
│   │   ├── pin_guard.py / pin_hash.py
│   │   ├── ollama_manager.py    # auto-start, healthcheck
│   │   └── backup_engine.py     # auto-snapshot (7-day rolling)
│   ├── routers/                 # 46 FastAPI routers (see table below)
│   ├── migrations/              # 056_word_reviews_easiness_real.py latest
│   ├── data/                    # static content (math/, daily_words/)
│   │   └── math/{G3,G4,G5,G6,glossary,kangaroo,placement}/
│   ├── DB_INDEX.md  API_INDEX.md
│   └── tests/
├── frontend/
│   ├── templates/               # child.html, parent_ingest.html
│   └── static/
│       ├── css/                 # 63 files (theme.css = single source of truth)
│       └── js/                  # 93 source files + bundle-a/b/c.min.js
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
│   ├── check_decor_assets.py    # Island decor PNG coverage report
│   ├── verify_ckla_data.py      # CKLA G3 data verification (Authority + Kid Fitness scores)
│   ├── setup_daughter_mac.sh  com.gia.learning.plist
├── tools/nss_ocr/               # OCR helper tooling
├── logs/                        # runtime logs
├── data/                        # academy/, raw_json/ (parsed content)
├── English/Voca_8000/           # source vocabulary content (Lesson_01 … per-lesson assets)
└── project_core.txt             # concatenated specs snapshot
```

---

## Backend Routers (46)

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

### CKLA / Island
| Router | Purpose |
|---|---|
| `ckla` | CKLA G3 reading curriculum (Read / Words / Q&A / Word Work) |
| `parent_ckla` | Parent dashboard CKLA stats (progress, Q&A accuracy, weekly graph) |
| `island` | Island system — characters, care, shop, decorate, currency, evolution (41 endpoints) |

---

## Frontend Modules

### HTML
- `child.html` — main learner shell (loads ~50 CSS files + 3 bundles)
- `parent_ingest.html` — parent OCR upload UI

### JS Bundles (`build.sh` → esbuild minify, 93 source files)
- **bundle-a.min.js** — feature modules (preview, wordmatch, fillblank, spelling, sentence, home, parent-*, reward-shop*, island-result, diary*, free-writing, calendar, daily-words*, ckla*, child + child-*, sentence_ai, collocation, finaltest, unittest, review, review-hub, math-spaced-review) + Island JSX components (17 files via Babel/React)
- **bundle-b.min.js** — math modules (depends on KaTeX CDN — katex-utils, manipulatives×2, 3read, problem-types/ui, learn-visuals/cards, academy-ui/shell/feedback/submit/main, lesson-complete, unit-test, problems-ui, fluency, placement*, daily, kangaroo*, glossary, navigation, math-review)
- **bundle-c.min.js** — word-manager + arcade (sfx, word-invaders, definition-match, spell-rush, crossword, math-invaders, sudoku, make24, word-builder, memory-match)

### Key JS modules (not exhaustive)
| File(s) | Purpose |
|---|---|
| `child.js` + `child-{calendar,exam,keyboard,text}.js` | Main learner shell, split by concern |
| `home.js` | Home dashboard (today's tasks, AI coach, reminders) |
| `navigation.js` | Top-level navigation + sidebar routing |
| `core.js` | Shared utils, fetch wrapper, toast bridge |
| `splash.js` | Splash screen (day-of-week bg color) |
| `offline-indicator.js` | Online/offline pill |
| `tts-client.js` / `sound.js` / `arcade-sfx.js` | Audio layer |
| `analytics.js` | Local activity logging |
| `parent-{panel,overview,settings,textbooks,math,streak,xp,ingest,goals,island}.js` | Parent dashboard split |
| `diary-{home,write,entry,calendar}.js` + `diary.js` | Diary section split |
| `math-academy{,-shell,-ui,-feedback,-submit}.js` + `math-review.js` | Math academy split |
| `daily-words.js` + `daily-words-weekly.js` | Daily words + weekly test |
| `ckla.js` + `ckla-{lesson,spelling,review}.js` | CKLA curriculum split |
| `math-spaced-review.js` | Math SM-2 review queue |
| `island-result.js` | Island XP+lumi gain card (shown on study result screens) |
| `reward-shop-island.js` | Island shop tab (Evolution/Food/Decor/Exchange) |

### CSS files (63)
- `theme.css` — global tokens (single source of truth)
- Layout: `main-shell`, `main-layout`, `main-stage`, `main-topbar`, `main-idle`, `main-responsive`, `base`, `layout`, `components`, `utilities`, `legacy-app`
- Stage CSS: `preview`, `wordmatch`, `fillblank`, `spelling`, `sentence`, `finaltest`, `unittest`, `review`, `review-hub`, `word-manager`
- Home / sub: `home`, `daily-words`, `reward-shop`, `parent`, `parent-ingest`, `splash`, `xp`, `toast`
- Diary: `diary`, `diary-home`, `diary-write`, `diary-entry`, `diary-calendar`, `diary-sub`, `calendar`
- Math: `math-home` + `math-academy-{shell,sidebar,learn,problems,stages,results,fluency,manip,daily,modes,kangaroo,glossary,content,anim,responsive}` + `math-kangaroo`, `math-learn-visuals`
- CKLA / Arcade: `ckla`, `arcade`, `collocation`
- Island: `island-loop`, `island-main`, `island-meta`, `island-screens`, `island-system`, `island-zones`

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
Wordle-style 48×48 boxes. 3 passes:
  Pass 1: vowels hidden (e.g. "wound" → "w_ _nd")
  Pass 2: first + last letter only (e.g. "wound" → "w___d")
  Pass 3: all hidden — full recall from memory
Wrong → retryQueue (all retries must clear before advancing to next stage).
No emoji in UI — use plain text or Lucide icons only.
Listen button uses `<i data-lucide="volume-2">` icon.

**Step 5 — Make a Sentence**
Stage 1 drag-and-drop word scramble. Stage 2 free writing → AI grade (grammar+spelling, Ollama → Gemini fallback).

**Final Test**
MC 20 + Fill-in 20. 30-min timer. Pass = 90%. Pass → XP +10 + GrowthEvent("lesson_pass"). Fail → re-learn required. Retry pass = +10. Implementation: `finaltest.js` (standalone overlay controller; the legacy `child-exam.js` Perfect Challenge flow was removed 2026-05-15).

---

## XP Rules (`services/xp_engine.py XP_RULES_DEFAULT`)

> Parent can override any rule via `app_config` key `xp_rule_<action>`. Defaults below.

| Action | XP | Limit |
|---|---:|---|
| `word_correct` | +1 | per attempt |
| `stage_complete` | +5 | once / stage / lesson |
| `final_test_pass` | +20 | once; retry pass = +20 |
| `unit_test_pass` | +5 | once |
| `daily_words_complete` | +10 | once / day |
| `weekly_test_pass` | +10 | once / week |
| `mywords_weekly_test_pass` | +10 | once / week |
| `review_complete` | +5 | once / day |
| `journal_complete` | +15 | once / day |
| `must_do_bonus` | +10 | once / day (all must-do done) |
| `all_complete_bonus` | +25 | once / day (all tasks done) |
| `streak_7_bonus` | +30 | per occurrence |
| `streak_30_bonus` | +200 | per occurrence |
| `streak_maintain` | +10 | once / day (streak kept) |
| `math_lesson_complete` | +15 | per lesson |
| `math_unit_test_pass` | +15 | once per unit (MATH_SPEC.md authoritative) |
| `math_kangaroo_complete` | +5 | per set |
| `math_kangaroo_80` | +5 | per set ≥80% |
| `math_kangaroo_perfect` | +10 | per set 100% |
| `ckla_lesson_complete` | +15 | 레슨 4탭 전부 완료 (첫 완료만) |
| `ckla_domain_test_pass` | +30 | Domain Test 80% 통과 |
| `ckla_grade_final_pass` | +100 | Grade Final Test 80% 통과 |
| `ckla_daily_goal` | +10 | 오늘 목표 레슨 수 달성 |
| Arcade round | +1/+2/+3 | thresholds 500/1000/2000 score; daily cap = `arcade_daily_cap` (default 10) |

Failed tests / re-learn after fail: 0 XP.

---

## Streak Rules (`services/streak_engine.py`)

- Tracks **3 subjects**: `ckla` / `math` / `game`. (Configurable via `app_config` keys `streak_subjects`, `streak_mode`.)
  - `ckla`: CKLA 레슨 1개 이상 완료 시 streak 유지
  - DUX는 streak과 무관
  - 기존 `english` streak → `ckla` streak으로 대체
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

Cache busters in `child.html` are auto-managed by `build.sh` — every run rewrites all `?v=...` markers to a single content hash derived from the freshly built bundles + every CSS file. **Do not bump versions by hand.** A server restart (which re-runs `build.sh` via lifespan) is enough to invalidate stale browser/service-worker caches.

---

## Math Module (v2.0, 2026-05-01)

### 개요
- 대상: Gia (9세, G3, MAP RIT 205, 94th percentile)
- 교재: Go Math + CCSS G3-G6
- 목표: 개념 이해 + 기억 유지 + 적용 능력 (교사 없이 전 과정 수행)
- 상세 스펙: `MATH_SPEC.md` v2.0 참조 (모든 설계 결정의 최종 기준)

---

### 모듈 구조
| 모듈 | 설명 | 상태 |
|---|---|---|
| Academy | 정규 수학 학습 (핵심 모듈) | 🔄 v2.0 재설계 |
| Fact Fluency | 연산 속도 훈련 | ✅ 유지 |
| Daily Challenge | 매일 혼합 문제 | ✅ 유지 |
| My Problems | 오답 관리 | ✅ 유지 |
| Placement Test | 진단/기록 | ✅ 유지 |
| Glossary | 용어집 | ✅ 유지 |
| Kangaroo | 별개 독립 모듈 | ⛔ 절대 건드리지 말 것 |

---

### Academy 레슨 플로우 (v2.0)
```
pre_test (5문항, 진단+뇌 준비, 점수 미표시)
└→ learn (4카드: I Do × 2 + vocab + 브릿지)
   └→ try (5문항, You Do, 2단계 피드백)
      └→ exit_quiz (5문항, 순수 인출, ≥80% 통과)
         ├→ 통과 → 레슨 완료 화면
         │         (마지막 레슨이면 Unit Test 자동 진입)
         └→ 미통과 → 문제 교체 후 try 재시도
                     (3회 미통과 → 오늘 종료)
```

---

### 핵심 설계 원칙
1. **한 화면 = 한 개념** (타이머 없음, 자유 속도)
2. **"틀렸습니다" 금지** → 성장 마인드셋 문구 사용
3. **점수 표시 금지** → pre_test는 진단 목적만
4. **힌트/Tools/Glossary** → exit_quiz/Unit Test/spaced_review에서 완전 차단
5. **CPA 애니메이션** → fade 0.3s만, 복잡한 애니메이션 금지
6. **자기설명 질문** → "생각해봤어요 ✓" 소프트 강제
7. **답 변경** → 확인 버튼 전까지 자유롭게 가능

---

### 피드백 시스템
```
1차 오답 → 설명적 피드백 + 재시도
2차 오답 → 오개념 피드백 + CPA 폴백 + 정답 공개
2연속 오답 → 재설명 카드 자동 표시
재설명 후 오답 → 난이도 하향
```

---

### 마스터리 기준
| 단계 | 기준 |
|---|---|
| exit_quiz | ≥80% (4/5) 통과 |
| Unit Test | ≥80% (8/10) 통과 |
| My Problems 제거 | 2연속 정답 |

---

### 잠금 정책
| 조건 | 결과 |
|---|---|
| 이전 레슨 exit_quiz ≥80% | 다음 레슨 해제 |
| Unit Test ≥80% | 다음 단원 해제 |
| Unit Test 미통과 | 다음 단원 전체 🔒 |
| 부모 강제 해제 | 잠금 무관하게 해제 가능 |

---

### 간격 반복 스케줄
| exit_quiz 점수 | 복습 인터벌 |
|---|---|
| 90~100% | 14일, 28일 |
| 70~89% | 7일, 14일, 28일 |
| 50~69% | 3일, 7일, 14일 |
| <50% | 1일, 3일, 7일 |

- 1일 놓침 → 인터벌 × 0.7
- 2일 이상 놓침 → 최초 인터벌로 리셋
- 복습은 홈보드 Review 섹션 (영어+수학 통합)

---

### XP 규칙 요약
| 항목 | XP |
|---|---|
| try/exit_quiz 정답 | +1 |
| 레슨 완료 | +10 |
| Unit Test 통과 | +15 |
| Daily Challenge 완료 | +5 |
| Daily Challenge 전체 정답 | +3 추가 |
| Fact Fluency 완료 | +10 |
| Fact Fluency 개인 최고 | +2 추가 |
| spaced_review 완료 | +3 |
| My Problems 2연속 정답 제거 | +5 |
| Placement Test 완료 | +20 |
| pre_test / 재학습 / 미통과 | 0 |

---

### 스트릭 규칙
| 상황 | 조건 |
|---|---|
| 레슨 있는 날 | 레슨 완료 필수 |
| 레슨 없는 날 | spaced_review or Daily Challenge 완료 |
| 아무것도 안 한 날 | 스트릭 리셋 |

---

### TTS 우선순위
`edge-tts` → `Web Speech API` → 텍스트 하이라이트

---

### DB 마이그레이션
- **Migration 022** 실행 필수 (`MATH_SPEC.md` 섹션 13 참조)
- 수정: `math_progress`, `math_wrong_review`
- 신규: `math_spaced_review`, `math_unit_test`, `math_placement_test`

---

### 파일 구조
**수정할 파일**:
- `math-learn-cards.js` — Card3 vocab + Card4 브릿지 + 자기설명
- `math-academy.js` — 새 레슨 플로우
- `math-academy-feedback.js` — 2단계 피드백 + 재설명 카드
- `math-academy-shell.js` — 단계 저장/복원 (resume)
- `math-problem-ui.js` — 힌트 딜레이 10초, Glossary 접근 제어
- `math-academy-learn.css` — 다크모드 토큰

**추가할 파일** (미구현):
- `math-spaced-review.js`
- `math-placement-test.js`
- `math-academy-stages.css`

**추가 완료** (2026-05-01):
- `math-unit-test.js` ✅
- `math-lesson-complete.js` ✅

**절대 건드리지 말 것 (Kangaroo — 독립 모듈)**:
- `math-kangaroo.js` (및 관련 kangaroo JS 파일 전체)
- `math-kangaroo.css`
- `templates/math_kangaroo.html`
- kangaroo 관련 DB 테이블 전체

---

### 개발 우선순위
- **Phase 1**: DB 018 → pre_test → learn → try → exit_quiz → 레슨 완료 → resume
- **Phase 2**: spaced_review + 홈보드 Review 통합 + 인터리빙
- **Phase 3**: Unit Test + Placement Test + 부모 대시보드
- **Phase 4**: My Problems + Glossary + Daily Challenge 업데이트

---

### 주의사항
- `MATH_SPEC.md` v2.0이 모든 설계 결정의 최종 기준
- 스펙에 없는 기능 임의 추가 금지
- Kangaroo 모듈은 Academy와 완전히 별개, 절대 건드리지 말 것
- 구현 중 스펙 불명확 시 `MATH_SPEC.md` 섹션 번호 명시 후 질문

---

### Math Kangaroo
104 sets in `backend/data/math/kangaroo/`: IKMC 2012-2023, intl 2009-2025, KSF 2020-2025, Lebanon 2024-2025, India, USA 2003-2025, Cyprus
Levels: Pre-Ecolier (1-2), Ecolier (3-4), Benjamin (5-6), Cadet, Junior, Student
Mode: 단일 모드 — 타이머 + 제출 후 결과 표시 (Practice/Test 구분 없음, 2026-05-03 통합)
XP: complete +5, ≥80% +5, perfect +10
Files: `math-kangaroo.js`, `-exam.js`, `-pdf-exam.js`, `-result.js`

**Data Architecture Decision (2026-05-03 확정)**
- ✅ PDF Anchor Mode 채택: PDF는 `frontend/static/math/kangaroo/pdf/` 에 보관, JSON에 `pdf_page` 필드만 추가해 앱이 해당 페이지를 PDF.js로 오픈
- ❌ base64 이미지 삽입 — 기각 (파일 크기 폭증)
- ❌ PNG 개별 추출 — 기각 (104세트 × 24문제 = 수작업 불가)
- ❌ `scripts/generate_kangaroo_solutions.py` (Gemini Vision) — deprecated (2026-05-03)

**Verified External Sources**

| 소스 | URL 패턴 | 용도 |
|------|----------|------|
| kaenguru.at | `https://www.kaenguru.at/files/problems/{YEAR}_{LEVEL}_E.pdf` | 영문 문제 PDF (2022–2025 확인) |
| mathkangaroo.org | `https://mathkangaroo.org/mks/wp-content/uploads/2026/04/{YEAR}.pdf` | 공식 답안 (전 레벨, 2022–2025 확인) |
| matematica.pt | `https://matematica.pt/en/useful/kangaroo-questions.php` | 백업 소스 (2009–2024) |

Level 키: `Pre_Ecolier` / `Ecolier` / `Benjamin` / `Cadet` / `Junior` / `Student` (kaenguru.at URL 기준)

**PDF 보유 현황** (`frontend/static/math/kangaroo/pdf/`)

| 접두사 | 연도 | 레벨 | 비고 |
|--------|------|------|------|
| `ikmc_` | 2012–2023 | Ecolier, Benjamin, Cadet (일부 Junior/Student) | kaenguru.at 소스 |
| `intl_` | 2009–2025 | Ecolier, Benjamin, Cadet (일부) | 국제 공식 PDF |
| `ksf_` | 2020–2025 | Junior, Student | KSF Lebanon 소스 |
| `leb_` | 2025 | Pre-Ecolier, Ecolier, Benjamin | Lebanon 공식 |

**Past Paper JSON 스키마** — `ikmc_2024_ecolier.json` 기준 (표준 완성본, 2026-05-04)

questions 배열 내 각 문제 필드:
```json
{
  "number": 1,
  "section": 1,
  "points": 3,
  "pdf_page": 2,
  "image_required": false,
  "question_text": "...",
  "options": {"A": "...", "B": "...", "C": "...", "D": "...", "E": "..."},
  "answer": "E",
  "solution": "English explanation (1-3 sentences).",
  "solution_steps": ["Step 1: ...", "Step 2: ..."],
  "difficulty": "easy | medium | hard",
  "topic": "arithmetic | geometry | logic | pattern | spatial_reasoning | algebra | number_theory | combinatorics"
}
```

> ⚠️ `ksf_2024_junior.json` 등 구형 파일은 루트의 `solutions: {"1": "..."}` dict 방식을 사용. 신규 파일은 반드시 per-question `solution` + `solution_steps` 필드 방식으로 작성.

**Solution 작성 원칙**
- Claude가 공식 PDF를 직접 읽고 풀이 후 MK USA 공식 답안과 대조 검증
- `image_required: true` → `solution`에 "See PDF page N for figure." 포함
- `image_required: false` → `question_text` 인라인 렌더링 가능
- 모든 solution은 영어로 작성

**Solution 구축 현황 (2026-05-04 기준)**

| set_id | 상태 | 비고 |
|--------|------|------|
| `ikmc_2024_ecolier` | ✅ 완료 (24/24) | Q8·Q10 답안 수정 포함 |
| `ksf_2024_junior` 외 ksf 12세트 | 구형 solutions dict (30개) | per-question 미변환 |
| 나머지 90세트 | solution 없음 | PDF는 보유 |

**Answer Key 검증 현황 (2026-05-03 기준)**
- VERIFIED: `intl_*` 전체, `ikmc_2021_*`, `ikmc_2023_ecolier`, `ikmc_2024_ecolier` (수학적 증명), `leb_2025_*`, `cyp_*`
- PENDING: `ikmc_2023_benjamin`(Q25-30 미검증), `ikmc_2023_pre_ecolier` — UI 버튼 비활성화
- UNVERIFIED: `ikmc_2012~2022`, `usa_*`, `ksf_*` 등 — 데이터 구조 정상, 답 출처 미확인
- ❌ 데이터 오류: `cyp_2015` Q30=V, `cyp_2024` Q5=V (그리스 파일, PDF 없어 UI 노출 안됨)
- ❌ 답안 오류 수정: `usa_2024_ecolier.json` Q8=B→D, Q10=A→C (ikmc_2024_ecolier 작성 시 발견)

**Sources**
| 소스 | URL / 경로 | 검증 방법 |
|------|------------|-----------|
| matematica.pt | `/en/useful/kangaroo-questions.php` | pymupdf 300dpi 렌더링 후 표 직접 판독 |
| kangaleb.com | Lebanon 공식 PDF | 텍스트 추출 |
| kaenguru.at | `files/problems/{YEAR}_{LEVEL}_E.pdf` | 영문 문제 PDF |

전체 상세 계획: `KANGAROO_DATA_PLAN.md` 참조

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
| Word Builder | `arcade-word-builder.js` |
| Memory Match | `arcade-memory-match.js` |

Hub UI is calm (`bg-page` + cards only). Energy/SFX (`arcade-sfx.js`) only inside games. Daily XP cap configurable.

---

## US Academy (word-first SM-2)

> ⚠️ 라우터 파일(`backend/routers/us_academy.py`)이 현재 존재하지 않음 — API 미구현 상태. DB 모델(USAcademyWord, USAcademyWordProgress)과 마이그레이션(010)은 존재함. 구현 전 라우터 파일 생성 필요.

데이터 모델: `USAcademyWord`, `USAcademyWordProgress` (passage/session/unit result 테이블은 047~048 migration으로 drop됨)
- Migration: `010_us_academy_tables.py`, `047_drop_us_academy_passages.py`, `048_drop_us_academy_session_results.py`

---

## CKLA Academy (메인 학습 — Grade 3~)

### 설계 원칙
- CKLA는 앱의 메인 학습 중심 (DUX는 보조)
- Grade-aware 설계: grade 컬럼으로 G3~G8 확장 가능
- DUX와 완전 분리: 코드/DB/UI 독립

### 사이드바 구조
- 최상단: CKLA (Grade Pill: G3 활성, G4~G6 잠김)
- 하단: DUX (아코디언, 기본 접힘)

### 레슨 흐름
1. Domain 선택 (11개, 완전 자유 순서)
2. Lesson 선택 (Domain당 평균 9개)
3. 탭 학습:
   - Read: 문단별 TTS, 스크롤+하이라이트, 글자크기 3단계
   - Words: 전체 단어 카드 → 4지선다 퀴즈 3문제 (2/3 통과)
   - Q&A: Literal×2+Inferential×2+Evaluative×1 랜덤 5문제, 1회 재시도 (같은 문제), 점수 숨김
   - Word Work: Focus Word 자유 타이핑, 힌트 버튼, 힌트 유사도 80% 이상이면 오답 처리
4. 완료 기준: Read 완료 → 나머지 3탭 자유순서 → 4탭 전부 제출
5. XP: 레슨 완료 +15 (첫 완료만)

### 테스트
- **Domain Test**: 각 Domain 완료 시 자동 잠금 해제
  - Vocab(4지선다×3 + 빈칸×2) + Q&A×5 = 10문제
  - 통과 기준 80%, 즉시 재시도 가능, 타이머 없음(시간만 기록)
  - 3회 연속 실패 시 Parent Dashboard 경고
  - XP: +30

- **Grade Final Test**: 전체 Domain 완료 시 잠금 해제
  - Vocab×15 + Q&A×10(Literal4+Inferential4+Evaluative2) + WordWork×2 = 27문제
  - 통과 기준 80%
  - 80% 미달 시 24시간 후 재시도, 대기 화면에 틀린 문제+복습 버튼
  - XP: +100

### 하루 학습량
- 방학 중: 앱 자동 계산(잔여레슨÷잔여일) + 부모 조정 가능
- 방학 후: 1레슨/일 자동 전환 (부모 변경 가능)
- Today's Tasks: "CKLA · N lessons" 하나로 표시

### Grade 확장
- DB: `grade INTEGER DEFAULT 3` 컬럼
- G4~: G3 Final Test 통과 시 자동 해제. 3회 실패 시 Parent Dashboard "강제 해제" 버튼 노출
- 칭호: 0~25% Beginner / 26~50% Explorer / 51~75% Adventurer / 76~99% Champion / 100% Master

### 배지/칭호
- Domain 완료 시 배지 자동 지급 (11개)
- Grade Final Test 통과 시 "CKLA G3 Master" 칭호
- 배지 갤러리: 칭호 클릭 → 획득(컬러+날짜)/미획득(흑백+조건)

### Parent Dashboard CKLA 탭
- Grade 3 전체 진행률
- Domain별 완료 현황
- Q&A 정확도
- 오늘 학습 여부
- `needs_parent_review` 항목
- 주간 학습 그래프 (주간/월간/전체)
- Domain Test 점수 이력 + 타이머 기록
- 예상 완료일 (현재 페이스 기준)
- 학습 시작 시간 패턴
- Domain Test 3회 실패 경고

### Parent Dashboard Settings CKLA 항목
- 하루 목표 레슨 수
- 방학 종료일
- Domain 순서 강제 여부 (기본: 자유)
- Domain/Grade Final Test 통과 기준 %
- XP 수치 전체
- 체감 난이도 표시 여부
- 힌트 버튼 표시 여부
- G4 강제 해제 버튼

### Phase 4 백로그
- 오프라인 지원 (전체 데이터 캐싱, Q&A는 복귀 후 동기화)
- AI 튜터 (실시간 질문/답변)
- 푸시 알림
- 모바일/태블릿 반응형
- 멀티 프로필 (DB user_id 확장 가능하도록 설계)

### Models
`CKLADomain`, `CKLALesson`, `CKLAQuestion`, `CKLAWordLesson`,
`CKLALessonProgress`, `CKLAQuestionResponse`,
`CKLABadge` (신규), `CKLAUserBadge` (신규)

### Routers
`ckla` (메인) — SM-2 복습은 `review` 라우터로 통합 (`source=ckla`)

### Service
`services/ckla_grader.py`

### Frontend
`ckla.js`, `ckla-lesson.js`, `ckla-spelling.js`, `ckla-review.js`, `ckla.css`

### Migrations
- 011: 기존 CKLA 테이블
- 018: island_tables (10개) — CKLA grade + XPLog source는 019에서
- 019: ckla_grade + ckla_badges + ckla_user_badges
- 020: ckla_badges/user_badges (019 확장)
- 021: ckla_spelling_grammar
- 025b: ckla_review_to_word_reviews (CKLA WordReview → 통합 테이블)

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
`XPLog`, `StreakLog`, `TaskSetting`, `RewardItem`, `PurchasedReward`

### `learning.py`
`DailyWordsProgress`, `AcademySession`, `LearningLog`, `WordAttempt`, `AcademySchedule`

### `diary.py`
`DiaryEntry`, `FreeWriting`, `GrowthEvent`, `DayOffRequest`

### `math.py`
`MathPlacementResult`, `MathProblem`, `MathProgress`, `MathAttempt`, `MathWrongReview`, `MathFactFluency`, `MathDailyChallenge`, `MathKangarooProgress`, `MathSpacedReview`, `MathUnitTest`, `MathPlacementTest`

### `assistant.py`
`AssistantLog`, `AiCallLog`

### `us_academy.py`
`USAcademyWord`, `USAcademyWordProgress` (passage/session/unit result 테이블은 migration 047~048로 drop됨)

### `ckla.py`
`CKLADomain`, `CKLALesson`, `CKLAQuestion`, `CKLAWordLesson`, `CKLALessonProgress`, `CKLAQuestionResponse`, `CKLABadge`, `CKLAUserBadge`, `CKLASpelling`, `CKLAGrammar`, `CKLAMorphology`

### `goals.py`
`WeeklyGoal`

### `island.py`
`IslandCharacter`, `IslandCharacterProgress`, `IslandCareLog`, `IslandShopItem`, `IslandInventory`, `IslandPlacedItem`, `IslandCurrency`, `IslandLumiLog`, `IslandLegendProgress`, `IslandZoneStatus`

### Migrations (`backend/migrations/`)

> 총 56개 파일. 시스템은 filename 전체로 추적하므로 동일 prefix(025/033/034/040/041)를 가진 5쌍은 각각 별개로 실행됨 — 안전.

**001~024 (기반 + Island 초기)**
001 base · 002 shop columns · 003 math tables · 004 review_source · 005 practice_sentence created_at · 006 academy_session active · 007 free_writings · 008 streak 3-subjects · 009 kangaroo columns · 010 us_academy_tables · 011 ckla_tables · 012 kangaroo rename set_ids · 013 diary_entry columns · 014 report schedule · 015 study_item starred · 016 weekly goals · 017 math_progress UNIQUE · 018 island_tables (10 new tables) · 019 ckla_grade · 020 ckla_badges · 021 ckla_spelling_grammar · 022 math_v2_schema · 023 island_decor_image_paths · 024 island_decor_extension

**025~039 (CKLA 데이터 품질 + Math v2)**
025a ai_call_log · 025b ckla_review_to_word_reviews · 026 ckla_aux_content · 027 fix_d1_lesson_titles · 028 fix_qa_model_answers · 029 fix_d4l9_evaluative · 030 audio_url_backfill · 031 fix_ocr_artifacts · 032 fix_data_quality_round2 · 033a add_qa_done · 033b math_progress_mastery · 034a math_attempt_misconception · 034b strip_wordnet_tags · 035 fix_bad_definitions · 036 fix_short_definitions · 037 fix_mw_colon_definitions · 038 fix_pos_and_short_definitions · 039 fix_circular_and_misc

**040~056 (DUX 사전 정규화 + Island 확장)**
040a fix_compound_noun_pos · 040b math_unique_constraints · 041a fix_relating_to_definitions · 041b math_daily_unique_date · 042 fix_examples_bold_and_wrong · 043 lowercase_definition_starts · 044 fix_structural_and_content_p1 · 045 expand_short_definitions · 046 fill_sort_order · 047 drop_us_academy_passages · 048 drop_us_academy_session_results · 049 fix_lesson14_progress · 050 generate_missing_audio · 051 normalize_pretest_stage · 052 island_zone_sequential_lock · 053 island_zone_first_evo_unlock · 054 xplog_composite_index · 055 island_evo_food_image_paths · **056 word_reviews_easiness_real** ← latest

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

**Tables status (2026-05-16):** `growth_theme_progress` — removed from `gamification.py`, `routers/growth_theme.py` deleted. `rewards` / `schedules` tables still exist (kept for back-compat).

---

### New Backend Files

| File | Purpose |
|------|---------|
| `routers/island.py` | All island API (41 endpoints, incl. `/decorate/{place,move,remove}`) |
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

### Completed Deletions (2026-05-16)

| File | Status |
|------|--------|
| `routers/growth_theme.py` | ✅ Deleted — island system is replacement |
| `models/gamification.py` (GrowthThemeProgress) | ✅ Removed from model and `__all__` |
| `frontend/static/js/growth-theme.js` | ✅ Deleted — removed from build.sh |

---

### Frontend Files

Island UI is built with JSX React components (`frontend/src/island/*.jsx`, 17 files). These are separate from the vanilla JS bundles and have their own build pipeline (`build.sh` builds all 17 JSX files + `island-result.js` via a separate React/Babel step).

JSX components (`frontend/src/island/`):
- `IslandMain.jsx` — main island screen
- `SettingsScreen.jsx` — island settings (Dev Tools panel included)
- (and 15 more island JSX components)

Vanilla JS (loaded separately, not in esbuild bundles):
- `frontend/static/js/island-result.js` — island update card shown on study result screens (XP + lumi gain summary)
- `frontend/static/js/reward-shop-island.js` — island shop tab content (Evolution / Food / Decor / Exchange)

CSS files (`frontend/static/css/`):
- `island-loop.css` — animation loop styles
- `island-main.css` — main island screen layout
- `island-meta.css` — meta/overlay panel styles
- `island-screens.css` — screen transition styles
- `island-system.css` — system-level island UI (currency display, gauges)
- `island-zones.css` — zone card and zone unlock styles

Config files:
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

---

## Architecture Decisions

### CKLA Data Verification Tool (2026-05-10)

**Tool:** `scripts/verify_ckla_data.py`  
**Purpose:** Read-only integrity check producing two scores:
- **Authority Score** (0–100): source fidelity — JSON↔DB consistency, structural completeness, app-critical fields
- **Kid Fitness Score** (0–100): age-appropriateness — word coverage ratios, Q&A quality, passage length suitability

**Design decisions:**
- ✅ Two-score system adopted (Authority + Kid Fitness) — single pass/fail rejected as too coarse for content quality
- ✅ 33 validation items in 5 groups: Source Fidelity (Group 1), Structure (Group 2), App Functionality (Group 3), KF_COUNT (count-based kid fitness), KF_RATIO (ratio-based kid fitness)
- ✅ Standard library only (`sqlite3`, `json`, `re`, `argparse`, `pathlib`) — no third-party deps
- ✅ Single read-only transaction (`BEGIN ... ROLLBACK`) for snapshot consistency
- ✅ Orphan cascade cap: if ≥5 lessons share same orphaned domain_id, deduction capped at 10 pts
- ❌ Single aggregate score rejected — masks authority vs enrichment distinction
- ❌ Live DB writes rejected — tool must be completely non-destructive
- **Thresholds:** Authority ≥100 + Kid Fitness ≥90 = "Ready"; Auth <80 = "Critical"
- **Exit codes:** 0 (clean), 1 (errors found), 2 (schema/DB missing)
- **Reports:** saved to `reports/ckla_verify_*.json` (gitignored, regenerable)
