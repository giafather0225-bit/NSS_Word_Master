/* ================================================================
   core.js — Constants, global state, utilities, audio FX, and
             session-storage helpers.
   Section: English / System
   Dependencies: none (loaded first)
   API endpoints: none
   ================================================================ */

/* eslint-disable no-use-before-define */

// ─── Constants ────────────────────────────────────────────────
/**
 * Application-wide configuration constants.
 * @tag SYSTEM
 */
const CONF = {
    TTS_REPEAT: 3,
    EXAM_POOL_SIZE: 5,
    EXAM_MAX_QUESTIONS: 8,
    SPELLING_PASSES: 3,
    FB_MAX_STRIKES: 3,
    FB_RETRY_MAX_STRIKES: 3,
    PARTICLE_MAX: 48,
    PARTICLE_LIFETIME: 3000,
    STAGE_CLEAR_DELAY: 2000,
    WRONG_ANSWER_DISPLAY: 2000,
};

// ─── Stage / Roadmap enums ─────────────────────────────────────
/**
 * Stage key enumeration.
 * @tag NAVIGATION ENGLISH
 */
const STAGE = {
    PREVIEW: "PREVIEW",
    A: "A",
    B: "B",
    C: "C",
    D: "D",
    EXAM: "EXAM",
};

/** @tag NAVIGATION */
const ROADMAP_STAGES = [STAGE.PREVIEW, STAGE.A, STAGE.B, STAGE.C, STAGE.D];
/** @tag NAVIGATION */
const ROADMAP_LABELS = ["1. Preview", "2. Word Match", "3. Fill Blank", "4. Spelling", "5. Sentence"];
/** @tag NAVIGATION */
const IMPLEMENTED_STAGES = [STAGE.PREVIEW, STAGE.A, STAGE.B, STAGE.C, STAGE.D];

/** @tag FINAL_TEST */
const EXAM_MODE = {
    EXAMPLE_BLANK: "example",
    OWN_SENTENCE_BLANK: "own",
};

// ─── Global state ──────────────────────────────────────────────
/** @tag NAVIGATION SIDEBAR */
let currentSubject = "English";
/** @tag NAVIGATION SIDEBAR */
let currentTextbook = "";

const LESSON_REQUEST = new URLSearchParams(location.search).get("lesson") || "";
/** @tag NAVIGATION SIDEBAR */
let selectedLesson = LESSON_REQUEST || "";

/** @tag ENGLISH */
let items = [];
/** @tag NAVIGATION */
let stage = null;
/** @tag NAVIGATION */
let stageIndex = 0;
/** @tag FINAL_TEST */
let magicFailCount = 0;
/** @tag XP AWARD */
let starCount = 0;
/** @tag NAVIGATION */
let currentPhaseIndex = 0;
/** @tag NAVIGATION */
let unlockedPhaseIndex = 0;
/** @tag NAVIGATION */
let sessionActive = false;
/** @tag NAVIGATION */
let roadmapComplete = false;
/** @tag REVIEW */
let wrongMap = {};
/** @tag FINAL_TEST SENTENCE */
let ownSentencesByItemId = {};
/** @tag FINAL_TEST */
let examQueue = [];
/** @tag FINAL_TEST */
let examIndex = 0;
/** @tag MY_WORDS */
const wordVaultSet = new Set();
/** @tag SENTENCE */
let lastTypedSentence = "";

// ─── Stage state objects (owned here; modules reference these) ─
/**
 * Preview stage done-map: item.id → "ok" | "miss"
 * @tag PREVIEW
 */
const previewDoneMap = new Map();

/**
 * Fill-the-Blank stage state.
 * @tag FILL_BLANK
 */
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

/**
 * Word-Match stage state.
 * @tag WORD_MATCH
 */
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

/**
 * Spelling Master stage state.
 * @tag SPELLING
 */
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

/**
 * Sentence Maker stage state.
 * @tag SENTENCE
 */
const smState = {
    initialized: false,
    attempt: {},
    reset() {
        this.initialized = false;
        this.attempt = {};
    }
};

// ─── Utility helpers ──────────────────────────────────────────
/**
 * getElementById shorthand.
 * @tag SYSTEM
 */
function $(id) {
    return document.getElementById(id);
}

/**
 * fetch + res.ok check + res.json() as one atomic op.
 * Throws Error(`METHOD URL → STATUS STATUSTEXT: <body preview>`) on non-2xx.
 * Callers can no longer forget the status check — that is the point.
 * @tag SYSTEM @tag API
 */
async function apiFetchJSON(url, opts) {
    const res = await fetch(url, opts);
    if (!res.ok) {
        let detail = "";
        try { detail = (await res.text()).slice(0, 200); } catch (_) {}
        const method = (opts && opts.method) || "GET";
        throw new Error(`${method} ${url} → ${res.status} ${res.statusText}${detail ? ": " + detail : ""}`);
    }
    return res.json();
}
window.apiFetchJSON = apiFetchJSON;

/**
 * Escape HTML special characters.
 * @tag SYSTEM
 */
function escapeHtml(s) {
    return String(s)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;");
}

/**
 * Escape a string for use in a RegExp.
 * @tag SYSTEM
 */
function escapeRe(s) {
    return String(s).replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

/**
 * Fisher-Yates shuffle — returns a new array.
 * @tag SYSTEM
 */
function shuffle(arr) {
    const a = arr.slice();
    for (let i = a.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [a[i], a[j]] = [a[j], a[i]];
    }
    return a;
}

/**
 * Safely parse item.extra_data JSON.
 * @tag ENGLISH
 */
function parseItemExtra(item) {
    try {
        return JSON.parse(item.extra_data || "{}");
    } catch (err) {
        console.warn('[parseItemExtra] Failed to parse extra_data:', err.message || err);
        return {};
    }
}

/**
 * Return image URL from item extra data, or "".
 * @tag ENGLISH
 */
function itemImageUrl(item) {
    const ex = parseItemExtra(item);
    const u = ex.image || ex.image_url || ex.url || "";
    return typeof u === "string" ? u.trim() : "";
}

/**
 * Total word count for the current lesson.
 * @tag ENGLISH NAVIGATION
 */
function wordCountAll() {
    return items.length || 0;
}

/**
 * Increment wrong-answer counter and track the attempt.
 * @tag REVIEW ACTIVE_RECALL
 */
function bumpWrong(item) {
    wrongMap[item.id] = (wrongMap[item.id] || 0) + 1;
    _trackWordAttempt(item, false, "");
}

/**
 * Set the hidden child-status element text.
 * @tag SYSTEM
 */
function setStatus(text) {
    const el = $("child-status");
    if (el) el.textContent = text;
}

/**
 * Update the star-count display element.
 * @tag XP AWARD
 */
function updateStars() {
    const el = $("star-count");
    if (!el) return;
    el.textContent = String(starCount);
}

/**
 * Return the human-readable title for the current stage.
 * @tag NAVIGATION
 */
function stageTitle() {
    if (stage === STAGE.PREVIEW) return "Step 1 — Preview";
    if (stage === STAGE.A)       return "Step 2 — Word Match";
    if (stage === STAGE.B)       return "Step 3 — Fill the Blank";
    if (stage === STAGE.C)       return "Step 4 — Spelling Master";
    if (stage === STAGE.D)       return "Step 5 — Make a Sentence";
    if (stage === STAGE.EXAM)    return "Step 6 — Final Test";
    return "Learning";
}

/**
 * Return the currently-active study item.
 * @tag ENGLISH
 */
function currentItem() {
    if (!items.length) return null;
    return items[stageIndex];
}

/**
 * Return the selected lesson name.
 * @tag NAVIGATION
 */
function lessonSelected() {
    return selectedLesson;
}

// ─── Stage-completion storage ─────────────────────────────────
/**
 * localStorage key for completed-stages set (per subject/textbook/lesson).
 * @tag SYSTEM NAVIGATION
 */
function stageStorageKey() {
    return `nss_done_${currentSubject}_${currentTextbook}_${selectedLesson}`;
}

/**
 * Read completed stages Set from localStorage.
 * @tag NAVIGATION
 */
function getCompletedStages() {
    try { return new Set(JSON.parse(localStorage.getItem(stageStorageKey()) || "[]")); }
    catch (err) { console.warn('[getCompletedStages] localStorage read failed:', err.message || err); return new Set(); }
}

/**
 * Mark a stage as complete in localStorage and notify SM2 module.
 * @tag NAVIGATION SM2
 */
function markStageComplete(stageKey) {
    if (!stageKey) return;
    const done = getCompletedStages();
    done.add(stageKey);
    localStorage.setItem(stageStorageKey(), JSON.stringify([...done]));
    if (window.ReviewModule && typeof window.ReviewModule.registerLesson === "function") {
        try { window.ReviewModule.registerLesson(currentSubject, currentTextbook, selectedLesson); } catch(e) { console.warn("[SM2] registerLesson error:", e); }
    }
}

/**
 * Return true when every roadmap stage has been completed.
 * @tag NAVIGATION
 */
function allStagesDone() {
    const done = getCompletedStages();
    return ROADMAP_STAGES.every((s) => done.has(s));
}

/**
 * Return the next roadmap stage that hasn't been completed yet.
 * @tag NAVIGATION
 */
function nextStageToStart() {
    const done = getCompletedStages();
    if (!done.has(STAGE.PREVIEW)) return STAGE.PREVIEW;
    return ROADMAP_STAGES.find((s) => !done.has(s)) || STAGE.PREVIEW;
}

/**
 * Return true if a stage is unlocked for the student.
 * Preview is always unlocked; Steps 2–5 unlock after Preview is complete.
 * @tag NAVIGATION
 */
function isStageUnlocked(key) {
    if (key === STAGE.PREVIEW) return true;
    const done = getCompletedStages();
    return done.has(STAGE.PREVIEW);
}

/**
 * Reset all per-stage state objects and counters.
 * @tag NAVIGATION SYSTEM
 */
function resetAllStageState() {
    clearWmScrollHandler();
    wmState.reset();
    fbState.reset();
    spState.reset();
    smState.reset();
    stageIndex = 0;
    wrongMap = {};
}

/**
 * Check whether a lesson is fully complete (all 5 stages done).
 * @tag NAVIGATION
 */
function isLessonComplete(subject, textbook, lesson) {
    try {
        const key  = `nss_done_${subject}_${textbook}_${lesson}`;
        const done = new Set(JSON.parse(localStorage.getItem(key) || "[]"));
        return ROADMAP_STAGES.every(s => done.has(s));
    } catch (err) { console.warn('[isLessonComplete] localStorage read failed:', err.message || err); return false; }
}

/**
 * Re-render lesson dropdown option text to show ✓ for completed lessons.
 * @tag NAVIGATION SIDEBAR
 */
function refreshLessonCompletion() {
    const sel = $("lesson-select");
    if (!sel) return;
    Array.from(sel.options).forEach(opt => {
        if (!opt.value) return;
        const done = isLessonComplete(currentSubject, currentTextbook, opt.value);
        opt.textContent = (done ? "✓ " : "") + opt.value + (opt.dataset.ready === "false" ? " ·" : "");
    });
}

/**
 * Set the lesson select value and sync display.
 * @tag NAVIGATION SIDEBAR
 */
function setActiveLessonTab(lessonName) {
    selectedLesson = lessonName;
    const sel = $("lesson-select");
    if (sel) sel.value = lessonName;
}

// ─── Inline progress helpers ──────────────────────────────────
/**
 * Fractional progress within the current stage (0–1).
 * @tag NAVIGATION
 */
function intraPhaseProgress() {
    const n = Math.max(1, wordCountAll());
    if (stage === STAGE.PREVIEW) {
        return (previewDoneMap ? previewDoneMap.size : 0) / n;
    }
    if (stage === STAGE.C) {
        const pass = spState.pass || 1;
        return (stageIndex + (pass - 1) / 3) / n;
    }
    return stageIndex / n;
}

/**
 * Update the top-bar progress percentage and challenge-meta labels.
 * @tag NAVIGATION XP
 */
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
        if (pct < 30)       fill.style.stroke = "";
        else if (pct < 70)  fill.style.stroke = "#22c55e";
        else                fill.style.stroke = "#f59e0b";
    }

    if (stage === STAGE.EXAM) {
        const den = Math.max(1, examQueue.length);
        const pct = Math.round((examIndex / den) * 100);
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
        setMeta("All done!");
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
        const prevDone = previewDoneMap ? previewDoneMap.size : 0;
        metaText = `${prevDone}/${n} words`;
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

/**
 * Stub — challenge-meta is managed by updateProgressPct().
 * @tag NAVIGATION
 */
function updateChallengeMeta() {}

// ─── Audio FX ─────────────────────────────────────────────────
/**
 * Play a short synthesised tone via Web Audio API.
 * @tag SYSTEM
 */
function _playTone(freq, dur, type) {
    // legacy shim — kept for backward compat; new code uses SoundFX directly
    if (window.SoundFX) return;
    try {
        const ctx = new (window.AudioContext || window.webkitAudioContext)();
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.type = type || "sine";
        osc.frequency.value = freq;
        gain.gain.value = 0.18;
        osc.connect(gain);
        gain.connect(ctx.destination);
        osc.start();
        gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + dur);
        osc.stop(ctx.currentTime + dur);
    } catch(e) {}
}

/**
 * Flash the stage element green and play a correct-answer tone.
 * @tag SYSTEM
 */
function stageFxCorrect() {
    const s = $("stage");
    if (!s) return;
    s.classList.remove("fx-wrong");
    s.classList.add("fx-correct");
    setTimeout(() => s.classList.remove("fx-correct"), 650);
    if (window.SoundFX) { SoundFX.correct(); } else {
        _playTone(523, 0.12, "sine");
        setTimeout(() => _playTone(784, 0.18, "sine"), 120);
    }
}

/**
 * Flash the stage element red, play a wrong-answer tone, and vibrate.
 * @tag SYSTEM
 */
function stageFxWrong() {
    const s = $("stage");
    if (!s) return;
    s.classList.remove("fx-correct");
    s.classList.remove("fx-wrong");
    void s.offsetWidth;
    s.classList.add("fx-wrong");
    setTimeout(() => s.classList.remove("fx-wrong"), 350);
    if (window.SoundFX) { SoundFX.wrong(); } else {
        _playTone(200, 0.25, "square");
    }
    if (navigator.vibrate) navigator.vibrate(150);
}

// ─── Particle system ──────────────────────────────────────────
/** @tag SYSTEM */
const _particleTimers = [];

/**
 * Show the "Perfect!" banner briefly.
 * @tag SYSTEM XP
 */
function showPerfectBanner(text) {
    const el = $("perfect-banner");
    if (!el) return;
    el.style.display = "";
    el.textContent = text;
    el.classList.remove("fire");
    void el.offsetWidth;
    el.classList.add("fire");
    setTimeout(() => { el.style.display = "none"; }, 3000);
}

/**
 * Spawn a particle burst at the centre of the particle layer.
 * @tag SYSTEM XP
 */
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

window.addEventListener("pagehide", () => {
    _particleTimers.forEach(clearTimeout);
    _particleTimers.length = 0;
    const layer = $("particle-layer");
    if (layer) layer.innerHTML = "";
});

// ─── Word vault ───────────────────────────────────────────────
/**
 * Render the word-vault chip list.
 * @tag MY_WORDS DAILY_WORDS
 */
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

/**
 * Add a word to the vault and re-render.
 * @tag MY_WORDS DAILY_WORDS
 */
function addWordVault(word) {
    const w = String(word || "").trim();
    if (!w) return;
    wordVaultSet.add(w);
    renderWordVault();
}

// ─── Stage-card visibility ────────────────────────────────────
/**
 * Show the idle card, hide the stage card.
 * @tag NAVIGATION
 */
function showIdleCard() {
    const iw = $("idle-wrapper");
    const sc = $("stage-card");
    if (iw) iw.classList.remove("hidden");
    if (sc) sc.classList.add("hidden");
}

/**
 * Show the stage card, hide the idle card.
 * @tag NAVIGATION
 */
function showStageCard() {
    const iw = $("idle-wrapper");
    const sc = $("stage-card");
    if (iw) iw.classList.add("hidden");
    if (sc) {
        sc.classList.remove("hidden");
        sc.style.display = "";
        sc.classList.remove("fx-swoosh");
        if (!sc.querySelector("#stage")) {
            sc.innerHTML = '<div id="stage"></div>';
        }
    }
}

/**
 * Animate the stage card out with a swoosh, then call onDone.
 * @tag NAVIGATION SYSTEM
 */
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

// ─── Magic-overlay ────────────────────────────────────────────
/**
 * Show the "challenge reset" magic overlay briefly (auto-hides).
 * @tag FINAL_TEST
 */
function showMagicOverlayBrief(resetCount) {
    const o = $("magic-overlay");
    const c = $("magic-count");
    if (c) c.textContent = String(resetCount);
    if (o) {
        o.classList.remove("hidden");
        setTimeout(() => o.classList.add("hidden"), 2500);
    }
}

/**
 * Show the magic overlay (stays visible until hidden).
 * @tag FINAL_TEST
 */
function showMagicOverlay() {
    const o = $("magic-overlay");
    const c = $("magic-count");
    if (c) c.textContent = String(magicFailCount);
    if (o) o.classList.remove("hidden");
}

/**
 * Hide the magic overlay.
 * @tag FINAL_TEST
 */
function hideMagicOverlay() {
    const o = $("magic-overlay");
    if (o) o.classList.add("hidden");
}

// ─── Sentence utilities ───────────────────────────────────────
/**
 * Replace all occurrences of word in sentence with "________".
 * @tag FILL_BLANK FINAL_TEST
 */
function replaceWordWithBlank(sentence, word) {
    const re = new RegExp(escapeRe(word), "gi");
    return String(sentence).replace(re, "________");
}

/**
 * Return true if sentence contains word (whole-word match for Latin words).
 * @tag SENTENCE FILL_BLANK
 */
function sentenceHasWord(sentence, word) {
    const w = String(word).trim();
    if (!w) return false;
    if (/^[a-zA-Z-']+$/.test(w)) {
        return new RegExp(`\\b${escapeRe(w)}\\b`, "i").test(sentence);
    }
    return sentence.toLowerCase().includes(w.toLowerCase());
}
