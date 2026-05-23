/* ================================================================
   parent-panel-math.js — Parent Dashboard: Math tab (Variant C)
   Section: Parent
   Dependencies: core.js, parent-panel.js
   API endpoints: /api/parent/math-summary, /api/math/placement/results,
                  /api/math/academy/{grade}/units
   ================================================================ */

const _PP_MATH_STAGES = ["pretest", "learn", "try", "practice_r1", "practice_r2", "practice_r3", "unit_test"];

/** Convert grade string ("G3") to integer (3) for numeric comparison. @tag PARENT MATH */
function _ppGradeNum(g) { return parseInt((g || "G3").replace(/\D/g, ""), 10); }

/** Math tab entry. @tag PARENT MATH */
async function _ppMathSummary(body) {
    try {
        const _safe = (p, fb) => p.catch(() => fb);
        const grade = window._ppCurrentGrade || "G3";

        const [summary, placement, unitsResp] = await Promise.all([
            _safe(apiFetchJSON("/api/parent/math-summary"),               {}),
            _safe(apiFetchJSON("/api/math/placement/results"),            { results: [] }),
            _safe(apiFetchJSON(`/api/math/academy/${grade}/units`),       { grade, units: [] }),
        ]);

        body.innerHTML = `
            ${_ppMathPlacementStrip(placement.results || [])}
            ${_ppMathUnitGrid(grade, unitsResp.units || [], summary)}
            <div class="pp-2col pp-2col--top">
                ${_ppMathRowsCard(summary)}
                ${_ppMathFluencyCard(summary.fluency || [])}
            </div>
            <div class="pp-2col pp-2col--top">
                ${_ppMathGlossaryCard(summary)}
                ${_ppMathSpacedReviewCard(summary.spaced_review || {})}
            </div>`;

        if (typeof lucide !== "undefined") lucide.createIcons();
    } catch (err) {
        console.error("[parent-math] load failed:", err);
        body.innerHTML = `<p class="pp-error-pad">Failed to load Math.</p>`;
    }
}

/** Placement test strip — N domain cards horizontally. @tag PARENT MATH_PLACEMENT */
function _ppMathPlacementStrip(results) {
    if (!results.length) {
        return `
            <div class="pp-panel">
                <div class="pp-panel-title">
                    <div class="pp-panel-title-left">Placement Test
                        <span class="pp-panel-sub">Not taken yet</span>
                    </div>
                </div>
                <p class="pp-text-hint">Placement test not taken. Take it to get a personalized starting point.</p>
            </div>`;
    }

    // Estimate suggested grade as the most common across domains.
    const gradeCounts = {};
    results.forEach(r => { gradeCounts[r.estimated_grade] = (gradeCounts[r.estimated_grade] || 0) + 1; });
    const suggested = Object.keys(gradeCounts).sort((a, b) => gradeCounts[b] - gradeCounts[a])[0] || "G3";
    const weakDomains = results.filter(r => _ppGradeNum(r.estimated_grade) < _ppGradeNum(suggested));

    const date = (results[0]?.test_date || "").slice(0, 10);
    const subText = `Taken ${date}` + (weakDomains.length ? ` · Weak: ${weakDomains.map(d => _ppHumanDomain(d.domain)).join(", ")}` : "");

    const cards = results.map(r => {
        const isWeak = (r.estimated_grade || "G3") < suggested;
        return `
            <div class="pp-mplace-card ${isWeak ? "is-weak" : ""}">
                <div class="pp-mplace-label">${escapeHtml(_ppHumanDomain(r.domain))}</div>
                <div class="pp-mplace-num">
                    <span class="mono pp-mplace-grade ${isWeak ? "is-weak" : ""}">${escapeHtml(r.estimated_grade || "—")}</span>
                    <span class="mono pp-mplace-raw">${r.raw_score || 0}/${r.total_questions || 0}</span>
                </div>
                <div class="pp-mplace-bar">
                    <div class="pp-mplace-bar-fill ${isWeak ? "is-weak" : ""}" style="width:${((r.raw_score || 0) / (r.total_questions || 1) * 100).toFixed(0)}%"></div>
                </div>
            </div>`;
    }).join("");

    return `
        <div class="pp-panel">
            <div class="pp-panel-title">
                <div class="pp-panel-title-left">Placement Test · Suggested ${escapeHtml(suggested)}
                    <span class="pp-panel-sub">${escapeHtml(subText)}</span>
                </div>
            </div>
            <div class="pp-mplace-strip">${cards}</div>
        </div>`;
}

/** Human-readable domain label. @tag PARENT */
function _ppHumanDomain(slug) {
    if (!slug) return "—";
    return slug.split("_").map(w => w[0].toUpperCase() + w.slice(1)).join(" ");
}

/** Academy unit grid + current lesson stage chips. @tag PARENT MATH_ACADEMY */
function _ppMathUnitGrid(grade, units, summary) {
    const academy = summary.academy || {};
    const passedCount = academy.unit_tests_passed || 0;
    const totalUnits = units.length;
    const totalLessons = academy.total_lessons || 0;
    const doneLessons = academy.completed || 0;
    const weakAreas = (summary.weak_areas || []).map(w => w.lesson || "").filter(Boolean);
    const currentLessonIdx = academy.current_stage_idx ?? 2; // default to "try"
    const currentLessonLabel = academy.current_lesson_label || "";

    // Stage chips for current lesson
    const stageChips = _PP_MATH_STAGES.map((st, i) => {
        const isDone = i < currentLessonIdx;
        const isCurrent = i === currentLessonIdx;
        const cls = isDone ? "is-done" : isCurrent ? "is-current" : "";
        const label = st.replace("practice_", "R").replace("unit_test", "U-test");
        return `<div class="pp-stage-chip ${cls}">${isDone ? `<i data-lucide="check"></i>` : ""}${escapeHtml(label)}</div>${i < _PP_MATH_STAGES.length - 1 ? `<span class="pp-stage-arrow">→</span>` : ""}`;
    }).join("");

    // Per-unit cards — units is now [{name, is_locked, unit_test_passed}]
    const cards = units.map(u => {
        const unitKey = (typeof u === 'object' && u.name) ? u.name : u; // compat
        const isLocked = typeof u === 'object' ? !!u.is_locked : false;
        const unitPassed = typeof u === 'object' ? !!u.unit_test_passed : false;
        const num = unitKey.split("_")[0]; // e.g. "U1" or "misconceptions"
        const label = unitKey.split("_").slice(1).map(w => w[0]?.toUpperCase() + w.slice(1)).join(" ") || unitKey;
        const isWeak = weakAreas.some(l => l.startsWith(unitKey + "_") || l.startsWith(unitKey.replace("U", "L")));
        return `
            <div class="pp-unit-card ${isWeak ? "pp-unit-card--weak" : ""} ${isLocked ? "pp-unit-card--locked" : ""}">
                <div class="pp-unit-card-head">
                    <span class="mono pp-unit-key">${escapeHtml(num.toUpperCase())}</span>
                    ${isLocked ? `<i data-lucide="lock" class="pp-unit-icon-lock"></i>` : unitPassed ? `<i data-lucide="check-circle" class="pp-unit-icon-done"></i>` : isWeak ? `<i data-lucide="alert-triangle" class="pp-unit-icon-weak"></i>` : ""}
                </div>
                <div class="pp-unit-name">${escapeHtml(label || unitKey)}</div>
                <div class="pp-unit-row">
                    <div class="pp-unit-bar"><div class="pp-unit-bar-fill" style="width:${unitPassed ? 100 : 0}%"></div></div>
                </div>
            </div>`;
    }).join("");

    return `
        <div class="pp-panel">
            <div class="pp-panel-title">
                <div class="pp-panel-title-left">${escapeHtml(grade)} Academy · unit-by-unit
                    <span class="pp-panel-sub">${doneLessons}/${totalLessons} lessons · ${passedCount} unit tests passed</span>
                </div>
            </div>
            <div class="pp-current-lesson">
                <div class="pp-mini-kick">Current lesson${currentLessonLabel ? " · " + escapeHtml(currentLessonLabel) : ""}</div>
                <div class="pp-stage-chips">${stageChips}</div>
            </div>
            <div class="pp-unit-grid">${cards || `<p class="pp-text-hint">No units found.</p>`}</div>
            <div class="pp-unit-legend">
                <span><i data-lucide="check-circle" class="pp-legend-ok"></i>Unit-test passed</span>
                <span><span class="pp-legend-sq pp-legend-sq--math"></span>Currently working</span>
                <span><i data-lucide="alert-triangle" class="pp-legend-warn"></i>Weak area</span>
                <span><i data-lucide="lock" class="pp-legend-mute"></i>Locked</span>
            </div>
        </div>`;
}

/** Academy / Daily / Kangaroo / My Problems 4-row card. @tag PARENT MATH */
function _ppMathRowsCard(summary) {
    const academy = summary.academy || {};
    const dailyArr = summary.daily_recent || [];
    const dailyToday = dailyArr[0] || {};
    const kang = (summary.kangaroo || [])[0] || {};
    const wrong = summary.wrong_review || {};

    const todayIso = new Date().toISOString().slice(0, 10);
    const dailyDoneCount = dailyArr.slice(0, 7).filter(d => d.completed_at).length;
    const dailyOf = Math.min(dailyArr.length, 7);
    const dailyDoneSub = dailyOf > 0 ? ` · ${dailyDoneCount}/${dailyOf} last ${dailyOf}d` : "";

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
                <div class="pp-panel-title-left">Academy · Daily · Kangaroo</div>
            </div>
            <div class="pp-rev-list">
                ${row("Academy",         `${academy.completed || 0}/${academy.total_lessons || 0}`,
                       `Pass rate ${Math.round(academy.eq_pass_rate || 0)}% · ${academy.unit_tests_passed || 0} unit tests passed`,
                       "var(--math-primary)")}
                ${row("Daily Challenge", dailyToday.score != null ? `${dailyToday.score}/${dailyToday.total || 5}` : "—",
                       dailyToday.completed_at
                           ? `${dailyToday.completed_at.slice(0,10) === todayIso ? "Completed today" : `Done ${dailyToday.completed_at.slice(0,10)}`}${dailyDoneSub}`
                           : `Pending today${dailyDoneSub}`,
                       dailyToday.completed_at ? "var(--ok)" : "var(--warn)")}
                ${row("Kangaroo",        `${kang.score || 0}/${kang.total || 0}`,
                       `Recent ${escapeHtml(kang.set_id || "—")} · ${kang.completed_at?.slice(0,10) || ""}`)}
                ${row("My Problems",     wrong.pending || 0,
                       `Mastered ${wrong.mastered || 0}`,
                       "var(--review-primary)")}
            </div>
        </div>`;
}

/** Fact Fluency 2-col grid with phase pill per set. @tag PARENT MATH_FLUENCY */
function _ppMathFluencyCard(fluencyList) {
    if (!fluencyList.length) {
        return `
            <div class="pp-panel">
                <div class="pp-panel-title">
                    <div class="pp-panel-title-left">Fact Fluency</div>
                </div>
                <p class="pp-text-hint">No fluency data yet.</p>
            </div>`;
    }
    const mastered = fluencyList.filter(s => s.phase === "C").length;
    const total = fluencyList.length;

    const cells = fluencyList.map(s => {
        const phaseCls = s.phase === "C" ? "is-c" : s.phase === "B" ? "is-b" : "is-a";
        const isMastered = s.phase === "C";
        return `
            <div class="pp-fluency-cell ${isMastered ? "is-mastered" : ""}">
                <span class="pp-fluency-phase mono ${phaseCls}">${escapeHtml(s.phase || "A")}</span>
                <span class="pp-fluency-name">${escapeHtml(_ppHumanDomain(s.fact_set))}</span>
                <span class="mono pp-fluency-acc">${Math.round(s.accuracy_pct || 0)}%</span>
                ${isMastered ? `<i data-lucide="check-circle" class="pp-fluency-check"></i>` : ""}
            </div>`;
    }).join("");

    return `
        <div class="pp-panel">
            <div class="pp-panel-title">
                <div class="pp-panel-title-left">Fact Fluency · ${mastered}/${total} mastered
                    <span class="pp-panel-sub">Phase A → B → C (mastery)</span>
                </div>
            </div>
            <div class="pp-fluency-grid">${cells}</div>
        </div>`;
}

/** Math Glossary card with ring. @tag PARENT MATH_GLOSSARY */
function _ppMathGlossaryCard(summary) {
    const viewed = summary.glossary_viewed || 0;
    const total = summary.glossary_total || 92;
    const pct = total ? Math.round((viewed / total) * 100) : 0;
    return `
        <div class="pp-panel">
            <div class="pp-panel-title">
                <div class="pp-panel-title-left">Math Glossary
                    <span class="pp-panel-sub">G3 terms · ${viewed}/${total} viewed</span>
                </div>
            </div>
            <div class="pp-glossary-flex">
                ${_ppRing(viewed, total, { size: 56, stroke: 6, color: "var(--math-primary)", label: `${pct}%` })}
                <div class="pp-glossary-text">
                    <div class="mono pp-glossary-num">${viewed}<span class="pp-glossary-num-sub">/${total} terms</span></div>
                    <div class="pp-glossary-hint">Glossary helps with placement-test weak domains.</div>
                </div>
            </div>
        </div>`;
}

/** Spaced Review card. @tag PARENT MATH_REVIEW */
function _ppMathSpacedReviewCard(sr) {
    const due = sr.due_today || 0;
    const done = sr.reviewed_today || 0;
    const total = due + done || 1;
    const pct = (done / total) * 100;

    return `
        <div class="pp-panel">
            <div class="pp-panel-title">
                <div class="pp-panel-title-left">Spaced Review
                    <span class="pp-panel-sub">Mastered problems on a SM-2 schedule</span>
                </div>
            </div>
            <div class="pp-sr-flex">
                <div>
                    <div class="mono pp-sr-big">${due}</div>
                    <div class="pp-sr-big-sub">due today</div>
                </div>
                <div class="pp-sr-right">
                    <div class="pp-sr-row">
                        <span>Done today</span>
                        <span class="mono"><b class="pp-sr-strong">${done}</b> / ${due + done}</span>
                    </div>
                    <div class="pp-sr-bar"><div class="pp-sr-bar-fill" style="width:${pct.toFixed(0)}%"></div></div>
                    <div class="pp-sr-hint">Intervals: 1d → 3d → 7d → 21d. One correct review = mastered.</div>
                </div>
            </div>
        </div>`;
}

window._ppMathSummary = _ppMathSummary;
