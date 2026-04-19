/* ================================================================
   Word Manager — Full-screen overlay (My_Words)
   ================================================================ */
(function () {
  "use strict";

  const API = "/api/mywords";
  let currentLesson = null;
  let words = [];
  let mode = "manual";

  const $ = (id) => document.getElementById(id);
  const esc = (s) => String(s ?? "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
  const ce = (tag, cls, html) => {
    const el = document.createElement(tag);
    if (cls) el.className = cls;
    if (html) el.innerHTML = html;
    return el;
  };

  async function api(url, opts = {}) {
    const res = await fetch(url, {
      headers: { "Content-Type": "application/json" },
      ...opts,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "HTTP " + res.status);
    }
    return res.json();
  }

  /* ── Open / Close ────────────────────────────────────── */
  function open() {
    const ov = $("wm-overlay");
    ov.classList.remove("hidden", "closing");
    currentLesson = null;
    words = [];
    renderLessonList();
  }

  function close() {
    const ov = $("wm-overlay");
    ov.classList.add("closing");
    setTimeout(() => ov.classList.add("hidden"), 260);
  }

  /* ── Lesson List ─────────────────────────────────────── */
  async function renderLessonList() {
    const body = $("wm-body");
    body.innerHTML =
      '<div class="wm-lesson-list">' +
        '<div class="wm-section-title">My Word Lists</div>' +
        '<div id="wm-weekly-test-bar" class="wm-weekly-test-bar"></div>' +
        '<div id="wm-lessons-container" class="wm-lessons-container">' +
          '<div class="wm-loading">Loading...</div>' +
        '</div>' +
        '<div class="wm-create-row">' +
          '<input type="text" id="wm-new-lesson" class="wm-input" placeholder="New list name (e.g., Week_01)" maxlength="40" />' +
          '<button id="wm-btn-create" class="wm-btn-primary">+ Create</button>' +
        '</div>' +
      '</div>';

    $("wm-btn-create").onclick = createLesson;
    $("wm-new-lesson").onkeydown = (e) => { if (e.key === "Enter") createLesson(); };
    renderWeeklyTestBar();

    try {
      const res = await fetch("/api/lessons/English/My_Words");
      if (!res.ok) throw new Error("No lessons");
      const data = await res.json();
      const lessons = data.lessons || [];
      const container = $("wm-lessons-container");

      if (!lessons.length) {
        container.innerHTML = '<div class="wm-empty">No word lists yet.<br>Create one to get started!</div>';
        return;
      }

      container.innerHTML = "";

      // Fetch word counts for each lesson
      for (const l of lessons) {
        const name = typeof l === "string" ? l : l.name;
        let wordCount = 0;
        try {
          const r = await fetch("/api/study/English/My_Words/" + encodeURIComponent(name));
          if (r.ok) {
            const d = await r.json();
            wordCount = (d.items || []).length;
          }
        } catch (e) {}

        const card = ce("div", "wm-lesson-card");
        const canLearn = wordCount > 0;
        card.innerHTML =
          '<div class="wm-lesson-info" data-lesson="' + name + '">' +
            '<span class="wm-lesson-icon">📝</span>' +
            '<div class="wm-lesson-meta">' +
              '<span class="wm-lesson-name">' + name.replace(/_/g, " ") + '</span>' +
              '<span class="wm-lesson-count">' + wordCount + ' words</span>' +
            '</div>' +
          '</div>' +
          '<div class="wm-lesson-actions">' +
            '<button class="wm-lesson-learn" data-lesson="' + name + '" title="Learn"' +
              (canLearn ? '' : ' disabled') + '>▶ Learn</button>' +
            '<button class="wm-lesson-rename" data-lesson="' + name + '" title="Rename">✏️</button>' +
            '<button class="wm-lesson-del" data-lesson="' + name + '" title="Delete">✕</button>' +
          '</div>';
        card.querySelector(".wm-lesson-info").onclick = () => openLesson(name);
        const learnBtn = card.querySelector(".wm-lesson-learn");
        if (learnBtn && canLearn) learnBtn.onclick = (e) => {
          e.stopPropagation();
          startLearning(name);
        };
        card.querySelector(".wm-lesson-rename").onclick = (e) => {
          e.stopPropagation();
          renameLesson(name);
        };
        card.querySelector(".wm-lesson-del").onclick = (e) => {
          e.stopPropagation();
          deleteLesson(name);
        };
        container.appendChild(card);
      }
    } catch (err) {
      $("wm-lessons-container").innerHTML = '<div class="wm-empty">No word lists yet.<br>Create one to get started!</div>';
    }
  }

  async function createLesson() {
    const input = $("wm-new-lesson");
    const name = input.value.trim();
    if (!name) return;
    try {
      await api(API + "/lessons", { method: "POST", body: JSON.stringify({ name }) });
      input.value = "";
      renderLessonList();
    } catch (err) {
      toast(err.message, "error");
    }
  }

  async function renameLesson(oldName) {
    const newName = prompt("New name for \"" + oldName.replace(/_/g, " ") + "\":", oldName);
    if (!newName || newName.trim() === oldName) return;
    try {
      await api(API + "/lessons/" + encodeURIComponent(oldName) + "/rename", {
        method: "PUT",
        body: JSON.stringify({ name: newName.trim() }),
      });
      renderLessonList();
    } catch (err) {
      toast(err.message, "error");
    }
  }

  async function deleteLesson(name) {
    if (!confirm('Delete "' + name.replace(/_/g, " ") + '" and all its words?')) return;
    try {
      await api(API + "/lessons/" + encodeURIComponent(name), { method: "DELETE" });
      renderLessonList();
    } catch (err) {
      toast(err.message, "error");
    }
  }

  /* ── Lesson Detail ───────────────────────────────────── */
  async function openLesson(name) {
    currentLesson = name;
    const body = $("wm-body");
    body.innerHTML = 
      '<div class="wm-detail">' +
        '<button class="wm-back-btn" id="wm-back">← Back to Lists</button>' +
        '<div class="wm-detail-title">' + name.replace(/_/g, " ") + '</div>' +

        '<div class="wm-mode-toggle">' +
          '<button class="wm-mode-btn active" data-mode="manual">✏️ Direct Input</button>' +
          '<button class="wm-mode-btn" data-mode="ai">AI Assist</button>' +
        '</div>' +

        '<div class="wm-form" id="wm-form">' +
          '<div class="wm-form-row">' +
            '<input type="text" id="wm-word" class="wm-input wm-input-word" placeholder="Word" maxlength="60" />' +
            '<input type="text" id="wm-pos" class="wm-input wm-input-pos" placeholder="Part of speech" maxlength="20" />' +
          '</div>' +
          '<div id="wm-manual-fields">' +
            '<div class="wm-form-row"><input type="text" id="wm-def" class="wm-input" placeholder="Definition" maxlength="200" /></div>' +
            '<div class="wm-form-row"><input type="text" id="wm-example" class="wm-input" placeholder="Example sentence" maxlength="300" /></div>' +
          '</div>' +
          '<div class="wm-ai-section hidden" id="wm-ai-fields">' +
            '<button id="wm-btn-ai" class="wm-btn-ai">Generate with AI</button>' +
            '<div id="wm-ai-result" class="wm-ai-result hidden"></div>' +
          '</div>' +
          '<button id="wm-btn-add" class="wm-btn-primary wm-btn-add">+ Add Word</button>' +
        '</div>' +

        '<div class="wm-wordlist-title">Words <span id="wm-word-count" class="wm-word-count">0</span></div>' +
        '<div id="wm-wordlist" class="wm-wordlist"></div>' +
      '</div>';

    $("wm-back").onclick = () => renderLessonList();

    body.querySelectorAll(".wm-mode-btn").forEach((btn) => {
      btn.onclick = () => {
        mode = btn.dataset.mode;
        body.querySelectorAll(".wm-mode-btn").forEach((b) => b.classList.remove("active"));
        btn.classList.add("active");
        $("wm-manual-fields").classList.toggle("hidden", mode === "ai");
        $("wm-ai-fields").classList.toggle("hidden", mode === "manual");
        $("wm-ai-result").classList.add("hidden");
        $("wm-ai-result").innerHTML = "";
      };
    });

    $("wm-btn-ai").onclick = generateAI;
    $("wm-btn-add").onclick = addWord;
    $("wm-word").onkeydown = (e) => {
      if (e.key === "Enter") {
        if (mode === "ai" && !$("wm-ai-def")) generateAI();
        else addWord();
      }
    };

    await loadWords();
  }

  /* ── AI Generate ─────────────────────────────────────── */
  async function generateAI() {
    const word = $("wm-word").value.trim();
    const pos = $("wm-pos").value.trim();
    if (!word) { $("wm-word").focus(); return; }

    const btn = $("wm-btn-ai");
    const result = $("wm-ai-result");
    btn.disabled = true;
    btn.textContent = "⏳ Generating...";
    result.classList.add("hidden");

    try {
      const data = await api(API + "/ai-enrich", {
        method: "POST",
        body: JSON.stringify({ word, pos }),
      });

      const aiPos = data.pos ? (Array.isArray(data.pos) ? data.pos[0] : data.pos) : "";

      if (data.definition) {
        result.classList.remove("hidden");
        result.innerHTML = 
          '<div class="wm-ai-card">' +
            '<div class="wm-ai-field">' +
              '<div class="wm-ai-label">DEFINITION</div>' +
              '<textarea id="wm-ai-def" class="wm-input wm-ai-input wm-textarea" rows="2">' + esc(data.definition) + '</textarea>' +
            '</div>' +
            '<div class="wm-ai-field">' +
              '<div class="wm-ai-label">EXAMPLE</div>' +
              '<textarea id="wm-ai-example" class="wm-input wm-ai-input wm-textarea" rows="2">' + esc(data.example) + '</textarea>' +
            '</div>' +
            (aiPos && !pos ?
              '<div class="wm-ai-field wm-ai-field-half">' +
                '<div class="wm-ai-label">PART OF SPEECH</div>' +
                '<input type="text" id="wm-ai-pos" class="wm-input wm-ai-input" value="' + esc(aiPos) + '" />' +
              '</div>' : '') +
            '<div class="wm-ai-provider">Generated by ' + esc(data.provider) + '</div>' +
          '</div>';
      } else {
        result.classList.remove("hidden");
        result.innerHTML = '<div class="wm-ai-fail">AI couldn\'t generate. Please enter manually.</div>';
      }
    } catch (err) {
      result.classList.remove("hidden");
      result.innerHTML = '<div class="wm-ai-fail">Error: ' + esc(err.message) + '</div>';
    } finally {
      btn.disabled = false;
      btn.textContent = "Generate with AI";
    }
  }

  /* ── Add Word ────────────────────────────────────────── */
  async function addWord() {
    const word = $("wm-word").value.trim();
    if (!word) { $("wm-word").focus(); return; }

    var definition = "", example = "", pos = $("wm-pos").value.trim();

    if (mode === "ai") {
      var aiDef = $("wm-ai-def");
      var aiEx = $("wm-ai-example");
      var aiPos = $("wm-ai-pos");
      definition = aiDef ? aiDef.value.trim() : "";
      example = aiEx ? aiEx.value.trim() : "";
      if (aiPos && !pos) pos = aiPos.value.trim();
      if (!definition) {
        toast("Generate AI definition first, or switch to Direct Input.", "warn");
        return;
      }
    } else {
      definition = $("wm-def").value.trim();
      example = $("wm-example").value.trim();
      if (!definition) { $("wm-def").focus(); return; }
    }

    var btn = $("wm-btn-add");
    btn.disabled = true;
    btn.textContent = "Adding...";

    try {
      await api(API + "/" + encodeURIComponent(currentLesson) + "/words", {
        method: "POST",
        body: JSON.stringify({ word: word, pos: pos, definition: definition, example: example }),
      });

      $("wm-word").value = "";
      $("wm-pos").value = "";
      if ($("wm-def")) $("wm-def").value = "";
      if ($("wm-example")) $("wm-example").value = "";
      $("wm-ai-result").classList.add("hidden");
      $("wm-ai-result").innerHTML = "";
      $("wm-word").focus();

      await loadWords();
    } catch (err) {
      toast(err.message, "error");
    } finally {
      btn.disabled = false;
      btn.textContent = "+ Add Word";
    }
  }

  /* ── Load & Render Words ─────────────────────────────── */
  async function loadWords() {
    try {
      var res = await fetch("/api/study/English/My_Words/" + encodeURIComponent(currentLesson));
      if (!res.ok) { words = []; renderWords(); return; }
      var data = await res.json();
      words = (data.items || []).map(function(it) {
        var extra = {};
        try { extra = JSON.parse(it.extra_data || "{}"); } catch(e) {}
        return {
          id: it.id,
          word: it.answer,
          definition: it.question,
          example: it.hint || "",
          pos: extra.pos || "",
        };
      });
      renderWords();
    } catch (err) {
      words = [];
      renderWords();
    }
  }

  function renderWords() {
    var list = $("wm-wordlist");
    $("wm-word-count").textContent = words.length;

    if (!words.length) {
      list.innerHTML = '<div class="wm-empty-words">No words yet. Start adding!</div>';
      return;
    }

    list.innerHTML = words.map(function(w, i) {
      return '<div class="wm-word-item">' +
        '<div class="wm-word-num">' + (i + 1) + '</div>' +
        '<div class="wm-word-main">' +
          '<div class="wm-word-text">' + w.word + ' <span class="wm-word-pos">' + w.pos + '</span></div>' +
          '<div class="wm-word-def">' + w.definition + '</div>' +
          (w.example ? '<div class="wm-word-ex">' + w.example + '</div>' : '') +
        '</div>' +
        '<button class="wm-word-del" data-word="' + w.word.replace(/"/g, '&quot;') + '" title="Delete">✕</button>' +
      '</div>';
    }).join("");

    list.querySelectorAll(".wm-word-del").forEach(function(btn) {
      btn.onclick = function() { deleteWord(btn.dataset.word); };
    });
  }

  async function deleteWord(word) {
    if (!confirm('Delete "' + word + '"?')) return;
    try {
      await api(API + "/" + encodeURIComponent(currentLesson) + "/words/" + encodeURIComponent(word), { method: "DELETE" });
      await loadWords();
    } catch (err) {
      toast(err.message, "error");
    }
  }

  /* ── Learn Flow (Daily Words 스타일 Preview 재사용) ─── */
  /**
   * Iterate through every word in `lessonName` via the Academy Preview modal
   * (Listen → Shadow → Spell). On each pass, collect the word; when the
   * session ends, register all completed words into the unified SM-2 Review
   * queue so they show up in the Review section alongside Academy / Daily.
   */
  async function startLearning(lessonName) {
    let wordList = [];
    try {
      const res = await fetch("/api/study/English/My_Words/" + encodeURIComponent(lessonName));
      if (!res.ok) throw new Error("HTTP " + res.status);
      const data = await res.json();
      wordList = (data.items || []).map((it) => ({
        id: "mw-" + lessonName + "-" + it.id,
        answer: it.answer,
        question: it.question || "",
        hint: it.hint || "",
      }));
    } catch (err) {
      toast("Failed to load words: " + err.message, "error");
      return;
    }
    if (!wordList.length) { toast("No words in this list.", "warn"); return; }
    if (typeof window.openPreviewModal !== "function") {
      toast("Preview module not loaded.", "error"); return;
    }

    const ov = $("wm-overlay");
    ov.classList.add("hidden");

    const learned = [];
    let idx = 0;

    const restoreAcademy = (() => {
      const prevItems = window.items;
      const prevStage = window.stage;
      return () => { window.items = prevItems; window.stage = prevStage; };
    })();

    function next() {
      if (idx >= wordList.length) { finish(); return; }
      const item = wordList[idx];
      // Stub Academy globals so closeModal() doesn't trigger advanceToNextStage.
      window.items = [item];
      if (typeof previewDoneMap !== "undefined") previewDoneMap.clear();
      window.stage = "mywords";
      window.openPreviewModal(item, (status) => {
        if (status === "ok" || status === "auto-pass") {
          learned.push({ word: item.answer, question: item.question, hint: item.hint });
          idx++;
          next();
        } else {
          // 'skip' → user closed modal; end session and register what we have.
          finish();
        }
      });
    }

    async function finish() {
      restoreAcademy();
      if (learned.length > 0) {
        try {
          await api("/api/review/register-words", {
            method: "POST",
            body: JSON.stringify({ source: "my", source_ref: lessonName, words: learned }),
          });
        } catch (err) { console.warn("[MyWords] register-words failed", err); }
      }
      ov.classList.remove("hidden");
      // Refresh review badge if review.js exposes a refresher.
      if (typeof window.refreshReviewBadge === "function") window.refreshReviewBadge();
    }

    next();
  }

  /* ── Weekly Test ─────────────────────────────────────── */
  /**
   * Render the Weekly Test bar above the lesson list. Shows total word count;
   * enables the test when ≥ min_required (50). Gate is enforced server-side too.
   * @tag MYWORDS @tag WEEKLY_TEST
   */
  async function renderWeeklyTestBar() {
    const bar = $("wm-weekly-test-bar");
    if (!bar) return;
    try {
      const res = await fetch("/api/mywords/weekly-test");
      if (!res.ok) { bar.innerHTML = ""; return; }
      const d = await res.json();
      const total = d.total_word_count || 0;
      const need = d.min_required || 50;
      const ok = !!d.available;
      bar.innerHTML =
        '<div class="wm-wt-bar ' + (ok ? 'ready' : 'locked') + '">' +
          '<div class="wm-wt-info">' +
            '<span class="wm-wt-title">Weekly Test</span>' +
            '<span class="wm-wt-sub">' +
              (ok
                ? 'Ready — ' + total + ' words available'
                : (need - total) + ' more words needed (' + total + '/' + need + ')') +
            '</span>' +
          '</div>' +
          '<button id="wm-wt-start" class="wm-btn-primary" ' +
            (ok ? '' : 'disabled') + '>Start</button>' +
        '</div>';
      const btn = $("wm-wt-start");
      if (btn && ok) btn.onclick = startWeeklyTest;
    } catch (err) {
      bar.innerHTML = "";
    }
  }

  /**
   * Run the Weekly Test. Presents definition → user types word → auto-grade
   * (case-insensitive exact match). Submits result on completion.
   * @tag MYWORDS @tag WEEKLY_TEST
   */
  async function startWeeklyTest() {
    let data;
    try {
      const res = await fetch("/api/mywords/weekly-test");
      data = await res.json();
      if (!data.available) { toast("Not enough words yet.", "warn"); return; }
    } catch (err) { toast("Failed to load test.", "error"); return; }

    const words = data.words || [];
    if (!words.length) return;

    let idx = 0, correct = 0;
    const body = $("wm-body");

    function renderQ() {
      if (idx >= words.length) return submit();
      const w = words[idx];
      body.innerHTML =
        '<div class="wm-detail">' +
          '<div class="wm-detail-title">Weekly Test  ' +
            '<span class="wm-word-count">' + (idx + 1) + ' / ' + words.length + '</span></div>' +
          '<div class="wm-wt-def">' + (w.definition || '(no definition)') + '</div>' +
          (w.example ? '<div class="wm-wt-ex">' + w.example.replace(new RegExp(w.word, 'ig'), '____') + '</div>' : '') +
          '<input type="text" id="wm-wt-input" class="wm-input" placeholder="Type the word..." autocomplete="off" />' +
          '<button id="wm-wt-submit" class="wm-btn-primary" style="margin-top:12px;">Submit</button>' +
          '<div id="wm-wt-fb" class="wm-wt-fb"></div>' +
        '</div>';
      const input = $("wm-wt-input");
      input.focus();
      input.onkeydown = (e) => { if (e.key === "Enter") grade(); };
      $("wm-wt-submit").onclick = grade;

      function grade() {
        const ans = (input.value || "").trim().toLowerCase();
        const truth = (w.word || "").trim().toLowerCase();
        const fb = $("wm-wt-fb");
        if (ans === truth) {
          correct++;
          fb.className = "wm-wt-fb ok";
          fb.textContent = "✓ Correct!";
        } else {
          fb.className = "wm-wt-fb ng";
          fb.textContent = "✗ Answer: " + w.word;
        }
        input.disabled = true;
        $("wm-wt-submit").textContent = "Next →";
        $("wm-wt-submit").onclick = () => { idx++; renderQ(); };
      }
    }

    async function submit() {
      let result = { passed: false, xp_awarded: 0, accuracy: 0 };
      try {
        const r = await fetch("/api/mywords/weekly-test/result", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ correct_count: correct, total_count: words.length }),
        });
        result = await r.json();
      } catch (err) {}

      body.innerHTML =
        '<div class="wm-detail" style="text-align:center;">' +
          '<div class="wm-detail-title">' + (result.passed ? "🎉 Passed!" : "Keep practicing") + '</div>' +
          '<div style="font-size:48px;font-weight:700;margin:20px 0;">' +
            correct + ' / ' + words.length + '</div>' +
          '<div style="color:var(--text-secondary);margin-bottom:16px;">' +
            Math.round((result.accuracy || 0) * 100) + '% accuracy' +
            (result.xp_awarded > 0 ? ' · +' + result.xp_awarded + ' XP' : '') +
          '</div>' +
          '<button id="wm-wt-done" class="wm-btn-primary">Done</button>' +
        '</div>';
      $("wm-wt-done").onclick = renderLessonList;
    }

    renderQ();
  }

  /* ── Init ────────────────────────────────────────────── */
  function init() {
    var btn = $("btn-word-manager");
    if (btn) btn.addEventListener("click", open);
    var closeBtn = $("wm-close");
    if (closeBtn) closeBtn.addEventListener("click", close);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
