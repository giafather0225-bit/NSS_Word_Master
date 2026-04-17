/* ═══════════════════════════════════════════
   NSS Word Master — Parent Dashboard JS
   ═══════════════════════════════════════════ */
(function () {
    "use strict";

    const $ = (id) => document.getElementById(id);
    const getPin = () => localStorage.getItem("parent_pin") || "1234";

    /* ── PIN Gate ── */
    function initPin() {
        const overlay = $("pin-overlay");
        if (sessionStorage.getItem("parent_unlocked") === "1") {
            overlay.classList.add("hidden");
            $("parent-content").style.display = "block";
            boot();
            return;
        }
        $("btn-pin").addEventListener("click", () => {
            const v = $("pin-input").value.trim();
            if (v === getPin()) {
                sessionStorage.setItem("parent_unlocked", "1");
                overlay.classList.add("hidden");
                $("pin-error").classList.add("hidden");
                $("parent-content").style.display = "block";
                boot();
            } else {
                $("pin-error").classList.remove("hidden");
            }
        });
        $("pin-input").addEventListener("keydown", (e) => {
            if (e.key === "Enter") $("btn-pin").click();
        });
    }

    /* ── Boot: load everything ── */
    let _refreshTimer = null;

    function boot() {
        loadStats();
        loadAnalytics();
        loadMathSummary();
        initModals();
        initPinChange();

        _refreshTimer = setInterval(() => {
            loadStats();
            loadAnalytics();
            loadMathSummary();
        }, 30000);

        document.addEventListener("visibilitychange", () => {
            if (document.hidden) {
                clearInterval(_refreshTimer);
            } else {
                loadStats();
                loadAnalytics();
                _refreshTimer = setInterval(() => {
                    loadStats();
                    loadAnalytics();
                }, 30000);
            }
        });
    }

    /* ── Stats API ── */
    async function loadStats() {
        try {
            const res = await fetch("/api/dashboard/stats");
            if (!res.ok) throw new Error();
            const d = await res.json();
            $("stat-total-words").textContent = d.total_words || 0;
            $("stat-words-detail").textContent = d.words_detail || "";
            $("stat-textbooks").textContent = d.textbook_count || 0;
            $("stat-textbooks-detail").textContent = d.textbook_count > 0 ? d.textbook_count + " registered" : "";
            $("stat-lessons").textContent = d.lesson_count || 0;
            $("stat-lessons-detail").textContent = d.lessons_detail || "";
            $("stat-streak").textContent = d.best_streak || 0;
            $("stat-streak-detail").textContent = d.streak_detail || "";
            renderTextbooks(d.textbooks || []);
        } catch {
            $("stat-total-words").textContent = "?";
            fallbackStats();
        }
    }

    async function fallbackStats() {
        // If /api/dashboard/stats doesn't exist yet, do individual calls
        try {
            const res = await fetch("/api/lessons/English");
            if (!res.ok) return;
            const data = await res.json();
            let totalWords = 0, totalLessons = 0;
            const textbooks = [];
            for (const [tb, lessons] of Object.entries(data)) {
                const lessonList = Array.isArray(lessons) ? lessons : Object.keys(lessons);
                totalLessons += lessonList.length;
                textbooks.push({ name: tb, lessons: lessonList.length, words: "?" });
            }
            $("stat-textbooks").textContent = Object.keys(data).length;
            $("stat-lessons").textContent = totalLessons;
            renderTextbooks(textbooks);
        } catch {}
    }

    function renderTextbooks(list) {
        const el = $("textbook-overview");
        if (!list.length) { el.innerHTML = '<p class="empty">No textbooks found</p>'; return; }
        el.innerHTML = list.map(tb => `
            <div class="textbook-group">
                <div class="textbook-item" data-tb="${esc(tb.name)}" onclick="toggleTextbook(this)">
                    <div class="tb-icon ${tb.name === 'My_Words' ? 'mywords' : 'voca'}">${tb.name === 'My_Words' ? '✏️' : '📚'}</div>
                    <div class="tb-info">
                        <div class="tb-name">${esc(tb.name)}</div>
                        <div class="tb-meta">${tb.lessons || 0} lessons · ${tb.words || 0} words</div>
                    </div>
                    <div class="tb-chevron">›</div>
                </div>
                <div class="tb-lessons hidden" id="tb-lessons-${esc(tb.name)}">
                    <div class="tb-lessons-loading">Loading…</div>
                </div>
            </div>
        `).join("");
    }

    window.toggleTextbook = async function(el) {
        const tb = el.dataset.tb;
        const panel = $("tb-lessons-" + tb);
        const chevron = el.querySelector(".tb-chevron");
        if (!panel.classList.contains("hidden")) {
            panel.classList.add("hidden");
            chevron.classList.remove("open");
            return;
        }
        panel.classList.remove("hidden");
        chevron.classList.add("open");
        // Load lessons
        try {
            const res = await fetch("/api/dashboard/textbook/" + encodeURIComponent(tb));
            const data = await res.json();
            if (!data.lessons || !data.lessons.length) {
                panel.innerHTML = '<p class="empty" style="padding:8px 12px;">No lessons</p>';
                return;
            }
            panel.innerHTML = data.lessons.map(l => `
                <div class="tb-lesson-row">
                    <span class="tb-lesson-name">${esc(l.lesson)}</span>
                    <span class="tb-lesson-words">${l.words} words</span>
                    <a href="/child?textbook=${encodeURIComponent(tb)}&lesson=${encodeURIComponent(l.lesson)}" 
                       class="tb-lesson-go" title="Open in GIA Mode">▶</a>
                </div>
            `).join("");
        } catch {
            panel.innerHTML = '<p class="empty" style="padding:8px 12px;">Error loading</p>';
        }
    };

    /* ── Schedules ── */
    async function loadSchedules() {
        try {
            const res = await fetch("/api/schedules");
            const list = await res.json();
            const el = $("schedule-list");
            if (!list.length) { el.innerHTML = '<p class="empty">No schedules</p>'; return; }
            el.innerHTML = list.map(s => {
                const diff = daysUntil(s.test_date);
                const cls = diff > 0 ? 'future' : diff === 0 ? 'today' : 'past';
                const label = diff > 0 ? `D-${diff}` : diff === 0 ? 'D-Day!' : `D+${Math.abs(diff)}`;
                return `<div class="sch-item">
                    <span class="sch-date">${esc(s.test_date)}</span>
                    <span class="sch-memo">${esc(s.memo)}</span>
                    <span class="sch-badge ${cls}">${label}</span>
                    <button class="del-btn" onclick="deleteSchedule(${s.id})">&times;</button>
                </div>`;
            }).join("");
        } catch {}
    }

    window.deleteSchedule = async (id) => {
        if (!confirm("Delete this schedule?")) return;
        await fetch(`/api/schedules/${id}`, { method: "DELETE" });
        loadSchedules();
    };

    /* ── Rewards ── */
    async function loadRewards() {
        try {
            const res = await fetch("/api/rewards");
            const list = await res.json();
            const el = $("reward-list");
            if (!list.length) { el.innerHTML = '<p class="empty">No rewards</p>'; return; }
            el.innerHTML = list.map(r => `
                <div class="reward-item ${r.is_earned ? 'earned' : ''}" onclick="toggleReward(${r.id})">
                    <div class="reward-check">${r.is_earned ? '✓' : ''}</div>
                    <div class="reward-info">
                        <div class="reward-title">${esc(r.title)}</div>
                        <div class="reward-desc">${esc(r.description)}</div>
                    </div>
                    <button class="del-btn" onclick="event.stopPropagation();deleteReward(${r.id})">&times;</button>
                </div>
            `).join("");
        } catch {}
    }

    window.toggleReward = async (id) => {
        await fetch(`/api/rewards/${id}`, { method: "PUT" });
        loadRewards();
    };
    window.deleteReward = async (id) => {
        if (!confirm("Delete this reward?")) return;
        await fetch(`/api/rewards/${id}`, { method: "DELETE" });
        loadRewards();
    };

    /* ── Modal System ── */
    function initModals() {
        // Close buttons
        document.querySelectorAll(".modal-close").forEach(btn => {
            btn.addEventListener("click", () => {
                const id = btn.dataset.close;
                if (id) $(id).classList.add("hidden");
            });
        });
        // Overlay click-to-close
        document.querySelectorAll(".modal-overlay").forEach(ov => {
            let mouseDownTarget = null;
            ov.addEventListener("mousedown", (e) => { mouseDownTarget = e.target; });
            ov.addEventListener("mouseup", (e) => {
                if (e.target === ov && mouseDownTarget === ov) {
                    ov.classList.add("hidden");
                }
                mouseDownTarget = null;
            });
        });
        // Tool card openers
        $("btn-open-pin").addEventListener("click", () => $("pin-modal").classList.remove("hidden"));
        $("btn-open-backup").addEventListener("click", () => $("backup-modal").classList.remove("hidden"));
    }

    
    /* ── Ingest (2-step: OCR preview → review → save) ── */
    function initIngest() {
        const fileInput = $("ingest-file");
        const dropLabel = $("ingest-drop");
        const preview   = $("ingest-preview");
        const runBtn    = $("btn-run-ocr");
        const status    = $("ingest-status");
        const step1     = $("ingest-step1");
        const step2     = $("ingest-step2");
        const tbody     = $("ocr-result-body");
        const countEl   = $("ocr-word-count");
        const saveBtn   = $("btn-save-reviewed");
        const saveStatus= $("save-status");

        let ocrWords = [];

        dropLabel.addEventListener("click", (e) => { e.stopPropagation(); fileInput.click(); });
        dropLabel.addEventListener("dragover", (e) => { e.preventDefault(); dropLabel.classList.add("dragover"); });
        dropLabel.addEventListener("dragleave", () => dropLabel.classList.remove("dragover"));
        dropLabel.addEventListener("drop", (e) => {
            e.preventDefault(); dropLabel.classList.remove("dragover");
            if (e.dataTransfer.files.length) {
                fileInput.files = e.dataTransfer.files;
                showPreview();
            }
        });
        fileInput.addEventListener("click", (e) => e.stopPropagation());
        fileInput.addEventListener("change", () => {
            if (fileInput.files.length) showPreview();
        });

        function showPreview() {
            const files = fileInput.files;
            if (!files || !files.length) return;
            runBtn.disabled = false;
            let html = '<div style="display:flex;gap:8px;flex-wrap:wrap">';
            for (let i = 0; i < files.length; i++) {
                const f = files[i];
                if (f.type.startsWith("image/")) {
                    const url = URL.createObjectURL(f);
                    html += '<img src="' + url + '" alt="preview" style="max-height:120px;border-radius:8px;border:1px solid var(--border)">';
                } else {
                    html += '<p style="font-size:13px;color:var(--text-secondary);padding:8px">📄 ' + esc(f.name) + '</p>';
                }
            }
            html += '</div><p style="font-size:12px;color:var(--text-secondary);margin-top:4px">' + files.length + ' file(s) selected</p>';
            preview.innerHTML = html;
            preview.classList.remove("hidden");
        }

        // Step 1: Run OCR (preview only)
        runBtn.addEventListener("click", async () => {
            if (!fileInput.files || !fileInput.files.length) return;
            runBtn.disabled = true;
            status.textContent = "Running OCR on " + fileInput.files.length + " image(s)… (~10s each)";
            status.className = "status-msg mt-8";
            const fd = new FormData();
            for (let i = 0; i < fileInput.files.length; i++) {
                fd.append("files", fileInput.files[i]);
            }
            try {
                const res = await fetch("/api/voca/ocr-preview", { method: "POST", body: fd });
                const data = await res.json().catch(() => ({}));
                if (!res.ok) {
                    status.textContent = data.detail || "OCR failed: " + res.status;
                    status.classList.add("error");
                    runBtn.disabled = false;
                    return;
                }
                ocrWords = data.words || [];
                renderTable(ocrWords);
                populateIngestLessons();
                step1.classList.add("hidden");
                step2.classList.remove("hidden");
            } catch(e) {
                status.textContent = "Network error: " + e.message;
                status.classList.add("error");
            }
            runBtn.disabled = false;
        });

        function renderTable(words) {
            countEl.textContent = words.length + " words extracted";
            tbody.innerHTML = "";
            words.forEach((w, i) => {
                const tr = document.createElement("tr");
                tr.innerHTML =
                    '<td><input class="ocr-edit" data-idx="' + i + '" data-field="word" value="' + esc(w.word || "") + '"></td>' +
                    '<td><input class="ocr-edit ocr-pos" data-idx="' + i + '" data-field="pos" value="' + esc(w.pos || "") + '"></td>' +
                    '<td><input class="ocr-edit" data-idx="' + i + '" data-field="definition" value="' + esc(w.definition || "") + '"></td>' +
                    '<td><input class="ocr-edit" data-idx="' + i + '" data-field="example" value="' + esc(w.example || "") + '"></td>' +
                    '<td><button class="btn-del-word" data-idx="' + i + '" title="Delete">✕</button></td>';
                tbody.appendChild(tr);
            });
            // Inline edit handlers
            tbody.querySelectorAll(".ocr-edit").forEach(inp => {
                inp.addEventListener("input", () => {
                    const idx = parseInt(inp.dataset.idx);
                    const field = inp.dataset.field;
                    if (ocrWords[idx]) ocrWords[idx][field] = inp.value;
                });
            });
            // Delete handlers
            tbody.querySelectorAll(".btn-del-word").forEach(btn => {
                btn.addEventListener("click", () => {
                    const idx = parseInt(btn.dataset.idx);
                    ocrWords.splice(idx, 1);
                    renderTable(ocrWords);
                });
            });
        }

        // Add word
        $("btn-add-word").addEventListener("click", () => {
            ocrWords.push({ word: "", pos: "", definition: "", example: "" });
            renderTable(ocrWords);
            const lastInput = tbody.querySelector("tr:last-child .ocr-edit");
            if (lastInput) lastInput.focus();
        });

        // Back button
        $("btn-back-upload").addEventListener("click", () => {
            step2.classList.add("hidden");
            step1.classList.remove("hidden");
            status.textContent = "";
        });

        // Save reviewed words
        saveBtn.addEventListener("click", async () => {
            const lesson = $("ingest-lesson").value;
            if (!lesson) { saveStatus.textContent = "Select a lesson"; return; }
            // Clean empty words
            const cleaned = ocrWords.filter(w => w.word && w.word.trim());
            if (!cleaned.length) { saveStatus.textContent = "No words to save"; return; }
            saveBtn.disabled = true;
            saveStatus.textContent = "Saving…";
            saveStatus.className = "status-msg mt-8";
            const fd = new FormData();
            fd.append("lesson", lesson);
            fd.append("words_json", JSON.stringify(cleaned));
            try {
                const res = await fetch("/api/voca/save-reviewed", { method: "POST", body: fd });
                const data = await res.json().catch(() => ({}));
                if (!res.ok) {
                    saveStatus.textContent = data.detail || "Save failed";
                    saveStatus.classList.add("error");
                } else {
                    saveStatus.textContent = "Saved " + (data.synced || 0) + " words to " + lesson;
                    saveStatus.classList.add("success");
                    setTimeout(() => {
                        $("ingest-modal").classList.add("hidden");
                        step2.classList.add("hidden");
                        step1.classList.remove("hidden");
                        fileInput.value = "";
                        preview.classList.add("hidden");
                        status.textContent = "";
                        saveStatus.textContent = "";
                        ocrWords = [];
                        tbody.innerHTML = "";
                        loadStats();
                    }, 1500);
                }
            } catch(e) {
                saveStatus.textContent = "Network error: " + e.message;
                saveStatus.classList.add("error");
            }
            saveBtn.disabled = false;
        });
    }


    async function populateIngestLessons() {
        const sel = $("ingest-lesson");
        sel.innerHTML = '<option value="Lesson_01">Lesson_01 (new)</option>';
        try {
            const res = await fetch("/api/lessons/English");
            const data = await res.json();
            for (const [tb, lessons] of Object.entries(data)) {
                const arr = Array.isArray(lessons) ? lessons : Object.keys(lessons);
                arr.forEach(l => {
                    const opt = document.createElement("option");
                    opt.value = l;
                    opt.textContent = `${tb} / ${l}`;
                    sel.appendChild(opt);
                });
            }
        } catch {}
    }

    /* ── PIN Change ── */
    function initPinChange() {
        $("btn-save-pin").addEventListener("click", () => {
            const cur = $("pin-current").value.trim();
            const nw = $("pin-new").value.trim();
            const st = $("pin-change-status");
            if (cur !== getPin()) {
                st.textContent = "Current PIN is incorrect.";
                st.className = "status-msg mt-8 error";
                return;
            }
            if (!/^\d{4,8}$/.test(nw)) {
                st.textContent = "New PIN: 4-8 digits required.";
                st.className = "status-msg mt-8 error";
                return;
            }
            localStorage.setItem("parent_pin", nw);
            $("pin-current").value = "";
            $("pin-new").value = "";
            st.textContent = "PIN saved ✓";
            st.className = "status-msg mt-8 success";
        });
    }

    /* ── Schedule Add ── */
    function initScheduleAdd() {
        $("btn-submit-schedule").addEventListener("click", async () => {
            const date = $("sch-date").value;
            const memo = $("sch-memo").value.trim();
            if (!date || !memo) return;
            await fetch("/api/schedules", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ test_date: date, memo }),
            });
            $("sch-date").value = "";
            $("sch-memo").value = "";
            $("schedule-modal").classList.add("hidden");
            loadSchedules();
        });
    }

    /* ── Reward Add ── */
    function initRewardAdd() {
        $("btn-submit-reward").addEventListener("click", async () => {
            const title = $("reward-title").value.trim();
            const desc = $("reward-desc").value.trim();
            if (!title || !desc) return;
            await fetch("/api/rewards", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ title, description: desc }),
            });
            $("reward-title").value = "";
            $("reward-desc").value = "";
            $("reward-modal").classList.add("hidden");
            loadRewards();
        });
    }

    /* ── Reward Burst ── */
    function checkBurst() {
        const params = new URLSearchParams(location.search);
        if (params.get("cleared") === "1") {
            fetch("/api/rewards/earn_all", { method: "POST" }).catch(() => {});
            $("reward-burst-modal").classList.remove("hidden");
            $("btn-burst-ok").addEventListener("click", () => {
                $("reward-burst-modal").classList.add("hidden");
                history.replaceState({}, "", "/");
            });
        }
    }



    /* ── Learning Analytics ── */
    async function loadAnalytics() {
        try {
            const res = await fetch("/api/dashboard/analytics");
            if (!res.ok) return;
            const d = await res.json();

            // Update stats cards with real data
            const totalMin = Math.round((d.total_study_sec || 0) / 60);
            const todayMin = Math.round((d.today_study_sec || 0) / 60);
            
            // Render recent activity
            renderRecentActivity(d.recent_activity || []);
            renderWeakWords(d.weak_words || []);
            renderLessonProgress(d.lesson_progress || []);
            
            // Update streak card
            const streakEl = $("stat-streak");
            if (streakEl && d.study_streak_days > 0) {
                $("stat-streak-detail").textContent = d.study_streak_days + " day streak";
            }
            
            // Study time
            const timeEl = $("stat-study-time");
            if (timeEl) {
                timeEl.textContent = totalMin > 60 ? Math.round(totalMin/60) + "h" : totalMin + "m";
                const timeDetail = $("stat-study-time-detail");
                if (timeDetail) timeDetail.textContent = todayMin > 0 ? "Today: " + todayMin + " min" : "No study today";
            }
        } catch(e) { console.log("Analytics not loaded:", e); }
    }

    function renderRecentActivity(list) {
        const el = $("recent-activity");
        if (!el) return;
        if (!list.length) { el.innerHTML = '<p class="empty">No activity yet. Start studying!</p>'; return; }
        const stageEmoji = {preview:"👀",word_match:"🔗",fill_blank:"✏️",spelling:"📝",sentence:"💬",exam:"🏆"};
        el.innerHTML = list.slice(0, 8).map(a => {
            const emoji = stageEmoji[a.stage] || "📖";
            const dur = a.duration_sec > 0 ? Math.round(a.duration_sec/60) + "m" : "";
            const acc = a.word_count > 0 ? Math.round(a.correct_count * 100 / a.word_count) + "%" : "";
            const date = a.completed_at ? new Date(a.completed_at).toLocaleDateString("en", {month:"short",day:"numeric",hour:"2-digit",minute:"2-digit"}) : "";
            return '<div class="activity-row">' +
                '<span class="activity-emoji">' + emoji + '</span>' +
                '<div class="activity-info">' +
                    '<span class="activity-title">' + esc(a.lesson) + ' — ' + esc(a.stage) + '</span>' +
                    '<span class="activity-meta">' + [acc, dur, date].filter(Boolean).join(" · ") + '</span>' +
                '</div>' +
            '</div>';
        }).join("");
    }

    function renderWeakWords(list) {
        const el = $("weak-words");
        if (!el) return;
        if (!list.length) { el.innerHTML = '<p class="empty">No weak words detected yet</p>'; return; }
        el.innerHTML = list.map(w => {
            const pct = w.accuracy || 0;
            const color = pct < 40 ? "var(--danger)" : pct < 70 ? "#f59e0b" : "var(--accent)";
            return '<div class="weak-row">' +
                '<span class="weak-word">' + esc(w.word) + '</span>' +
                '<span class="weak-lesson">' + esc(w.lesson) + '</span>' +
                '<div class="weak-bar"><div class="weak-bar-fill" style="width:' + pct + '%;background:' + color + '"></div></div>' +
                '<span class="weak-pct" style="color:' + color + '">' + pct + '%</span>' +
            '</div>';
        }).join("");
    }

    function renderLessonProgress(list) {
        const el = $("lesson-progress");
        if (!el) return;
        if (!list.length) { el.innerHTML = '<p class="empty">No study data yet</p>'; return; }
        const allStages = ["preview","word_match","fill_blank","spelling","sentence","exam"];
        el.innerHTML = list.map(lp => {
            const done = (lp.completed_stages || "").split(",").filter(Boolean);
            const pct = Math.round(done.length / allStages.length * 100);
            const totalMin = Math.round((lp.total_time || 0) / 60);
            const lastDate = lp.last_studied ? new Date(lp.last_studied).toLocaleDateString("en",{month:"short",day:"numeric"}) : "";
            return '<div class="lp-row">' +
                '<div class="lp-info">' +
                    '<span class="lp-name">' + esc(lp.textbook) + ' / ' + esc(lp.lesson) + '</span>' +
                    '<span class="lp-meta">' + done.length + '/6 stages · ' + totalMin + 'm · ' + lastDate + '</span>' +
                '</div>' +
                '<div class="lp-bar"><div class="lp-bar-fill" style="width:' + pct + '%"></div></div>' +
            '</div>';
        }).join("");
    }

    /* ── Helpers ── */
    function daysUntil(dateStr) {
        const [y, m, d] = dateStr.split("-").map(Number);
        const target = Date.UTC(y, m - 1, d);
        const now = new Date();
        const today = Date.UTC(now.getFullYear(), now.getMonth(), now.getDate());
        return Math.round((target - today) / 86400000);
    }
    function esc(s) {
        return String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");
    }

    /* ── Math Summary ── */
    async function loadMathSummary() {
        const el = $("parent-math-body");
        if (!el) return;
        try {
            const res = await fetch("/api/parent/math-summary");
            if (!res.ok) throw new Error("bad");
            const d = await res.json();
            renderMathSummary(el, d);
        } catch (e) {
            el.innerHTML = '<p class="empty">Math stats unavailable.</p>';
        }
    }

    function renderMathSummary(el, d) {
        const a = d.academy || {};
        const r = d.recent_7d || {};
        const wr = d.wrong_review || {};
        const weak = d.weak_areas || [];
        const flu = d.fluency || [];
        const daily = d.daily_recent || [];
        const kang = d.kangaroo || [];

        const weakHtml = weak.length
            ? weak.map(w => '<li>' + esc(w.lesson || '—') + ' <span class="pm-count">' + w.wrong_count + ' wrong</span></li>').join('')
            : '<li class="empty">No weak areas detected</li>';

        const fluHtml = flu.length
            ? flu.map(f => '<tr><td>' + esc(f.fact_set) + '</td><td>' + esc(f.phase) + '</td><td>' + f.best_score + '</td><td>' + f.accuracy_pct + '%</td><td>' + f.total_rounds + '</td></tr>').join('')
            : '<tr><td colspan="5" class="empty">No fluency rounds yet</td></tr>';

        const dailyHtml = daily.length
            ? daily.slice(0, 7).map(x => '<div class="pm-daily-cell ' + (x.completed ? 'done' : 'pending') + '" title="' + esc(x.date) + '">' + (x.completed ? (x.score + '/' + x.total) : '—') + '</div>').join('')
            : '<p class="empty">No daily challenges yet</p>';

        const kangHtml = kang.length
            ? kang.map(k => '<li>' + esc(k.set_id) + ' — ' + k.score + '/' + k.total + ' <span class="pm-date">' + esc(k.completed_at) + '</span></li>').join('')
            : '<li class="empty">No sets completed</li>';

        el.innerHTML =
            '<div class="pm-grid">' +
                '<div class="pm-card"><div class="pm-label">Academy</div>' +
                    '<div class="pm-stat">' + (a.completed || 0) + ' / ' + (a.total_lessons || 0) + '</div>' +
                    '<div class="pm-sub">lessons completed</div>' +
                    '<div class="pm-sub">' + (a.pretest_passed || 0) + ' pretests · ' + (a.unit_tests_passed || 0) + ' unit tests</div>' +
                '</div>' +
                '<div class="pm-card"><div class="pm-label">Last 7 days</div>' +
                    '<div class="pm-stat">' + (r.accuracy_pct || 0) + '%</div>' +
                    '<div class="pm-sub">' + (r.correct_attempts || 0) + ' / ' + (r.total_attempts || 0) + ' correct</div>' +
                '</div>' +
                '<div class="pm-card"><div class="pm-label">Wrong Review</div>' +
                    '<div class="pm-stat">' + (wr.pending || 0) + '</div>' +
                    '<div class="pm-sub">due today · ' + (wr.mastered || 0) + ' mastered</div>' +
                '</div>' +
            '</div>' +
            '<div class="pm-section">' +
                '<h3>Weak Areas</h3>' +
                '<ul class="pm-list">' + weakHtml + '</ul>' +
            '</div>' +
            '<div class="pm-section">' +
                '<h3>Fact Fluency</h3>' +
                '<table class="pm-table"><thead><tr><th>Set</th><th>Phase</th><th>Best</th><th>Accuracy</th><th>Rounds</th></tr></thead><tbody>' + fluHtml + '</tbody></table>' +
            '</div>' +
            '<div class="pm-section">' +
                '<h3>Daily Challenge (last 7)</h3>' +
                '<div class="pm-daily-row">' + dailyHtml + '</div>' +
            '</div>' +
            '<div class="pm-section">' +
                '<h3>Kangaroo</h3>' +
                '<ul class="pm-list">' + kangHtml + '</ul>' +
            '</div>';
    }

    /* ── Init ── */
    document.addEventListener("DOMContentLoaded", initPin);
})();

    /* ── Dashboard Calendar ──────────────── */
    var _dCalYear, _dCalMonth;
    function _$(id) { return document.getElementById(id); }

    function initDashCalendar() {
        var now = new Date();
        _dCalYear = now.getFullYear();
        _dCalMonth = now.getMonth();
        renderDashCalendar();
        var prev = _$("dash-cal-prev");
        var next = _$("dash-cal-next");
        if (prev) prev.onclick = function() { _dCalMonth--; if (_dCalMonth < 0) { _dCalMonth = 11; _dCalYear--; } renderDashCalendar(); };
        if (next) next.onclick = function() { _dCalMonth++; if (_dCalMonth > 11) { _dCalMonth = 0; _dCalYear++; } renderDashCalendar(); };
    }

    function renderDashCalendar() {
        var grid = _$("dash-cal-grid");
        var title = _$("dash-cal-title");
        if (!grid) return;
        var months = ["January","February","March","April","May","June","July","August","September","October","November","December"];
        if (title) title.textContent = months[_dCalMonth] + " " + _dCalYear;
        grid.innerHTML = "";
        ["Mo","Tu","We","Th","Fr","Sa","Su"].forEach(function(h) {
            var el = document.createElement("div");
            el.className = "dash-cal-header";
            el.textContent = h;
            grid.appendChild(el);
        });
        var firstDay = new Date(_dCalYear, _dCalMonth, 1).getDay();
        var startOffset = firstDay === 0 ? 6 : firstDay - 1;
        var daysInMonth = new Date(_dCalYear, _dCalMonth + 1, 0).getDate();
        var now = new Date();
        for (var i = 0; i < startOffset; i++) {
            var empty = document.createElement("div");
            empty.className = "dash-cal-day empty";
            grid.appendChild(empty);
        }
        for (var d = 1; d <= daysInMonth; d++) {
            var cell = document.createElement("div");
            cell.className = "dash-cal-day";
            cell.textContent = d;
            cell.dataset.date = _dCalYear + "-" + String(_dCalMonth+1).padStart(2,"0") + "-" + String(d).padStart(2,"0");
            if (d === now.getDate() && _dCalMonth === now.getMonth() && _dCalYear === now.getFullYear()) {
                cell.classList.add("today");
            }
            grid.appendChild(cell);
        }
        loadDashCalendarData();
    }

    function loadDashCalendarData() {
        fetch("/api/dashboard/analytics")
            .then(function(res) { return res.json(); })
            .then(function(data) {
                var sessions = data.recent_activity || [];
                var studiedDates = new Set();
                sessions.forEach(function(s) {
                    var dateStr = s.completed_at ? s.completed_at.substring(0,10) : "";
                    if (dateStr) studiedDates.add(dateStr);
                });
                var grid = _$("dash-cal-grid");
                if (!grid) return;
                grid.querySelectorAll(".dash-cal-day[data-date]").forEach(function(cell) {
                    if (studiedDates.has(cell.dataset.date)) cell.classList.add("studied");
                });
            })
            .catch(function() {});
    }

    function renderLessonProgress(list) {
        var el = _$("lesson-progress");
        if (!el) return;
        if (!list.length) { el.innerHTML = '<p class="empty">No progress data yet</p>'; return; }
        el.innerHTML = list.map(function(lp) {
            var pct = lp.completion_pct || 0;
            var cls = pct >= 100 ? "done" : pct >= 60 ? "high" : pct >= 30 ? "mid" : "low";
            return '<div class="progress-row">' +
                '<span class="progress-lesson-name">' + esc(lp.lesson || "") + '</span>' +
                '<div class="progress-bar-wrap"><div class="progress-bar-fill ' + cls + '" style="width:' + pct + '%"></div></div>' +
                '<span class="progress-pct">' + pct + '%</span>' +
            '</div>';
        }).join("");
    }

    initDashCalendar();
