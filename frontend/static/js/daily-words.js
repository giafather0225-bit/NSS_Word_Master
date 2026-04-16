/* ================================================================
   daily-words.js — Daily Words state, view, placement test, daily study
   Section: English / Daily Words
   Dependencies: core.js, analytics.js
   API endpoints: /api/daily-words/status, /api/daily-words/today,
                  /api/daily-words/day1-result, /api/daily-words/complete
   ================================================================ */

// ─── Module State ─────────────────────────────────────────────
/**
 * Shared state for the current Daily Words session.
 * @tag DAILY_WORDS
 */
const dwState = {
    words: [],            // word objects for current session
    currentIndex: 0,      // position within words[]
    correctCount: 0,      // correct answers this session
    wrongWords: [],       // words answered incorrectly
    cycleDay: 1,          // 1–7
    grade: "grade_3",
    alreadyDoneToday: false,
    sessionType: "study", // "placement" | "study" | "weekly"
};

// ─── View Entry / Exit ────────────────────────────────────────
/** Show Daily Words view. @tag DAILY_WORDS NAVIGATION */
async function showDailyWordsView() {
    const view = document.getElementById("daily-words-view");
    if (!view) return;
    view.classList.add("active");
    const sa = document.getElementById("stage-area");
    if (sa) sa.style.display = "none";
    await _dwLoadAndRender();
}

/** Hide Daily Words view and restore stage area. @tag DAILY_WORDS NAVIGATION */
function hideDailyWordsView() {
    const view = document.getElementById("daily-words-view");
    if (view) view.classList.remove("active");
    const sa = document.getElementById("stage-area");
    if (sa) sa.style.display = "";
}

// ─── Load & Render ────────────────────────────────────────────

/**
 * Fetch today's session data and render the appropriate screen.
 * @tag DAILY_WORDS
 */
async function _dwLoadAndRender() {
    const view = document.getElementById("daily-words-view");
    if (!view) return;
    view.innerHTML = `${_dwHeader("Daily Words", "")}<p style="color:var(--text-secondary);margin-top:40px;">Loading…</p>`;

    try {
        const res = await fetch("/api/daily-words/today");
        if (!res.ok) throw new Error("API " + res.status);
        const data = await res.json();

        dwState.words           = data.words || [];
        dwState.cycleDay        = data.cycle_day || 1;
        dwState.grade           = data.grade || "grade_3";
        dwState.alreadyDoneToday = data.already_done_today || false;
        dwState.currentIndex    = 0;
        dwState.correctCount    = 0;
        dwState.wrongWords      = [];

        if (dwState.alreadyDoneToday && dwState.cycleDay !== 7) {
            _dwRenderAlreadyDone(); return;
        }
        if (dwState.cycleDay === 1) { dwState.sessionType = "placement"; _dwRenderPlacementIntro(); }
        else if (dwState.cycleDay === 7) { dwState.sessionType = "weekly"; dwRenderWeeklyIntro(); }
        else { dwState.sessionType = "study"; _dwRenderStudyCard(); }
    } catch (_) {
        const view2 = document.getElementById("daily-words-view");
        if (view2) view2.innerHTML = `${_dwHeader("Daily Words", "")}
          <p style="color:var(--color-error);margin-top:40px;">Failed to load. Please try again.</p>`;
    }
}

// ─── Shared UI builders ───────────────────────────────────────

/** Build the HTML header bar with a back button. @tag DAILY_WORDS */
function _dwHeader(title, sub) {
    return `<div class="dw-header">
        <button class="dw-header-back" onclick="hideDailyWordsView()">←</button>
        <span class="dw-header-title">${escapeHtml(title)}</span>
        <span class="dw-header-sub">${escapeHtml(sub)}</span>
    </div>`;
}

/** Build a progress bar at fraction 0–1. @tag DAILY_WORDS */
function _dwProgressBar(fraction) {
    const pct = Math.round(Math.min(1, Math.max(0, fraction)) * 100);
    return `<div class="dw-progress-bar"><div class="dw-progress-fill" style="width:${pct}%"></div></div>`;
}

/** Format grade key as label e.g. "grade_5" → "Grade 5". @tag DAILY_WORDS */
function _dwGradeLabel(grade) {
    return (grade || "grade_3").replace("_", " ").replace(/\b\w/g, c => c.toUpperCase());
}

// ─── Already done screen ──────────────────────────────────────

/**
 * Render "already completed today" screen.
 * @tag DAILY_WORDS
 */
function _dwRenderAlreadyDone() {
    const view = document.getElementById("daily-words-view");
    view.innerHTML = `
        ${_dwHeader("Daily Words", _dwGradeLabel(dwState.grade))}
        <div class="dw-result">
            <div class="dw-result-emoji">✅</div>
            <div class="dw-result-title">Done for today!</div>
            <div class="dw-result-sub">Day ${dwState.cycleDay} complete. Come back tomorrow.</div>
            <div class="dw-btn-row">
                <button class="dw-btn dw-btn-secondary" onclick="hideDailyWordsView()">← Back</button>
            </div>
        </div>`;
}

// ─── Placement Test (Day 1) ───────────────────────────────────

/**
 * Render the Day 1 placement test introduction screen.
 * @tag DAILY_WORDS
 */
function _dwRenderPlacementIntro() {
    const view = document.getElementById("daily-words-view");
    view.innerHTML = `
        ${_dwHeader("Daily Words", _dwGradeLabel(dwState.grade))}
        <div class="dw-placement-intro">
            <h2>📋 Placement Test</h2>
            <p>${dwState.words.length} words. Choose the correct meaning for each.<br>
               Words you miss become your <strong>study list</strong> for this week.</p>
            <div class="dw-btn-row">
                <button class="dw-btn dw-btn-primary" onclick="_dwPlacementNext()">Start →</button>
            </div>
        </div>`;
}

/**
 * Render the next placement test MC question.
 * @tag DAILY_WORDS
 */
function _dwPlacementNext() {
    if (dwState.currentIndex >= dwState.words.length) { _dwFinishPlacement(); return; }
    const item = dwState.words[dwState.currentIndex];
    const fraction = dwState.currentIndex / dwState.words.length;
    const allDefs = dwState.words.map(w => w.definition);
    const choices = [item.definition,
        ...allDefs.filter(d => d !== item.definition).sort(() => Math.random() - 0.5).slice(0, 3)
    ].sort(() => Math.random() - 0.5);

    const view = document.getElementById("daily-words-view");
    view.innerHTML = `
        ${_dwHeader("Placement Test", `${dwState.currentIndex + 1} / ${dwState.words.length}`)}
        ${_dwProgressBar(fraction)}
        <div class="dw-card">
            <div class="dw-question-word">${escapeHtml(item.word)}</div>
            <div class="dw-choices">${choices.map(def =>
                `<button class="dw-choice-btn" onclick="_dwPlacementAnswer(this,${def === item.definition},${JSON.stringify(item.word)})">${escapeHtml(def)}</button>`
            ).join("")}</div>
        </div>`;
}

/**
 * Handle a placement test MC answer click.
 * @tag DAILY_WORDS
 */
function _dwPlacementAnswer(btn, isCorrect, word) {
    btn.closest(".dw-choices").querySelectorAll(".dw-choice-btn").forEach(b => {
        b.onclick = null; b.style.pointerEvents = "none";
    });
    btn.classList.add(isCorrect ? "correct" : "wrong");
    if (isCorrect) { dwState.correctCount++; }
    else { dwState.wrongWords.push(word); }
    setTimeout(() => { dwState.currentIndex++; _dwPlacementNext(); }, isCorrect ? 400 : 900);
}

/**
 * POST Day 1 failures and show the placement result screen.
 * @tag DAILY_WORDS
 */
async function _dwFinishPlacement() {
    try {
        await fetch("/api/daily-words/day1-result", {
            method: "POST", headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ failed_words: dwState.wrongWords })
        });
    } catch (_) {}
    const wrong = dwState.wrongWords.length;
    const total = dwState.words.length;
    const pct = Math.round(((total - wrong) / total) * 100);
    const view = document.getElementById("daily-words-view");
    view.innerHTML = `
        ${_dwHeader("Daily Words", "Day 1 Done")}
        <div class="dw-result">
            <div class="dw-result-emoji">${pct >= 90 ? "🌟" : pct >= 70 ? "👍" : "📚"}</div>
            <div class="dw-result-title">Placement Done!</div>
            <div class="dw-result-sub">${wrong > 0 ? `${wrong} words in your study list this week.` : "Perfect! All words known."}</div>
            <div class="dw-result-stats">
                <div class="dw-stat"><span class="dw-stat-num">${total - wrong}</span><span class="dw-stat-label">Correct</span></div>
                <div class="dw-stat"><span class="dw-stat-num">${wrong}</span><span class="dw-stat-label">To Study</span></div>
                <div class="dw-stat"><span class="dw-stat-num">${pct}%</span><span class="dw-stat-label">Score</span></div>
            </div>
            <div class="dw-btn-row"><button class="dw-btn dw-btn-secondary" onclick="hideDailyWordsView()">← Back</button></div>
        </div>`;
    loadDailyWordsSection();
}

// ─── Daily Study (Days 2–6) ───────────────────────────────────

/**
 * Render the current flashcard for daily study.
 * @tag DAILY_WORDS
 */
function _dwRenderStudyCard() {
    if (dwState.currentIndex >= dwState.words.length) { _dwFinishStudy(); return; }
    const item = dwState.words[dwState.currentIndex];
    const view = document.getElementById("daily-words-view");
    view.innerHTML = `
        ${_dwHeader(`Day ${dwState.cycleDay}`, `${dwState.currentIndex + 1} / ${dwState.words.length}`)}
        ${_dwProgressBar(dwState.currentIndex / dwState.words.length)}
        <div class="dw-card">
            <div class="dw-card-word">${escapeHtml(item.word)}</div>
            <div class="dw-card-definition">${escapeHtml(item.definition)}</div>
            ${item.example ? `<div class="dw-card-example">${escapeHtml(item.example)}</div>` : ""}
        </div>
        <div class="dw-btn-row">
            <button class="dw-btn dw-btn-primary" onclick="_dwStudyNext()">Next →</button>
        </div>`;
}

/**
 * Advance to next study card.
 * @tag DAILY_WORDS
 */
function _dwStudyNext() {
    dwState.currentIndex++;
    dwState.correctCount++;
    _dwRenderStudyCard();
}

/**
 * Complete daily study: POST to /api/daily-words/complete and show result.
 * @tag DAILY_WORDS XP
 */
async function _dwFinishStudy() {
    let xpAwarded = 0;
    try {
        const res = await fetch("/api/daily-words/complete", {
            method: "POST", headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ learned_count: dwState.words.length })
        });
        if (res.ok) { const d = await res.json(); xpAwarded = d.xp_awarded || 0; }
    } catch (_) {}
    const view = document.getElementById("daily-words-view");
    view.innerHTML = `
        ${_dwHeader("Daily Words", `Day ${dwState.cycleDay} Done`)}
        <div class="dw-result">
            <div class="dw-result-emoji">🎉</div>
            <div class="dw-result-title">Day ${dwState.cycleDay} Complete!</div>
            <div class="dw-result-sub">${dwState.words.length} words studied today.</div>
            ${xpAwarded > 0 ? `<div style="font-size:18px;font-weight:700;color:var(--color-primary);margin-bottom:16px;">+${xpAwarded} XP</div>` : ""}
            <div class="dw-btn-row"><button class="dw-btn dw-btn-secondary" onclick="hideDailyWordsView()">← Back</button></div>
        </div>`;
    loadDailyWordsSection();
}

// ─── Sidebar update ───────────────────────────────────────────

/**
 * Fetch /api/daily-words/status and update sidebar accordion labels.
 * @tag DAILY_WORDS SIDEBAR
 */
async function loadDailyWordsSection() {
    try {
        const res = await fetch("/api/daily-words/status");
        if (!res.ok) return;
        const d = await res.json();
        const el = id => document.getElementById(id);
        if (el("dw-grade-label"))    el("dw-grade-label").textContent    = d.grade_label || "Grade 3";
        if (el("dw-week-progress"))  el("dw-week-progress").textContent  = `This Week: ${d.week_done}/${d.week_total} days`;
        if (el("dw-today-progress")) el("dw-today-progress").textContent = `Today: ${d.today_done}/${d.today_total} words`;
        const btn = el("dw-start-btn");
        if (btn) {
            const span = btn.querySelector(".sb-card-label");
            const done = d.already_done_today && d.cycle_day !== 7;
            if (span) span.textContent = done ? "✅ Done"
                : d.cycle_day === 1 ? "Placement Test →"
                : d.cycle_day === 7 ? "Weekly Test →"
                : `Day ${d.cycle_day} →`;
            btn.disabled = done;
        }
    } catch (_) {}
}
