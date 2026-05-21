/* ================================================================
   word-manager.js — Word Manager overlay: core state, lesson list
   Section: English
   Dependencies: word-manager-words.js, word-manager-test.js (loaded after in bundle-c)
   API endpoints:
     GET  /api/lessons/English/My_Words
     POST /api/mywords/lessons
     PUT  /api/mywords/lessons/{name}/rename
     DEL  /api/mywords/lessons/{name}
   ================================================================ */

// ── Shared module state (referenced by word-manager-words.js + word-manager-test.js) ──
var _wmState = { currentLesson: null, words: [], mode: "manual" };
var _WM_API = "/api/mywords";

// ── Shared helpers ────────────────────────────────────────────────────────────

/** @tag MY_WORDS */
function _wmEl(id) { return document.getElementById(id); }

/** @tag MY_WORDS */
function _wmEsc(s) {
  return String(s == null ? "" : s)
    .replace(/&/g, "&amp;").replace(/</g, "&lt;")
    .replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

/** @tag MY_WORDS */
function _wmCe(tag, cls, html) {
  var el = document.createElement(tag);
  if (cls) el.className = cls;
  if (html) el.innerHTML = html;
  return el;
}

/** @tag MY_WORDS */
async function _wmApi(url, opts) {
  opts = opts || {};
  var res = await fetch(url, Object.assign({ headers: { "Content-Type": "application/json" } }, opts));
  if (!res.ok) {
    var err = await res.json().catch(function () { return {}; });
    throw new Error(err.detail || "HTTP " + res.status);
  }
  return res.json();
}

// ── Open / Close ──────────────────────────────────────────────────────────────

/**
 * Open the Word Manager overlay.
 * @tag MY_WORDS
 */
function wmOpen() {
  var ov = _wmEl("wm-overlay");
  ov.classList.remove("hidden", "closing");
  _wmState.currentLesson = null;
  _wmState.words = [];
  renderLessonList();
}

/**
 * Close the Word Manager overlay.
 * @tag MY_WORDS
 */
function wmClose() {
  var ov = _wmEl("wm-overlay");
  ov.classList.add("closing");
  setTimeout(function () { ov.classList.add("hidden"); }, 260);
}

// ── Lesson List ───────────────────────────────────────────────────────────────

/**
 * Render the lesson chooser (root screen).
 * @tag MY_WORDS
 */
async function renderLessonList() {
  var body = _wmEl("wm-body");
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

  _wmEl("wm-btn-create").onclick = wmCreateLesson;
  _wmEl("wm-new-lesson").onkeydown = function (e) { if (e.key === "Enter") wmCreateLesson(); };
  renderWeeklyTestBar();

  try {
    var res = await fetch("/api/lessons/English/My_Words");
    if (!res.ok) throw new Error("No lessons");
    var data = await res.json();
    var lessons = data.lessons || [];
    var container = _wmEl("wm-lessons-container");

    if (!lessons.length) {
      container.innerHTML = '<div class="wm-empty">No word lists yet.<br>Create one to get started!</div>';
      return;
    }

    container.innerHTML = "";

    for (var i = 0; i < lessons.length; i++) {
      var l = lessons[i];
      var name = typeof l === "string" ? l : l.name;
      var wordCount = 0;
      try {
        var r = await fetch("/api/study/English/My_Words/" + encodeURIComponent(name));
        if (r.ok) {
          var d = await r.json();
          wordCount = (d.items || []).length;
        }
      } catch (e) {}

      var card = _wmCe("div", "wm-lesson-card");
      var canLearn = wordCount > 0;
      card.innerHTML =
        '<div class="wm-lesson-info" data-lesson="' + _wmEsc(name) + '">' +
          '<span class="wm-lesson-icon"><i data-lucide="file-text" style="width:16px;height:16px;stroke-width:1.5"></i></span>' +
          '<div class="wm-lesson-meta">' +
            '<span class="wm-lesson-name">' + _wmEsc(name.replace(/_/g, " ")) + '</span>' +
            '<span class="wm-lesson-count">' + wordCount + " words</span>" +
          '</div>' +
        '</div>' +
        '<div class="wm-lesson-actions">' +
          '<button class="wm-lesson-learn" data-lesson="' + _wmEsc(name) + '" title="Learn"' +
            (canLearn ? "" : " disabled") + ">&#9654; Learn</button>" +
          '<button class="wm-lesson-rename" data-lesson="' + _wmEsc(name) + '" title="Rename"><i data-lucide="pencil" style="width:14px;height:14px;pointer-events:none"></i></button>' +
          '<button class="wm-lesson-del" data-lesson="' + _wmEsc(name) + '" title="Delete"><i data-lucide="x" style="width:14px;height:14px;pointer-events:none"></i></button>' +
        '</div>';

      (function (lessonName, canLearnFlag) {
        card.querySelector(".wm-lesson-info").onclick = function () { wmOpenLesson(lessonName); };
        var learnBtn = card.querySelector(".wm-lesson-learn");
        if (learnBtn && canLearnFlag) learnBtn.onclick = function (e) {
          e.stopPropagation();
          wmStartLearning(lessonName);
        };
        card.querySelector(".wm-lesson-rename").onclick = function (e) {
          e.stopPropagation();
          wmRenameLesson(lessonName);
        };
        card.querySelector(".wm-lesson-del").onclick = function (e) {
          e.stopPropagation();
          wmDeleteLesson(lessonName);
        };
      })(name, canLearn);

      container.appendChild(card);
    }
    if (typeof lucide !== "undefined") lucide.createIcons();
  } catch (err) {
    _wmEl("wm-lessons-container").innerHTML =
      '<div class="wm-empty">No word lists yet.<br>Create one to get started!</div>';
  }
}

/** @tag MY_WORDS */
async function wmCreateLesson() {
  var input = _wmEl("wm-new-lesson");
  var name = input.value.trim();
  if (!name) return;
  try {
    await _wmApi(_WM_API + "/lessons", { method: "POST", body: JSON.stringify({ name: name }) });
    input.value = "";
    renderLessonList();
  } catch (err) {
    toast(err.message, "error");
  }
}

/** @tag MY_WORDS */
async function wmRenameLesson(oldName) {
  var newName = prompt('New name for "' + oldName.replace(/_/g, " ") + '":', oldName);
  if (!newName || newName.trim() === oldName) return;
  try {
    await _wmApi(_WM_API + "/lessons/" + encodeURIComponent(oldName) + "/rename", {
      method: "PUT",
      body: JSON.stringify({ name: newName.trim() }),
    });
    renderLessonList();
  } catch (err) {
    toast(err.message, "error");
  }
}

/** @tag MY_WORDS */
async function wmDeleteLesson(name) {
  if (!confirm('Delete "' + name.replace(/_/g, " ") + '" and all its words?')) return;
  try {
    await _wmApi(_WM_API + "/lessons/" + encodeURIComponent(name), { method: "DELETE" });
    renderLessonList();
  } catch (err) {
    toast(err.message, "error");
  }
}

// ── Lesson Detail ─────────────────────────────────────────────────────────────

/**
 * Open the word-editor view for a specific lesson.
 * @tag MY_WORDS
 */
async function wmOpenLesson(name) {
  _wmState.currentLesson = name;
  var body = _wmEl("wm-body");
  body.innerHTML =
    '<div class="wm-detail">' +
      '<button class="wm-back-btn" id="wm-back">&#8592; Back to Lists</button>' +
      '<div class="wm-detail-title">' + name.replace(/_/g, " ") + "</div>" +

      '<div class="wm-mode-toggle">' +
        '<button class="wm-mode-btn active" data-mode="manual">' +
          '<i data-lucide="pencil" style="width:13px;height:13px;vertical-align:-2px;stroke-width:1.5"></i>' +
          " Direct Input</button>" +
        '<button class="wm-mode-btn" data-mode="ai">AI Assist</button>' +
      "</div>" +

      '<div class="wm-form" id="wm-form">' +
        '<div class="wm-form-row">' +
          '<input type="text" id="wm-word" class="wm-input wm-input-word" placeholder="Word" maxlength="60" />' +
          '<input type="text" id="wm-pos" class="wm-input wm-input-pos" placeholder="Part of speech" maxlength="20" />' +
        "</div>" +
        '<div id="wm-manual-fields">' +
          '<div class="wm-form-row"><input type="text" id="wm-def" class="wm-input" placeholder="Definition" maxlength="200" /></div>' +
          '<div class="wm-form-row"><input type="text" id="wm-example" class="wm-input" placeholder="Example sentence" maxlength="300" /></div>' +
        "</div>" +
        '<div class="wm-ai-section hidden" id="wm-ai-fields">' +
          '<button id="wm-btn-ai" class="wm-btn-ai">Generate with AI</button>' +
          '<div id="wm-ai-result" class="wm-ai-result hidden"></div>' +
        "</div>" +
        '<button id="wm-btn-add" class="wm-btn-primary wm-btn-add">+ Add Word</button>' +
      "</div>" +

      '<div class="wm-wordlist-title">Words <span id="wm-word-count" class="wm-word-count">0</span></div>' +
      '<div id="wm-wordlist" class="wm-wordlist"></div>' +
    "</div>";

  _wmEl("wm-back").onclick = function () { renderLessonList(); };
  if (typeof lucide !== "undefined") lucide.createIcons();

  body.querySelectorAll(".wm-mode-btn").forEach(function (btn) {
    btn.onclick = function () {
      _wmState.mode = btn.dataset.mode;
      body.querySelectorAll(".wm-mode-btn").forEach(function (b) { b.classList.remove("active"); });
      btn.classList.add("active");
      _wmEl("wm-manual-fields").classList.toggle("hidden", _wmState.mode === "ai");
      _wmEl("wm-ai-fields").classList.toggle("hidden", _wmState.mode === "manual");
      _wmEl("wm-ai-result").classList.add("hidden");
      _wmEl("wm-ai-result").innerHTML = "";
    };
  });

  _wmEl("wm-btn-ai").onclick = wmGenerateAI;
  _wmEl("wm-btn-add").onclick = wmAddWord;
  _wmEl("wm-word").onkeydown = function (e) {
    if (e.key === "Enter") {
      if (_wmState.mode === "ai" && !_wmEl("wm-ai-def")) wmGenerateAI();
      else wmAddWord();
    }
  };

  await wmLoadWords();
}

// ── Init ──────────────────────────────────────────────────────────────────────

/** @tag MY_WORDS */
function _wmInit() {
  var btn = _wmEl("btn-word-manager");
  if (btn) btn.addEventListener("click", wmOpen);
  var closeBtn = _wmEl("wm-close");
  if (closeBtn) closeBtn.addEventListener("click", wmClose);
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", _wmInit);
} else {
  _wmInit();
}
