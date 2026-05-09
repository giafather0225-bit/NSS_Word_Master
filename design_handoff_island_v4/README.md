# Phase 4 Handoff — Final System Screens (㉑–㉔)

> Gia's Island · 마지막 4개 화면. 게임 오프닝 임팩트 + 핵심 카타르시스 + 바이럴 + 미세 피드백.

---

## 📦 Contents

| # | 화면 | 변형 | 우선순위 |
|---|------|------|----------|
| ㉑ | **Onboarding Full Flow** | welcome → nickname → pick friend → first feed → done (5 steps) | P0 |
| ㉒ | **Evolution Sequence** | before · during · after · branching choice | P0 |
| ㉓ | **Photo Capture & Share** | compose · preview · shared (3 phases) | P1 |
| ㉔ | **Toast / Snackbar System** | success · reward · error · info · achievement · stacked | P0 |

---

## 구현 순서

1. **㉔ Toast** — 시스템 컴포넌트. 다른 모든 화면이 의존.
2. **㉑ Onboarding** — 신규 가입 동선. 첫 인상 결정.
3. **㉒ Evolution** — 게임 핵심 카타르시스. 진화 트리거 로직 + 풀스크린 연출.
4. **㉓ Photo** — 바이럴 요소. 카메라 권한 + 이미지 합성 필요.

---

## ㉑ Onboarding Full Flow

5 단계, 좌상단 step indicator, 우상단 Skip 항상 노출.

| Step | 핵심 |
|------|------|
| 1. Welcome | 풀스크린 그라디언트 + 로고 섬 + Begin CTA |
| 2. Nickname | 입력 필드 + 추천 닉네임 chip 5종 + 🎲 random |
| 3. Pick friend | 3 zone 친구 (Forest=Clover unlocked, Ocean=Pip locked, Space=Nova locked). MVP는 Clover 단일 선택만 |
| 4. First feed | Clover + Lumi 등장 + 사과 강조 + 인벤토리 트레이 |
| 5. Done | 입양 완료 carousel + 보상 chip + Enter island CTA |

### Acceptance
- 모든 step에서 ← Back / Skip 동작 (Skip은 5단계 통째로 종료, 5번째 done은 Skip 숨김)
- 닉네임 1–12자, 한글/영문/숫자만. 비속어 필터 (서버 측)
- 4단계 First feed는 인터랙션 mandatory. 5초 idle 시 Lumi 힌트 재출력
- 완료 후 `profile.onboarding_done = true` + 첫 친구 인벤토리 추가

---

## ㉒ Evolution Sequence

게임 최대 카타르시스 모먼트. 풀스크린 takeover.

| Phase | 길이 | 연출 |
|-------|------|------|
| before | 사용자 트리거 대기 | 골드 오로라 배경 + glow + "Begin evolution" CTA |
| during | 2–3초 자동 | 다크 배경 + conic-gradient 회전 + 별 + 흰 실루엣 |
| after | 사용자 dismiss 대기 | 그린 배경 + 컨페티 + before/after 비교 + 보상 chip |
| choice | (선택사항) | 분기 진화 시. 두 형태 카드 비교 + 영구 선택 경고 |

### Acceptance
- during phase는 **반드시** 2초 이상 (skip 불가). 카타르시스 보호.
- after에서 보상 (Lumi + diary entry + dex update) 동시 발생.
- choice는 V2 기능. MVP는 일직선 진화만.
- 진화 직후 자동으로 ⑮ Diary 새 entry 생성.
- 푸시 ⑲ `evolution` 트리거는 진화 가능 조건 충족 후 1회만.

---

## ㉓ Photo Capture & Share

게임 내 카메라. 친구와 함께 한 순간을 남기는 행위.

| Phase | 화면 |
|-------|------|
| compose | 풀스크린 카메라 mock + 스티커 트레이 + 셔터 |
| preview | 찍은 사진 + 캡션 입력 + 저장처 토글 (Diary/Dex/Camera roll) |
| shared | 성공 confirm + Story/Link/More 공유 옵션 |

### Acceptance
- compose에서 **시간/계절 따른 환경 자동 적용** (forest는 낮/밤 변화).
- 스티커 8종 (✨🌸💕🍃⭐🌙🌿💫) + 텍스트 도구.
- 저장 토글 기본값: Diary ON, Dex ON, Camera roll OFF.
- "Save & Share" 클릭 시 OS native share sheet (iOS는 `navigator.share`).
- 공유 이미지에 워터마크 (좌하단 "Gia's Island" 작게).

### 기술 노트
- HTML2Canvas 또는 서버 사이드 렌더링.
- 카메라 권한 X — **게임 내 캐릭터/환경만**으로 합성. 진짜 카메라 X.

---

## ㉔ Toast / Snackbar System

전역 시스템 컴포넌트. 모든 화면에서 호출 가능해야 함.

### 6 variants

| variant | 색상 | 사용처 |
|---------|------|--------|
| success | green #E8F5E0 | 저장됨, 완료됨 |
| reward | gold #FFE5C2 | Lumi/gem 획득, 미션 완료 |
| error | red-ish #FBEEF2 | 실패, 네트워크 오류 (Retry 버튼 포함) |
| info | purple #F2ECFA | Lumi 메시지, 안내 (View 버튼 포함) |
| achieve | gradient gold→pink | 마일스톤, streak 업적 |
| stack | — | 2개 이상 동시 출현 시 자동 묶음 |

### Behavior
- 위치: 화면 상단 (header 아래 60px), 좌우 14px margin
- 자동 dismiss: success/reward 2.5s, info 4s, error/achieve 사용자 dismiss까지
- 같은 종류 연속 발생 시 카운터로 묶기 (예: "+3 Lumi · 3건")
- 최대 동시 표시 3개. 4개 이상은 큐.
- ✕ 버튼 항상 노출. Retry/View는 variant 따라 노출.

### API 제안 (참고)
```js
toast.success('Saved to diary');
toast.reward('+3 Lumi earned', { sub: 'daily mission complete' });
toast.error('Couldn\'t save', { onRetry: () => save() });
toast.info('Lumi has a message', { onClick: () => openMail() });
toast.achieve('New milestone!', { sub: '7-day streak unlocked' });
```

---

## 🎨 토큰

신규 토큰 0개. 기존 V1–V3 토큰 모두 재사용.

토스트 색상은 토큰화 권장:
```css
--toast-success-bg: #E8F5E0;  --toast-success-fg: #3D6B47;
--toast-reward-bg:  #FFE5C2;  --toast-reward-fg:  #D9A055;
--toast-error-bg:   #FBEEF2;  --toast-error-fg:   #C25770;
--toast-info-bg:    #F2ECFA;  --toast-info-fg:    #5C4A87;
```

---

## 📋 QA 체크리스트

- [ ] ㉑ 모든 step Skip 동작
- [ ] ㉑ 닉네임 validation (1–12자, 비속어)
- [ ] ㉑ first feed interaction mandatory (5s idle 시 hint)
- [ ] ㉒ during phase ≥ 2초 (skip 불가)
- [ ] ㉒ after에서 Diary entry 자동 생성
- [ ] ㉓ 저장 토글 default (Diary ON, Dex ON, Roll OFF)
- [ ] ㉓ 공유 이미지 워터마크
- [ ] ㉔ 자동 dismiss 시간 variant별 정확
- [ ] ㉔ 동시 3개 cap, 4개 이상 큐 처리
- [ ] ㉔ 같은 종류 연속 시 묶기 (counter)

---

생성: 2026-05-01
디자인 파일: `Gia's Island.html` → ㉑ Onboarding / ㉒ Evolution / ㉓ Photo / ㉔ Toast 섹션
