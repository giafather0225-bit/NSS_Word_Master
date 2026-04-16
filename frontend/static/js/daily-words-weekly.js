/* ================================================================
   daily-words-weekly.js — Daily Words weekly test (Day 7)
   Section: English / Daily Words
   Dependencies: daily-words.js (dwState, _dwHeader, _dwProgressBar,
                 _dwGradeLabel, loadDailyWordsSection), core.js
   API endpoints: /api/daily-words/weekly-test/result
   ================================================================ */

// ─── Weekly Test Intro ────────────────────────────────────────

/**
 * Render the weekly test introduction screen.
 * @tag DAILY_WORDS
 */
function dwRenderWeeklyIntro() {
    const view = document.getElementById("daily-words-view");
    if (!view) return;
    view.innerHTML = `
        ${_dwHeader("Weekly Test", _dwGradeLabel(dwState.grade))}
        <div class="dw-placement-intro">
            <h2>📝 Weekly Test</h2>
            <p>Type the correct word for each definition.<br>
               You need <strong>90%</strong> to pass and earn +10 XP.</p>
            <p style="font-size:13px;">${dwState.words.length} words • Type to answer</p>
            <div class="dw-btn-row">
                <button class="dw-btn dw-btn-primary" onclick="dwWeeklyNext()">Start →</button>
            </div>
        </div>`;
}

// ─── Weekly Test Question ─────────────────────────────────────

/**
 * Render the next weekly test question (type the word from the definition).
 * @tag DAILY_WORDS
 */
function dwWeeklyNext() {
    if (dwState.currentIndex >= dwState.words.length) { _dwFinishWeekly(); return; }
    const item = dwState.words[dwState.currentIndex];
    const fraction = dwState.currentIndex / dwState.words.length;
    const view = document.getElementById("daily-words-view");
    view.innerHTML = `
        ${_dwHeader("Weekly Test", `${dwState.currentIndex + 1} / ${dwState.words.length}`)}
        ${_dwProgressBar(fraction)}
        <div class="dw-test-card">
            <div class="dw-test-definition">${escapeHtml(item.definition)}</div>
            ${item.example ? `<div class="dw-test-example">"${escapeHtml(item.example)}"</div>` : ""}
            <input id="dw-test-input" class="dw-test-input" type="text"
                   placeholder="type the word…" autocomplete="off" autocorrect="off"
                   autocapitalize="off" spellcheck="false" />
        </div>
        <div class="dw-btn-row">
            <button class="dw-btn dw-btn-primary" onclick="dwWeeklySubmit()">Submit</button>
        </div>`;
    const inp = document.getElementById("dw-test-input");
    if (inp) {
        inp.focus();
        inp.addEventListener("keydown", e => { if (e.key === "Enter") dwWeeklySubmit(); });
    }
}

// ─── Weekly Test Answer ───────────────────────────────────────

/**
 * Handle weekly test answer submission.
 * @tag DAILY_WORDS
 */
function dwWeeklySubmit() {
    const item = dwState.words[dwState.currentIndex];
    const inp = document.getElementById("dw-test-input");
    if (!inp) return;
    const userAnswer = inp.value.trim().toLowerCase();
    const correct    = item.word.toLowerCase();
    const isCorrect  = userAnswer === correct;

    inp.classList.add(isCorrect ? "correct" : "wrong");
    inp.disabled = true;

    if (isCorrect) {
        dwState.correctCount++;
    } else {
        inp.value = item.word;
        inp.style.color = "var(--color-error)";
        dwState.wrongWords.push(item.word);
    }

    setTimeout(() => { dwState.currentIndex++; dwWeeklyNext(); }, isCorrect ? 400 : 1100);
}

// ─── Weekly Test Finish ───────────────────────────────────────

/**
 * POST weekly test result and show the summary screen.
 * @tag DAILY_WORDS XP
 */
async function _dwFinishWeekly() {
    const total    = dwState.words.length;
    const correct  = dwState.correctCount;
    const accuracy = total > 0 ? correct / total : 0;
    const passed   = accuracy >= 0.9;
    let xpAwarded  = 0;
    let newGrade   = dwState.grade;

    try {
        const res = await fetch("/api/daily-words/weekly-test/result", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ correct_count: correct, total_count: total, advance_grade: false })
        });
        if (res.ok) {
            const d = await res.json();
            xpAwarded = d.xp_awarded || 0;
            newGrade  = d.new_grade  || dwState.grade;
        }
    } catch (_) {}

    _dwRenderWeeklyResult(correct, total, passed, xpAwarded, newGrade);
    loadDailyWordsSection();
}

/**
 * Render the weekly test result summary screen.
 * @tag DAILY_WORDS
 */
function _dwRenderWeeklyResult(correct, total, passed, xpAwarded, newGrade) {
    const view  = document.getElementById("daily-words-view");
    const pct   = Math.round((correct / Math.max(total, 1)) * 100);
    const glabel = _dwGradeLabel(newGrade);
    view.innerHTML = `
        ${_dwHeader("Weekly Test", "Result")}
        <div class="dw-result">
            <div class="dw-result-emoji">${passed ? "🏆" : "📚"}</div>
            <div class="dw-result-title">${passed ? "Test Passed!" : "Keep Practicing"}</div>
            <div class="dw-result-sub">${passed
                ? `New cycle starts with ${glabel}.`
                : `Score ${pct}% — need 90% to pass. New cycle begins now.`}</div>
            <div class="dw-result-stats">
                <div class="dw-stat"><span class="dw-stat-num">${correct}</span><span class="dw-stat-label">Correct</span></div>
                <div class="dw-stat"><span class="dw-stat-num">${total - correct}</span><span class="dw-stat-label">Wrong</span></div>
                <div class="dw-stat"><span class="dw-stat-num">${pct}%</span><span class="dw-stat-label">Score</span></div>
            </div>
            ${xpAwarded > 0 ? `<div style="font-size:18px;font-weight:700;color:var(--color-primary);margin-bottom:16px;">+${xpAwarded} XP</div>` : ""}
            <div class="dw-btn-row">
                <button class="dw-btn dw-btn-secondary" onclick="hideDailyWordsView()">← Back to Home</button>
            </div>
        </div>`;
}
