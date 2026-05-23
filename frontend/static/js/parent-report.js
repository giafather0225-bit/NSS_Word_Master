/* ================================================================
   parent-report.js — Parent Dashboard: Weekly Report settings
   Section: Parent
   Dependencies: core.js, parent-panel.js
   API endpoints: GET/POST /api/parent/report/schedule,
                  POST /api/parent/report/send,
                  GET  /api/parent/report/preview
   ================================================================ */

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

window._ppSaveReportSchedule = _ppSaveReportSchedule;
window._ppSendReportNow      = _ppSendReportNow;
window._ppPreviewReport      = _ppPreviewReport;
