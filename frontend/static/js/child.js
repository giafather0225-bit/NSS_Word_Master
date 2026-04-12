/* eslint-disable no-use-before-define */
// ─── 상수 ──────────────────────────────────────────────────
const CONF = {
    TTS_REPEAT: 3,              // Preview TTS 반복 횟수
    EXAM_POOL_SIZE: 5,          // Final Test 문제 풀 크기
    EXAM_MAX_QUESTIONS: 8,      // Final Test 최대 문제 수
    SPELLING_PASSES: 3,         // Spelling Master 패스 수
    FB_MAX_STRIKES: 3,          // Fill Blank 최대 오답 횟수
    FB_RETRY_MAX_STRIKES: 3,    // Fill Blank retry에서도 최대 오답 (무한루프 방지)
    PARTICLE_MAX: 48,           // 파티클 최대 개수
    PARTICLE_LIFETIME: 1300,    // 파티클 수명 (ms)
    STAGE_CLEAR_DELAY: 5000,    // 스테이지 클리어 화면 표시 시간 (ms)
    WRONG_ANSWER_DISPLAY: 2000, // 오답 표시 시간 (ms)
};

// currentSubject: "English" / "Math" — 폴더 이름과 일치
let currentSubject = "English";
// currentTextbook: "Voca_8000" 등 — 교재 폴더 이름
let currentTextbook = "";

const LESSON_REQUEST = new URLSearchParams(location.search).get("lesson") || "";
let selectedLesson = LESSON_REQUEST || "";

const STAGE = {
    PREVIEW: "PREVIEW",
    A: "A",
    B: "B",
    C: "C",
    D: "D",
    EXAM: "EXAM",
};

const ROADMAP_STAGES = [STAGE.PREVIEW, STAGE.A, STAGE.B, STAGE.C, STAGE.D];
const ROADMAP_LABELS = ["1. Preview", "2. Word Match", "3. Fill Blank", "4. Spelling", "5. Sentence"];
const IMPLEMENTED_STAGES = [STAGE.PREVIEW, STAGE.A, STAGE.B, STAGE.C, STAGE.D];

// 언락 규칙:
//   - Preview는 항상 가능
//   - Steps 2-5 는 Preview 완료 후 동시에 전부 언락
//   - Final Test 는 모든 5단계 완료 후 언락
function isStageUnlocked(key) {
    if (key === STAGE.PREVIEW) return true;
    const done = getCompletedStages();
    return done.has(STAGE.PREVIEW);  // Steps 2-5: Preview 완료 시 전부 오픈
}

const EXAM_MODE = {
    EXAMPLE_BLANK: "example",
    OWN_SENTENCE_BLANK: "own",
};

let items = [];
let stage = null;

let stageIndex = 0;
let magicFailCount = 0;
let starCount = 0;

let currentPhaseIndex = 0;
let unlockedPhaseIndex = 0;
let sessionActive = false;
let roadmapComplete = false;

let wrongMap = {};
// ─── Learning Analytics Tracking ───────────────────────
let _stageStartTime = null;
let _stageAttempts = [];  // collect word attempts per stage

function _trackStageStart() {
    _stageStartTime = new Date().toISOString();
    _stageAttempts = [];
}

function _trackWordAttempt(item, isCorrect, userAnswer) {
    _stageAttempts.push({
        study_item_id: item.id,
        textbook: currentTextbook,
        lesson: selectedLesson,
        word: item.answer || item.word || "",
        stage: stage || "",
        is_correct: isCorrect,
        user_answer: userAnswer || "",
        attempted_at: new Date().toISOString()
    });
}

function _trackStageComplete(completedStage) {
    const now = new Date().toISOString();
    const durationSec = _stageStartTime
        ? Math.round((new Date(now) - new Date(_stageStartTime)) / 1000)
        : 0;
    const wordCount = items.length || 0;
    const wrongKeys = Object.keys(wrongMap).filter(k => wrongMap[k] > 0);
    const correctCount = wordCount - wrongKeys.length;
    const wrongWords = wrongKeys.map(k => {
        const it = items.find(i => String(i.id) === String(k));
        return it ? (it.answer || it.word || k) : k;
    });

    // Send stage log
    fetch("/api/learning/log", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            textbook: currentTextbook,
            lesson: selectedLesson,
            stage: completedStage || "",
            word_count: wordCount,
            correct_count: Math.max(0, correctCount),
            wrong_words: wrongWords,
            started_at: _stageStartTime || "",
            completed_at: now,
            duration_sec: durationSec
        })
    }).catch(() => {});

    // Send word attempts batch
    if (_stageAttempts.length > 0) {
        fetch("/api/learning/word-attempts-batch", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ attempts: _stageAttempts })
        }).catch(() => {});
    }

    _stageStartTime = null;
    _stageAttempts = [];
}
// ─── End Learning Analytics ────────────────────────────

let ownSentencesByItemId = {};

let examQueue = [];
let examIndex = 0;

const wordVaultSet = new Set();

// ─── 개발자 디버그 도구 (브라우저 콘솔에서 DEV.go(3) 등으로 사용) ──────────────
window.DEV = {
    async go(stageNum) {
        const stageMap = {1: 'PREVIEW', 2: 'A', 3: 'B', 4: 'C', 5: 'D'};
        const key = stageMap[stageNum];
        if (!key) { console.log('1-5 사이 숫자를 입력하세요'); return; }
        if (!items.length) {
            const lesson = lessonSelected();
            if (!lesson) { console.log('레슨을 먼저 선택하세요'); return; }
            await loadStudyItems(lesson);
        }
        jumpToStage(key);
        console.log('Stage ' + stageNum + ' (' + key + ')');
    },
    skip() {
        if (stage) markStageComplete(stage);
        advanceToNextStage();
        console.log('Stage skipped');
    },
    clearAll() {
        ROADMAP_STAGES.forEach(s => markStageComplete(s));
        updateRoadmapUI();
        refreshStartLabel();
        console.log('All stages marked complete');
    },
    reset() {
        localStorage.removeItem(stageStorageKey());
        sessionActive = false;
        stage = null;
        stageIndex = 0;
        updateRoadmapUI();
        refreshStartLabel();
        renderIdleStage();
        console.log('Progress reset');
    },
    word(n) {
        stageIndex = Math.max(0, Math.min(n, items.length - 1));
        renderStage();
        console.log('Word index: ' + stageIndex);
    },
    last() {
        stageIndex = Math.max(0, items.length - 2);
        renderStage();
        console.log('Near last word: ' + stageIndex);
    },
    info() {
        console.table({
            stage, stageIndex,
            totalWords: items.length,
            sessionActive,
            completed: [...getCompletedStages()].join(', '),
            wrongCount: Object.keys(wrongMap).filter(k => wrongMap[k] > 0).length
        });
    }
};

// ─── Preview stage state ──────────────────────────────────
// Maps item.id → "ok" | "miss"  (reset each time Preview starts)
const previewDoneMap = new Map();

// ─── Fill the Blank state ──────────────────────────────────
const fbState = {
    mistakeCount: {},
    retryQueue: [],
    retryMode: false,
    retryIndex: 0,
    initialized: false,
    reset() {
        this.mistakeCount = {};
        this.retryQueue = [];
        this.retryMode = false;
        this.retryIndex = 0;
        this.initialized = false;
    }
};

// ─── Word Match state ──────────────────────────────────────
const wmState = {
    BATCH_SIZE: 7,
    round: 0,
    batchIdx: 0,
    matched: new Set(),
    selectedWordIdx: null,
    shuffleOrder: null,
    scrollHandler: null,
    initialized: false,
    reset() {
        this.round = 0;
        this.batchIdx = 0;
        this.matched = new Set();
        this.selectedWordIdx = null;
        this.shuffleOrder = null;
        this.scrollHandler = null;
        this.initialized = false;
    }
};

// ─── 스테이지 완료 추적 (localStorage, subject + lesson별 분리) ──────────────
function stageStorageKey() {
    return `nss_done_${currentSubject}_${currentTextbook}_${selectedLesson}`;
}
function getCompletedStages() {
    try { return new Set(JSON.parse(localStorage.getItem(stageStorageKey()) || "[]")); }
    catch (err) { console.warn('[getCompletedStages] localStorage read failed:', err.message || err); return new Set(); }
}
function markStageComplete(stageKey) {
    if (!stageKey) return;
    const done = getCompletedStages();
    done.add(stageKey);
    localStorage.setItem(stageStorageKey(), JSON.stringify([...done]));
}
function allStagesDone() {
    const done = getCompletedStages();
    return ROADMAP_STAGES.every((s) => done.has(s));
}
function nextStageToStart() {
    const done = getCompletedStages();
    // Preview 안 했으면 항상 Preview
    if (!done.has(STAGE.PREVIEW)) return STAGE.PREVIEW;
    // Preview 완료 → 아직 안 한 단계 중 첫 번째
    return ROADMAP_STAGES.find((s) => !done.has(s)) || STAGE.PREVIEW;
}

function resetAllStageState() {
    clearWmScrollHandler();
    wmState.reset();
    fbState.reset();
    spState.reset();
    smState.reset();
    stageIndex = 0;
    wrongMap = {};
}

// 특정 스테이지로 바로 점프 (로드맵 필 클릭 시 호출)
function jumpToStage(stageKey) {
    const idx = ROADMAP_STAGES.indexOf(stageKey);
    if (idx === -1) return;
    currentPhaseIndex = idx;
    unlockedPhaseIndex = Math.max(unlockedPhaseIndex, idx);
    resetAllStageState();
    stage = stageKey;
    sessionActive = true;
    roadmapComplete = false;
    const sidebar = document.getElementById('sidebar');
    if (sidebar) sidebar.classList.add('collapsed');
    localStorage.setItem('sb_collapsed', '1');
    renderStage();
    enterSessionSidebar();
    setStatus(stageTitle() + " \u2014 start!");
    particleBurst(16);
}

// HTML의 setSubject('eng') / setSubject('math') 에서 호출
window.setSubject = async function (key) {
    // UI toggle (merged from child.html)
    const isEng = key !== 'math';
    document.body.classList.toggle('math-mode', !isEng);
    const tabEng = document.getElementById('tab-eng');
    const tabMath = document.getElementById('tab-math');
    if (tabEng) tabEng.classList.toggle('active', isEng);
    if (tabMath) tabMath.classList.toggle('active', !isEng);
    localStorage.setItem('subject_mode', key);

    const subjectMap = { eng: "English", math: "Math" };
    const newSubject = subjectMap[key] || key;
    if (currentSubject === newSubject) return;
    currentSubject = newSubject;
    currentTextbook = "";
    selectedLesson = "";

    // 과목 탭 UI 갱신
    document.querySelectorAll(".sb-subject-tab").forEach((t) => t.classList.remove("active"));
    const activeTab = document.getElementById(`tab-${key}`);
    if (activeTab) activeTab.classList.add("active");

    // math-mode 테마 토글
    document.body.classList.toggle("math-mode", newSubject === "Math");

    // 세션 초기화
    sessionActive = false;
    roadmapComplete = false;
    stage = null;
    stageIndex = 0;
    currentPhaseIndex = 0;
    unlockedPhaseIndex = 0;
    spState.pass = 1;
    wrongMap = {};
    items = [];
    wordVaultSet.clear();
    renderWordVault();
    renderIdleStage();
    updateRoadmapUI();
    if (typeof initWeeklyCalendar === "function") initWeeklyCalendar();
    updateProgressPct();
    updateChallengeMeta();
    setStatus(`Subject: ${newSubject}`);

    await loadTextbooks(newSubject);
    refreshStartLabel();
};

function refreshStartLabel() {
    const isDone = allStagesDone();

    // Exam 버튼은 items 로드 여부와 관계없이 항상 과목별 완료 상태로 결정
    const ex = $("btn-exam");
    if (ex) ex.disabled = !isDone;

    const btn = $("btn-start");
    if (!btn) return;
    if (isDone) { btn.textContent = "Repeat ↩"; return; }
    const done = getCompletedStages();
    const doneCount = ROADMAP_STAGES.filter((s) => done.has(s)).length;
    if (doneCount === 0) { btn.textContent = "Start"; return; }
    // 일부 완료: 다음 안 한 단계 표시
    const next = nextStageToStart();
    const nextLabel = ROADMAP_LABELS[ROADMAP_STAGES.indexOf(next)] || "Start";
    btn.textContent = `▶ ${nextLabel}`;
}

function challengeResetStorageKey() {
    return `nss_challenge_reset_${new Date().toISOString().slice(0, 10)}`;
}

function loadChallengeResetsToday() {
    return Number(sessionStorage.getItem(challengeResetStorageKey()) || 0);
}

function bumpChallengeResetToday() {
    const k = challengeResetStorageKey();
    const n = Number(sessionStorage.getItem(k) || 0) + 1;
    sessionStorage.setItem(k, String(n));
    return n;
}

function $(id) {
    return document.getElementById(id);
}

function escapeHtml(s) {
    return String(s)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;");
}

function escapeRe(s) {
    return String(s).replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function shuffle(arr) {
    const a = arr.slice();
    for (let i = a.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [a[i], a[j]] = [a[j], a[i]];
    }
    return a;
}

function parseItemExtra(item) {
    try {
        return JSON.parse(item.extra_data || "{}");
    } catch (err) {
        console.warn('[parseItemExtra] Failed to parse extra_data:', err.message || err);
        return {};
    }
}

function itemImageUrl(item) {
    const ex = parseItemExtra(item);
    const u = ex.image || ex.image_url || ex.url || "";
    return typeof u === "string" ? u.trim() : "";
}

function wordCountAll() {
    return items.length || 0;
}

function setStatus(text) {
    const el = $("child-status");
    if (el) el.textContent = text;
}

function updateStars() {
    const el = $("star-count");
    if (!el) return;
    el.textContent = String(starCount);
}

function setActiveLessonTab(lessonName) {
    selectedLesson = lessonName;
    const sel = $("lesson-select");
    if (sel) sel.value = lessonName;
}

function isLessonComplete(subject, textbook, lesson) {
    try {
        const key  = `nss_done_${subject}_${textbook}_${lesson}`;
        const done = new Set(JSON.parse(localStorage.getItem(key) || "[]"));
        return ROADMAP_STAGES.every(s => done.has(s));
    } catch (err) { console.warn('[isLessonComplete] localStorage read failed:', err.message || err); return false; }
}

function refreshLessonCompletion() {
    const sel = $("lesson-select");
    if (!sel) return;
    Array.from(sel.options).forEach(opt => {
        if (!opt.value) return;
        const done = isLessonComplete(currentSubject, currentTextbook, opt.value);
        opt.textContent = (done ? "✓ " : "") + opt.value + (opt.dataset.ready === "false" ? " ·" : "");
    });
}

async function loadTextbooks(subject) {
    const sel = $("textbook-select");
    if (!sel) return;
    sel.innerHTML = '<option value="">Select textbook</option>';

    try {
        const res = await fetch(`/api/textbooks/${encodeURIComponent(subject)}`);
        if (res.ok) {
            const data = await res.json();
            (data.textbooks || []).forEach((tb) => {
                const opt = document.createElement("option");
                opt.value = tb;
                opt.textContent = tb;
                sel.appendChild(opt);
            });
            // 교재가 하나면 자동 선택
            if (data.textbooks && data.textbooks.length === 1) {
                sel.value = data.textbooks[0];
                await loadLessons(subject, data.textbooks[0]);
            }
        }
    } catch (err) {
        console.warn('[loadTextbooks] Failed to fetch textbooks:', err.message || err);
    }
}

async function loadLessons(subject, textbook) {
    currentTextbook = textbook;
    const sel = $("lesson-select");
    if (!sel) return;
    sel.innerHTML = '<option value="">Select lesson</option>';

    if (!textbook) return;

    let lessons = [];
    try {
        const res = await fetch(`/api/lessons/${encodeURIComponent(subject)}/${encodeURIComponent(textbook)}`);
        if (res.ok) {
            const data = await res.json();
            lessons = (data.lessons || []).map((l) =>
                typeof l === "string" ? { name: l, ready: true } : l
            );
        }
    } catch (err) {
        console.warn('[loadLessons] Failed to fetch lessons:', err.message || err);
    }

    if (!lessons.length) { setStatus("No lessons yet — upload an image to get started."); return; }

    const names = lessons.map((l) => l.name);
    if (LESSON_REQUEST && names.includes(LESSON_REQUEST)) selectedLesson = LESSON_REQUEST;
    else if (!names.includes(selectedLesson)) selectedLesson = lessons[0].name;

    lessons.forEach(({ name: l, ready }) => {
        const opt = document.createElement("option");
        opt.value = l;
        const done = isLessonComplete(subject, textbook, l);
        opt.textContent = `${done ? "✓ " : ""}${l}${ready ? "" : " ·"}`;
        opt.dataset.ready = ready ? "true" : "false";
        if (l === selectedLesson) opt.selected = true;
        sel.appendChild(opt);
    });

    // Lesson change handler
    sel.onchange = () => {
        const l = sel.value;
        if (!l || l === selectedLesson) return;
        const lessonObj = lessons.find(x => x.name === l);
        const ready = lessonObj ? lessonObj.ready : true;
        setActiveLessonTab(l);
        sessionActive = false;
        roadmapComplete = allStagesDone();
        stage = null;
        stageIndex = 0;
        currentPhaseIndex = 0;
        unlockedPhaseIndex = 0;
        spState.pass = 1;
        wrongMap = {};
        items = [];
        wordVaultSet.clear();
        renderWordVault();
        renderIdleStage();
        updateRoadmapUI();
        updateProgressPct();
        updateChallengeMeta();
        refreshStartLabel();
        setStatus(ready ? `${l} selected — press Start` : `${l} — upload an image first`);
    };
}

async function loadStudyItems(lesson) {
    const res = await fetch(`/api/study/${encodeURIComponent(currentSubject)}/${encodeURIComponent(currentTextbook)}/${encodeURIComponent(lesson)}`);
    if (!res.ok) {
        let txt = "";
        try {
            txt = await res.text();
        } catch {}
        const msg = txt ? txt.slice(0, 250) : "";
        throw new Error(`Failed to load lesson (${res.status}). ${msg}`.trim());
    }
    const data = await res.json();
    items = data.items || [];
    return data.progress || null;
}

async function apiPreviewTTS(item) {
    try {
        await fetch("/api/tts/preview_sequence", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ word: item.answer, meaning: item.question, example: item.hint }),
        });
    } catch (err) {
        console.warn('[TTS] Preview failed:', err.message || err);
    }
}

let _wordOnlyInFlight = false;
async function apiWordOnly(word) {
    if (_wordOnlyInFlight) return;
    _wordOnlyInFlight = true;
    try {
        const res = await fetch("/api/tts/word_only", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ word }),
        });
        if (!res.ok) return;
        const blob = await res.blob();
        if (blob.size === 0) return;
        const url = URL.createObjectURL(blob);
        const audio = new Audio(url);
        await new Promise((resolve, reject) => {
            audio.onended = () => { URL.revokeObjectURL(url); resolve(); };
            audio.onerror = (e) => { URL.revokeObjectURL(url); reject(e); };
            audio.play().catch(reject);
        });
    } catch (err) {
        if (err.name !== 'AbortError') console.warn('[TTS] apiWordOnly failed:', err.message || err);
    } finally {
        _wordOnlyInFlight = false;
    }
}

let _exampleFullInFlight = false;
async function apiExampleFull(sentence) {
    if (_exampleFullInFlight) return;
    _exampleFullInFlight = true;
    try {
        const res = await fetch("/api/tts/example_full", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ sentence }),
        });
        if (!res.ok) return;
        const blob = await res.blob();
        if (blob.size === 0) return;
        const url = URL.createObjectURL(blob);
        const audio = new Audio(url);
        await new Promise((resolve, reject) => {
            audio.onended = () => { URL.revokeObjectURL(url); resolve(); };
            audio.onerror = (e) => { URL.revokeObjectURL(url); reject(e); };
            audio.play().catch(reject);
        });
    } catch (err) {
        console.warn('[TTS] apiExampleFull failed:', err.message || err);
    } finally {
        _exampleFullInFlight = false;
    }
}

async function apiTutorReply(word, sentence) {
    try {
        const res = await fetch("/api/tutor", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ word, sentence }),
        });
        if (!res.ok) throw new Error(`tutor ${res.status}`);
        const d = await res.json();
        return d.feedback || "";
    } catch {
        return `🪄 Great sentence using "${word}"! 💖\n✨ Ollama is sleeping — try again in a moment.`;
    }
}

async function evaluateSentence(word, sentence) {
    // Route through backend /api/evaluate-sentence (Ollama → Gemini fallback)
    try {
        const res = await fetch('/api/evaluate-sentence', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ word, sentence }),
        });
        if (!res.ok) throw new Error(`evaluate ${res.status}`);
        const result = await res.json();
        return { structured: true, data: result };
    } catch {
        const feedback = await apiTutorReply(word, sentence);
        return { structured: false, data: feedback };
    }
}

function formatStructuredFeedback(result) {
    const grammarIcon = result.grammar.correct ? "✅" : "⚠️";
    const wordIcon    = result.wordUsage.correct ? "✅" : "⚠️";
    const stars       = "⭐".repeat(Math.min(5, Math.max(1, result.creativity.score || 1)));
    return grammarIcon + " Grammar: " + result.grammar.feedback + "\n"
         + wordIcon    + " Word Use: " + result.wordUsage.feedback + "\n"
         + stars       + " Creativity: " + result.creativity.feedback + "\n"
         + "🎉 " + result.overall;
}

async function savePracticeSentence(itemId, sentence, lesson) {
    try {
        await fetch("/api/practice/sentence", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ subject: currentSubject, textbook: currentTextbook, lesson, item_id: itemId, sentence }),
        });
    } catch (err) {
        console.warn('[save] Practice sentence not saved:', err.message || err);
    }
}

async function loadOwnSentences(lesson) {
    try {
        const res = await fetch(`/api/practice/sentences/${encodeURIComponent(currentSubject)}/${encodeURIComponent(currentTextbook)}/${encodeURIComponent(lesson)}`);
        if (!res.ok) return {};
        const data = await res.json();
        return data.by_item_id || {};
    } catch (err) {
        console.warn('[load] Own sentences fetch failed:', err.message || err);
        return {};
    }
}

async function apiSpartaReset() {
    try {
        await fetch("/api/progress/sparta_reset", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ subject: currentSubject, textbook: currentTextbook, lesson: lessonSelected() }),
        });
    } catch (err) {
        console.warn('[reset] Sparta reset failed:', err.message || err);
    }
}

function lessonSelected() {
    return selectedLesson;
}

function stageTitle() {
    if (stage === STAGE.PREVIEW) return "Step 1 — Preview";
    if (stage === STAGE.A)       return "Step 2 — Word Match";
    if (stage === STAGE.B)       return "Step 3 — Fill the Blank";
    if (stage === STAGE.C)       return "Step 4 — Spelling Master";
    if (stage === STAGE.D)       return "Step 5 — Make a Sentence";
    if (stage === STAGE.EXAM)    return "Step 6 — Final Test";
    return "Learning";
}

function bumpWrong(item) {
    wrongMap[item.id] = (wrongMap[item.id] || 0) + 1;
    _trackWordAttempt(item, false, "");
}

const _particleTimers = [];

function showPerfectBanner(text) {
    const el = $("perfect-banner");
    if (!el) return;
    el.textContent = text;
    el.classList.remove("fire");
    void el.offsetWidth; // reflow
    el.classList.add("fire");
}

function particleBurst(count) {
    const layer = $("particle-layer");
    if (!layer) return;
    const n = Math.min(CONF.PARTICLE_MAX, Math.max(8, count | 0));
    const rect = layer.getBoundingClientRect();
    const cx = rect.width * 0.5;
    const cy = rect.height * 0.35;
    for (let i = 0; i < n; i++) {
        const p = document.createElement("div");
        p.className = "particle";
        const ang = (Math.PI * 2 * i) / n + Math.random() * 0.4;
        const dist = 80 + Math.random() * 120;
        p.style.left = `${cx + (Math.random() - 0.5) * 40}px`;
        p.style.top = `${cy + (Math.random() - 0.5) * 40}px`;
        p.style.setProperty("--dx", `${Math.cos(ang) * dist}px`);
        p.style.setProperty("--dy", `${Math.sin(ang) * dist - 20}px`);
        layer.appendChild(p);
        const tid = setTimeout(() => {
            p.remove();
            const idx = _particleTimers.indexOf(tid);
            if (idx !== -1) _particleTimers.splice(idx, 1);
        }, CONF.PARTICLE_LIFETIME);
        _particleTimers.push(tid);
    }
}

// 페이지 이탈 시 파티클 타이머 정리 (메모리릭 방지)
window.addEventListener("pagehide", () => {
    _particleTimers.forEach(clearTimeout);
    _particleTimers.length = 0;
    const layer = $("particle-layer");
    if (layer) layer.innerHTML = "";
});

function animateStageClear(onDone) {
    const card = $("stage-card");
    if (!card) {
        if (onDone) onDone();
        return;
    }
    card.classList.add("fx-swoosh");
    setTimeout(() => {
        if (onDone) onDone();
    }, 440);
}

function renderWordVault() {
    const el = $("word-vault");
    if (!el) return;
    el.innerHTML = "";
    [...wordVaultSet].sort((a, b) => a.localeCompare(b)).forEach((w) => {
        const s = document.createElement("span");
        s.className = "vault-chip";
        s.textContent = w;
        el.appendChild(s);
    });
}

function addWordVault(word) {
    const w = String(word || "").trim();
    if (!w) return;
    wordVaultSet.add(w);
    renderWordVault();
}

function showMagicOverlayBrief(resetCount) {
    const o = $("magic-overlay");
    const c = $("magic-count");
    if (c) c.textContent = String(resetCount);
    if (o) {
        o.classList.remove("hidden");
        setTimeout(() => o.classList.add("hidden"), 1150);
    }
}

function intraPhaseProgress() {
    const n = Math.max(1, wordCountAll());
    if (stage === STAGE.C) {
        const pass = spState.pass || 1;
        return (stageIndex + (pass - 1) / 3) / n;
    }
    return stageIndex / n;
}

function updateProgressPct() {
    const el = $("progress-pct");
    if (!el) return;

    function setMeta(text) {
        const m = $("challenge-meta");
        if (m) m.textContent = text;
    }
    function setRingColor(pct) {
        const fill = document.getElementById("progress-ring-fill");
        if (!fill) return;
        if (pct < 30)       fill.style.stroke = "";          // default blue (CSS)
        else if (pct < 70)  fill.style.stroke = "#22c55e";   // green
        else                fill.style.stroke = "#f59e0b";   // gold
    }

    if (stage === STAGE.EXAM) {
        const den = Math.max(1, examQueue.length);
        // exam progress handled separately
        el.textContent = `${pct}%`;
        setMeta(`${examIndex}/${examQueue.length} words`);
        setRingColor(pct);
        return;
    }
    if (!sessionActive && !roadmapComplete) {
        el.textContent = "0%";
        setMeta("");
        setRingColor(0);
        return;
    }
    if (roadmapComplete) {
        el.textContent = "100%";
        setMeta("All done! 🎉");
        setRingColor(100);
        return;
    }
    const intra = intraPhaseProgress();
    const pct = Math.min(100, Math.round(((currentPhaseIndex + intra) / ROADMAP_STAGES.length) * 100));
    el.textContent = `${pct}%`;
    setRingColor(pct);

    const n = Math.max(1, items.length);
    let metaText = "";
    if (stage === STAGE.PREVIEW) {
        metaText = `${Math.min(stageIndex + 1, n)}/${n} words`;
    } else if (stage === STAGE.A) {
        metaText = `Round ${wmState.round + 1}/3`;
    } else if (stage === STAGE.B) {
        if (fbState.retryMode) {
            metaText = `Retry ${fbState.retryQueue.length - fbState.retryIndex} left`;
        } else {
            metaText = `${Math.min(stageIndex + 1, n)}/${n} words`;
        }
    } else if (stage === STAGE.C) {
        if (spState.retryMode) {
            metaText = `Retry ${spState.retryQueue.length - spState.retryIndex} left`;
        } else {
            metaText = `${Math.min(stageIndex + 1, n)}/${n} words`;
        }
    } else if (stage === STAGE.D) {
        metaText = `${Math.min(stageIndex + 1, n)}/${n} words`;
    }
    setMeta(metaText);
}

function updateChallengeMeta() {
    // challenge-meta is now managed by updateProgressPct()
}

function initLessonDropdownUI() {
    const sel      = document.getElementById('lesson-select');
    const display  = document.getElementById('sb-lesson-name');
    const dropdown = document.getElementById('sb-lesson-dropdown');
    if (!sel || !display || !dropdown) return;

    const nameEl = display.querySelector('.sb-tb-name-text');

    function cleanText(t) {
        return t.replace(/^✓\s*/, '').replace(/\s*·\s*$/, '').trim();
    }

    function sync() {
        const opt = sel.options[sel.selectedIndex];
        if (nameEl) nameEl.textContent = (opt && opt.value) ? cleanText(opt.text) : '—';
    }

    function buildDropdown() {
        dropdown.innerHTML = '';
        const cur = sel.value;
        Array.from(sel.options).filter(o => o.value).forEach(opt => {
            const item = document.createElement('div');
            item.className = 'sb-tb-option' + (opt.value === cur ? ' selected' : '');
            item.textContent = cleanText(opt.text);
            item.addEventListener('click', () => {
                sel.value = opt.value;
                sel.dispatchEvent(new Event('change'));
                closeDropdown();
            });
            dropdown.appendChild(item);
        });
    }

    function openDropdown() {
        buildDropdown();
        dropdown.classList.add('open');
        display.classList.add('open');
    }

    function closeDropdown() {
        dropdown.classList.remove('open');
        display.classList.remove('open');
    }

    display.addEventListener('click', e => {
        e.stopPropagation();
        dropdown.classList.contains('open') ? closeDropdown() : openDropdown();
    });

    document.addEventListener('click', closeDropdown);

    function syncIdleCard() {
        const opt = sel.options[sel.selectedIndex];
        const nameIdleEl = document.getElementById('idle-lesson-name');
        const metaEl = document.getElementById('idle-lesson-meta');
        if (!nameIdleEl) return;
        if (opt && opt.value) {
            nameIdleEl.textContent = cleanText(opt.text);
            if (metaEl) {
                if (items && items.length) {
                    metaEl.textContent = items.length + ' words \u00b7 5 steps';
                } else {
                    metaEl.textContent = 'Loading...';
                    var _sub = typeof currentSubject !== 'undefined' ? currentSubject : 'English';
                    var _tb = typeof currentTextbook !== 'undefined' ? currentTextbook : 'Voca_8000';
                    fetch('/api/study/' + encodeURIComponent(_sub) + '/' + encodeURIComponent(_tb) + '/' + encodeURIComponent(opt.value))
                        .then(function(r) { return r.json(); })
                        .then(function(d) {
                            var cnt = (d.items && d.items.length) ? d.items.length : 0;
                            metaEl.textContent = cnt + ' words \u00b7 5 steps';
                        })
                        .catch(function() { metaEl.textContent = '0 words \u00b7 5 steps'; });
                }
            }
        } else {
            nameIdleEl.textContent = 'Select a lesson to begin';
            if (metaEl) metaEl.textContent = '';
        }
    }

    sel.addEventListener('change', () => {
        sync();
        syncIdleCard();
        if (dropdown.classList.contains('open')) buildDropdown();
    });
    new MutationObserver(() => {
        sync();
        syncIdleCard();
        if (dropdown.classList.contains('open')) buildDropdown();
    }).observe(sel, { childList: true, subtree: true });
    sync();
    syncIdleCard();
}

function initTextbookDropdownUI() {
    const sel      = document.getElementById('textbook-select');
    const display  = document.getElementById('sb-textbook-name');
    const dropdown = document.getElementById('sb-tb-dropdown');
    if (!sel || !display || !dropdown) return;

    const nameEl = display.querySelector('.sb-tb-name-text');

    function sync() {
        const opt = sel.options[sel.selectedIndex];
        if (nameEl) nameEl.textContent = (opt && opt.value) ? opt.text : '—';
    }

    function buildDropdown() {
        dropdown.innerHTML = '';
        const cur = sel.value;
        Array.from(sel.options).filter(o => o.value).forEach(opt => {
            const item = document.createElement('div');
            item.className = 'sb-tb-option' + (opt.value === cur ? ' selected' : '');
            item.textContent = opt.text;
            item.addEventListener('click', () => {
                sel.value = opt.value;
                sel.dispatchEvent(new Event('change'));
                closeDropdown();
            });
            dropdown.appendChild(item);
        });
    }

    function openDropdown() {
        buildDropdown();
        dropdown.classList.add('open');
        display.classList.add('open');
    }

    function closeDropdown() {
        dropdown.classList.remove('open');
        display.classList.remove('open');
    }

    display.addEventListener('click', e => {
        e.stopPropagation();
        dropdown.classList.contains('open') ? closeDropdown() : openDropdown();
    });

    document.addEventListener('click', closeDropdown);

    sel.addEventListener('change', sync);
    new MutationObserver(() => {
        sync();
        if (dropdown.classList.contains('open')) buildDropdown();
    }).observe(sel, { childList: true, subtree: true });
    sync();
}

function initOcrButton() {
    const ocrBtn = document.getElementById('btn-ocr');
    if (!ocrBtn) return;

    function updateOcrBtn() {
        const sel = document.getElementById('lesson-select');
        if (!sel || !sel.value) { ocrBtn.style.display = 'none'; return; }
        const opt = sel.options[sel.selectedIndex];
        const isReady = opt && opt.dataset.ready !== 'false';
        ocrBtn.style.display = isReady ? 'none' : 'block';
        ocrBtn.dataset.lesson = sel.value;
    }

    const lessonSel = document.getElementById('lesson-select');
    if (lessonSel) lessonSel.addEventListener('change', () => setTimeout(updateOcrBtn, 50));
    updateOcrBtn();

    ocrBtn.addEventListener('click', async () => {
        const lesson = ocrBtn.dataset.lesson;
        if (!lesson) return;
        ocrBtn.textContent = '⏳ Running OCR… (30–60 s)';
        ocrBtn.classList.add('loading');
        ocrBtn.disabled = true;
        try {
            const res = await fetch(`/api/lessons/ingest_disk/${encodeURIComponent(lesson)}`, {
                method: 'POST'
            });
            const data = await res.json();
            if (!res.ok) throw new Error(data.detail || 'OCR failed');
            ocrBtn.textContent = `✅ ${data.words} words registered!`;
            ocrBtn.style.borderColor = 'rgba(16,185,129,0.5)';
            ocrBtn.style.color = '#059669';
            setTimeout(() => { window.location.reload(); }, 1500);
        } catch (err) {
            ocrBtn.textContent = `❌ Error: ${err.message}`;
            ocrBtn.classList.remove('loading');
            ocrBtn.disabled = false;
        }
    });
}

function initKeyboardShortcuts() {
    document.addEventListener('keydown', (e) => {
        const active = document.activeElement;
        const inInput = active && (
            active.tagName === 'INPUT' ||
            active.tagName === 'TEXTAREA' ||
            active.isContentEditable
        );

        /* Space → replay pronunciation */
        if (e.code === 'Space' && !inInput) {
            e.preventDefault();
            const item = typeof currentItem === 'function' && currentItem();
            if (item && typeof apiWordOnly === 'function') {
                apiWordOnly(item.answer);
            } else {
                const soundBtn = document.querySelector('[data-action="sound"], #btn-sound, .st-btn.sound');
                if (soundBtn) soundBtn.click();
            }
        }

        /* Escape → close open modals */
        if (e.key === 'Escape') {
            const modals = [
                document.getElementById('preview-modal'),
                document.getElementById('tutor-modal'),
                document.getElementById('magic-overlay'),
            ];
            for (const el of modals) {
                if (el && !el.hidden && el.style.display !== 'none') {
                    el.hidden = true;
                    el.style.display = 'none';
                    break;
                }
            }
        }

        /* 1–5 → jump to roadmap stage */
        if (!inInput && e.key >= '1' && e.key <= '5') {
            const stageMap = {
                '1': STAGE.PREVIEW,
                '2': STAGE.A,
                '3': STAGE.B,
                '4': STAGE.C,
                '5': STAGE.D,
            };
            const target = stageMap[e.key];
            if (target && isStageUnlocked(target)) {
                e.preventDefault();
                jumpToStage(target);
            }
        }

        /* ⌘L → next lesson */
        if (e.metaKey && e.key === 'l') {
            e.preventDefault();
            const sel = document.getElementById('lesson-select');
            if (sel && sel.options.length > 1) {
                const next = (sel.selectedIndex + 1) % sel.options.length || 1;
                sel.selectedIndex = next;
                sel.dispatchEvent(new Event('change'));
            }
        }

        /* ⌘\ → toggle sidebar */
        if (e.metaKey && e.key === '\\') {
            e.preventDefault();
            document.getElementById('sidebar').classList.toggle('collapsed');
        }

        /* ⌘, → parent mode */
        if (e.metaKey && e.key === ',') {
            e.preventDefault();
            document.getElementById('btn-parent')?.click();
        }
    });
}

function updateRoadmapUI() {
    const rm = $("roadmap");
    if (!rm) return;
    rm.innerHTML = "";
    const inExam = stage === STAGE.EXAM;
    const completedSet = getCompletedStages();

    for (let i = 0; i < ROADMAP_STAGES.length; i++) {
        const key = ROADMAP_STAGES[i];
        const isDone     = completedSet.has(key);
        const isCurrent  = stage === key;
        const isUnlocked = isStageUnlocked(key);

        const div = document.createElement("div");
        div.className = "road-pill";

        // 시각 상태 결정
        if (inExam) {
            div.classList.add("done");
            div.textContent = "✓ " + ROADMAP_LABELS[i];
        } else if (isCurrent) {
            div.classList.add("current");
            const n = items.length;
            let progressInfo = "";
            if (n > 0 && sessionActive) {
                if (stage === STAGE.A) {
                    progressInfo = ` (R${wmState.round + 1}/3)`;
                } else if (stage === STAGE.B && fbState.retryMode) {
                    progressInfo = " (retry)";
                } else if (stage === STAGE.C && spState.retryMode) {
                    progressInfo = " (retry)";
                } else {
                    progressInfo = ` (${Math.min(stageIndex + 1, n)}/${n})`;
                }
            }
            div.textContent = ROADMAP_LABELS[i] + progressInfo;
        } else if (isDone) {
            div.classList.add("done");
            div.textContent = "✓ " + ROADMAP_LABELS[i];
        } else if (isUnlocked) {
            div.classList.add("next");
            div.textContent = ROADMAP_LABELS[i];
        } else {
            div.classList.add("locked");
            div.textContent = ROADMAP_LABELS[i];
        }

        // 언락된 단계만 클릭 가능 (완료된 것도 재도전 가능)
        const canClick = !inExam && isUnlocked;
        if (canClick) {
            div.style.cursor = "pointer";
            div.title = isDone ? `${ROADMAP_LABELS[i]} — redo` : `${ROADMAP_LABELS[i]} — start`;
            div.addEventListener("click", async () => {
                if (!items.length) {
                    // 아이템 먼저 로드 후 점프
                    const lesson = lessonSelected();
                    try {
                        await loadStudyItems(lesson);
                    } catch (e) {
                        setStatus("Failed to load lesson: " + (e.message || ""));
                        return;
                    }
                }
                jumpToStage(key);
            });
        }

        // Strip numeric prefix from pill labels (e.g. "1. Preview" → "Preview")
        div.textContent = div.textContent.replace(/^\d+\.\s*/, '').replace(/^✓\s*/, '✓ ');

        rm.appendChild(div);
    }
}

function stageFxCorrect() {
    const s = $("stage");
    if (!s) return;
    s.classList.remove("fx-wrong");
    s.classList.add("fx-correct");
    setTimeout(() => s.classList.remove("fx-correct"), 650);
}

function stageFxWrong() {
    const s = $("stage");
    if (!s) return;
    s.classList.remove("fx-correct");
    s.classList.remove("fx-wrong");
    void s.offsetWidth;
    s.classList.add("fx-wrong");
    setTimeout(() => s.classList.remove("fx-wrong"), 350);
}

function showIdleCard() {
    const iw = $("idle-wrapper");
    const sc = $("stage-card");
    if (iw) iw.classList.remove("hidden");
    if (sc) sc.classList.add("hidden");
}

function showStageCard() {
    const iw = $("idle-wrapper");
    const sc = $("stage-card");
    if (iw) iw.classList.add("hidden");
    if (sc) {
        sc.classList.remove("hidden");
        sc.classList.remove("fx-swoosh");
        // Restore #stage if it was replaced by a completion screen
        if (!sc.querySelector("#stage")) {
            sc.innerHTML = '<div id="stage"></div>';
        }
    }
}

function renderIdleStage() {
    const stageEl = document.getElementById('stage');
    if (!stageEl) return;

    const lesson   = lessonSelected();
    const isDone   = allStagesDone();
    const doneSet  = getCompletedStages();
    const doneCount = doneSet.size;

    /* ── No lesson selected ── */
    if (!lesson) {
        stageEl.innerHTML = `
            <div style="display:flex;align-items:center;justify-content:center;
                        height:100%;min-height:260px;">
                <div style="background:#FFFFFF;border-radius:16px;
                            border:1px solid #E0E0E5;padding:48px;
                            min-width:320px;max-width:420px;width:100%;text-align:center;">
                    <div style="font-size:15px;font-weight:400;color:#6E6E73;line-height:1.75;">
                        Select a textbook and lesson<br>from the left panel,<br>
                        then press <strong style="color:#1D1D1F;font-weight:600;">▶ Start</strong> to begin.
                    </div>
                </div>
            </div>`;
        showIdleCard();
        // Update btn-start label
        const btn = $("btn-start");
        if (btn) {
            const done = getCompletedStages();
            const dc = ROADMAP_STAGES.filter(s => done.has(s)).length;
            if (allStagesDone()) { btn.textContent = "Repeat ↩"; }
            else if (dc === 0) { btn.textContent = "▶  Start"; }
            else {
                const next = nextStageToStart();
                const nextLabel = ROADMAP_LABELS[ROADMAP_STAGES.indexOf(next)] || "Start";
                btn.textContent = `▶  ${nextLabel}`;
            }
        }
        return;
    }

    /* ── Lesson selected: pick subtitle ── */
    let subtitle;
    if (isDone) {
        subtitle = 'All steps complete — press <strong style="color:#1D1D1F;font-weight:600;">📝 Final Test</strong> to go!';
    } else if (doneCount > 0) {
        subtitle = `${doneCount} / 5 steps complete — press <strong style="color:#1D1D1F;font-weight:600;">▶ Start</strong> to continue.`;
    } else {
        subtitle = 'Press <strong style="color:#1D1D1F;font-weight:600;">▶ Start</strong> to begin.';
    }

    const wc = wordCountAll();
    const subInfo = `${wc} words · 5 steps`;
    stageEl.innerHTML = `
        <div style="display:flex;align-items:center;justify-content:center;
                    height:100%;min-height:260px;">
            <div style="background:#FFFFFF;border-radius:16px;
                        border:1px solid #E0E0E5;padding:48px;
                        min-width:320px;max-width:420px;width:100%;text-align:center;">
                <div style="font-size:22px;font-weight:600;color:#1D1D1F;
                            margin-bottom:8px;overflow:hidden;text-overflow:ellipsis;
                            white-space:nowrap;">${escapeHtml(lesson)}</div>
                <div style="font-size:13px;color:#6E6E73;">${subInfo}</div>
                <div style="font-size:15px;color:#6E6E73;margin-top:24px;
                            line-height:1.75;">${subtitle}</div>
            </div>
        </div>`;

    showIdleCard();

    // Update btn-start label
    const btn = $("btn-start");
    if (btn) {
        const done = getCompletedStages();
        const dc = ROADMAP_STAGES.filter(s => done.has(s)).length;
        if (isDone) { btn.textContent = "Repeat ↩"; }
        else if (dc === 0) { btn.textContent = "▶  Start"; }
        else {
            const next = nextStageToStart();
            const nextLabel = ROADMAP_LABELS[ROADMAP_STAGES.indexOf(next)] || "Start";
            btn.textContent = `▶  ${nextLabel}`;
        }
    }
}

function renderRoadmapComplete() {
    const stageEl = $("stage");
    if (!stageEl) return;
    stageEl.innerHTML = `
        <p class="st-h1">All steps complete!</p>
        <p class="st-sub">Amazing work! Press Start to repeat any step, or take the Final Test below.</p>
    `;
}

// ─── Sidebar session mode ─────────────────────────────────

function wordsLeftDisplay() {
    if (!items.length) return "—";
    if (stage === STAGE.A) {
        const done = wmState.matched ? wmState.matched.size : 0;
        return `${items.length - done}/${items.length} left`;
    }
    if (stage === STAGE.PREVIEW) {
        const done = previewDoneMap ? previewDoneMap.size : 0;
        return `${items.length - done}/${items.length} left`;
    }
    if (stage === STAGE.EXAM) {
        if (!examQueue.length) return "—";
        const left = Math.max(0, examQueue.length - examIndex);
        return `${left}/${examQueue.length} left`;
    }
    const left = Math.max(0, items.length - stageIndex);
    return `${left}/${items.length} left`;
}

function updateHints() {
    const container = $("sb-hints-container");
    if (!container) return;
    container.querySelectorAll(".kb[data-hint]").forEach(h => {
        const key = h.dataset.hint;
        let active = false;
        if (sessionActive) {
            if (key === "listen") active = true;
            if (key === "submit") active = stage !== STAGE.PREVIEW && stage !== STAGE.A;
            if (key === "next")   active = stage === STAGE.PREVIEW || stage === STAGE.A;
        }
        h.classList.toggle("kb-active", active);
    });
}

function updateSessionSidebarInfo() {
    if (!sessionActive) return;
    const elLesson   = $("sb-info-lesson");
    const elStage    = $("sb-info-stage");
    const elProgress = $("sb-info-progress");
    const elWrong    = $("sb-info-wrong");
    const skipBtn    = $("sb-btn-skip");
    if (elLesson)   elLesson.textContent   = selectedLesson || "—";
    if (elStage)    elStage.textContent    = stageTitle();
    if (elProgress) elProgress.textContent = wordsLeftDisplay();
    if (elWrong) {
        const cnt = Object.keys(wrongMap).filter(k => wrongMap[k] > 0).length;
        elWrong.textContent = String(cnt);
        elWrong.classList.toggle("val-warn", cnt > 0);
    }
    if (skipBtn) skipBtn.classList.toggle("hidden", stage === STAGE.EXAM);
    updateHints();
}

function wireSbSessionButtons() {
    const listenBtn = $("sb-btn-listen");
    const skipBtn   = $("sb-btn-skip");
    if (listenBtn) {
        listenBtn.onclick = async () => {
            const item = currentItem();
            if (item) await apiWordOnly(item.answer);
        };
    }
    if (skipBtn) {
        skipBtn.onclick = () => {
            if (stage === STAGE.EXAM) return;
            stageIndex++;
            if (stageIndex >= items.length) {
                advanceToNextStage();
            } else {
                renderStage();
            }
        };
    }
}

function enterSessionSidebar() {
    const sel  = $("sb-selection-area");
    const info = $("sb-session-info");
    if (sel)  sel.classList.add("hidden");
    if (info) info.classList.remove("hidden");
    wireSbSessionButtons();
    updateSessionSidebarInfo();
}

function exitSessionSidebar() {
    const sel  = $("sb-selection-area");
    const info = $("sb-session-info");
    if (sel)  sel.classList.remove("hidden");
    if (info) info.classList.add("hidden");
    updateHints();
}

// ──────────────────────────────────────────────────────────

function renderStage() {
    _trackStageStart();
    const stageEl = $("stage");
    if (!stageEl) return;

    const mo = $("magic-overlay");
    if (mo) mo.classList.add("hidden");

    if (stage === STAGE.EXAM) {
        renderExam(stageEl);
        updateRoadmapUI();
        updateProgressPct();
        return;
    }

    if (roadmapComplete && !sessionActive) {
        renderRoadmapComplete();
        updateRoadmapUI();
        updateProgressPct();
        updateChallengeMeta();
        return;
    }

    if (!stage || !items.length) {
        renderIdleStage();
        return;
    }

    if (stage === STAGE.PREVIEW) {
        renderPreview(stageEl);
    } else if (stage === STAGE.A) {
        renderMeaningMatch(stageEl);
    } else if (stage === STAGE.B) {
        renderContextFill(stageEl);
    } else if (stage === STAGE.C) {
        renderSpelling(stageEl);
    } else if (stage === STAGE.D) {
        renderSentenceMaker(stageEl);
    }

    updateRoadmapUI();
    updateProgressPct();
    updateChallengeMeta();
    updateSessionSidebarInfo();
}

function currentItem() {
    if (!items.length) return null;
    return items[stageIndex];
}

function replaceWordWithBlank(sentence, word) {
    const re = new RegExp(escapeRe(word), "gi");
    return String(sentence).replace(re, "________");
}

function sentenceHasWord(sentence, word) {
    const w = String(word).trim();
    if (!w) return false;
    if (/^[a-zA-Z-']+$/.test(w)) {
        return new RegExp(`\\b${escapeRe(w)}\\b`, "i").test(sentence);
    }
    return sentence.toLowerCase().includes(w.toLowerCase());
}

// ─── PREVIEW: card grid ──────────────────────────────────
function renderPreview(el) {
    previewDoneMap.clear();   // reset when stage renders fresh (Start button re-enters)

    const doneCount  = () => previewDoneMap.size;
    const totalCount = items.length;

    function buildGrid() {
        el.innerHTML = "";

        // Header
        const hdr = document.createElement("div");
        hdr.className = "preview-header";
        hdr.innerHTML = `
            <h2>Step 1 — Preview</h2>
            <span class="preview-prog-pill" id="prev-prog">${doneCount()} / ${totalCount}</span>
        `;
        el.appendChild(hdr);

        // Grid
        const grid = document.createElement("div");
        grid.className = "preview-grid";
        grid.id = "preview-grid";
        items.forEach((item) => {
            const status = previewDoneMap.get(item.id); // "ok" | "miss" | undefined

            const card = document.createElement("div");
            card.className = `preview-card${status === "ok" ? " done" : status === "miss" ? " failed" : ""}`;
            card.dataset.id = item.id;

            card.innerHTML = `
                <div class="pc-word">${escapeHtml(item.answer)}</div>
                ${status === "ok"   ? `<span class="pc-badge ok"  aria-label="correct">✓</span>` : ""}
                ${status === "miss" ? `<span class="pc-badge miss" aria-label="seen">~</span>` : ""}
            `;

            card.addEventListener("click", () => openPreviewModal(item, buildGrid));
            grid.appendChild(card);
        });
        el.appendChild(grid);

        // ── All-done footer ─────────────────────────────────
        if (doneCount() === totalCount) {
            const footer = document.createElement("p");
            footer.className = "st-sub";
            footer.style.cssText = "margin-top:20px; text-align:center; font-size:14px;";
            footer.innerHTML = "All words done! 👆 Tap <strong>2. Word Match</strong> above to continue.";
            el.appendChild(footer);
        }

        updateRoadmapUI();
        updateProgressPct();
    }

    buildGrid();
}

// ─── PREVIEW: card modal with Shadow + Spell ────────────────
function openPreviewModal(item, onClose) {
    const modal   = $('preview-modal');
    const content = $('pm-content');
    if (!modal || !content) return;

    const extra    = parseItemExtra(item);
    const posRaw   = (extra.pos || '').replace(/[.\s]/g, '').toLowerCase();
    const posMap   = { n:'noun', v:'verb', adj:'adjective', adv:'adverb',
        prep:'preposition', conj:'conjunction', pron:'pronoun',
        noun:'noun', verb:'verb', adjective:'adjective',
        adverb:'adverb', preposition:'preposition' };
    const posLabel = posMap[posRaw] || posRaw;
    const word     = item.answer.trim();

    content.innerHTML = `
        ${posLabel ? `<p class="pm-pos"><span data-pos="${posLabel}">${posLabel}</span></p>` : ''}
        <p class="pm-word" id="pm-word">${escapeHtml(word)}</p>
        ${item.question ? `<p class="pm-meaning" id="pm-meaning">${escapeHtml(item.question)}</p>` : ''}
        ${item.hint     ? `<div class="pm-example" id="pm-example">"${escapeHtml(item.hint)}"</div>` : ''}
        <div class="pm-divider"></div>
        <button type="button" class="pm-listen-btn" id="pm-listen">🔊 Listen</button>
        <p class="pm-listen-hint hidden" id="pm-listen-hint">Press the mic and repeat the word</p>
        <p class="pm-shadow-label locked" id="pm-shadow-label">SHADOW (Repeat 3×)</p>
        <div class="pm-shadow-rows" id="pm-shadow-rows"></div>
        <p class="pm-spell-unlock-hint hidden" id="pm-spell-unlock-hint">Great! Now type the word</p>
        <p class="pm-spell-label locked" id="pm-spell-label">SPELL (Type 3×)</p>
        <div class="pm-spell-rows locked" id="pm-spell-rows"></div>
        <div class="pm-verdict" id="pm-verdict"></div>
    `;

    modal.classList.remove('hidden');
    modal.hidden = false;
    modal.style.display = '';

    /* shadow: null=pending, number=last score */
    const shadowState     = [null, null, null];
    const shadowRecording = [false, false, false];
    /* spell: null=pending, true=correct, false=wrong */
    const spellState = [null, null, null];
    let spellUnlocked = false;
    let activeRec = null;
    let listenDone = false;

    /* ── Levenshtein similarity (0–100) ──────────────────── */
    function similarity(a, b) {
        a = a.toLowerCase().trim();
        b = b.toLowerCase().trim();
        if (a === b) return 100;
        const m = a.length, n = b.length;
        const dp = Array.from({length: m+1}, (_, i) =>
            Array.from({length: n+1}, (_, j) => i === 0 ? j : j === 0 ? i : 0));
        for (let i = 1; i <= m; i++)
            for (let j = 1; j <= n; j++)
                dp[i][j] = a[i-1] === b[j-1]
                    ? dp[i-1][j-1]
                    : 1 + Math.min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1]);
        return Math.round((1 - dp[m][n] / Math.max(m, n)) * 100);
    }

    /* ── Shadow rows ─────────────────────────────────────── */
    function buildShadowRows() {
        const el = $('pm-shadow-rows');
        if (!el) return;
        el.innerHTML = '';
        shadowState.forEach((score, i) => {
            const passed    = score !== null && score >= 90;
            const recording = shadowRecording[i];

            const row = document.createElement('div');
            row.className = 'pm-shadow-row';

            const mic = document.createElement('button');
            mic.type = 'button';
            mic.className = 'pm-mic-btn' +
                (recording ? ' recording' : passed ? ' done' : '');
            mic.innerHTML = recording ? '&#9209;' : '🎤';
            mic.disabled = passed || !listenDone;
            if (!passed && !recording && listenDone) mic.addEventListener('click', () => startShadow(i));

            const icon = document.createElement('span');
            icon.className = 'pm-row-icon';
            icon.textContent = passed ? '✓' : '○';
            icon.style.color = passed ? '#34C759' : '#B0B0B5';

            const scoreEl = document.createElement('span');
            scoreEl.className = 'pm-score-text';
            scoreEl.textContent = score !== null ? score + '%' : '';

            row.append(mic, icon, scoreEl);
            el.appendChild(row);
        });
    }

    const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;

    function startShadow(i) {
        if (!SpeechRec) {
            /* fallback: auto-pass */
            shadowState[i] = 100;
            buildShadowRows();
            checkShadowDone();
            return;
        }
        shadowRecording[i] = true;
        buildShadowRows();

        const rec = new SpeechRec();
        rec.lang = 'en-US';
        rec.interimResults = false;
        rec.maxAlternatives = 3;

        rec.onresult = (e) => {
            const score = Math.max(...Array.from(e.results[0])
                .map(alt => similarity(alt.transcript, word)));
            shadowRecording[i] = false;
            shadowState[i] = score;
            buildShadowRows();
            if (score >= 90) {
                checkShadowDone();
            } else {
                /* retry: reset after 1.5 s */
                setTimeout(() => { shadowState[i] = null; buildShadowRows(); }, 1500);
            }
        };
        rec.onerror = () => { shadowRecording[i] = false; activeRec = null; buildShadowRows(); };
        rec.onend   = () => { if (shadowRecording[i]) { shadowRecording[i] = false; buildShadowRows(); } activeRec = null; };
        activeRec = rec;
        rec.start();
    }

    function checkShadowDone() {
        if (shadowState.every(s => s !== null && s >= 90)) {
            spellUnlocked = true;
            const hint = $('pm-spell-unlock-hint');
            if (hint) hint.classList.remove('hidden');
            buildSpellRows();
        }
    }

    /* ── Spell rows ──────────────────────────────────────── */
    function buildSpellRows() {
        const rowsEl  = $('pm-spell-rows');
        const labelEl = $('pm-spell-label');
        if (!rowsEl) return;
        const locked = !spellUnlocked;

        if (labelEl) labelEl.classList.toggle('locked', locked);
        rowsEl.classList.toggle('locked', locked);
        rowsEl.innerHTML = '';

        spellState.forEach((result, i) => {
            const row = document.createElement('div');
            row.className = 'pm-spell-row';

            const inp = document.createElement('input');
            inp.type = 'text';
            inp.className = 'pm-typing-input' +
                (result === true ? ' correct' : result === false ? ' wrong' : '');
            inp.id = `pm-inp-${i}`;
            inp.autocomplete = 'off';
            inp.setAttribute('autocorrect', 'off');
            inp.setAttribute('autocapitalize', 'off');
            inp.setAttribute('spellcheck', 'false');
            inp.placeholder = locked ? 'Complete Shadow first…' : 'Type the word…';
            inp.disabled = locked || result !== null;
            if (result === true) inp.value = word;

            const icon = document.createElement('span');
            icon.className = 'pm-row-icon';
            icon.textContent = result === true ? '✓' : result === false ? '✗' : '○';
            icon.style.color = result === true ? '#34C759' :
                               result === false ? '#FF3B30' : '#B0B0B5';

            const btn = document.createElement('button');
            btn.type = 'button';
            btn.className = 'pm-chk-btn';
            btn.textContent = 'Check';
            btn.disabled = locked || result !== null;

            btn.addEventListener('click', () => checkSpell(i));
            inp.addEventListener('keydown', e => { if (e.key === 'Enter') checkSpell(i); });

            row.append(inp, icon, btn);
            rowsEl.appendChild(row);
        });

        if (!locked) {
            const first = spellState.findIndex(s => s === null);
            if (first !== -1) setTimeout(() => {
                const el = $(`pm-inp-${first}`);
                if (el) el.focus();
            }, 60);
        }
    }

    function checkSpell(i) {
        const inp   = $(`pm-inp-${i}`);
        const guess = (inp ? inp.value : '').trim();
        if (!guess) return;
        const correct = guess.toLowerCase() === word.toLowerCase();
        spellState[i] = correct;
        if (correct) {
            fetch('/api/tts/word_only', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({word})})
                .then(r => r.blob()).then(blob => {
                    const u = URL.createObjectURL(blob);
                    const a = new Audio(u);
                    a.onended = () => URL.revokeObjectURL(u);
                    a.play().catch(() => {});
                }).catch(() => {});
        }
        buildSpellRows();
        if (spellState.every(s => s !== null)) evaluateSpell();
    }

    function evaluateSpell() {
        const allOk  = spellState.every(s => s === true);
        const verdict = $('pm-verdict');
        if (allOk) {
            const msgs = ['Perfect! You nailed it! 🎉', 'Amazing! All three! ⭐', "That's the way! 🌟"];
            verdict.className = 'pm-verdict pass';
            verdict.innerHTML = msgs[Math.floor(Math.random() * msgs.length)] +
                '<br><button type="button" class="pm-next-btn" id="pm-next">Next word →</button>';
            $('pm-next').dataset.created = Date.now();
            $('pm-next').addEventListener('click', () => closeModal('ok'));
            particleBurst(20);
        } else {
            verdict.className = 'pm-verdict retry';
            verdict.textContent = 'Not quite — try the missed ones again!';
            setTimeout(() => {
                spellState.forEach((s, i) => { if (s === false) spellState[i] = null; });
                verdict.className = 'pm-verdict';
                buildSpellRows();
            }, 1000);
        }
    }

    /* ── Listen (blob TTS) ───────────────────────────────── */
    let ttsAbort = null;
    let currentAudio = null;

    const _playTTS = async (url, body) => {
        ttsAbort = new AbortController();
        const res = await fetch(url, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(body),
            signal: ttsAbort.signal
        });
        if (!res.ok) return;
        const blob = await res.blob();
        if (blob.size < 100) return; // empty response (non-audio endpoint)
        const blobUrl = URL.createObjectURL(blob);
        currentAudio = new Audio(blobUrl);
        await new Promise((resolve, reject) => {
            currentAudio.onended = () => { URL.revokeObjectURL(blobUrl); currentAudio = null; resolve(); };
            currentAudio.onerror = () => { URL.revokeObjectURL(blobUrl); currentAudio = null; resolve(); };
            currentAudio.play().catch(() => resolve());
        });
    };

    $('pm-listen').addEventListener('click', async () => {
        const btn       = $('pm-listen');
        const wordEl    = $('pm-word');
        const meaningEl = $('pm-meaning');
        const exampleEl = $('pm-example');
        btn.disabled = true; btn.classList.add('playing'); btn.textContent = '🎵 Playing…';
        const hl = (el, on) => el && el.classList.toggle('tts-hl', on);
        try {
            for (let j = 0; j < 3; j++) {
                hl(wordEl, true); hl(meaningEl, false);
                await _playTTS('/api/tts/preview_word_meaning', {word, meaning: item.question || '', rep: j+1});
                hl(wordEl, false);
                if (meaningEl) { hl(meaningEl, true); await new Promise(r=>setTimeout(r,300)); hl(meaningEl,false); }
                if (j < 2) await new Promise(r=>setTimeout(r,350));
            }
            if (item.hint && exampleEl) {
                await new Promise(r=>setTimeout(r,300));
                hl(exampleEl, true);
                await _playTTS('/api/tts/example_full', {sentence: item.hint});
                hl(exampleEl, false);
            }
        } catch(e) {
            if (e.name !== 'AbortError') console.warn('[TTS] Listen playback error:', e.message || e);
        } finally {
            hl(wordEl,false); hl(meaningEl,false); hl(exampleEl,false);
            btn.disabled = false; btn.classList.remove('playing'); btn.textContent = '🔊 Listen';
            ttsAbort = null;
            // Listen 완료 → Shadow 언락
            listenDone = true;
            const shadowLabel = $('pm-shadow-label');
            if (shadowLabel) shadowLabel.classList.remove('locked');
            const listenHint = $('pm-listen-hint');
            if (listenHint) listenHint.classList.remove('hidden');
            buildShadowRows();
        }
    });

    /* ── Modal-scoped AbortController (removes all listeners on close) ── */
    const _modalAC = new AbortController();
    const _modalSig = { signal: _modalAC.signal };

    /* ── Close / complete ────────────────────────────────── */
    function closeModal(status) {
        stopAudio();
        if (ttsAbort) { ttsAbort.abort(); ttsAbort = null; }
        if (currentAudio) { currentAudio.pause(); currentAudio.currentTime = 0; currentAudio = null; }
        _modalAC.abort(); // 이 모달에서 등록된 모든 이벤트 리스너 일괄 제거
        previewDoneMap.set(item.id, status);
        addWordVault(word);
        modal.classList.add('hidden');

        const card = document.querySelector(`.preview-card[data-id="${item.id}"]`);
        if (card) {
            card.classList.remove('done', 'failed');
            card.classList.add(status === 'ok' ? 'done' : 'failed');
            const old = card.querySelector('.pc-badge');
            if (old) old.remove();
            const badge = document.createElement('span');
            badge.className = `pc-badge ${status === 'ok' ? 'ok' : 'miss'}`;
            badge.textContent = status === 'ok' ? '✓' : '~';
            card.appendChild(badge);
        }
        setTimeout(onClose, 400);

        if (previewDoneMap.size >= items.length) {
            _trackStageComplete(STAGE.PREVIEW);
            markStageComplete(STAGE.PREVIEW);
            updateRoadmapUI();
            refreshStartLabel();
            setTimeout(() => {
                particleBurst(48);
                showPerfectBanner("Step 1 Complete! 🎉");
                // 완료 화면을 stage-card에 표시
                const card = $('stage-card');
                if (card) {
                    card.innerHTML = `
                        <div style="display:flex;flex-direction:column;align-items:center;justify-content:center;height:100%;padding:40px;text-align:center;">
                            <div style="font-size:4rem;line-height:1;">🎉</div>
                            <div style="font-size:2rem;font-weight:900;margin:16px 0 8px;color:var(--color-text,#1D1D1F);">Preview Complete!</div>
                            <div style="font-size:1.1rem;color:var(--color-text-secondary,#6E6E73);">⭐ ${starCount} star${starCount !== 1 ? 's' : ''} earned · ${items.length} words reviewed</div>
                            <div style="font-size:1rem;color:var(--color-text-secondary,#6E6E73);margin-top:4px;">
                                ${Object.keys(wrongMap).filter(k => wrongMap[k] > 0).length > 0
                                    ? '💪 ' + Object.keys(wrongMap).filter(k => wrongMap[k] > 0).length + ' word(s) to practice more'
                                    : '✨ No mistakes — perfect!'}
                            </div>
                            <button type="button" id="preview-next-btn"
                                style="margin-top:28px;padding:14px 36px;font-size:1.1rem;font-weight:700;
                                       border:none;border-radius:12px;cursor:pointer;
                                       background:var(--color-primary,#D4619E);color:#fff;
                                       box-shadow:0 4px 12px rgba(212,97,158,0.3);
                                       transition:transform 0.15s,box-shadow 0.15s;">
                                Next → Word Match
                            </button>
                        </div>
                    `;
                    const nextBtn = $('preview-next-btn');
                    if (nextBtn) {
                        nextBtn.addEventListener('mouseenter', () => {
                            nextBtn.style.transform = 'scale(1.03)';
                            nextBtn.style.boxShadow = '0 6px 16px rgba(212,97,158,0.4)';
                        });
                        nextBtn.addEventListener('mouseleave', () => {
                            nextBtn.style.transform = '';
                            nextBtn.style.boxShadow = '0 4px 12px rgba(212,97,158,0.3)';
                        });
                        nextBtn.addEventListener('click', () => {
                            if (typeof jumpToStage === 'function') {
                                jumpToStage(STAGE.A);
                            }
                        });
                    }
                }
                setStatus("Preview complete! Click 'Next' to start Word Match.");
            }, 300);
        } else {
            const okCount = [...previewDoneMap.values()].filter(v => v === "ok").length;
            setStatus(`${okCount} / ${items.length} done`);
        }
    }

    function stopAudio() {
        if (ttsAbort) { ttsAbort.abort(); ttsAbort = null; }
        if (currentAudio) { currentAudio.pause(); currentAudio.currentTime = 0; currentAudio = null; }
        window.speechSynthesis.cancel();
        document.querySelectorAll('audio').forEach(a => { a.pause(); a.currentTime = 0; });
        if (activeRec) { try { activeRec.abort(); } catch(e) {} activeRec = null; }
    }

    $('pm-close-btn').addEventListener('click', () => closeModal('skip'), _modalSig);

    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            // Only allow outside-click close BEFORE Listen is started
            // Check DOM state: if shadow label is unlocked, Listen was done
            const shadowLocked = document.querySelector('.pm-shadow-label.locked');
            const listenBtn = document.getElementById('pm-listen');
            const listenStarted = !shadowLocked || (listenBtn && listenBtn.classList.contains('playing'));
            if (listenStarted) return;
            stopAudio();
            closeModal('skip');
        }
    }, _modalSig);

    function escHandler(e) {
        if (e.key === 'Escape') {
            closeModal('skip');
        }
        // Enter key → click Next word button if visible and not just created
        if (e.key === 'Enter') {
            const nextBtn = document.getElementById('pm-next');
            if (nextBtn) {
                const age = Date.now() - parseInt(nextBtn.dataset.created || '0');
                if (age > 300) { e.preventDefault(); nextBtn.click(); }
            }
        }
    }
    document.addEventListener('keydown', escHandler, _modalSig);

    /* ── Init ────────────────────────────────────────────── */
    buildShadowRows();
    buildSpellRows();
}

function buildMeaningChoices(item) {
    const correct = item.answer;
    const others = items.filter((x) => x.id !== item.id).map((x) => x.answer);
    const unique = shuffle([...new Set(others)]).filter((w) => w && w.toLowerCase() !== correct.toLowerCase());
    const picks = unique.slice(0, 3);
    const all = shuffle([correct, ...picks]);
    while (all.length < 4) all.push(correct);
    return all.slice(0, 4);
}

// ── SVG line helpers for Word Match ───────────────────────────
function clearWmScrollHandler() {
    if (wmState.scrollHandler) {
        window.removeEventListener("scroll", wmState.scrollHandler, true);
        wmState.scrollHandler = null;
    }
    // Remove fixed SVG overlay if present
    const old = document.getElementById("wm-svg-overlay");
    if (old) old.remove();
}

function drawWmLines() {
    let svg = document.getElementById("wm-svg-overlay");
    if (!svg) return;
    // Clear previous lines
    while (svg.firstChild) svg.removeChild(svg.firstChild);

    for (const mi of wmState.matched) {
        const wordBtn = document.getElementById("wm-w-" + mi);
        const meaningBtn = document.getElementById("wm-m-" + mi);
        if (!wordBtn || !meaningBtn) continue;

        const wr = wordBtn.getBoundingClientRect();
        const mr = meaningBtn.getBoundingClientRect();

        // Right-edge center of word button → left-edge center of meaning button
        const x1 = wr.right;
        const y1 = (wr.top + wr.bottom) / 2;
        const x2 = mr.left;
        const y2 = (mr.top + mr.bottom) / 2;

        // Bezier control points for a smooth S-curve
        const cx = (x1 + x2) / 2;
        const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
        path.setAttribute("d", "M " + x1 + " " + y1 + " C " + cx + " " + y1 + " " + cx + " " + y2 + " " + x2 + " " + y2);
        path.setAttribute("stroke", "#22c55e");
        path.setAttribute("stroke-width", "2.5");
        path.setAttribute("fill", "none");
        path.setAttribute("stroke-linecap", "round");
        path.setAttribute("opacity", "0.75");
        svg.appendChild(path);
    }
}

function updateWmButtonStates(el) {
    // 단어 버튼 상태 업데이트 (전체 재구성 대신)
    el.querySelectorAll(".wm-word-btn").forEach(btn => {
        const idx = Number(btn.dataset.idx);
        const matched = wmState.matched.has(idx);
        const selected = wmState.selectedWordIdx === idx;
        btn.classList.toggle("wm-matched", matched);
        btn.classList.toggle("wm-selected", selected && !matched);
        btn.disabled = matched;
    });
    // 뜻 버튼 상태 업데이트
    el.querySelectorAll(".wm-meaning-btn").forEach(btn => {
        const idx = Number(btn.dataset.idx);
        const matched = wmState.matched.has(idx);
        btn.classList.toggle("wm-matched", matched);
        btn.disabled = matched;
    });
    // 진행 텍스트 업데이트
    const prog = el.querySelector(".st-prog");
    if (prog) {
        const batchStart = wmState.batchIdx * wmState.BATCH_SIZE;
        const batchEnd = Math.min(batchStart + wmState.BATCH_SIZE, items.length);
        let batchMatchedCount = 0;
        for (let i = batchStart; i < batchEnd; i++) {
            if (wmState.matched.has(i)) batchMatchedCount++;
        }
        prog.textContent = batchMatchedCount + " / " + (batchEnd - batchStart) + " matched";
    }
    // SVG 라인 다시 그리기
    requestAnimationFrame(drawWmLines);
}

function renderMeaningMatch(el) {
    // ── Clean up previous scroll handler ──────────────────────
    clearWmScrollHandler();

    // ── Fresh start: reset state & shuffle items ─────────────
    if (!wmState.initialized) {
        wmState.initialized = true;
        const shuffled = shuffle(items);
        items.splice(0, items.length, ...shuffled);
        wmState.reset();
        wmState.initialized = true; // reset이 false로 되돌리므로 다시 설정
    }

    const n = items.length;
    if (!n) { advanceToNextStage(); return; }

    // ── Compute current batch range ────────────────────────────
    const batchStart   = wmState.batchIdx * wmState.BATCH_SIZE;
    const batchEnd     = Math.min(batchStart + wmState.BATCH_SIZE, n);
    const totalBatches = Math.ceil(n / wmState.BATCH_SIZE);
    const batchSize    = batchEnd - batchStart;

    // Generate or reuse meaning-column shuffle for this batch
    if (!wmState.shuffleOrder) {
        const batchIndices = [];
        for (let i = batchStart; i < batchEnd; i++) batchIndices.push(i);
        wmState.shuffleOrder = shuffle(batchIndices);
    }

    // ── Labels ─────────────────────────────────────────────────
    const roundLabel = "Round " + (wmState.round + 1) + " of 3"
        + (totalBatches > 1 ? " \u00b7 Words " + (batchStart + 1) + "\u2013" + batchEnd : "");

    // ── Build word column HTML (left: English words) ───────────
    let wordColHtml = "";
    for (let i = batchStart; i < batchEnd; i++) {
        const matched  = wmState.matched.has(i);
        const selected = wmState.selectedWordIdx === i;
        const cls = "wm-word-btn" + (matched ? " wm-matched" : selected ? " wm-selected" : "");
        const dis = matched ? " disabled" : "";
        wordColHtml += "<button class='" + cls + "' id='wm-w-" + i + "' data-idx='" + i + "' type='button'" + dis + ">"
                    + escapeHtml(items[i].answer) + "</button>";
    }

    // ── Build meaning column HTML (right: Korean, shuffled) ────
    let meaningColHtml = "";
    for (let k = 0; k < wmState.shuffleOrder.length; k++) {
        const mi = wmState.shuffleOrder[k];
        const matched = wmState.matched.has(mi);
        const cls = "wm-meaning-btn" + (matched ? " wm-matched" : "");
        const dis = matched ? " disabled" : "";
        meaningColHtml += "<button class='" + cls + "' id='wm-m-" + mi + "' data-idx='" + mi + "' type='button'" + dis + ">"
                       + escapeHtml(items[mi].question) + "</button>";
    }

    // Count matched items in current batch
    let batchMatchedCount = 0;
    for (let i = batchStart; i < batchEnd; i++) {
        if (wmState.matched.has(i)) batchMatchedCount++;
    }

    el.innerHTML = "<p class='st-h1'>Step 2 \u2014 Word Match</p>"
        + "<p class='st-sub'>" + escapeHtml(roundLabel) + " &nbsp;\u00b7&nbsp; Click a word, then click its meaning.</p>"
        + "<div class='wm-grid'>"
        +   "<div class='wm-col wm-col-words'>" + wordColHtml + "</div>"
        +   "<div class='wm-col-connector'></div>"
        +   "<div class='wm-col wm-col-meanings'>" + meaningColHtml + "</div>"
        + "</div>"
        + "<p class='st-prog'>" + batchMatchedCount + " / " + batchSize + " matched</p>";

    // ── Create fixed SVG overlay for connecting lines ──────────
    const svgNS = "http://www.w3.org/2000/svg";
    const svgEl = document.createElementNS(svgNS, "svg");
    svgEl.setAttribute("id", "wm-svg-overlay");
    svgEl.style.cssText = "position:fixed;top:0;left:0;width:100vw;height:100vh;pointer-events:none;z-index:999;overflow:visible";
    document.body.appendChild(svgEl);

    // Draw lines after layout is complete
    requestAnimationFrame(drawWmLines);

    // Redraw on scroll so lines track their buttons
    wmState.scrollHandler = function() { requestAnimationFrame(drawWmLines); };
    window.addEventListener("scroll", wmState.scrollHandler, { passive: true, capture: true });

    // ── Wire word buttons ──────────────────────────────────────
    el.querySelectorAll(".wm-word-btn:not([disabled])").forEach(function(btn) {
        btn.addEventListener("click", function() {
            const idx = Number(btn.dataset.idx);
            wmState.selectedWordIdx = (wmState.selectedWordIdx === idx) ? null : idx;
            updateWmButtonStates(el);  // 전체 재렌더링 대신 상태만 업데이트
        });
    });

    // ── Wire meaning buttons ───────────────────────────────────
    el.querySelectorAll(".wm-meaning-btn:not([disabled])").forEach(function(btn) {
        btn.addEventListener("click", async function() {
            if (wmState.selectedWordIdx === null) {
                setStatus("👈 Click a word first!");
                return;
            }
            const mi = Number(btn.dataset.idx);
            const prevSelected = wmState.selectedWordIdx;

            if (prevSelected === mi) {
                // ✅ Correct match!
                wmState.matched.add(mi);
                wmState.selectedWordIdx = null;
                stageFxCorrect();
                starCount++;
                updateStars();
                addWordVault(items[mi].answer);

                // Check if all items in current batch are matched
                let batchDone = true;
                for (let i = batchStart; i < batchEnd; i++) {
                    if (!wmState.matched.has(i)) { batchDone = false; break; }
                }

                if (batchDone) {
                    requestAnimationFrame(drawWmLines); // show final lines for batch
                    await new Promise(function(r) { setTimeout(r, 700); });

                    const hasNextBatch = (wmState.batchIdx + 1) < totalBatches;
                    if (hasNextBatch) {
                        // Advance to next batch within same round
                        wmState.batchIdx++;
                        wmState.selectedWordIdx = null;
                        wmState.shuffleOrder    = null;
                        setStatus("Great! Keep going \u2014 next group! \ud83d\udcaa");
                        renderMeaningMatch(el);
                    } else if (wmState.round < 2) {
                        // All batches done — advance round
                        wmState.round++;
                        wmState.batchIdx        = 0;
                        wmState.matched         = new Set();
                        wmState.selectedWordIdx = null;
                        wmState.shuffleOrder    = null;
                        setStatus("Round " + (wmState.round + 1) + " \u2014 go! \ud83d\udd04");
                        renderMeaningMatch(el);
                    } else {
                        items.forEach(it => { if (!wrongMap[it.id]) _trackWordAttempt(it, true, it.answer); });
                        setStatus("🎉 Word Match complete!");
                        await new Promise(function(r) { setTimeout(r, 600); });
                        clearWmScrollHandler();
                        advanceToNextStage();
                    }
                } else {
                    renderMeaningMatch(el);
                }
            } else {
                // ❌ Wrong match
                stageFxWrong();
                wmState.selectedWordIdx = null;
                btn.classList.add("wm-shake");
                setTimeout(function() { btn.classList.remove("wm-shake"); }, 500);
                setStatus("Not quite — try again!");
                renderMeaningMatch(el);
            }
        });
    });
}

function renderContextFill(el) {
    // ── Fresh start: init state ───────────────────────────────
    if (!fbState.initialized) {
        fbState.mistakeCount = {};
        fbState.retryQueue = [];
        fbState.retryMode = false;
        fbState.retryIndex = 0;
        fbState.initialized = true;
        stageIndex = 0; // 0-based index into items[]
    }

    // ── Retry mode: all main words done, now redo wrong ones ──
    if (fbState.retryMode) {
        if (fbState.retryIndex >= fbState.retryQueue.length) {
            fbState.initialized = false;
            advanceToNextStage();
            return;
        }
        const retryItem = fbState.retryQueue[fbState.retryIndex];
        renderFillItem(el, retryItem, true);
        return;
    }

    // ── Main pass ─────────────────────────────────────────────
    const item = items[stageIndex];
    if (!item) {
        // All words done — go to retry if any failed
        if (fbState.retryQueue.length > 0) {
            fbState.retryMode = true;
            fbState.retryIndex = 0;
            fbState.retryQueue.forEach(it => { fbState.mistakeCount[it.id] = 0; });
            setStatus("Almost there! Let's retry the ones you missed. 💪");
            renderContextFill(el);
        } else {
            fbState.initialized = false;
            advanceToNextStage();
        }
        return;
    }
    renderFillItem(el, item, false);
}

function renderFillItem(el, item, isRetry) {
    const example = item.hint && String(item.hint).trim() ? item.hint : "";
    const mistakes = fbState.mistakeCount[item.id] || 0;
    const total = isRetry ? fbState.retryQueue.length : items.length;
    const current = isRetry ? fbState.retryIndex + 1 : stageIndex + 1;

    // Build word box (shuffled display order, already-done ones greyed out)
    const displayOrder = items.map((it, i) => ({ it, i }));
    for (let k = displayOrder.length - 1; k > 0; k--) {
        const j = Math.floor(Math.random() * (k + 1));
        [displayOrder[k], displayOrder[j]] = [displayOrder[j], displayOrder[k]];
    }
    const wordBoxHtml = displayOrder.map(({ it, i }) => {
        const used = !isRetry && i < stageIndex;
        return `<span class="fb-word${used ? " fb-used" : ""}">${escapeHtml(it.answer)}</span>`;
    }).join(" ");

    // Hint level based on mistake count
    let hintHtml = "";
    if (mistakes >= 1) {
        const len = String(item.answer).length;
        hintHtml = `<p class="hint-line">💡 ${len} letters</p>`;
    }
    if (mistakes >= 2) {
        const first = String(item.answer).charAt(0).toUpperCase();
        hintHtml = `<p class="hint-line">💡 Starts with <strong>${escapeHtml(first)}</strong> · ${String(item.answer).length} letters</p>`;
    }

    const blanked = example ? replaceWordWithBlank(example, item.answer) : "(no example sentence)";
    const retryLabel = isRetry ? " — Retry" : "";
    const progLabel = `${current} / ${total}${isRetry ? " retries" : ""}`;

    el.innerHTML = `
        <p class="st-h1">Step 3 — Fill the Blank${retryLabel}</p>
        <div class="fb-word-box">${wordBoxHtml}</div>
        <div class="example-box">${escapeHtml(blanked)}</div>
        ${hintHtml}
        <div class="st-input-row">
            <input class="st-input" id="answer-input" type="text"
                   autocomplete="off" spellcheck="false" placeholder="Type the missing word…"/>
            <button type="button" class="st-btn" id="ctx-submit">Check ✓</button>
        </div>
        <p class="st-prog">${progLabel}</p>
    `;

    const inp = el.querySelector("#answer-input");
    if (inp) inp.focus();

    // ── Word-chip click → auto-fill input ─────────────────────
    el.querySelectorAll(".fb-word").forEach(function(span) {
        if (span.classList.contains("fb-used")) {
            span.style.cursor = "default";
            return;
        }
        span.style.cursor = "pointer";
        span.addEventListener("click", function() {
            if (span.classList.contains("fb-used")) return;
            if (inp) {
                inp.value = span.textContent.trim();
                inp.focus();
            }
        });
    });

    const submitBtn = el.querySelector("#ctx-submit");
    if (!submitBtn) return;

    const doSubmit = async () => {
        const val = (inp.value || "").trim();
        if (!val) return;

        if (val.toLowerCase() === item.answer.toLowerCase()) {
            // ✅ Correct
            stageFxCorrect();
            starCount++;
            updateStars();
            addWordVault(item.answer);
            fetch("/api/tts/word_meaning", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ word: item.answer, meaning: item.question }),
            }).catch(() => {});

            if (isRetry) {
                fbState.retryIndex++;
                const moreRetries = fbState.retryIndex < fbState.retryQueue.length;
                setStatus(moreRetries ? "Correct! Next retry..." : "All done! 🎉");
                await new Promise(r => setTimeout(r, 400));
                renderContextFill(el);
            } else {
                stageIndex++;
                const moreItems = stageIndex < items.length;
                if (!moreItems) {
                    if (fbState.retryQueue.length > 0) {
                        fbState.retryMode = true;
                        fbState.retryIndex = 0;
                        setStatus("Good job! Now let's retry " + fbState.retryQueue.length + " missed word(s). 💪");
                        await new Promise(r => setTimeout(r, 400));
                        renderContextFill(el);
                    } else {
                        fbState.initialized = false;
                        items.forEach(it => { if (!wrongMap[it.id]) _trackWordAttempt(it, true, it.answer); });
                        setStatus("🎉 Fill the Blank complete!");
                        await new Promise(r => setTimeout(r, 400));
                        advanceToNextStage();
                    }
                } else {
                    setStatus("Correct! ✓");
                    await new Promise(r => setTimeout(r, 300));
                    renderContextFill(el);
                }
            }
        } else {
            // ❌ Wrong
            bumpWrong(item);
            stageFxWrong();
            fbState.mistakeCount[item.id] = (fbState.mistakeCount[item.id] || 0) + 1;
            const mc = fbState.mistakeCount[item.id];
            inp.value = "";

            if (mc >= CONF.FB_MAX_STRIKES) {
                // 3 strikes: add to retry queue, move on
                if (!fbState.retryQueue.find(it => it.id === item.id)) {
                    fbState.retryQueue.push(item);
                }
                setStatus("Tough one — we'll come back to it! ❌");
                await new Promise(r => setTimeout(r, 600));
                if (!isRetry) {
                    stageIndex++;
                    if (stageIndex >= items.length) {
                        fbState.retryMode = true;
                        fbState.retryIndex = 0;
                        fbState.retryQueue.forEach(it => { fbState.mistakeCount[it.id] = 0; });
                        setStatus("Let's retry the words you missed! 💪");
                    }
                } else {
                    fbState.retryIndex++;
                }
                renderContextFill(el);
            } else {
                // Show stronger hint and stay on same word
                setStatus(mc === 1 ? "Not quite! Check the hint below. 💡" : "Try again — stronger hint! 💡💡");
                renderFillItem(el, item, isRetry);
            }
        }
    };

    submitBtn.addEventListener("click", doSubmit);
    if (inp) inp.addEventListener("keydown", (e) => { if (e.key === "Enter") doSubmit(); });
}

// ─── Spelling Master state ─────────────────────────────────
const spState = {
    initialized: false,
    pass: 1,
    retryQueue: [],
    retryMode: false,
    retryIndex: 0,
    masks: {},
    reset() {
        this.initialized = false;
        this.pass = 1;
        this.retryQueue = [];
        this.retryMode = false;
        this.retryIndex = 0;
        this.masks = {};
    }
};

function makeSpellMask(word, pass) {
    // pass 1: hide ~half the letters (alternating)
    // pass 2: hide a different half
    // pass 3: hide all letters
    const chars = [...word];
    const alphaIdx = chars.map((c, i) => /[a-zA-Z]/.test(c) ? i : -1).filter(i => i >= 0);
    if (!alphaIdx.length) return "____";

    if (pass === CONF.SPELLING_PASSES) {
        return chars.map(c => /[a-zA-Z]/.test(c) ? "_" : c).join("");
    }
    // pass 1: hide even-indexed alpha chars; pass 2: hide odd-indexed
    const hideSet = new Set(alphaIdx.filter((_, k) => pass === 1 ? k % 2 === 0 : k % 2 !== 0));
    return chars.map((c, i) => hideSet.has(i) ? "_" : c).join("");
}

function renderSpelling(el) {
    // ── Init ──────────────────────────────────────────────────
    if (!spState.initialized) {
        spState.initialized = true;
        spState.pass = 1;
        spState.retryQueue = [];
        spState.retryMode = false;
        spState.retryIndex = 0;
        spState.masks = {};
        stageIndex = 0;
        // Shuffle items for variety
        const shuffled = shuffle(items);
        items.splice(0, items.length, ...shuffled);
    }

    // ── Retry mode ────────────────────────────────────────────
    if (spState.retryMode) {
        if (spState.retryIndex >= spState.retryQueue.length) {
            spState.initialized = false;
            advanceToNextStage();
            return;
        }
        renderSpellItem(el, spState.retryQueue[spState.retryIndex], true);
        return;
    }

    // ── Main pass ─────────────────────────────────────────────
    const item = items[stageIndex];
    if (!item) {
        if (spState.retryQueue.length > 0) {
            spState.retryMode = true;
            spState.retryIndex = 0;
            spState.pass = 1;
            spState.masks = {};
            setStatus("Let's redo the tricky ones! 💪");
            renderSpelling(el);
        } else {
            spState.initialized = false;
            advanceToNextStage();
        }
        return;
    }

    // Precompute masks for this word if not done yet
    if (!spState.masks[stageIndex]) {
        spState.masks[stageIndex] = {
            1: makeSpellMask(item.answer, 1),
            2: makeSpellMask(item.answer, 2),
            3: makeSpellMask(item.answer, 3),
        };
    }

    renderSpellItem(el, item, false);
}

function renderSpellItem(el, item, isRetry) {
    const total = isRetry ? spState.retryQueue.length : items.length;
    const current = isRetry ? spState.retryIndex + 1 : stageIndex + 1;
    const pass = spState.pass;

    // Mask for current pass
    let mask;
    if (isRetry) {
        mask = makeSpellMask(item.answer, pass);
    } else {
        mask = (spState.masks[stageIndex] || {})[pass] || makeSpellMask(item.answer, pass);
    }

    const passDesc = pass === 1 ? "Some letters hidden" : pass === 2 ? "More letters hidden" : "All hidden — type from memory!";
    const retryLabel = isRetry ? " — Retry" : "";
    const progLabel = `${current} / ${total}${isRetry ? " retries" : ""} &nbsp;·&nbsp; Pass ${pass}/${CONF.SPELLING_PASSES}`;

    // Pass badge: red on pass 3 for tension, primary color otherwise
    const badgeBg = pass === CONF.SPELLING_PASSES
        ? "var(--color-error, #FF3B30)"
        : "var(--color-primary, #D4619E)";

    el.innerHTML = `
        <p class="st-h1">Step 4 — Spelling Master${retryLabel}</p>
        <p class="st-sub">${escapeHtml(passDesc)} &nbsp;·&nbsp; Listen, then type the word.</p>
        <div style="text-align:center">
            <span class="sp-pass-badge" style="background:${badgeBg}">
                Pass ${pass} / ${CONF.SPELLING_PASSES}
            </span>
        </div>
        <div class="sp-mask-box">${escapeHtml(mask)}</div>
        <p class="sp-meaning">${escapeHtml(item.question)}</p>
        <div class="st-input-row">
            <input class="st-input" id="answer-input" type="text"
                   autocomplete="off" spellcheck="false" placeholder="Type the word…"/>
            <button type="button" class="st-btn ghost" id="btn-listen-word">🔊 Listen</button>
            <button type="button" class="st-btn" id="spell-submit">Check</button>
        </div>
        <p id="sp-feedback" class="sp-feedback"></p>
        <p class="st-prog">${progLabel}</p>
    `;

    const inp       = el.querySelector("#answer-input");
    const submitBtn = el.querySelector("#spell-submit");
    const feedback  = el.querySelector("#sp-feedback");
    if (inp) inp.focus();

    const listenBtn = el.querySelector("#btn-listen-word");
    if (listenBtn) listenBtn.addEventListener("click", async () => {
        setStatus("Listening\u2026");
        await apiWordOnly(item.answer);
    });

    // Auto-play removed — user clicks Listen button manually

    const lockInput = () => {
        if (inp)       inp.disabled       = true;
        if (submitBtn) submitBtn.disabled = true;
    };

    const doCheck = async () => {
        const val = (inp.value || "").trim();
        if (!val) return;

        if (val.toLowerCase() === item.answer.toLowerCase()) {
            // ✅ Correct
            lockInput();
            if (pass < CONF.SPELLING_PASSES) {
                // Show green border + "Pass N ✓" then advance to next pass
                inp.style.borderColor = "#22c55e";
                inp.style.boxShadow   = "0 0 0 4px rgba(34,197,94,0.18)";
                feedback.style.color  = "#16a34a";
                feedback.textContent  = "Pass " + pass + " \u2713";
                spState.pass++;
                setStatus("Pass " + pass + " done! Now pass " + spState.pass + "\u2026");
                await new Promise(r => setTimeout(r, 600));
                renderSpelling(el);
            } else {
                // All 3 passes correct — word complete
                stageFxCorrect();
                inp.style.borderColor = "#22c55e";
                inp.style.boxShadow   = "0 0 0 4px rgba(34,197,94,0.18)";
                feedback.style.color  = "#16a34a";
                feedback.textContent  = "Perfect Spelling! \u2b50";
                spState.pass = 1;
                if (!spState.masks[stageIndex]) spState.masks[stageIndex] = {};
                starCount++;
                updateStars();
                addWordVault(item.answer);

                if (!isRetry) {
                    stageIndex++;
                } else {
                    spState.retryIndex++;
                }
                setStatus("Spelling master! \u2713");
                await new Promise(r => setTimeout(r, 700));
                renderSpelling(el);
            }
        } else {
            // ❌ Wrong — show answer for 2 seconds, then move on
            bumpWrong(item);
            stageFxWrong();
            lockInput();
            inp.value             = "";
            inp.style.borderColor = "var(--color-error, #FF3B30)";
            inp.style.boxShadow   = "0 0 0 4px var(--color-error-light, rgba(255,59,48,0.12))";
            feedback.style.color  = "var(--color-error, #FF3B30)";
            feedback.textContent  = "\uc815\ub2f5: " + item.answer;

            if (!spState.retryQueue.find(it => it.id === item.id)) {
                spState.retryQueue.push(item);
            }

            setStatus("Not quite \u2014 moving on, we\u2019ll retry it! \u274c");
            await new Promise(r => setTimeout(r, CONF.WRONG_ANSWER_DISPLAY));

            spState.pass = 1; // reset pass for next word
            if (!isRetry) {
                stageIndex++;
                if (stageIndex >= items.length) {
                    if (spState.retryQueue.length > 0) {
                        spState.retryMode  = true;
                        spState.retryIndex = 0;
                    } else {
                        spState.initialized = false;
                        advanceToNextStage();
                        return;
                    }
                }
            } else {
                spState.retryIndex++;
            }
            renderSpelling(el);
        }
    };

    if (submitBtn) submitBtn.addEventListener("click", doCheck);
    if (inp) inp.addEventListener("keydown", (e) => { if (e.key === "Enter") doCheck(); });
}

// ─── Sentence Maker state ──────────────────────────────────
const smState = {
    initialized: false,
    attempt: {},
    reset() {
        this.initialized = false;
        this.attempt = {};
    }
};

function renderSentenceMaker(el) {
    if (!smState.initialized) {
        smState.initialized = true;
        smState.attempt = {};
        stageIndex = 0;
        // Shuffle items for variety
        const shuffled = shuffle(items);
        items.splice(0, items.length, ...shuffled);
    }

    const item = items[stageIndex];
    if (!item) {
        smState.initialized = false;
        advanceToNextStage();
        return;
    }

    renderSentenceItem(el, item);
}

function renderSentenceItem(el, item) {
    const attempt = smState.attempt[item.id] || 1;
    const total = items.length;
    const current = stageIndex + 1;
    const attemptLabel = attempt === 2 ? " (2nd try)" : "";

    const hintHtml = item.question
        ? `<div class="sm-hint-block"><div class="sm-hint-meaning">${escapeHtml(item.question)}</div></div>`
        : `<div class="sm-hint-block"></div>`;

    el.innerHTML = `
        <p class="st-h1">Step 5 — Make a Sentence</p>
        <p class="st-sub">Use this word in a sentence${attemptLabel}:</p>
        <div class="sm-word-chip">${escapeHtml(item.answer)}</div>
        ${hintHtml}
        <div id="sm-feedback-area"></div>
        <div id="sm-ai-loading" class="sm-ai-loading" style="display:none;">🤖 AI가 문장을 읽고 있어요...</div>
        <div class="st-input-row" id="sm-input-row">
            <textarea class="sm-textarea" id="sentence-input" rows="3"
                      autocomplete="off" spellcheck="false" placeholder="Your sentence…"></textarea>
            <button type="button" class="st-btn" id="sent-submit">Submit ✓</button>
        </div>
        <p class="st-prog">${current} / ${total}</p>
    `;

    const inp = el.querySelector("#sentence-input");
    if (inp) inp.focus();

    // Shift+Enter = newline; Enter alone = submit
    if (inp) {
        inp.addEventListener("keydown", (e) => {
            if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                const si = el.querySelector("#sent-submit");
                if (si && !si.disabled) si.click();
            }
        });
    }

    const si = el.querySelector("#sent-submit");
    if (!si) return;

    si.addEventListener("click", async () => {
        const sentence = (inp ? inp.value || "" : "").trim();
        if (!sentence || sentence.split(/\s+/).length < 2) {
            setStatus("Write a full sentence (at least 2 words)!");
            return;
        }
        if (!sentenceHasWord(sentence, item.answer)) {
            stageFxWrong();
            setStatus("Your sentence must include \"" + item.answer + "\"!");
            return;
        }

        // Disable input while checking
        if (inp) inp.disabled = true;
        si.disabled = true;
        si.textContent = "AI checking… 🤔";
        setStatus("Asking AI tutor…");

        // Show loading animation
        const loadingEl = el.querySelector("#sm-ai-loading");
        if (loadingEl) loadingEl.style.display = "block";

        try {
            const evalResult = await evaluateSentence(item.answer, sentence);
            await savePracticeSentence(item.id, sentence, lessonSelected());
            lastTypedSentence = sentence;

            // Hide loading animation
            if (loadingEl) loadingEl.style.display = "none";

            let feedbackText;
            let hasError;
            if (evalResult.structured) {
                feedbackText = formatStructuredFeedback(evalResult.data);
                hasError = !(evalResult.data.grammar.correct && evalResult.data.wordUsage.correct);
            } else {
                feedbackText = evalResult.data;
                hasError = /correct(ed|ion)|grammar|mistake|should be|try:/i.test(feedbackText)
                         && !/perfect sentence|correct ✅|great!/i.test(feedbackText.slice(0, 80));
            }

            if (!hasError || attempt >= 2) {
                // ✅ OK or 2nd attempt → show feedback and advance
                stageFxCorrect();
                starCount++;
                updateStars();
                addWordVault(item.answer);

                const feedbackEl = el.querySelector("#sm-feedback-area");
                if (feedbackEl) {
                    feedbackEl.innerHTML = "<div class='sm-feedback'>" + escapeHtml(feedbackText).replace(/\n/g, "<br>") + "</div>"
                        + "<button type='button' class='sm-next-btn' id='sm-next'>Next Word ▶</button>";
                    const nextBtn = feedbackEl.querySelector("#sm-next");
                    if (nextBtn) nextBtn.addEventListener("click", () => {
                        stageIndex++;
                        renderSentenceMaker(el);
                    });
                }
                // Hide input row — remove from DOM to avoid CSS override
                const inputRow = el.querySelector("#sm-input-row");
                if (inputRow) inputRow.remove();
                setStatus(attempt >= 2 ? "Nice effort! Moving on. ✨" : "Great sentence! ⭐");
            } else {
                // ❌ Error on 1st attempt → show feedback, let user retry
                smState.attempt[item.id] = 2;
                const feedbackEl = el.querySelector("#sm-feedback-area");
                if (feedbackEl) {
                    feedbackEl.innerHTML = "<div class='sm-feedback sm-hint'>" + escapeHtml(feedbackText).replace(/\n/g, "<br>") + "</div>";
                }
                // Re-enable input for 2nd try
                if (inp) { inp.disabled = false; inp.value = ""; inp.focus(); }
                si.disabled = false;
                si.textContent = "Submit ✓ (2nd try)";
                setStatus("Here's a hint — give it another try! 💡");
            }
        } catch(e) {
            if (loadingEl) loadingEl.style.display = "none";
            if (inp) inp.disabled = false;
            si.disabled = false;
            si.textContent = "Submit ✓";
            setStatus("Tutor is sleeping — try again!");
        }
    });
}

function showMagicOverlay() {
    const o = $("magic-overlay");
    const c = $("magic-count");
    if (c) c.textContent = String(magicFailCount);
    if (o) o.classList.remove("hidden");
}

function hideMagicOverlay() {
    const o = $("magic-overlay");
    if (o) o.classList.add("hidden");
}

function renderExam(el) {
    const q = examQueue[examIndex];
    if (!q) return;
    const item = q.item;
    const sentence = q.mode === EXAM_MODE.OWN_SENTENCE_BLANK ? q.sentence : item.hint;

    const blanked = replaceWordWithBlank(sentence, item.answer);

    const modeLabel = q.mode === EXAM_MODE.OWN_SENTENCE_BLANK ? "Your sentence blank" : "Example blank";

    const mo = $("magic-overlay");
    if (mo) mo.classList.add("hidden");

    el.innerHTML = `
        <p class="st-h1">Perfect challenge</p>
        <p class="st-sub">${escapeHtml(modeLabel)} — type the missing word.</p>
        <div class="example-box">${escapeHtml(blanked)}</div>
        <div class="st-row">
            <button type="button" class="st-btn ghost" id="btn-exam-listen">Listen</button>
        </div>
        <div class="st-input-row">
            <input class="st-input" id="answer-input" type="text" autocomplete="off" spellcheck="false" placeholder="Word…"/>
            <button type="button" class="st-btn" id="exam-submit">Submit</button>
        </div>
        <p class="st-prog">Question ${examIndex + 1} / ${examQueue.length} — exam breaks: ${magicFailCount}</p>
    `;

    $("btn-exam-listen").addEventListener("click", async () => {
        await apiExampleFull(sentence);
    });

    $("exam-submit").addEventListener("click", async () => {
        const inp = $("answer-input");
        const val = (inp.value || "").trim();
        if (!val) return;

        if (val.toLowerCase() === item.answer.toLowerCase()) {
            stageFxCorrect();
            examIndex++;
            starCount++;
            updateStars();
            if (examIndex >= examQueue.length) {
                await finishPerfectChallenge();
                return;
            }
            renderStage();
        } else {
            bumpWrong(item);
            stageFxWrong();
            magicFailCount++;
            showMagicOverlay();
            await apiSpartaReset();
            fetch("/api/tts", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ text: "Magic broke! Reset to the beginning!" }),
            }).catch(() => {});
            inp.value = "";
            setTimeout(async () => {
                hideMagicOverlay();
                await startPerfectChallenge();
            }, 2000);
        }
    });
}

function advanceToNextStage() {
    // ── Analytics: log stage completion ──
    if (stage) _trackStageComplete(stage);
    // 현재 단계 완료 기록
    if (stage) markStageComplete(stage);

    // 축하 화면 2초 표시
    const completedStageLabel = ROADMAP_LABELS[ROADMAP_STAGES.indexOf(stage)] || "Step";
    const reviewCount = Object.keys(wrongMap).filter(k => wrongMap[k] > 0).length;
    const starsEarned = starCount;
    const allDone = allStagesDone();

    const stageEl = $("stage");
    if (stageEl) {
        // Multiple celebration patterns — pick one randomly
        const patterns = [
            { // Pattern 1: Trophy
                bg: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                icon: "🏆",
                accent: "#ffd700",
                confetti: true,
            },
            { // Pattern 2: Rocket
                bg: "linear-gradient(135deg, #f093fb 0%, #f5576c 100%)",
                icon: "🚀",
                accent: "#ff6b6b",
                confetti: false,
            },
            { // Pattern 3: Star burst
                bg: "linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)",
                icon: "🌟",
                accent: "#feca57",
                confetti: true,
            },
            { // Pattern 4: Fire
                bg: "linear-gradient(135deg, #fa709a 0%, #fee140 100%)",
                icon: "🔥",
                accent: "#ff9f43",
                confetti: false,
            },
            { // Pattern 5: Diamond
                bg: "linear-gradient(135deg, #a18cd1 0%, #fbc2eb 100%)",
                icon: "💎",
                accent: "#c56cf0",
                confetti: true,
            },
        ];
        const allDonePattern = {
            bg: "linear-gradient(135deg, #f5af19 0%, #f12711 100%)",
            icon: "🎉",
            accent: "#ffd700",
            confetti: true,
        };
        const p = allDone ? allDonePattern : patterns[Math.floor(Math.random() * patterns.length)];

        const reviewLine = reviewCount > 0
            ? `<div style="margin:12px 0 0;font-size:0.95rem;color:rgba(255,255,255,0.85);background:rgba(0,0,0,0.15);border-radius:12px;padding:8px 16px;display:inline-block;">📝 ${reviewCount} word${reviewCount > 1 ? "s" : ""} to review</div>`
            : `<div style="margin:12px 0 0;font-size:0.95rem;color:rgba(255,255,255,0.9);">✨ Perfect — no mistakes!</div>`;

        const next = allDone ? null : nextStageToStart();
        const nextLabel = next ? (ROADMAP_LABELS[ROADMAP_STAGES.indexOf(next)] || "Next") : null;
        const nextBtnHtml = allDone
            ? `<button type="button" id="stage-complete-btn" style="margin-top:24px;padding:14px 40px;border:none;border-radius:16px;background:rgba(255,255,255,0.95);color:#333;font-size:1.1rem;font-weight:700;cursor:pointer;box-shadow:0 4px 15px rgba(0,0,0,0.2);transition:transform 0.2s;">📝 Take Final Test</button>`
            : `<button type="button" id="stage-complete-btn" style="margin-top:24px;padding:14px 40px;border:none;border-radius:16px;background:rgba(255,255,255,0.95);color:#333;font-size:1.1rem;font-weight:700;cursor:pointer;box-shadow:0 4px 15px rgba(0,0,0,0.2);transition:transform 0.2s;">${nextLabel} →</button>`;

        stageEl.innerHTML = `
            <div style="display:flex;flex-direction:column;align-items:center;justify-content:center;
                        height:100%;padding:40px;text-align:center;
                        background:${p.bg};border-radius:20px;position:relative;overflow:hidden;">
                ${p.confetti ? `
                <div style="position:absolute;top:0;left:0;right:0;bottom:0;pointer-events:none;overflow:hidden;">
                    ${Array.from({length:20}, (_, i) => {
                        const x = Math.random() * 100;
                        const delay = Math.random() * 2;
                        const size = 6 + Math.random() * 8;
                        const colors = ['#ffd700','#ff6b6b','#48dbfb','#ff9ff3','#54a0ff','#5f27cd','#01a3a4','#f368e0'];
                        const color = colors[Math.floor(Math.random() * colors.length)];
                        return `<div style="position:absolute;left:${x}%;top:-10px;width:${size}px;height:${size}px;
                                    background:${color};border-radius:${Math.random()>0.5?'50%':'2px'};
                                    animation:confetti-fall ${2+Math.random()*2}s ${delay}s ease-in forwards;
                                    transform:rotate(${Math.random()*360}deg);"></div>`;
                    }).join('')}
                </div>` : ''}
                <div style="font-size:5rem;line-height:1;animation:bounce-in 0.6s ease;
                            filter:drop-shadow(0 4px 8px rgba(0,0,0,0.2));">${p.icon}</div>
                <div style="font-size:2.2rem;font-weight:900;margin:16px 0 6px;color:#fff;
                            text-shadow:0 2px 8px rgba(0,0,0,0.2);
                            animation:slide-up 0.5s 0.2s ease both;">${completedStageLabel} Complete!</div>
                <div style="font-size:1.15rem;color:rgba(255,255,255,0.9);animation:slide-up 0.5s 0.4s ease both;">
                    ⭐ ${starsEarned} star${starsEarned !== 1 ? "s" : ""} earned
                </div>
                <div style="animation:slide-up 0.5s 0.6s ease both;">${reviewLine}</div>
                <div style="animation:slide-up 0.5s 0.8s ease both;">${nextBtnHtml}</div>
            </div>
        `;

        // Add CSS animations if not already present
        if (!document.getElementById('stage-complete-styles')) {
            const style = document.createElement('style');
            style.id = 'stage-complete-styles';
            style.textContent = `
                @keyframes confetti-fall {
                    0% { transform: translateY(0) rotate(0deg); opacity: 1; }
                    100% { transform: translateY(calc(100vh)) rotate(720deg); opacity: 0; }
                }
                @keyframes bounce-in {
                    0% { transform: scale(0); opacity: 0; }
                    50% { transform: scale(1.2); }
                    100% { transform: scale(1); opacity: 1; }
                }
                @keyframes slide-up {
                    0% { transform: translateY(20px); opacity: 0; }
                    100% { transform: translateY(0); opacity: 1; }
                }
                #stage-complete-btn:hover { transform: scale(1.05); }
                #stage-complete-btn:active { transform: scale(0.98); }
            `;
            document.head.appendChild(style);
        }

        // Next stage button handler
        const completeBtn = stageEl.querySelector('#stage-complete-btn');
        if (completeBtn) {
            completeBtn.addEventListener('click', () => {
                if (allDone) {
                    // Start Final Test
                    const examBtn = $('btn-exam');
                    if (examBtn) examBtn.click();
                } else {
                    const nextKey = nextStageToStart();
                    if (nextKey) jumpToStage(nextKey);
                }
            });
        }

        particleBurst(48);
        showPerfectBanner(`${completedStageLabel} Complete! ${p.icon}`);
    }

    // 세션 상태 초기화 (자동 진행 없음 — 유저가 다음 단계 선택)
    sessionActive = false;
    stageIndex = 0;
    stage = null;
    spState.pass = 1;
    exitSessionSidebar();

    updateRoadmapUI();
    refreshLessonCompletion();

    setTimeout(() => {
        if (allDone) {
            roadmapComplete = true;
            const ex = $("btn-exam");
            if (ex) ex.disabled = false;
            refreshStartLabel();
            // Don't auto-navigate — user clicks the button
            setStatus("🎉 All steps complete! Click the button to take the Final Test.");
        } else {
            refreshStartLabel();
            // Don't auto-navigate — user clicks the "Next →" button
            const next = nextStageToStart();
            const nextLabel = ROADMAP_LABELS[ROADMAP_STAGES.indexOf(next)] || next;
            setStatus(`Step done! Click the button or tap "${nextLabel}" above.`);
        }
    }, CONF.STAGE_CLEAR_DELAY);
}

function canStartExamNow() {
    const ex = $("btn-exam");
    return ex && !ex.disabled;
}

function buildExamQueue() {
    const wrongSorted = items.map((it) => ({ it, n: wrongMap[it.id] || 0 })).sort((a, b) => b.n - a.n);

    const topWrong = wrongSorted.filter((x) => x.n > 0).slice(0, CONF.EXAM_POOL_SIZE).map((x) => x.it);
    const pool = topWrong.length ? topWrong : shuffle(items).slice(0, Math.min(CONF.EXAM_POOL_SIZE, items.length));
    const queue = [];

    for (const it of pool) {
        const hasOwn = ownSentencesByItemId[it.id] && String(ownSentencesByItemId[it.id]).trim().length > 0;
        if (hasOwn && Math.random() < 0.5) {
            queue.push({
                item: it,
                mode: EXAM_MODE.OWN_SENTENCE_BLANK,
                sentence: ownSentencesByItemId[it.id],
            });
        } else {
            queue.push({ item: it, mode: EXAM_MODE.EXAMPLE_BLANK });
        }
    }

    const finalQ = queue.length ? shuffle(queue) : shuffle(items).slice(0, CONF.EXAM_POOL_SIZE).map((it) => ({ item: it, mode: EXAM_MODE.EXAMPLE_BLANK }));
    return finalQ.slice(0, Math.min(CONF.EXAM_MAX_QUESTIONS, finalQ.length));
}

async function startPerfectChallenge() {
    ownSentencesByItemId = await loadOwnSentences(lessonSelected());
    examQueue = buildExamQueue();
    examIndex = 0;
    stage = STAGE.EXAM;
    sessionActive = true;
    magicFailCount = 0;
    renderStage();
    enterSessionSidebar();
    setStatus("Perfect challenge — good luck!");
}

async function finishPerfectChallenge() {
    _trackStageComplete("exam");
    await fetch("/api/progress/challenge_complete", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ subject: currentSubject, textbook: currentTextbook, lesson: lessonSelected() }),
    }).catch(() => {});

    if (magicFailCount === 0) {
        try { await fetch("/api/rewards/earn_all", { method: "POST" }); } catch {}
    }

    // 페이지 이동 없이 완료 화면 — 버튼 활성 상태 유지로 재도전 가능
    stage = null;
    sessionActive = false;
    exitSessionSidebar();
    const sidebar = document.getElementById('sidebar');
    if (sidebar) sidebar.classList.remove('collapsed');
    localStorage.setItem('sb_collapsed', '0');
    updateRoadmapUI();

    const stageEl = $("stage");
    const perfect = magicFailCount === 0;
    if (stageEl) {
        const bgStyle = perfect
            ? "background:linear-gradient(135deg,#f6d365 0%,#fda085 100%);border-radius:16px;padding:32px;"
            : "padding:32px;";
        const bodyLines = perfect
            ? `<div style="font-size:4rem;line-height:1;">🏆</div>
               <div style="font-size:2.2rem;font-weight:900;margin:14px 0 8px;color:#7d4600;">PERFECT!</div>
               <div style="font-size:1.2rem;font-weight:700;color:#7d4600;">No mistakes — incredible!</div>`
            : `<div style="font-size:3.5rem;line-height:1;">✅</div>
               <div style="font-size:1.8rem;font-weight:800;margin:14px 0 8px;color:#2c3e50;">Final Test Done!</div>
               <div style="font-size:1.1rem;color:#555;">Finished with ${magicFailCount} reset(s).</div>
               <div style="font-size:1rem;color:#7f8c8d;margin-top:4px;">Keep practicing!</div>`;
        stageEl.innerHTML = `
            <div style="display:flex;flex-direction:column;align-items:center;justify-content:center;height:100%;text-align:center;${bgStyle}">
                ${bodyLines}
                <div style="margin-top:28px;display:flex;gap:12px;flex-wrap:wrap;justify-content:center;">
                    <button type="button" class="exam-retry-btn" id="exam-retry-btn"
                        style="padding:10px 22px;font-size:1rem;font-weight:700;border:none;border-radius:10px;cursor:pointer;background:#3498db;color:#fff;">
                        Take Final Test Again
                    </button>
                    <button type="button" class="exam-menu-btn" id="exam-menu-btn"
                        style="padding:10px 22px;font-size:1rem;font-weight:700;border:none;border-radius:10px;cursor:pointer;background:#ecf0f1;color:#2c3e50;">
                        Back to Menu
                    </button>
                </div>
            </div>
        `;
        const retryBtn = $("exam-retry-btn");
        if (retryBtn) retryBtn.addEventListener("click", () => startPerfectChallenge());

        const menuBtn = $("exam-menu-btn");
        if (menuBtn) menuBtn.addEventListener("click", () => {
            sessionActive = false;
            renderIdleStage();
            updateRoadmapUI();
        });
    }
    particleBurst(perfect ? 48 : 32);
    showPerfectBanner(perfect ? "Perfect! 🏆" : "Final Test Done! ✅");
    setStatus(perfect
        ? "🏆 Perfect score! Click \"Test\" to retake."
        : `Done! ${magicFailCount} reset(s). Click the Test button to retry.`
    );

    // Final Test 버튼 활성 유지 → 즉시 재도전 가능
    const ex = $("btn-exam");
    if (ex) ex.disabled = false;
}

function wireTutorModal() {
    const modal = $("tutor-modal");
    const next = $("btn-tutor-next");
    if (!modal || !next) return;
    next.addEventListener("click", () => {
        modal.classList.add("hidden");
        const item = currentItem();
        if (item) addWordVault(item.answer);
        starCount++;
        updateStars();
        stageIndex++;
        if (stage && stageIndex >= wordCountAll()) advanceToNextStage();
        else renderStage();
    });
}

function wireStartButtons() {
    $("btn-start").addEventListener("click", async () => {
        const btnStart = $("btn-start");
        if (btnStart) btnStart.disabled = true;

        // 어느 스테이지부터 시작할지 결정 (다음 미완료 스테이지)
        const targetStage = nextStageToStart();
        const targetIdx   = ROADMAP_STAGES.indexOf(targetStage);

        currentPhaseIndex  = targetIdx;
        unlockedPhaseIndex = Math.max(unlockedPhaseIndex, targetIdx);
        sessionActive      = true;
        roadmapComplete    = allStagesDone(); // 이미 전부 완료라면 유지
        stage              = targetStage;
        resetAllStageState();
        magicFailCount     = 0;
        examQueue          = [];
        examIndex          = 0;
        wordVaultSet.clear();
        renderWordVault();

        // Exam 버튼: 전부 완료된 경우에만 활성화
        const ex0 = $("btn-exam");
        if (ex0) ex0.disabled = !allStagesDone();

        setStatus("Loading lesson…");
        const lesson = lessonSelected();

        showStageCard();
        const stageEl = $("stage");
        if (stageEl) {
            stageEl.innerHTML = `<p class="st-h1">Loading</p><p class="st-sub">${escapeHtml(lesson)}</p>`;
        }

        try {
            await loadStudyItems(lesson);
        } catch (e) {
            sessionActive = false;
            roadmapComplete = false;
            stage = null;
            showIdleCard();
            setStatus("Error loading lesson.");
            if (console && console.error) console.error(e);
            if (btnStart) btnStart.disabled = false;
            updateRoadmapUI();
            updateProgressPct();
            updateChallengeMeta();
            return;
        }

        if (!items.length) {
            sessionActive = false;
            stage = null;
            showIdleCard();
            setStatus("No items.");
            if (btnStart) btnStart.disabled = false;
            updateRoadmapUI();
            updateProgressPct();
            return;
        }

        const sidebar = document.getElementById('sidebar');
        if (sidebar) sidebar.classList.add('collapsed');
        localStorage.setItem('sb_collapsed', '1');
        renderStage();
        enterSessionSidebar();
        setStatus(`${stageTitle()} — start!`);

        updateRoadmapUI();
        updateProgressPct();
        updateChallengeMeta();
        refreshStartLabel();

        if (btnStart) btnStart.disabled = false;
    });

    $("btn-exam").addEventListener("click", async () => {
        if (!canStartExamNow()) return;
        await startPerfectChallenge();
    });
}

const TEXT_REPLACEMENTS = {
    'Click a word, then click its meaning.':
        'Tap a word on the left, then find its meaning on the right! 👉',
    'Type the missing word…':
        'Type the missing word ✏️',
    'Some letters hidden':
        'Some letters are hidden 👀',
    'More letters hidden':
        'More letters are hidden now! 🫣',
    'All hidden — type from memory!':
        'All hidden — type from memory! 🧠',
    'Listen, then type the word.':
        'Listen and type the word 🎧',
    'Use this word in a sentence':
        'Write a sentence using this word ✍️',
};

const roundRegex = /Round (\d+) of (\d+)\s*[·•]\s*Words (\d+)[–-](\d+)\s*[·•]\s*Click a word, then click its meaning\./;

function replaceDescriptionTexts() {
    document.querySelectorAll('.st-sub').forEach(el => {
        const roundMatch = el.textContent.match(roundRegex);
        if (roundMatch) {
            el.innerHTML = `Round ${roundMatch[1]}/${roundMatch[2]} · Words ${roundMatch[3]}–${roundMatch[4]} · Tap a word, then find its meaning! 👉`;
            return;
        }
        for (const [original, replacement] of Object.entries(TEXT_REPLACEMENTS)) {
            if (el.textContent.includes(original)) {
                el.textContent = el.textContent.replace(original, replacement);
            }
        }
    });

    const answerInput = document.querySelector('#answer-input');
    if (answerInput) {
        if (answerInput.placeholder === 'Type the missing word…') {
            answerInput.placeholder = 'Type the missing word...';
        } else if (answerInput.placeholder === 'Type the word…') {
            answerInput.placeholder = 'Type the word...';
        }
    }

    const sentenceInput = document.querySelector('#sentence-input');
    if (sentenceInput && sentenceInput.placeholder === 'Your sentence…') {
        sentenceInput.placeholder = 'Write your sentence here...';
    }
}

document.addEventListener("DOMContentLoaded", async () => {
    // 교재 드롭다운 변경 이벤트
    const textbookSel = $("textbook-select");
    if (textbookSel) {
        textbookSel.addEventListener("change", async () => {
            const tb = textbookSel.value;
            if (!tb) return;
            // 레슨 전환과 동일하게 세션 초기화
            sessionActive = false;
            roadmapComplete = false;
            stage = null;
            stageIndex = 0;
            currentPhaseIndex = 0;
            unlockedPhaseIndex = 0;
            spState.pass = 1;
            wrongMap = {};
            items = [];
            wordVaultSet.clear();
            renderWordVault();
            renderIdleStage();
            updateRoadmapUI();
            updateProgressPct();
            updateChallengeMeta();
            await loadLessons(currentSubject, tb);
            refreshStartLabel();
            setStatus(`${tb} selected — choose a lesson.`);
        });
    }

    await loadTextbooks(currentSubject);

    starCount = 0;
    updateStars();

    wireTutorModal();
    wireStartButtons();

    const btnParent = $("btn-parent");
    if (btnParent) {
        btnParent.addEventListener("click", () => {
            const lesson = encodeURIComponent(lessonSelected());
            window.location.href = `/parent?lesson=${lesson}`;
        });
    }

    // 초기 상태 복원 (localStorage 기반)
    sessionActive = false;
    roadmapComplete = allStagesDone();
    currentPhaseIndex = 0;
    unlockedPhaseIndex = 0;
    stageIndex = 0;
    stage = null;
    spState.pass = 1;

    // Exam 버튼 상태 복원
    const ex = $("btn-exam");
    if (ex) ex.disabled = !allStagesDone();

    renderIdleStage();
    updateRoadmapUI();
    updateProgressPct();
    updateChallengeMeta();
    renderWordVault();
    refreshStartLabel();
    if (typeof initWeeklyCalendar === "function") initWeeklyCalendar();

    const previewDone = getCompletedStages().has(STAGE.PREVIEW);
    if (previewDone && selectedLesson) {
        setStatus(`${selectedLesson} — Step 1 complete! Press Start to repeat.`);
    } else {
        setStatus("Select a lesson and press Start.");
    }

    /* ── Word Match: flash animation on correct match ─────────
       Watches for .wm-matched being added to any card and briefly
       applies .wm-flash.                                         */
    (function() {
        const stageEl = document.getElementById('stage-content');
        if (!stageEl) return;
        const observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(m) {
                if (m.type !== 'attributes' || m.attributeName !== 'class') return;
                const el = m.target;
                if (!el.classList.contains('wm-word-btn') && !el.classList.contains('wm-meaning-btn')) return;
                if (!el.classList.contains('wm-matched')) return;
                el.classList.add('wm-flash');
                setTimeout(function() { el.classList.remove('wm-flash'); }, 400);
            });
        });
        observer.observe(stageEl, { subtree: true, attributes: true, attributeFilter: ['class'] });
    })();

    // ── TASK 1: Sidebar toggle ──────────────────────────────────────
    const _sidebar = document.getElementById('sidebar');
    const _toggle  = document.getElementById('sidebar-toggle');
    if (_toggle && _sidebar) {
        _toggle.addEventListener('click', () => _sidebar.classList.toggle('collapsed'));
    }

    // ── TASK 2: Restore subject from localStorage ──────────────────
    const savedSubject = localStorage.getItem('subject_mode') || 'eng';
    window.setSubject(savedSubject);

    // ── TASK 3 & 4: Init dropdown UIs ─────────────────────────────
    initLessonDropdownUI();
    initTextbookDropdownUI();

    // ── TASK 7: OCR button ─────────────────────────────────────────
    initOcrButton();

    // ── TASK 8: Progress bar sync ──────────────────────────────────
    (function() {
        const fill  = document.getElementById('progress-ring-fill');
        const label = document.getElementById('progress-pct');
        const bar   = document.getElementById('top-progress-fill');
        const CIRC  = 2 * Math.PI * 16;

        function updateProgress() {
            const pct = parseFloat(label ? label.textContent : '0') || 0;
            if (fill) fill.style.strokeDashoffset = CIRC - (pct / 100) * CIRC;
            if (bar)  bar.style.width = pct + '%';
        }

        if (label) {
            new MutationObserver(updateProgress)
                .observe(label, { childList: true, characterData: true, subtree: true });
        }
        updateProgress();
    })();

    // ── TASK 9: Stars mirror (sidebar → top-bar) ──────────────────
    (function() {
        const src  = document.getElementById('star-count');
        const dest = document.getElementById('stars-count');
        if (!src || !dest) return;
        function syncStars() { dest.textContent = src.textContent; }
        new MutationObserver(syncStars)
            .observe(src, { childList: true, characterData: true, subtree: true });
        syncStars();
    })();

    // ── TASK 10: fx-wrong propagation ─────────────────────────────
    (function() {
        const stage = document.getElementById('stage');
        const card  = document.getElementById('stage-card');
        if (!stage || !card) return;

        new MutationObserver(() => {
            if (stage.classList.contains('fx-wrong')) {
                card.classList.remove('fx-wrong');
                void card.offsetWidth;
                card.classList.add('fx-wrong');
                card.addEventListener('animationend', () => card.classList.remove('fx-wrong'), { once: true });
            }
        }).observe(stage, { attributes: true, attributeFilter: ['class'] });
    })();

    // ── TASK 11: fx-correct / Perfect banner ──────────────────────
    (function() {
        const stageObs  = document.getElementById('stage');
        const banner = document.getElementById('perfect-banner');
        if (!stageObs || !banner) return;

        new MutationObserver(() => {
            if (stageObs.classList.contains('fx-correct')) {
                banner.classList.remove('fire');
                void banner.offsetWidth;
                banner.classList.add('fire');
            }
        }).observe(stageObs, { attributes: true, attributeFilter: ['class'] });
    })();

    // ── TASK 12: Keyboard shortcuts ────────────────────────────────
    initKeyboardShortcuts();

    // Text replacement observer
    const stageEl = document.getElementById('stage') || document.getElementById('stage-card');
    if (stageEl) {
        const textObserver = new MutationObserver(() => replaceDescriptionTexts());
        textObserver.observe(stageEl, { childList: true, subtree: true, characterData: true });
        replaceDescriptionTexts();
    }
});


// ─── Dev Tools (Console에서 사용) ─────────────────────────────
window.devComplete = function() { advanceToNextStage(); };
window.devCompleteUpTo = function(n) {
    const stages = [STAGE.PREVIEW, STAGE.A, STAGE.B, STAGE.C, STAGE.D];
    for (let i = 0; i < Math.min(n, stages.length); i++) markStageComplete(stages[i]);
    updateRoadmapUI(); refreshStartLabel(); renderStage();
    console.log("✅ Completed up to stage", n);
};
window.devReset = function() {
    localStorage.removeItem(stageStorageKey());
    location.reload();
};
window.devJump = function(n) {
    const stages = [STAGE.PREVIEW, STAGE.A, STAGE.B, STAGE.C, STAGE.D];
    if (n >= 1 && n <= 5) jumpToStage(stages[n-1]);
};
window.devSkipWord = function() {
    stageIndex++;
    renderStage();
    console.log("⏭ Skipped to word", stageIndex + 1);
};
console.log("🛠 Dev tools: devComplete() devCompleteUpTo(n) devReset() devJump(n) devSkipWord()");

/* ── Monthly Calendar ──────────────────── */
var _calYear, _calMonth;

function initWeeklyCalendar() { initMonthlyCalendar(); }

function initMonthlyCalendar() {
    var now = new Date();
    _calYear = now.getFullYear();
    _calMonth = now.getMonth();
    renderMonthlyCalendar();
    var prev = document.getElementById("sb-cal-prev");
    var next = document.getElementById("sb-cal-next");
    if (prev) prev.onclick = function() { _calMonth--; if (_calMonth < 0) { _calMonth = 11; _calYear--; } renderMonthlyCalendar(); };
    if (next) next.onclick = function() { _calMonth++; if (_calMonth > 11) { _calMonth = 0; _calYear++; } renderMonthlyCalendar(); };
}

function renderMonthlyCalendar() {
    var grid = document.getElementById("sb-cal-grid");
    var title = document.getElementById("sb-cal-title");
    if (!grid) return;
    var months = ["January","February","March","April","May","June","July","August","September","October","November","December"];
    if (title) title.textContent = months[_calMonth] + " " + _calYear;
    grid.innerHTML = "";
    var headers = ["Mo","Tu","We","Th","Fr","Sa","Su"];
    headers.forEach(function(h) {
        var el = document.createElement("div");
        el.className = "sb-cal-day-header";
        el.textContent = h;
        grid.appendChild(el);
    });
    var firstDay = new Date(_calYear, _calMonth, 1).getDay();
    var startOffset = firstDay === 0 ? 6 : firstDay - 1;
    var daysInMonth = new Date(_calYear, _calMonth + 1, 0).getDate();
    var now = new Date();
    var todayDate = now.getDate();
    var todayMonth = now.getMonth();
    var todayYear = now.getFullYear();
    for (var i = 0; i < startOffset; i++) {
        var empty = document.createElement("div");
        empty.className = "sb-cal-day empty";
        grid.appendChild(empty);
    }
    for (var d = 1; d <= daysInMonth; d++) {
        var cell = document.createElement("div");
        cell.className = "sb-cal-day";
        cell.textContent = d;
        cell.dataset.date = _calYear + "-" + String(_calMonth+1).padStart(2,"0") + "-" + String(d).padStart(2,"0");
        if (d === todayDate && _calMonth === todayMonth && _calYear === todayYear) {
            cell.classList.add("today");
        }
        grid.appendChild(cell);
    }
    loadMonthlyStudyData();
}

function loadMonthlyStudyData() {
    fetch("/api/dashboard/analytics")
        .then(function(res) { return res.json(); })
        .then(function(data) {
            var sessions = data.daily_sessions || data.sessions || [];
            var studiedDates = new Set();
            sessions.forEach(function(s) {
                var dateStr = s.date || (s.started_at ? s.started_at.substring(0,10) : "");
                if (dateStr) studiedDates.add(dateStr);
            });
            var grid = document.getElementById("sb-cal-grid");
            if (!grid) return;
            grid.querySelectorAll(".sb-cal-day[data-date]").forEach(function(cell) {
                if (studiedDates.has(cell.dataset.date)) {
                    cell.classList.add("studied");
                }
            });
        })
        .catch(function() {});
}
