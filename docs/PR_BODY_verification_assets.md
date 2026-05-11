# G3 Misconception 라이브러리 + Stage 7 파일럿 인프라

## 배경

기존 PR #1 (`verification-upgrade`)은 main에서 178 커밋 뒤처진 시점에서 분기되어
G3 콘텐츠 121개 파일에서 충돌이 발생함. main에서는 그 사이 `Phase 1-3 schema
standardization`, `Phase 4-E learn card type collapse`, `Phase A 145개 hint
업그레이드` 등 대대적 발전이 있었음.

→ **이 PR은** verification-upgrade에서 schema-independent하고 재사용 가능한
자산만 cherry-pick. 검증 메타 데이터 작업은 별도로 main의 새 schema 위에서
재실행 예정.

## 신규 자산 (25 파일)

### 1. Misconception 라이브러리 (22 파일 + README)
`backend/data/math/G3/misconceptions/` — Grade 3 전체 표준 커버.

| 영역 | 표준 |
|---|---|
| 자릿값/덧뺄셈 | 3.NBT.A.1·2·3 |
| 곱·나눗셈 | 3.OA.A.1·2·3·4, 3.OA.B.5, 3.OA.C.7, 3.OA.D.8·9 |
| 분수 | 3.NF.A.1 |
| 측정/데이터/둘레/넓이 | 3.MD.A.1·2, 3.MD.B.3·4, 3.MD.C.5·6·7, 3.MD.D.8 |
| 도형 | 3.G.A.1·2 |

각 표준당 7개 misconception × 학술 인용 ≈ **154 항목**.

참고문헌: NCTM Progressions (K-6), Van de Walle (8th ed.), Van Hiele, Battista,
Outhred & Mitchelmore, Friel et al., EngageNY G3 Modules 1-7, Smarter Balanced 2015.

### 2. Stage 7 학습자 파일럿 (2026-06-13~19)
- `docs/PILOT_STAGE7_2026_06.md`: 7일 운영 가이드
  - 5개 측정 지표 (정답률·매칭률·학습효과·시간·피드백)
  - 합격 기준 (80% 정상 범위 / 60% 매칭률 / +20%pt)
  - 회고 양식·윤리 동의
- `scripts/stage7_pilot_analyze.py`: math_attempts → 자동 리포트
  - 5개 지표 자동 산출, 마크다운 리포트 생성

### 3. 콘텐츠 감사 도구
- `scripts/generate_audit_report.py`: G3 콘텐츠 정합성 검사

## 다음 단계 (이 PR 머지 후)

1. **머지** → `main`에 misconception 라이브러리 + 파일럿 인프라 반영
2. **검증 메타 재적용** — main의 새 schema (Phase 1-3 / 4-A·E) 위에 7단계 검증
   메타를 다시 적용하는 신규 작업 시작
3. **Stage 7 파일럿 준비** — 학습자 모집 (~1개월 여유)
4. **파일럿 실시** (2026-06-13~19) → 학습자 데이터로 misconception 매칭률 검증

## Test plan

- [x] 신규 파일만 추가, 기존 파일 수정 없음 → 회귀 위험 0
- [x] main에서 +1 커밋만 추가, 충돌 없음
- [ ] `expected_errors` 필드에서 신규 misconception ID 참조 시 백엔드 호환성 확인
- [ ] Stage 7 분석 스크립트 dry-run (빈 DB)

## 폐기되는 작업

기존 `verification-upgrade` 브랜치의 검증 메타 적용 변경 (G3 121 레슨 JSON 수정)은
main 새 schema와 호환되지 않아 **폐기**됨. 대신 main 새 schema 위에서 동일한
프로토콜을 재적용하는 별도 작업이 후속 PR로 진행될 예정.

기존 PR #1은 close, 이 PR로 대체.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
