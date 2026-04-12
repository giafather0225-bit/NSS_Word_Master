/* ================================================================
   Unit Test — MC only, up to 3 lessons, retry all / retry wrong
   ================================================================ */
(function() {
    'use strict';

    /* ── Helpers ─────────────────────────────────────────────── */
    function $id(id) { return document.getElementById(id); }
    function esc(s)  { var d = document.createElement('div'); d.textContent = s; return d.innerHTML; }
    function shuffle(arr) {
        var a = arr.slice();
        for (var i = a.length - 1; i > 0; i--) {
            var j = Math.floor(Math.random() * (i + 1));
            var t = a[i]; a[i] = a[j]; a[j] = t;
        }
        return a;
    }

    /* ── State ───────────────────────────────────────────────── */
    var words       = [];
    var mcOptions   = [];
    var mcAnswers   = {};   // word.id → answer
    var mcIndex     = 0;
    var timerID     = null;
    var timeLeft    = 0;
    var selectedLessons = [];
    var allWords    = [];   // keep original for retry-all
    var wrongWords  = [];   // for retry-wrong

    /* ── Context ─────────────────────────────────────────────── */
    function getCtx() {
        var tab  = document.querySelector('.sb-subject-tab.active');
        var subj = tab ? tab.textContent.trim() : 'English';
        var tb   = ($id('textbook-select') || {}).value || '';
        return { subject: subj, textbook: tb };
    }

    /* ── Fetch words for one lesson ──────────────────────────── */
    async function fetchWords(subject, textbook, lesson) {
        var url = '/api/study/' + encodeURIComponent(subject) + '/' +
                  encodeURIComponent(textbook) + '/' +
                  encodeURIComponent(lesson);
        var res = await fetch(url);
        if (!res.ok) throw new Error('HTTP ' + res.status);
        var data = await res.json();
        return data.items || [];
    }

    /* ── Get definition ──────────────────────────────────────── */
    function getDef(w) {
        return w.question || w.definition || w.meaning || '';
    }

    /* ── Timer ───────────────────────────────────────────────── */
    function startTimer(minutes) {
        timeLeft = minutes * 60;
        updateTimerDisplay();
        if (timerID) clearInterval(timerID);
        timerID = setInterval(function() {
            timeLeft--;
            updateTimerDisplay();
            if (timeLeft <= 0) {
                clearInterval(timerID);
                timerID = null;
                showResults();
            }
        }, 1000);
    }

    function updateTimerDisplay() {
        var el = $id('ut-timer');
        if (!el) return;
        var m = Math.floor(timeLeft / 60);
        var s = timeLeft % 60;
        el.textContent = m + ':' + (s < 10 ? '0' : '') + s;
        if (timeLeft <= 60) el.classList.add('ut-timer-warn');
        else el.classList.remove('ut-timer-warn');
    }

    function stopTimer() {
        if (timerID) { clearInterval(timerID); timerID = null; }
    }

    /* ── Progress (handled inside showMC) ────────────────────── */

    /* ── Build MC options ────────────────────────────────────── */
    function buildMCOptions(wordList) {
        return wordList.map(function(w) {
            var pool = shuffle(wordList.filter(function(x) { return x.id !== w.id; }));
            var wrong = pool.slice(0, 3).map(function(x) { return x.answer; });
            return shuffle([w.answer].concat(wrong));
        });
    }

    /* ── Lesson Selection UI ─────────────────────────────────── */
    function showLessonSelector() {
        var overlay = $id('ut-overlay');
        if (!overlay) return;

        var sel = $id('lesson-select');
        if (!sel) return;

        var lessons = [];
        for (var i = 0; i < sel.options.length; i++) {
            var opt = sel.options[i];
            if (opt.value) lessons.push(opt.value);
        }

        var html = '<div class="ut-container">' +
            '<div class="ut-header">' +
                '<h2 class="ut-title">Unit Test</h2>' +
                '<button class="ut-close-btn" id="ut-close-btn">&times;</button>' +
            '</div>' +
            '<div class="ut-selector">' +
                '<p class="ut-desc">Select up to <strong>3 lessons</strong> to test</p>' +
                '<div class="ut-lesson-list" id="ut-lesson-list">';

        lessons.forEach(function(les) {
            html += '<label class="ut-lesson-item">' +
                '<input type="checkbox" class="ut-lesson-cb" value="' + esc(les) + '"> ' +
                '<span class="ut-lesson-name">' + esc(les) + '</span>' +
            '</label>';
        });

        html += '</div>' +
                '<div class="ut-selected-info" id="ut-selected-info">0 lessons selected</div>' +
                '<button class="ut-start-btn" id="ut-start-btn" disabled>Start Unit Test</button>' +
            '</div>' +
        '</div>';

        overlay.innerHTML = html;
        overlay.classList.remove('hidden');

        // Events
        $id('ut-close-btn').addEventListener('click', closeUT);

        var cbs = overlay.querySelectorAll('.ut-lesson-cb');
        cbs.forEach(function(cb) {
            cb.addEventListener('change', function() {
                var checked = overlay.querySelectorAll('.ut-lesson-cb:checked');
                if (checked.length > 3) {
                    cb.checked = false;
                    return;
                }
                var info = $id('ut-selected-info');
                var btn  = $id('ut-start-btn');
                info.textContent = checked.length + ' lesson' + (checked.length !== 1 ? 's' : '') + ' selected';
                btn.disabled = checked.length === 0;
            });
        });

        $id('ut-start-btn').addEventListener('click', function() {
            var checked = overlay.querySelectorAll('.ut-lesson-cb:checked');
            selectedLessons = [];
            checked.forEach(function(cb) { selectedLessons.push(cb.value); });
            startTest();
        });
    }

    /* ── Start Test ──────────────────────────────────────────── */
    async function startTest(retryWords) {
        var overlay = $id('ut-overlay');
        var ctx = getCtx();

        if (retryWords) {
            // Retry mode
            allWords = retryWords.slice();
            words = shuffle(retryWords);
        } else {
            // Fresh start — fetch from selected lessons
            overlay.innerHTML = '<div class="ut-container"><div class="ut-loading">Loading words...</div></div>';

            var fetched = [];
            for (var i = 0; i < selectedLessons.length; i++) {
                try {
                    var items = await fetchWords(ctx.subject, ctx.textbook, selectedLessons[i]);
                    fetched = fetched.concat(items);
                } catch(e) {
                    console.error('Failed to fetch', selectedLessons[i], e);
                }
            }

            if (!fetched.length) {
                overlay.innerHTML = '<div class="ut-container"><div class="ut-msg ut-msg-err">No words found.</div></div>';
                return;
            }

            // Deduplicate by id
            var seen = {};
            allWords = [];
            fetched.forEach(function(w) {
                if (!seen[w.id]) { seen[w.id] = true; allWords.push(w); }
            });

            words = shuffle(allWords);
        }

        // Limit: 1 lesson=20, 2=40, 3=60
        var limit = selectedLessons.length * 20;
        if (words.length > limit) words = words.slice(0, limit);

        mcOptions = buildMCOptions(words);
        mcAnswers = {};
        mcIndex   = 0;
        wrongWords = [];

        // Timer: 1 lesson=10min, 2=20min, 3=30min
        var minutes = selectedLessons.length * 10;

        // Render test UI
        var html = '<div class="ut-container">' +
            '<div class="ut-header">' +
                '<h2 class="ut-title">Unit Test</h2>' +
                '<div class="ut-header-right">' +
                    '<span class="ut-timer" id="ut-timer"></span>' +
                    '<span class="ut-progress" id="ut-progress"></span>' +
                '</div>' +
                '<button class="ut-close-btn" id="ut-close-btn">&times;</button>' +
            '</div>' +
            '<div class="ut-progress-track"><div class="ut-progress-bar" id="ut-progress-bar"></div></div>' +
            '<div class="ut-body" id="ut-body"></div>' +
        '</div>';

        overlay.innerHTML = html;
        $id('ut-close-btn').addEventListener('click', closeUT);

        startTimer(minutes);
        showMC();
    }

    var PAGE_SIZE = 3;
    var pageAnswered = 0;

    /* ── Show MC Page (3 questions) ──────────────────────────── */
    function showMC() {
        var body = $id('ut-body');
        if (!body) return;

        var startIdx = mcIndex;
        var endIdx   = Math.min(mcIndex + PAGE_SIZE, words.length);
        var pageTotal = endIdx - startIdx;
        pageAnswered = 0;

        // Update progress to show current page range
        var el = $id('ut-progress');
        if (el) el.textContent = startIdx + 1 + '-' + endIdx + ' / ' + words.length;
        var bar = $id('ut-progress-bar');
        if (bar) bar.style.width = (endIdx / words.length * 100) + '%';

        var html = '<div class="ut-page">';

        for (var qi = startIdx; qi < endIdx; qi++) {
            var w    = words[qi];
            var opts = mcOptions[qi];
            var def  = getDef(w);

            html += '<div class="ut-q-card" data-qi="' + qi + '">' +
                '<div class="ut-q-header">' +
                    '<span class="ut-q-badge">Q' + (qi + 1) + '</span>' +
                    '<span class="ut-q-def-text">' + esc(def) + '</span>' +
                '</div>' +
                '<div class="ut-q-opts">';

            opts.forEach(function(opt, i) {
                html += '<button class="ut-mc-opt" data-qi="' + qi + '" data-val="' + esc(opt) + '">' +
                    '<span class="ut-opt-num">' + (i + 1) + '</span>' + esc(opt) +
                '</button>';
            });

            html += '</div></div>';
        }

        html += '</div>';
        body.innerHTML = html;

        body.querySelectorAll('.ut-mc-opt').forEach(function(btn) {
            btn.addEventListener('click', function() { onMCSelect(btn, pageTotal); });
        });
    }

    /* ── MC Select Handler ───────────────────────────────────── */
    function onMCSelect(btn, pageTotal) {
        var qi      = parseInt(btn.dataset.qi);
        var val     = btn.dataset.val;
        var w       = words[qi];
        var card    = btn.closest('.ut-q-card');

        // Prevent double-click on same card
        if (card.classList.contains('ut-answered')) return;
        card.classList.add('ut-answered');

        var correct = val.toLowerCase() === w.answer.toLowerCase();
        mcAnswers[w.id] = val;

        btn.classList.add(correct ? 'ut-mc-correct' : 'ut-mc-wrong');
        if (!correct) {
            wrongWords.push(w);
            card.querySelectorAll('.ut-mc-opt').forEach(function(b) {
                if (b.dataset.val.toLowerCase() === w.answer.toLowerCase()) b.classList.add('ut-mc-correct');
            });
        }
        card.querySelectorAll('.ut-mc-opt').forEach(function(b) { b.disabled = true; });

        pageAnswered++;
        if (pageAnswered >= pageTotal) {
            setTimeout(function() {
                mcIndex += pageTotal;
                if (mcIndex >= words.length) showResults();
                else showMC();
            }, 700);
        }
    }

    /* ── Results ─────────────────────────────────────────────── */
    function showResults() {
        stopTimer();
        var total   = words.length;
        var correct = 0;
        words.forEach(function(w) {
            if (mcAnswers[w.id] && mcAnswers[w.id].toLowerCase() === w.answer.toLowerCase()) correct++;
        });
        var pct = Math.round(correct / total * 100);
        var passed = pct >= 90;

        var body = $id('ut-body');
        if (!body) return;
        var lessonsStr = selectedLessons.join(', ');

        var html = '<div class="ut-result-wrap">' +
            '<div class="ut-result ' + (passed ? 'ut-result-pass' : 'ut-result-fail') + '">' +
                '<div class="ut-result-icon">' + (passed ? '🎉' : '📝') + '</div>' +
                '<div class="ut-result-score">' + pct + '%</div>' +
                '<div class="ut-result-detail">' + correct + ' / ' + total + ' correct</div>' +
                '<div class="ut-result-lessons">Lessons: ' + esc(lessonsStr) + '</div>' +
                '<div class="ut-result-status">' + (passed ? 'PASSED!' : 'Need 90% to pass') + '</div>' +
                '<div class="ut-result-btns">';

        html += '<button class="ut-retry-btn ut-retry-all" id="ut-retry-all">🔄 Retry All</button>';

        if (wrongWords.length > 0) {
            html += '<button class="ut-retry-btn ut-retry-wrong" id="ut-retry-wrong">❌ Retry Wrong (' + wrongWords.length + ')</button>';
        }

        html += '</div></div>' +
            '<div class="ut-result-divider"></div>' +
            '<button class="ut-back-btn" id="ut-back-btn">← Select Lessons</button>' +
        '</div>';

        body.innerHTML = html;

        // Update progress bar to 100%
        var bar = $id('ut-progress-bar');
        if (bar) bar.style.width = '100%';

        $id('ut-back-btn').addEventListener('click', function() {
            showLessonSelector();
        });

        $id('ut-retry-all').addEventListener('click', function() {
            startTest(allWords);
        });

        if ($id('ut-retry-wrong')) {
            $id('ut-retry-wrong').addEventListener('click', function() {
                startTest(wrongWords);
            });
        }
    }

    /* ── Close ───────────────────────────────────────────────── */
    function closeUT() {
        stopTimer();
        var overlay = $id('ut-overlay');
        if (overlay) {
            overlay.innerHTML = '';
            overlay.classList.add('hidden');
        }
    }

    /* ── Init: attach to button ──────────────────────────────── */
    function init() {
        // Remove Speed Runner button
        var speedBtn = $id('btn-speed-runner');
        if (speedBtn) speedBtn.remove();

        // Attach Unit Test button
        var btn = $id('btn-kigoosa');
        if (btn) {
            btn.addEventListener('click', function() {
                showLessonSelector();
            });
        }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
