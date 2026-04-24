# 03 · Data Contracts

프론트엔드 대시보드가 기대하는 데이터 형태입니다. 백엔드(FastAPI + SQLite)가 이 스펙에 맞춰 JSON을 반환하면 됩니다.

모든 엔드포인트는 `/api/v1/` 접두사 기준. 인증 방식은 v1에서 세션 쿠키 또는 단순 `user_id` 헤더로 가정.

---

## GET `/api/v1/dashboard`

대시보드 진입 시 단 한 번 호출하여 모든 위젯 데이터를 수신.

### Response

```json
{
  "user": {
    "id": "u_001",
    "name": "Gia",
    "grade": 3,
    "crew": "Ocean crew",
    "level": 1,
    "xp_current": 31,
    "xp_next_level": 100
  },
  "greeting": {
    "date_iso": "2026-04-24",
    "time_of_day": "morning"
  },
  "tasks": {
    "groups": [
      {
        "section": "english",
        "label": "English",
        "items": [
          { "id": "e1", "label": "Voca · Lesson 07 Preview",     "xp": 10, "done": true,  "due": null },
          { "id": "e2", "label": "Voca · Word Match (3 rounds)", "xp": 15, "done": true,  "due": null },
          { "id": "e3", "label": "Voca · Fill the Blank",        "xp": 15, "done": false, "due": "now" },
          { "id": "e4", "label": "Voca · Spelling Master",       "xp": 20, "done": false, "due": null },
          { "id": "e5", "label": "Voca · Make a Sentence (×3)",  "xp": 20, "done": false, "due": null }
        ]
      },
      {
        "section": "math",
        "label": "Math",
        "items": [
          { "id": "m1", "label": "Multiply by 6 · Learn",      "xp": 10, "done": false, "due": null },
          { "id": "m2", "label": "Multiply by 6 · Practice 1", "xp": 15, "done": false, "due": null },
          { "id": "m3", "label": "Fact Fluency · 60 sec",      "xp": 10, "done": false, "due": null },
          { "id": "m4", "label": "Kangaroo · 3 problems",      "xp": 15, "done": false, "due": null }
        ]
      },
      {
        "section": "diary",
        "label": "Diary",
        "items": [
          { "id": "d1", "label": "3 sentences with new words", "xp": 15, "done": false, "due": null },
          { "id": "d2", "label": "Today's mood check-in",       "xp": 5,  "done": false, "due": null }
        ]
      },
      {
        "section": "review",
        "label": "Review",
        "items": [
          { "id": "r1", "label": "Yesterday's wrong problems", "xp": 15, "done": false, "due": null }
        ]
      }
    ]
  },
  "stats": {
    "words_learned": { "value": 342,  "sub": "all-time" },
    "total_xp":      { "value": 1250, "sub": "+45 today" },
    "streak":        { "value_days": 5, "best_days": 12 }
  },
  "weekly": {
    "days": [
      { "label": "S", "value": 0.3 },
      { "label": "M", "value": 0.8 },
      { "label": "T", "value": 0.6 },
      { "label": "W", "value": 1.0 },
      { "label": "T", "value": 0.4 },
      { "label": "F", "value": 0.9 },
      { "label": "S", "value": 0.0 }
    ],
    "streak_days": 5
  },
  "world": {
    "id": "ocean",
    "name": "Ocean World",
    "collected": 3,
    "total": 10,
    "illustration_url": null
  }
}
```

**주요 필드 설명**
- `tasks.groups[].section` — 색 토큰 매핑용. enum: `english` · `math` · `diary` · `arcade` · `shop` · `review`
- `tasks.groups[].items[].due` — `null` | `"now"` | `"overdue"` (v1은 `null`과 `"now"`만 사용)
- `weekly.days[].value` — 0.0 ~ 1.0. 프론트가 막대 높이 계산에 사용.
- `stats.*.sub` — 카드 우측에 표시되는 보조 텍스트.

---

## PATCH `/api/v1/tasks/{task_id}`

체크리스트 항목 완료 토글.

### Request

```json
{ "done": true }
```

### Response

```json
{
  "task": { "id": "e3", "done": true, "xp": 15 },
  "user": { "xp_current": 46, "level": 1 },
  "xp_earned_delta": 15
}
```

프론트는 낙관적 업데이트 후 이 응답으로 XP 막대와 진행 카운트를 동기화.

---

---

## 📔 Diary 섹션 API

Diary는 **hub-level** 화면 (사이드바 없음). 4개 화면 / 3개 라우트 prefix:
- `/diary` (Home), `/diary/write`, `/diary/entry/:id`, `/diary/calendar`

### Types

```ts
type Mood      = 'great' | 'happy' | 'calm' | 'curious' | 'tired' | 'sad';
type FontKey   = 'nunito' | 'caveat' | 'patrick' | 'shadows' | 'indie' | 'kalam';
type SizeKey   = 's' | 'm' | 'l';
type ColorKey  = 'default' | 'diary' | 'english' | 'math' | 'arcade' | 'rewards' | 'review';
type BgMoodKey = 'default' | 'pink' | 'mint' | 'sky' | 'butter' | 'lavender' | 'peach';
```

### Endpoints

#### GET `/api/v1/diary?month=YYYY-MM`
한 달치 목록 + 스탯 + day off 목록 (Calendar / Home).

```json
{
  "entries": [
    {
      "id": "d_20260422",
      "date": "2026-04-22",
      "type": "journal",
      "mood": "great",
      "title": "Brave day",
      "prompt": "What made you smile today, even a little?",
      "body": "My reading test was hard, but I kept going… 🌸",
      "words_used": ["whisper", "brave"],
      "photos": [
        { "id": "ph1", "url": "/storage/diary/u_001/d_20260422/ph1.jpg", "name": "aquarium.jpg" }
      ],
      "xp": 15,
      "style": {
        "font": "caveat",
        "text_size": "m",
        "text_color": "diary",
        "bg_mood": "pink"
      }
    }
  ],
  "stats": { "entries": 18, "streak": 5, "words": 642, "day_off": 2 },
  "day_offs": [
    { "date": "2026-04-06", "status": "approved", "reason": "family trip" },
    { "date": "2026-04-13", "status": "approved", "reason": "sick" },
    { "date": "2026-04-17", "status": "pending",  "reason": null }
  ]
}
```

`day_offs[]` — 기존 앱의 `DayOffRequest` 테이블에서 해당 월 레코드. Calendar 셀 렌더에 사용. `status` enum: `pending` | `approved` | `rejected` (rejected는 Calendar에서 무시).

#### POST `/api/v1/day-offs`
아이가 Diary Home에서 day off 신청 (child-initiated).

Request:
```json
{ "date": "2026-04-25", "reason": "Family trip" }
```

- `date`: ISO yyyy-mm-dd, 반드시 **미래 날짜** (오늘 포함 불가)
- `reason`: optional, 60자 제한
- 서버 검증:
  - 이번 달 `approved` 개수가 이미 2이면 **400** (`DAY_OFF_LIMIT`)
  - 같은 날짜에 `pending` 또는 `approved`가 이미 있으면 **409** (`DAY_OFF_DUP`)

Response:
```json
{ "day_off": { "id": "do_42", "date": "2026-04-25", "status": "pending", "reason": "Family trip" } }
```

#### DELETE `/api/v1/day-offs/:id`
Pending 상태의 요청만 취소 가능. Approved는 400.

#### SQLite 스키마
기존 `DayOffRequest` 테이블 재사용. 참고용 스키마:

```sql
CREATE TABLE day_off_requests (
  id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL REFERENCES users(id),
  date TEXT NOT NULL,
  status TEXT CHECK(status IN ('pending','approved','rejected')) NOT NULL DEFAULT 'pending',
  reason TEXT,
  requested_at TEXT NOT NULL,
  decided_at TEXT,
  UNIQUE (user_id, date)
);
```

**월 사용 카운트 규칙**: `stats.day_off` = `approved` 상태의 해당 월 요청 수. `pending`은 소진으로 치지 않지만 신청 UI에서 "used"에는 포함시키지 않음.

#### GET `/api/v1/diary/:id`
단일 entry (Calendar 날짜 클릭 / Home 폴라로이드 클릭).

#### GET `/api/v1/diary/:id/neighbors`
Entry 하단 페이지 네비게이션용.

```json
{
  "prev": { "id": "d_20260421", "date": "2026-04-21", "title": "Whisper" },
  "next": { "id": "d_20260423", "date": "2026-04-23", "title": "The yellow fish" }
}
```

`prev` 또는 `next`가 없으면 `null`. Entry는 이 값으로 "No earlier pages" / "No later pages" 렌더.

#### POST `/api/v1/diary`
새 entry 생성 (Write → Save).

Request:
```json
{
  "type": "journal",
  "mood": "happy",
  "title": "The yellow fish",
  "prompt": "What made you smile today?",
  "body": "…",
  "style": { "font": "caveat", "text_size": "m", "text_color": "default", "bg_mood": "pink" }
}
```

Response: 생성된 `DiaryEntry` + `xp_earned_delta`.

**검증**
- `mode === 'journal'` 이 아니면 `prompt` 무시
- `words_used`는 서버가 본문 텍스트에서 레슨 단어 사전과 매칭해 자동 추출 (클라이언트가 보낸 값은 무시)
- `body` 공백 제거 기준 **15단어 이상**이어야 함 (미만이면 400)

#### PATCH `/api/v1/diary/:id`
내부 마이그레이션/관리 용도. **Entry 화면에서는 호출하지 않음** (Edit 버튼 제거됨).

#### DELETE `/api/v1/diary/:id`
확인 팝오버 통과 후 호출. 하드 삭제. 관련 사진 파일도 함께 삭제.

#### GET `/api/v1/diary/prompts?mode=journal`
PromptBank / PromptCard 프롬프트 풀.

```json
{
  "prompts": [
    "What made you smile today?",
    "A small thing that surprised you.",
    "Something you felt proud of.",
    "A word you learned today.",
    "A question you asked in your head."
  ]
}
```

#### POST `/api/v1/diary/:id/photos`  (multipart/form-data)
Photo 업로드. 양쪽 모드(Journal/Free Write) 모두 허용.

- 필드명: `files[]` (최대 3장, 이미 N장이 있으면 `3 - N`장까지)
- 허용 MIME: `image/jpeg`, `image/png`, `image/webp`, `image/heic`
- 최대 크기: 10MB/장
- 서버: EXIF 회전 정규화, 256×256 썸네일 별도 저장
- Response: `{ photos: DiaryPhoto[] }` (해당 entry의 **최종** 사진 배열)

#### DELETE `/api/v1/diary/:id/photos/:photoId`
개별 사진 삭제.

---

## SQLite 스키마 — Diary 추가

```sql
CREATE TABLE diary_entries (
  id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL REFERENCES users(id),
  date TEXT NOT NULL,                                   -- ISO yyyy-mm-dd
  type TEXT CHECK(type IN ('journal','free')) NOT NULL,
  mood TEXT CHECK(mood IN ('great','happy','calm','curious','tired','sad')) NOT NULL,
  title TEXT NOT NULL,
  prompt TEXT,                                          -- journal만
  body TEXT NOT NULL,                                   -- 스티커 이모지 포함한 원문
  words_used TEXT NOT NULL DEFAULT '[]',                -- JSON array
  xp INTEGER NOT NULL DEFAULT 15,
  style_json TEXT NOT NULL DEFAULT '{}',                -- {font,text_size,text_color,bg_mood}
  created_at TEXT NOT NULL,
  UNIQUE (user_id, date)                                -- 하루 한 entry 원칙 (정책이 바뀌면 제거)
);

CREATE TABLE diary_photos (
  id TEXT PRIMARY KEY,
  entry_id TEXT NOT NULL REFERENCES diary_entries(id) ON DELETE CASCADE,
  url TEXT NOT NULL,
  thumb_url TEXT,
  name TEXT,
  width INTEGER,
  height INTEGER,
  sort_order INTEGER DEFAULT 0
);

CREATE INDEX idx_diary_user_date ON diary_entries(user_id, date);
```

### Dashboard 연계
- Diary entry 저장 시 `daily_activity`의 해당 날짜 행을 `+15 XP` 업데이트 → WeeklyStrip 막대 높이 반영
- `stats.streak` 계산 시 `diary_entries.date` 연속성도 포함 (대시보드 streak = 앱 전체 연속 학습일 기준)

---

## GET `/api/v1/parent/tasks` *(⋯ 메뉴 → Parent Dashboard 진입 시, 이번 핸드오프 범위 밖이지만 스키마 공유)*

부모가 오늘의 과제를 선택/변경하는 화면에서 사용. 구조만 참고.

```json
{
  "available_tasks": [
    { "id": "e1", "section": "english", "label": "...", "xp": 10 }
  ],
  "selected_ids": ["e1", "e2", "e3", ...]
}
```

---

## 에러 포맷

모든 4xx/5xx:

```json
{ "error": { "code": "NOT_FOUND", "message": "task not found" } }
```

HTTP status code는 표준(400/401/404/500) 사용.

---

## SQLite 스키마 제안 (FastAPI/SQLAlchemy용 힌트)

```sql
CREATE TABLE users (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  grade INTEGER,
  crew TEXT,
  level INTEGER DEFAULT 1,
  xp_current INTEGER DEFAULT 0
);

CREATE TABLE tasks (
  id TEXT PRIMARY KEY,
  user_id TEXT REFERENCES users(id),
  section TEXT CHECK(section IN ('english','math','diary','arcade','shop','review')),
  label TEXT NOT NULL,
  xp INTEGER NOT NULL,
  done INTEGER DEFAULT 0,
  due TEXT,         -- null | 'now' | 'overdue'
  scheduled_date TEXT NOT NULL, -- ISO date, 오늘 기준 필터
  sort_order INTEGER DEFAULT 0
);

CREATE TABLE daily_activity (
  user_id TEXT REFERENCES users(id),
  date TEXT,
  xp_earned INTEGER DEFAULT 0,
  completion_ratio REAL DEFAULT 0, -- 0.0~1.0, WeeklyStrip용
  PRIMARY KEY (user_id, date)
);

CREATE TABLE user_world (
  user_id TEXT REFERENCES users(id),
  world_id TEXT,
  collected INTEGER DEFAULT 0,
  total INTEGER,
  PRIMARY KEY (user_id, world_id)
);
```
