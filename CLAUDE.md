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

**현재 적용된 토큰 (2026-04 Pinterest Schoolgirl Diary — Palette B):**

컨셉: warm cream page + milk-tea pastel 6-section palette. Stationery 느낌 (soft shadow, 둥근 radius, Nunito/Quicksand/Caveat 조합). Brand anchor = Diary Pink `#E09AAE`.

```css
:root {
  /* ═══ Section palette (B — Pinterest Schoolgirl) ═══ */
  /* 각 섹션 5-tone: primary · hover · light(배경) · soft(중간) · ink(짙은 텍스트) */

  --english-primary: #7FA8CC; --english-light: #EEF4FA; --english-ink: #345A80;  /* Baby Blue */
  --math-primary:    #8AC4A8; --math-light:    #EEF7F2; --math-ink:    #3A6A54;  /* Fresh Mint */
  --diary-primary:   #E09AAE; --diary-light:   #FBEEF2; --diary-ink:   #84425A;  /* Sweet Pink */
  --arcade-primary:  #EEC770; --arcade-light:  #FBF3DE; --arcade-ink:  #7A5A1E;  /* Butter */
  --rewards-primary: #B8A4DC; --rewards-light: #F2ECFA; --rewards-ink: #5A4883;  /* Lavender */
  --review-primary:  #EBA98C; --review-light:  #FBEBE0; --review-ink:  #844A30;  /* Peach */

  /* Brand alias — Diary Pink */
  --color-primary:       var(--diary-primary);
  --color-primary-hover: var(--diary-hover);
  --color-primary-light: var(--diary-light);
  --color-primary-glow:  rgba(224, 154, 174, 0.22);

  /* Warm cream neutrals */
  --bg-page:    #FAF6EF;
  --bg-card:    #FFFFFF;
  --bg-sidebar: #F4EEE4;
  --bg-surface: #EFE8DB;

  /* Text (warm dark) */
  --text-primary:   #2B2722;
  --text-secondary: #706659;
  --text-hint:      #A79A89;

  /* Borders */
  --border-default: #DCD2C2;
  --border-subtle:  #EBE3D5;
  --border-card:    rgba(43, 39, 34, 0.06);

  /* Shadows — soft stationery (border-only 규칙 폐기) */
  --shadow-soft:  0 2px 10px rgba(120, 90, 60, 0.06);
  --shadow-modal: 0 10px 30px rgba(90, 65, 40, 0.12);

  /* Radius — 넉넉한 둥글기 */
  --radius-sm: 8px; --radius-md: 12px; --radius-lg: 16px;
  --radius-xl: 20px; --radius-2xl: 28px; --radius-full: 9999px;

  /* Sidebar */
  --sidebar-width: 232px;

  /* Fonts (Google Fonts 로드 필수) */
  --font-family:         'Nunito', -apple-system, sans-serif;     /* body */
  --font-family-display: 'Quicksand', 'Nunito', sans-serif;        /* 헤드라인/카드 타이틀 */
  --font-family-hand:    'Caveat', cursive;                        /* 손글씨 액센트 */

  --font-size-xs: 12px; --font-size-sm: 14px; --font-size-md: 16px;
  --font-size-lg: 18px; --font-size-xl: 24px; --font-size-2xl: 32px; --font-size-3xl: 44px;

  /* Motion */
  --transition-fast: 0.12s ease; --transition-normal: 0.18s ease; --transition-slow: 0.3s ease;
}
```

**규칙**
- 컴포넌트 CSS에서 hex 직접 금지 — `var(--token)`만 사용
- 아이콘: Lucide (이모지 금지)
- 헤드라인(`.h1` ~ `.h3`)은 Quicksand 자동 적용 + `letter-spacing: -0.02em`
- UPPERCASE 라벨은 `letter-spacing: 0.08em`, weight 700, 10.5~11px
- 카드 기본: `bg-card + border-subtle + radius-xl(20px) + shadow-soft`
- 아이콘: Lucide (`<i data-lucide="아이콘명" width="16" height="16">`) — 이모지 절대 금지
- 아이콘 초기화: JS에서 `lucide.createIcons()` 호출 필요

### Email HTML Palette (CSS variables 불가 환경용 — hex 직접 사용)

> 이메일 클라이언트는 CSS variables 미지원 → 아래 hex 값을 직접 사용.
> theme.css 전체 토큰의 이메일용 완전 매핑.

#### 배경 / 레이아웃
| 토큰 | hex | 용도 |
|------|-----|------|
| `--bg-page` | `#FAF6EF` | 이메일 전체 배경 (warm cream) |
| `--bg-card` | `#FFFFFF` | 카드 / 섹션 박스 배경 |
| `--bg-surface` | `#EFE8DB` | 구분선 배경, 인용 박스 |
| `--bg-sidebar` | `#F4EEE4` | 사이드 컬럼, 서브 섹션 배경 |

#### 텍스트
| 토큰 | hex | 용도 |
|------|-----|------|
| `--text-primary` | `#2B2722` | 본문 메인 텍스트 |
| `--text-secondary` | `#706659` | 보조 설명, 라벨 |
| `--text-hint` | `#A79A89` | 날짜, 캡션, 힌트 텍스트 |
| `--text-on-primary` | `#FFFFFF` | 색상 배경 위 텍스트 (버튼 등) |

#### 보더
| 토큰 | hex | 용도 |
|------|-----|------|
| `--border-default` | `#DCD2C2` | 카드 테두리, 구분선 |
| `--border-subtle` | `#EBE3D5` | 연한 구분선 |

#### 섹션 팔레트 (6 sections)
| 섹션 | primary | light (배경) | soft (중간) | ink (진한 텍스트) |
|------|---------|-------------|------------|-----------------|
| English (Baby Blue) | `#7FA8CC` | `#EEF4FA` | `#CFE0EE` | `#345A80` |
| Math (Fresh Mint) | `#8AC4A8` | `#EEF7F2` | `#CFE6D9` | `#3A6A54` |
| Diary (Sweet Pink) | `#E09AAE` | `#FBEEF2` | `#F3D2DC` | `#84425A` |
| Arcade (Butter) | `#EEC770` | `#FBF3DE` | `#F1DCA5` | `#7A5A1E` |
| Rewards (Lavender) | `#B8A4DC` | `#F2ECFA` | `#DCCFEE` | `#5A4883` |
| Review (Peach) | `#EBA98C` | `#FBEBE0` | `#F4D2BE` | `#844A30` |

#### 상태 색상
| 토큰 | hex | 용도 |
|------|-----|------|
| `--color-success` | `#8FBF87` | 정답, 완료, 달성 |
| `--color-success-light` | `#E8F5E4` | 성공 배경 tint |
| `--color-success-ink` | `#4E7A46` | 성공 텍스트 |
| `--color-error` | `#D97A7A` | 오답, 경고, 실패 |
| `--color-error-light` | `#FAEAEA` | 오류 배경 tint |
| `--color-error-ink` | `#8A4538` | 오류 텍스트 |
| `--color-warning` | `#EEC770` | 주의, 취약 단어 |
| `--color-warning-light` | `#FBF3DE` | 경고 배경 tint |
| `--color-info` | `#7FA8CC` | 정보 (= English primary) |
| `--color-info-light` | `#EEF4FA` | 정보 배경 tint |

#### 브랜드 / 앱 앵커
| 토큰 | hex | 용도 |
|------|-----|------|
| `--color-primary` (Diary Pink) | `#E09AAE` | 앱 브랜드 컬러, CTA 버튼 |
| `--color-secondary` (Arcade Butter) | `#EEC770` | XP, 게이미피케이션 강조 |
| `--color-accent` (Lavender) | `#B8A4DC` | Shop, 프리미엄 강조 |

#### 이메일 전용 스타일 가이드
- **섀도우**: `box-shadow: 0 2px 8px rgba(120, 90, 60, 0.08)` (--shadow-soft 대체)
- **카드 보더**: `border: 1px solid #DCD2C2; border-radius: 16px`
- **섹션 구분**: 왼쪽 4px 컬러 바 사용 (English=`#7FA8CC`, Math=`#8AC4A8` 등)
- **폰트**: `font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif`
- **이모지 금지**: 섹션 아이콘 대신 컬러 바 또는 컬러 도트(●) 사용
- **최대 너비**: 600px (이메일 클라이언트 표준)

---

## Dark Mode 토큰 (준비됨 — UI 토글 미구현)

Warm dark(브라운 베이스 + 파스텔 액센트). 동일 6-section 구조 유지.

```css
[data-theme="dark"] {
  --bg-page: #201C18; --bg-card: #2C2822; --bg-sidebar: #25211C; --bg-surface: #352F28;
  --text-primary: #F6F0E4; --text-secondary: #CABFAD; --text-hint: #8C8070;
  --border-default: #3E362D; --border-subtle: #2F2A24; --border-card: rgba(255, 248, 232, 0.06);

  /* 섹션 tone 다크 변형 */
  --english-light: #1E2A36; --math-light:    #1F2E26; --diary-light:   #33212A;
  --arcade-light:  #33291A; --rewards-light: #2A2436; --review-light:  #33261D;

  --english-primary: #9AC1E0; --math-primary:    #A4D7BF; --diary-primary:   #EDB1C2;
  --arcade-primary:  #F2D489; --rewards-primary: #CDBCE8; --review-primary:  #F2BFA4;

  --color-success: #9BCF94; --color-error: #E48C8C; --color-warning: #F2D489;
  --shadow-soft: 0 2px 12px rgba(0, 0, 0, 0.3); --shadow-modal: 0 14px 34px rgba(0, 0, 0, 0.5);
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
