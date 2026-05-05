# KANGAROO_DATA_PLAN.md
# GIA Learning App — Math Kangaroo Data Architecture & Build Plan
# Created: 2026-05-03 | Updated: 2026-05-04 | Author: Claude + Mark (확정)
# 이 파일은 CLAUDE.md / MATH_SPEC.md 의 Kangaroo 섹션과 연계됩니다.

---

## 1. 결정된 아키텍처 (Final Decision — 2026-05-03)

### 채택: PDF Anchor Mode ✅

| 방식 | 결정 | 이유 |
|------|------|------|
| base64 이미지 JSON 삽입 | ❌ 기각 | 파일 크기 폭증, 모바일 성능 저하 |
| PNG 개별 추출 | ❌ 기각 | 104세트 × 24문제 = 수작업 불가 |
| Gemini Vision 스크립트 (`generate_kangaroo_solutions.py`) | ❌ 기각 / deprecated | 비용·속도·정확도 문제 |
| **PDF 유지 + `pdf_page` 필드 추가** | ✅ 채택 | PDF 이미 서버에 존재, JSON에 필드 1개 추가만으로 구현 |

### 현재 앱 동작 방식 (실제 구현 기준)

- `pdf_available: true` → `math-kangaroo-pdf-exam.js` 실행
  - PDF.js로 해당 `pdf_page` 렌더링
  - 하단에 A–E 선택지 표시
  - 문제 간 페이지 네비게이션 지원
- `pdf_available: false` → `math-kangaroo-exam.js` 실행
  - 문제 텍스트 직접 표시 (인라인)

---

## 2. 표준 JSON 스키마

### 레퍼런스 파일: `ikmc_2024_ecolier.json` ✅ (신규 표준 — 24문제 전체 per-question solution 완비, 2026-05-04)

> ⚠️ 구형 `ksf_2024_junior.json` 등은 루트의 `solutions: {"1": "..."}` dict 방식 — 신규 파일은 아래 per-question 방식으로 작성.

```json
{
  "set_id": "ikmc_2024_ecolier",
  "title": "Känguru der Mathematik Austria 2024 — Level Écolier (Grades 3-4)",
  "level": "ecolier",
  "level_label": "Écolier",
  "source": "IKMC",
  "source_type": "official_past_paper",
  "source_year": 2024,
  "grade_range": "Grades 3-4",
  "total_questions": 24,
  "time_limit_minutes": 60,
  "max_score": 120,
  "start_points": 24,
  "scoring": {
    "section1_questions": "1-8",
    "section1_points": 3,
    "section2_questions": "9-16",
    "section2_points": 4,
    "section3_questions": "17-24",
    "section3_points": 5,
    "penalty": "-1/4 of question points",
    "starting_points": 24
  },
  "pdf_file": "/static/math/kangaroo/pdf/intl_2024_ecolier.pdf",
  "pdf_available": true,
  "answers_verified": true,
  "answers_verified_source": "Mathematical proof + cross-check against kaenguru.at PDF",
  "answers": {"1":"E","2":"C",...},
  "questions": [
    {
      "number": 1,
      "section": 1,
      "points": 3,
      "pdf_page": 2,
      "image_required": true,
      "question_text": "...",
      "options": {"A": "...", "B": "...", "C": "...", "D": "...", "E": "..."},
      "answer": "E",
      "solution": "English explanation (1-3 sentences).",
      "solution_steps": ["Step 1: ...", "Step 2: ...", "Step 3: ..."],
      "difficulty": "easy",
      "topic": "arithmetic"
    }
  ]
}
```

### Level별 특이사항

**Écolier (Gr3-4)**
- 총 24문제 (Section1: Q1-8, 3pt / Section2: Q9-16, 4pt / Section3: Q17-24, 5pt)
- `start_points: 24` (Écolier 채점 방식: 24점 시작), `max_score: 120`, `time_limit_minutes: 60`
- pdf_page 매핑: Q1-6→2, Q7-12→3, Q13-18→4, Q19-24→5 (intl_2024 기준, 연도별 ±1 차이 있을 수 있음)

**Benjamin (Gr5-6)**
- 총 24문제 (Section1: Q1-8, 3pt / Section2: Q9-16, 4pt / Section3: Q17-24, 5pt)
- `start_points: 0`, `max_score: 96`, `time_limit_minutes: 75`

**Junior/Student (Gr9-12)**
- 총 30문제, `start_points: 0`, `max_score: 120`, `time_limit_minutes: 75`

### `topic` 값 목록
`arithmetic` | `geometry` | `logic` | `pattern` | `spatial_reasoning` | `algebra` | `number_theory` | `combinatorics`

### `difficulty` 값 목록
`easy` (Section 1) | `medium` (Section 2) | `hard` (Section 3)

---

## 3. 외부 데이터 소스 (검증 완료)

| 소스 | URL 패턴 | 용도 | 확인 연도 |
|------|----------|------|-----------|
| kaenguru.at (Austria) | `https://www.kaenguru.at/files/problems/{YEAR}_{LEVEL}_E.pdf` | 영문 문제 PDF | 2022–2025 ✅ |
| mathkangaroo.org (USA) | `https://mathkangaroo.org/mks/wp-content/uploads/2026/04/{YEAR}.pdf` | 공식 전레벨 답안 | 2022–2025 ✅ |
| matematica.pt | `https://matematica.pt/en/useful/kangaroo-questions.php` | 백업 소스 | 2009–2024 |

### Level ↔ Grade 매핑

| kaenguru.at 레벨 | MK USA 열 이름 | 학교 학년 | JSON set_id prefix |
|-----------------|--------------|----------|-------------------|
| Pre_Ecolier | Grades 1-2 | G1–G2 | `ikmc_{YEAR}_pre_ecolier` |
| Ecolier | Grades 3-4 | G3–G4 | `ikmc_{YEAR}_ecolier` |
| Benjamin | Grades 5-6 | G5–G6 | `ikmc_{YEAR}_benjamin` |
| Cadet | Grades 7-8 | G7–G8 | `ikmc_{YEAR}_cadet` |
| Junior | Grades 9-10 | G9–G10 | `ikmc_{YEAR}_junior` |
| Student | Grades 11-12 | G11–G12 | `ikmc_{YEAR}_student` |

---

## 4. 파일 위치 규칙

```
backend/data/math/kangaroo/
  ikmc_{YEAR}_{LEVEL}.json       ← IKMC 공식 문제 (kaenguru.at 소스)
  ksf_{YEAR}_{LEVEL}.json        ← KSF 소스
  {LEVEL}_practice_0N.json       ← 연습 세트
  {LEVEL}_drill_0N.json          ← 드릴 세트

frontend/static/math/kangaroo/pdf/
  ikmc_{YEAR}_{LEVEL}.pdf        ← 로컬 저장 PDF (kaenguru.at에서 다운로드)
  ksf_{YEAR}_{LEVEL}.pdf
```

---

## 5. 해설(Solution) 작성 원칙

- **담당:** Claude가 공식 PDF 직접 열람 후 풀이
- **검증:** MK USA 공식 답안 PDF 대조 확인 필수
- **언어:** 영어로 작성 (앱 UI 언어 기준)
- **필드 규칙:**
  - `solution`: 1–3문장 핵심 해설 (영어)
  - `solution_steps`: 단계별 배열 (최소 2단계)
  - `difficulty`: `easy`(Sec1) / `medium`(Sec2) / `hard`(Sec3)
  - 이미지 필요 문제: `image_required: true` 설정, `solution`에 "See PDF page N for figure." 안내 포함
  - 텍스트만 가능 문제: `image_required: false`, `question_text` 인라인 렌더링 가능

---

## 6. 구축 우선순위 (2026-05-04 업데이트)

| 순서 | set_id | JSON 파일 | PDF 파일 | 상태 | 비고 |
|------|--------|-----------|----------|------|------|
| 1 | `ikmc_2024_ecolier` | ✅ 있음 | `intl_2024_ecolier.pdf` ✅ | ✅ 완료 | 24문제 solution 전체, Q8/Q10 수정 |
| 2 | `ikmc_2025_ecolier` | ✅ 있음 | `intl_2025_ecolier.pdf` ✅ | ✅ 완료 | 24문제 solution 전체 (2026-05-04) |
| 3 | `ikmc_2023_ecolier` | 🔶 답만 | `ikmc_2023_ecolier.pdf` ✅ | ⬜ 대기 | 기존 JSON 있음, solution 없음 |
| 4 | `ikmc_2024_benjamin` | ⬜ 없음 | `intl_2024_benjamin.pdf` ✅ | ⬜ 대기 | PDF 보유, JSON 신규 작성 필요 |
| 5 | `ikmc_2025_benjamin` | ⬜ 없음 | `intl_2025_benjamin.pdf` ✅ | ⬜ 대기 | PDF 보유, JSON 신규 작성 필요 |
| 6 | `ikmc_2022_ecolier` | 🔶 답만 | `ikmc_2022_ecolier.pdf` ✅ | ⬜ 대기 | 기존 JSON 있음, solution 없음 |
| 7 | `ikmc_2022_benjamin` | 🔶 답만 | `ikmc_2022_benjamin.pdf` ✅ | ⬜ 대기 | 기존 JSON 있음, solution 없음 |
| 8 | `ikmc_2023_benjamin` | 🔶 답만 | `ikmc_2023_benjamin.pdf` ✅ | ⬜ 대기 | Q25-30 답안 PENDING 상태 |
| 9+ | 2012~2021 Ecolier/Benjamin | 🔶 답만 | ✅ 있음 | ⬜ 계획 | 각 레벨 PDF 보유 |
| 10+ | Cadet (2012~2023) | 🔶 답만 | ✅ 있음 | ⬜ 계획 | Junior/Student는 ksf 파일 우선 |

**🔶 기존 JSON 업그레이드 전략 (3번, 6번, 7번, 8번)**
- 기존 파일에 per-question 필드(`question_text`, `options`, `solution`, `solution_steps`, `pdf_page`, `image_required`) 추가
- 루트의 구형 `solutions` dict는 남겨도 무방 (앱이 두 방식 모두 지원)

---

## 7. 각 파일 업데이트 계획

### 7.1 CLAUDE.md
- 위치: `## Math Module > ### Math Kangaroo` 섹션 교체
- 추가 내용: Data Architecture Decision, Verified Sources, JSON 추가 필드, Solution 원칙, Build Priority

### 7.2 MATH_SPEC.md
- 위치: `## Kangaroo Practice Module` 아래 `### Kangaroo Data Pipeline` 신규 삽입
- 추가 내용: 채택 방식 결정 경위, 외부 소스 표, JSON 필드 스펙, 해설 원칙, 우선순위

### 7.3 backend/API_INDEX.md
- 위치: Math 섹션 내 신규 추가
- 추가 내용: `GET /api/math/kangaroo/sets`, `GET /api/math/kangaroo/set/{set_id}`, `POST /api/math/kangaroo/submit` 3개 항목

### 7.4 scripts/generate_kangaroo_solutions.py
- 작업: 파일 상단에 deprecated 주석 추가 (파일 삭제 안 함, 구 방식 참조용 보관)

### 7.5 backend/routers/math_kangaroo.py
- 위치: `qs_out.append(...)` 딕셔너리
- 작업: `pdf_page`, `image_required` 두 필드 반환 추가

### 7.6 scripts/validate_kangaroo_phase1.py
- 작업: Past paper 검증 로직 추가 (별도 함수로 분리)
- 추가 검증: `pdf_page` 필드 존재, `solution` 비어있지 않음, `solution_steps` 최소 2개
- 우선순위: 나중에 (데이터 구축 완료 후)

---

## 8. 완료 체크리스트

### 데이터 구축
- [x] `ikmc_2024_ecolier.json` — solution 24개 완성 (2026-05-04)
- [x] `ikmc_2025_ecolier.json` — solution 24개 완성 (2026-05-04)
- [ ] `ikmc_2023_ecolier.json` — solution 24개 완성 (기존 JSON 업그레이드)
- [ ] `ikmc_2024_benjamin.json` — solution 24개 완성
- [ ] `ikmc_2025_benjamin.json` — solution 24개 완성
- [ ] `ikmc_2022_ecolier.json` — solution 24개 완성 (기존 JSON 업그레이드)
- [ ] `ikmc_2022_benjamin.json` — solution 24개 완성 (기존 JSON 업그레이드)
- [ ] `ikmc_2023_benjamin.json` — solution 24개 완성 (Q25-30 답안 PENDING 해결 선행)

### 코드 수정
- [ ] `math_kangaroo.py` — `pdf_page`, `image_required` 필드 반환 추가
- [ ] `math-kangaroo-pdf-exam.js` — `pdf_page` 기반 페이지 이동 구현 확인

### 문서 업데이트
- [x] `CLAUDE.md` — Math Kangaroo 섹션 전면 개편 (2026-05-04)
- [x] `KANGAROO_DATA_PLAN.md` — 우선순위 표 + 레퍼런스 파일 업데이트 (2026-05-04)
- [x] `backend/API_INDEX.md` — Kangaroo API 3줄 추가 (2026-05-03)
- [x] `scripts/generate_kangaroo_solutions.py` — deprecated 주석 추가 (2026-05-03)
- [ ] `MATH_SPEC.md` — Kangaroo Data Pipeline 섹션 추가

### 검증
- [x] 2024 Ecolier 답안 24개 — 수학적 증명으로 검증 완료 (Q8·Q10 수정)
- [ ] `validate_kangaroo_phase1.py` — past paper 검증 로직 추가
- [ ] 2025 Ecolier 답안 24개 MK USA 공식 PDF 대조

---

## 9. 관련 파일 현황 요약 (2026-05-04 기준)

| 파일 | 캥거루 관련 내용 | 상태 |
|------|----------------|------|
| `CLAUDE.md` | Math Kangaroo 전체 섹션 (PDF 현황, 스키마, solution 현황) | ✅ 최신 |
| `KANGAROO_DATA_PLAN.md` | 아키텍처 결정 + 우선순위 + 체크리스트 | ✅ 최신 |
| `backend/API_INDEX.md` | Kangaroo API 3개 항목 | ✅ 완료 |
| `MATH_SPEC.md` | Kangaroo Practice Module 개요 | Pipeline 섹션 없음 |
| `backend/routers/math_kangaroo.py` | `pdf_page`, `image_required` 미반환 | 코드 수정 필요 |
| `scripts/generate_kangaroo_solutions.py` | 구 Gemini Vision 방식 | ✅ deprecated 주석 완료 |
| `scripts/validate_kangaroo_phase1.py` | Practice 세트만 검증 | Past paper 검증 없음 |
| `ikmc_2024_ecolier.json` | 24문제 solution 완비 (신규 표준 스키마) | ✅ 완료 |
| `ksf_2024_junior.json` 외 ksf 12세트 | 구형 solutions dict (30개) | per-question 미변환 |
| `ikmc_2023_ecolier.json` 외 | 답안만 있음, per-question solution 없음 | 해설 필요 |
