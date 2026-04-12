const CURRENT_SUBJECT = "vocabulary";

function getCurrentPin() {
    // Default PIN is 1234, but Parent can change it and it is stored locally.
    return window.localStorage.getItem("parent_pin") || "1234";
}

function $(id) {
    return document.getElementById(id);
}

function showAdminMsg(nearEl, msg, isError) {
    const key = '_adminMsg';
    let el = nearEl[key];
    if (!el) {
        el = document.createElement('p');
        el.style.cssText = 'margin:4px 0 0;font-size:13px;';
        nearEl.insertAdjacentElement('afterend', el);
        nearEl[key] = el;
    }
    el.style.color = isError ? 'var(--danger, #FF3B30)' : 'var(--success, #34C759)';
    el.textContent = msg;
    clearTimeout(el._t);
    el._t = setTimeout(() => { el.textContent = ''; }, 3000);
}

function escapeHtml(s) {
    return String(s)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;");
}

function lessonSelected() {
    const el = $("parent-lesson");
    const raw = el ? el.value.trim() : "Lesson_09";
    if (raw.startsWith("Lesson_")) return raw;
    if (/^\d+$/.test(raw)) return `Lesson_${String(parseInt(raw, 10)).padStart(2, "0")}`;
    return `Lesson_${raw}`;
}

function refreshChildLink() {
    const lesson = encodeURIComponent(lessonSelected());
    const link = $("btn-child");
    if (link) link.href = `/child?lesson=${lesson}`;
}

document.addEventListener("DOMContentLoaded", () => {
    const pinOverlay = $("pin-overlay");
    const parentContent = $("parent-content");
    const pinInput = $("pin-input");
    const pinError = $("pin-error");

    window.localStorage.removeItem("parent_unlocked");
    const saved = window.sessionStorage.getItem("parent_unlocked") === "1";
    if (saved) {
        pinOverlay.classList.add("hidden");
        parentContent.style.display = "block";
    }

    $("btn-pin").addEventListener("click", () => {
        const val = (pinInput.value || "").trim();
        if (!val || val !== getCurrentPin()) {
            pinError.classList.remove("hidden");
            return;
        }
        window.sessionStorage.setItem("parent_unlocked", "1");
        pinOverlay.classList.add("hidden");
        pinError.classList.add("hidden");
        parentContent.style.display = "block";
        refreshChildLink();
        loadDashboardStats();
    });

    $("btn-save-pin").addEventListener("click", () => {
        const currentPinInput = ($("pin-current-input") && $("pin-current-input").value || "").trim();
        const v = ($("pin-change-input").value || "").trim();
        const status = $("pin-change-status");
        // 기존 PIN 확인 필수
        if (currentPinInput !== getCurrentPin()) {
            status.textContent = "Current PIN is incorrect.";
            status.style.color = "#e74c3c";
            status.classList.remove("hidden");
            return;
        }
        if (!/^\d{4,8}$/.test(v)) {
            status.textContent = "New PIN must be 4-8 digits.";
            status.style.color = "#e74c3c";
            status.classList.remove("hidden");
            return;
        }
        window.localStorage.setItem("parent_pin", v);
        if ($("pin-current-input")) $("pin-current-input").value = "";
        $("pin-change-input").value = "";
        status.textContent = "PIN saved. ✓";
        status.style.color = "#27ae60";
        status.classList.remove("hidden");
    });

    $("parent-lesson").addEventListener("change", () => {
        refreshChildLink();
        loadDashboardStats();
    });
    $("parent-lesson").addEventListener("keyup", () => {
        refreshChildLink();
    });

    $("btn-dad-settings").addEventListener("click", () => $("admin-modal").classList.remove("hidden"));
    $("admin-close").addEventListener("click", () => $("admin-modal").classList.add("hidden"));









    async function loadDashboardStats() {
        const lesson = encodeURIComponent(lessonSelected());
        try {
            const [resR, resS, resProg] = await Promise.all([
                fetch("/api/rewards"),
                fetch("/api/schedules"),
                fetch(`/api/study/${CURRENT_SUBJECT}/${lesson}`),
            ]);
            const rewards = await resR.json();
            const schedules = await resS.json();
            const data = await resProg.json();
            $("dash-streak").textContent = data.progress ? data.progress.best_streak : 0;

            const scheduleList = $("schedule-list");
            scheduleList.innerHTML = schedules.length
                ? ""
                : '<p class="empty-txt">No schedules.</p>';
            schedules.forEach((s) => {
                const div = document.createElement("div");
                div.className = "sch-item";
                const [fy, fm, fd] = s.test_date.split("-").map(Number);
                const today = new Date();
                const targetMs = Date.UTC(fy, fm - 1, fd);
                const todayMs = Date.UTC(today.getFullYear(), today.getMonth(), today.getDate());
                const diffDays = Math.round((targetMs - todayMs) / (1000 * 60 * 60 * 24));
                const dDayHtml =
                    diffDays > 0
                        ? `<span class="badge-dday">D-${diffDays}</span>`
                        : diffDays === 0
                          ? `<span class="badge-dday today">D-Day!</span>`
                          : `<span class="badge-dday past">D+${Math.abs(diffDays)}</span>`;
                div.innerHTML = `<div class="sch-header"><strong>${escapeHtml(s.test_date)}</strong> ${dDayHtml}</div><span>${escapeHtml(s.memo)}</span><button class="del-btn" onclick="deleteSchedule(${s.id})">&times;</button>`;
                scheduleList.appendChild(div);
            });

            const rewardList = $("reward-list");
            rewardList.innerHTML = rewards.length ? "" : '<p class="empty-txt">No rewards.</p>';
            rewards.forEach((r) => {
                const div = document.createElement("div");
                div.className = `reward-item ${r.is_earned ? "earned" : ""}`;
                div.onclick = (e) => {
                    if (e.target.classList.contains("del-btn")) return;
                    if (!r.is_earned) toggleReward(r.id);
                };
                div.innerHTML = `<h4>${escapeHtml(r.title)}</h4><p>${escapeHtml(r.description)}</p><button class="del-btn" onclick="deleteReward(${r.id})">&times;</button>`;
                rewardList.appendChild(div);
            });
        } catch {
            /* ignore */
        }
    }

    // Reward burst on perfect clear
    const params = new URLSearchParams(window.location.search);
    if (params.get("cleared") === "1") {
        // Earn all rewards once
        fetch("/api/rewards/earn_all", { method: "POST" }).catch(() => {});
        $("reward-burst-modal").classList.remove("hidden");
        $("btn-reward-burst-ok").onclick = () => {
            $("reward-burst-modal").classList.add("hidden");
            window.history.replaceState({}, "", "/");
        };
    }

    refreshChildLink();
    loadDashboardStats();
});

