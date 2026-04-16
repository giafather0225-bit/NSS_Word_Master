/* ================================================================
   collocation.js — Collocation/Chunk Learning bonus stage
   Section: English / Daily Words
   Dependencies: core.js
   API endpoints: GET /api/collocation/today, POST /api/collocation/submit
   ================================================================ */
(function () {
    'use strict';

    /* ── State ──────────────────────────────────────────────── */
    /** @type {Array<{word:string, collocation:string, definition:string, example:string}>} */
    var items = [];
    /** @type {Array<{word:string, collocation:string, blank:string, answer:string, pattern:'A'|'B'}>} */
    var quizItems = [];
    var quizIndex = 0;
    /** @type {Array<{word:string, collocation:string, user_answer:string, correct:boolean}>} */
    var answers = [];
    var cardIndex = 0;
    var submitted = false; // prevent double submit on current question

    /* ── DOM helpers ────────────────────────────────────────── */
    function $id(id) { return document.getElementById(id); }

    /**
     * Escape HTML special characters.
     * @param {string} s
     * @returns {string}
     */
    function esc(s) {
        return String(s || '')
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;');
    }

    /* ── API ────────────────────────────────────────────────── */

    /**
     * Fetch collocation items from the server.
     * @returns {Promise<Array>}
     * @tag DAILY_WORDS
     */
    async function fetchItems() {
        try {
            var res = await fetch('/api/collocation/today');
            if (!res.ok) return [];
            var data = await res.json();
            return Array.isArray(data.items) ? data.items : [];
        } catch (e) {
            console.warn('[Collocation] fetchItems error:', e);
            return [];
        }
    }

    /**
     * Check if collocation data is available (used by finaltest.js to show/hide button).
     * @returns {Promise<boolean>}
     * @tag DAILY_WORDS
     */
    async function checkData() {
        var fetched = await fetchItems();
        return fetched.length > 0;
    }

    /**
     * Submit quiz answers and get XP result from server.
     * @returns {Promise<{correct_count:number, total:number, xp_earned:number, perfect:boolean}>}
     * @tag DAILY_WORDS @tag XP
     */
    async function submitAnswers() {
        try {
            var res = await fetch('/api/collocation/submit', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ grade: 4, answers: answers }),
            });
            if (!res.ok) throw new Error('HTTP ' + res.status);
            return await res.json();
        } catch (e) {
            console.warn('[Collocation] submitAnswers error:', e);
            return { correct_count: 0, total: answers.length, xp_earned: 0, perfect: false };
        }
    }

    /* ── Open ───────────────────────────────────────────────── */

    /**
     * Open the Collocation overlay, fetch data, and start the Learn phase.
     * @tag DAILY_WORDS
     */
    async function open() {
        var overlay = $id('collocation-overlay');
        if (!overlay) return;

        // Show loading state immediately
        overlay.classList.remove('hidden');
        overlay.classList.remove('closing');
        setBody('<div class="coll-loading"><div class="coll-spinner"></div><p>Loading chunk cards…</p></div>');
        setPhaseLabel('');
        setProgress(0);

        items = await fetchItems();
        if (!items.length) {
            setBody('<div class="coll-loading"><p>No collocation data available for your current grade.</p></div>');
            return;
        }

        // Build quiz items now (so they're ready when Learn ends)
        quizItems = items.map(function (item) {
            return buildQuizItem(item);
        });
        answers = [];
        cardIndex = 0;
        quizIndex = 0;
        showLearn();
    }

    /* ── Learn phase ────────────────────────────────────────── */

    /**
     * Render the Learn phase card for the current cardIndex.
     * @tag DAILY_WORDS
     */
    function showLearn() {
        setPhaseLabel('Learn');
        setProgress(cardIndex / items.length);

        var item = items[cardIndex];

        var colHTML = highlightWord(item.collocation, item.word);
        var exHTML  = underlineCollocation(item.example, item.collocation);

        var prevDisabled = cardIndex === 0 ? 'disabled' : '';
        var isLast = cardIndex === items.length - 1;

        var dotsHTML = items.map(function (_, i) {
            return '<div class="coll-dot' + (i === cardIndex ? ' active' : '') + '"></div>';
        }).join('');

        var navHTML = isLast
            ? '<button class="coll-btn-start-quiz" id="coll-start-quiz">Start Quiz →</button>'
            : '<div class="coll-card-nav">' +
                '<button class="coll-btn-nav" id="coll-prev" ' + prevDisabled + '>← Prev</button>' +
                '<button class="coll-btn-nav" id="coll-next">Next →</button>' +
              '</div>';

        setBody(
            '<div class="coll-card-area">' +
                '<div class="coll-card">' +
                    '<div class="coll-card-word">' + esc(item.word) + '</div>' +
                    '<div class="coll-card-divider"></div>' +
                    '<div class="coll-card-collocation">' + colHTML + '</div>' +
                    (item.example ? '<div class="coll-card-example">' + exHTML + '</div>' : '') +
                '</div>' +
                '<div class="coll-dots">' + dotsHTML + '</div>' +
                navHTML +
            '</div>'
        );

        if (isLast) {
            var startBtn = $id('coll-start-quiz');
            if (startBtn) startBtn.addEventListener('click', showQuiz);
        } else {
            var prevBtn = $id('coll-prev');
            var nextBtn = $id('coll-next');
            if (prevBtn) prevBtn.addEventListener('click', function () { cardIndex--; showLearn(); });
            if (nextBtn) nextBtn.addEventListener('click', function () { cardIndex++; showLearn(); });
        }
    }

    /**
     * Wrap the target word in the collocation with a highlight span.
     * Case-insensitive, replaces first occurrence.
     * @param {string} collocation
     * @param {string} word
     * @returns {string} HTML string
     * @tag DAILY_WORDS
     */
    function highlightWord(collocation, word) {
        var escaped = esc(collocation);
        var escapedWord = esc(word);
        var pattern = new RegExp('(' + escapedWord.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + ')', 'i');
        return escaped.replace(pattern, '<span class="coll-highlight">$1</span>');
    }

    /**
     * Underline the collocation phrase inside an example sentence.
     * Case-insensitive, replaces first occurrence.
     * @param {string} example
     * @param {string} collocation
     * @returns {string} HTML string
     * @tag DAILY_WORDS
     */
    function underlineCollocation(example, collocation) {
        if (!example) return '';
        var escaped = esc(example);
        var escapedCol = esc(collocation);
        var pattern = new RegExp('(' + escapedCol.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + ')', 'i');
        return escaped.replace(pattern, '<span class="coll-example-mark">$1</span>');
    }

    /* ── Quiz phase ─────────────────────────────────────────── */

    /**
     * Build a quiz question from a collocation item.
     * Randomly chooses pattern A (word ___) or B (___ other-word).
     * @param {{word:string, collocation:string, definition:string}} item
     * @returns {{word:string, collocation:string, blank:string, answer:string, pattern:string}}
     * @tag DAILY_WORDS
     */
    function buildQuizItem(item) {
        var parts = item.collocation.split(/\s+/);
        var pattern, answer, blank;

        if (parts.length < 2) {
            // Single word — always blank it
            pattern = 'A';
            answer = item.collocation;
            blank = '___';
        } else {
            // Find the target word's position
            var wordLower = item.word.toLowerCase();
            var idx = -1;
            for (var i = 0; i < parts.length; i++) {
                if (parts[i].toLowerCase() === wordLower) { idx = i; break; }
            }

            if (idx === -1) {
                // word not found literally — blank last token
                idx = parts.length - 1;
            }

            // Randomly pick: blank the word (A) or blank the other half (B)
            var usePatternA = Math.random() < 0.5;
            if (usePatternA || parts.length === 1) {
                // Pattern A: blank the target word
                pattern = 'A';
                answer = parts[idx];
                var clonedA = parts.slice();
                clonedA[idx] = '___';
                blank = clonedA.join(' ');
            } else {
                // Pattern B: blank a non-target word
                var otherIdx = idx === 0 ? 1 : 0;
                pattern = 'B';
                answer = parts[otherIdx];
                var clonedB = parts.slice();
                clonedB[otherIdx] = '___';
                blank = clonedB.join(' ');
            }
        }

        return {
            word: item.word,
            collocation: item.collocation,
            blank: blank,
            answer: answer,
            definition: item.definition || '',
        };
    }

    /**
     * Render the Quiz phase for the current quizIndex.
     * @tag DAILY_WORDS
     */
    function showQuiz() {
        submitted = false;
        setPhaseLabel('Quiz  ' + (quizIndex + 1) + ' / ' + quizItems.length);
        setProgress((quizIndex + 0.5) / quizItems.length);

        var q = quizItems[quizIndex];
        var promptHTML = esc(q.blank).replace('___',
            '<span class="coll-blank" aria-label="blank"></span>');

        setBody(
            '<div class="coll-quiz-area">' +
                '<div class="coll-quiz-counter">' + (quizIndex + 1) + ' / ' + quizItems.length + '</div>' +
                '<div class="coll-quiz-card">' +
                    '<div class="coll-quiz-prompt">' + promptHTML + '</div>' +
                    (q.definition ? '<div class="coll-quiz-def">' + esc(q.definition) + '</div>' : '') +
                    '<div class="coll-quiz-input-wrap">' +
                        '<input class="coll-quiz-inp" id="coll-inp" type="text" ' +
                               'autocomplete="off" spellcheck="false" ' +
                               'placeholder="Type the missing word…">' +
                        '<div class="coll-quiz-feedback" id="coll-feedback"></div>' +
                    '</div>' +
                    '<button class="coll-btn-submit" id="coll-submit">Check Answer</button>' +
                '</div>' +
            '</div>'
        );

        var inp = $id('coll-inp');
        var submitBtn = $id('coll-submit');
        if (inp) {
            inp.focus();
            inp.addEventListener('input', function () {
                inp.value = inp.value.toLowerCase();
            });
            inp.addEventListener('keydown', function (e) {
                if (e.key === 'Enter') checkAnswer();
            });
        }
        if (submitBtn) submitBtn.addEventListener('click', checkAnswer);
    }

    /**
     * Evaluate the user's answer for the current quiz question.
     * Shows feedback then advances after a short delay.
     * @tag DAILY_WORDS
     */
    function checkAnswer() {
        if (submitted) return;
        var inp = $id('coll-inp');
        var fb  = $id('coll-feedback');
        var btn = $id('coll-submit');
        if (!inp) return;

        var q = quizItems[quizIndex];
        var userAns = inp.value.trim().toLowerCase();
        var correctAns = q.answer.trim().toLowerCase();
        var isCorrect = (userAns === correctAns);

        submitted = true;
        inp.disabled = true;
        if (btn) btn.disabled = true;

        // Record answer
        answers.push({
            word: q.word,
            collocation: q.collocation,
            user_answer: userAns,
            correct: isCorrect,
        });

        if (isCorrect) {
            inp.classList.add('correct');
            if (fb) { fb.textContent = '✓ Correct!'; fb.className = 'coll-quiz-feedback correct'; }
        } else {
            inp.classList.add('wrong');
            if (fb) {
                fb.textContent = '✕  Answer: ' + q.answer;
                fb.className = 'coll-quiz-feedback wrong';
            }
        }

        setTimeout(function () {
            quizIndex++;
            if (quizIndex < quizItems.length) {
                submitted = false;
                showQuiz();
            } else {
                showResult();
            }
        }, isCorrect ? 900 : 1800);
    }

    /* ── Result phase ───────────────────────────────────────── */

    /**
     * Submit answers to server, then render the Result screen.
     * @tag DAILY_WORDS @tag XP
     */
    async function showResult() {
        setPhaseLabel('Result');
        setProgress(1);
        setBody('<div class="coll-loading"><div class="coll-spinner"></div><p>Calculating score…</p></div>');

        var result = await submitAnswers();

        var correctCount = result.correct_count;
        var total        = result.total;
        var xpEarned     = result.xp_earned;
        var perfect      = result.perfect;

        var icon = perfect ? '✦' : (correctCount >= Math.ceil(total / 2) ? '✓' : '✕');

        setBody(
            '<div class="coll-result-area">' +
                '<div class="coll-result-score-wrap">' +
                    '<div class="coll-result-icon">' + icon + '</div>' +
                    '<div class="coll-result-score">' + correctCount + '<span style="font-size:28px;font-weight:400;color:var(--text-secondary);">/' + total + '</span></div>' +
                    '<div class="coll-result-score-sub">Questions correct</div>' +
                '</div>' +
                (xpEarned > 0
                    ? '<div class="coll-result-xp">+' + xpEarned + ' XP earned!</div>'
                    : '') +
                (perfect
                    ? '<div class="coll-result-perfect-msg">✦ Perfect score! Keep it up!</div>'
                    : '') +
                '<button class="coll-btn-home" id="coll-home-btn">Back to Home</button>' +
            '</div>'
        );

        var homeBtn = $id('coll-home-btn');
        if (homeBtn) {
            homeBtn.addEventListener('click', function () {
                closeOverlay();
                // Navigate to home if available
                if (typeof switchView === 'function') switchView('home');
                else if (typeof window.goHome === 'function') window.goHome();
            });
        }
    }

    /* ── Helpers ────────────────────────────────────────────── */

    /**
     * Replace the body content of the overlay.
     * @param {string} html
     */
    function setBody(html) {
        var body = $id('coll-body');
        if (body) body.innerHTML = html;
    }

    /**
     * Update the phase label in the header.
     * @param {string} text
     */
    function setPhaseLabel(text) {
        var el = $id('coll-phase-label');
        if (el) el.textContent = text ? 'Phase — ' + text : '';
    }

    /**
     * Update the progress bar fill (0–1 ratio).
     * @param {number} ratio
     */
    function setProgress(ratio) {
        var fill = $id('coll-progress-fill');
        if (fill) fill.style.width = Math.round(ratio * 100) + '%';
    }

    /**
     * Close the collocation overlay with a fade animation.
     * @tag DAILY_WORDS
     */
    function closeOverlay() {
        var overlay = $id('collocation-overlay');
        if (!overlay) return;
        overlay.classList.add('closing');
        setTimeout(function () {
            overlay.classList.add('hidden');
            overlay.classList.remove('closing');
        }, 200);
    }

    /* ── Init ───────────────────────────────────────────────── */
    document.addEventListener('DOMContentLoaded', function () {
        var closeBtn = $id('coll-close-btn');
        if (closeBtn) closeBtn.addEventListener('click', closeOverlay);
    });

    /* ── Public API ─────────────────────────────────────────── */
    window.Collocation = {
        /** Open the overlay and start the Learn phase. */
        open: open,
        /** Returns a Promise<boolean> — true if data is available for the current grade. */
        checkData: checkData,
    };

}());
