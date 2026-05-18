/* ================================================================
   parent-reading.js — Parent Dashboard: Reading tab (English + CKLA sub-tabs)
   Section: Parent
   Dependencies: core.js, parent-panel.js (_ppEmpty), parent-ckla.js (_ppCKLA)
   API endpoints: /api/parent/word-stats, /api/parent/stage-stats
   ================================================================ */

let _ppReadingSubTab = "english";

/** Reading tab entry — renders sub-tab bar then the active sub-tab content. @tag PARENT */
async function _ppReading(body) {
    _ppReadingSubTab = "english";
    body.innerHTML = `
        <div class="pp-subtab-nav" id="pp-reading-subtabs">
            <button class="pp-subtab-btn active" data-subtab="english" onclick="_ppReadingSwitch('english', this)">
                <i data-lucide="book-open" style="width:14px;height:14px"></i> English
            </button>
            <button class="pp-subtab-btn" data-subtab="ckla" onclick="_ppReadingSwitch('ckla', this)">
                <i data-lucide="layers" style="width:14px;height:14px"></i> CKLA
            </button>
        </div>
        <div id="pp-reading-content"><p class="pp-loading-center">Loading…</p></div>`;
    if (typeof lucide !== "undefined") lucide.createIcons();
    await _ppReadingEnglish(document.getElementById("pp-reading-content"));
}

/** Switch between Reading sub-tabs. @tag PARENT */
async function _ppReadingSwitch(sub, btn) {
    if (_ppReadingSubTab === sub) return;
    _ppReadingSubTab = sub;
    document.querySelectorAll(".pp-subtab-btn").forEach(b => b.classList.toggle("active", b.dataset.subtab === sub));
    const content = document.getElementById("pp-reading-content");
    if (!content) return;
    content.innerHTML = `<p class="pp-loading-center">Loading…</p>`;
    if (sub === "english") {
        await _ppReadingEnglish(content);
    } else {
        if (typeof _ppCKLA === "function") {
            await _ppCKLA(content);
        } else {
            content.innerHTML = `<p style="color:var(--color-error);padding:20px">CKLA module not loaded.</p>`;
        }
    }
}

/** English sub-tab: word stats + stage performance. @tag PARENT WORD_STATS */
async function _ppReadingEnglish(el) {
    if (!el) return;
    try {
        const [ws, stg] = await Promise.all([
            apiFetchJSON("/api/parent/word-stats"),
            apiFetchJSON("/api/parent/stage-stats"),
        ]);

        const words = ws.top_wrong || [];
        const totalAttempts = words.reduce((a, w) => a + (w.attempts || 0), 0);
        const totalWrong    = words.reduce((a, w) => a + (w.wrong_count || 0), 0);
        const overallAcc    = totalAttempts ? Math.round((1 - totalWrong / totalAttempts) * 100) : 0;
        const stages        = stg.stages || {};
        const totalStageDone = Object.values(stages).reduce((a, s) => a + (s.completions || 0), 0);

        const summary = `
            <div class="pp-stats pp-english-stats pp-stats--mb20">
                <div class="pp-stat"><div class="pp-stat-num">${words.length}</div><div class="pp-stat-label">Tracked Words</div></div>
                <div class="pp-stat"><div class="pp-stat-num">${overallAcc}%</div><div class="pp-stat-label">Overall Accuracy</div></div>
                <div class="pp-stat"><div class="pp-stat-num">${totalStageDone}</div><div class="pp-stat-label">Stage Completions</div></div>
            </div>`;

        const wordRows = words.length
            ? words.map(w =>
                `<tr><td><strong>${escapeHtml(w.word)}</strong></td><td>${escapeHtml(w.lesson)}</td><td class="pp-td-error-right">${w.wrong_count}</td><td class="pp-td-right">${Math.round(w.accuracy * 100)}%</td></tr>`
              ).join("")
            : `<tr><td colspan="4">${_ppEmpty("file-search-2", "No missed words tracked yet.", "Words appear after Gia misses them in Word Match or Spelling.")}</td></tr>`;

        const STAGE_META = {
            preview:    { name: "Preview",    icon: "eye"            },
            word_match: { name: "Word Match", icon: "shuffle"        },
            fill_blank: { name: "Fill Blank", icon: "type"           },
            spelling:   { name: "Spelling",   icon: "spell-check"    },
            sentence:   { name: "Sentence",   icon: "pen-line"       },
            final_test: { name: "Final Test", icon: "graduation-cap" },
        };
        const STAGE_ORDER = ["preview", "word_match", "fill_blank", "spelling", "sentence", "final_test"];
        const stageList = STAGE_ORDER
            .filter(k => stages[k])
            .map(k => {
                const s = stages[k];
                const meta = STAGE_META[k] || { name: k, icon: "circle" };
                const acc = Math.round(s.avg_accuracy || 0);
                const accClass = acc >= 90 ? "good" : acc >= 70 ? "ok" : "low";
                return `
                    <div class="pp-stage-card">
                        <div class="pp-stage-head">
                            <i data-lucide="${meta.icon}" style="width:16px;height:16px"></i>
                            <span class="pp-stage-name">${meta.name}</span>
                            <span class="pp-stage-acc pp-stage-acc--${accClass}">${acc}%</span>
                        </div>
                        <div class="pp-stage-row"><span>Avg Time</span><strong>${Math.round(s.avg_time_sec / 60)}m</strong></div>
                        <div class="pp-stage-row"><span>Completions</span><strong>${s.completions}x</strong></div>
                    </div>`;
            }).join("");

        el.innerHTML = `
            ${summary}
            <div class="pp-grid-2">
                <div>
                    <div class="pp-section-title pp-section-title--no-top">Most Missed Words</div>
                    <div class="pp-table-wrap">
                        <table class="pp-log-table">
                            <thead><tr>
                                <th>Word</th><th>Lesson</th>
                                <th class="pp-th-right">Wrong</th>
                                <th class="pp-th-right">Accuracy</th>
                            </tr></thead>
                            <tbody>${wordRows}</tbody>
                        </table>
                    </div>
                </div>
                <div>
                    <div class="pp-section-title pp-section-title--no-top">Stage Performance</div>
                    <div class="pp-stage-list">${stageList || _ppEmpty("layers", "No stages completed yet.", "Each finished stage feeds accuracy and time stats.")}</div>
                </div>
            </div>`;

        if (typeof lucide !== "undefined") lucide.createIcons();
    } catch (_) {
        el.innerHTML = `<p style="color:var(--color-error);padding:20px">Failed to load English stats.</p>`;
    }
}

window._ppReading       = _ppReading;
window._ppReadingSwitch = _ppReadingSwitch;
