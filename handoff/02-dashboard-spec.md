# 02 · Dashboard Hub — Screen Spec

**화면**: Dashboard Hub (진입 첫 화면, 사이드바 없이 풀 너비)
**라우트**: `/` 또는 `/dashboard`
**레이아웃 기준 폭**: 1280px 데스크톱. 좌우 36px 패딩 + 최대 컨테이너 1280px.

---

## 🗺️ 전체 레이아웃

```
┌──────────────────────────────────────────────────────────────────────┐
│                                                    ⋯ (top-right)     │
│  ┌─────────┐   ┌─────────────────────────────┐  ┌───────────────┐   │
│  │ Greeting│   │   Header (PICK A ROOM)       │  │ Stats Stack    │   │
│  │ Block   │   │                              │  │ · Words        │   │
│  │         │   │   ┌────┐ ┌────┐ ┌────┐       │  │ · Total XP     │   │
│  │         │   │   │ EN │ │ MA │ │ DI │       │  │ · Streak       │   │
│  │ Today's │   │   └────┘ └────┘ └────┘       │  └───────────────┘   │
│  │ Tasks   │   │   ┌────┐ ┌────┐ ┌────┐       │  ┌───────────────┐   │
│  │ (scroll)│   │   │ AR │ │ SH │ │ RV │       │  │ Ocean World    │   │
│  │         │   │   └────┘ └────┘ └────┘       │  │ illustration   │   │
│  │         │   │                              │  │ 3/10 collected │   │
│  │         │   │   Weekly Strip (bar chart)   │  │                │   │
│  └─────────┘   └─────────────────────────────┘  └───────────────┘   │
│                                                                     ● │
│                                                               (mascot)│
└──────────────────────────────────────────────────────────────────────┘
```

Grid: `260px 1fr 280px` · gap `28px` · padding `28px 36px 56px`.

---

## 🧩 컴포넌트 단위

### 1. TopRightMenu — 우측 상단 ⋯ 오버플로 메뉴

- 위치: `position: fixed; top: 14px; right: 14px; z-index: 50;`
- 버튼: 40x40 원형, 기본 `background: transparent`, 열림/호버 시 `var(--bg-card) + border-subtle + shadow-soft`
- 아이콘: lucide `more-horizontal` (3-dot horizontal)
- 클릭 → 드롭다운 (right: 0, top: 48):
  - **Parent Dashboard** (icon: `users`) → `/parent`
  - **Settings** (icon: `settings`) → `/settings`
- 바깥 클릭 시 닫힘 (오버레이 `position: fixed; inset: 0;`)

---

### 2. GreetingBlock — 좌측 상단 인사말

```
FRIDAY, APRIL 24          ← font-size: 12, color: --text-hint, uppercase, ls: 0.08em
Good morning,             ← Quicksand, 30px, weight 600, ls: -0.02em
Gia                       ← 동일 스타일, color: var(--diary-primary)
```

- 날짜: `new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' })`
- 시간대별 인사말: 5–11 Good morning / 12–17 Good afternoon / 18–4 Good evening

---

### 3. TodayChecklist — 오늘의 과제 카드

- 컨테이너: `.card` + padding 18 + `display: flex; flex-direction: column; flex: 1; min-height: 0;`
- 헤더: "Today's tasks" + 우측 `{doneCount} / {totalCount} done` (11px hint)
- 서브: "Set by parent · {earnedXP} / {totalXP} XP earned" (11px hint)
- 전체 진행바 4px, fill: `var(--diary-primary)`
- 본문: 섹션별 그룹 (English · Math · Diary · Review) 세로 리스트, `overflow-y: auto`

**ChecklistGroup**
- 섹션 라벨 행: `● English   2/5` (색 도트 6x6 + 섹션 ink 컬러 라벨 + 우측 hint 카운트)
- 아이템 리스트 gap 4px

**ChecklistRow** (항목 단위)
```
[○ / ●✓]  Voca · Lesson 07 Preview  [NOW]            +10
         (line-through if done, opacity .55)
```
- 상태별 스타일:
  - `done`: 체크 원 fill = 섹션 primary, text line-through, opacity 0.55
  - `due === 'now'`: 배경 `color-mix(section-color 8%, transparent)` + 섹션 primary 알약 "NOW"
  - idle: 투명 배경
- XP 배지: `padding: 2px 7px; border-radius: 20px; background: color-mix(section-color 14%, transparent); color: section-color; font-size: 10px; font-weight: 700;` → `+{xp}`

---

### 4. HeaderBar — 센터 상단

```
PICK A ROOM                        ← 11px hint uppercase ls: 0.09em
What do you feel like today?       ← Quicksand 22px, weight 600
```

---

### 5. SectionGrid — 6개 섹션 카드 (동일 크기)

- 컨테이너: `display: grid; grid-template-columns: repeat(3, 1fr); grid-auto-rows: 1fr; gap: 14px;`
- 6 카드: English / Math / Diary / Arcade / Shop / Review

**SectionCard** (모두 동일 스펙)
- `button` 요소, `width: 100%; aspect-ratio: 1/1; min-height: 140px;`
- 배경: `var(--{section}-light)`
- border: `1px solid var(--border-subtle)`
- radius: `var(--radius-xl)` (20)
- shadow: `var(--shadow-soft)` → hover: `translateY(-2px) + 0 8px 20px rgba(120,90,60,.08)`
- 내부: `display: grid; place-items: center;` 중앙에 타이틀 텍스트 하나만
  - Quicksand 28px weight 600, ls: -0.02em, line-height: 1.25
  - color: `var(--{section}-ink)`
- 클릭 라우트:
  - English → `/english`
  - Math → `/math`
  - Diary → `/diary`
  - Arcade → `/arcade`
  - Shop → `/shop`
  - Review → `/review`

**중요**: 카드 안에 아이콘, 진행바, 서브타이틀 **없음**. 이름만.

---

### 6. WeeklyStrip — 이번 주 차트

- 컨테이너: `.card` + padding `16px 18px` + radius 16
- 헤더: "This week" / 우측 "5-day streak" + lucide `flame` 12px (color: `var(--arcade-primary)`)
- 막대 그래프: grid 7열, 각 요일 S M T W T F S
- 각 막대 높이: `max(value * 56px, 4px)`
- 막대 색 규칙:
  - `value >= 0.9` → `var(--diary-primary)`
  - `value >= 0.5` → `var(--diary-soft)`
  - `value > 0`    → `var(--bg-surface)`
  - else           → `var(--border-subtle)`
- 라벨: 10px hint, 6px gap

---

### 7. StatsStack — 우측 스탯 3개

세로 카드 3개, gap 10. 각 카드 padding `12px 14px` + radius 16 + `.card`.

| Stat           | Value    | Sub         | Icon       | Color (icon bg)        |
|----------------|----------|-------------|------------|------------------------|
| Words learned  | 342      | all-time    | book-open  | `var(--english-primary)` |
| Total XP       | 1,250    | +45 today   | sparkles   | `var(--diary-primary)` |
| Streak         | 5 days   | best: 12    | flame      | `var(--arcade-primary)` |

각 행: `아이콘(32x32 rounded-10, color-mix 14% bg) / 라벨+숫자 / 서브`
- 라벨: 11px hint
- 숫자: Quicksand 16px weight 700
- 서브: 10.5px hint (우측 정렬)

---

### 8. OceanWorldCard — 월드 카드

- 그라디언트 배경: `linear-gradient(180deg, var(--english-light), var(--english-soft))`
- `.card` 외관 + padding `16px 16px 14px` + `min-height: 160px;` + `overflow: hidden;`
- 상단 라벨 "WORLD" (uppercase, 11px, color: `var(--english-ink)`)
- 타이틀 "Ocean World" (Quicksand 20px weight 600)
- 서브 "Illustration placeholder"
- 중앙 일러스트 자리: 대시 패턴 SVG + "ocean illustration" 텍스트 placeholder
- 하단 진행: "3 / 10 sea creatures collected"

---

### 9. MascotPlaceholder — GIA 마스코트 (우측 하단 고정)

- `position: fixed; right: 24px; bottom: 24px; z-index: 10;`
- 92x92 원형, `background: #fff; border: 1px solid var(--border-subtle); box-shadow: 0 8px 24px rgba(120,90,60,.12);`
- 내부 72x72 원 (`background: var(--bg-surface);`) 중앙에 "GIA" 텍스트
- 실제 마스코트 이미지로 교체 예정 (프로덕션 플레이스홀더)

---

## 🔗 라우트 맵

| 트리거                       | 목적지                |
|------------------------------|----------------------|
| 섹션 카드 English            | `/english`           |
| 섹션 카드 Math               | `/math`              |
| 섹션 카드 Diary              | `/diary`             |
| 섹션 카드 Arcade             | `/arcade`            |
| 섹션 카드 Shop               | `/shop`              |
| 섹션 카드 Review             | `/review`            |
| ⋯ 메뉴 > Parent Dashboard    | `/parent`            |
| ⋯ 메뉴 > Settings            | `/settings`          |
| ChecklistRow 클릭            | 해당 과제 상세 (추후 정의) |

---

## 🧠 상호작용 규칙

1. 체크리스트 항목 클릭 시 완료 토글은 **낙관적 업데이트 + XP 카운트 즉시 반영** (실패 시 롤백).
2. 6개 섹션 카드는 호버/포커스 시 살짝 상승. 키보드 Tab 순회 가능.
3. ⋯ 메뉴는 외부 클릭·Esc 닫힘.
4. 다크모드 토글은 이 화면에 노출 안 함 — `/settings`에서 관리.
5. 페이지 진입 시 `document.title = "NSS Word Master"`.
6. `localStorage`에 `nss.view` 키로 마지막 섹션 기억 (이미 프로토타입에서 사용).

---

## ♿ 접근성

- 6개 섹션 카드는 `<button aria-label="English — open">` 형태.
- 진행바는 `role="progressbar" aria-valuenow="31" aria-valuemin="0" aria-valuemax="100"`.
- 체크박스는 `role="checkbox" aria-checked="true|false"`.
- 포커스 링은 `outline: 2px solid var(--english-primary); outline-offset: 2px;` (섹션별 컬러).

---

## 📱 반응형 (v1 범위 외지만 힌트)

- 1024px 이하: 우측 컬럼을 아래로 스택.
- 768px 이하: 단일 컬럼, 6 카드 2열, MascotPlaceholder 제거.

프로덕션 단계에서 세부 확정.
