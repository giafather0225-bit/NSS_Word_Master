/* ================================================================
   parent-textbooks.js — Parent Dashboard Textbooks tab renderer
   Section: Parent
   Dependencies: core.js (escapeHtml), parent-panel.js
   API endpoints: /api/dashboard/stats, /api/dashboard/textbook/{name}
   ================================================================ */

/** Render textbook accordion with lesson breakdown. @tag PARENT WORD_STATS */
async function _ppTextbooks(body) {
    try {
        const data = await apiFetchJSON("/api/dashboard/stats");
        const tbs  = (data.textbooks || []).filter(tb => tb.name.toLowerCase() !== 'my_words');

        if (!tbs.length) {
            body.innerHTML = `<p style="text-align:center;color:var(--text-secondary);padding:40px">No textbooks found.</p>`;
            return;
        }

        const summary = `
            <div class="pp-stats" style="grid-template-columns:repeat(3,1fr);margin-bottom:20px">
                <div class="pp-stat"><div class="pp-stat-num">${data.total_words || 0}</div><div class="pp-stat-label">Total Words</div></div>
                <div class="pp-stat"><div class="pp-stat-num">${data.textbook_count || 0}</div><div class="pp-stat-label">Textbooks</div></div>
                <div class="pp-stat"><div class="pp-stat-num">${data.lesson_count || 0}</div><div class="pp-stat-label">Lessons</div></div>
            </div>`;

        const rows = tbs.map((tb, i) => `
            <div style="border-bottom:1px solid var(--color-primary-light)">
                <div style="display:flex;align-items:center;gap:12px;padding:14px 4px;cursor:pointer"
                     onclick="_ppTbToggle('ppTb${i}', '${escapeHtml(tb.name)}')">
                    <span style="font-size:20px">📚</span>
                    <div style="flex:1;min-width:0">
                        <div style="font-size:15px;font-weight:600;color:var(--text-primary)">${escapeHtml(tb.name)}</div>
                        <div style="font-size:12px;color:var(--text-secondary);margin-top:2px">${tb.lessons||0} lessons · ${tb.words||0} words</div>
                    </div>
                    <span id="ppTbArrow${i}" style="font-size:18px;color:var(--text-secondary);transition:transform 0.2s">›</span>
                </div>
                <div id="ppTb${i}" style="display:none;padding:0 0 8px 52px"></div>
            </div>`).join("");

        const addBtn = `
            <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:16px">
                <div class="pp-section-title" style="margin:0">Textbook Overview</div>
                <button class="pp-btn primary" style="font-size:12px;padding:6px 14px"
                        onclick="window.open('/ingest','_blank')">+ Add Textbook</button>
            </div>`;
        body.innerHTML = summary + addBtn + `<div>${rows}</div>`;
    } catch (err) {
        console.error("[parent-textbooks] load failed:", err);
        body.innerHTML = `<p style="color:var(--color-error);padding:20px">Failed to load.</p>`;
    }
}

/** Toggle textbook accordion and lazy-load lessons. @tag PARENT WORD_STATS */
async function _ppTbToggle(panelId, tbName) {
    const panel = document.getElementById(panelId);
    const idx   = panelId.replace("ppTb", "");
    const arrow = document.getElementById(`ppTbArrow${idx}`);
    if (!panel) return;

    const isOpen = panel.style.display !== "none";
    panel.style.display = isOpen ? "none" : "block";
    if (arrow) arrow.style.transform = isOpen ? "" : "rotate(90deg)";
    if (isOpen || panel.dataset.loaded) return;

    panel.dataset.loaded = "1";
    panel.innerHTML = `<p style="font-size:13px;color:var(--text-secondary);padding:4px 0">Loading…</p>`;
    try {
        const data = await apiFetchJSON("/api/dashboard/textbook/" + encodeURIComponent(tbName));
        const lessons = data.lessons || [];
        if (!lessons.length) {
            panel.innerHTML = `<p style="font-size:13px;color:var(--text-secondary);padding:4px 0">No lessons.</p>`;
            return;
        }
        panel.innerHTML = lessons.map(l => `
            <div style="display:flex;align-items:center;gap:10px;padding:8px 12px;border-radius:var(--radius-sm);transition:background 0.15s"
                 onmouseover="this.style.background='var(--color-primary-light)'" onmouseout="this.style.background=''">
                <span style="font-size:13px;font-weight:500;color:var(--text-primary);flex:1">${escapeHtml(l.lesson)}</span>
                <span style="font-size:12px;color:var(--text-secondary)">${l.words||0} words</span>
            </div>`).join("");
    } catch (err) {
        console.error("[parent-textbooks] lessons failed:", err);
        panel.innerHTML = `<p style="font-size:13px;color:var(--color-error);padding:4px 0">Failed to load.</p>`;
    }
}

window._ppTextbooks = _ppTextbooks;
window._ppTbToggle  = _ppTbToggle;
