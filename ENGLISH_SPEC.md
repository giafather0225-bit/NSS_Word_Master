# ENGLISH_SPEC.md — v0.2
> Project: NSS Word Master — English G3 Module
> Last Updated: 2026-05-06
> Owner: 아빠(Code/Deploy) + 엄마(Daily Operation/Observation)
> Target Learner: C (G3, 9세, 미국 원어민)
> Status: 섹션 1~3 확정 / 섹션 4~6 작성 중

---

## 섹션 1. Overview

### 1.1 학습자 프로파일

- 미국 거주 G3 원어민, 약 9세 (호칭: C)
- Tier 1 해독 완료
- 학습 집중 영역: CKLA 커리큘럼 흐름을 따름 (별도 집중 영역 명시 안 함)

### 1.2 사용 시기

- 여름방학 (6/20~8/10, 52일): G3 예습용
- 학기 중: 복습용

### 1.3 P0 원칙

- 검증 안 된 콘텐츠는 C에게 노출 금지
- 버그 있는 채로 릴리즈 금지

### 1.4 6/19 릴리즈 범위

**포함:**
- CKLA 11개 도메인 (D1~D11)
- Daily Words G3 (200단어, 7일 사이클)
- Grammar 11개 유닛
- Morphology 11개 유닛
- 기존 SM-2 단어, 뱃지, 도메인 테스트, 최종 테스트

**제외:**
- Spelling — 가을 추가 예정, 탭은 "가을에 추가됩니다" 안내 표시
- Writing W.3.1 — 제거 확정

### 1.5 커리큘럼 프레임

- CKLA = 메인 커리큘럼 (학습 골격)
- CCSS = 학습 목표 (RL.3.x, RI.3.x, L.3.x 등)
- 보강 자료 = CKLA가 CCSS를 못 채우는 부분을 권위 출처에서 보충

### 1.6 성공 지표

| 지표 | 기준 |
|---|---|
| 어휘 기억 | SM-2 기반, 학습 후 90일 시점 정답률 80% 이상 |
| CKLA 도메인 완료 | 도메인 최종 테스트 80% 이상 |
| CCSS 코드별 통과 | 해당 코드 문제를 5문제 이상 풀었을 때 정답률 80% 이상 |
| 자동 검증 | 1,400문항 중 90% 이상 자동 통과 + 전체 1,400문항 개발자 직접 검토 (정답 정확성 + CCSS 코드 매핑 확인) |

> 자동 검증은 1차 필터로 의심 큐 우선순위 분류에 사용. 자동 통과 여부와 무관하게 전체 개발자 검토 필수.

---

## 섹션 2. Tech Stack & Existing Infra

### 2.1 기술 스택

- **백엔드:** Python 3 + FastAPI, SQLite WAL (`~/NSS_Learning/database/voca.db`), SQLAlchemy
- **AI:** Ollama gemma2:2b (C Mac Air M1 8GB 제약), Gemini-1.5-flash 유료 (CKLA 단답 채점만)
- **TTS:** edge-tts + macOS say
- **프론트엔드:** child.html SPA, bundle-a.min.js, theme.css

### 2.2 환경 구성

| 환경 | 사양 | 역할 |
|---|---|---|
| 개발자 MacBook M5 24GB | 개발/빌드 | 코드 작성 + push |
| C Mac Air M1 8GB | 배포/운영 중 | 실제 학습 환경 |

- 전달 통로: GitHub (개발자 push → C pull, 자동/수동)
- 6/19 코드 프리즈 = 그날 이후 GitHub push 중단

### 2.3 기존 인프라 (2026-05-06 스캔 결과)

**라우터:**
- `routers/ckla.py` — 20 endpoints, grade-aware (G3)
- `routers/us_academy.py` — 10 endpoints, SM-2 단어 학습
- `routers/daily_words.py` — Daily Words API

**서비스:**
- `services/ckla_grader.py` — Ollama → Gemini fallback, 0/1/2 채점
- `services/daily_words_engine.py` — 7일 사이클, 학년 자동 진급

**모델:** `models/ckla.py` — 11개 ORM 테이블
(CKLADomain, CKLALesson, CKLAQuestion, CKLAWordLesson, CKLALessonProgress, CKLAQuestionResponse, CKLABadge, CKLAUserBadge, CKLASpelling, CKLAGrammar, CKLAMorphology)

**데이터:**
- `data/academy/ckla_g3/D1~D11.json` — ≈1.4MB, 154 레슨, ~1,400 Q
- `backend/data/daily_words/grade_3.json` — 200 words

**스크립트:**

| 파일 | 역할 |
|---|---|
| `scripts/import_ckla.py` | JSON → DB import (idempotent) |
| `scripts/enrich_mw.py` | MW Elementary API로 단어 정의·발음·예문 보강 |
| `scripts/enrich_missing.py` | MW 미등재 단어를 형태소 분석(NLTK) + WordNet 폴백으로 보완 |
| `scripts/ckla_parser.py` | CKLA Teacher Anthology PDF 파싱 |
| `scripts/parse_amplify_grammar.py` | Grammar/Morphology 토픽 파싱 (verified_data → JSON export 필요) |
| `scripts/parse_ck_spelling.py` | Spelling PDF 파싱 (가을 사용) |
| `scripts/backfill_g3_content.py` | G3 콘텐츠 누락 필드 일괄 채우기 |

**프론트엔드 JS:**
- `ckla.js`, `ckla-lesson.js`, `ckla-review.js`, `ckla-spelling.js`, `parent-ckla.js`

**프론트엔드 CSS:**
- `ckla.css`

---

## 섹션 3. Cross-Project Boundaries & Security

### 3.1 작업 분리 원칙

1. 영어 전용 파일 작업
2. 수학 전용 파일 작업
3. 공유 인프라 통합 (xp_engine, streak_engine, child.html, models/__init__.py 등)

공유 인프라는 각 파트 완성 후에만 수정. 이 순서로 충돌 자체를 방지하므로 영어/수학 우선순위 별도 명시 안 함.

### 3.2 마이그레이션 번호 예약

| 범위 | 용도 |
|---|---|
| 001~023 | 기사용 (Island 데코 경로까지 완료) |
| **024~029** | **영어 모듈 (이번 작업)** |
| 030~036 | 수학 v2.0 Phase 3~4 |

### 3.3 Git 브랜치 전략

- 마일스톤(M1, M2, ...) 단위로 브랜치 분리
- 각 마일스톤 완료 시 main에 머지
- 문제 발생 시 이전 마일스톤 완료 시점으로 복귀 가능

### 3.4 외부 전송 정책 (β)

**허용:**
- CKLA 단답 채점 Gemini 호출 — passage, question, model_answer, user_answer, rubric만 전송 (PII 제외)
- TTS edge-tts — 단어/문장 텍스트만

**금지:**
- C의 학습 진행 데이터, 일기, 개인 정보

**보안:**
- API 키: `.env` 파일 저장, `.gitignore`로 Git 제외
- 호출 로그: `ai_call_log` 테이블 — 시각, 대상, 전송 데이터 요약, 응답, 성공/실패 기록

### 3.5 백업

- **코드:** GitHub (개발 중 수시 push)
- **학습 데이터:** C Mac Air 로컬 자동 백업 (외부 전송 금지)
- **주기:** 매일 자동 (cron)
- **보관 일수:** 구현 시 결정 (기본값 7일 검토)

### 3.6 복구 스크립트

| 스크립트 | 용도 | 실행자 |
|---|---|---|
| `scripts/rollback_migration.py` | 마이그레이션 실패 시 이전 DB 상태 복구 | 개발자 |
| `scripts/restore_from_backup.sh` | 백업 폴더에서 1-click DB 복구 | 개발자 부재 시 C 또는 엄마 |

두 스크립트 모두 6/19 코드 프리즈 전 완성 및 테스트 완료 필수.

---

## 섹션 4. Reading-Science Based Pedagogy

### 4.1 설계 기반 (Evidence Base)

이 모듈의 교수법 설계는 아래 네 개 근거 체계를 따른다.

| 근거 | 핵심 주장 | 이 모듈에서의 적용 |
|---|---|---|
| NRP (2000) Five Pillars | 읽기 = Phonemic Awareness + Phonics + Fluency + Vocabulary + Comprehension | C는 처음 두 항목 완료 → Fluency·Vocabulary·Comprehension 집중 |
| Beck & McKeown (2002) | Tier 2 어휘가 학업 성취의 핵심 레버 | CKLA vocabulary + Daily Words = Tier 2 중심 선정 |
| Hattie (2009) Meta-Analysis | 형성평가(d=0.73), 피드백(d=0.75), 인출 연습(d=0.67)이 고효과 전략 | SM-2 인출 연습, Q&A 즉시 피드백, 도메인 테스트 |
| IES Practice Guide (2010) | 읽기 이해: 배경지식 활성화 + 추론 질문 + 독해 전략 명시적 교수 | CKLA 도메인 지식 축적 구조, Q&A 3분류(Literal·Inferential·Evaluative) |

### 4.2 NRP Five Pillars — C 적용 매핑

| Pillar | C 상태 | 모듈 처리 |
|---|---|---|
| Phonemic Awareness | 완료 | 다루지 않음 |
| Phonics | 완료 | 다루지 않음 |
| Fluency | 진행 중 | Read 탭 TTS + 문단별 하이라이트로 모델링 제공 |
| Vocabulary | 집중 영역 | CKLA Words 탭 + Daily Words G3 + SM-2 복습 |
| Comprehension | 집중 영역 | Q&A 탭 (Literal·Inferential·Evaluative 3분류) |

> Spelling은 Fluency 범주에 속하나 6/19 release에서 제외 (데이터 미완성). 가을 추가 시 Fluency Pillar 보강.

### 4.3 Tier 2 어휘 선정 원칙 (Beck & McKeown)

**Tier 2 선정 기준 (세 가지 모두 충족):**
1. 여러 도메인에 걸쳐 반복 출현 (domain-general)
2. 교사 없이 스스로 쓸 수 있는 생산적 어휘
3. G3 학교 지문에서 실제 마주칠 빈도

**적용:**
- CKLA D1~D11 vocabulary: 각 레슨의 정의·예문이 Tier 2 기준으로 큐레이션된 CKLA 원본 데이터 사용
- Daily Words G3 (200단어): MW Elementary 기반 정의, 4개 주제 그룹으로 구성 (섹션 5에서 상세)
- Tier 1 (일상어) / Tier 3 (전문 기술 용어)는 자동 필터링 안 함 — CKLA 커리큘럼이 이미 선별한 단어 목록 그대로 사용

### 4.4 Q&A 3분류 설계 (IES + Bloom)

| 유형 | 정의 | CKLA 출제 비율 | Bloom 레벨 |
|---|---|---|---|
| Literal | 본문에 명시적으로 있는 정보 | 40% | Remember / Understand |
| Inferential | 본문 단서 + 배경지식 연결 | 40% | Analyze / Evaluate |
| Evaluative | 주제·가치·저자 의도 판단 | 20% | Evaluate / Create |

**채점 기준 (ckla_grader.py):**
- Score 2: 정확하고 완전한 답변
- Score 1: 방향은 맞으나 불완전
- Score 0: 오답 또는 무응답

**피드백 방식:** Socratic — 정답을 직접 알려주지 않고 본문의 어느 부분을 다시 읽으면 도움이 되는지 안내. 1회 재시도 허용.

**외부 AI 사용:** Ollama gemma2:2b 우선 → 실패 시 Gemini-1.5-flash 유료 폴백. 개인정보 없이 passage + question + answer만 전송 (섹션 3.4 β 정책).

### 4.5 인출 연습 설계 (Hattie + Cognitive Science)

**SM-2 알고리즘 적용 대상:**
- CKLA Words 탭 어휘 퀴즈 결과
- Daily Words G3 주간 테스트 결과

**간격 반복 원칙:**
- 정답: 간격 늘림 (2일 → 7일 → 14일 → 30일)
- 오답: 간격 초기화 후 짧은 간격 재학습
- 목표: 학습 후 90일 시점 정답률 80% (섹션 1.6 성공 지표)

**인출 강도 설계:**
- Words 탭: 4지선다 (인식 수준)
- Word Work 탭: 자유 타이핑 (인출 수준) — 힌트 유사도 80% 이상이면 오답 처리
- Daily Words: Day 1 진단(70문항) → Day 2-6 학습 → Day 7 주간 테스트 (90% 통과 기준)

### 4.6 형성평가 구조 (Hattie d=0.73)

| 평가 시점 | 형태 | 피드백 속도 |
|---|---|---|
| 레슨 내 | Words 퀴즈 (3문항) | 즉시 |
| 레슨 내 | Q&A 5문항 + 1회 재시도 | 즉시 (Socratic) |
| 레슨 내 | Word Work 자유 타이핑 | 즉시 (유사도 점수) |
| 도메인 완료 후 | Domain Test (10문항, 80% 기준) | 즉시 |
| 전체 완료 후 | Grade Final Test (27문항, 80% 기준) | 즉시 |
| 매일 | Daily Words 주간 사이클 | 주 1회 (Day 7) |

### 4.7 배경지식 축적 설계 (Knowledge-Rich Curriculum)

CKLA의 핵심 원칙은 **지식 축적형 커리큘럼**이다. 단순 독해 기술 훈련이 아니라 11개 도메인(고전·동물·인체·로마·빛·바이킹·천문·원주민·탐험·식민지·생태)을 통해 배경지식 자체를 쌓는다.

**앱 설계에서의 반영:**
- 도메인 완료 순서: 자유 선택 허용 (순서 강제 없음)
- 도메인 간 어휘 연결: Daily Words 4개 주제 그룹이 CKLA 도메인과 주제적으로 겹치도록 설계
- 지식 누적 가시화: 도메인 완료 배지 11개 — 지식 지형도처럼 표시
