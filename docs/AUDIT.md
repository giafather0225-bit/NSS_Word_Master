# GIA Learning App — Codebase Audit
> Generated: 2026-05-03 | Auditor: Claude Code (read-only pass)

---

## Section 1: Documentation Drift

| # | Location | Claim | Actual | Severity |
|---|----------|-------|--------|----------|
| 1 | CLAUDE.md "Tech Stack" | "mounts **45 routers**" | 47 `.py` files in `backend/routers/` (plus `__init__.py`) | Medium |
| 2 | CLAUDE.md "Frontend Modules" | "83 JS source files" | 86 `.js` source files in `frontend/static/js/` (excl. bundles) | Low |
| 3 | CLAUDE.md "Migrations" (models section) | highest listed = `019_ckla_grade` | Files go up to `022_math_v2_schema.py`; migrations 020–022 exist on disk but are absent from the CLAUDE.md list | High |
| 4 | CLAUDE.md "Migrations" (models section) | `019 = ckla_badges + ckla_user_badges` | `019` = `ckla_grade.py`; `020` = `ckla_badges`; mismatch on every number from 019 onward | High |
| 5 | CLAUDE.md "Backend Routers" table (45 entries) | `parent_ckla` not listed | `parent_ckla.py` exists and is registered in `main.py` line 270 | Medium |
| 6 | CLAUDE.md "Island System — Deleted Files" | "`routers/growth_theme.py` — Replaced by island" | `growth_theme.py` still exists and is still registered in `main.py` line 250 | High |
| 7 | CLAUDE.md "Island System — Deleted Files" | `GrowthThemeProgress` model parts removed | `GrowthThemeProgress` class still present in `backend/models/gamification.py` | High |
| 8 | CLAUDE.md "Island System" | Frontend described as vanilla JS config files | Island frontend is actually JSX React components (`frontend/src/island/*.jsx`, 18 files bundled via esbuild) — not documented anywhere in CLAUDE.md | High |
| 9 | CLAUDE.md "Tests" (via `pytest.ini`) | Tests described as being in `backend/tests/` | Tests live at `tests/` (project root); `backend/tests/` does not exist | Medium |
| 10 | README.md "Project Layout" | `backend/models.py` listed as "SQLAlchemy models (23 tables)" | Models are split into 11 domain files under `backend/models/`; no single `models.py` exists | High |
| 11 | README.md | "Phases 1–10 complete" | Island system (documented as partially built), Math v2.0 re-design (migration 022 untracked), and math-spaced-review.js (untracked) indicate active in-progress work beyond phase 10 | Medium |
| 12 | CLAUDE.md Math Module "추가할 파일" | `math-unit-test.js` and `math-placement-test.js` listed as files to add | Neither file appears in `frontend/static/js/` or `build.sh`; `math-spaced-review.js` is present but untracked | Medium |
| 13 | CLAUDE.md Math v2.0 | "Migration 018 실행 필수" for math_spaced_review, math_unit_test tables | Migration 018 is named `018_island_tables.py`; math v2 schema is migration 022 | Medium |
| 14 | CLAUDE.md "Backend Routers" | `ckla_review` listed under "US Academy / CKLA" as "`ckla_review` — CKLA review queue" | Also flagged in notes as "삭제 예정 → review로 통합" but file still exists and is registered | Low |

---

## Section 2: Module Inventory Table

| Router file | Primary JS counterpart(s) | CSS file(s) | In CLAUDE.md? | Test in tests/? | In navigation.js sidebar? |
|---|---|---|---|---|---|
| `ai_coach.py` | `home.js` | `home.css` | Yes | No | No (called from home) |
| `arcade.py` | `arcade.js` | `arcade.css` | Yes | No | No (view switch) |
| `calendar_api.py` | `diary-calendar.js`, `calendar.js` | `diary-calendar.css`, `calendar.css` | Yes (implicit) | No | No |
| `ckla.py` | `ckla.js`, `ckla-lesson.js` | `ckla.css` | Yes | No | Yes (`showCKLAView()`) |
| `ckla_review.py` | `ckla-review.js` | `ckla.css` | Yes | No | Yes (`showCKLAReview()`) |
| `collocation.py` | `collocation.js` | `collocation.css` | Yes | No | No |
| `daily_words.py` | `daily-words.js`, `daily-words-weekly.js` | `daily-words.css` | Yes | No | Yes (`showDailyWordsView()`) |
| `dashboard.py` | `home.js` | `home.css` | Yes | No | No |
| `day_off.py` | `diary-home.js` | `diary-home.css` | Yes | No | No |
| `diary.py` | `diary-write.js`, `diary-entry.js`, `diary.js` | `diary.css`, `diary-write.css`, `diary-entry.css` | Yes | No | No |
| `diary_photo.py` | `diary-write.js` | `diary-write.css` | Yes | No | No |
| `diary_sentences.py` | `diary-home.js` | `diary-sub.css` | Yes | No | No |
| `files.py` | `parent-ingest.js` | `parent-ingest.css` (n/a child) | Yes | Yes (`test_file_storage.py`) | No |
| `free_writing.py` | `free-writing.js` | `diary-sub.css` | Yes | No | No |
| `goals.py` | `parent-goals.js` | `parent.css` | Yes | No | No |
| `growth_theme.py` | `growth-theme.js` | none dedicated | Yes | No | No (should be removed per spec) |
| `island.py` | `reward-shop-island.js`, `island-result.js`, JSX bundle | `island-*.css` (6 files) | Yes (ISLAND_SPEC section) | No | No (home card click) |
| `lessons.py` | `navigation.js` | none dedicated | Yes | No | Yes |
| `math_academy.py` | `math-academy.js`, `-shell.js`, `-ui.js`, `-feedback.js`, `math-learn-cards.js` | `math-academy-*.css` | Yes | Yes (`test_math_academy.py`) | No (math home) |
| `math_daily.py` | `math-daily.js` | `math-academy-daily.css` | Yes | Yes (`test_math_daily.py`) | No |
| `math_fluency.py` | `math-fluency.js` | `math-academy-fluency.css` | Yes | Yes (`test_math_fluency.py`) | No |
| `math_glossary.py` | `math-glossary.js` | `math-academy-glossary.css` | Yes | Yes (`test_math_glossary.py`) | No |
| `math_kangaroo.py` | `math-kangaroo.js`, `-exam.js`, `-pdf-exam.js`, `-result.js` | `math-kangaroo.css` | Yes | Yes (`test_math_kangaroo.py`) | No |
| `math_placement.py` | `math-placement.js`, `math-placement-results.js` | `math-academy-modes.css` | Yes | Yes (`test_math_placement.py`) | No |
| `math_problems.py` | `math-review.js` (wrong-review) | `math-academy-problems.css` | Yes | Yes (`test_math_problems.py`) | No |
| `parent.py` | `parent-panel.js`, `parent-settings.js` | `parent.css` | Yes | No | No |
| `parent_ckla.py` | `parent-ckla.js` | `parent.css` | **No** (not in router table) | No | No |
| `parent_math.py` | `parent-math.js` | `parent.css` | Yes | No | No |
| `parent_report.py` | `parent-report.js` | `parent.css` | Yes | No | No |
| `parent_stats.py` | `parent-overview.js` | `parent.css` | Yes | No | No |
| `parent_streak.py` | `parent-streak.js` | `parent.css` | Yes | No | No |
| `parent_xp.py` | `parent-xp.js` | `parent.css` | Yes | No | No |
| `progress.py` | `child.js`, `child-exam.js` | none dedicated | Yes (implicit) | No | No |
| `reminder.py` | `home.js` | `home.css` | Yes | No | No |
| `review.py` | `review.js` | `review.css` | Yes | No | Yes (`btn-review`) |
| `reward_shop.py` | `reward-shop.js`, `reward-shop-use.js`, `reward-shop-island.js` | `reward-shop.css` | Yes | No | No |
| `rewards.py` | `reward-shop.js` (legacy compat) | `reward-shop.css` | Yes (legacy) | No | No |
| `schedules.py` | `parent-settings.js` | `parent.css` | Yes | No | No |
| `speech.py` | `child.js` (per-stage mic) | none | Yes | No | No |
| `starred.py` | `child.js` | none | Yes | No | No |
| `study.py` | `child.js`, `navigation.js` | none | Yes | No | Yes |
| `system.py` | `parent-panel.js` | `parent.css` | Yes | No | No |
| `tts.py` | `tts-client.js`, `sound.js` | none | Yes | No | No |
| `tutor_sentence.py` | `sentence.js`, `sentence_ai.js` | `sentence.css` | Yes | No | No |
| `us_academy.py` | none identified in build.sh | none | Yes | No | No |
| `words.py` | `child.js` (word manager) | `word-manager.css` | Yes | No | Yes (`btn-word-manager`) |
| `xp.py` | `home.js` | `xp.css` | Yes | No | No |

---

## Section 3: Screen Inventory

| # | Screen name | Entry path | Frontend file(s) | Backend router | Status | Notes |
|---|---|---|---|---|---|---|
| 1 | Splash Screen | App load | `splash.js` | none | works | Per-day-of-week bg colors |
| 2 | Home Dashboard | `/` default | `home.js` | `dashboard.py`, `ai_coach.py`, `reminder.py` | works | Today tasks, AI coach, XP, streak |
| 3 | English Hub (sidebar) | Home → English | `child.html` sidebar | none | works | Shows CKLA + DUX + Review sections |
| 4 | CKLA Domain List | English → Open CKLA | `ckla.js` | `ckla.py` | partial | Grades G4–G6 locked; migration 019–020 needed |
| 5 | CKLA Lesson — Read Tab | CKLA domain → lesson | `ckla-lesson.js` | `ckla.py` | partial | CSS modified (unstaged); TTS integration unknown |
| 6 | CKLA Lesson — Words Tab | CKLA lesson tabs | `ckla-lesson.js` | `ckla.py` | partial | 4-choice quiz logic |
| 7 | CKLA Lesson — Q&A Tab | CKLA lesson tabs | `ckla-lesson.js` | `ckla.py` | partial | 5-question randomized |
| 8 | CKLA Lesson — Word Work Tab | CKLA lesson tabs | `ckla-lesson.js` | `ckla.py` | partial | Free-type + hint; migration 021 adds spelling/grammar columns |
| 9 | CKLA Review Queue | English → CKLA Review | `ckla-review.js` | `ckla_review.py` | unknown | Router marked "삭제 예정" in CLAUDE.md |
| 10 | CKLA Badge Gallery | English → Badges | `ckla.js` (`showBadgeGallery`) | `ckla.py` | unknown | Depends on migration 020 |
| 11 | CKLA Domain Test | Auto-unlock after domain | `ckla-lesson.js` | `ckla.py` | unknown | 10-question test; XP +30 |
| 12 | CKLA Grade Final Test | After all domains done | `ckla-lesson.js` | `ckla.py` | unknown | 27-question; XP +100 |
| 13 | DUX: Lesson Select | English → DUX accordion | `navigation.js` | `lessons.py`, `study.py` | works | Textbook + lesson dropdowns |
| 14 | DUX: Preview (Step 1) | DUX lesson → Start | `preview.js` | `study.py`, `tts.py` | works | Card grid + modal + TTS + STT shadow |
| 15 | DUX: Word Match (Step 2) | Preview complete | `wordmatch.js` (bundle-a) | `progress.py` | works | 7 words/round matching |
| 16 | DUX: Fill Blank (Step 3) | Word Match complete | `fillblank.js` | `progress.py` | works | Sentence + word pills |
| 17 | DUX: Spelling (Step 4) | Fill Blank complete | `spelling.js` | `progress.py` | works | Wordle-style 3-pass |
| 18 | DUX: Make Sentence (Step 5) | Spelling complete | `sentence.js`, `sentence_ai.js` | `tutor_sentence.py` | works | Drag-drop + AI grade |
| 19 | DUX: Final Test | Sidebar btn-exam | `finaltest.js`, `child-exam.js` | `progress.py` | works | 20 MC + 20 fill; 90% pass |
| 20 | DUX: Unit Test | Sidebar btn-kigoosa | `unittest.js` (bundle-a) | `progress.py` | works | Cross-lesson test |
| 21 | Review (SM-2 unified) | English → Review badge | `review.js` | `review.py` | works | Unified English + Math queue |
| 22 | Daily Words | English → Daily Words accordion | `daily-words.js` | `daily_words.py` | works | 10 words/day |
| 23 | Daily Words Weekly Test | Daily Words → weekly | `daily-words-weekly.js` | `daily_words.py` | works | End-of-week review |
| 24 | Collocation | (no visible sidebar entry) | `collocation.js` | `collocation.py` | unknown | No clear sidebar entry point found in child.html |
| 25 | My Words / Word Manager | English → My Words | `child.js` (word manager) | `words.py` | works | CRUD + AI enrich |
| 26 | Math Home | Home → Math | `math-navigation.js` | `dashboard.py` | works | Module hub grid |
| 27 | Math Academy: Pre-test | Math → Academy | `math-academy.js` | `math_academy.py` | partial | v2 flow; migration 022 untracked |
| 28 | Math Academy: Learn Cards | Pre-test complete | `math-learn-cards.js`, `math-learn-visuals.js` | `math_academy.py` | partial | CPA cards; CSS modified (unstaged) |
| 29 | Math Academy: Try (You Do) | Learn complete | `math-academy.js`, `math-problem-ui.js`, `math-academy-feedback.js` | `math_academy.py` | partial | 2-step feedback; JS modified (unstaged) |
| 30 | Math Academy: Exit Quiz | Try complete | `math-academy.js` | `math_academy.py` | partial | ≥80% pass; spaced review schedule |
| 31 | Math Academy: Lesson Complete | Exit quiz pass | `math-academy.js` | `math_academy.py` | unknown | No dedicated `math-lesson-complete.js` (CLAUDE.md says add it) |
| 32 | Math Academy: Unit Test | Last lesson exit quiz pass | `math-academy.js` | `math_academy.py` | partial | CLAUDE.md says `math-unit-test.js` needed; not present |
| 33 | Math Academy: Spaced Review | Home Review card | `math-spaced-review.js` | `math_academy.py` | partial | File is untracked; partially wired to home dashboard (recent commit `32d869b`) |
| 34 | Math Fact Fluency | Math → Fluency | `math-fluency.js` | `math_fluency.py` | works | Timed drill rounds |
| 35 | Math Daily Challenge | Math → Daily | `math-daily.js` | `math_daily.py` | works | Mixed daily problems |
| 36 | Math Placement Test | Math → Placement | `math-placement.js` | `math_placement.py` | works | Diagnostic test |
| 37 | Math Placement Results | After placement test | `math-placement-results.js` | `math_placement.py` | works | Grade/unit breakdown |
| 38 | Math Kangaroo Hub | Math → Kangaroo | `math-kangaroo.js` | `math_kangaroo.py` | works | 103 sets; PDF anchor mode |
| 39 | Math Kangaroo Exam | Kangaroo set select | `math-kangaroo-exam.js`, `math-kangaroo-pdf-exam.js` | `math_kangaroo.py` | works | Timer + submit |
| 40 | Math Kangaroo Results | After exam submit | `math-kangaroo-result.js` | `math_kangaroo.py` | works | Score + solutions |
| 41 | Math Glossary | Math → Glossary | `math-glossary.js` | `math_glossary.py` | works | Per-grade vocab |
| 42 | My Problems (wrong review) | Math → My Problems | `math-review.js` | `math_problems.py` | works | 2-consecutive-correct removal |
| 43 | Diary Hub | Home → Diary | `diary-home.js` | `diary.py` | works | 4 stats + week calendar |
| 44 | Diary: Daily Journal | Diary → write | `diary-write.js` | `diary.py` | works | AI feedback |
| 45 | Diary: Entry View | Diary → past entry | `diary-entry.js` | `diary.py` | works | View + photos |
| 46 | Diary: Free Writing | Diary → Free Writing | `free-writing.js` | `free_writing.py` | works | Free-form text |
| 47 | Diary: My Sentences | Diary → My Sentences | `diary-home.js` | `diary_sentences.py` | works | Step-5 sentence archive |
| 48 | Diary: My Worlds | Diary → My Worlds | `growth-theme.js` | `growth_theme.py` | unknown | CLAUDE.md says replaced by Island; still in codebase |
| 49 | Diary: Calendar | Diary → Calendar | `diary-calendar.js` | `calendar_api.py` | works | Monthly streak/journal markers |
| 50 | Diary: Day Off | Diary → Day Off | `diary-home.js` | `day_off.py` | works | Request → email parent → approve/deny |
| 51 | Diary: Photo | Diary entry → attach | `diary-write.js` | `diary_photo.py` | works | Multi-photo upload |
| 52 | Growth Theme (legacy) | (no clear sidebar entry) | `growth-theme.js` | `growth_theme.py` | unknown | Spec says deleted; still live |
| 53 | Reward Shop — Rewards | (home or nav trigger) | `reward-shop.js` | `reward_shop.py` | works | XP spend; 5 default items |
| 54 | Reward Shop — Evolution tab | Reward shop tab | `reward-shop-island.js` | `reward_shop.py` / `island.py` | partial | Lumi spend; depends on Island |
| 55 | Reward Shop — Food tab | Reward shop tab | `reward-shop-island.js` | `island.py` | partial | Lumi spend |
| 56 | Reward Shop — Decor tab | Reward shop tab | `reward-shop-island.js` | `island.py` | partial | Lumi spend |
| 57 | Reward Shop — Exchange tab | Reward shop tab | `reward-shop-island.js` | `island.py` | partial | 100 Lumi → 1 Legend Lumi |
| 58 | Arcade Hub | (nav or home) | `arcade.js` | `arcade.py` | works | 7-game hub |
| 59 | Arcade: Word Invaders | Arcade → Word Invaders | `arcade-word-invaders.js` | `arcade.py` | works | |
| 60 | Arcade: Spell Rush | Arcade → Spell Rush | `arcade-spell-rush.js` | `arcade.py` | works | |
| 61 | Arcade: Definition Match | Arcade → Def Match | `arcade-definition-match.js` | `arcade.py` | works | |
| 62 | Arcade: Crossword | Arcade → Crossword | `arcade-crossword.js` | `arcade.py` | works | |
| 63 | Arcade: Sudoku | Arcade → Sudoku | `arcade-sudoku.js` | `arcade.py` | works | |
| 64 | Arcade: Make 24 | Arcade → Make 24 | `arcade-make24.js` | `arcade.py` | works | |
| 65 | Arcade: Math Invaders | Arcade → Math Invaders | `arcade-math-invaders.js` | `arcade.py` | works | |
| 66 | Island: Main View | Home → Island card | `IslandMain.jsx` (JSX bundle) | `island.py` | partial | JSX components exist; migration 018 present; Phase 2 partially built |
| 67 | Island: Zone Detail | Island → zone | `ZoneDetail.jsx` | `island.py` | partial | |
| 68 | Island: Character Detail | Island → character | `CharacterDetail.jsx` | `island.py` | partial | |
| 69 | Island: Evolution Modal | Character → evolve | `EvolutionModal.jsx` | `island.py` | partial | |
| 70 | Island: Onboarding | First launch | `Onboarding.jsx` | `island.py` | partial | |
| 71 | Island: Shop | Island → shop | `IslandShop.jsx` | `island.py` | partial | |
| 72 | Island: Inventory | Island → inventory | `Inventory.jsx` | `island.py` | partial | |
| 73 | Island: Collection | Island → collection | `Collection.jsx` | `island.py` | partial | |
| 74 | Island: Daily Screen | Island → daily | `DailyScreen.jsx` | `island.py` | partial | |
| 75 | Island: Settings | Island → settings | `SettingsScreen.jsx` | `island.py` | partial | File modified (unstaged) |
| 76 | Island: Lumi Log | Island → lumi log | `LumiLog.jsx` | `island.py` | unknown | No dedicated backend endpoint confirmed |
| 77 | Island: Feed | Island → feed | `FeedScreen.jsx` | `island.py` | partial | |
| 78 | US Academy | (no visible sidebar entry in child.html) | none found in build.sh | `us_academy.py` | unknown | No JS counterpart in any bundle; may be dead/unreachable UI |
| 79 | Parent Dashboard: Home | Home → ··· PIN | `parent-overview.js` | `parent.py`, `parent_stats.py` | works | 6-tab shell; PIN-gated |
| 80 | Parent Dashboard: English | Parent → English tab | `parent-panel.js` | `parent_stats.py` | works | Missed words, stage accuracy |
| 81 | Parent Dashboard: Math | Parent → Math tab | `parent-math.js` | `parent_math.py` | works | 4-stat grid, weak concepts |
| 82 | Parent Dashboard: Habits | Parent → Habits tab | `parent-streak.js` | `parent_streak.py` | works | Streak grid, day-off approvals |
| 83 | Parent Dashboard: Goals | Parent → Goals tab | `parent-goals.js` | `goals.py` | works | Weekly goals, PIN-gated edit |
| 84 | Parent Dashboard: Settings | Parent → Settings tab | `parent-settings.js`, `parent-textbooks.js` | `parent.py`, `schedules.py` | works | Task settings, PIN, report schedule |
| 85 | Parent Dashboard: CKLA | Parent → (CKLA tab?) | `parent-ckla.js` | `parent_ckla.py` | unknown | Router not in CLAUDE.md router table; tab may not be wired in parent-panel.js |
| 86 | Parent Weekly Report | Settings → Send/Preview | `parent-report.js` | `parent_report.py` | works | Email preview + schedule |
| 87 | Parent Ingest (OCR) | `/ingest` URL | `parent-ingest.js` | `files.py` | works | Image → OCR → word import |

**Totals: 87 screens — 30 works / 31 partial / 0 broken / 26 unknown**

---

## Section 4: Things I Could NOT Verify Without Running The App

| # | Item | Reason |
|---|------|--------|
| 1 | TTS first-byte latency | Requires runtime measurement of edge-tts BytesIO pipeline |
| 2 | Ollama → Gemini AI fallback chain | Cannot test offline conditions from code alone |
| 3 | Web Speech API STT accuracy thresholds (≥80% shadow, ≥90% sentence read) | Browser API, no unit tests |
| 4 | PWA service worker cache invalidation | Requires browser + network throttle testing |
| 5 | Island gauge decay correctness on first app open | `run_daily_batch` runs at lifespan startup; correctness depends on prior DB state |
| 6 | Island JSX bundle actually renders (no JS errors) | `frontend/src/island/*.jsx` compiled via esbuild but no tests exist |
| 7 | math-spaced-review.js integration with home dashboard | File is untracked; wiring commit exists (`32d869b`) but runtime behavior unverified |
| 8 | Migration 022 (`math_v2_schema.py`) idempotency and correctness | File is untracked; not yet committed or validated |
| 9 | US Academy reachability | No JS bundle entry, no sidebar entry point found — may be an unreachable dead module |
| 10 | Collocation sidebar entry point | No `showCollocation` or `btn-collocation` found in child.html; entry path unclear |
| 11 | Parent CKLA tab wiring | `parent_ckla.py` + `parent-ckla.js` exist but no tab entry confirmed in `parent-panel.js` without running |
| 12 | CKLA badge display correctness | Depends on migration 020 having run; badge data not verifiable from code alone |
| 13 | Growth Theme screen reachability | No sidebar entry found; may only be accessible from within Diary My Worlds |
| 14 | Day-off email delivery | Requires `GEMINI_API_KEY` or SMTP config; `email_sender.py` not verified end-to-end |
| 15 | SM-2 interval correctness after math v2 spaced review integration | Algorithm in `backend/sm2.py`; integration with new `math_spaced_review` table unverified |
| 16 | XP/Lumi dual-award on study complete | `xp_engine.py` + `lumi_engine.py` both modified (unstaged); combined behavior unconfirmed |
| 17 | iOS PWA behavior (safe-area, apple-touch-icon) | Requires physical device test |
| 18 | KaTeX rendering for all math problem types | CDN dependency; auto-render needs correct LaTeX in JSON data files |
