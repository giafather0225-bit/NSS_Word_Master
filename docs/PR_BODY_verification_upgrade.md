# G3 검증 프로토콜 — 13개 단원 + Stage 7 파일럿 인프라

## Summary

G3 (3학년) 전체 13개 단원에 7단계 검증 프로토콜 적용 완료.

- **레슨**: 80+ 개 (각 43문항 / PT=5 LEARN=8 TRY=5 R1=10 R2=10 R3=5)
- **unit_test**: 13개 (모두 검증 메타 정합화)
- **misconception 파일**: 15개 (이 PR에서 7개 신규)
- **Stage 7 파일럿 인프라**: 운영 가이드 + 데이터 분석 스크립트

## 단원별 진행

| 단원 | 표준 | 상태 |
|---|---|---|
| U1 add_sub_1000 | 3.NBT.A.2 | ✅ 레슨 + UT |
| U2 represent_interpret_data | 3.MD.B.3·4 | ✅ 레슨 + UT |
| U3 understand_multiplication | 3.OA.A.1 | ✅ 레슨 + UT |
| U4 multiplication_facts_strategies | 3.OA.C.7 | ✅ 레슨 + UT |
| U5 use_multiplication_facts | 3.NBT.A.3 | ✅ 레슨 + UT |
| U6 understand_division | 3.OA.A.2 | ✅ 레슨 + UT |
| U7 division_facts_strategies | 3.OA.C.7·D.8 | ✅ 레슨 + UT |
| U8 understand_fractions | 3.NF.A.1·2·3 | ✅ 레슨 + UT |
| U9 compare_fractions | 3.NF.A.3 | ✅ 레슨 + UT |
| U10 perimeter | 3.MD.D.8 | ✅ 레슨 + UT (20→30) |
| U11 time_mass_volume | 3.MD.A.1·2 | ✅ 레슨 + UT (cherry-pick) |
| U12 area | 3.MD.C.5·6·7 | ✅ 레슨 + UT (cherry-pick) |
| U13 shapes | 3.G.A.1·2 | ✅ 레슨 + UT (cherry-pick) |

## 검증 메타 정합화

모든 문항에 다음 추가:
- `verification`: 3소스 dict (Go Math / EngageNY / Smarter Balanced)
- `expected_errors`: misconception ID 리스트 또는 dict
- `cpa_stage`: concrete / pictorial / abstract
- `math_note`, `feedback_correct`, `hints`
- `vertical_alignment` (top-level): prerequisite / current / successor
- `metadata.upgraded = True`

## Misconception 파일 (이번 PR 신규 7개)

3.MD.A.1, 3.MD.A.2, 3.MD.C.5, 3.MD.C.6, 3.MD.C.7, 3.G.A.1, 3.G.A.2 —
각 7개 항목 (총 49개) × 학술 인용 (Van Hiele, Van de Walle, Battista, NCTM Progressions, EngageNY 등).

## Stage 7 파일럿 인프라

- `docs/PILOT_STAGE7_2026_06.md`: 2026-06-13~19 운영 가이드
- `scripts/stage7_pilot_analyze.py`: math_attempts → 자동 리포트

5개 지표 산출:
1. 정답률 분포 (단원/레슨/단계별)
2. Misconception 매칭률 (목표 60%+)
3. 학습 효과 (PT→R3, 목표 +20%pt)
4. 시간 분포 (mean/p50/p95)
5. 이상치 탐지 (<20% 또는 >95%)

## Test plan

- [ ] 모든 마이그레이션 스크립트 idempotent 확인 (재실행 시 변경 없음)
- [ ] 백엔드 API에서 G3 단원 13개 모두 정상 로드
- [ ] U11-U13 레슨에서 `expected_errors` dict 형식이 백엔드와 호환되는지
- [ ] Stage 7 분석 스크립트가 빈 DB에서도 graceful하게 실패
- [ ] 회귀 테스트: 학습자 진도 데이터 영향 없음
- [ ] main과의 충돌 해결 (178 commits behind)

## 통계

- 커밋: 123개
- 신규/수정 파일: 약 50+
- 신규 misconception 항목: 49개
- 검증 메타 적용 문항: ~3,500+ (80레슨 × 43문항)

🤖 Generated with [Claude Code](https://claude.com/claude-code)
