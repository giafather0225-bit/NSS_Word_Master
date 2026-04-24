# NSS Word Master — Handoff Package (Dashboard + Diary)

이 폴더는 **Dashboard Hub + Diary 섹션(4개 화면)**을 실제 제품으로 옮기기 위한 개발 핸드오프 패키지입니다.
Claude Code에게 그대로 넘겨서 구현을 진행할 수 있도록 디자인 시스템 · 컴포넌트 스펙 · 데이터 계약 · 프롬프트까지 모두 정리되어 있습니다.

---

## 📁 폴더 구조

```
handoff/
├── README.md                     ← 지금 이 파일
├── 01-design-system.md           ← 색·타입·간격·라운드·그림자 토큰 + Style Variants(Decorated/Minimal)
├── 02-dashboard-spec.md          ← 대시보드 화면 전체 스펙 (Minimal 변형)
├── 02b-diary-spec.md             ← Diary 4개 화면 스펙 (Decorated 변형, hub-level)
├── 03-data-contracts.md          ← 프론트가 기대하는 API/데이터 형태 (Dashboard + Diary)
├── 04-implementation-guide.md    ← 기술 스택별 구현 지침 (FastAPI + Vanilla JS + SQLite)
├── 05-claude-code-prompt.md      ← Claude Code에게 붙여넣을 프롬프트 (복붙용)
└── reference/
    ├── theme.css                 ← 디자인 토큰 CSS (그대로 사용 가능)
    ├── Home.jsx                  ← 대시보드 React 프로토타입 (Minimal 레퍼런스)
    ├── DiaryScreens.jsx          ← Diary 4화면 React 프로토타입 (Decorated 레퍼런스)
    └── Dashboard.html            ← 대시보드 standalone 프리뷰
```

---

## 🎯 포함된 범위

**✅ 이 패키지의 범위**

**Dashboard Hub (`/`)**
- 좌측 Today's Tasks · 중앙 6개 섹션 카드 + Weekly Strip · 우측 Stats + Ocean World
- 우측 상단 ⋯ 오버플로 메뉴 (Parent Dashboard / Settings 진입)
- 우측 하단 GIA 마스코트 플레이스홀더
- 클릭 시 이동할 라우트 URL 규약

**Diary 섹션 (hub-level, 사이드바 없음)**
- `/diary` — **Diary Home** (2×2 그리드: Mode CTA, Prompt, Week mood + Recent polaroids, Stats)
- `/diary/write` — **Write** (Journal / Free Write, 사진, Mood 팝오버, Style/Decor 툴, Sticker tray, 7 폰트, 7 색)
- `/diary/entry/:id` — **Entry** (읽기 전용, 저장된 스타일 복원, 앞뒤 페이지 네비, Delete 확인 팝오버)
- `/diary/calendar` — **Calendar** (월별 mood 그리드, missed day 표시, Legend + Summary)

**🚧 이 패키지의 범위가 아닌 것**
- English 5-step 학습 화면 / Math 상세 / Shop / Review / Parent Dashboard / Settings
- 인증, 결제, 푸시
- 모바일 레이아웃 (데스크톱 1280×900 기준)

---

## 🚀 Claude Code에게 넘기는 방법

1. 이 폴더 `handoff/` 전체를 저장소 루트에 복사한다.
2. `05-claude-code-prompt.md` 내용을 그대로 Claude Code 세션 **첫 메시지**로 붙여 넣는다.
3. Claude Code는 문서 6개를 순서대로 읽고 8-12 bullet 계획을 반환한 뒤 구현을 시작한다.

---

## ✨ 디자인 원칙 요약

- **Pinterest Schoolgirl Diary 톤** — 크림 페이지(#FAF6EF) + 파스텔 섹션 컬러
- **둥글고 따뜻한 스테이셔너리 언어** — 16–28px radius, 부드러운 soft shadow
- **하나의 카드 = 하나의 이름** — 아이콘·장식·그라디언트 최소화, 이름만 크게 (Dashboard)
- **섹션 컬러 6가지** — English(Baby Blue) / Math(Mint) / Diary(Pink) / Arcade(Butter) / Shop(Lavender) / Review(Peach)
- **타입 시스템**
  - Nunito (본문), Quicksand (디스플레이)
  - **Diary 전용**: Caveat + Patrick Hand + Shadows Into Light + Indie Flower + Kalam (사용자 선택)

## 🎭 Style Variants — 섹션별 규칙

**한 섹션은 하나의 변형만 사용. 절대 섞지 마세요.**

| Section | Variant |
|---|---|
| Diary | **Decorated** (워싱테이프·폴라로이드·Caveat 손글씨·노트 줄 배경·스티커·7색 페이지) |
| Dashboard · English · Math · Arcade · Shop · Review · Parent | **Minimal** (플랫 파스텔·장식 없음·rotation 금지) |

규칙 상세: `01-design-system.md` "Style Variants" 섹션.
Diary 내부 비교용 `Diary Preview.html`의 Decorated↔Minimal 토글은 **프로덕션 미탑재**.

---

## 🧭 Diary 4화면 핵심 요약

| 화면 | 역할 | 들어가는 경로 |
|---|---|---|
| **Home** | 입구 · 갤러리 · 허브 | Dashboard → Diary 카드 |
| **Write** | 작성소 (Journal / Free Write) | Home CTA, Prompt 카드 |
| **Entry** | 기록 열람실 (읽기 전용) | Home 폴라로이드, Calendar 날짜, Write Save 직후 |
| **Calendar** | 월간 지도 | Home "Month view →" |

**Diary의 핵심 원칙**
- Entry는 **읽기 전용** — Edit / Write CTA / AI 카드 없음, Delete만 (확인 팝오버)
- Calendar는 **탐색 화면** — 작성 CTA 없음, missed day는 dashed 보더로 표시
- AI Assistant (Siri 스타일)는 **기존 전역 패널 재사용** — Diary 내 별도 AI UI 없음
- 사용자가 Write에서 설정한 **font / size / color / bg / 스티커**는 Entry에서 그대로 복원됨
