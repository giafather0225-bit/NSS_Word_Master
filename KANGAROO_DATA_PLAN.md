# KANGAROO_DATA_PLAN.md
# GIA Learning App — Math Kangaroo Data Architecture & Build Plan
# Created: 2026-05-03 | Author: Claude + Mark (확정)
# 이 파일은 CLAUDE.md / MATH_SPEC.md 의 Kangaroo 섹션과 연계됩니다.

---

## 1. 결정된 아키텍처 (Final Decision — 2026-05-03)

### 채택: PDF Anchor Mode ✅

| 방식 | 결정 | 이유 |
|------|------|------|
| base64 이미지 JSON 삽입 | ❌ 기각 | 파일 크기 폭증, 모바일 성능 저하 |
| PNG 개별 추출 | ❌ 기각 | 103세트 × 24문제 = 수작업 불가 |
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

### 레퍼런스 파일: `ksf_2024_junior.json` ✅ (완성본 — 30문제 전체 solution 완비)

```json
{
  "set_id": "ksf_2024_junior",
  "title": "40th International Kangaroo Mathematics Contest 2024 — Junior (Grades 9-10)",
  "level": "junior",
  "source": "KSF",
  "year": 2024,
  "grade_range": "Grades 9-10",
  "total_questions": 30,
  "time_limit_minutes": 75,
  "max_score": 120,
  "start_points": 0,
  "scoring": {
    "section1_points": 3,
    "section2_points": 4,
    "section3_points": 5,
    "penalty": "-1/4 of question points",
    "starting_points": 0
  },
  "pdf_source_url": "https://www.kaenguru.at/files/problems/2024_Junior_E.pdf",
  "answer_key_source": "https://mathkangaroo.org/mks/wp-content/uploads/2026/04/2024.pdf",
  "questions": [
    {
      "number": 1,
      "section": 1,
      "points": 3,
      "pdf_page": 1,
      "image_required": false,
      "question_text": "...",
      "options": {"A": "...", "B": "...", "C": "...", "D": "...", "E": "..."},
      "answer": "D",
      "solution": "Step-by-step explanation in English.",
      "solution_steps": ["Step 1: ...", "Step 2: ...", "Step 3: ..."],
      "difficulty": "easy",
      "topic": "arithmetic"
    }
  ]
}
```

### Écolier (Gr3-4) 특이사항
- 총 24문제 (Section1: Q1-8, 3pt / Section2: Q9-16, 4pt / Section3: Q17-24, 5pt)
- `start_points: 24` (Écolier 채점 방식: 24점 시작)
- `max_score: 96`
- `time_limit_minutes: 60`

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

## 6. 구축 우선순위 (2026-05-03 기준)

| 순서 | set_id | 상태 | 문제 수 | 비고 |
|------|--------|------|---------|------|
| 1 | `ikmc_2024_ecolier` | 🔄 진행 중 | 24 | 답안 확인 완료, 해설 작성 중 |
| 2 | `ikmc_2025_ecolier` | ⬜ 대기 | 24 | PDF 확인 완료 |
| 3 | `ikmc_2023_ecolier` | ⬜ 대기 | 24 | 답안만 있음, PDF 미확인 |
| 4 | `ikmc_2024_benjamin` | ⬜ 대기 | 24 | PDF 확인 완료 |
| 5 | `ikmc_2025_benjamin` | ⬜ 대기 | 24 | — |
| 6 | `ikmc_2022_ecolier` | ⬜ 대기 | 24 | — |
| 7 | `ikmc_2022_benjamin` | ⬜ 대기 | 24 | — |
| 8+ | 이후 레벨/연도 확장 | ⬜ 계획 중 | — | Cadet, Junior, Student |

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
- [ ] `ikmc_2024_ecolier.json` — solution 24개 완성
- [ ] `ikmc_2025_ecolier.json` — solution 24개 완성
- [ ] `ikmc_2023_ecolier.json` — solution 24개 완성
- [ ] `ikmc_2024_benjamin.json` — solution 24개 완성
- [ ] `ikmc_2025_benjamin.json` — solution 24개 완성

### 코드 수정
- [ ] `math_kangaroo.py` — `pdf_page`, `image_required` 필드 반환 추가
- [ ] `math-kangaroo-pdf-exam.js` — `pdf_page` 기반 페이지 이동 구현 확인

### 문서 업데이트
- [ ] `CLAUDE.md` — Math Kangaroo 섹션 교체
- [ ] `MATH_SPEC.md` — Kangaroo Data Pipeline 섹션 추가
- [ ] `backend/API_INDEX.md` — Kangaroo API 3줄 추가
- [ ] `scripts/generate_kangaroo_solutions.py` — deprecated 주석 추가

### 검증
- [ ] `validate_kangaroo_phase1.py` — past paper 검증 로직 추가
- [ ] 2024 Ecolier 답안 24개 MK USA 공식 PDF 대조 완료
- [ ] 2025 Ecolier 답안 24개 MK USA 공식 PDF 대조 완료

---

## 9. 관련 파일 현황 요약

| 파일 | 캥거루 관련 내용 | 상태 |
|------|----------------|------|
| `CLAUDE.md` | Math Kangaroo 4줄 요약 | 업데이트 필요 |
| `MATH_SPEC.md` | Kangaroo Practice Module 개요 | Pipeline 섹션 없음 |
| `backend/API_INDEX.md` | Kangaroo API 없음 | 추가 필요 |
| `backend/routers/math_kangaroo.py` | `pdf_page` 필드 없음 | 코드 수정 필요 |
| `scripts/generate_kangaroo_solutions.py` | 구 Gemini Vision 방식 | deprecated 주석 필요 |
| `scripts/validate_kangaroo_phase1.py` | Practice 세트만 검증 | Past paper 검증 없음 |
| `ksf_2024_junior.json` | solution + solution_steps 완비 | 표준 레퍼런스 ✅ |
| `ikmc_2023_ecolier.json` | 답안만 있음, 해설 없음 | 해설 필요 |
| 나머지 past paper JSON들 | PDF 참조만 있음 | 해설 필요 |
