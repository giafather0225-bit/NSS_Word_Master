# 04 · Implementation Guide

**스택**: Python FastAPI + SQLite (백엔드) / Vanilla JS + HTML + CSS (프론트엔드)
브라우저 지원: Chrome, Safari (최신 2버전)
타겟 해상도: 데스크톱 1280px (v1)

---

## 🏗️ 권장 폴더 구조

```
project/
├── backend/
│   ├── main.py                  ← FastAPI 엔트리
│   ├── db.py                    ← SQLite 연결 + 스키마
│   ├── routes/
│   │   ├── dashboard.py         ← GET /api/v1/dashboard
│   │   └── tasks.py             ← PATCH /api/v1/tasks/{id}
│   ├── models.py                ← Pydantic 모델
│   └── seed.py                  ← 더미 데이터 삽입
├── frontend/
│   ├── index.html               ← 대시보드 진입점
│   ├── css/
│   │   └── theme.css            ← handoff/reference/theme.css 복사
│   ├── js/
│   │   ├── api.js               ← fetch 래퍼
│   │   ├── dashboard.js         ← 화면 렌더
│   │   ├── components/
│   │   │   ├── sectionCard.js
│   │   │   ├── todayChecklist.js
│   │   │   ├── weeklyStrip.js
│   │   │   ├── statsStack.js
│   │   │   └── topRightMenu.js
│   │   └── icons.js             ← lucide 아이콘 helper
│   └── assets/                  ← 폰트, 마스코트 placeholder 이미지
└── requirements.txt
```

---

## 🐍 FastAPI 뼈대

**`backend/main.py`**
```python
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from routes import dashboard, tasks

app = FastAPI(title="NSS Word Master API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # dev only
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(dashboard.router, prefix="/api/v1")
app.include_router(tasks.router, prefix="/api/v1")

# Serve the static frontend at /
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
```

**`backend/routes/dashboard.py`**
```python
from fastapi import APIRouter, Header
from datetime import date
import db

router = APIRouter()

@router.get("/dashboard")
def get_dashboard(user_id: str = Header(default="u_001")):
    user = db.get_user(user_id)
    tasks = db.get_today_tasks(user_id, date.today())
    stats = db.get_user_stats(user_id)
    weekly = db.get_weekly_activity(user_id)
    world = db.get_user_world(user_id, "ocean")
    return {
        "user": user,
        "greeting": {"date_iso": date.today().isoformat(),
                     "time_of_day": _time_of_day()},
        "tasks": {"groups": _group_by_section(tasks)},
        "stats": stats,
        "weekly": weekly,
        "world": world,
    }
```

---

## 🖥️ 프론트 구현 지침

### 1. 아이콘
**lucide** 아이콘을 SVG 인라인으로 사용. 필요한 것만:
- `more-horizontal`, `users`, `settings`, `check`, `book-open`, `sparkles`, `flame`, `chevron-right`

`frontend/js/icons.js`에 얇은 헬퍼:
```js
export function icon(name, size = 16, color = "currentColor") {
  const paths = ICON_PATHS[name];
  return `<svg width="${size}" height="${size}" viewBox="0 0 24 24"
            fill="none" stroke="${color}" stroke-width="2"
            stroke-linecap="round" stroke-linejoin="round">${paths}</svg>`;
}
```

### 2. CSS 사용 규칙
- `handoff/reference/theme.css` 전체를 `frontend/css/theme.css`로 그대로 복사.
- **모든 색·간격·라운드·그림자는 `var(--token)` 사용.** hex/rgb 금지.
- 컴포넌트별 CSS는 BEM 또는 `[data-component="section-card"]` 속성 선택자 추천.

### 3. 렌더 전략
v1은 SPA가 아니라 vanilla DOM. 구조:
```js
// dashboard.js
async function init() {
  const data = await api.get("/api/v1/dashboard");
  document.getElementById("greeting").innerHTML = renderGreeting(data.user, data.greeting);
  document.getElementById("today-tasks").innerHTML = renderChecklist(data.tasks);
  document.getElementById("section-grid").innerHTML = renderSectionGrid();
  document.getElementById("weekly").innerHTML = renderWeeklyStrip(data.weekly);
  document.getElementById("stats").innerHTML = renderStatsStack(data.stats);
  document.getElementById("world").innerHTML = renderWorld(data.world);
  bindEvents();
}
```

### 4. 체크리스트 토글 (낙관적 업데이트)
```js
async function onToggleTask(taskId, nextDone) {
  // 1. 즉시 UI 반영
  setTaskDoneLocally(taskId, nextDone);
  recalcProgressLocally();
  try {
    const res = await api.patch(`/api/v1/tasks/${taskId}`, { done: nextDone });
    syncXpFromServer(res.user);
  } catch (err) {
    // 실패 시 롤백
    setTaskDoneLocally(taskId, !nextDone);
    recalcProgressLocally();
    toast("Could not save. Try again.");
  }
}
```

### 5. HTML 뼈대 (`frontend/index.html`)
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=1280"/>
  <title>NSS Word Master</title>
  <link rel="stylesheet" href="/css/theme.css"/>
  <link rel="stylesheet" href="/css/dashboard.css"/>
  <link rel="preconnect" href="https://fonts.googleapis.com"/>
  <link href="https://fonts.googleapis.com/css2?family=Quicksand:wght@400;500;600;700&family=Nunito:wght@400;500;600;700;800&family=Caveat:wght@400;600&display=swap" rel="stylesheet"/>
</head>
<body>
  <main class="dashboard">
    <div id="top-right-menu"></div>
    <div class="dashboard-grid">
      <aside class="col-left">
        <div id="greeting"></div>
        <div id="today-tasks"></div>
      </aside>
      <section class="col-center">
        <div id="header-bar"></div>
        <div id="section-grid"></div>
        <div id="weekly"></div>
      </section>
      <aside class="col-right">
        <div id="stats"></div>
        <div id="world"></div>
      </aside>
    </div>
    <div id="mascot"></div>
  </main>
  <script type="module" src="/js/dashboard.js"></script>
</body>
</html>
```

### 6. 키 이벤트
- Esc → ⋯ 메뉴 닫기
- Tab → 섹션 카드 순회
- Space/Enter → 활성 카드 이동 / 체크박스 토글

---

## 🧪 테스트 체크리스트

구현 완료 후 최소한 다음이 맞는지 확인:

**디자인 충실도**
- [ ] 크림 배경 `#FAF6EF`이 전 영역에 깔려 있다.
- [ ] 6개 섹션 카드가 **모두 동일 크기**(`aspect-ratio: 1/1`)로 3×2 배치.
- [ ] 카드 안에 아이콘/그라디언트/서브 텍스트 없이 **이름만**.
- [ ] Today's tasks에 섹션별 그룹(색 도트 + 라벨)이 보이고, NOW 뱃지가 해당 항목에 붙는다.
- [ ] 우측 상단 ⋯ 버튼을 누르면 Parent Dashboard / Settings 드롭다운이 열린다.
- [ ] 우측 하단 GIA 마스코트 플레이스홀더가 `fixed` 위치에 있다.
- [ ] 🔥 이모지가 아닌 lucide `flame` 아이콘이 streak 옆에 표시된다.

**상호작용**
- [ ] 체크박스 클릭 → 즉시 선 긋기/opacity 변경, API 응답 후 XP 동기화.
- [ ] 섹션 카드 클릭 → 해당 라우트로 이동 (v1은 placeholder 페이지로도 OK).
- [ ] ⋯ 메뉴 외부 클릭/Esc → 닫힘.
- [ ] 다크모드 토큰만 바뀌어도 전 화면이 자연스럽게 전환.

**백엔드**
- [ ] `GET /api/v1/dashboard` 응답이 `03-data-contracts.md` 스키마와 1:1 일치.
- [ ] `PATCH /api/v1/tasks/{id}` 후 `users.xp_current`가 증가/감소.
- [ ] SQLite 파일이 `./data/app.db`에 생성되고 `seed.py`로 더미 유저 1명(Gia) + 12 tasks 삽입.

**접근성**
- [ ] 모든 버튼에 `aria-label` 또는 텍스트가 있다.
- [ ] 키보드만으로 체크리스트 토글 + 섹션 이동이 가능하다.
- [ ] 포커스 링이 섹션 컬러로 표시된다.

---

## 🚦 DoD (Definition of Done)

1. `uvicorn backend.main:app --reload` 실행 후 `http://localhost:8000/`에서 대시보드 로드.
2. 프로토타입(`reference/Dashboard.html`)과 **시각적으로 동일**.
3. 위 체크리스트가 모두 통과.
4. README에 실행 방법·환경변수·시드 절차 기록.
