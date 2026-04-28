/* ================================================================
   child-exam.js — Final Test (Perfect Challenge) flow
   Section: English / Final Test
   Dependencies: core.js (state, helpers), child.js (renderStage,
                 renderIdleStage, updateRoadmapUI, enterSessionSidebar,
                 exitSessionSidebar, _trackStageComplete)
   API endpoints: /api/progress/sparta_reset,
                  /api/progress/challenge_complete,
                  /api/rewards/earn_all,
                  /api/tts
   ================================================================ */

// ─── Exam (Final Test) renderer ───────────────────────────────
/**
 * Render one exam question card.
 * @tag FINAL_TEST
 */
function renderExam(el) {
    const q = examQueue[examIndex];
    if (!q) return;
    const item     = q.item;
    const sentence = q.mode === EXAM_MODE.OWN_SENTENCE_BLANK ? q.sentence : item.hint;
    const blanked  = replaceWordWithBlank(sentence, item.answer);
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

    $("answer-input").addEventListener("keydown", (e) => {
        if (e.key === "Enter") $("exam-submit").click();
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
            })
                .then(r => r.ok ? r.blob() : null)
                .then(blob => {
                    if (!blob || blob.size === 0) return;
                    const url = URL.createObjectURL(blob);
                    const audio = new Audio(url);
                    audio.onended = () => URL.revokeObjectURL(url);
                    audio.onerror = () => URL.revokeObjectURL(url);
                    audio.play().catch(() => URL.revokeObjectURL(url));
                })
                .catch(() => {});
            inp.value = "";
            setTimeout(async () => {
                hideMagicOverlay();
                await startPerfectChallenge();
            }, 2000);
        }
    });
}

// ─── Challenge flow ───────────────────────────────────────────
/**
 * Reset sparta progress on the backend.
 * @tag FINAL_TEST
 */
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

/**
 * Start (or restart) the Perfect Challenge exam.
 * @tag FINAL_TEST
 */
async function startPerfectChallenge() {
    ownSentencesByItemId = await loadOwnSentences(lessonSelected());
    examQueue   = buildExamQueue();
    examIndex   = 0;
    stage       = STAGE.EXAM;
    sessionActive = true;
    magicFailCount = 0;
    renderStage();
    enterSessionSidebar();
    setStatus("Perfect challenge — good luck!");
}

/**
 * Handle exam completion: POST results, show final screen, burst particles.
 * @tag FINAL_TEST AWARD
 */
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

    stage = null;
    sessionActive = false;
    exitSessionSidebar();
    const sidebar = document.getElementById('sidebar');
    if (sidebar) sidebar.classList.remove('collapsed');
    localStorage.setItem('sb_collapsed', '0');
    updateRoadmapUI();

    const stageEl  = $("stage");
    const perfect  = magicFailCount === 0;
    if (stageEl) {
        const bgStyle = perfect ? "exam-result--perfect" : "exam-result--done";
        const bodyLines = perfect
            ? `<div class="exam-result-trophy">🏆</div>
               <div class="exam-result-title exam-result-title--perfect">PERFECT!</div>
               <div class="exam-result-sub exam-result-sub--perfect">No mistakes — incredible!</div>`
            : `<div class="exam-result-check"><span class="check-dot check-dot--lg"></span></div>
               <div class="exam-result-title">Final Test Done!</div>
               <div class="exam-result-sub">Finished with ${magicFailCount} reset(s).</div>
               <div class="exam-result-hint">Keep practicing!</div>`;
        stageEl.innerHTML = `
            <div class="exam-result-wrap ${bgStyle}">
                ${bodyLines}
                <div style="margin-top:28px;display:flex;gap:12px;flex-wrap:wrap;justify-content:center;">
                    <button type="button" class="exam-retry-btn" id="exam-retry-btn">
                        Take Final Test Again
                    </button>
                    <button type="button" class="exam-menu-btn" id="exam-menu-btn">
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
    showPerfectBanner(perfect ? "Perfect! 🏆" : "Final Test Done!");
    setStatus(perfect
        ? "🏆 Perfect score! Click \"Test\" to retake."
        : `Done! ${magicFailCount} reset(s). Click the Test button to retry.`
    );

    const ex = $("btn-exam");
    if (ex) ex.disabled = false;
}
