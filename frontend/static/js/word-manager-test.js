/* ================================================================
   word-manager-test.js — Word Manager: weekly test flow
   Section: English
   Dependencies: word-manager.js (_wmEl, _wmEsc, renderLessonList — loaded first in bundle-c)
   API endpoints:
     GET  /api/mywords/weekly-test
     POST /api/mywords/weekly-test/result
   ================================================================ */

/**
 * Render the Weekly Test status bar above the lesson list.
 * Shows total word count; enables Start when >= min_required words exist.
 * @tag MY_WORDS @tag WEEKLY_TEST
 */
async function renderWeeklyTestBar() {
  var bar = _wmEl("wm-weekly-test-bar");
  if (!bar) return;
  try {
    var res = await fetch("/api/mywords/weekly-test");
    if (!res.ok) { bar.innerHTML = ""; return; }
    var d = await res.json();
    var total = d.total_word_count || 0;
    var need = d.min_required || 50;
    var ok = !!d.available;
    bar.innerHTML =
      '<div class="wm-wt-bar ' + (ok ? "ready" : "locked") + '">' +
        '<div class="wm-wt-info">' +
          '<span class="wm-wt-title">Weekly Test</span>' +
          '<span class="wm-wt-sub">' +
            (ok
              ? "Ready — " + total + " words available"
              : (need - total) + " more words needed (" + total + "/" + need + ")") +
          "</span>" +
        "</div>" +
        '<button id="wm-wt-start" class="wm-btn-primary" ' + (ok ? "" : "disabled") + ">Start</button>" +
      "</div>";
    var btn = _wmEl("wm-wt-start");
    if (btn && ok) btn.onclick = wmStartWeeklyTest;
  } catch (err) {
    bar.innerHTML = "";
  }
}

/**
 * Run the Weekly Test: definition prompt → user types word → auto-grade → submit result.
 * @tag MY_WORDS @tag WEEKLY_TEST
 */
async function wmStartWeeklyTest() {
  var data;
  try {
    var res = await fetch("/api/mywords/weekly-test");
    data = await res.json();
    if (!data.available) { toast("Not enough words yet.", "warn"); return; }
  } catch (err) { toast("Failed to load test.", "error"); return; }

  var testWords = data.words || [];
  if (!testWords.length) return;

  var idx = 0, correct = 0;
  var body = _wmEl("wm-body");

  function renderQ() {
    if (idx >= testWords.length) { submit(); return; }
    var w = testWords[idx];
    body.innerHTML =
      '<div class="wm-detail">' +
        '<div class="wm-detail-title">Weekly Test  ' +
          '<span class="wm-word-count">' + (idx + 1) + " / " + testWords.length + "</span></div>" +
        '<div class="wm-wt-def">' + _wmEsc(w.definition || "(no definition)") + "</div>" +
        (w.example
          ? '<div class="wm-wt-ex">' +
              _wmEsc(w.example).replace(new RegExp(_wmEsc(w.word), "ig"), "____") +
            "</div>"
          : "") +
        '<input type="text" id="wm-wt-input" class="wm-input" placeholder="Type the word..." autocomplete="off" />' +
        '<button id="wm-wt-submit" class="wm-btn-primary" style="margin-top:12px;">Submit</button>' +
        '<div id="wm-wt-fb" class="wm-wt-fb"></div>' +
      "</div>";

    var input = _wmEl("wm-wt-input");
    input.focus();
    input.onkeydown = function (e) { if (e.key === "Enter") grade(); };
    _wmEl("wm-wt-submit").onclick = grade;

    function grade() {
      var ans = (input.value || "").trim().toLowerCase();
      var truth = (w.word || "").trim().toLowerCase();
      var fb = _wmEl("wm-wt-fb");
      if (ans === truth) {
        correct++;
        fb.className = "wm-wt-fb ok";
        fb.textContent = "Correct!";
      } else {
        fb.className = "wm-wt-fb ng";
        fb.textContent = "Answer: " + w.word;
      }
      input.disabled = true;
      _wmEl("wm-wt-submit").textContent = "Next →";
      _wmEl("wm-wt-submit").onclick = function () { idx++; renderQ(); };
    }
  }

  async function submit() {
    var result = { passed: false, xp_awarded: 0, accuracy: 0 };
    try {
      var r = await fetch("/api/mywords/weekly-test/result", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ correct_count: correct, total_count: testWords.length }),
      });
      result = await r.json();
    } catch (err) {}

    body.innerHTML =
      '<div class="wm-detail" style="text-align:center;">' +
        '<div class="wm-detail-title">' + (result.passed ? "Passed!" : "Keep practicing") + "</div>" +
        '<div style="font-size:48px;font-weight:700;margin:20px 0;">' +
          correct + " / " + testWords.length +
        "</div>" +
        '<div style="color:var(--text-secondary);margin-bottom:16px;">' +
          Math.round((result.accuracy || 0) * 100) + "% accuracy" +
          (result.xp_awarded > 0 ? " · +" + result.xp_awarded + " XP" : "") +
        "</div>" +
        '<button id="wm-wt-done" class="wm-btn-primary">Done</button>' +
      "</div>";
    _wmEl("wm-wt-done").onclick = renderLessonList;
  }

  renderQ();
}
