# NSS Learning 앱 - 프로젝트 스펙

## 1. 폴더 구조
~/NSS_Learning/
├── English/
│   ├── Voca_8000/
│   │   ├── Lesson_01/
│   │   │   ├── source.heic (원본)
│   │   │   ├── data.json (OCR 결과)
│   │   │   └── images/ (변환된 JPG)
│   │   ├── Lesson_02/
│   │   └── ...
│   ├── Oxford_5000/
│   │   ├── Lesson_01/
│   │   └── ...
│   └── [다른 교재들]
│
└── Math/
├── 초등수학_기본/
│   ├── Unit_01/
│   ├── Unit_02/
│   └── ...
├── RPM_중학수학/
│   ├── Chapter_01/
│   └── ...
└── [다른 교재들]
## 2. 5단계 학습 흐름

### Step 1: Preview (단어 카드 학습)
- 모든 단어 카드 그리드 표시 (이미지 포함)
- 카드 클릭 → 확대
  - 단어 표시 + TTS 읽기
  - 예문 표시 + TTS 읽기
  - 스펠링 타이밍 게임 (3회)
    - "S - P - E - L - L ..." 순서대로 표시
    - 아이가 소리내서 따라 말함 (입력 없음)
    - 충분한 시간 제공
- 완료 → 그리드로 돌아감
- 모든 단어 완료 → 축하메시지 (매번 다름)
- 반복 학습 가능

### Step 2: Word Match (의미 연결하기)
- 5개 단어 × 5개 뜻을 한 화면에 표시
- 좌측: 단어 클릭 가능
- 우측: 뜻 클릭 가능
- 단어 + 뜻 매칭 성공 → 하이라이트 표시
- 오류 시 진동/음향 피드백 후 리셋
- 3라운드 반복 필수 (매번 순서 섞임)
- 마지막 라운드 완료 → "학습완료" 메시지
- 반복 학습 가능

### Step 3: Fill the Blank (빈칸 채우기)
- 상단: 📦 단어 박스 (모든 단어 나열, 사용한 것은 흐릿함)
- 예문들 (하나씩 나옴): "The ____ was very beautiful." (의미: 풍경)
- 입력창에 단어 타이핑 + 확인 버튼
  - ✅ 맞음: 체크 ✓ → 다음 문장
  - ❌ 틀림 (1회): 힌트 표시 (글자 수, 첫글자)
  - ❌ 틀림 (2회): 더 강한 힌트
  - ❌ 틀림 (3회): X 표시 + 마지막에 재도전
- 모든 문장 완료 → 틀린 것만 다시 출제
- 모두 맞음 → "학습완료" 메시지
- 반복 학습 가능

### Step 4: Spelling Master (철자 학습)
- 한 단어당 3회 시도
  - 1회: "L__N" (일부 글자만 숨김)
  - 2회: "L__N" (다른 위치 숨김)
  - 3회: "____" (완전 숨김)
- 각 시도 전 단어 발음 제공 (TTS)
  - ✅ 맞음: 통과 → 다음 단어로
  - ❌ 틀림: 일단 넘어감 (마지막에 틀린 것만 재도전)
- 모든 단어 3회 완료 → 틀린 것 재도전
- 모두 맞음 → "학습완료" 메시지
- 반복 학습 가능

### Step 5: Make a Sentence (문장 창작 + AI 피드백)
- 한 단어씩 출제: "이 단어로 문장을 만들어 봐: LANDSCAPE"
- 입력 → 제출

AI 검사:
- ✅ 문법/내용 OK → "멋신데! ⭐" → 다음 단어
- ❌ 오류 발견:
  - 1회차 오류 → "여기를 이렇게 고쳐보면 어때?" (수정안 제시) → 아이가 다시 쓰기
  - 2회차 오류 → "함께 만든 문장: ..." (최종 수정안) → 다음 단어로 자동 진행

- 모든 단어 완료 → "학습완료" 메시지
- 반복 학습 가능

### Step 6: Final Test (모의고사)
- 모든 5단계 완료 후 시작
- 학습한 모든 단어 무작위 출제
- Fill the Blank, Word Match, Spelling, Make a Sentence 섞임
- 100% 완료 시 최종 축하 메시지 + 리워드 🎉

## 3. 백엔드 API 설계

### 폴더 & 교재 조회
GET /api/subjects
응답: ["English", "Math"]
GET /api/textbooks/{subject}
응답: ["Voca_8000", "Oxford_5000", ...]
GET /api/lessons/{subject}/{textbook}
응답: ["Lesson_01", "Lesson_02", ...]
### 파일 업로드
POST /api/files/upload
파라미터:

subject (English / Math)
textbook (Voca_8000 등)
lesson (Lesson_01 등)
file (HEIC / JPG / PNG)

응답:

synced: 동기화된 단어 개수
data_json: 저장된 data.json 경로


### 학습 데이터 조회
GET /api/study/{subject}/{textbook}/{lesson}
응답:

items: [{ id, word, meaning, example, image, ... }]
progress: { current_index, best_streak }


### 학습 진행률 업데이트
POST /api/progress/verify
POST /api/progress/challenge_complete
POST /api/progress/sparta_reset

## 4. 데이터베이스 스키마

### StudyItem (수정)
id (Primary Key)
subject: String (English / Math)
textbook: String (Voca_8000 / RPM_중학수학 등)
lesson: String (Lesson_01 / Unit_01 등)
question: String (단어의 뜻)
answer: String (단어 자체)
hint: String (예문)
extra_data: JSON ({ pos, image_url, ... })

### Progress (수정)
id (Primary Key)
subject: String
textbook: String
lesson: String
current_index: Integer
best_streak: Integer

## 5. 프론트엔드 구조 (다음 단계)

### 홈 화면
- 과목 선택 탭 (English / Math)
- 교재 선택 드롭다운 또는 버튼
- 레슨 선택 탭
- Start 버튼

### 학습 화면
- Preview: 카드 그리드 + 확대 모달
- Word Match: 좌우 매칭 게임
- Fill the Blank: 단어 박스 + 예문 입력
- Spelling Master: 카드 + 입력창
- Make a Sentence: 단어 + 문장 입력 + AI 피드백

## 6. 기술 스택 (기존)

- Backend: FastAPI (main.py)
- Database: SQLite (database.py)
- Frontend: Vanilla JS (child.js, app.js)
- OCR: Ollama (llava 모델)
- TTS: macOS `say` 커맨드
- 이미지 변환: macOS `sips` 커맨드

## 7. 구현 우선순위

1. 백엔드: 폴더 구조 + API 설계
2. 프론트엔드: 과목/교재/레슨 선택 UI
3. Preview 카드 UI 완전 재작성
4. Word Match → Fill the Blank → Spelling Master → Make a Sentence 순차 구현
5. Final Test 구현

