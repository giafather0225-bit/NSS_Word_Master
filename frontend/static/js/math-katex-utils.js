/* ================================================================
   math-katex-utils.js — KaTeX rendering helpers
   Section: Math
   Dependencies: KaTeX (CDN) — window.katex, window.renderMathInElement
   API endpoints: none
   Exports (window):
     window.mathRenderIn(el)       — scan el and render math in delimiters
     window.mathRenderText(str)    — return HTML with math rendered in-place
     window.mathAutoMathify(str)   — heuristic: wrap a/b and × as LaTeX
   ================================================================ */

/* global katex, renderMathInElement */

// ── Delimiter config ───────────────────────────────────────
// Support $...$ and \(...\) (inline), $$...$$ and \[...\] (block).
// Note: single $ is ambiguous with currency, but this app is K–6 math so
// we opt in. Authors can always escape with \$ if they need a literal $.
const _KATEX_DELIMS = [
    { left: '$$', right: '$$', display: true },
    { left: '\\[', right: '\\]', display: true },
    { left: '\\(', right: '\\)', display: false },
    { left: '$',  right: '$',  display: false },
];

const _KATEX_OPTS = {
    delimiters: _KATEX_DELIMS,
    throwOnError: false,
    errorColor: '#c0392b',
    strict: 'ignore',
    trust: false,
    macros: {
        '\\x': '\\times',
    },
};

// ── Heuristic auto-mathify ─────────────────────────────────
/**
 * Convert common K–6 plain-text math notation into LaTeX wrapped in \( \).
 * Only fires inside segments that already look math-y (digits + operators).
 * Called by mathRenderText for author convenience — NOT by mathRenderIn,
 * which trusts explicit delimiters only.
 * @tag MATH @tag KATEX
 */
function mathAutoMathify(str) {
    if (!str || typeof str !== 'string') return str || '';
    // Skip if the string already contains an explicit delimiter.
    if (/\$|\\\(|\\\[/.test(str)) return str;

    // a/b → \(\frac{a}{b}\) when both are integers (up to 4 digits).
    let out = str.replace(/(?<![\w.])(\d{1,4})\s*\/\s*(\d{1,4})(?!\d)/g,
        (_, a, b) => `\\(\\frac{${a}}{${b}}\\)`);

    // " x " between numbers → × (only when flanked by digits/spaces).
    out = out.replace(/(\d)\s*[x×]\s*(\d)/g, '$1 \\times $2');

    return out;
}

// ── Main render helpers ────────────────────────────────────
/**
 * Render math inside a DOM element using the KaTeX auto-render extension.
 * Safe to call on elements with no math — it's a no-op. Safe to call more
 * than once — KaTeX skips already-rendered spans.
 * @tag MATH @tag KATEX
 */
function mathRenderIn(el) {
    if (!el || typeof renderMathInElement !== 'function') return;
    try {
        renderMathInElement(el, _KATEX_OPTS);
    } catch (err) {
        // Never let a render error break the page.
        console.warn('[katex] renderIn failed:', err);
    }
}

/**
 * Render a raw string to HTML with math expressions rendered.
 * Use when you need the HTML fragment (e.g. to assign to innerHTML after
 * other escaping is complete). Applies the auto-mathify heuristic first.
 * Caller is responsible for having escaped any untrusted non-math text.
 * @tag MATH @tag KATEX
 */
function mathRenderText(str) {
    if (!str && str !== 0) return '';
    const mathified = mathAutoMathify(String(str));
    if (typeof katex === 'undefined' || !katex.renderToString) return mathified;

    // Walk delimiters manually so we can return a string (auto-render is DOM-only).
    return _renderDelimsToString(mathified);
}

/**
 * Replace $...$ / \(...\) / $$...$$ / \[...\] spans with KaTeX-rendered HTML.
 * Non-math text is returned unchanged. @tag MATH @tag KATEX
 */
function _renderDelimsToString(s) {
    // Order matters: longest / most specific delimiters first.
    const patterns = [
        { re: /\$\$([\s\S]+?)\$\$/g,      display: true  },
        { re: /\\\[([\s\S]+?)\\\]/g,      display: true  },
        { re: /\\\(([\s\S]+?)\\\)/g,      display: false },
        { re: /\$([^\$\n]+?)\$/g,         display: false },
    ];
    let out = s;
    for (const { re, display } of patterns) {
        out = out.replace(re, (match, tex) => {
            try {
                return katex.renderToString(tex, {
                    displayMode: display,
                    throwOnError: false,
                    strict: 'ignore',
                    macros: _KATEX_OPTS.macros,
                });
            } catch (err) {
                console.warn('[katex] renderToString failed:', err);
                return match; // leave original text on failure
            }
        });
    }
    return out;
}

// Expose on window (no ES modules in this app).
window.mathRenderIn = mathRenderIn;
window.mathRenderText = mathRenderText;
window.mathAutoMathify = mathAutoMathify;


// ── Shared escape helpers ──────────────────────────────────
/**
 * HTML-escape a value for safe innerHTML insertion.
 * Replaces all per-module _escF / _escD / _escR / _escPl / _escP / _escS duplicates.
 * @tag MATH @tag UTILS
 */
function _mathEsc(str) {
    const d = document.createElement('div');
    d.textContent = str == null ? '' : String(str);
    return d.innerHTML;
}

/**
 * Escape a value for use in HTML attribute values (e.g. data-val="...").
 * @tag MATH @tag UTILS
 */
function _mathEscAttr(str) {
    return String(str == null ? '' : str)
        .replace(/&/g, '&amp;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');
}

window._mathEsc     = _mathEsc;
window._mathEscAttr = _mathEscAttr;
