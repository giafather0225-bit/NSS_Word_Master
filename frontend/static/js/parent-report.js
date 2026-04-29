/* ================================================================
   parent-report.js — Parent Dashboard: Weekly Report settings
   Section: Parent
   Dependencies: core.js, parent-panel.js
   API endpoints: GET/POST /api/parent/report/schedule,
                  POST /api/parent/report/send,
                  GET  /api/parent/report/preview
   ================================================================ */

const _PP_REPORT_DAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

/** Render Weekly Report form. @tag PARENT REPORT SETTINGS */
async function ppRenderReport(body) {
    try {
        const res  = await window._ppFetch("/api/parent/report/schedule");
        if (!res.ok) {
            body.innerHTML = `<p class="pp-form-hint">Schedule available after PIN re-verify.</p>`;
            return;
        }
        const data = await res.json();
        const dayOpts = _PP_REPORT_DAYS.map((d, i) =>
            `<option value="${i}" ${i === data.day_of_week ? "selected" : ""}>${d}</option>`
        ).join("");
        const emailHint = data.parent_email
            ? `Sends to <strong>${escapeHtml(data.parent_email)}</strong>`
            : `<span style="color:var(--color-error)">No parent email set — configure it in Account.</span>`;

        body.innerHTML = `
            <div class="pp-form-stack">
                <label class="pp-toggle-row">
                    <input id="pp-rep-enabled" type="checkbox" ${data.enabled ? "checked" : ""}>
                    <span>Enable weekly auto-send</span>
                </label>

                <div class="pp-form-row">
                    <div style="flex:1">
                        <label class="pp-form-label">Send on</label>
                        <select id="pp-rep-day" class="pp-input">${dayOpts}</select>
                    </div>
                    <div style="flex:2">
                        <label class="pp-form-label">Child name in report</label>
                        <input id="pp-rep-name" class="pp-input" type="text" maxlength="40"
                               value="${escapeHtml(data.child_name || "Gia")}">
                    </div>
                </div>

                <p class="pp-form-hint">${emailHint}</p>

                <div style="display:flex;gap:8px;flex-wrap:wrap">
                    <button class="pp-btn primary"   onclick="_ppSaveReportSchedule()">Save Schedule</button>
                    <button class="pp-btn secondary" onclick="_ppSendReportNow()">Send Now</button>
                    <button class="pp-btn secondary" onclick="_ppPreviewReport()">Preview Data</button>
                </div>
                <p id="pp-rep-msg" class="pp-form-msg"></p>
                <pre id="pp-rep-preview" class="pp-rep-preview" hidden></pre>
            </div>`;
    } catch (err) {
        console.error("[parent-report] load failed:", err);
        body.innerHTML = `<p style="color:var(--color-error);padding:12px">Failed to load report settings.</p>`;
    }
}

/** Save schedule (enabled + day + name). @tag PARENT REPORT */
async function _ppSaveReportSchedule() {
    const msg     = document.getElementById("pp-rep-msg");
    const enabled = document.getElementById("pp-rep-enabled")?.checked ?? false;
    const day     = parseInt(document.getElementById("pp-rep-day")?.value || "1", 10);
    const name    = (document.getElementById("pp-rep-name")?.value || "").trim();
    const setMsg = (text, kind) => {
        if (!msg) return;
        msg.textContent = text;
        msg.className = `pp-form-msg ${kind || ""}`;
    };
    if (!name) { setMsg("Child name required.", "error"); return; }
    try {
        const res = await window._ppFetch("/api/parent/report/schedule", {
            method:  "POST",
            headers: { "Content-Type": "application/json" },
            body:    JSON.stringify({ enabled, day_of_week: day, child_name: name }),
        });
        if (res.ok) setMsg("Schedule saved.", "success");
        else {
            const err = await res.json().catch(() => ({}));
            setMsg(err.detail || "Failed to save.", "error");
        }
    } catch (_) {
        setMsg("Network error.", "error");
    }
}

/** Send a report email immediately. @tag PARENT REPORT */
async function _ppSendReportNow() {
    const msg = document.getElementById("pp-rep-msg");
    const setMsg = (text, kind) => {
        if (!msg) return;
        msg.textContent = text;
        msg.className = `pp-form-msg ${kind || ""}`;
    };
    setMsg("Queuing report…", "");
    try {
        const res = await window._ppFetch("/api/parent/report/send", { method: "POST" });
        const j   = await res.json().catch(() => ({}));
        if (res.ok) setMsg(j.message || "Report queued.", "success");
        else        setMsg(j.detail  || "Failed to queue report.", "error");
    } catch (_) {
        setMsg("Network error.", "error");
    }
}

/** GET preview JSON and dump into the <pre> block. @tag PARENT REPORT */
async function _ppPreviewReport() {
    const out = document.getElementById("pp-rep-preview");
    const msg = document.getElementById("pp-rep-msg");
    if (!out) return;
    try {
        const res = await window._ppFetch("/api/parent/report/preview");
        if (!res.ok) {
            if (msg) { msg.textContent = "Preview failed."; msg.className = "pp-form-msg error"; }
            return;
        }
        const data = await res.json();
        out.textContent = JSON.stringify(data, null, 2);
        out.hidden = false;
        if (msg) { msg.textContent = ""; msg.className = "pp-form-msg"; }
    } catch (_) {
        if (msg) { msg.textContent = "Network error."; msg.className = "pp-form-msg error"; }
    }
}

window.ppRenderReport       = ppRenderReport;
window._ppSaveReportSchedule = _ppSaveReportSchedule;
window._ppSendReportNow      = _ppSendReportNow;
window._ppPreviewReport      = _ppPreviewReport;
