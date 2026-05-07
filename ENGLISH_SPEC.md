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
- `data/academy/ckla_g3/D1~D11.json` — ≈1.4MB, **104 레슨**, **819 Q&A + 684 어휘 = 1,503 항목**
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

---

## 섹션 5. Curriculum Structure

### 5.1 CKLA G3 — 11 Domain Map

> 실제 JSON 스캔 기준 (2026-05-07). 도메인 이름은 `grammar_morphology.json` 기준.

| D | Domain Name | Lessons | Q&A | Grammar Topics | Morphology Topics |
|---|---|---|---|---|---|
| 1 | Classic Tales | 12 | 80 | — | — |
| 2 | Classification of Animals | 9 | 57 | nouns & verbs · adjectives & adverbs · compound sentences | suffixes (-ed/-ing) · prefixes (un-/non-) |
| 3 | Human Body: Systems and Senses | 9 | 90 | plural nouns · irregular plural nouns | prefixes (dis-/mis-) |
| 4 | Ancient Roman Civilization | 12 | 92 | verb tenses · irregular verbs | suffixes (-ist/-ian/-y/-al) |
| 5 | Light and Sound | 8 | 56 | adjectives & adverbs · conjunctions | suffixes (-er/-or/-ist/-ian) · suffix (-ly) |
| 6 | The Vikings and Norse Mythology | 8 | 57 | conjunction (because) | suffixes (-ive/-ly) |
| 7 | Astronomy: The Solar System and Beyond | 10 | 92 | conjunction (so) | suffixes (-ful/-less) |
| 8 | Native Americans | 8 | 62 | plural possessive nouns · possessive pronouns | suffixes (-ish/-ness) · suffixes (-able/-ible) |
| 9 | European Exploration of North America | 9 | 76 | linking words · comparative & superlative adj. | prefixes (pro-/anti-) |
| 10 | Colonial America | 12 | 108 | comparative & superlative adverbs | prefixes (uni-/bi-/tri-/multi-) |
| 11 | Ecology | 7 | 49 | subject & object pronouns · conjunctions review | prefix review · end-of-year review |
| | **Total** | **104** | **819** | | |

**어휘 항목:** 684 단어 (전 도메인 합산)  
**C가 답하는 총 항목:** 819 Q&A + 312 vocab quiz (레슨당 3문항 × 104) + 104 Word Work = **약 1,235 문항**  
**섹션 1.6 검토 기준:** 819 Q&A 정확성 + CCSS 코드 매핑 — 개발자 직접 검토 대상

> **주의:** D1 Classic Tales는 Grammar/Morphology 토픽 없음. CKLA 원본 커리큘럼 설계 그대로.

---

### 5.2 CKLA 레슨 구조 (레슨 1개 기준)

각 레슨은 4탭으로 구성. 탭 완료 순서는 자유, 4탭 전부 제출해야 레슨 완료.

| 탭 | 콘텐츠 | 완료 기준 |
|---|---|---|
| **Read** | 지문 + TTS + 문단 하이라이트 + 글자 크기 3단계 | 끝까지 스크롤 |
| **Vocabulary** | 전체 어휘 카드 (정의·예문) → 4지선다 퀴즈 3문항 | 퀴즈 2/3 통과 |
| **Q&A** | Literal×2 + Inferential×2 + Evaluative×1 (랜덤 5문항) · 1회 재시도 | 5문항 전부 제출 |
| **Word Work** | Focus Word 자유 타이핑 · 힌트 버튼 | 제출 (유사도 80% 미만 = 오답 기록) |

---

### 5.3 CKLA 테스트 구조

**Domain Test** (각 도메인 완료 시 해제)

| 항목 | 내용 |
|---|---|
| 문항 구성 | Vocab 4지선다×3 + 빈칸×2 + Q&A×5 = **10문항** |
| 통과 기준 | 80% (8/10) |
| 재시도 | 즉시 가능 (문항 랜덤 교체) |
| 3회 연속 실패 | Parent Dashboard 경고 |
| XP | +30 |

**Grade Final Test** (11개 도메인 모두 완료 시 해제)

| 항목 | 내용 |
|---|---|
| 문항 구성 | Vocab×15 + Q&A×10 (Literal4+Inferential4+Evaluative2) + WordWork×2 = **27문항** |
| 통과 기준 | 80% (22/27) |
| 재시도 | 24시간 대기 후 재시도 (대기 화면에 틀린 문항 + 복습 버튼) |
| XP | +100 |

---

### 5.4 Daily Words G3 — 13주 사이클

**기본 정보**

| 항목 | 값 |
|---|---|
| 총 단어 수 | 200 단어 |
| 출처 | Flocabulary G3 + Think SRSD Tier 2 G3 |
| 사이클 | 7일 (Day 1 진단 → Day 2-6 학습 → Day 7 주간 테스트) |
| 하루 학습량 | 10단어/일 |
| 총 콜로케이션 | 60개 (Week 12~13) |
| 주간 테스트 통과 기준 | 90% 이상 → 다음 학년 진급 |

**13주 테마 구성**

| Week | Theme | 샘플 어휘 |
|---|---|---|
| 1 | Exploring & Discovering | curious, observe, explore |
| 2 | People & Qualities | brave, clever, loyal |
| 3 | Nature & Environment | habitat, climate, moisture |
| 4 | Actions & Problem Solving | solution, cooperate, communicate |
| 5 | Thinking & Learning | imagine, consider, realize |
| 6 | Feelings & Experiences | fortunate, terrify, thrill |
| 7 | Change & Movement | increase, decrease, replace |
| 8 | Communication & Society | participate, contribute, respond |
| 9 | Strategy & Survival | avoid, defend, protect |
| 10 | Describing & Comparing | ancient, delicate, rare |
| 11 | Daily Life & Actions | perform, schedule, adopt |
| 12 | Collocations & Chunks | make a decision, take a break, pay attention |
| 13 | More Collocations & Expressions | come up with, point out, run out of |

> Week 1~11: 단일 어휘 (Tier 2 중심). Week 12~13: 콜로케이션·관용 표현.  
> 7일 사이클 × 13주 = 91일. 여름방학 52일 안에 Week 1~7 완료, 나머지는 학기 중 연속.

---

### 5.5 Grammar & Morphology — 11 Unit Scope

> 출처: Amplify CKLA G3 Scope and Sequence PDF → `data/ckla_source/grammar_morphology.json`  
> Unit 번호 = Domain 번호 (D1=U1, …, D11=U11).

| Unit | Domain | Grammar | Morphology |
|---|---|---|---|
| 1 | Classic Tales | — | — |
| 2 | Classification of Animals | nouns & verbs · adjectives & adverbs · compound sentences | suffixes (-ed/-ing) · prefixes (un-/non-) |
| 3 | Human Body | plural nouns · irregular plural nouns | prefixes (dis-/mis-) |
| 4 | Ancient Roman Civilization | verb tenses · irregular verbs | suffixes (-ist/-ian/-y/-al) |
| 5 | Light and Sound | adjectives & adverbs · conjunctions | suffixes (-er/-or/-ist/-ian) · suffix (-ly) |
| 6 | Vikings and Norse Mythology | conjunction (because) | suffixes (-ive/-ly) |
| 7 | Astronomy | conjunction (so) | suffixes (-ful/-less) |
| 8 | Native Americans | plural possessive nouns · possessive pronouns | suffixes (-ish/-ness) · suffixes (-able/-ible) |
| 9 | European Exploration | linking words · comparative & superlative adjectives | prefixes (pro-/anti-) |
| 10 | Colonial America | comparative & superlative adverbs | prefixes (uni-/bi-/tri-/multi-) |
| 11 | Ecology | subject & object pronouns · conjunctions review | prefix review · end-of-year review |

**Unit 1 처리:** CKLA 원본에서 Grammar/Morphology 없음. 앱에서 Grammar/Morphology 탭 비활성화 또는 "No Grammar lesson for this domain." 안내 표시.

---

### 5.6 CCSS G3 ELA 코드 매핑 (요약)

> 코드별 문항 배분 상세는 섹션 7 (Content Validation Plan)에서 정의.

| CCSS 영역 | 코드 범위 | 주 커버 탭 |
|---|---|---|
| Reading Literature (RL) | RL.3.1~9 | Q&A (D1·D6·D7 등 문학 도메인) |
| Reading Informational (RI) | RI.3.1~10 | Q&A (D2~D5·D8~D11 등 정보 도메인) |
| Language (L) | L.3.1~6 | Grammar + Morphology + Vocabulary |

**L.3.x 세부 매핑:**

| L 코드 | 내용 | 커버 위치 |
|---|---|---|
| L.3.1a | Noun-verb agreement | Grammar U2~U4 |
| L.3.1b | Regular/irregular plurals | Grammar U3 |
| L.3.1c | Abstract nouns | Grammar U2 |
| L.3.1d | Verb tenses | Grammar U4 |
| L.3.1e | Compound/complex sentences | Grammar U2 |
| L.3.1f | Adjectives and adverbs | Grammar U2, U5 |
| L.3.1g | Conjunctions | Grammar U5~U7, U11 |
| L.3.1h | Commas in compound sentences | **보강 자료 필요** |
| L.3.1i | Capitalization/punctuation | **보강 자료 필요** |
| L.3.2 | Spelling conventions | **제외 (가을)** |
| L.3.4 | Context clues for word meaning | Vocabulary + Q&A |
| L.3.4b | Affixes and roots | Morphology U2~U11 |
| L.3.4c | Root word meaning | Morphology U2~U11 |
| L.3.5 | Word relationships, nuances | Word Work + Vocabulary |
| L.3.6 | Tier 2 academic vocabulary | Daily Words + CKLA Vocabulary |

> L.3.1h·L.3.1i: CKLA 커버 없음 → 보강 자료 출처를 섹션 7에서 결정.

---

## Section 6 — Lesson Flow (구현 기준)

> 이 섹션은 실제 소스 코드(`ckla.js`, `ckla-lesson.js`, `daily-words.js`, `daily-words-weekly.js`, `ckla-review.js`)를 직접 분석한 구현 기준 문서다. 스펙과 구현이 어긋날 경우 이 섹션이 진실 기준(source of truth).

---

### 6.1 CKLA 레슨 탭 구조 및 잠금 정책

레슨 화면은 **7개 탭**으로 구성된다.

#### 탭 목록

| 탭 ID | 표시명 | 분류 | 초기 잠금 여부 |
|---|---|---|---|
| `reading` | Read | 핵심 | ❌ (항상 열림) |
| `vocab` | Words | 핵심 | ✅ (reading_done까지) |
| `questions` | Q&A | 핵심 | ✅ (reading_done까지) |
| `word-work` | Word Work | 핵심 | ✅ (reading_done까지) |
| `spelling` | Spelling | 참조 | ❌ (항상 열림) |
| `grammar` | Grammar | 참조 | ❌ (항상 열림) |
| `morphology` | Morphology | 참조 | ❌ (항상 열림) |

#### 잠금 해제 트리거

```
POST /api/academy/ckla/lessons/{id}/progress  {reading_done: true}
  → progress.reading_done = true
  → _cklaUpdateTabLocks() 재호출
  → vocab / questions / word-work 탭 잠금 해제
```

- `refTabs = new Set(['spelling', 'grammar', 'morphology'])` — 참조 탭은 잠금 로직에서 완전 제외
- 잠긴 탭 클릭 시: 아무 동작 없음 (클릭 이벤트 무시)

#### 완료 기준 (4탭 모두)

| 탭 | 완료 조건 | 서버 필드 |
|---|---|---|
| Read | "Done Reading" 버튼 클릭 | `reading_done: true` |
| Words | 단어 카드 끝까지 + 퀴즈 ≥ 2/3 정답 | `vocab_done: true` |
| Q&A | 모든 질문 제출 완료 | `questions_attempted` ≥ 전체 문항 수 |
| Word Work | 답안 제출 | `word_work_done: true` |

4탭 전부 완료 → `progress.completed = true` (서버가 자동 설정) → 완료 플로우 진입.

---

### 6.2 핵심 탭별 상세 플로우

#### 6.2.1 Read (읽기) 탭

```
진입
  → 타이머 시작 (서버 측 time_taken 기록)
  → 지문 파싱: _parsePassage()
      - § 마커(§, 섹션 구분자)로 1차 분리
      - >80자 + 문장 종결 기호 + 다음 줄 대문자 → 문단 분리
  → 문단 카드 렌더링 (인덱스 0부터)

사용자 상호작용:
  [문단 클릭 또는 재생 버튼]
    → _cklaReadParagraph(idx)
    → TTS: POST /api/tts/sentence {text, voice:'en-US-AriaNeural', rate:0.85}
    → 해당 문단에 .ckla-para-active 클래스 → 하이라이트
    → 재생 완료 시 다음 문단으로 자동 이동

  [Listen All 버튼]
    → _cklaReadAloud()
    → 전체 지문 순서대로 TTS 연속 재생

  [폰트 크기 버튼: sm / md / lg]
    → localStorage['ckla_font_size'] 에 저장
    → 즉시 적용 (새로고침 없이)

  [Done Reading 버튼]
    → _markReadingDone()
    → POST /api/academy/ckla/lessons/{id}/progress {reading_done: true}
    → 성공 시 → _cklaUpdateTabLocks() → vocab/questions/word-work 잠금 해제
```

**TTS 폴백 체인:** edge-tts (en-US-AriaNeural, rate 0.85) → browser `speechSynthesis` API

---

#### 6.2.2 Words (어휘) 탭

```
진입
  → GET /api/academy/ckla/lessons/{id}  (lesson.words 배열 사용)
  → 단어 카드 브라우저 렌더링
      카드: 단어 / 품사 / 정의 / 예문(example_1) / TTS 버튼
  → "Take Quiz" 버튼: 비활성화 (마지막 카드 도달 전)

카드 탐색:
  → 이전/다음 버튼으로 이동
  → 마지막 카드 도달(atEnd = true) → "Take Quiz (3 questions)" 활성화

[Take Quiz 버튼]
  → _startVocabQuiz()
  → 3문항 순서대로 출제 (단어 → 4개 정의 보기, 1개 정답)
  → 문항 사이: 900ms 자동 딜레이
  → 완료 후 채점:
      pass 기준: 정답 수 ≥ Math.ceil(총 문항 × 2/3)  → 2/3 = 최소 2문항
  → pass: POST /api/academy/ckla/lessons/{id}/progress {vocab_done: true}
  → fail: "Try again" → 퀴즈 재시작 (카드 브라우저 재진입 없이)
```

---

#### 6.2.3 Q&A (질문과 답변) 탭

```
진입
  → GET /api/academy/ckla/lessons/{id}  (lesson.questions 배열)
  → 질문 1개씩 순서대로 표시
  → 각 질문: 종류 배지(Literal / Inferential / Evaluative) + 질문 텍스트 + textarea

[답안 제출]
  → _submitAnswer(questionId)
  → POST /api/academy/ckla/questions/{id}/answer  {user_answer: "..."}
  → 응답: {score: 0|1|2, feedback: "..."}
      score 0 → ✗ (틀림)
      score 1 → △ (부분 정답)
      score 2 → ✓ (정답)
  → 결과 표시 후 → "Next Question" 버튼으로 이동
  → 캐시: _cklaResponses Map에 questionId → {score, feedback} 저장

완료 판정:
  → 별도 "완료" 버튼 없음
  → 서버가 questions_attempted 카운트 추적
  → 전체 질문 제출 완료 → questions_done: true (서버 자동 설정)
```

**AI 채점 로직 (서버측 `services/ckla_grader.py`):**
- Literal: 키워드 매칭 + 의미 유사도
- Inferential/Evaluative: Ollama(gemma2:2b) → Gemini 폴백
- 점수 기준: 0 = 관련 없음, 1 = 부분적으로 정확, 2 = 완전 정확

---

#### 6.2.4 Word Work (단어 활용) 탭

```
진입
  → lesson.word_work_word 필드의 집중 단어 표시
  → textarea: "Write a sentence using this word"

[Hint 버튼 (토글)]
  → 정의(definition) + 예문(example_1) 표시
  → 토글 방식 (열기/닫기)

[제출 버튼]
  → _markWordWorkDone()
  → 유효성 검사: 빈 입력 → 오렌지 테두리 (var(--review-primary)) + 포커스
  → POST /api/academy/ckla/lessons/{id}/progress
        {word_work_done: true, word_work_answer: "사용자 입력"}
  → 서버측 유사도 검증: answer와 힌트(definition) 간 80% 이상 유사도
      → 80% 미만: 오답으로 처리 (완료는 됨, 정확도 기록에만 영향)
  → 완료: word_work_done = true
```

---

### 6.3 참조 탭 (Spelling / Grammar / Morphology)

참조 탭은 잠금 정책에서 제외되며 **레슨 진행과 무관하게 언제든 접근** 가능하다.

#### Unit 1 특수 처리

Unit 1(Classic Tales)은 문법/형태소 내용이 없으므로 참조 탭에서 안내 메시지 표시:

```
"Unit 1 is a review unit — [Spelling / Grammar / Morphology topics] begin in Unit 2."
```

#### Spelling 탭

```
GET /api/academy/ckla/spelling/{unit}
→ {weeks: [{week, pattern, words, challenge_words}]}

표시: 주차별 패턴 카드
  - week: "Week 1" 등
  - pattern: 철자 규칙 설명
  - words: 연습 단어 목록
  - challenge_words: 심화 단어 목록

[Practice 버튼]
  → startSpellingPractice(weekJson, unit)
  → 별도 철자 연습 화면 진입
```

#### Grammar 탭

```
GET /api/academy/ckla/grammar/{unit}
→ {topics: ["nouns and verbs", "adjectives and adverbs", ...]}

표시: 해당 Unit의 문법 주제 목록 (텍스트 리스트)
데이터 소스: data/ckla_source/grammar_morphology.json
```

#### Morphology 탭

```
GET /api/academy/ckla/morphology/{unit}
→ {topics: ["suffixes (-ed and -ing)", "prefixes (un- and non-)", ...]}

표시: 해당 Unit의 형태소 주제 목록 (텍스트 리스트)
데이터 소스: data/ckla_source/grammar_morphology.json
```

---

### 6.4 레슨 완료 플로우

```
progress.completed = true 감지 (4탭 전부 완료 후 서버 응답)
  ↓
_maybeShowDifficultyPrompt(prog) 호출
  ↓
1단계: 완료 축하 버스트 (1.6초)
  → "★ Lesson Complete!" 텍스트 + CSS 애니메이션
  → 1,600ms 후 자동 해제

  ↓
2단계: 난이도 평가 오버레이
  → 3개 버튼: Easy / Just right / Hard
  → 선택 시: POST /api/academy/ckla/lessons/{id}/difficulty  {rating: "easy"|"just_right"|"hard"}
  → 즉시 다음 단계 진행 (서버 응답 대기 없음)

  ↓
3단계: Domain Test 배너 확인
  → _maybeShowDomainTestBanner()
  → 해당 Domain의 모든 레슨 완료 여부 확인
  → 미완료: 배너 미표시, 레슨 목록으로 복귀
  → 완료: "Domain Test Available" 배너 표시
      → [Start Domain Test] 버튼 → openDomainTest(domainId) 호출

XP 지급: +15 (첫 완료만, 서버측 중복 방지)
```

---

### 6.5 Domain Test 플로우

**진입:** Domain의 모든 레슨 완료 후 자동 해제. `openDomainTest(domainId)` 호출.

**구성:** 총 10문항

| 유형 | 문항 수 | 방식 |
|---|---|---|
| vocab_mc | 3 | 정의 → 단어 선택 (A/B/C/D 4지선다) |
| vocab_fill | 2 | 정의 제시 → 단어 직접 입력 (Enter로 제출) |
| Q&A | 5 | 질문 + textarea → AI 채점 |

**채점 및 통과:**

```
POST /api/academy/ckla/domains/{id}/test
  body: {answers: [...], time_taken_seconds: N}
  →응답: {score: N, total: 10, passed: bool, ...}

통과 기준: score ≥ 8 / 10 (80%)
```

**재시도 정책:**
- 실패 시 즉시 재시도 가능 (잠금 없음)
- 3회 연속 실패 시: Parent Dashboard에 경고 플래그 설정

**통과 후:**
- 배지 자동 지급: POST `/api/academy/ckla/badges/check?grade=3` (best-effort)
- XP: +30
- Domain 완료 상태 → 사이드바 배지 업데이트

---

### 6.6 Grade Final Test 플로우

**진입 조건:** 11개 Domain 전부 완료. `showGradeFinalTest()` 호출.

**구성:** 총 27문항

| 유형 | 문항 수 | 방식 |
|---|---|---|
| vocab_mc | 15 | 정의 → 단어 선택 (4지선다) |
| word_work | 2 | 집중 단어 → 문장 작성 |
| Q&A | 10 | Literal×4 + Inferential×4 + Evaluative×2 |

**통과 기준:** score ≥ 22 / 27 (≈ 80%)

**결과 처리:**

```
통과 시:
  → XP +100
  → 배지 "CKLA G3 Master" 지급
  → POST /api/academy/ckla/badges/check?grade=3
  → 축하 화면 표시

실패 시:
  → _cklaRenderFinalTestWait() 호출
  → 24시간 카운트다운 타이머 표시
  → 틀린 문항 목록 + 복습 버튼
  → 24시간 후 재시도 해제 (서버측 잠금)
```

**3회 연속 실패:**
- Parent Dashboard: "G4 강제 해제" 버튼 노출
- 학습 상태: Grade Final Test 대기 화면 유지

---

### 6.7 Daily Words 7일 사이클

**진입:** `GET /api/daily-words/today`

```
응답: {
  cycleDay: 1~7,
  sessionType: "placement"|"study"|"weekly",
  alreadyDoneToday: bool,
  words: [...],
  currentIndex: 0
}
```

**오늘 이미 완료한 경우 (Day 7 제외):**
```
alreadyDoneToday = true && cycleDay !== 7
→ "Done for today! Come back tomorrow." 화면
→ 더 이상 진행 불가
```

#### Day 1 — 진단 퀴즈 (Placement)

```
sessionType = "placement" (cycleDay === 1)
→ _dwRenderPlacementIntro() → 진단 시작

각 단어: MC 퀴즈 (단어 → 정의 보기 4개)
  → 정답: 이미 아는 단어 (복습 필요도 낮음)
  → 오답: 이번 주 집중 단어로 지정

결과: POST /api/daily-words/day1-result
  → {failed_word_ids: [...]} 전송
  → 이 단어들이 Day 2~6 플래시카드 학습 대상
```

#### Day 2~6 — 플래시카드 학습 (Study)

```
sessionType = "study"
→ 플래시카드 브라우저

각 카드:
  앞면: 단어 + TTS 버튼
  뒤면: 정의 + 예문

상태 관리:
  status = 'ok'     → 완료 처리 (다음 카드 자동 이동)
  status = 'auto-pass' → 완료 처리

전체 완료:
  → POST /api/daily-words/complete
  → XP +10
  → "See you tomorrow!" 화면
```

#### Day 7 — 주간 스펠링 테스트 (Weekly Test)

```
sessionType = "weekly" (cycleDay === 7)
→ dwRenderWeeklyIntro()
→ 인트로 화면: "You need 90% to pass and earn +10 XP"

각 문항:
  → 정의 표시 + TTS
  → 사용자가 단어 직접 입력 (스펠링)
  → dwWeeklySubmit() → 채점 → dwWeeklyNext()

결과 (dwFinishWeekly):
  pass 기준: 정답률 ≥ 0.9 (90%)

  통과:
    → POST /api/daily-words/weekly-test/result {passed: true, ...}
    → XP +10
    → 사이클 리셋 (새 단어 세트로 Day 1 재시작)
    → _dwRenderWeeklyResult(correct, total, passed=true, xpAwarded=10, newGrade)

  실패:
    → POST /api/daily-words/weekly-test/result {passed: false, ...}
    → XP 없음
    → 사이클 리셋 (실패해도 새 사이클 시작)
    → 화면: "Score X% — need 90% to pass. New cycle begins now."
```

---

### 6.8 SM-2 Review 플로우

**진입:** `showCKLAReview()` 호출 → `GET /api/academy/ckla/review/due`

```
응답: {words: [{id, word, part_of_speech, definition, audio_url, example_1}, ...]}

words 비어있는 경우:
  → _cklaRenderReviewEmpty() 호출
  → "No words to review today!" 화면
  → "Keep studying lessons — new review words will appear tomorrow."
  → 더 이상 진행 없음
```

**3단계 상태 머신: `prompt` → `result` → (다음 단어로) `prompt` → ... → `summary`**

#### Phase 1: Prompt

```
표시:
  - 단어 (크게)
  - 품사 (있는 경우)
  - 오디오 버튼 (audio_url 있는 경우)
  - 입력 필드: "Type the meaning of this word"
  - 진행 바: N / 총 단어 수 + 현재 정답 수 ✓

버튼:
  [Show Answer] → _cklaRevShowAnswer(): 오답 처리 + result 화면
  [Check]       → _cklaRevCheck(): 답안 검증
  [Enter 키]    → _cklaRevCheck() 동일
```

#### 답안 검증 (_cklaRevMatchAnswer)

퍼지 매칭 로직 (순서대로 적용):

```
1. 정규화: 소문자 변환 + 비영숫자 제거
2. 완전 일치: ua === def → 정답
3. 포함 일치: def.includes(ua) && ua.length > 3 → 정답
4. 키워드 매칭:
   - 정의에서 불용어(stop words) 제외한 핵심 단어 추출
   - 사용자 입력의 단어와 비교 (stem prefix 매칭 포함)
   - 매칭 비율 ≥ 0.4 (40%) → 정답

불용어 예시: a, an, the, is, are, to, of, in, for, and, that, ...
```

#### Phase 2: Result

```
POST /api/academy/ckla/review/result
  body: {word_id: N, is_correct: bool, attempts: N}

표시:
  - 정답: "✓ Correct!" (green, .ckla-review-correct)
  - 오답: "✗ Not quite" (red, .ckla-review-wrong)
  - 정의 표시 (항상)
  - 예문 표시 (example_1, 있는 경우)
  - [Next Word →] 또는 [See Results] 버튼
```

#### Phase 3: Summary

```
모든 단어 완료 시:
  pct = round(correct / total × 100)

  pct ≥ 80: "🌟 Excellent work!"
  pct ≥ 50: "👍 Good effort!"
  pct < 50: "💪 Keep practicing!"

  표시: 정답 수 / 총 단어 수 + 퍼센트 + 메시지
  [Done] 버튼 → hideCKLAView()

XP: 서버측 자동 처리 (UI에 미표시)
```

---

### 6.9 플로우 상태 전환 요약

```
CKLA 메인 화면 (Domain 목록)
  └─→ Domain 선택 → Lesson 목록
        └─→ Lesson 선택 → 레슨 탭 화면
              ├─→ Read 탭 (항상 접근 가능)
              │     └─→ "Done Reading" → vocab/Q&A/Word Work 잠금 해제
              ├─→ Words 탭 (reading_done 후)
              │     └─→ 카드 끝 → 퀴즈 → pass → vocab_done
              ├─→ Q&A 탭 (reading_done 후)
              │     └─→ 전 문항 제출 → questions_done
              ├─→ Word Work 탭 (reading_done 후)
              │     └─→ 답안 제출 → word_work_done
              └─→ [4탭 완료] → progress.completed = true
                    → 1.6s 버스트 → 난이도 평가 → Domain Test 배너 확인

Domain Test (Domain 완료 후 해제)
  └─→ 10문항 → 80% 통과 → 배지 + XP +30
        → 11개 Domain 모두 완료 → Grade Final Test 해제

Grade Final Test
  └─→ 27문항 → 80% 통과 → "CKLA G3 Master" 배지 + XP +100
        → 실패: 24시간 잠금 → 재시도

Daily Words (별도 진입점)
  └─→ Day 1: 진단 퀴즈 → 집중 단어 결정
  └─→ Day 2~6: 플래시카드 → +10 XP
  └─→ Day 7: 스펠링 테스트 → 90% 통과 → +10 XP → 사이클 리셋

SM-2 Review (별도 진입점)
  └─→ due 단어 목록 → prompt → result → (반복) → summary
```

---

## Section 7 — Content Validation Plan

> 이 섹션은 앱이 CCSS G3 ELA Language strand를 실제로 얼마나 커버하는지 검증하고, 미커버 항목의 처리 방침을 결정한다.

---

### 7.1 CCSS L.3 커버리지 최종 판정

| L 코드 | 기준 | 앱 커버 여부 | 커버 위치 | 판정 |
|---|---|---|---|---|
| L.3.1a | Subject-verb agreement | ✅ | Grammar U2~U4 | 커버 |
| L.3.1b | Regular / irregular plurals | ✅ | Grammar U3 | 커버 |
| L.3.1c | Abstract nouns | ✅ | Grammar U2 | 커버 |
| L.3.1d | Verb tenses (present / past / future) | ✅ | Grammar U4 | 커버 |
| L.3.1e | Compound / complex sentences | ✅ | Grammar U2, U5 | 커버 |
| L.3.1f | Adjectives and adverbs | ✅ | Grammar U2, U5 | 커버 |
| L.3.1g | Subordinating / coordinating conjunctions | ✅ | Grammar U5~U7, U11 | 커버 |
| L.3.1h | Commas in compound sentences | ❌ | — | **제외 (가을)** |
| L.3.1i | Capitalization / punctuation in writing | ❌ | — | **제외 (가을)** |
| L.3.2 | Spelling conventions | ❌ | — | **제외 (가을)** |
| L.3.4 | Context clues for word meaning | ✅ | Vocabulary + Q&A | 커버 |
| L.3.4b | Affixes and roots | ✅ | Morphology U2~U11 | 커버 |
| L.3.4c | Root word meaning | ✅ | Morphology U2~U11 | 커버 |
| L.3.5 | Word relationships and nuances | ✅ | Word Work + Vocabulary | 커버 |
| L.3.6 | Tier 2 academic vocabulary acquisition | ✅ | Daily Words + CKLA Vocabulary | 커버 |

**커버율: 12 / 15 항목 (80%)**

---

### 7.2 미커버 항목 처리 방침

#### L.3.1h — Commas in Compound Sentences

- **현황:** CKLA G3 도메인 텍스트에서 쉼표 규칙을 명시적으로 다루지 않음
- **결정: 2026 가을 학기 스코프로 이연**
  - 시기: 2026년 9월 이후 Phase 2
  - 방법: Grammar 탭에 Unit별 미니 퀴즈 추가 (옵션 C) — 개발 비용 최소화
  - 임시 대응: Word Work 자유 작문에서 부수적 노출은 되나 채점 기준에 포함 안 됨

#### L.3.1i — Capitalization and Punctuation in Writing

- **현황:** Word Work 답안 서버 유사도 검증 시 구두점 무시 (정규화 과정에서 제거)
- **결정: 2026 가을 학기 스코프로 이연**
  - 시기: 2026년 9월 이후 Phase 2
  - 방법: Word Work 채점 기준 확장 — 대문자 + 마침표 존재 여부 가산점

#### L.3.2 — Spelling Conventions

- **현황:** Spelling 탭(참조 전용)에서 패턴 제시만 함. 채점 없음.
- **결정: 2026 가을 학기 스코프로 이연**
  - 현재 Daily Words Day 7 스펠링 테스트가 부분 대체 역할 수행
  - Phase 2에서 Spelling 탭에 채점형 연습 추가 검토

---

### 7.3 Q&A 문항 유형 분포 검증

CKLA G3 레슨 Q&A는 **Bloom's Taxonomy** + **Webb's DOK** 기준으로 3종류로 분류된다.

| 유형 | 설명 | 목표 비율 | 실제 분포 기준 |
|---|---|---|---|
| Literal | 텍스트에 명시된 사실 질문 | 40% | 5문항 중 2문항 |
| Inferential | 텍스트 근거로 추론 요구 | 40% | 5문항 중 2문항 |
| Evaluative | 자신의 의견·판단 요구 | 20% | 5문항 중 1문항 |

**Domain Test Q&A (5문항):** 동일 비율 적용 — Literal 2 + Inferential 2 + Evaluative 1  
**Grade Final Test Q&A (10문항):** Literal 4 + Inferential 4 + Evaluative 2

---

### 7.4 Vocabulary 문항 분포 검증

#### 레슨 내 퀴즈 (3문항)
- 해당 레슨 vocabulary 단어에서 랜덤 추출
- 보기 4개: 정답 1 + 오답 3 (다른 레슨 단어에서 추출)
- 최소 통과: 2/3 (≈ 67%)

#### Domain Test vocab (5문항: 3 MC + 2 Fill)
- MC 3문항: Domain 전체 단어 풀에서 추출
- Fill 2문항: MC 오답 단어 또는 고빈도 단어 우선

#### Grade Final Test vocab (15문항)
- 11개 Domain 전체 단어 풀에서 가중 랜덤 추출
- SM-2 `ef < 2.0` (취약 단어) 우선 출제
- 보기 오답: 동일 Domain 단어 우선 → 타 Domain 보조

---

### 7.5 Word Work 채점 기준 (현재 구현)

```
서버측 유사도 계산 (services/ckla_grader.py):
  - 사용자 문장 정규화 (소문자 + 구두점 제거)
  - 집중 단어 definition + example_1 과 코사인 유사도 계산
  - 임계값: 0.80 (80%) 이상 → 정답 처리
  - 임계값 미달: 완료는 됨, accuracy 기록에만 반영 (차단 없음)

Phase 2 개선 예정:
  - 대문자·마침표 유무 체크 (+L.3.1i 부분 커버)
  - 집중 단어 포함 여부 필수 체크
```

---

### 7.6 SM-2 간격 반복 스케줄 (CKLA 단어 기준)

| 채점 결과 | 다음 복습 간격 |
|---|---|
| 정답 (is_correct=true), 1회 시도 | EF 상승 → 인터벌 × EF |
| 정답 (is_correct=true), 2회 시도 | EF 유지 |
| 오답 (is_correct=false) | EF 하강, 인터벌 1일로 리셋 |

- 초기값: EF = 2.5, interval = 1일
- 최대 간격: 설정 없음 (표준 SM-2)
- `GET /api/academy/ckla/review/due`: 오늘 날짜 ≥ next_review_date 인 단어만 반환

---

### 7.7 데이터 품질 검증 체크리스트

배포 전 아래 항목을 확인한다.

| 항목 | 기준 | 검증 방법 |
|---|---|---|
| 레슨당 단어 수 | 5~15개 | `SELECT COUNT(*) FROM ckla_word_lessons GROUP BY lesson_id` |
| 레슨당 질문 수 | 3~7개 | `SELECT COUNT(*) FROM ckla_questions GROUP BY lesson_id` |
| word_work_word 필드 | 전 레슨에 존재 | `SELECT COUNT(*) FROM ckla_lessons WHERE word_work_word IS NULL` |
| Domain당 레슨 수 | 5~15개 | `SELECT COUNT(*) FROM ckla_lessons GROUP BY domain_id` |
| TTS 대상 텍스트 | 500자 이내 / 문단 | `ckla_grader.py` 전처리 단계 확인 |
| Q&A 유형 분포 | Literal ≥ 1, Inf ≥ 1, Eval ≥ 1 / 레슨 | `SELECT kind, COUNT(*) FROM ckla_questions GROUP BY kind, lesson_id` |

---

### 7.8 Phase 2 백로그 (가을 학기)

| 항목 | 설명 | 우선순위 |
|---|---|---|
| L.3.1h 미니 퀴즈 | Grammar 탭 Unit별 쉼표 퀴즈 추가 | P2 |
| L.3.1i 채점 기준 확장 | Word Work 대문자·마침표 가산점 | P2 |
| L.3.2 Spelling 채점 | Spelling 탭 채점형 전환 | P3 |
| Word Work 필수 단어 체크 | 집중 단어 포함 여부 필수화 | P2 |
| Q&A 재시도 허용 | 동일 문항 1회 재시도 (Inferential/Evaluative) | P3 |
| 오프라인 지원 | 전체 레슨 데이터 캐싱 | P4 |
