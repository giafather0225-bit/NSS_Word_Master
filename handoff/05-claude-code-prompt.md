# 05 · Claude Code Prompt (복붙용)

아래 블록을 **Claude Code 세션의 첫 메시지**로 그대로 붙여 넣으세요.
저장소에 `handoff/` 폴더가 함께 있으면 Claude Code가 참고 문서를 읽고 구현을 시작합니다.

---

```
You are implementing NSS Word Master — a warm, stationery-themed study app for 3rd-grade students.
Target in this batch: Dashboard Hub + Diary section (4 screens).

📚 READ THESE FILES FIRST (in order), then plan, then build:
1. handoff/README.md                — scope & folder map
2. handoff/01-design-system.md      — color / type / radius / shadow tokens + Style Variants (Decorated vs Minimal)
3. handoff/02-dashboard-spec.md     — full component spec for the Dashboard Hub screen
4. handoff/02b-diary-spec.md        — full component spec for the 4 Diary screens (Decorated variant, hub-level)
5. handoff/03-data-contracts.md     — API shapes and SQLite schema (Dashboard + Diary)
6. handoff/04-implementation-guide.md — stack, folder layout, DoD

Reference files you can inspect but do not modify:
- handoff/reference/theme.css        — copy into frontend/css/theme.css verbatim
- handoff/reference/Home.jsx         — Dashboard React prototype (visual reference only; do NOT use React)
- handoff/reference/DiaryScreens.jsx — Diary React prototype for all 4 screens (visual reference only)
- handoff/reference/Dashboard.html   — standalone preview of the Dashboard screen

🛠️ STACK (non-negotiable)
- Backend: Python 3.11+, FastAPI, SQLite (SQLAlchemy optional), Pydantic v2
- Frontend: Vanilla JS (ES modules), HTML, CSS. No frameworks. No bundlers beyond simple static serving via FastAPI StaticFiles.
- Browsers: Chrome + Safari, latest 2 versions, 1280×900 desktop baseline (MacBook Air).

🎯 SCOPE (this task)
Dashboard Hub:
- Implement Dashboard at `/`.
- Endpoints: `GET /api/v1/dashboard`, `PATCH /api/v1/tasks/{id}`.
- Seed demo user "Gia" + 12 tasks via `backend/seed.py`.

Diary section (new):
- Implement 4 screens at `/diary` (Home), `/diary/write`, `/diary/entry/:id`, `/diary/calendar`.
- Diary is **hub-level** — NO sidebar on any Diary screen, full 1280px width.
- Endpoints: see `03-data-contracts.md` Diary section.
- Diary uses **Decorated** style variant exclusively (washi tape, polaroids, Caveat handwriting, ruled paper, etc.).
- Do NOT ship the Decorated/Minimal toggle from `Diary Preview.html` — Diary is always Decorated in production.

Everything else (English / Math / Arcade / Shop / Review / Parent / Settings) = placeholder pages showing route name + "Coming soon".

🎨 DESIGN RULES (strict)
- Use `var(--token)` from theme.css for every color, spacing, radius, and shadow. No hex literals anywhere except inside theme.css.
- Dashboard section cards: identical size (`aspect-ratio: 1/1`), Quicksand title only, no icon/gradient inside card. Minimal variant.
- Diary screens: Decorated variant — washi tape, polaroid tilt (±1.5°), Caveat handwriting for prompts/titles/body, ruled paper background.
- Lucide icons (inline SVG) for UI glyphs. Emoji are ALLOWED only inside diary body text (user-inserted stickers) and in the Diary sticker tray.
- Fonts (load from Google Fonts):
  - Quicksand: display / card titles
  - Nunito: body / buttons
  - Caveat, Patrick Hand, Shadows Into Light, Indie Flower, Kalam: Diary font picker options
- Warm cream background `var(--bg-page)` across the whole app.
- Cards: 1px `var(--border-subtle)` + `var(--shadow-soft)`. Hover: translateY(-2px) + softer elevated shadow.

🧭 IMPLEMENTATION ORDER
1. Scaffold folder layout from `04-implementation-guide.md`.
2. Copy `theme.css` into `frontend/css/`.
3. Build the API first (Dashboard first, then Diary), seed DB, verify shapes match `03-data-contracts.md`.
4. Implement Dashboard Hub end-to-end and verify visually against `reference/Dashboard.html`.
5. Implement Diary screens in this order:
   a. Shared primitives: `DiaryChrome`, `WashiTape`, `DiaryPill`, `MoodDot`, style resolvers (font/size/color/bg)
   b. Diary Home (2×2 grid)
   c. Write screen (mode segmented control, photo strip, mood popover, Style & Decor tools)
   d. Entry screen (read-only, style restoration, prev/next page nav, Delete confirm)
   e. Calendar (month grid with missed-day dashed cells)
6. Wire routing so Diary screens hide the sidebar.
7. Implement localStorage seed handoff for Home → Write (`nss.diary.seed.mode` / `nss.diary.seed.prompt`).
8. Hook the existing AI Assistant panel (`ai-assistant-stt.js`, `ai-assistant-tts.js`) to Write's Speak/Listen buttons. NO new AI card UI inside Diary.
9. Run the DoD checklist.

✅ DEFINITION OF DONE
- `uvicorn backend.main:app --reload` serves the app at `http://localhost:8000/`.
- Dashboard matches `reference/Dashboard.html` side-by-side.
- All 4 Diary screens render at 1280×900 without scroll, matching `reference/DiaryScreens.jsx` behavior.
- Photo upload works end-to-end in Write, saved photos show in Entry + Home polaroids + Calendar mood dots.
- Style snapshot (font/size/textColor/bgMood) saved on Write, restored exactly on Entry.
- Sticker click inserts emoji at textarea caret position in Write.
- Entry Delete button shows confirm popover; Entry has NO Edit button, NO Ask buddy button, NO "Write tomorrow" button.
- Calendar has NO "Write today's page" CTA; missed past days show dashed border + small gray dot.
- Every item in `04-implementation-guide.md` test checklist passes.
- Root `README.md` explains install, seed, run.

❓ WHEN IN DOUBT
- If a visual detail isn't in the spec, match the reference JSX/HTML exactly.
- If a data field isn't in the spec, propose it in your plan before coding — do NOT invent silently.
- Never add content (sections, copy, icons, AI cards) that isn't explicitly in the spec.
- The AI Assistant in Diary is the **existing global panel** (ai-assistant-stt.js / ai-assistant-tts.js). Do not create a new AI feedback card in Diary.

Start by reading the six handoff docs, then reply with a short plan (8-12 bullets covering Dashboard + Diary phases), then proceed to build.
```

---

## 사용 팁

- 저장소 루트에 `handoff/` 폴더 전체를 커밋한 상태에서 위 프롬프트를 붙여 넣으면 Claude Code가 문서를 차례로 읽고 계획을 세웁니다.
- 디자인 피드백이 필요할 때는 `reference/Dashboard.html`과 `reference/DiaryScreens.jsx` 내부 주석을 참고하도록 지시하세요.
- 추후 English/Math 화면을 추가할 때는 `06-english-spec.md`, `07-math-spec.md` 포맷으로 이어붙이면 됩니다.
- Diary 내부의 Decorated ↔ Minimal 토글은 디자인 비교용이므로 프로덕션에는 탑재하지 말 것.
