/* ================================================================
   child.js — App shell: stage dispatcher, navigation flow, exam runner,
              UI wiring, calendar, and DOMContentLoaded bootstrap.
   Section: English / System
   Dependencies: core.js, tts-client.js, analytics.js, navigation.js,
                 preview.js, wordmatch.js, fillblank.js, spelling.js,
                 sentence.js
   API endpoints: /api/progress/sparta_reset,
                  /api/progress/challenge_complete,
                  /api/rewards/earn_all
   ================================================================ */

/* eslint-disable no-use-before-define */

// ─── Developer debug tools ─────────────────────────────────────
/**
 * Browser-console dev helpers: DEV.go(N), DEV.skip(), etc.
 * @tag SYSTEM
 */
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
        stageIndex = Math.max(0, items.length - 1);
        renderStage();
        console.log("Jump to last word");
    }
};

// ─── Stage dispatcher ──────────────────────────────────────────
/**
 * Render the appropriate stage view based on the current `stage` value.
 * @tag NAVIGATION ENGLISH
 */
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

/**
 * Render the Hero card shown before a session starts.
 * Replaces the legacy idle+Start pattern — main CTA ("Jump back in")
 * plus per-stage chips let the user jump straight into any unlocked step.
 * @tag NAVIGATION
 */
function renderIdleStage() {
    const wrap = document.getElementById('idle-wrapper');
    if (!wrap) return;

    const lesson    = lessonSelected();
    const textbook  = (currentTextbook || '').replace(/_/g, ' ');

    if (!lesson) {
        wrap.innerHTML = `
            <div class="hero-card">
                <div class="hero-empty">
                    Pick a textbook and lesson on the left<br>to start learning.
                </div>
            </div>`;
        showIdleCard();
        refreshStartLabel();
        return;
    }

    const isDone    = allStagesDone();
    const doneSet   = getCompletedStages();
    const doneCount = ROADMAP_STAGES.filter(s => doneSet.has(s)).length;
    const total     = ROADMAP_STAGES.length;
    const pct       = Math.round((doneCount / total) * 100);
    const next      = isDone ? null : nextStageToStart();
    const nextLabel = next ? (ROADMAP_LABELS[ROADMAP_STAGES.indexOf(next)] || '') : '';

    let headline, ctaLabel, ctaTarget;
    if (isDone) {
        headline  = 'All done! 🎉';
        ctaLabel  = '📝 Take Final Test';
        ctaTarget = 'exam';
    } else if (doneCount > 0) {
        headline  = 'Keep going! 🔥';
        ctaLabel  = `▶ Continue · ${nextLabel}`;
        ctaTarget = next;
    } else {
        headline  = `Let's start Lesson ${lesson.replace(/^Lesson_?/, '')}!`;
        ctaLabel  = `▶ Begin · ${nextLabel}`;
        ctaTarget = next;
    }

    const chipsHtml = ROADMAP_STAGES.map((s, i) => {
        const label    = ROADMAP_LABELS[i] || '';
        const done     = doneSet.has(s);
        const isNext   = !done && s === next;
        const unlocked = done || isNext;
        const cls      = done ? 'done' : (isNext ? 'current' : 'locked');
        const icon     = done ? '✓' : (isNext ? '●' : '🔒');
        const attrs    = unlocked ? `data-stage="${s}"` : 'disabled';
        return `<button type="button" class="hero-chip ${cls}" ${attrs}>
            <span class="hero-chip-icon">${icon}</span>
            <span class="hero-chip-label">${escapeHtml(label)}</span>
        </button>`;
    }).join('');

    wrap.innerHTML = `
        <div class="hero-card">
            <div class="hero-eyebrow">${escapeHtml(textbook)} · ${escapeHtml(lesson.replace(/_/g, ' '))}</div>
            <h1 class="hero-title">${escapeHtml(headline)}</h1>
            <div class="hero-progress">
                <div class="hero-progress-bar"><div class="hero-progress-fill" style="width:${pct}%"></div></div>
                <div class="hero-progress-meta">${doneCount} / ${total} steps · ${pct}%</div>
            </div>
            <button type="button" class="hero-cta" id="hero-cta" data-target="${ctaTarget}">${escapeHtml(ctaLabel)}</button>
            <div class="hero-divider"><span>Or pick a step</span></div>
            <div class="hero-chips">${chipsHtml}</div>
        </div>`;

    const cta = document.getElementById('hero-cta');
    if (cta) cta.addEventListener('click', () => {
        const target = cta.dataset.target;
        if (target === 'exam') {
            const ex = document.getElementById('btn-exam');
            if (ex && !ex.disabled) ex.click();
        } else {
            startLessonAt(target);
        }
    });
    wrap.querySelectorAll('.hero-chip[data-stage]').forEach(chip => {
        chip.addEventListener('click', () => startLessonAt(chip.dataset.stage));
    });

    showIdleCard();
    refreshStartLabel();
}

/**
 * Render the "all steps complete" congratulations card.
 * @tag NAVIGATION
 */
function renderRoadmapComplete() {
    const stageEl = $("stage");
    if (!stageEl) return;
    stageEl.innerHTML = `
        <p class="st-h1">All steps complete!</p>
        <p class="st-sub">Amazing work! Press Start to repeat any step, or take the Final Test below.</p>
    `;
}

/**
 * Mark the current stage complete, show a stage-clear card,
 * and set up the "next stage" button.
 * @tag NAVIGATION
 */
function advanceToNextStage() {
    if (stage) _trackStageComplete(stage);
    if (stage) markStageComplete(stage);
    if (window.SoundFX) SoundFX.stageComplete();

    const _stageAtComplete      = stage;
    const completedStageLabel   = ROADMAP_LABELS[ROADMAP_STAGES.indexOf(_stageAtComplete)] || "Step";
    const reviewCount           = Object.keys(wrongMap).filter(k => wrongMap[k] > 0).length;
    const allDone               = allStagesDone();

    const stageEl = $("stage");
    if (stageEl) {
        const next      = allDone ? null : nextStageToStart();
        const nextLabel = next ? (ROADMAP_LABELS[ROADMAP_STAGES.indexOf(next)] || "Next") : null;
        const nextBtnHtml = allDone
            ? `<button type="button" id="stage-complete-btn" class="sc-btn sc-btn-primary">Take Final Test</button>`
            : `<button type="button" id="stage-complete-btn" class="sc-btn sc-btn-primary">${nextLabel} \u2192</button>`;

        const okItems   = items.filter(it => !wrongMap[it.id]);
        const missItems = items.filter(it => wrongMap[it.id] > 0);
        const totalCt   = items.length;
        const okCt      = okItems.length;
        const missCt    = missItems.length;

        const chipHtml = items.map(it => {
            const isMiss = wrongMap[it.id] > 0;
            const cls = isMiss ? 'sc-chip sc-chip-miss' : 'sc-chip sc-chip-ok';
            const mark = isMiss ? '~' : '\u2713';
            return `<span class="${cls}"><span class="sc-chip-mark">${mark}</span>${escapeHtml(it.answer)}</span>`;
        }).join('');

        const retryBtnHtml = missCt > 0 && !allDone
            ? `<button type="button" id="sc-retry-btn" class="sc-btn sc-btn-ghost">Review ${missCt} word${missCt > 1 ? 's' : ''}</button>`
            : '';

        stageEl.innerHTML = `
            <div class="sc-card">
                <div class="sc-hero">
                    <svg class="sc-svg" viewBox="0 0 52 52" aria-hidden="true">
                        <circle class="sc-circle" cx="26" cy="26" r="24"/>
                        <path class="sc-tick" d="M15 27l7 7 15-15"/>
                    </svg>
                    <p class="sc-eyebrow">Stage Complete</p>
                    <p class="sc-title">${completedStageLabel}</p>
                </div>
                <div class="sc-stats">
                    <div class="sc-stat"><span class="sc-stat-val">${okCt}</span><span class="sc-stat-lbl">Mastered</span></div>
                    <div class="sc-stat"><span class="sc-stat-val sc-stat-val-miss">${missCt}</span><span class="sc-stat-lbl">To Review</span></div>
                    <div class="sc-stat"><span class="sc-stat-val">${totalCt}</span><span class="sc-stat-lbl">Total</span></div>
                </div>
                <div class="sc-chips" aria-label="Words in this stage">${chipHtml}</div>
                <div class="sc-cta-row">
                    ${retryBtnHtml}
                    ${nextBtnHtml}
                </div>
            </div>
        `;

    }

    const _savedNextKey = allDone ? null : nextStageToStart();
    sessionActive = false;
    stageIndex    = 0;
    stage         = null;
    spState.pass  = 1;
    exitSessionSidebar();

    const completeBtn = stageEl ? stageEl.querySelector('#stage-complete-btn') : null;
    if (completeBtn) {
        completeBtn.addEventListener('click', async () => {
            if (allDone) {
                const examBtn = $('btn-exam');
                if (examBtn) examBtn.click();
            } else if (_savedNextKey) {
                if (!items.length) {
                    const lesson = lessonSelected();
                    if (lesson) await loadStudyItems(lesson);
                }
                jumpToStage(_savedNextKey);
            }
        });
    }
    const retryBtn = stageEl ? stageEl.querySelector('#sc-retry-btn') : null;
    if (retryBtn && _stageAtComplete) {
        retryBtn.addEventListener('click', async () => {
            if (!items.length) {
                const lesson = lessonSelected();
                if (lesson) await loadStudyItems(lesson);
            }
            jumpToStage(_stageAtComplete);
        });
    }

    updateRoadmapUI();
    refreshLessonCompletion();

    setTimeout(() => {
        if (allDone) {
            roadmapComplete = true;
            const ex = $("btn-exam");
            if (ex) ex.disabled = false;
            refreshStartLabel();
            setStatus("All steps complete! Press the button for Final Test.");
        } else {
            refreshStartLabel();
            const next = nextStageToStart();
            const nextLabel = ROADMAP_LABELS[ROADMAP_STAGES.indexOf(next)] || next;
            setStatus("Step done! Click the button or tap \"" + nextLabel + "\" above.");
        }
    }, CONF.STAGE_CLEAR_DELAY);
}

/**
 * Return true if the Final Test button is currently enabled.
 * @tag FINAL_TEST
 */
function canStartExamNow() {
    const ex = $("btn-exam");
    return ex && !ex.disabled;
}

/**
 * Build the exam question queue from wrong-answer history and own sentences.
 * @tag FINAL_TEST
 */
function buildExamQueue() {
    const wrongSorted = items.map((it) => ({ it, n: wrongMap[it.id] || 0 })).sort((a, b) => b.n - a.n);
    const topWrong = wrongSorted.filter((x) => x.n > 0).slice(0, CONF.EXAM_POOL_SIZE).map((x) => x.it);
    const pool = topWrong.length ? topWrong : shuffle(items).slice(0, Math.min(CONF.EXAM_POOL_SIZE, items.length));
    const queue = [];

    for (const it of pool) {
        const hasOwn = ownSentencesByItemId[it.id] && String(ownSentencesByItemId[it.id]).trim().length > 0;
        if (hasOwn && Math.random() < 0.5) {
            queue.push({ item: it, mode: EXAM_MODE.OWN_SENTENCE_BLANK, sentence: ownSentencesByItemId[it.id] });
        } else {
            queue.push({ item: it, mode: EXAM_MODE.EXAMPLE_BLANK });
        }
    }

    const finalQ = queue.length
        ? shuffle(queue)
        : shuffle(items).slice(0, CONF.EXAM_POOL_SIZE).map((it) => ({ item: it, mode: EXAM_MODE.EXAMPLE_BLANK }));
    return finalQ.slice(0, Math.min(CONF.EXAM_MAX_QUESTIONS, finalQ.length));
}

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

// ─── Tutor modal wiring ───────────────────────────────────────
/**
 * Wire the AI Tutor modal "Continue" button.
 * @tag AI SENTENCE
 */
function wireTutorModal() {
    const modal = $("tutor-modal");
    const next  = $("btn-tutor-next");
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

// ─── Start / Exam buttons ─────────────────────────────────────
/**
 * Begin (or resume) a lesson at the given stage key.
 * Shared by the Hero CTA and per-stage chips; no Start button required.
 * @tag NAVIGATION
 * @param {string} stageKey - One of ROADMAP_STAGES; falls back to nextStageToStart().
 */
async function startLessonAt(stageKey) {
    const targetStage = stageKey || nextStageToStart();
    const targetIdx   = ROADMAP_STAGES.indexOf(targetStage);
    if (targetIdx < 0) return;

    currentPhaseIndex  = targetIdx;
    unlockedPhaseIndex = Math.max(unlockedPhaseIndex, targetIdx);
    sessionActive      = true;
    roadmapComplete    = allStagesDone();
    stage              = targetStage;
    window.shadowContext = {
        lesson:   lessonSelected(),
        activity: ROADMAP_LABELS[ROADMAP_STAGES.indexOf(targetStage)] || targetStage,
    };
    resetAllStageState();
    magicFailCount = 0;
    examQueue      = [];
    examIndex      = 0;
    wordVaultSet.clear();
    renderWordVault();

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
        sessionActive   = false;
        roadmapComplete = false;
        stage           = null;
        renderIdleStage();
        setStatus("Error loading lesson.");
        if (console && console.error) console.error(e);
        updateRoadmapUI();
        updateProgressPct();
        updateChallengeMeta();
        return;
    }

    if (!items.length) {
        sessionActive = false;
        stage         = null;
        renderIdleStage();
        setStatus("No items.");
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
}

/**
 * Wire the Final Test button. The legacy Start button is gone — the
 * Hero card handles lesson entry now.
 * @tag NAVIGATION
 */
function wireStartButtons() {
    const ex = $("btn-exam");
    if (ex) ex.addEventListener("click", async () => {
        if (!canStartExamNow()) return;
        await startPerfectChallenge();
    });
}

// Keyboard shortcuts and openParentDashboard moved to child-keyboard.js

// Text-replacement pass moved to child-text.js

// Sidebar Mini Calendar moved to child-calendar.js

// ─── DOMContentLoaded bootstrap ──────────────────────────────
/**
 * Application entry point: wire all UI, restore state, load initial data.
 * @tag SYSTEM NAVIGATION
 */
document.addEventListener("DOMContentLoaded", async () => {
    // Textbook change handler
    const textbookSel = $("textbook-select");
    if (textbookSel) {
        textbookSel.addEventListener("change", async () => {
            const tb = textbookSel.value;
            if (!tb) return;
            sessionActive   = false;
            roadmapComplete = false;
            stage           = null;
            stageIndex      = 0;
            currentPhaseIndex  = 0;
            unlockedPhaseIndex = 0;
            spState.pass    = 1;
            wrongMap        = {};
            items           = [];
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

    // XP is now fetched from API via renderSummaryBar → _updateTopBarXP (home.js)

    wireTutorModal();
    wireStartButtons();

    const btnParent = $("btn-parent");
    if (btnParent) {
        // Phase 7: open in-app Parent Dashboard overlay (PIN verified via backend)
        btnParent.addEventListener("click", () => {
            if (typeof openParentPanel === "function") openParentPanel();
        });
    }

    // Restore state from localStorage
    sessionActive      = false;
    roadmapComplete    = allStagesDone();
    currentPhaseIndex  = 0;
    unlockedPhaseIndex = 0;
    stageIndex         = 0;
    stage              = null;
    spState.pass       = 1;

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

    // Word Match: flash animation on correct match
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

    // Sidebar toggle
    const _sidebar = document.getElementById('sidebar');
    const _toggle  = document.getElementById('sidebar-toggle');
    if (_toggle && _sidebar) {
        _toggle.addEventListener('click', () => _sidebar.classList.toggle('collapsed'));
    }

    // Restore subject
    const savedSubject = localStorage.getItem('subject_mode') || 'eng';
    window.setSubject(savedSubject);

    // Init dropdown UIs
    initLessonDropdownUI();
    initTextbookDropdownUI();

    // OCR button
    initOcrButton();

    // Progress bar sync (ring + top bar fill)
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

    // Stars mirror disabled — top-bar XP now driven by API via home.js _updateTopBarXP
    // (sidebar star-count kept for legacy compat but no longer mirrors to top-bar)

    // fx-wrong propagation: stage → stage-card
    (function() {
        const stageObs = document.getElementById('stage');
        const card     = document.getElementById('stage-card');
        if (!stageObs || !card) return;
        new MutationObserver(() => {
            if (stageObs.classList.contains('fx-wrong')) {
                card.classList.remove('fx-wrong');
                void card.offsetWidth;
                card.classList.add('fx-wrong');
                card.addEventListener('animationend', () => card.classList.remove('fx-wrong'), { once: true });
            }
        }).observe(stageObs, { attributes: true, attributeFilter: ['class'] });
    })();

    // fx-correct → perfect banner
    (function() {
        const stageObs = document.getElementById('stage');
        const banner   = document.getElementById('perfect-banner');
        if (!stageObs || !banner) return;
        new MutationObserver(() => {
            if (stageObs.classList.contains('fx-correct')) {
                banner.classList.remove('fire');
                void banner.offsetWidth;
                banner.classList.add('fire');
            }
        }).observe(stageObs, { attributes: true, attributeFilter: ['class'] });
    })();

    // Keyboard shortcuts
    initKeyboardShortcuts();

    // Text-replacement observer
    const stageEl = document.getElementById('stage') || document.getElementById('stage-card');
    if (stageEl) {
        const textObserver = new MutationObserver(() => replaceDescriptionTexts());
        textObserver.observe(stageEl, { childList: true, subtree: true, characterData: true });
        replaceDescriptionTexts();
    }

    // Auto-open parent panel when redirected from Folder Browser (?parent=1)
    if (new URLSearchParams(window.location.search).get("parent") === "1") {
        history.replaceState({}, "", window.location.pathname);
        if (typeof openParentPanel === "function") openParentPanel();
    }

    if (typeof lucide !== "undefined") lucide.createIcons();
});
