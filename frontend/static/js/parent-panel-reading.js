/* ================================================================
   parent-panel-reading.js — Parent Dashboard: Reading tab (Variant C)
   Section: Parent
   Dependencies: core.js, parent-panel.js
   API endpoints: /api/parent/ckla-summary, /api/parent/stage-stats,
                  /api/parent/word-stats, /api/parent/weaknesses,
                  /api/dashboard/stats, /api/daily-words/status,
                  /api/review/stats
   ================================================================ */

const _PP_STAGE_LABEL = {
    preview:    "Preview",
    word_match: "Word Match",
    fill_blank: "Fill Blank",
    spelling:   "Spelling",
    sentence:   "Sentence",
};
const _PP_STAGE_ORDER = ["preview", "word_match", "fill_blank", "spelling", "sentence"];

/** Reading tab entry. @tag PARENT */
async function _ppReading(body) {
    try {
        const _safe = (p, fb) => p.catch(() => fb);

        const [ckla, stageStats, wordStats, weak, dashStats, daily, reviewStats] = await Promise.all([
            _safe(apiFetchJSON("/api/parent/ckla-summary?grade=3"), {}),
            _safe(apiFetchJSON("/api/parent/stage-stats"),          { stages: {} }),
            _safe(apiFetchJSON("/api/parent/word-stats"),           { words: [], top_wrong: [] }),
            _safe(apiFetchJSON("/api/parent/weaknesses"),           { weaknesses: [] }),
            _safe(apiFetchJSON("/api/dashboard/stats"),             {}),
            _safe(apiFetchJSON("/api/daily-words/status"),          {}),
            _safe(apiFetchJSON("/api/review/stats"),                {}),
        ]);

        body.innerHTML = `
            <div class="pp-reading-row1">
                ${_ppReadingCkla(ckla)}
                ${_ppReadingVocab(dashStats)}
                ${_ppReadingDailyRev(daily, reviewStats, dashStats)}
            </div>
            <div class="pp-reading-row2">
                ${_ppReadingStageStats(stageStats.stages || {})}
                ${_ppReadingWordStats(wordStats)}
                ${_ppReadingWeak(weak.weaknesses || [], stageStats.stages || {})}
            </div>`;

        if (typeof lucide !== "undefined") lucide.createIcons();
    } catch (err) {
        console.error("[parent-reading] load failed:", err);
        body.innerHTML = `<p class="pp-error-pad">Failed to load Reading.</p>`;
    }
}

/** CKLA domains card with cumulative sparkline + per-domain rows. @tag PARENT CKLA */
function _ppReadingCkla(ckla) {
    const domains = ckla.domains || [];
    const totalDone = domains.reduce((a, d) => a + (d.completed_count || 0), 0);
    const totalLessons = domains.reduce((a, d) => a + (d.lesson_count || 0), 0);
    const grade = ckla.grade ? `G${ckla.grade}` : "G3";

    const rows = domains.slice(0, 6).map(d => {
        const done = d.completed_count || 0;
        const total = d.lesson_count || 0;
        const pct = total ? done / total : 0;
        const locked = !!d.locked;
        return `
            <div class="pp-ckla-row">
                <span class="pp-ckla-row-name ${locked ? "is-locked" : ""}">
                    ${escapeHtml(d.title || `Domain ${d.domain_num}`)}${locked ? ' <i data-lucide="lock" class="pp-ckla-lock"></i>' : ""}
                </span>
                <span class="mono pp-ckla-row-count">${done}/${total}</span>
                <div class="pp-ckla-bar"><div class="pp-ckla-bar-fill" style="width:${(pct*100).toFixed(0)}%"></div></div>
                <span class="pp-ckla-sparkline">${_ppSparkline([0, done * 0.3, done * 0.6, done].map(Math.round), { width: 50, height: 16, color: locked ? "var(--ink-4)" : "var(--english-primary)", strokeWidth: 1.2 })}</span>
            </div>`;
    }).join("");

    return `
        <div class="pp-panel">
            <div class="pp-panel-title">
                <div class="pp-panel-title-left">CKLA Domains
                    <span class="pp-panel-sub">${grade} · ${totalDone}/${totalLessons} lessons</span>
                </div>
            </div>
            <div class="pp-ckla-trend">
                <div>
                    <div class="pp-ckla-trend-kick">Total lessons done</div>
                    <div class="pp-ckla-trend-num">
                        <span class="mono">${totalDone}</span>
                        <span class="pp-ckla-trend-sub">across ${domains.length} domains</span>
                    </div>
                </div>
                <div class="pp-ckla-trend-spark">
                    ${_ppSparkline(domains.map(d => d.completed_count || 0), { width: 200, height: 32, color: "var(--english-primary)", fill: true, strokeWidth: 1.6 })}
                </div>
            </div>
            <div class="pp-ckla-rows">${rows || `<p class="pp-text-hint">No domains data.</p>`}</div>
        </div>`;
}

/** Vocabulary (Voca_8000) card with 5-stage indicator and weekly minutes sparkline. @tag PARENT ENGLISH */
function _ppReadingVocab(dashStats) {
    const totalLessons = dashStats.total_lessons || 40;
    const completed = dashStats.completed_lessons || 0;
    const currentTextbook = dashStats.current_textbook || "Voca_8000";
    const currentLesson = dashStats.current_lesson || "—";
    const stageNames = ["pre", "wor", "fil", "spe", "sen"];
    const stageDone = dashStats.current_lesson_stages || {}; // {preview:bool, wordmatch:bool, ...}
    const stagesArr = [
        !!stageDone.preview,
        !!stageDone.wordmatch,
        !!stageDone.fillblank,
        !!stageDone.spelling,
        !!stageDone.sentence,
    ];

    const stagePills = stageNames.map((lbl, i) => `
        <div class="pp-vocab-stage ${stagesArr[i] ? "is-done" : ""}">${lbl.toUpperCase()}</div>
    `).join("");

    return `
        <div class="pp-panel">
            <div class="pp-panel-title">
                <div class="pp-panel-title-left">Vocabulary
                    <span class="pp-panel-sub">${escapeHtml(currentTextbook)} · ${escapeHtml(currentLesson)}</span>
                </div>
            </div>
            <div class="pp-vocab-big">
                <span class="mono">${completed}/${totalLessons}</span>
                <span class="pp-vocab-big-sub">lessons</span>
            </div>
            <div class="pp-vocab-stages">${stagePills}</div>
            <div class="pp-vocab-stage-hint">5-stage progress for current lesson</div>
        </div>`;
}

/** Daily Words / Review / My Words 3-row list. @tag PARENT */
function _ppReadingDailyRev(daily, reviewStats, dashStats) {
    const dwThisWeek = daily.this_week_days || 0;
    const dwToday = daily.today_words || 0;
    const dwTarget = daily.target_per_day || 10;
    const dwStreak = daily.streak || 0;
    const due = reviewStats.due_today || 0;
    const doneToday = reviewStats.reviewed_today || 0;
    const mastered = reviewStats.mastered || 0;
    const totalReviews = due + doneToday || 1;
    const retention = reviewStats.retention_pct || 0;
    const saved = dashStats.my_words_saved || 0;
    const enriched = dashStats.my_words_enriched || 0;

    const row = (label, val, sub, accent) => `
        <div class="pp-rev-row">
            <div class="pp-rev-row-head">
                ${accent ? `<span class="pp-kpi-dot" style="background:${accent}"></span>` : ""}
                <span class="pp-rev-row-label">${label}</span>
                <span class="mono pp-rev-row-val">${val}</span>
            </div>
            <div class="pp-rev-row-sub">${sub}</div>
        </div>`;

    return `
        <div class="pp-panel">
            <div class="pp-panel-title">
                <div class="pp-panel-title-left">Daily Words / Review</div>
            </div>
            <div class="pp-rev-list">
                ${row("Daily Words", `${dwThisWeek}/5`, `Today ${dwToday}/${dwTarget} · ${dwStreak}-day streak`)}
                ${row("Review (SM-2)", due, `Done today ${doneToday}/${totalReviews} · Recall ${retention}%`, "var(--review-primary)")}
                ${row("My Words", saved, `AI-enriched ${enriched}/${saved}`)}
            </div>
        </div>`;
}

/** 5-stage performance with attempts + accuracy bar + avg time. @tag PARENT STAGES */
function _ppReadingStageStats(stages) {
    const rows = _PP_STAGE_ORDER.map((key, i) => {
        const s = stages[key] || {};
        const acc = Math.round(s.avg_accuracy || 0);
        const attempts = s.completions || 0;
        const avgTime = s.avg_time_sec || 0;
        const isWeak = acc < 70 && attempts > 0;
        return `
            <div class="pp-stage5-row">
                <span class="mono pp-stage5-idx">${i + 1}</span>
                <span class="pp-stage5-name ${isWeak ? "is-weak" : ""}">${_PP_STAGE_LABEL[key]}</span>
                <span class="mono pp-stage5-tries">${attempts} tries</span>
                <div class="pp-stage5-bar">
                    <div class="pp-stage5-bar-fill ${isWeak ? "is-weak" : ""}" style="width:${acc}%"></div>
                </div>
                <span class="mono pp-stage5-acc ${isWeak ? "is-weak" : ""}">${acc}%</span>
                <span class="mono pp-stage5-time">${avgTime}s avg</span>
            </div>`;
    }).join("");

    // Find weakest stage for footer
    let weakest = null;
    let lowestAcc = 101;
    _PP_STAGE_ORDER.forEach(key => {
        const s = stages[key];
        if (s && (s.avg_accuracy ?? 100) < lowestAcc && (s.completions || 0) > 0) {
            lowestAcc = s.avg_accuracy;
            weakest = key;
        }
    });
    const footerMsg = weakest && lowestAcc < 80
        ? `<b class="pp-stage5-weak-name">${_PP_STAGE_LABEL[weakest]}</b> needs the most attention — ${Math.round(lowestAcc)}% accuracy.`
        : `All stages currently above 80% accuracy.`;

    return `
        <div class="pp-panel">
            <div class="pp-panel-title">
                <div class="pp-panel-title-left">5-stage performance
                    <span class="pp-panel-sub">Preview → Word Match → Fill Blank → Spelling → Sentence</span>
                </div>
            </div>
            <div class="pp-stage5-list">${rows}</div>
            <div class="pp-stage5-footer">${footerMsg}</div>
        </div>`;
}

/** Word mastery 3-bucket card + struggling examples. @tag PARENT WORD_STATS */
function _ppReadingWordStats(wordStats) {
    const words = wordStats.words || [];
    const total = words.length;
    const mastered = words.filter(w => (w.accuracy || 0) >= 80).length;
    const learning = words.filter(w => (w.accuracy || 0) >= 50 && (w.accuracy || 0) < 80).length;
    const struggling = words.filter(w => (w.accuracy || 0) < 50).length;
    const masteredPct = total ? Math.round((mastered / total) * 100) : 0;
    const strugglingExamples = words.filter(w => (w.accuracy || 0) < 50).slice(0, 5).map(w => w.word);

    const safeTotal = total || 1;
    const segHtml = `
        <div class="pp-word-stack">
            <div class="pp-word-stack-seg" title="Mastered: ${mastered}" style="width:${(mastered/safeTotal*100).toFixed(0)}%;background:var(--ok)"></div>
            <div class="pp-word-stack-seg" title="Learning: ${learning}" style="width:${(learning/safeTotal*100).toFixed(0)}%;background:var(--warn)"></div>
            <div class="pp-word-stack-seg" title="Struggling: ${struggling}" style="width:${(struggling/safeTotal*100).toFixed(0)}%;background:var(--bad)"></div>
        </div>`;

    const examplesHtml = strugglingExamples.length
        ? strugglingExamples.map(w => `<span class="mono pp-struggle-chip">${escapeHtml(w)}</span>`).join("")
        : `<span class="pp-text-hint">None — great job!</span>`;

    return `
        <div class="pp-panel">
            <div class="pp-panel-title">
                <div class="pp-panel-title-left">Word mastery
                    <span class="pp-panel-sub">${total} words tracked</span>
                </div>
            </div>
            <div class="pp-word-pct">
                <span class="mono">${masteredPct}%</span>
                <span class="pp-word-pct-sub">mastered</span>
            </div>
            ${segHtml}
            <div class="pp-word-legend">
                <span><span class="pp-word-legend-dot" style="background:var(--ok)"></span>Mastered <b class="mono">${mastered}</b></span>
                <span><span class="pp-word-legend-dot" style="background:var(--warn)"></span>Learning <b class="mono">${learning}</b></span>
                <span><span class="pp-word-legend-dot" style="background:var(--bad)"></span>Struggling <b class="mono">${struggling}</b></span>
            </div>
            <div class="pp-word-struggle">
                <div class="pp-mini-kick">Currently struggling</div>
                <div class="pp-struggle-chips">${examplesHtml}</div>
            </div>
        </div>`;
}

/** Weakness analysis (from /api/parent/weaknesses + stage stats inference). @tag PARENT */
function _ppReadingWeak(items, stages) {
    // Derive top 3 from real weaknesses + stage stats.
    const cards = [];

    // Stage-based weakness card (always shown for context)
    let stageWeakest = null;
    let lowestAcc = 101;
    Object.entries(stages).forEach(([key, s]) => {
        if ((s.avg_accuracy ?? 100) < lowestAcc && (s.completions || 0) > 0) {
            lowestAcc = s.avg_accuracy;
            stageWeakest = key;
        }
    });
    if (stageWeakest && lowestAcc < 80) {
        cards.push({
            area: `${_PP_STAGE_LABEL[stageWeakest]} stage`,
            score: Math.round(lowestAcc),
            why: `Lowest accuracy across all 5 stages.`,
            action: `Repeat ${_PP_STAGE_LABEL[stageWeakest]} drills`,
        });
    }
    // Wrong words
    items.filter(w => w.subject === "english").slice(0, 2).forEach(w => {
        cards.push({
            area: w.label || "Vocabulary",
            score: w.accuracy ?? 0,
            why: w.detail || `${w.attempts || 0} attempts.`,
            action: "Open word",
        });
    });
    // CKLA
    items.filter(w => w.subject === "ckla").slice(0, 1).forEach(w => {
        cards.push({
            area: `CKLA · ${w.label}`,
            score: w.accuracy ?? 0,
            why: w.detail || "Below class average.",
            action: "Continue domain",
        });
    });

    if (!cards.length) {
        return `
            <div class="pp-panel">
                <div class="pp-panel-title">
                    <div class="pp-panel-title-left">Weakness analysis</div>
                </div>
                <p class="pp-text-hint">No weak areas yet — keep studying to see patterns here.</p>
            </div>`;
    }

    const rows = cards.slice(0, 3).map(c => `
        <div class="pp-weak-card">
            <div class="pp-weak-head">
                <i data-lucide="alert-triangle" class="pp-weak-icon"></i>
                <span class="pp-weak-area">${escapeHtml(c.area)}</span>
                ${c.score < 70 ? `<span class="mono pp-weak-score">${c.score}%</span>` : ""}
            </div>
            <div class="pp-weak-why">${escapeHtml(c.why)}</div>
            <button class="pp-weak-action">
                ${escapeHtml(c.action)} <i data-lucide="arrow-right"></i>
            </button>
        </div>`).join("");

    return `
        <div class="pp-panel">
            <div class="pp-panel-title">
                <div class="pp-panel-title-left">Weakness analysis
                    <span class="pp-panel-sub">From /api/parent/weaknesses</span>
                </div>
            </div>
            <div class="pp-weak-list">${rows}</div>
        </div>`;
}

window._ppReading = _ppReading;
