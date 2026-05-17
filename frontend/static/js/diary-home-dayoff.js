/* ================================================================
   diary-home-dayoff.js — Diary Home · Day Off request modal
   Section: Diary
   Dependencies: diary-home.js (_DH_DAYOFF_MAX, _dhState, _dhIcon, _dhRefreshIcons,
                                 _dhLoadHomeData, escapeHtml)
   API endpoints: POST /api/day-off/request
   ================================================================ */

/* ── Day Off Request modal (Home) ──────────────────────────────── */

/** Modal markup — hidden by default, rendered inside _renderDiaryHome. */
function _dhDayOffModalHTML() {
    return `
        <div class="dh-modal-backdrop is-hidden" id="dh-dayoff-modal" role="dialog"
             aria-modal="true" aria-label="Request a day off"
             onclick="_dhCloseDayOffModalIfBackdrop(event)">
            <div class="dh-modal" onclick="event.stopPropagation()" lang="en">
                <span class="dh-washi" style="top:-9px;left:32px;width:90px;background:var(--arcade-soft);transform:rotate(-4deg);"></span>
                <div class="dh-modal-head">
                    <div class="dh-modal-icon">${_dhIcon("coffee", 17)}</div>
                    <div>
                        <div class="dh-modal-title">Take a day off?</div>
                        <div class="dh-modal-sub" id="dh-dayoff-sub">— left this month</div>
                    </div>
                </div>
                <div class="dh-modal-field">
                    <label class="dh-modal-label" for="dh-dayoff-start">Single day or range?</label>
                    <div class="dh-modal-range">
                        <input class="dh-modal-input" type="date" id="dh-dayoff-start" min="" lang="en"/>
                        <span class="dh-modal-range-sep">→</span>
                        <input class="dh-modal-input" type="date" id="dh-dayoff-end" min="" lang="en"
                               placeholder="optional"/>
                    </div>
                    <div class="dh-modal-help">Leave the second date empty for a single day.</div>
                </div>
                <div class="dh-modal-field">
                    <label class="dh-modal-label" for="dh-dayoff-reason">
                        Why? <span class="dh-modal-label-hint">(optional)</span>
                    </label>
                    <input class="dh-modal-input" type="text" id="dh-dayoff-reason"
                           maxlength="60" placeholder="e.g. Family trip, feeling sick"/>
                </div>
                <div class="dh-modal-note">
                    ${_dhIcon("heart", 13)}
                    Mom or Dad will see your request and say OK.
                </div>
                <div class="dh-modal-error" id="dh-dayoff-error"></div>
                <div class="dh-modal-actions">
                    <button class="dh-modal-cancel" type="button" onclick="_dhCloseDayOffModal()">Cancel</button>
                    <button class="dh-modal-submit" id="dh-dayoff-submit" type="button"
                            onclick="_dhSubmitDayOff()" disabled aria-disabled="true">
                        ${_dhIcon("check", 12)} Send request
                    </button>
                </div>
            </div>
        </div>`;
}

function _dhOpenDayOffModal() {
    const monthIso = new Date().toISOString().slice(0, 7);
    const used = (_dhState.dayOffs || [])
        .filter(r => (r.request_date || "").startsWith(monthIso))
        .filter(r => {
            const s = (r.status || "").toLowerCase();
            return s === "approved" || s === "pending";
        }).length;
    const left = Math.max(_DH_DAYOFF_MAX - used, 0);
    if (left <= 0) return;

    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    const minDate = tomorrow.toISOString().slice(0, 10);

    const modal = document.getElementById("dh-dayoff-modal");
    const startEl = document.getElementById("dh-dayoff-start");
    const endEl = document.getElementById("dh-dayoff-end");
    const reasonEl = document.getElementById("dh-dayoff-reason");
    const subEl = document.getElementById("dh-dayoff-sub");
    const errEl = document.getElementById("dh-dayoff-error");
    const submitEl = document.getElementById("dh-dayoff-submit");
    if (!modal) return;

    [startEl, endEl].forEach(el => {
        if (!el) return;
        el.value = "";
        el.min = minDate;
        el.removeEventListener("input", _dhDayOffValidate);
        el.addEventListener("input", _dhDayOffValidate);
    });
    if (reasonEl) reasonEl.value = "";
    if (subEl) subEl.textContent = `${left} / ${_DH_DAYOFF_MAX} left this month`;
    if (errEl) errEl.textContent = "";
    if (submitEl) {
        submitEl.disabled = true;
        submitEl.setAttribute("aria-disabled", "true");
        submitEl.innerHTML = `${_dhIcon("check", 12)} Send request`;
    }

    modal.classList.remove("is-hidden");
    _dhState.modal.open = true;
    document.addEventListener("keydown", _dhDayOffKey);
    _dhRefreshIcons();
    setTimeout(() => startEl && startEl.focus(), 30);
}

function _dhDayOffValidate() {
    const startEl = document.getElementById("dh-dayoff-start");
    const endEl   = document.getElementById("dh-dayoff-end");
    const submitEl = document.getElementById("dh-dayoff-submit");
    const errEl   = document.getElementById("dh-dayoff-error");
    if (!submitEl) return;
    const start = startEl && startEl.value;
    const end   = endEl   && endEl.value;
    let ok = !!start;
    let err = "";
    if (start && end && end < start) {
        ok = false;
        err = "End date must be on/after the start.";
    }
    // Range size limit: don't let one request blow past the monthly quota.
    if (ok && start && end) {
        const days = _dhDayCount(start, end);
        if (days > _DH_DAYOFF_MAX) {
            ok = false;
            err = `Range too long — max ${_DH_DAYOFF_MAX} days.`;
        }
    }
    if (errEl) errEl.textContent = err;
    submitEl.disabled = !ok;
    submitEl.setAttribute("aria-disabled", String(!ok));
}

/** Inclusive day count between two ISO yyyy-mm-dd strings. */
function _dhDayCount(start, end) {
    const a = new Date(start + "T00:00:00");
    const b = new Date(end   + "T00:00:00");
    const ms = b - a;
    if (Number.isNaN(ms) || ms < 0) return 0;
    return Math.round(ms / 86400000) + 1;
}

/** Build ISO yyyy-mm-dd strings from start..end inclusive. */
function _dhExpandRange(start, end) {
    const out = [];
    const a = new Date(start + "T00:00:00");
    const b = new Date((end || start) + "T00:00:00");
    if (Number.isNaN(a.getTime()) || Number.isNaN(b.getTime())) return out;
    for (let d = new Date(a); d <= b; d.setDate(d.getDate() + 1)) {
        out.push(d.toISOString().slice(0, 10));
    }
    return out;
}

/** Render a compact history list inside the modal. */
function _dhRenderDayOffHistory() {
    const wrap = document.getElementById("dh-dayoff-history");
    if (!wrap) return;
    const rows = (_dhState.dayOffs || []).slice(0, 5);
    if (!rows.length) { wrap.innerHTML = ""; return; }
    const LABEL = { pending: "Pending", approved: "Approved", denied: "Denied" };
    wrap.innerHTML = `
        <div class="dh-modal-history-label">Recent requests</div>
        <div class="dh-modal-history-list">
            ${rows.map(r => {
                const s = (r.status || "pending").toLowerCase();
                return `<div class="dh-modal-history-row">
                    <span class="dh-modal-history-date">${escapeHtml(r.request_date || "")}</span>
                    <span class="dh-modal-history-status ${s}">${LABEL[s] || s}</span>
                </div>`;
            }).join("")}
        </div>`;
}

function _dhCloseDayOffModal() {
    const modal = document.getElementById("dh-dayoff-modal");
    if (modal) modal.classList.add("is-hidden");
    _dhState.modal.open = false;
    document.removeEventListener("keydown", _dhDayOffKey);
}

function _dhCloseDayOffModalIfBackdrop(e) {
    if (e.target && e.target.id === "dh-dayoff-modal") _dhCloseDayOffModal();
}

function _dhDayOffKey(e) {
    if (e.key === "Escape" && _dhState.modal.open) _dhCloseDayOffModal();
}

async function _dhSubmitDayOff() {
    const startEl  = document.getElementById("dh-dayoff-start");
    const endEl    = document.getElementById("dh-dayoff-end");
    const reasonEl = document.getElementById("dh-dayoff-reason");
    const errEl    = document.getElementById("dh-dayoff-error");
    const submitEl = document.getElementById("dh-dayoff-submit");
    if (!startEl || !startEl.value) return;
    const start  = startEl.value;
    const end    = (endEl && endEl.value) || start;
    const dates  = _dhExpandRange(start, end);
    if (!dates.length) return;
    // Backend requires non-empty reason; provide a polite default if blank.
    const reason = (reasonEl && reasonEl.value.trim()) || "Personal day";

    if (errEl) errEl.textContent = "";
    if (submitEl) {
        submitEl.disabled = true;
        submitEl.innerHTML = `${_dhIcon("check", 12)} Sending…`;
        _dhRefreshIcons();
    }

    // Submit each day separately — the existing backend stores one row per
    // date and rejects duplicates with 409. We stop on the first hard
    // failure (other than 409) so the user can fix and retry.
    const failed = [];
    for (const d of dates) {
        try {
            const res = await fetch("/api/day-off/request", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ request_date: d, reason }),
            });
            if (!res.ok && res.status !== 409) {
                let msg = `Couldn't send ${d}.`;
                try {
                    const j = await res.json();
                    if (j && j.detail) msg = j.detail;
                } catch (_) {}
                failed.push({ d, msg });
                break;
            }
        } catch (_) {
            failed.push({ d, msg: `Network error on ${d}.` });
            break;
        }
    }
    if (failed.length) {
        if (errEl) errEl.textContent = failed[0].msg;
        if (submitEl) {
            submitEl.disabled = false;
            submitEl.innerHTML = `${_dhIcon("check", 12)} Send request`;
            _dhRefreshIcons();
        }
        return;
    }
    _dhCloseDayOffModal();
    _dhLoadHomeData();
}
