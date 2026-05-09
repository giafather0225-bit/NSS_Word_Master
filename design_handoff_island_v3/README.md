# Phase 3 Handoff — System Screens (⑰–⑳)

> Gia's Island · 시스템/외곽 화면 4종
> 게임 외곽을 감싸는 첫인상·안정성·복귀 동선을 책임지는 화면들.

---

## 📦 What's in this package

| # | 화면 | 변형 | 우선순위 |
|---|------|------|----------|
| ⑰ | **Loading / Splash** | splash · sync · reconnect | P0 |
| ⑱ | **Error / Offline** | offline · server · update · maintenance | P0 |
| ⑲ | **Push Notifications** | hungry · evolution · streak · stacked | P1 |
| ⑳ | **Tutorial Coachmarks** | step 1–4 | P1 |

---

## 구현 순서 (권장)

1. **⑰ Loading → ⑱ Error** — 앱 진입/장애 동선 먼저. 한 세트로 묶어 구현.
2. **⑳ Coachmarks** — 온보딩 직후 1회성 투어. 신규 유저 첫 인상 결정.
3. **⑲ Push Notifications** — 서버/FCM 연동 필요. 카피만 먼저 확정해도 OK.

---

## ⑰ Loading / Splash

**3 variants:**

- `splash` — 콜드 부트. 풀스크린 그라디언트 + 로고 섬 + Lumi 손글씨 톤.
- `sync` — 서버 데이터 복원. progress bar (0–100%) + Clover idle 일러스트.
- `reconnect` — 짧은 재연결 (1–3초). 스피너 + 한 줄 카피.

### Acceptance

- splash는 최소 800ms 노출 (브랜드 인상). 데이터 준비 완료시에도 800ms 보장.
- sync는 progress 1초 이상 0%에 머물면 안 됨 (가짜 progress라도 움직일 것).
- reconnect는 3초 이상 노출 시 ⑱ Error/offline으로 fallback.

### Tokens

- 배경: `linear-gradient(180deg, #FBEEF2 0%, #F2ECFA 50%, #EEF4FA 100%)`
- Progress: `linear-gradient(90deg, var(--diary), var(--rewards-primary))`
- 도트 펄스: `var(--diary)` + `pulse-glow` 키프레임 (1.4s ease infinite, stagger 0.2s)

---

## ⑱ Error / Offline

**4 variants:**

| kind | 트리거 | CTA | Alt |
|------|--------|-----|-----|
| `offline` | 네트워크 끊김 | Try again | Continue offline |
| `server` | 5xx / 타임아웃 | Try again | Report a bug |
| `update` | 강제 업데이트 | Update now | Later |
| `maintenance` | 점검 모드 | Notify me | — |

### 공통 구조

- 64px 일러스트 (이모지 placeholder, 추후 실제 일러스트 교체)
- Title (gi-h1, 26px) → Sub (14px secondary) → Hand (Caveat 20px)
- Primary CTA + (옵션) Ghost alt

### Voice 가이드

- 절대 비난 톤 금지. "Not your fault, promise!" 같은 따뜻한 hand-drawn 한 줄 필수.
- offline 카피 끝: "The island will wait for you 💕"
- maintenance: 복귀 예상 시간 chip 노출 (`⏰ Estimated 2h 14m`).

---

## ⑲ Push Notifications

iPhone 잠금화면 mock 기준 디자인. 발신자는 항상 **Lumi 🌙**.

### Voice & Copy 규칙

- 보내는 주체: Lumi (NPC 가이드). 절대 "Gia's Island"라는 시스템 톤 X.
- 이모지 1개 이내. 마침표 대신 자연스러운 호흡.
- **금지:** "지금 접속하세요!", "놓치지 마세요!" 류 FOMO/명령형.

### Scenarios

| ID | Trigger | Copy 예시 |
|----|---------|-----------|
| `hungry` | Hunger gauge < 30% & 4h+ idle | "Clover hasn't eaten in a while and is feeling a bit hungry 🥺" |
| `evolution` | 진화 조건 충족 | "✨ Clover is ready to evolve! Come visit the Forest." |
| `streak` | 21:00 KST 이전 미접속 (streak 3+일) | "Your 4-day streak ends in 3h — pop in for ✨ 1 Lumi" |
| `multiple` | 3개 이상 누적시 stacked 표시 | (Notification Center 자동 묶음) |

### 발송 정책

- **하루 최대 2건.** hungry + (evolution OR streak).
- 22:00–08:00 KST 무음 (긴급 streak 제외).
- 사용자가 24h 내 접속한 경우 streak 알림 skip.

---

## ⑳ Tutorial Coachmarks

온보딩 직후 1회성 투어. **건너뛰기 항상 노출.**

### 4 steps

1. **Tap a zone** — Forest 위에 spotlight + "Each zone has its own friend"
2. **Lumi balance** — 좌상단 Lumi chip 강조 + 획득/사용 설명
3. **Daily streak** — 우하단 streak panel 강조 + 7일차 보상 hint
4. **You're all set** — 중앙 카드 + "Tap anywhere to start"

### Behavior

- 첫 진입 후 1회만 노출. `localStorage.tutorialSeen = true` flag.
- "Skip tour" 클릭 시 즉시 종료 + flag 저장.
- 각 step은 사용자 탭 (배경/Next 버튼 둘 다) 시 진행. 자동 진행 X.
- Spotlight: `box-shadow: 0 0 0 9999px rgba(43,39,34,.7)` 트릭으로 cutout.
- 강조 테두리: `var(--diary)` 2px + `pulse-glow` 애니메이션.

---

## 🎨 사용 토큰 요약

이미 Phase 1/2에 정의된 토큰만 사용. 추가 토큰 없음.

```
--diary, --diary-light, --diary-soft, --diary-ink
--rewards-primary, --rewards-light, --rewards-ink
--bg-page, --bg-card, --bg-surface
--text-primary, --text-secondary, --text-hint
--border-subtle, --border-default
--r-md, --r-lg, --r-xl, --r-2xl
--shadow-soft, --shadow-modal
```

신규 키프레임: 없음. 기존 `pulse-glow`, `float` 재사용.

---

## 🛠 구현 노트 (Flask + Jinja2)

- 로딩/에러는 라우트 자체보다 **베이스 템플릿의 상태 슬롯**으로 처리 권장.
  - `{% block app_state %}` 정의 → `loading.html`, `error.html` partial.
- 코치마크는 별도 SPA 컴포넌트 (Alpine.js or vanilla JS). 서버 렌더 X.
  - 첫 페이지 로드 후 `fetch('/api/me')`로 `tutorial_seen` 체크.
- 푸시는 FCM token 등록 + 백엔드 cron job.
  - 한국 시간 기준 발송. `DJANGO_TZ`/`Asia/Seoul` 명시.

---

## 📋 QA 체크리스트

- [ ] ⑰ Splash 800ms 최소 노출
- [ ] ⑰ Sync progress 0% 정체 없음
- [ ] ⑱ 모든 에러 화면에 hand-drawn 위로 카피 1줄 이상
- [ ] ⑱ offline 시 마지막 동기화 시각 표시
- [ ] ⑲ 22:00–08:00 무음 정책 (streak 제외)
- [ ] ⑲ 일일 발송 횟수 cap 2건
- [ ] ⑳ Skip tour 항상 가시
- [ ] ⑳ tutorialSeen flag 영구 저장
- [ ] 모든 화면 다크/라이트 모두 정상 (현재는 라이트만 필수)

---

생성: 2026-05-01
디자인: `Gia's Island.html` → ⑰ Loading / ⑱ Error / ⑲ Push / ⑳ Coachmarks 섹션
