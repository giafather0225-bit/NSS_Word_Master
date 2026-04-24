# 01 · Design System Tokens

모든 토큰은 `reference/theme.css`에 CSS 변수로 정의되어 있습니다. **반드시 `var(--token)` 형태로만 사용하고 하드코딩된 hex 값은 쓰지 마세요.**

---

## 🎨 Color — Section palette (B · Pinterest Schoolgirl Diary)

각 섹션은 5-tone 세트를 가진다: `primary`(본색) · `hover` · `light`(배경) · `soft`(중간) · `ink`(짙은 텍스트).

| Section  | Primary   | Light     | Ink       | Usage                              |
|----------|-----------|-----------|-----------|------------------------------------|
| English  | `#7FA8CC` | `#EEF4FA` | `#345A80` | Baby Blue — 학습 / 단어             |
| Math     | `#8AC4A8` | `#EEF7F2` | `#3A6A54` | Fresh Mint — 논리 / 수학            |
| Diary    | `#E09AAE` | `#FBEEF2` | `#84425A` | Sweet Pink — 쓰기 / 감정            |
| Arcade   | `#EEC770` | `#FBF3DE` | `#7A5A1E` | Butter Yellow — 게임 / XP 뱃지       |
| Shop     | `#B8A4DC` | `#F2ECFA` | `#5A4883` | Soft Lavender — 리워드               |
| Review   | `#EBA98C` | `#FBEBE0` | `#844A30` | Peach — 복습                         |

토큰 이름: `--{section}-primary`, `--{section}-light`, `--{section}-soft`, `--{section}-ink`, `--{section}-hover`
예: `var(--english-primary)`, `var(--diary-light)`

### Semantic
- `--color-success` `#8FBF87`
- `--color-error`   `#D97A7A`
- `--color-warning` `#EEC770`

### Neutrals (warm cream)
- `--bg-page`     `#FAF6EF` — 페이지 배경 (크림)
- `--bg-card`     `#FFFFFF`
- `--bg-sidebar`  `#F4EEE4`
- `--bg-surface`  `#EFE8DB` — 칩 / 호버
- `--text-primary`   `#2B2722`
- `--text-secondary` `#706659`
- `--text-hint`      `#A79A89`
- `--border-default` `#DCD2C2`
- `--border-subtle`  `#EBE3D5`

### Dark mode
`<html data-theme="dark">`를 설정하면 warm dark(브라운 베이스 + 파스텔 액센트)로 전환. 모든 컴포넌트는 토큰만 사용하면 자동으로 대응됩니다.

---

## ✍️ Typography

| Family            | Token                       | Where                           |
|-------------------|-----------------------------|----------------------------------|
| **Nunito**        | `--font-family`             | 본문 · 버튼 · 리스트              |
| **Quicksand**     | `--font-family-display`     | 헤드라인 · 카드 타이틀 · 숫자 강조 |
| **Caveat**        | `--font-family-hand`        | 손글씨 액센트 (옵션)               |
| ui-monospace      | `--font-family-mono`        | 타이머, 코드                      |

Google Fonts 로드:
```html
<link href="https://fonts.googleapis.com/css2?family=Quicksand:wght@400;500;600;700&family=Nunito:wght@400;500;600;700;800&family=Caveat:wght@400;600&display=swap" rel="stylesheet"/>
```

### Scale

| Token              | px  | Example use            |
|--------------------|-----|------------------------|
| `--font-size-xs`   | 12  | hint, badge            |
| `--font-size-sm`   | 14  | caption, subtitle      |
| `--font-size-md`   | 16  | body                   |
| `--font-size-lg`   | 18  | card title small       |
| `--font-size-xl`   | 24  | section heading        |
| `--font-size-2xl`  | 32  | page heading           |
| `--font-size-3xl`  | 44  | display                |

Weights: 400 / 500 / 600 / 700 (`--font-weight-normal` … `--font-weight-extra`).

**규칙**
- 헤드라인은 `letter-spacing: -0.02em`, `line-height: 1.15–1.25`
- 본문은 `line-height: 1.5`
- UPPERCASE 라벨은 `letter-spacing: 0.08em`, `font-weight: 700`, `font-size: 10.5–11px`

---

## 📏 Radius

| Token              | px  | Use                    |
|--------------------|-----|------------------------|
| `--radius-sm`      | 8   | chip, small button     |
| `--radius-md`      | 12  | input, mid button      |
| `--radius-lg`      | 16  | card (compact)         |
| `--radius-xl`      | 20  | card (default)         |
| `--radius-2xl`     | 28  | hero / modal           |
| `--radius-full`    | 9999| pill, avatar           |

대시보드 6개 섹션 카드는 `--radius-xl` (20px).

---

## 🌑 Shadow

- `--shadow-soft`  `0 2px 10px rgba(120,90,60,.06)` — 모든 카드 기본
- `--shadow-modal` `0 10px 30px rgba(90,65,40,.12)` — 모달, 오버레이
- 호버 상승: `transform: translateY(-2px)` + `0 8px 20px rgba(120,90,60,.08)`

---

## 📐 Spacing

표준 grid gap / padding: **4 · 8 · 12 · 14 · 16 · 18 · 20 · 24 · 28 · 36 · 48**.

- 카드 내부 padding: 16–20px
- 카드 간 gap: 14–16px
- 메인 컬럼 gap: 24–28px
- 페이지 좌우 padding: 36px (데스크톱 1280px 기준)

---

## 🎞️ Motion

- `--transition-fast`   0.12s — 호버 색 전환
- `--transition-normal` 0.18s — 카드 상승
- `--transition-slow`   0.3s  — 진행바 width

모든 호버/액티브는 `cubic-bezier` 기본(ease) 사용. 과한 스프링 없음.

---

## 🔩 Misc

- `--sidebar-width` `232px`
- `--progress-bar-height` `2px`, `--progress-bar-height-lg` `6px`

---

## 🎭 Style Variants — Decorated vs Minimal

**두 가지 섹션-레벨 스타일 변형.** 한 섹션은 **하나만** 사용. 절대 섞지 마세요.

### 섹션별 할당

| Section | Variant | 이유 |
|---|---|---|
| **Diary** | **Decorated** | 감정·기록 — 따뜻함이 효율보다 우선 |
| **Dashboard (Hub)** | Minimal | 진입점 — 차분하고 스캔 가능해야 |
| **English** | Minimal | 학습 집중 — 시각 노이즈 제거 |
| **Math** | Minimal | 논리 집중 — 페이지를 조용하게 |
| **Arcade** | Minimal (플레이풀 컬러만) | 재미는 모션·컬러로, 장식으로가 아님 |
| **Shop (Rewards)** | Minimal | 제품 그리드 — 아이템이 곧 장식 |
| **Review** | Minimal | 오답 복습 — 학습자 방해 금지 |
| **Parent** | Minimal | 기능적 / 정보적 |

**원칙**: *감정*이 콘텐츠인 곳만 Decorated. 그 외엔 무조건 Minimal.

### Decorated — 허용 요소 (이 목록 외 금지)

| 요소 | 구현 위치 | 비고 |
|---|---|---|
| **Washi tape** | `DiaryScreens.jsx`의 `<WashiTape/>` | 파스텔 띠, 대각선 그라디언트, ±3°~±8° 회전. 카드당 1–2개, 상단에만. |
| **Polaroid cards** | `PolaroidEntry` | 흰 프레임, tilt ±1.5°, soft shadow, 상단에 "photo" swatch. 호버 시 수평 복귀. |
| **Caveat 손글씨** | `"Caveat", cursive` | 프롬프트·타이틀·본문. 22–32px. |
| **노트 줄 배경** | `repeating-linear-gradient(180deg, #fff 0 31px, var(--diary-light) 31px 32px)` | Write / Entry 종이 표면. |
| **대형 컬러 도트** | 28px mood 원 + 흰 보더 | 주간 스트립, Entry 메타. |
| **Word stickers** | `--english-soft` 보더의 rounded pill | Entry에서 사용된 단어. |

회전·기울기(transform rotate)는 **Decorated에서만**.

### Minimal — 규칙

**타이포그래피**
- Quicksand(display) + Nunito(body). **Caveat 금지.**
- Letter-spacing: display는 `-0.02em`, eyebrow 라벨만 `0.08em uppercase`.

**컬러**
- 파스텔 섹션 색은 쓰되 **플랫 fill만.**
- 예외 허용 그라디언트: CTA 카드의 `linear-gradient(160deg, var(--section-light), #fff)`.
- **그라디언트 텍스트·보더 금지.**

**형태·장식**
- Washi tape ❌, Polaroid tilt ❌, 모든 `transform: rotate(*)` ❌.
- `::before`/`::after` 장식 마크 ❌.
- 라운드: `--radius-md` (12) / `--radius-lg` (16) / `--radius-xl` (20). 2xl(28)은 대형 패널 전용.
- 그림자: `--shadow-soft`만. 호버 lift는 `translateY(-2px)` 최대.

**레이아웃**
- 폴라로이드가 아닌 **리스트**.
- 그리드 정렬, 직사각형 모양.
- Mood 도트는 **12–14px** — 스티커 크기로 키우지 말 것.

**아이콘**
- Lucide 스타일만 (strokeWidth 1.6). **이모지 금지.**

### 체크리스트 (장식 추가 전)

1. 이 요소가 들어갈 섹션은 어디? Minimal이면 **중단**.
2. 기능적인가 장식적인가? 장식은 Decorated 전용.
3. 회전/기울기가 있는가? Decorated 전용.
4. 손글씨인가? Decorated 전용.
5. 제거해도 의미 전달되나? 그렇다면 Minimal에서는 제거.

### 참고 파일
- Decorated 구현 레퍼런스: `design/components/DiaryScreens.jsx`
- Minimal 구현 레퍼런스: `design/components/Home.jsx`
- Decorated ↔ Minimal 시각 비교: `Diary Preview.html` (참고용, 프로덕션 탑재 금지)
- 규칙 요약: `design/STYLE_RULES.md`

---

## 🧱 Component primitives (구현 시 공통화 권장)

다음 3개는 대시보드 전반에 재사용되니 유틸 클래스 또는 컴포넌트로 먼저 만드세요.

1. **`.card`** — `background: var(--bg-card); border: 1px solid var(--border-subtle); border-radius: var(--radius-xl); box-shadow: var(--shadow-soft);`
2. **`.pill`** — `padding: 3px 10px; border-radius: var(--radius-full); font-size: 10.5px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em;`
3. **`.progress-bar`** — `height: 4–8px; border-radius: var(--radius-full); background: var(--bg-surface); overflow: hidden;` 내부 fill은 섹션 primary.
