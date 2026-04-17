# GIA Learning App — Frontend Component Map

> Maps each screen/feature to its JS, CSS, HTML, and API dependencies.
> Update when adding new screens or refactoring existing ones.

---

## App Entry (SPA Shell)

- **HTML:** `templates/child.html` (main SPA shell — rename to index.html in Phase 2)
- **Script load order:** core.js → tts-client.js → analytics.js → navigation.js → preview.js → wordmatch.js → fillblank.js → spelling.js → sentence.js → child.js → (feature-specific: finaltest.js, unittest.js, review.js, word-manager.js, sentence_ai.js)
- **CSS load order:** theme.css → style.css (or main.css) → feature CSS files

---

## Phase 1 — Current JS Module Map

| Module | File | Key Functions | Tags |
|--------|------|--------------|------|
| Core | `js/core.js` | CONF, STAGE, global state, escapeHtml, shuffle, stopAudio, stageStorageKey, markStageComplete | SYSTEM |
| TTS Client | `js/tts-client.js` | apiPreviewTTS, apiWordOnly, apiExampleFull, apiTutorReply | TTS, AI |
| Analytics | `js/analytics.js` | _trackStageStart, _trackWordAttempt, _trackStageComplete | ACADEMY |
| Navigation | `js/navigation.js` | loadTextbooks, loadLessons, loadStudyItems, setSubject, updateRoadmapUI | SIDEBAR, NAVIGATION, ENGLISH |
| Preview | `js/preview.js` | openPreviewModal, renderPreview | PREVIEW, SHADOW, SPELL |
| Word Match | `js/wordmatch.js` | wmState, renderMeaningMatch, drawWmLines | WORD_MATCH, ACADEMY |
| Fill Blank | `js/fillblank.js` | fbState, renderContextFill | FILL_BLANK, ACADEMY |
| Spelling | `js/spelling.js` | spState, renderSpelling | SPELLING, ACADEMY |
| Sentence | `js/sentence.js` | smState, renderSentenceMaker, evaluateSentence | SENTENCE, AI, ACADEMY |
| App Shell | `js/child.js` | renderStage, renderIdleStage, advanceToNextStage, buildExamQueue, DEV | ACADEMY, NAVIGATION |

---

## Home Dashboard (Phase 2)

- **JS:** `js/home.js`, `js/ai-coach.js`, `js/growth-theme.js`
- **CSS:** `css/home.css`
- **HTML:** `templates/index.html` `#home-dashboard`
- **API:**
  - GET /api/tasks/today
  - GET /api/xp/summary
  - GET /api/ai-coach/today
  - GET /api/reminders/today
- **Tags:** HOME_DASHBOARD, TODAY_TASKS, REMINDER, AI_COACH, XP, STREAK

---

## English > Academy (5-Stage Learning)

- **JS:** `js/core.js`, `js/navigation.js`, `js/preview.js`, `js/wordmatch.js`, `js/fillblank.js`, `js/spelling.js`, `js/sentence.js`, `js/child.js`, `js/sentence_ai.js`, `js/analytics.js`, `js/tts-client.js`
- **CSS:** `css/preview.css`, `css/wordmatch.css`, `css/fillblank.css`, `css/spelling.css`, `css/sentence.css`
- **HTML:** `templates/child.html` `#stage-card`, `#stage-area`, `#preview-modal`, `#tutor-modal`
- **API:**
  - GET /api/study/{subject}/{textbook}/{lesson}
  - POST /api/learning/log
  - POST /api/learning/word-attempt
  - POST /api/progress/verify
  - POST /api/tts/*
  - POST /api/evaluate-sentence
  - POST /api/practice/sentence
- **Tags:** ACADEMY, PREVIEW, WORD_MATCH, FILL_BLANK, SPELLING, SENTENCE, TTS, AI

---

## English > Final Test

- **JS:** `js/finaltest.js`
- **CSS:** `css/finaltest.css`
- **HTML:** `templates/child.html` `#exam-overlay`
- **API:** POST /api/progress/verify, POST /api/learning/log
- **Tags:** FINAL_TEST, ACADEMY

---

## English > Unit Test

- **JS:** `js/unittest.js`
- **CSS:** `css/unittest.css`
- **HTML:** `templates/child.html` `#ut-overlay`
- **API:** GET /api/study/{subject}/{textbook}/{lesson}
- **Tags:** UNIT_TEST, ACADEMY

---

## English > Review (SM-2)

- **JS:** `js/review.js`
- **CSS:** `css/review.css`
- **HTML:** `templates/child.html` (inline review UI triggered by `#btn-review`)
- **API:**
  - GET /api/review/today
  - POST /api/review/result
  - POST /api/review/register-lesson
  - GET /api/review/stats
- **Tags:** REVIEW, SM2, ACTIVE_RECALL

---

## English > My Words (Word Manager)

- **JS:** `js/word-manager.js`
- **CSS:** `css/word-manager.css`
- **HTML:** `templates/child.html` `#wm-overlay`, `#wm-body`
- **API:**
  - GET /api/storage/lessons/{lesson_id}/words
  - POST /api/mywords/lessons
  - POST /api/mywords/{lesson}/words
  - POST /api/mywords/ai-enrich
- **Tags:** MY_WORDS, AI

---

## English > Daily Words (Phase 4) ✅

- **JS:** `js/daily-words.js`, `js/daily-words-weekly.js`
- **CSS:** `css/daily-words.css`
- **HTML:** `templates/child.html` `#daily-words-view`, sidebar `#dw-grade-label`, `#dw-week-progress`, `#dw-today-progress`, `#dw-start-btn`
- **API:**
  - GET /api/daily-words/status
  - GET /api/daily-words/today
  - POST /api/daily-words/day1-result
  - POST /api/daily-words/complete
  - GET /api/daily-words/weekly-test
  - POST /api/daily-words/weekly-test/result
- **Tags:** DAILY_WORDS, WEEKLY_TEST

---

## GIA's Diary (Phase 6)

- **JS:** `js/diary.js`, `js/calendar.js`
- **CSS:** `css/diary.css`, `css/calendar.css`
- **HTML:** TBD (Phase 6)
- **API:**
  - POST/GET /api/diary/entries
  - GET /api/growth/timeline
  - GET /api/calendar/{year}/{month}
  - POST /api/day-off/request
- **Tags:** DIARY, JOURNAL, GROWTH_TIMELINE, CALENDAR, DAY_OFF

---

## Reward Shop (Phase 5)

- **JS:** `js/reward-shop.js`
- **CSS:** `css/reward-shop.css`
- **HTML:** TBD (Phase 5)
- **API:**
  - GET /api/shop/items
  - POST /api/shop/buy
  - POST /api/shop/use-reward
- **Tags:** SHOP, REWARD, PURCHASE, PIN

---

## Parent Dashboard

- **JS:** `js/parent-panel.js`, `js/parent-settings.js`, `js/parent-ingest.js`
- **CSS:** `css/parent.css`
- **HTML:** In-app overlay in `templates/child.html`; separate page `templates/parent_ingest.html`
- **API:** /api/parent/* (Phase 7), /api/parent/verify-pin
- **Tags:** PARENT, SETTINGS, WORD_STATS

---

## Growth Theme (Phase 8)

- **JS:** `js/growth-theme.js`
- **CSS:** embedded in `css/home.css`
- **HTML:** TBD (Phase 8)
- **API:** GET /api/growth/theme, POST /api/growth/theme/advance
- **Images:** `img/themes/{space,tree,city,animal,ocean}/step_{0-5}_v{1-3}.svg`
- **Tags:** GROWTH_THEME, THEME

---

## Quick Search

```bash
# Find all components for a screen
grep -A 5 "Home Dashboard" frontend/COMPONENT_MAP.md

# Find CSS class usage
grep -r "class-name" frontend/static/js/
grep -r "class-name" frontend/templates/

# Find API calls in frontend
grep -r "/api/xp" frontend/static/js/

# Find by tag
grep -r "@tag XP" frontend/static/js/
grep -r "@tag XP" backend/
```
