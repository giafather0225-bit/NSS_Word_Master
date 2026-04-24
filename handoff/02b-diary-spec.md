# 02b · Diary Section Spec (Decorated variant)

> Diary는 **유일하게 Decorated** 스타일을 쓰는 섹션입니다. 전체 규칙은 `01-design-system.md` "Style Variants" 섹션을 먼저 읽으세요.
> 참조 구현: `reference/DiaryScreens.jsx` (React 프로토타입, 비개발 참고용).

---

## 레이아웃 기본 원칙

- **Diary는 hub-level (사이드바 없음)** — Dashboard처럼 풀폭 1280px 사용
- 기준 뷰포트: **1280 × 900 (MacBook Air 기본)**
- 4개 화면 모두 스크롤 없이 한 화면에 완결
- 모든 화면 상단에 공통 `DiaryChrome`:
  - 왼쪽: `← Home` (Diary Home에서) 또는 `← Diary` (나머지에서). 투명 배경 pill, 호버 시 bg-card
  - Eyebrow pill (`DIARY · TODAY` / `DIARY · JOURNAL` / `DIARY · ENTRY` / `DIARY · MONTH`)
  - Title (Quicksand 32px, diary-ink)
  - Subtitle (13px, text-secondary)
  - 우측 slot (각 화면마다 다름)

---

## 범위 — 4개 화면

| # | Screen | Route | 컴포넌트 (in `DiaryScreens.jsx`) |
|---|---|---|---|
| 1 | Diary Home | `/diary` | `<DiaryHome/>` |
| 2 | Write | `/diary/write` | `<DiaryWrite/>` |
| 3 | Entry (detail) | `/diary/entry/:id` | `<DiaryEntry/>` |
| 4 | Calendar (month) | `/diary/calendar` | `<DiaryCalendar/>` |

**모드 (Write/Entry 한정)**: Journal (프롬프트 기반, mood 선택, 사진, 꾸미기) · Free Write (자유 작성 + Writing Tips + 사진 · 꾸미기).
Sentence 모드는 제외 (추후 삭제 예정).

**AI Assistant 연결 (Shadow / Siri 스타일)**
- 기존 프로젝트의 AI Assistant 패널 (`ai-assistant-stt.js` / `ai-assistant-tts.js`, 라우터 `ai_assistant.py`)을 그대로 재사용.
- Diary 안에 별도 AI 카드 **없음**. 사용자는 기존 전역 AI Assistant로 음성 대화.
- Write 화면의 "Speak / Listen" 버튼은 기존 STT/TTS 유틸 재사용.
- Entry 화면은 AI 관련 UI 없음 (읽기 전용).

---

## Screen 1 — Diary Home

**Layout**: 2×2 그리드, 1.15fr : 1fr, gap 18px, padding 20 32 24.

### Chrome 우측
- **Start writing** 버튼 (pen-tool 아이콘 + "Start writing"), diary primary 배경, 호버 lift

### 2×2 그리드

| | 좌 | 우 |
|---|---|---|
| **상단** | Mode CTAs (Journal + Free Write 2개) | Prompt card |
| **하단** | Week mood + Recent polaroids | Stats 2×2 타일 |

#### Mode CTAs (좌상)
- **Journal 카드**: `linear-gradient(160deg, var(--diary-light), #fff)`, 38px 아이콘 박스 (book-open, diary primary 배경), 20px 타이틀, 설명, "Begin →" 링크. 워싱테이프 1
- **Free Write 카드**: 동일 구조, english 색 계열, sparkles 아이콘

#### Prompt card (우상) — `<PromptCardV2/>`
- diary-light → white 그라디언트 배경, 워싱테이프 1
- eyebrow "Today's prompt"
- Caveat 26px 질문 ("What made you smile today?")
- 짧은 팁 라인 ("Try using three new words from Lesson 07.")
- **Start in Journal** 버튼 — 클릭 시 localStorage에 `nss.diary.seed.mode = 'journal'` + `nss.diary.seed.prompt` 기록 → Write로 이동

#### Week mood strip (좌하 상단)
- 카드 (diary-light 워싱테이프 1)
- 7열 그리드 — 각 칸: 요일 라벨(10px) + 큰 mood dot(26px, 흰 보더 2px)
- 데이터 없는 날은 dashed 보더 + 흐린 surface
- 우측 상단 "Month view →" 링크 → Calendar

#### Recent pages (좌하 하단) — 3개 폴라로이드
- 3열 그리드 (`alignItems: start`로 스트레치 방지)
- **`<PolaroidEntry/>`** 컴포넌트
  - tilt: -1.5° / 0° / +1.5° (호버 시 수평 + lift)
  - **사진 영역 `aspect-ratio: 4/3` 고정** (세로 늘어남 방지)
  - Journal + 사진 있음: 사진 모자이크 (1장 풀, 2장 좌우 1:1, 3장 좌 큰 2fr + 우 둘 1fr)
  - Journal + 사진 없음 / Free Write: mood 색 그라디언트 fallback
  - 좌하단 Journal/Free pill, 우상단 다중 사진 카운트 배지 (`⊞ N`)
  - Caveat 22px 제목 + 본문 2줄 클램프 + 날짜
  - mood 도트는 하단에 **없음** (사진 영역 색이 이미 mood 표현)

#### Stats 2×2 (우하) — `<StatsWithStreak/>`
- 카드 (워싱테이프 1), 상단 "This month / April" 헤더
- 4개 `<StatTile/>` 세로형: Entries / Words / Streak / Day off
  - 38px 아이콘 박스 (섹션 색 + 흰 아이콘)
  - 28px 숫자 (Quicksand 700)
  - uppercase 라벨 + 서브 텍스트
- **Mood mix / Last page 카드 없음** (중복 정리됨)

---

## Screen 2 — Write

**Layout**: 2컬럼 (1fr / 360px aside), gap 20, padding 20 32 24.

### Chrome 우측
1. **Mode segmented control**: Journal / Free Write (iOS 세그먼트 스타일, bg-surface 컨테이너, 활성 탭 흰색 배경 + soft shadow)
2. **⋯ 오버플로 메뉴** (`<WriteOverflowMenu/>`): Save draft / Clear all / Export as PDF
3. **Save · +15 XP** 버튼 — 15단어 미만일 땐 비활성

### 좌측 (Paper)
단일 종이 카드. 세로 배경은 `resolvePaperBackground(decorated, bgMood)`로 처리.

구성 (종이 내부 순서):
1. **Photos inline strip** (양쪽 모드)
   - 72×72 타일 최대 3장
   - Decorated 모드에선 ±1.5° tilt + 그림자
   - X 버튼으로 개별 제거, "Add photos" 점선 타일
   - 우측 "Photos N/3" 카운트
   - 하단 dashed 구분선
2. **Title 입력란**
   - 본문 폰트/크기/색 영향 받지 않고 항상 Caveat(Decorated)/Quicksand(Minimal) 큰 크기
   - placeholder "Give this page a title…"
   - 본문 20단어 이상 + 제목 비어있으면 **✨ Suggest** pill 나타남 (AI 제목 제안)
3. **Prompt quote** (보조 텍스트, 이탤릭 12.5px)
4. **Textarea**
   - `resolveFontFamily(font)`, `resolveFontSize(font, textSize)`, `resolveLineHeight`, `resolveTextColor(textColor)` 적용
5. **Footer**:
   - 좌측: **Mood 팝오버 pill** (현재 기분 1개 표시, 클릭 시 3×2 그리드 팝오버로 6 mood 펼침, 위로 올라오는 방향)
   - 우측: 단어 프로그레스 바 (80×5) + `<b>{wordCount}</b> / 15` (15 달성 시 색이 math primary로)
   - 우측 끝: `🎤 Speak` (STT) + `🔊 Listen` (TTS) 작은 버튼

### 우측 Aside (360px, 세로 스크롤)

3개 카드 고정 순서:

#### 1) 상단 카드 — 모드별
- **Journal**: `<PromptBank/>` — 5개 프롬프트 리스트. 클릭 시 본문 프롬프트 실시간 교체. 활성 프롬프트는 diary-primary 배경 + 흰 글씨
- **Free Write**: `<WritingTips/>` — English light 그라디언트, sparkles 아이콘, 팁 1개씩 순환 (4개 중), "Next →" 버튼, 하단 dot 인디케이터

#### 2) `<StyleTools/>` — 공통
- **Font**: 6종 (Caveat / Nunito / Patrick Hand / Shadows Into Light / Indie Flower / Kalam), 각 "Aa" 샘플로 표시
- **Size**: S / M / L (각각 Aa 시각 표시)
- **Text color**: 7색 원 (default ink + diary / english / math / arcade / rewards / review)

구현: Google Fonts 로드 후 `FONT_OPTIONS` / `TEXT_COLORS` 배열 기준.

#### 3) `<DecorTools/>` — 공통
- **Sticker tray**: 7 카테고리 × 8개 = 56 이모지
  - 카테고리: Nature / Sky / Hearts / Faces / Things / Food / Animals
  - 카테고리 탭 (pill), 선택된 카테고리 diary-primary 배경
  - 8열 그리드, 타일 호버 시 배경 + 1.1 scale
  - **클릭 → textarea 커서 위치에 이모지 + 공백 삽입** (`insertAtCaret`)
- **Page color**: 7개 원형 스와치 (Paper / Blossom / Mint / Sky / Butter / Lavender / Peach)
  - 활성 스와치 diary-primary 2px 보더 + soft shadow
  - default 스와치 안에 X 아이콘 (기본으로 돌아가기 힌트)
  - Decorated 모드면 노트 줄무늬도 선택된 톤으로 자동 변경

### State snapshot (Save 시 저장)
```ts
{
  mode: 'journal' | 'free',
  mood: 'happy',
  title: 'Brave day',
  body: '…',
  photos: [{ id, url }, ...],
  style: {
    font: 'caveat',
    textSize: 'm',
    textColor: 'diary',
    bgMood: 'pink',
  }
}
```

---

## Screen 3 — Entry (detail / read-only)

**Entry는 기록 열람실이다.** 작성 CTA, 편집 버튼 없음.

**Layout**: 1컬럼 (풀폭 Paper + 하단 페이지 네비게이션), padding 20 32 24.

### Chrome 우측
- **Delete 버튼만** (`<EntryDeleteButton/>`)
  - 클릭 시 팝오버 "Delete this page? This page will be gone forever. You can't get it back."
  - **Keep it** / **Delete** 2버튼
  - ESC 또는 외부 클릭으로 닫힘 (초등학생 실수 방지)
- **Edit 버튼 없음** (Entry는 읽기 전용)
- **Ask buddy 버튼 없음** (기존 전역 AI Assistant 사용)

### Paper (단일 페이지, 저장된 스타일 복원)

배경: `resolvePaperBackground(decorated, entry.style.bgMood)` — 저장 당시 배경 그대로.

구성 (종이 내부 순서):
1. **Photos inline strip** (Journal + 사진 있음)
   - Write와 동일한 72×72 타일, Decorated tilt
   - X 버튼 없음 (읽기 전용)
   - 우측 "N photos" 카운트
   - 하단 dashed 구분선
2. **Meta row**
   - 32px mood 색 사각형 (흰 보더 2.5px, soft shadow)
   - "Journal" / "Free write" 라벨 + mood 단어
   - 우측 `+15 XP` pill (arcade 색)
3. **Prompt quote** (Journal만)
   - diary-light 배경, 좌 3px diary-primary 보더
4. **Body** — 저장된 스타일 적용
   - `resolveFontFamily(entry.style.font)`
   - `resolveFontSize(entry.style.font, entry.style.textSize)`
   - `resolveLineHeight` / `resolveTextColor(entry.style.textColor)`
   - whiteSpace: pre-wrap (스티커 이모지가 본문 중간에 섞여 있음)
5. **Words used 행**
   - 좌측: "Words" 라벨 + 단어 pill (english-light)
   - 우측: **♡ Share with parent** 버튼 (diary primary, 이 페이지에 대한 액션)

### 하단 페이지 네비게이션 — `<EntryPageNav/>`
Paper 바깥 아래에 2개 카드 가로 배치 (책장 넘기기 메타포):
- **왼쪽 카드**: `← Earlier · APR 21 · Whisper`
- **오른쪽 카드**: `Later · APR 23 · The yellow fish →`
- 카드 클릭 시 해당 Entry로 이동
- 호버 시 bg-surface 배경
- **mood 도트 없음** (시각 노이즈 제거)
- 가장 오래된/최신 일기일 땐 "No earlier pages" / "No later pages" 비활성 표시

---

## Screen 4 — Calendar (monthly)

**Layout**: 2컬럼 (1fr / 260px aside), gap 16, padding 14 28 16.

### Chrome 우측
- **월 네비게이션**: `[← Apr →]` (chevron-left / 월 라벨 / chevron-right)

### 좌측 (달력 카드)
워싱테이프 1.

#### 요일 헤더
7열 그리드 (Sun~Sat), 10px uppercase, text-hint.

#### 날짜 셀 (7열, 5~6행)

| 상태 | 보더 | 배경 | 숫자 색 | 불투명도 | 마커 |
|---|---|---|---|---|---|
| 기록 있음 | 1px solid border-subtle | bg-card | text-primary 600 | 1 | 우하단 12px mood 도트 |
| 오늘 | **2px solid diary-primary** | bg-page | diary-primary 700 | 1 | — |
| 미래 | solid | transparent | — | 0.4 (disabled) | — |
| **missed (과거+기록無)** | **1px dashed** | bg-page | **text-hint** | **0.65** | **우하단 4px 회색 점** |
| **Day off (approved)** | **1px solid arcade-soft** | **arcade-light** | **arcade-ink** | 1 | **우하단 ☕ 커피 아이콘 (arcade-primary)** |
| **Day off (pending)** | **1px dashed arcade-primary** | bg-page | text-hint | **0.75** | **흐린 ☕ 커피 아이콘** |

- 기록 있는 셀만 클릭 가능 → Entry 이동
- Day off 셀은 클릭 불가
- 호버 시 `translateY(-1px)` (기록 있는 셀만)
- 툴팁: 'Day off · approved' / 'Day off · waiting for parent' / 'No entry this day'

### 우측 Aside (260px)

#### Legend
6 mood 아이템, 2열 그리드
- 각 행: mood 도트 + 라벨 + 우측에 월 카운트 숫자
- 하단에 점선 구분선 후 **Day off** / **Waiting** 2행 추가
  - Day off: 14×14 radius 4 arcade-light 타일 + ☕ 아이콘 + 월 카운트
  - Waiting: dashed 보더 arcade-primary + 흐린 ☕ + 카운트

#### April summary
- diary-light → white 그라디언트, 워싱테이프 1
- eyebrow "April summary"
- Caveat 22px 문구 (예: "Mostly happy. / A brave month.")
- 하단 3열 MiniStat (Entries / Streak / Words)

#### **CTA 없음** — Calendar는 탐색/지도 화면 (Entry의 "Write tomorrow" 제거와 일관)

---

## 데이터 모델

```ts
type Mood = 'great' | 'happy' | 'calm' | 'curious' | 'tired' | 'sad';
type FontKey = 'nunito' | 'caveat' | 'patrick' | 'shadows' | 'indie' | 'kalam';
type SizeKey = 's' | 'm' | 'l';
type ColorKey = 'default' | 'diary' | 'english' | 'math' | 'arcade' | 'rewards' | 'review';
type BgMoodKey = 'default' | 'pink' | 'mint' | 'sky' | 'butter' | 'lavender' | 'peach';

interface DiaryPhoto {
  id: string;
  url: string;
  name?: string;
  width?: number;
  height?: number;
}

interface DiaryStyle {
  font: FontKey;
  textSize: SizeKey;
  textColor: ColorKey;
  bgMood: BgMoodKey;
}

interface DiaryEntry {
  id: string;
  date: string;          // ISO yyyy-mm-dd
  type: 'journal' | 'free';
  mood: Mood;
  prompt?: string;       // journal만
  title: string;
  body: string;          // 본문 (스티커 이모지 포함, 그대로 저장)
  wordsUsed: string[];   // 레슨 단어 중 사용된 것
  photos: DiaryPhoto[];  // 양쪽 모드 모두 최대 3장
  xp: number;
  style: DiaryStyle;     // 저장 시점의 꾸미기 스냅샷 (Entry에서 복원)
}
```

### Day off 통합 (아이 신청 → 부모 승인)

DB 계층은 **기존 앱의 `DayOffRequest` 테이블**을 그대로 사용. 신청 UI만 Diary 안에 새로 만든다.

**흐름**
1. 아이가 Diary Home의 Stats 카드 하단 **"Request a day off"** 버튼 클릭
2. `<DayOffRequestModal/>` — 날짜 선택 (미래 날짜만) + 이유 (선택) 입력
3. 제출 → `POST /api/v1/day-offs` → status = `pending`
4. 부모가 기존 Parent Dashboard에서 승인/거절
5. Diary Calendar에 상태별 시각 표현 (approved / pending)

**제약**
- 월 최대 **2회** (`DAY_OFF_MAX = 2`)
- 남은 횟수 0 이면 버튼 비활성 + "No day offs left this month"
- 과거/오늘 날짜는 신청 불가 (input `min` = 내일)
- 이유는 선택 입력, 60자 제한
- pending 상태 요청은 Calendar에서 해당 날짜 선택 → 취소 옵션 제공 (Approved는 취소 불가)

**Home Stats 카드 수정 (기존 스펙 덮어씀)**
- Day off 타일 값: `{used}/{MAX}` (예: `1/2`), sub 텍스트는 `N left` 또는 `all used`
- Stats grid 아래에 **Day off request CTA 버튼** (arcade-light 배경, coffee 아이콘)

**Calendar 셀 상태 매핑**
- `status === 'approved'` → 셀에 arcade-light 배경 + ☕ 커피 아이콘
- `status === 'pending'` → dashed arcade-primary 보더 + 흐린 ☕
- `status === 'rejected'` 또는 없음 → 일반 missed day 규칙 적용

**접근성**
- 모달: `role="dialog"`, `aria-label="Request a day off"`, ESC로 닫힘, 배경 클릭 닫힘
- 초점 관리: 모달 열릴 때 날짜 입력으로 포커스, 닫힐 때 트리거 버튼으로 복귀

### API 엔드포인트
- `GET /api/v1/diary?month=YYYY-MM` → `{ entries: DiaryEntry[], stats: { entries, streak, words, day_off }, day_offs: DayOff[] }`
  - `day_offs`: 해당 월의 DayOffRequest 목록 (Calendar 렌더용). `[{ date, status }]`
- `GET /api/v1/diary/:id` → 단일 entry (Entry / Calendar 클릭 시)
- `GET /api/v1/diary/:id/neighbors` → `{ prev: DiaryEntry|null, next: DiaryEntry|null }` (Entry 하단 페이지 네비게이션)
- `POST /api/v1/diary` → 생성 (mode, mood, title, body, photos, style)
- `PATCH /api/v1/diary/:id` → 수정 (Entry에서는 사용하지 않음 — Edit 버튼 제거됨. 내부 마이그레이션 용도)
- `DELETE /api/v1/diary/:id`
- `GET /api/v1/diary/prompts?mode=journal` → 프롬프트 풀
- `POST /api/v1/diary/:id/photos` (multipart) → 사진 업로드 (최대 3장)
- `DELETE /api/v1/diary/:id/photos/:photoId` → 사진 제거

### 사진 저장 규칙
- 경로: `storage/diary/{user_id}/{entry_id}/{photo_id}.jpg`
- 허용 MIME: `image/jpeg`, `image/png`, `image/webp`, `image/heic`
- 최대 크기: 10MB/장, EXIF 회전 정규화, 256×256 썸네일 별도 저장
- Free Write에도 사진 업로드 허용

---

## 상호작용 규칙

- **Mood 선택** 후 본문 **15단어** 넘어야 Save 활성화
- **Save 성공** 시 XP +15, Dashboard의 streak 낙관적 업데이트
- **Entry 삭제**: Delete 팝오버 → "Keep it" or "Delete". 확인 없이 바로 삭제하지 않음
- **Calendar 날짜 클릭**: 기록 있는 날만 — Entry 이동, missed 날 / 미래 날 비활성
- **Week strip 요일 클릭**: 동일 로직
- **Photo uploader**:
  - 파일 선택 즉시 `URL.createObjectURL`로 미리보기
  - Save 시 `POST /api/v1/diary/:id/photos`로 전송
  - 실패 시 해당 타일에 `--color-error` 보더 + 재시도
  - 모드 전환해도 photos state 보존
- **PromptBank 선택** (Journal):
  - 본문 프롬프트만 교체, body 유지
  - 활성 프롬프트 diary-primary 하이라이트
- **Sticker 클릭**:
  - textarea 커서 위치에 이모지 + 공백 삽입
  - textarea에 focus 복귀, 커서는 삽입 직후로
- **Font / Size / Color / BG** 변경:
  - textarea + Paper 배경 실시간 반영
  - Save 시 `style` 스냅샷으로 저장 → Entry에서 그대로 복원
- **Home "Start in Journal"**:
  - localStorage `nss.diary.seed.mode` + `nss.diary.seed.prompt` → Write 진입
  - Write 마운트 시 seed 읽고 즉시 삭제

---

## 접근성

- Mood pill (footer): `aria-haspopup`, `aria-expanded`, 팝오버 오픈 시 `role="dialog"` 또는 `role="menu"`
- Mood 선택 버튼: `role="radiogroup"`, 각 버튼 `aria-pressed`
- 달력 셀: `aria-label="April 22, great mood"` / `aria-label="April 14, no entry"`
- 단어 progress bar: `role="progressbar"`, `aria-valuenow / min / max`
- 폴라로이드 tilt: 순수 시각 — `aria-hidden` 없이 접근 가능해야 함
- Photo uploader: 숨긴 input이지만 label로 버튼과 연결, 각 타일 X버튼 `aria-label="Remove photo"`, 썸네일 `aria-label="View photo N"`
- Sticker tray 버튼: `aria-label="Insert sticker 🌸"` 등
- Delete 확인 팝오버: `role="alertdialog"`, 초점 관리
- AI 관련 접근성 규칙: 기존 AI Assistant 컴포넌트 승계

---

## 다크모드
- 노트 줄 배경은 `var(--bg-card)` + bgMood 토큰 혼합 → 다크에서 자동 대응
- 워싱테이프 색은 섹션 soft 토큰 → 다크에서 탁함 주의, 필요 시 `opacity: 0.7`
- 폴라로이드 사진 mood 그라디언트는 dot 색상 사용 → 다크에서도 선명

---

## 구현 체크리스트

### 공통
- [ ] Diary 섹션 전체를 **hub-level 라우팅** 처리 (사이드바 없음)
- [ ] `<DiaryChrome/>` 공통화 — back button 라벨은 `onBack` 유무로 분기
- [ ] Google Fonts: Quicksand, Nunito, Caveat, Patrick Hand, Shadows Into Light, Indie Flower, Kalam
- [ ] `<WashiTape/>`, `<DiaryPill/>`, `<MoodDot/>` 공통
- [ ] Font/Color/BG 리졸버 공통 (`resolveFontFamily`, `resolveFontSize`, `resolveLineHeight`, `resolveTextColor`, `resolvePaperBackground`)

### Home
- [ ] 2×2 그리드 1.15fr : 1fr
- [ ] `<PolaroidEntry/>` 사진 영역 `aspect-ratio: 4/3` 고정
- [ ] `<StatsWithStreak/>` — 4 StatTile만, mood mix / last page 없음
- [ ] Prompt card "Start in Journal" 버튼 seed 저장

### Write
- [ ] Chrome 우측: Mode 세그먼트 / ⋯ 메뉴 / Save
- [ ] `<PhotoInlineStrip/>` Paper 안 상단 (양쪽 모드)
- [ ] Title 입력 + Suggest pill (20단어+)
- [ ] `<MoodFooterPicker/>` Paper footer 팝오버
- [ ] `<PromptBank/>` (Journal) vs `<WritingTips/>` (Free)
- [ ] `<StyleTools/>` Font 6종 / Size S·M·L / Text color 7색
- [ ] `<DecorTools/>` Sticker 7 카테고리 / Page color 7색
- [ ] Sticker 클릭 시 `insertAtCaret` 동작
- [ ] Save 시 style 스냅샷 저장
- [ ] Home seed 소비 후 localStorage 정리

### Entry
- [ ] Chrome 우측: **Delete만** (Edit/Ask buddy 없음)
- [ ] `<EntryDeleteButton/>` 확인 팝오버
- [ ] Paper 안 상단 PhotoInlineStrip (읽기 전용, X 버튼 없음)
- [ ] 저장된 `style` 복원 (font/size/color/bg)
- [ ] Words used 행 + Share with parent
- [ ] `<EntryPageNav/>` Paper 아래, mood 도트 없음

### Calendar
- [ ] 월 네비게이션 chrome 우측 `[← Apr →]`
- [ ] Missed day: dashed 보더 + 4px 회색 점 + 흐린 숫자
- [ ] **Write today's page CTA 없음**
- [ ] Legend 2열 + Summary Caveat + MiniStat 3개

### Tweaks / dev flags
- [ ] `Diary Preview.html`의 Decorated/Minimal 토글은 **프로덕션에 탑재하지 않음**. Diary는 항상 Decorated.
