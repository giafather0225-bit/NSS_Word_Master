/* ══════════════════════════════════════════════════════════════
   FINAL TEST — Independent exam controller
   • Part 1: Multiple Choice (20 Qs, one at a time)
   • Part 2: Fill-in-all    (all 20 at once, scroll)
   • 30-min timer, 90% pass threshold
   • No dependency on child.js internals
   ══════════════════════════════════════════════════════════════ */
(function () {
    'use strict';

    /* ── Constants ──────────────────────────────────────────── */
    var PASS_PCT       = 90;           // pass threshold %
    var TIMER_SEC      = 30 * 60;      // 30 minutes
    var WARN_SEC       = 5  * 60;      // last 5 min → timer turns red
    var REQUIRED       = ['PREVIEW', 'A', 'B', 'C', 'D'];

    /* ── State ──────────────────────────────────────────────── */
    var words       = [];
    var mcOptions   = [];   // [[opt,opt,opt,opt], …] per word
    var mcAnswers   = {};   // word.id → selected answer string
    var fillAnswers = [];   // user's typed answers
    var mcIndex     = 0;
    var timerID     = null;
    var secsLeft    = TIMER_SEC;
    var phase       = null; // 'mc' | 'fill' | 'result'
    var ctx         = {};   // {subject, textbook, lesson}

    /* ── DOM helpers ────────────────────────────────────────── */
    function $id(id)  { return document.getElementById(id); }
    function eo(suf)  { return $id('eo-' + suf); }

    /* ── Utility ────────────────────────────────────────────── */
    function shuffle(arr) {
        var a = arr.slice();
        for (var i = a.length - 1; i > 0; i--) {
            var j = Math.floor(Math.random() * (i + 1));
            var t = a[i]; a[i] = a[j]; a[j] = t;
        }
        return a;
    }

    function esc(s) {
        return String(s || '')
            .replace(/&/g,'&amp;').replace(/</g,'&lt;')
            .replace(/>/g,'&gt;').replace(/"/g,'&quot;');
    }

    /* ── Context ────────────────────────────────────────────── */
    function getCtx() {
        var tab = document.querySelector('.sb-subject-tab.active');
        var subj = tab ? tab.textContent.trim() : 'English';
        var tb   = ($id('textbook-select') || {}).value || '';
        var les  = ($id('lesson-select')   || {}).value || '';
        return { subject: subj, textbook: tb, lesson: les };
    }

    /* ── LocalStorage keys ──────────────────────────────────── */
    function doneKey(c)   { return 'nss_done_'       + c.subject + '_' + c.textbook + '_' + c.lesson; }
    function passedKey(c) { return 'nss_ft_passed_'  + c.subject + '_' + c.textbook + '_' + c.lesson; }

    function allStagesDone(c) {
        try {
            var arr = JSON.parse(localStorage.getItem(doneKey(c)) || '[]');
            return REQUIRED.every(function(s) { return arr.indexOf(s) !== -1; });
        } catch(e) { return false; }
    }
    function hasPassed(c) {
        return c.lesson && localStorage.getItem(passedKey(c)) === '1';
    }
    function isUnlocked(c) {
        // Button available when: all stages done currently, OR ever passed 90%+
        return !c.lesson ? false : allStagesDone(c) || hasPassed(c);
    }
    function savePass(c) {
        if (c.lesson) localStorage.setItem(passedKey(c), '1');
    }
    function clearStages(c) {
        if (c.lesson) localStorage.removeItem(doneKey(c));
    }

    /* ── btn-exam: keep enabled if ever passed ──────────────── */
    function updateLockIcons() {
        var c = getCtx();
        var examLock = $id('lock-exam');
        var examBtn = $id('btn-exam');
        if (examLock && examBtn) {
            if (isUnlocked(c)) {
                examLock.style.display = 'none';
                examBtn.classList.remove('locked');
            } else {
                examLock.style.display = '';
                examBtn.classList.add('locked');
            }
        }
    }

    function refreshExamBtn() {
        var btn = $id('btn-exam');
        if (!btn) return;
        var c = getCtx();
        if (!c.lesson) return;
        updateLockIcons();
            if (isUnlocked(c) && btn.disabled) {
            _refreshing = true;
            btn.disabled = false;
            _refreshing  = false;
        }
    }

    var _refreshing = false;

    function setupBtnOverride() {
        var btn = $id('btn-exam');
        if (!btn) return;

        // Watch disabled attribute changes from child.js
        var obs = new MutationObserver(function() {
            if (!_refreshing) refreshExamBtn();
        });
        obs.observe(btn, { attributes: true, attributeFilter: ['disabled'] });

        // Watch lesson selection changes
        document.addEventListener('change', function(e) {
            if (e.target && (e.target.id === 'lesson-select' || e.target.id === 'textbook-select')) {
                setTimeout(refreshExamBtn, 150);
            }
        });

        // Initial check after child.js has had time to set state
        setTimeout(refreshExamBtn, 700);
    }

    /* ── Timer ──────────────────────────────────────────────── */
    function startTimer() {
        secsLeft = TIMER_SEC;
        renderTimer();
        timerID = setInterval(function() {
            secsLeft--;
            renderTimer();
            if (secsLeft <= 0) {
                clearInterval(timerID);
                onTimeUp();
            }
        }, 1000);
    }
    function stopTimer() { if (timerID) { clearInterval(timerID); timerID = null; } }
    function renderTimer() {
        var el = eo('timer');
        if (!el) return;
        var m  = Math.floor(secsLeft / 60);
        var s  = secsLeft % 60;
        el.textContent = (m < 10 ? '0' : '') + m + ':' + (s < 10 ? '0' : '') + s;
        el.classList.toggle('eo-timer-warn', secsLeft <= WARN_SEC);
    }
    function onTimeUp() {
        if (phase === 'mc') {
            // Fill remaining MC with null, jump to Part 2
            while (mcAnswers.length < words.length) mcAnswers.push(null);
            mcIndex = words.length;
            showFill();
        } else if (phase === 'fill') {
            submitFill();
        }
    }

    /* ── Fetch words ────────────────────────────────────────── */
    async function fetchWords(c) {
        var url = '/api/study/' + encodeURIComponent(c.subject) + '/' +
                  encodeURIComponent(c.textbook) + '/' +
                  encodeURIComponent(c.lesson);
        var res = await fetch(url);
        if (!res.ok) throw new Error('HTTP ' + res.status);
        var data = await res.json();
        return data.items || [];
    }

    /* ── Open exam ──────────────────────────────────────────── */
    async function openExam() {
        ctx = getCtx();
        var overlay = $id('exam-overlay');
        if (!overlay || !ctx.lesson) return;

        // Show overlay in loading state
        overlay.classList.remove('hidden');
        eo('crumb').textContent = ctx.lesson;
        eo('part-label').textContent = 'Loading…';
        eo('body').innerHTML =
            '<div class="eo-loading"><div class="eo-spinner"></div><p>Loading test…</p></div>';

        try {
            words = await fetchWords(ctx);
        } catch (e) {
            eo('body').innerHTML = '<div class="eo-msg eo-msg-err">Failed to load test. Please close and try again.</div>';
            return;
        }
        if (!words.length) {
            eo('body').innerHTML = '<div class="eo-msg eo-msg-err">No words found for this lesson.</div>';
            return;
        }

        // (pass flag saved only on 90%+ score, not here)

        // Build MC option sets (1 correct + 3 random wrong)
        words = shuffle(words);
        mcOptions = words.map(function(w) {
            var pool = shuffle(words.filter(function(x) { return x.id !== w.id; }));
            var wrong = pool.slice(0, 3).map(function(x) { return x.answer; });
            return shuffle([w.answer].concat(wrong));
        });

        // Reset state
        mcAnswers   = {};
        fillAnswers = new Array(words.length).fill('');
        mcIndex     = 0;

        startTimer();
        showMC();
    }

    /* ── Part 1: Multiple Choice ────────────────────────────── */
    function showMC() {
        phase = 'mc';
        updateProgress();
        eo('part-label').textContent = 'Part 1 — Multiple Choice  ' + (mcIndex + 1) + ' / ' + words.length;

        var w    = words[mcIndex];
        var opts = mcOptions[mcIndex];
        var def  = getDef(w);

        var optHTML = opts.map(function(opt, i) {
            return '<button class="eo-mc-opt" data-val="' + esc(opt) + '">' +
                       '<span class="eo-mc-num">' + (i + 1) + '</span>' +
                       '<span>' + esc(opt) + '</span>' +
                   '</button>';
        }).join('');

        eo('body').innerHTML =
            '<div class="eo-mc-wrap">' +
                '<div class="eo-mc-q-num">' + (mcIndex + 1) + ' / ' + words.length + '</div>' +
                '<div class="eo-mc-def-card">' + esc(def) + '</div>' +
                '<div class="eo-mc-grid">' + optHTML + '</div>' +
            '</div>';

        eo('body').querySelectorAll('.eo-mc-opt').forEach(function(btn) {
            btn.addEventListener('click', function() { onMCSelect(btn); });
        });
    }

    function onMCSelect(btn) {
        var val     = btn.dataset.val;
        var correct = val === words[mcIndex].answer;
        mcAnswers[words[mcIndex].id] = val;

        // Mark buttons
        btn.classList.add(correct ? 'eo-mc-correct' : 'eo-mc-wrong');
        if (!correct) {
            eo('body').querySelectorAll('.eo-mc-opt').forEach(function(b) {
                if (b.dataset.val === words[mcIndex].answer) b.classList.add('eo-mc-correct');
            });
        }
        eo('body').querySelectorAll('.eo-mc-opt').forEach(function(b) { b.disabled = true; });

        setTimeout(function() {
            mcIndex++;
            if (mcIndex >= words.length) showFill();
            else showMC();
        }, 520);
    }

    /* ── Part 2: Fill-in-all ────────────────────────────────── */
    function showFill() {
        phase = 'fill';
        updateProgress();
        eo('part-label').textContent = 'Part 2 — Fill in the Blank';

        words = shuffle(words);
        var rows = words.map(function(w, i) {
            return '<div class="eo-fill-row">' +
                       '<div class="eo-fill-idx">' + (i + 1) + '</div>' +
                       '<div class="eo-fill-content">' +
                           '<div class="eo-fill-def">' + esc(getDef(w)) + '</div>' +
                           '<input class="eo-fill-inp" type="text" data-idx="' + i + '" ' +
                                  'autocomplete="off" spellcheck="false" ' +
                                  'placeholder="Type the word…" ' +
                                  'value="' + esc(fillAnswers[i] || '') + '">' +
                       '</div>' +
                   '</div>';
        }).join('');

        eo('body').innerHTML =
            '<div class="eo-fill-wrap">' +
                '<p class="eo-fill-desc">Type the correct word for each definition. You can scroll through all questions.</p>' +
                '<div class="eo-fill-list">' + rows + '</div>' +
                '<div class="eo-fill-footer">' +
                    '<button class="eo-btn-primary" id="eo-fill-submit">Submit All Answers</button>' +
                '</div>' +
            '</div>';

        // Focus first empty input
        var first = eo('body').querySelector('.eo-fill-inp');
        if (first) first.focus();

        eo('body').querySelectorAll('.eo-fill-inp').forEach(function(inp) {
            inp.addEventListener('input', function() {
                fillAnswers[+inp.dataset.idx] = inp.value;
            });
            inp.addEventListener('keydown', function(e) {
                if (e.key !== 'Enter') return;
                var nextIdx = +inp.dataset.idx + 1;
                var next = eo('body').querySelector('.eo-fill-inp[data-idx="' + nextIdx + '"]');
                if (next) { next.focus(); next.scrollIntoView({ behavior: 'smooth', block: 'center' }); }
                else submitFill();
            });
        });

        $id('eo-fill-submit').addEventListener('click', submitFill);
    }

    /* ── Submit & Score ─────────────────────────────────────── */
    function submitFill() {
        stopTimer();
        // Flush any un-saved inputs
        if (eo('body')) {
            eo('body').querySelectorAll('.eo-fill-inp').forEach(function(inp) {
                fillAnswers[+inp.dataset.idx] = inp.value.trim();
            });
        }
        showResults();
    }

    function showResults() {
        phase = 'result';
        eo('part-label').textContent = 'Results';
        updateProgress();

        var mcCorrect   = 0;
        var fillCorrect = 0;
        words.forEach(function(w, i) {
            if (mcAnswers[w.id]   && mcAnswers[w.id].toLowerCase()   === w.answer.toLowerCase()) mcCorrect++;
            if (fillAnswers[i] && fillAnswers[i].toLowerCase().trim() === w.answer.toLowerCase()) fillCorrect++;
        });

        var total  = mcCorrect + fillCorrect;
        var maxPts = words.length * 2;
        var pct    = Math.round((total / maxPts) * 100);
        var passed = pct >= PASS_PCT;

        // Save permanent pass on 90%+ — unlocks exam button forever
        if (passed) savePass(ctx);

        eo('body').innerHTML = buildResultsHTML(mcCorrect, fillCorrect, total, maxPts, pct, passed);

        $id('eo-action-btn').addEventListener('click', function() {
            if (passed) {
                // Just close — pass is already saved, exam button stays open
                closeExam();
            } else {
                // Reset learning stages + reload
                clearStages(ctx);
                closeExam();
                setTimeout(function() { location.reload(); }, 300);
            }
        });
    }

    function buildResultsHTML(mcC, fillC, total, maxPts, pct, passed) {
        var icon, headline, msg, btnLabel, btnClass;

        if (passed) {
            icon     = '🎉';
            headline = 'Congratulations! You passed!';
            msg      = 'You scored <strong>' + pct + '%</strong> on ' + esc(ctx.lesson) + '.<br>' +
                       'This lesson is permanently marked as passed. Well done!';
            btnLabel = 'Back to Lessons';
            btnClass = 'eo-btn-primary';
        } else {
            icon     = '💪';
            headline = 'Almost there — you\'ve got this!';
            msg      = 'You scored <strong>' + pct + '%</strong>. You need <strong>90%</strong> to pass.<br>' +
                       'Don\'t give up — review the words and try again!';
            btnLabel = 'Back to Study';
            btnClass = 'eo-btn-primary eo-btn-danger';
        }

        return '<div class="eo-results">' +
            '<div class="eo-res-icon">' + icon + '</div>' +
            '<div class="eo-res-score ' + (passed ? 'eo-res-pass' : 'eo-res-fail') + '">' + pct + '%</div>' +
            '<div class="eo-res-headline">' + headline + '</div>' +
            '<div class="eo-res-msg">' + msg + '</div>' +
            '<div class="eo-res-breakdown">' +
                '<div class="eo-res-row">' +
                    '<span>Part 1 — Multiple Choice</span>' +
                    '<span class="eo-res-pts">' + mcC + ' / ' + words.length + '</span>' +
                '</div>' +
                '<div class="eo-res-row">' +
                    '<span>Part 2 — Fill in the Blank</span>' +
                    '<span class="eo-res-pts">' + fillC + ' / ' + words.length + '</span>' +
                '</div>' +
                '<div class="eo-res-row eo-res-total">' +
                    '<span>Total</span>' +
                    '<span class="eo-res-pts">' + total + ' / ' + maxPts + '</span>' +
                '</div>' +
            '</div>' +
            '<button class="' + btnClass + '" id="eo-action-btn">' + btnLabel + '</button>' +
        '</div>';
    }

    /* ── Helpers ────────────────────────────────────────────── */
    function getDef(w) {
        try {
            var ed = typeof w.extra_data === 'string' ? JSON.parse(w.extra_data) : (w.extra_data || {});
            return ed.definition || ed.meaning || w.question || '(no definition)';
        } catch(e) { return w.question || '(no definition)'; }
    }

    function updateProgress() {
        var fill = eo('progress-fill');
        if (!fill) return;
        var pct = phase === 'mc'     ? Math.round((mcIndex / (words.length * 2)) * 100) :
                  phase === 'fill'   ? 50 :
                  phase === 'result' ? 100 : 0;
        fill.style.width = pct + '%';
    }

    /* ── Close overlay ──────────────────────────────────────── */
    function closeExam() {
        stopTimer();
        var overlay = $id('exam-overlay');
        if (!overlay) return;
        overlay.classList.add('closing');
        setTimeout(function() {
            overlay.classList.add('hidden');
            overlay.classList.remove('closing');
            phase = null;
        }, 250);
    }

    /* ── Init ───────────────────────────────────────────────── */
    document.addEventListener('DOMContentLoaded', function() {
        var examBtn = $id('btn-exam');
        if (!examBtn) return;

        // Capture-phase listener: intercept BEFORE child.js bubble listener
        examBtn.addEventListener('click', function(e) {
            e.stopImmediatePropagation();
            var c = getCtx();
            if (c.lesson && isUnlocked(c)) openExam();
        }, true);

        // Close button
        var closeBtn = $id('eo-close');
        if (closeBtn) closeBtn.addEventListener('click', closeExam);

        // "Ever-unlocked" button management
        setupBtnOverride();
    });

}());
