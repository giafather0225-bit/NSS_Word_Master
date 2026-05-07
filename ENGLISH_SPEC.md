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
