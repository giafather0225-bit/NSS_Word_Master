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

        if (!document.getElementById('sc-btn-style')) {
            const sty = document.createElement('style');
            sty.id = 'sc-btn-style';
            sty.textContent = `
                @keyframes sc-draw{from{stroke-dashoffset:151}to{stroke-dashoffset:0}}
                @keyframes sc-tick{from{stroke-dashoffset:40}to{stroke-dashoffset:0}}
                @keyframes sc-fade{from{opacity:0;transform:translateY(12px)}to{opacity:1;transform:translateY(0)}}
                .sc-card{display:flex;flex-direction:column;align-items:stretch;justify-content:flex-start;gap:24px;max-width:680px;margin:24px auto;padding:32px 28px;background:var(--bg-card);border:1px solid var(--border-card);border-radius:var(--radius-lg)}
                .sc-hero{display:flex;flex-direction:column;align-items:center;gap:6px;opacity:0;animation:sc-fade 0.4s 0.2s ease forwards}
                .sc-svg{width:64px;height:64px;margin-bottom:4px}
                .sc-circle{fill:none;stroke:var(--color-success);stroke-width:2.5;stroke-linecap:round;stroke-dasharray:151;stroke-dashoffset:151;animation:sc-draw 0.7s ease forwards}
                .sc-tick{fill:none;stroke:var(--color-success);stroke-width:3;stroke-linecap:round;stroke-linejoin:round;stroke-dasharray:40;stroke-dashoffset:40;animation:sc-tick 0.35s 0.55s ease forwards}
                .sc-eyebrow{font-size:12px;font-weight:600;letter-spacing:0.08em;text-transform:uppercase;color:var(--text-secondary);margin:0}
                .sc-title{font-size:22px;font-weight:700;color:var(--text-primary);letter-spacing:-0.01em;margin:0}
                .sc-stats{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;padding:16px;background:var(--bg-surface);border-radius:var(--radius-md);opacity:0;animation:sc-fade 0.4s 0.5s ease forwards}
                .sc-stat{display:flex;flex-direction:column;align-items:center;gap:2px}
                .sc-stat-val{font-size:24px;font-weight:700;color:var(--color-primary);line-height:1.1}
                .sc-stat-val-miss{color:var(--color-warning)}
                .sc-stat-lbl{font-size:11px;font-weight:500;letter-spacing:0.04em;text-transform:uppercase;color:var(--text-secondary)}
                .sc-chips{display:flex;flex-wrap:wrap;gap:8px;justify-content:center;max-height:160px;overflow-y:auto;padding:4px 0;opacity:0;animation:sc-fade 0.4s 0.7s ease forwards}
                .sc-chip{display:inline-flex;align-items:center;gap:6px;padding:6px 12px;border-radius:var(--radius-full);font-size:13px;font-weight:500;border:1px solid var(--border-default);background:var(--bg-card);color:var(--text-primary)}
                .sc-chip-ok{border-color:var(--color-success);color:var(--color-success);background:var(--color-success-light)}
                .sc-chip-miss{border-color:var(--color-warning);color:var(--color-warning);background:var(--color-warning-light)}
                .sc-chip-mark{font-weight:700;font-size:12px}
                .sc-cta-row{display:flex;gap:12px;justify-content:center;flex-wrap:wrap;opacity:0;animation:sc-fade 0.4s 0.9s ease forwards}
                .sc-btn{padding:12px 28px;border-radius:var(--radius-md);font-size:15px;font-weight:600;cursor:pointer;transition:background 0.15s ease,transform 0.12s ease,border-color 0.15s ease;border:1px solid transparent;min-height:44px}
                .sc-btn-primary{background:var(--color-primary);border-color:var(--color-primary);color:var(--text-on-primary)}
                .sc-btn-primary:hover{background:var(--color-primary-hover);border-color:var(--color-primary-hover)}
                .sc-btn-ghost{background:transparent;border-color:var(--border-default);color:var(--text-primary)}
                .sc-btn-ghost:hover{background:var(--bg-surface);border-color:var(--border-strong)}
                .sc-btn:active{transform:scale(0.98);opacity:0.9}
                @media (max-width:520px){.sc-card{padding:24px 18px;gap:18px}.sc-title{font-size:20px}.sc-stat-val{font-size:20px}}
            `;
            document.head.appendChild(sty);
        }
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
        const bgStyle = perfect
            ? "background:linear-gradient(135deg,#f6d365 0%,#fda085 100%);border-radius:16px;padding:32px;"
            : "padding:32px;";
        const bodyLines = perfect
            ? `<div style="font-size:4rem;line-height:1;">🏆</div>
               <div style="font-size:2.2rem;font-weight:900;margin:14px 0 8px;color:#7d4600;">PERFECT!</div>
               <div style="font-size:1.2rem;font-weight:700;color:#7d4600;">No mistakes — incredible!</div>`
            : `<div style="line-height:1;"><span class="check-dot check-dot--lg"></span></div>
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

// ─── Keyboard shortcuts ───────────────────────────────────────
/**
 * Register global keyboard shortcuts (Space, Esc, 1–5, ⌘L, ⌘\, ⌘,).
 * @tag NAVIGATION SYSTEM
 */
function initKeyboardShortcuts() {
    document.addEventListener('keydown', (e) => {
        const active = document.activeElement;
        const inInput = active && (
            active.tagName === 'INPUT' ||
            active.tagName === 'TEXTAREA' ||
            active.isContentEditable
        );

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

        if (!inInput && e.key >= '1' && e.key <= '5') {
            const stageMap = { '1': STAGE.PREVIEW, '2': STAGE.A, '3': STAGE.B, '4': STAGE.C, '5': STAGE.D };
            const target = stageMap[e.key];
            if (target && isStageUnlocked(target)) {
                e.preventDefault();
                jumpToStage(target);
            }
        }

        if (e.metaKey && e.key === 'l') {
            e.preventDefault();
            const sel = document.getElementById('lesson-select');
            if (sel && sel.options.length > 1) {
                const next = (sel.selectedIndex + 1) % sel.options.length || 1;
                sel.selectedIndex = next;
                sel.dispatchEvent(new Event('change'));
            }
        }

        if (e.metaKey && e.key === '\\') {
            e.preventDefault();
            document.getElementById('sidebar').classList.toggle('collapsed');
        }

        if (e.metaKey && e.key === ',') {
            e.preventDefault();
            document.getElementById('btn-parent')?.click();
        }
    });
}

/**
 * Open Parent Dashboard from home dashboard gear button.
 * Delegates to the sidebar #btn-parent click handler.
 * @tag PARENT HOME_DASHBOARD
 */
function openParentDashboard() {
    if (typeof openParentPanel === 'function') {
        openParentPanel();
    } else {
        document.getElementById('btn-parent')?.click();
    }
}

// ─── Text-replacement pass ────────────────────────────────────
/**
 * Friendly-text replacements for stage sub-titles and placeholders.
 * @tag ENGLISH SYSTEM
 */
const TEXT_REPLACEMENTS = {
    'Click a word, then click its meaning.':
        'Tap a word on the left, then find its meaning on the right.',
    'Type the missing word…':
        'Type the missing word.',
    'Some letters hidden':
        'Some letters are hidden.',
    'More letters hidden':
        'More letters are hidden now!',
    'Listen, then type the word.':
        'Listen and type the word.',
    'Use this word in a sentence':
        'Write a sentence using this word.',
};

/** @tag ENGLISH SYSTEM */
const roundRegex = /Round (\d+) of (\d+)\s*[·•]\s*Words (\d+)[–-](\d+)\s*[·•]\s*Click a word, then click its meaning\./;

/**
 * Walk .st-sub elements and apply friendly text replacements.
 * @tag ENGLISH SYSTEM
 */
function replaceDescriptionTexts() {
    document.querySelectorAll('.st-sub').forEach(el => {
        const roundMatch = el.textContent.match(roundRegex);
        if (roundMatch) {
            el.innerHTML = `Round ${roundMatch[1]}/${roundMatch[2]} · Words ${roundMatch[3]}–${roundMatch[4]} · Tap a word, then find its meaning! 👉`;
            return;
        }
        for (const [original, replacement] of Object.entries(TEXT_REPLACEMENTS)) {
            if (original === replacement) continue;
            if (el.textContent.includes(original)) {
                const next = el.textContent.replace(original, replacement);
                if (next !== el.textContent) el.textContent = next;
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

// ─── Sidebar Mini Calendar ────────────────────────────────────
// NOTE: distinct from the Phase 6 full Calendar in calendar.js — this one
// powers the small #sb-cal-grid widget in the sidebar. Renamed to _sbCal*
// to avoid colliding with calendar.js's _calYear/_calMonth (1-indexed).
/** @tag SYSTEM */
let _sbCalYear, _sbCalMonth;

/**
 * Alias kept for compatibility — delegates to initMonthlyCalendar().
 * @tag SYSTEM
 */
function initWeeklyCalendar() { initMonthlyCalendar(); }

/**
 * Initialise the monthly sidebar calendar and wire prev/next buttons.
 * @tag SYSTEM
 */
function initMonthlyCalendar() {
    const now = new Date();
    _sbCalYear  = now.getFullYear();
    _sbCalMonth = now.getMonth();
    renderMonthlyCalendar();
    const prev = document.getElementById("sb-cal-prev");
    const next = document.getElementById("sb-cal-next");
    if (prev) prev.onclick = function() { _sbCalMonth--; if (_sbCalMonth < 0)  { _sbCalMonth = 11; _sbCalYear--; } renderMonthlyCalendar(); };
    if (next) next.onclick = function() { _sbCalMonth++; if (_sbCalMonth > 11) { _sbCalMonth = 0;  _sbCalYear++; } renderMonthlyCalendar(); };
}

/**
 * Render the month grid into #sb-cal-grid and trigger study-data fetch.
 * @tag SYSTEM
 */
function renderMonthlyCalendar() {
    const grid  = document.getElementById("sb-cal-grid");
    const title = document.getElementById("sb-cal-title");
    if (!grid) return;
    const months = ["January","February","March","April","May","June","July","August","September","October","November","December"];
    if (title) title.textContent = months[_sbCalMonth] + " " + _sbCalYear;
    grid.innerHTML = "";
    const headers = ["Mo","Tu","We","Th","Fr","Sa","Su"];
    headers.forEach(function(h) {
        const el = document.createElement("div");
        el.className = "sb-cal-day-header";
        el.textContent = h;
        grid.appendChild(el);
    });
    const firstDay    = new Date(_sbCalYear, _sbCalMonth, 1).getDay();
    const startOffset = firstDay === 0 ? 6 : firstDay - 1;
    const daysInMonth = new Date(_sbCalYear, _sbCalMonth + 1, 0).getDate();
    const now         = new Date();
    const todayDate   = now.getDate();
    const todayMonth  = now.getMonth();
    const todayYear   = now.getFullYear();
    for (let i = 0; i < startOffset; i++) {
        const empty = document.createElement("div");
        empty.className = "sb-cal-day empty";
        grid.appendChild(empty);
    }
    for (let d = 1; d <= daysInMonth; d++) {
        const cell = document.createElement("div");
        cell.className = "sb-cal-day";
        cell.textContent = d;
        cell.dataset.date = _sbCalYear + "-" + String(_sbCalMonth+1).padStart(2,"0") + "-" + String(d).padStart(2,"0");
        if (d === todayDate && _sbCalMonth === todayMonth && _sbCalYear === todayYear) {
            cell.classList.add("today");
        }
        grid.appendChild(cell);
    }
    loadMonthlyStudyData();
}

/**
 * Fetch analytics and highlight studied days on the calendar grid.
 * @tag SYSTEM
 */
function loadMonthlyStudyData() {
    fetch("/api/dashboard/analytics")
        .then(function(res) { return res.json(); })
        .then(function(data) {
            const sessions = data.daily_sessions || data.sessions || [];
            const studiedDates = new Set();
            sessions.forEach(function(s) {
                const dateStr = s.date || (s.started_at ? s.started_at.substring(0,10) : "");
                if (dateStr) studiedDates.add(dateStr);
            });
            const grid = document.getElementById("sb-cal-grid");
            if (!grid) return;
            grid.querySelectorAll(".sb-cal-day[data-date]").forEach(function(cell) {
                if (studiedDates.has(cell.dataset.date)) {
                    cell.classList.add("studied");
                }
            });
        })
        .catch(function() {});
}

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
