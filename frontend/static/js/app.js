/**
 * NSS Word Master — Dashboard (Magic Vault = ⚙️ 단일)
 */
const CURRENT_SUBJECT = "vocabulary";

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

function getLesson() {
    const el = document.getElementById("active-lesson");
    const raw = (el && el.value.trim()) || "Lesson_09";
    if (raw.startsWith("Lesson_")) return raw;
    if (/^\d+$/.test(raw)) return `Lesson_${String(parseInt(raw, 10)).padStart(2, "0")}`;
    return `Lesson_${raw}`;
}

function refreshStudyLinks() {
    const l = encodeURIComponent(getLesson());
    document.querySelectorAll(".link-study").forEach((a) => {
        a.href = `/study?lesson=${l}`;
    });
    document.querySelectorAll(".mono-lesson").forEach((s) => {
        s.textContent = getLesson();
    });
}

document.addEventListener("DOMContentLoaded", () => {
    const adminModal = document.getElementById("admin-modal");
    const lessonInput = document.getElementById("active-lesson");

    lessonInput.addEventListener("change", () => {
        refreshStudyLinks();
        loadDashboardStats();
    });
    lessonInput.addEventListener("keyup", () => {
        refreshStudyLinks();
    });

    document.getElementById("btn-dad-settings").addEventListener("click", () => adminModal.classList.remove("hidden"));
    document.getElementById("admin-close").addEventListener("click", () => adminModal.classList.add("hidden"));

    document.getElementById("btn-add-reward").addEventListener("click", async () => {
        const title = document.getElementById("admin-reward-title").value;
        const desc = document.getElementById("admin-reward-desc").value;
        const rewardBtn = document.getElementById("btn-add-reward");
        if (!title || !desc) return showAdminMsg(rewardBtn, "제목과 설명을 입력해 주세요.", true);
        await fetch("/api/rewards", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ title, description: desc }),
        });
        document.getElementById("admin-reward-title").value = "";
        document.getElementById("admin-reward-desc").value = "";
        loadDashboardStats();
    });

    document.getElementById("btn-add-sch").addEventListener("click", async () => {
        const date = document.getElementById("admin-sch-date").value;
        const memo = document.getElementById("admin-sch-memo").value;
        const schBtn = document.getElementById("btn-add-sch");
        if (!date || !memo) return showAdminMsg(schBtn, "날짜와 메모를 입력해 주세요.", true);
        await fetch("/api/schedules", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ test_date: date, memo }),
        });
        document.getElementById("admin-sch-date").value = "";
        document.getElementById("admin-sch-memo").value = "";
        loadDashboardStats();
    });

    document.getElementById("btn-ingest").addEventListener("click", async () => {
        const fileEl = document.getElementById("ingest-file");
        const status = document.getElementById("ingest-status");
        const f = fileEl.files && fileEl.files[0];
        if (!f) { status.style.color = 'var(--danger, #FF3B30)'; status.textContent = "이미지 파일을 선택해 주세요."; return; }
        status.textContent = "Ollama 처리 중… (시간이 걸릴 수 있어요)";
        const fd = new FormData();
        fd.append("lesson", getLesson());
        fd.append("file", f);
        try {
            const res = await fetch("/api/voca/ingest", { method: "POST", body: fd });
            const data = await res.json().catch(() => ({}));
            if (!res.ok) {
                const d = data.detail;
                status.textContent =
                    typeof d === "string" ? d : Array.isArray(d) ? d.map((x) => x.msg || x).join(" ") : `오류 ${res.status}`;
                return;
            }
            status.textContent = `완료! ${data.synced}개 단어 동기화 · ${data.data_json || ""}`;
            loadDashboardStats();
            fileEl.value = "";
        } catch {
            status.textContent = "네트워크 오류 — 서버·Ollama를 확인해 주세요.";
        }
    });

    window.deleteReward = async (id) => {
        if (confirm("이 보상을 삭제할까요?")) {
            await fetch(`/api/rewards/${id}`, { method: "DELETE" });
            loadDashboardStats();
        }
    };
    window.toggleReward = async (id) => {
        if (confirm("이 보상을 달성(earned)으로 표시할까요? ✨")) {
            await fetch(`/api/rewards/${id}`, { method: "PUT" });
            loadDashboardStats();
        }
    };
    window.deleteSchedule = async (id) => {
        if (confirm("일정을 삭제할까요?")) {
            await fetch(`/api/schedules/${id}`, { method: "DELETE" });
            loadDashboardStats();
        }
    };

    async function loadDashboardStats() {
        try {
            const [resR, resS] = await Promise.all([fetch("/api/rewards"), fetch("/api/schedules")]);
            const rewards = await resR.json();
            const schedules = await resS.json();

            const scheduleList = document.getElementById("schedule-list");
            scheduleList.innerHTML = schedules.length ? "" : '<p class="empty-txt">등록된 시험 일정이 없어요.</p>';
            schedules.forEach((s) => {
                // 타임존 독립적 D-day 계산 (YYYY-MM-DD → UTC midnight 비교)
                const [fy, fm, fd] = s.test_date.split("-").map(Number);
                const today = new Date();
                const targetMs = Date.UTC(fy, fm - 1, fd);
                const todayMs = Date.UTC(today.getFullYear(), today.getMonth(), today.getDate());
                const diffDays = Math.round((targetMs - todayMs) / (1000 * 60 * 60 * 24));
                let dDayHtml =
                    diffDays > 0
                        ? `<span class="badge-dday">D-${diffDays}</span>`
                        : diffDays === 0
                          ? `<span class="badge-dday today">D-Day! 🔥</span>`
                          : `<span class="badge-dday past">D+${Math.abs(diffDays)}</span>`;

                const div = document.createElement("div");
                div.className = "sch-item";
                div.innerHTML = `<div class="sch-header"><strong>${s.test_date}</strong> ${dDayHtml}</div><span>${s.memo}</span><button class="del-btn" onclick="deleteSchedule(${s.id})">&times;</button>`;
                scheduleList.appendChild(div);
            });

            const rewardList = document.getElementById("reward-list");
            rewardList.innerHTML = rewards.length ? "" : '<p class="empty-txt">보상 카드가 아직 없어요.</p>';
            rewards.forEach((r) => {
                const div = document.createElement("div");
                div.className = `reward-item ${r.is_earned ? "earned" : ""}`;
                div.onclick = (e) => {
                    if (e.target.classList.contains("del-btn")) return;
                    if (!r.is_earned) toggleReward(r.id);
                };
                div.innerHTML = `<h4>${r.title}</h4><p>${r.description}</p><button class="del-btn" onclick="deleteReward(${r.id})">&times;</button>`;
                rewardList.appendChild(div);
            });

            const les = getLesson();
            const resStats = await fetch(`/api/study/${CURRENT_SUBJECT}/${encodeURIComponent(les)}`);
            const data = await resStats.json();
            document.getElementById("dash-streak").textContent = data.progress ? data.progress.best_streak : 0;
        } catch (err) {
            console.error("Dashboard 통계 로드 실패:", err);
            const scheduleList = document.getElementById("schedule-list");
            if (scheduleList && scheduleList.innerHTML === "") {
                 scheduleList.innerHTML = '<p class="empty-txt" style="color:#FF3B30">데이터를 불러오지 못했어요.</p>';
            }
        }
    }

    refreshStudyLinks();
    loadDashboardStats();

    const params = new URLSearchParams(window.location.search);
    if (params.get("cleared") === "1") {
        const mission = document.getElementById("mission-label");
        const wrap = document.querySelector(".checkbox-wrapper");
        if (mission) mission.textContent = "🎉 완료!";
        if (wrap) wrap.innerHTML = '<span class="custom-checkbox"></span> ✅ <strong>노 미스 클리어!</strong>';
        const burst = document.getElementById("reward-burst-modal");
        burst.classList.remove("hidden");
        document.getElementById("btn-reward-burst-ok").onclick = () => {
            burst.classList.add("hidden");
            window.history.replaceState({}, "", "/");
        };
    }
});
