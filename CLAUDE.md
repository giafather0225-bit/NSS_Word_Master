# GIA Learning App — Project Spec (CLAUDE.md)
> Last updated: 2026-04 | 실제 현황 기준으로 전면 재작성

## Overview
- **Product**: 9세 여아(Gia)를 위한 AI 학습 앱 — English vocabulary, Math Academy, Diary, Arcade
- **GitHub**: https://github.com/giafather0225-bit/NSS_Word_Master
- **Working directory**: `/Users/markjhlee/Documents/GitHub/NSS_Word_Master`
- **DB**: `~/NSS_Learning/database/voca.db` (SQLite WAL)
- **Server**: `python3 app.py` → http://localhost:8000

---

## Tech Stack
- **Backend**: Python / FastAPI (`backend/routers/` — 40+ routers)
- **Frontend**: HTML + CSS + Vanilla JS (no bundler, no framework)
- **Database**: SQLite WAL
- **AI**: Ollama (`gemma2:2b`, local) → Gemini fallback (`GEMINI_API_KEY`)
- **TTS**: edge-tts → BytesIO in-memory (no temp files)
- **Speech**: Web Speech API (browser)
- **Icons**: Lucide (CDN, stroke-width 1.5) — emoji 사용 금지

---

## Work Principles (MUST FOLLOW)

1. 수정 전 반드시 기존 코드 읽기. 기존 기능 절대 파괴 금지.
2. 파일당 최대 300줄. 초과 시 모듈 분리.
3. CSS: `theme.css` 변수만 사용. 하드코딩 hex 금지.
4. 모든 API: 적절한 에러 핸들링 + HTTP 상태코드.
5. DB 스키마 변경: `backend/migrations/`에 idempotent 마이그레이션 작성.
6. Python: type hints + docstrings. JS: JSDoc `@tag` comments.
7. async/await 일관성. N+1 쿼리 금지.
8. 모든 사용자 입력 sanitize. SQL injection / XSS / prompt injection 방어.
9. 변경 후 스모크 테스트: 5-Stage 학습, Review, Final Test, Unit Test, Word Manager.
10. UI 텍스트: 영어만. 이모지 사용 금지 (Lucide 아이콘으로 대체).
11. class/ID 변경 시 모든 참조 동시 업데이트.
12. 응답 마지막에 수정된 파일 목록 기재.

---

## Design System (theme.css — single source of truth)

**현재 적용된 토큰 (2026-04 Apple Soft Study 재설계):**

```css
:root {
  /* Primary — Apple Blue (기능 요소 전용: 버튼, 링크, 활성 상태) */
  --color-primary:       #0A84FF;
  --color-primary-hover: #0070E0;
  --color-primary-light: rgba(10, 132, 255, 0.08);
  --color-primary-glow:  rgba(10, 132, 255, 0.15);

  /* Subtle Accents — 점·선·뱃지 전용 (면적 <10% 규칙) */
  --color-lilac:      #CDBDFF;  /* Diary / 완료 뱃지 */
  --color-lilac-light:#F0ECFF;
  --color-pink:       #E8CFE0;  /* 개인화 포인트 */
  --color-pink-light: #F8F0F5;
  --color-mint:       #CFE9E2;  /* Math / 긍정 피드백 */
  --color-mint-light: #EBF7F4;
  --color-peach:      #FFDAB9;
  --color-peach-light:#FFF5EC;

  /* 섹션 컬러 — 아이콘 색 + 4px vertical line 전용 */
  --section-english-color: var(--color-primary);  /* Blue */
  --section-diary-color:   var(--color-lilac);    /* Lilac */
  --section-math-color:    var(--color-mint);     /* Mint */

  /* 배경 */
  --bg-page:    #F5F5F7;
  --bg-card:    #FFFFFF;
  --bg-sidebar: #F2F2F5;
  --bg-surface: #ECECF1;

  /* 텍스트 */
  --text-primary:   #111111;
  --text-secondary: #5C5C66;
  --text-hint:      #8E8E98;

  /* 테두리 */
  --border-default: #D9D9E0;
  --border-subtle:  #ECECF1;
  --border-card:    rgba(0, 0, 0, 0.05);

  /* 그림자 — 최소화, border 우선 */
  --shadow-card:  0 0 0 1px var(--border-card);
  --shadow-modal: 0 8px 24px rgba(0, 0, 0, 0.08);

  /* Radius */
  --radius-sm:   6px;
  --radius-md:   10px;
  --radius-lg:   12px;
  --radius-xl:   16px;
  --radius-full: 9999px;

  /* Progress (Apple Fitness 스타일) */
  --progress-bar-height: 2px;
  --progress-bar-height-lg: 6px;

  /* Sidebar */
  --sidebar-width: 240px;

  /* 폰트 */
  --font-family:        -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  --font-size-xs: 12px; --font-size-sm: 14px;
  --font-size-md: 16px; --font-size-lg: 18px;
  --font-size-xl: 24px; --font-size-2xl: 32px;
  --font-weight-normal: 400; --font-weight-medium: 500;
  --font-weight-bold: 600;   --font-weight-extra: 700;

  /* 애니메이션 */
  --transition-fast:   0.12s ease;
  --transition-normal: 0.18s ease;
  --transition-slow:   0.3s ease;
}
```

---

## Dark Mode 토큰 (준비됨 — UI 토글 미구현)

```css
[data-theme="dark"] {
  --bg-page:    #1C1C1E;
  --bg-card:    #2C2C2E;
  --bg-sidebar: #232326;
  --bg-surface: #343438;

  --text-primary:   #F5F5F7;
  --text-secondary: #C7C7CC;
  --text-hint:      #8E8E93;

  --border-default: #3A3A3C;
  --border-subtle:  #2F2F33;
  --border-card:    rgba(255, 255, 255, 0.06);

  --color-primary-light: #123A63;
  --color-lilac-light:   #2A2547;
  --color-mint-light:    #1A2E2B;
  --color-pink-light:    #2E2030;

  --color-success: #32D74B;
  --color-error:   #FF6961;
  --color-warning: #FFD60A;

  --color-lilac: #B8A7FF;
  --color-mint:  #9BCFC3;
  --color-pink:  #CFAFC3;

  --shadow-card:  0 0 0 1px var(--border-card);
  --shadow-modal: 0 8px 24px rgba(0, 0, 0, 0.32);

  --overlay-scrim: rgba(0, 0, 0, 0.6);
}
```

---

## Learning Flow

```
Home Dashboard → English → Lesson Select
→ Preview (Step 1) → Word Match (Step 2) → Fill Blank (Step 3)
→ Spelling (Step 4) → Make Sentence (Step 5) → Final Test → Complete
```

### Step Specs

**Step 1 — Preview**
4×5 card grid. Click → popup modal.
- POS pill → Word (32px 700) → Definition → Example (italic)
- Listen (TTS) → Shadow ×2 (mic → Web Speech → ≥80%) → Spell ×2
- Sentence Reading ×2 (TTS → mic → ≥90%)

**Step 2 — Word Match**
7 words/round, 두 컬럼. word ↔ definition 매칭.
- Selected: `--color-primary` border+bg
- Matched: `--color-success` + opacity 0.6
- Wrong: shake 0.3s

**Step 3 — Fill the Blank**
문장 빈칸 + word tag pills. 정답 선택.
- Correct: `--color-success` / Wrong: `--color-error` + shake

**Step 4 — Spelling Master**
Wordle 스타일 48×48px 박스. 3 passes (hint→첫글자→blank). Wrong → retryQueue (전부 클리어 후 진행).

**Step 5 — Make a Sentence**
Stage 1: drag-and-drop word scramble. Stage 2: free writing → AI 채점 (grammar+spelling, Ollama→Gemini fallback).

**Final Test**
MC 20 + Fill-in 20. 30분 타이머. 합격 = 90%. 합격 → XP +10 + GrowthEvent("lesson_pass"). 불합격 → 재학습 필요. 재시도 합격 → XP +10.

---

## XP Rules

| Action | XP | Limit |
|---|---|---|
| Word correct | +1 | per attempt |
| Stage complete | +2 | once/stage/lesson |
| Final Test pass | +10 | once; retry = +10 |
| Unit Test pass | +5 | once |
| Daily Words complete | +5 | once/day |
| Weekly Test pass | +10 | once/week |
| Review complete | +2 | once/day |
| Daily Journal | +10 | once/day |
| Must Do all | +5 | once/day |
| All tasks complete | +15 | once/day |
| 7-day streak | +30 | per occurrence |
| 30-day streak | +200 | per occurrence |
| Arcade round | +1/+2/+3 | 500/1000/2000점; daily cap +10 |
| Math Kangaroo complete | +5 | per set |
| Math Kangaroo ≥80% | +5 | per set |
| Math Kangaroo perfect | +10 | per set |

No XP: 테스트 실패, 실패 후 재학습.

---

## Streak Rules
- Review 가능한 날: Review + Daily Words → streak 유지
- Review 없는 날: Daily Words만 → streak 유지
- 승인된 Day Off → streak 동결 (유지)

---

## Diary Sections

| 섹션 | 설명 | 상태 |
|---|---|---|
| Today | 대시보드 (stats 4개 + week calendar + milestones) | ✅ 2026-04 신규 |
| Daily Journal | 글쓰기 + AI feedback (2-column layout) | ✅ |
| Free Writing | 자유 글쓰기 | ✅ |
| My Sentences | Step 5 문장 모음, 2주 경과 → Rewrite 프롬프트 | ✅ |
| My Worlds | 완료한 Growth Theme 컬렉션 | ✅ |
| Growth Timeline | GrowthEvent 로그 (역순) | ✅ |
| Calendar | 월간 뷰 (🔥⬜🏖️📝✅ 마커) | ✅ |
| Day Off | 사유 폼 → 부모 이메일 → pending/approved/denied | ✅ |

---

## Reward Shop
기본 아이템: YouTube 30분(300), Roblox 30분(300), Family Movie(500), Dinner Out(500), Custom Reward(300).

구매 플로우: 카드 클릭 → 확인 팝업 → XP 차감 → PurchasedReward 생성.
사용 플로우: My Rewards → [Use] → 4자리 PIN → is_used=True.

---

## Parent Dashboard
접근: Home 배너 "···" → 4자리 PIN.
섹션: Overview, Word Stats, Shop Management, Task Settings, Academy Schedule, Day Off Requests, Notifications, Change PIN, Add Textbook.

---

## Math Module

### Math Academy
- G4 완성, G3 일부 완성
- CPA 방식 (Concrete → Pictorial → Abstract)
- routers: `math_academy.py`, `math_daily.py`, `math_fluency.py`, `math_glossary.py`, `math_placement.py`, `math_problems.py`

### Math Kangaroo
- 100+ sets (IKMC 2012-2023, Lebanon, India KSF, USA 2003-2025)
- 레벨: Pre-Ecolier(1-2), Ecolier(3-4), Benjamin(5-6)
- 모드: Practice (즉시 채점) / Test (타이머 + 전체 채점)
- XP: complete +5, ≥80% +5, perfect +10

---

## Arcade

| 게임 | 파일 |
|---|---|
| Word Invaders | `arcade-word-invaders.js` |
| Spell Rush | `arcade-spell-rush.js` |
| Definition Match | `arcade-definition-match.js` |
| Crossword | `arcade-crossword.js` |
| Sudoku | `arcade-sudoku.js` |
| Make 24 | `arcade-make24.js` |
| Math Invaders | `arcade-math-invaders.js` |

허브 화면은 calm (배경 = `bg-page`, 카드만 표시). 게임 진입 후 내부에서만 에너지 허용.

---

## CKLA Academy
- CKLA Grade 3 읽기 교재 기반
- 탭: Read / Words / Q&A / Word Work
- 아티클 텍스트: `_parsePassage()` 로 PDF 줄바꿈 처리 (산문 렌더링)
- routers: `ckla.py`, `ckla_review.py`
- frontend: `ckla.js`, `ckla-lesson.js`, `ckla.css`

---

## AI Assistant (Shadow)
학습 중 실시간 도움 패널
- STT: `ai-assistant-stt.js` (Web Speech API)
- TTS: `ai-assistant-tts.js` (edge-tts)
- routers: `ai_assistant.py`, `ai_assistant_log.py`, `ai_assistant_safety.py`

---

## System

| 기능 | 파일 | 상태 |
|---|---|---|
| Ollama auto-start | `services/ollama_manager.py` | ✅ |
| Auto-backup (7일) | `services/backup_engine.py` | ✅ |
| Offline indicator | `offline-indicator.js` | ✅ |
| Dark mode toggle | 미구현 | 🟡 |
| macOS LaunchAgent | README 참조 | ✅ |

---

## Database Models

### Phase 0 (수정 금지)
Lesson, StudyItem, Progress, Reward, Schedule, UserPracticeSentence, Word, WordReview

### Phase 1 (migration 001)
AppConfig, XPLog, StreakLog, TaskSetting, RewardItem, PurchasedReward, DailyWordsProgress, DiaryEntry, GrowthEvent, DayOffRequest, AcademySession, LearningLog, WordAttempt, AcademySchedule, GrowthThemeProgress

### Math (별도 migration)
MathKangarooProgress, MathAcademySession 등

전체 스키마: `backend/DB_INDEX.md`

---

## Code Annotation Rules

### 파일 헤더 (모든 JS/CSS/Python 파일)

```
/* ================================================================
   [filename] — [한줄 설명]
   Section: [Home / English / Math / Diary / Arcade / Shop / Parent / System]
   Dependencies: [목록]
   API endpoints: [목록 또는 "none"]
   ================================================================ */
```

### 함수 태그

```js
/** @tag XP @tag AWARD */
async function awardXP(action, detail) { ... }
```

### 사용 가능한 태그

```
HOME_DASHBOARD  TODAY_TASKS   REMINDER      AI_COACH      AI_ASSISTANT
SIDEBAR         ACCORDION     NAVIGATION
ENGLISH         ACADEMY       DAILY_WORDS   MY_WORDS      READING
CKLA            COLLOCATION   US_ACADEMY
PREVIEW         SHADOW        SENTENCE_READ SPELL
WORD_MATCH      FILL_BLANK    SPELLING      SENTENCE
FINAL_TEST      UNIT_TEST     WEEKLY_TEST
REVIEW          SM2           ACTIVE_RECALL
DIARY           JOURNAL       FREE_WRITING  MY_SENTENCES
MY_WORLDS       GROWTH_TIMELINE CALENDAR    DAY_OFF
MATH            MATH_ACADEMY  MATH_DAILY    MATH_FLUENCY
MATH_KANGAROO   MATH_GLOSSARY MATH_PLACEMENT MATH_PROBLEMS
ARCADE
XP              STREAK        AWARD         BONUS
SHOP            REWARD        PURCHASE      PIN
PARENT          SETTINGS      WORD_STATS    SCHEDULE      NOTIFICATION
TTS             AI            OLLAMA        GEMINI        OCR
BACKUP          SYSTEM        THEME
```
