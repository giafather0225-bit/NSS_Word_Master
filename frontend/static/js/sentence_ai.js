/* ══════════════════════════════════════════════════════════════
   SENTENCE AI — Feedback visual transformer
   Watches #sm-feedback-area and converts child.js plain-text
   output into structured, styled feedback cards.
   No child.js modification required.
   ══════════════════════════════════════════════════════════════ */
(function () {
    'use strict';

    /* ── Parse one feedback line ────────────────────────────── */
    // child.js formatStructuredFeedback output (innerHTML, <br> separated):
    //  "✅ Grammar: …<br>✅ Word Use: …<br>⭐⭐⭐ Creativity: …<br>🎉 …"

    function buildCard(lines) {
        var rows = '';

        lines.forEach(function (raw) {
            // Decode HTML entities (child.js uses escapeHtml)
            var text = raw
                .replace(/&amp;/g, '&').replace(/&lt;/g, '<')
                .replace(/&gt;/g, '>').replace(/&quot;/g, '"')
                .replace(/&#39;/g, "'").trim();

            if (!text) return;

            /* Grammar row */
            if (/^[✅⚠️]\s*Grammar:/i.test(text)) {
                var pass    = text.startsWith('✅');
                var content = text.replace(/^[✅⚠️]\s*Grammar:\s*/i, '');
                rows += buildRow('Grammar', content, pass ? 'pass' : 'fail',
                                 pass ? '✓' : '✗');
                return;
            }

            /* Word Use row */
            if (/^[✅⚠️]\s*Word Use:/i.test(text)) {
                var pass    = text.startsWith('✅');
                var content = text.replace(/^[✅⚠️]\s*Word Use:\s*/i, '');
                rows += buildRow('Word Use', content, pass ? 'pass' : 'fail',
                                 pass ? '✓' : '✗');
                return;
            }

            /* Creativity row */
            if (/^⭐.*Creativity:/i.test(text)) {
                var starCount = (text.match(/⭐/g) || []).length;
                var content   = text.replace(/^⭐+\s*Creativity:\s*/i, '');
                rows += buildCreativity(starCount, content);
                return;
            }

            /* Overall / 🎉 row */
            if (/^🎉/.test(text)) {
                var content = text.replace(/^🎉\s*/, '');
                rows += buildOverall(content);
                return;
            }

            /* Unrecognised line → show as-is */
            rows += '<div class="sm-ai-other">' + esc(text) + '</div>';
        });

        return rows ? '<div class="sm-ai-card">' + rows + '</div>' : null;
    }

    function buildRow(label, content, state, icon) {
        // Split "Fix: corrected sentence" if present (we put it in the grammar/wordUsage row)
        var fix = '';
        var fixMatch = content.match(/\|\s*Fix:\s*(.+)$/i);
        if (fixMatch) {
            fix    = fixMatch[1];
            content = content.slice(0, fixMatch.index).trim();
        }

        var fixHtml = fix
            ? '<div class="sm-ai-fix"><span class="sm-ai-fix-label">✏️ Fix</span>' + esc(fix) + '</div>'
            : '';

        return '<div class="sm-ai-row sm-ai-' + state + '">' +
                   '<span class="sm-ai-icon">' + icon + '</span>' +
                   '<div class="sm-ai-row-body">' +
                       '<span class="sm-ai-label">' + label + '</span>' +
                       '<span class="sm-ai-text">' + esc(content) + '</span>' +
                       fixHtml +
                   '</div>' +
               '</div>';
    }

    function buildCreativity(count, content) {
        var filled = Math.min(5, Math.max(1, count));
        var stars  = '';
        for (var i = 1; i <= 5; i++) {
            stars += '<span class="sm-star ' + (i <= filled ? 'sm-star-on' : '') + '">★</span>';
        }
        return '<div class="sm-ai-row sm-ai-neutral">' +
                   '<span class="sm-ai-icon">✦</span>' +
                   '<div class="sm-ai-row-body">' +
                       '<span class="sm-ai-label">Creativity</span>' +
                       '<div class="sm-ai-stars">' + stars + '</div>' +
                       '<span class="sm-ai-text">' + esc(content) + '</span>' +
                   '</div>' +
               '</div>';
    }

    function buildOverall(content) {
        // Split at "| Fix:" separator that we embed in the overall field
        var fix      = '';
        var fixMatch = content.match(/\|\s*Fix:\s*(.+)$/i);
        if (fixMatch) {
            fix     = fixMatch[1];
            content = content.slice(0, fixMatch.index).trim();
        }

        var fixHtml = fix
            ? '<div class="sm-ai-fix">' +
                  '<span class="sm-ai-fix-label">✏️ Suggested</span>' +
                  esc(fix) +
              '</div>'
            : '';

        return '<div class="sm-ai-overall">' +
                   '<span class="sm-ai-overall-text">' + esc(content) + '</span>' +
                   fixHtml +
               '</div>';
    }

    function esc(s) {
        return String(s || '')
            .replace(/&/g,'&amp;').replace(/</g,'&lt;')
            .replace(/>/g,'&gt;').replace(/"/g,'&quot;');
    }

    /* ── Transform a .sm-feedback div ──────────────────────── */
    function transformFeedback(div) {
        var html   = div.innerHTML || '';
        var lines  = html.split(/<br\s*\/?>/i);
        var result = buildCard(lines);

        if (result) {
            div.innerHTML = result;
            div.classList.add('sm-ai-transformed');
        }
    }

    /* ── MutationObserver on #sm-feedback-area ──────────────── */
    function watchFeedbackArea(area) {
        var obs = new MutationObserver(function (mutations) {
            mutations.forEach(function (m) {
                m.addedNodes.forEach(function (node) {
                    if (node.nodeType !== 1) return;

                    // Direct .sm-feedback child added
                    if (node.classList && node.classList.contains('sm-feedback')) {
                        // Slight delay so child.js finishes writing HTML
                        setTimeout(function () { transformFeedback(node); }, 20);
                        return;
                    }

                    // Or a sm-feedback nested inside (e.g. inside sm-hint wrapper)
                    var inner = node.querySelector && node.querySelector('.sm-feedback');
                    if (inner) {
                        setTimeout(function () { transformFeedback(inner); }, 20);
                    }
                });
            });
        });
        obs.observe(area, { childList: true, subtree: false });
    }

    /* ── Watch for #sm-feedback-area being created (it's ───────
       rendered fresh each word by child.js)                    */
    function init() {
        // Observe #stage for when sm-feedback-area appears
        var stage = document.getElementById('stage');
        if (!stage) return;

        var areaObs = new MutationObserver(function () {
            var area = document.getElementById('sm-feedback-area');
            if (area && !area._sm_watching) {
                area._sm_watching = true;
                watchFeedbackArea(area);
            }
        });
        areaObs.observe(stage, { childList: true, subtree: true });
    }

    document.addEventListener('DOMContentLoaded', init);
}());
