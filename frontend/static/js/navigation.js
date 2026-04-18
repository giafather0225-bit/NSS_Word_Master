/* ================================================================
   navigation.js — Subject/textbook/lesson selection, roadmap UI,
                   sidebar session mode, progress label, and OCR button.
   Section: English / Navigation
   Dependencies: core.js, analytics.js
   API endpoints: /api/textbooks/:subject, /api/lessons/:subject/:textbook,
                  /api/study/:subject/:textbook/:lesson,
                  /api/lessons/ingest_disk/:lesson
   ================================================================ */

/**
 * Mirror `.sidebar.collapsed` onto `body.sb-collapsed` so CSS rules that must
 * react to sidebar state (e.g. the floating toggle position) can use a stable
 * selector instead of the less-reliable `~` sibling combinator with fixed
 * positioning.
 * @tag NAVIGATION SIDEBAR
 */
(function mirrorSidebarCollapsed() {
    const apply = () => {
        const sidebar = document.getElementById('sidebar');
        if (!sidebar) return;
        document.body.classList.toggle('sb-collapsed', sidebar.classList.contains('collapsed'));
    };
    const init = () => {
        const sidebar = document.getElementById('sidebar');
        if (!sidebar) { setTimeout(init, 100); return; }
        apply();
        new MutationObserver(apply).observe(sidebar, { attributes: true, attributeFilter: ['class'] });
    };
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();

/**
 * Load the list of textbooks for a subject and populate the select.
 * Auto-selects if only one textbook is available.
 * @tag NAVIGATION SIDEBAR
 */
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
                opt.textContent = tb.replace(/_/g, ' ');
                sel.appendChild(opt);
            });
            if (data.textbooks && data.textbooks.length === 1) {
                sel.value = data.textbooks[0];
                await loadLessons(subject, data.textbooks[0]);
            }
        }
    } catch (err) {
        console.warn('[loadTextbooks] Failed to fetch textbooks:', err.message || err);
    }
}

/**
 * Load lessons for the given subject/textbook, populate the select, and
 * wire the change-handler for lesson switching.
 * @tag NAVIGATION SIDEBAR
 */
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
        const label = l.replace(/_/g, ' ');
        opt.textContent = `${done ? "✓ " : ""}${label}${ready ? "" : " ·"}`;
        opt.dataset.ready = ready ? "true" : "false";
        if (l === selectedLesson) opt.selected = true;
        sel.appendChild(opt);
    });

    setActiveLessonTab(selectedLesson);
    renderIdleStage();
    updateRoadmapUI();
    updateProgressPct();
    updateChallengeMeta();
    refreshStartLabel();

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

/**
 * Fetch study items for the current subject/textbook/lesson.
 * Populates the global items[] array.
 * @tag NAVIGATION ENGLISH
 */
async function loadStudyItems(lesson) {
    if (!currentTextbook) { console.warn("[loadStudyItems] no textbook selected"); return; }
    const res = await fetch(`/api/study/${encodeURIComponent(currentSubject)}/${encodeURIComponent(currentTextbook)}/${encodeURIComponent(lesson)}`);
    if (!res.ok) {
        let txt = "";
        try { txt = await res.text(); } catch {}
        const msg = txt ? txt.slice(0, 250) : "";
        throw new Error(`Failed to load lesson (${res.status}). ${msg}`.trim());
    }
    const data = await res.json();
    items = data.items || [];
    return data.progress || null;
}

/**
 * Switch active subject (eng / math), reload textbooks, and reset all state.
 * Exposed as window.setSubject for inline HTML onclick handlers.
 * @tag NAVIGATION SIDEBAR
 */
window.setSubject = async function (key) {
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

    document.querySelectorAll(".sb-subject-tab").forEach((t) => t.classList.remove("active"));
    const activeTab = document.getElementById(`tab-${key}`);
    if (activeTab) activeTab.classList.add("active");

    document.body.classList.toggle("math-mode", newSubject === "Math");

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

/**
 * Update the Start / Repeat button label to reflect current progress.
 * @tag NAVIGATION SIDEBAR
 */
function refreshStartLabel() {
    const isDone = allStagesDone();
    const ex = $("btn-exam");
    if (ex) ex.disabled = !isDone;
}

/**
 * Render the roadmap pill strip in the top bar.
 * @tag NAVIGATION
 */
function updateRoadmapUI() {
    const rm = $("roadmap");
    if (!rm) return;
    rm.innerHTML = "";
    const inExam = stage === STAGE.EXAM;
    const completedSet = getCompletedStages();
    const hasLesson = !!lessonSelected();

    for (let i = 0; i < ROADMAP_STAGES.length; i++) {
        const key = ROADMAP_STAGES[i];
        const isDone     = completedSet.has(key);
        const isCurrent  = hasLesson && (stage === key);
        const isUnlocked = hasLesson && isStageUnlocked(key);

        const div = document.createElement("div");
        div.className = "road-pill";

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

        const canClick = !inExam && isUnlocked;
        if (canClick) {
            div.style.cursor = "pointer";
            div.title = isDone ? `${ROADMAP_LABELS[i]} — redo` : `${ROADMAP_LABELS[i]} — start`;
            div.addEventListener("click", async () => {
                if (!items.length) {
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

        // Strip numeric prefix from pill labels
        div.textContent = div.textContent.replace(/^\d+\.\s*/, '').replace(/^✓\s*/, '✓ ');
        rm.appendChild(div);
    }
}

// ─── Sidebar session helpers ──────────────────────────────────
/**
 * Return a human-readable "N / total left" string for the current stage.
 * @tag NAVIGATION SIDEBAR
 */
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

/**
 * Toggle keyboard-hint pill visibility based on current stage.
 * @tag NAVIGATION SIDEBAR
 */
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

/**
 * Refresh the sidebar session-info rows (lesson, stage, progress, mistakes).
 * @tag NAVIGATION SIDEBAR
 */
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

/**
 * Wire the Listen and Skip buttons in the sidebar session panel.
 * @tag NAVIGATION SIDEBAR
 */
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

/**
 * Switch the sidebar into session mode (hide selection area, show info).
 * @tag NAVIGATION SIDEBAR
 */
function enterSessionSidebar() {
    const sel  = $("sb-selection-area");
    const info = $("sb-session-info");
    if (sel)  sel.classList.add("hidden");
    if (info) info.classList.remove("hidden");
    wireSbSessionButtons();
    updateSessionSidebarInfo();
}

/**
 * Switch the sidebar back to selection mode.
 * @tag NAVIGATION SIDEBAR
 */
function exitSessionSidebar() {
    const sel  = $("sb-selection-area");
    const info = $("sb-session-info");
    if (sel)  sel.classList.remove("hidden");
    if (info) info.classList.add("hidden");
    updateHints();
}

/**
 * Update the challenge-meta element (delegates to updateProgressPct).
 * @tag NAVIGATION
 */
function updateChallengeMeta_nav() {}

// ─── Lesson-dropdown custom UI ────────────────────────────────
/**
 * Initialise the custom lesson-dropdown UI that mirrors the hidden <select>.
 * @tag NAVIGATION SIDEBAR
 */
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
                    var _tb  = typeof currentTextbook !== 'undefined' ? currentTextbook : 'Voca_8000';
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

/**
 * Initialise the custom textbook-dropdown UI that mirrors the hidden <select>.
 * @tag NAVIGATION SIDEBAR
 */
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

/**
 * Initialise the OCR "Register (image → words)" button.
 * Hides itself when the lesson is already ready, shows and triggers OCR otherwise.
 * @tag OCR NAVIGATION
 */
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
            ocrBtn.textContent = `✓ ${data.words} words registered!`;
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

/**
 * Jump directly to a named stage (used by DEV tools and roadmap pill clicks).
 * @tag NAVIGATION
 */
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
