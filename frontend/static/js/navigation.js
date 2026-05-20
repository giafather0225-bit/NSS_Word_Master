/* ================================================================
   navigation.js — Subject/textbook/lesson selection and roadmap UI.
   Section: English / Navigation
   Dependencies: core.js, analytics.js
   API endpoints: /api/textbooks/:subject, /api/lessons/:subject/:textbook,
                  /api/study/:subject/:textbook/:lesson
   Split modules: navigation-sidebar.js (session helpers),
                  navigation-dropdown.js (dropdown UIs + OCR button)
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
        opt.textContent = `${done ? "[done] " : ""}${label}${ready ? "" : " ·"}`;
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

    // Tell the in-lesson cheer widget which zone's character to greet
    // the student with. `key` is the same identifier the API expects.
    if (window.IslandGuide && typeof window.IslandGuide.setSubject === "function") {
        try { window.IslandGuide.setSubject(key === "math" ? "math" : "english"); } catch (_) {}
    }

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
    rm.classList.add("stepbar");
    const inExam = stage === STAGE.EXAM;
    const completedSet = getCompletedStages();
    const hasLesson = !!lessonSelected();

    for (let i = 0; i < ROADMAP_STAGES.length; i++) {
        const key = ROADMAP_STAGES[i];
        const isDone     = completedSet.has(key) || inExam;
        const isCurrent  = !inExam && hasLesson && (stage === key);
        const isUnlocked = hasLesson && isStageUnlocked(key);

        const step = document.createElement("div");
        step.className = "step";

        // Base label: strip "N. " numeric prefix
        const rawLabel = ROADMAP_LABELS[i] || "";
        let label = rawLabel.replace(/^\d+\.\s*/, '').replace(/^\[done\]\s*/, '').trim();

        // Append progress info for the current stage
        if (isCurrent) {
            const n = items.length;
            if (n > 0 && sessionActive) {
                if (stage === STAGE.A) {
                    label += ` · R${wmState.round + 1}/3`;
                } else if (stage === STAGE.B && fbState.retryMode) {
                    label += " · retry";
                } else if (stage === STAGE.C && spState.retryMode) {
                    label += " · retry";
                } else {
                    label += ` · ${Math.min(stageIndex + 1, n)}/${n}`;
                }
            }
        }

        // State class
        if (isCurrent) {
            step.classList.add("active");
        } else if (isDone) {
            step.classList.add("done");
        } else if (!isUnlocked) {
            step.classList.add("locked");
        }

        const numEl = document.createElement("span");
        numEl.className = "step-num";
        numEl.textContent = String(i + 1);

        const labelEl = document.createElement("span");
        labelEl.className = "step-label";
        labelEl.textContent = label;

        step.appendChild(numEl);
        step.appendChild(labelEl);

        const canClick = !inExam && isUnlocked;
        if (canClick) {
            step.title = isDone ? `${label} — redo` : `${label} — start`;
            step.addEventListener("click", async () => {
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

        rm.appendChild(step);
    }
}

// Sidebar session helpers moved to navigation-sidebar.js
// Lesson/textbook dropdown UIs and OCR button moved to navigation-dropdown.js


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
