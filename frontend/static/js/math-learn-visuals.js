/* ================================================================
   math-learn-visuals.js — Static pictorial renderers for Learn cards
   Section: Math
   Dependencies: core.js
   API endpoints: none (pure UI)

   Renders non-interactive visual_type variants used by learn cards:
     equation, equation_pair, step_by_step, number_line, column_addition,
     comparison_table, illustration, highlight, diagram, place_value_chart,
     bar_model (static), summary_card, keyword_table, text, text_with_icon,
     warning_example, error_highlight, word_problem, none.

   Usage:
     const html = renderLearnStaticVisual(vtype, vdata, card); // string
   ================================================================ */

/** @tag MATH @tag LEARN @tag VISUAL */
function renderLearnStaticVisual(vtype, vdata, card) {
    const d = vdata || {};
    switch (vtype) {
        case 'equation':         return _lvEquation(d);
        case 'equation_pair':    return _lvEquationPair(d);
        case 'step_by_step':     return _lvStepByStep(d);
        case 'number_line':      return _lvNumberLine(d);
        case 'column_addition':  return _lvColumnAddition(d);
        case 'comparison_table': return _lvComparisonTable(d);
        case 'illustration':     return _lvIllustration(d);
        case 'highlight':        return _lvHighlight(d);
        case 'diagram':          return _lvDiagram(d);
        case 'place_value_chart':return _lvPlaceValueChart(d);
        case 'bar_model':        return _lvStaticBarModel(d);
        case 'summary_card':     return _lvSummaryCard(d, card);
        case 'keyword_table':    return _lvKeywordTable(d);
        case 'text':             return _lvTextBlock(d, '📝');
        case 'text_with_icon':   return _lvTextBlock(d, d.icon || '💡');
        case 'warning_example':  return _lvTextBlock(d, '⚠️', 'math-lv-warn');
        case 'error_highlight':  return _lvTextBlock(d, '❌', 'math-lv-err');
        case 'word_problem':     return _lvWordProblem(d);
        case 'none':             return '';
        default:                 return '';
    }
}

// ── Small helpers ──────────────────────────────────────────

/** @tag MATH @tag VISUAL */
function _lvEsc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g,
        c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}

function _lvWrap(body, cls) {
    const c = cls ? ` ${cls}` : '';
    return `<div class="math-learn-visual math-lv${c}">${body}</div>`;
}

// ── Renderers ──────────────────────────────────────────────

/** @tag MATH @tag VISUAL */
function _lvEquation(d) {
    const eq = d.equation || d.text || '';
    if (!eq) return '';
    return _lvWrap(`<div class="math-lv-eq">${_lvEsc(eq)}</div>`);
}

/** @tag MATH @tag VISUAL */
function _lvEquationPair(d) {
    const L = d.left || ''; const R = d.right || '';
    const prop = d.property || '';
    if (!L && !R) return '';
    return _lvWrap(`
        <div class="math-lv-eq-pair">
            <div class="math-lv-eq">${_lvEsc(L)}</div>
            <div class="math-lv-eq-sep">${prop ? '⇄' : ''}</div>
            <div class="math-lv-eq">${_lvEsc(R)}</div>
        </div>
        ${prop ? `<div class="math-lv-caption">${_lvEsc(prop)} property</div>` : ''}
    `);
}

/** @tag MATH @tag VISUAL */
function _lvStepByStep(d) {
    const steps = Array.isArray(d.steps) ? d.steps : [];
    if (!steps.length) return '';
    const items = steps.map((s, i) => `
        <li>
            <span class="math-lv-step-num">${i + 1}</span>
            <span class="math-lv-step-text">${_lvEsc(s)}</span>
        </li>`).join('');
    return _lvWrap(`<ol class="math-lv-steps">${items}</ol>`);
}

/** @tag MATH @tag VISUAL */
function _lvNumberLine(d) {
    // {numbers:[367,512], rounded:[400,500], place:"hundreds", sum:900}
    const nums = Array.isArray(d.numbers) ? d.numbers : [];
    const rounded = Array.isArray(d.rounded) ? d.rounded : [];
    if (!nums.length) return '';
    const rows = nums.map((n, i) => {
        const r = rounded[i];
        const arrow = (r != null) ? `<span class="math-lv-arr">→</span><span class="math-lv-nl-rounded">${_lvEsc(r)}</span>` : '';
        return `<div class="math-lv-nl-row"><span class="math-lv-nl-orig">${_lvEsc(n)}</span>${arrow}</div>`;
    }).join('');
    const caption = d.place ? `rounded to nearest ${_lvEsc(d.place)}` : '';
    const sum = (d.sum != null) ? `<div class="math-lv-nl-sum">Estimated sum: <b>${_lvEsc(d.sum)}</b></div>` : '';
    return _lvWrap(`
        <div class="math-lv-nl">
            ${rows}
            ${caption ? `<div class="math-lv-caption">${caption}</div>` : ''}
            ${sum}
        </div>
    `);
}

/** @tag MATH @tag VISUAL */
function _lvColumnAddition(d) {
    // {problem:"356+218", step:"ones", sum:14, write:4, carry:1}
    const prob = d.problem || '';
    const parts = String(prob).split('+').map(s => s.trim()).filter(Boolean);
    if (parts.length < 2) return '';
    const width = Math.max(...parts.map(p => p.length));
    const pad = (s) => String(s).padStart(width, ' ').replace(/ /g, '&nbsp;');
    const meta = [];
    if (d.step) meta.push(`Step: <b>${_lvEsc(d.step)}</b>`);
    if (d.sum != null) meta.push(`Sum: <b>${_lvEsc(d.sum)}</b>`);
    if (d.write != null) meta.push(`Write: <b>${_lvEsc(d.write)}</b>`);
    if (d.carry != null) meta.push(`Carry: <b>${_lvEsc(d.carry)}</b>`);
    return _lvWrap(`
        <div class="math-lv-col">
            <pre class="math-lv-col-num">  ${pad(parts[0])}
+ ${pad(parts.slice(1).join('+'))}
${'─'.repeat(width + 2)}</pre>
            ${meta.length ? `<div class="math-lv-caption">${meta.join(' · ')}</div>` : ''}
        </div>
    `);
}

/** @tag MATH @tag VISUAL */
function _lvComparisonTable(d) {
    // {methods:["Rounding","Compatible"], estimates:[700,600], exact:647}
    const methods = Array.isArray(d.methods) ? d.methods : [];
    const estimates = Array.isArray(d.estimates) ? d.estimates : [];
    if (!methods.length) return '';
    const rows = methods.map((m, i) => `
        <tr>
            <td>${_lvEsc(m)}</td>
            <td>${_lvEsc(estimates[i] != null ? estimates[i] : '—')}</td>
        </tr>`).join('');
    const exact = (d.exact != null) ? `<tr class="math-lv-exact"><td>Exact</td><td>${_lvEsc(d.exact)}</td></tr>` : '';
    return _lvWrap(`
        <table class="math-lv-cmp">
            <thead><tr><th>Method</th><th>Estimate</th></tr></thead>
            <tbody>${rows}${exact}</tbody>
        </table>
    `);
}

/** @tag MATH @tag VISUAL */
function _lvIllustration(d) {
    const desc = d.description || '';
    if (!desc) return '';
    return _lvWrap(`
        <div class="math-lv-illus">
            <span class="math-lv-illus-icon">🎨</span>
            <span class="math-lv-illus-text">${_lvEsc(desc)}</span>
        </div>
    `);
}

/** @tag MATH @tag VISUAL */
function _lvHighlight(d) {
    // {numbers:[18,39,32], friendly_pair:[18,32], pair_sum:50, total:89}
    const nums = Array.isArray(d.numbers) ? d.numbers : [];
    const pair = new Set((Array.isArray(d.friendly_pair) ? d.friendly_pair : []).map(String));
    if (!nums.length) return '';
    const chips = nums.map(n => {
        const on = pair.has(String(n));
        return `<span class="math-lv-chip${on ? ' math-lv-chip-hi' : ''}">${_lvEsc(n)}</span>`;
    }).join('');
    const meta = [];
    if (d.pair_sum != null) meta.push(`Friendly pair → ${_lvEsc(d.pair_sum)}`);
    if (d.total != null) meta.push(`Total: <b>${_lvEsc(d.total)}</b>`);
    return _lvWrap(`
        <div class="math-lv-hi">
            <div class="math-lv-chips">${chips}</div>
            ${meta.length ? `<div class="math-lv-caption">${meta.join(' · ')}</div>` : ''}
        </div>
    `);
}

/** @tag MATH @tag VISUAL */
function _lvDiagram(d) {
    // {original:[367,512], compatible:[375,525], sum:900}
    const orig = Array.isArray(d.original) ? d.original : [];
    const comp = Array.isArray(d.compatible) ? d.compatible : [];
    if (!orig.length) return '';
    const rows = orig.map((n, i) => {
        const c = comp[i];
        return `
            <div class="math-lv-dia-row">
                <span class="math-lv-nl-orig">${_lvEsc(n)}</span>
                <span class="math-lv-arr">→</span>
                <span class="math-lv-nl-rounded">${_lvEsc(c != null ? c : '?')}</span>
            </div>`;
    }).join('');
    const sum = (d.sum != null) ? `<div class="math-lv-nl-sum">Sum: <b>${_lvEsc(d.sum)}</b></div>` : '';
    return _lvWrap(`<div class="math-lv-dia">${rows}${sum}</div>`);
}

/** @tag MATH @tag VISUAL */
function _lvPlaceValueChart(d) {
    // Optional fields: digits:{hundreds,tens,ones} or digits_list:[...] or description
    const cells = d.digits || null;
    if (cells && typeof cells === 'object') {
        const cols = ['hundreds', 'tens', 'ones', 'thousands'].filter(k => cells[k] != null);
        const head = cols.map(c => `<th>${c[0].toUpperCase() + c.slice(1)}</th>`).join('');
        const body = cols.map(c => `<td>${_lvEsc(cells[c])}</td>`).join('');
        return _lvWrap(`<table class="math-lv-pvc"><thead><tr>${head}</tr></thead><tbody><tr>${body}</tr></tbody></table>`);
    }
    if (d.description) return _lvTextBlock(d, '🔢');
    return '';
}

/** @tag MATH @tag VISUAL */
function _lvStaticBarModel(d) {
    // Static illustrative variant. If parts present, delegate to interactive manipulative.
    if (Array.isArray(d.parts) && d.parts.length && typeof renderManipulative === 'function') {
        return `<div class="math-learn-manip" id="math-learn-manip"></div>`;
    }
    if (d.description) return _lvTextBlock(d, '▭');
    return '';
}

/** @tag MATH @tag VISUAL */
function _lvSummaryCard(d, card) {
    const body = d.description || (card && card.content) || '';
    if (!body) return '';
    return _lvWrap(`
        <div class="math-lv-summary">
            <div class="math-lv-summary-icon">⭐</div>
            <div class="math-lv-summary-text">${_lvEsc(body)}</div>
        </div>
    `);
}

/** @tag MATH @tag VISUAL */
function _lvKeywordTable(d) {
    const rows = Array.isArray(d.rows) ? d.rows : [];
    if (rows.length && rows[0] && typeof rows[0] === 'object') {
        const keys = Object.keys(rows[0]);
        const head = keys.map(k => `<th>${_lvEsc(k)}</th>`).join('');
        const body = rows.map(r => `<tr>${keys.map(k => `<td>${_lvEsc(r[k])}</td>`).join('')}</tr>`).join('');
        return _lvWrap(`<table class="math-lv-cmp"><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table>`);
    }
    if (d.description) return _lvTextBlock(d, '🔑');
    return '';
}

/** @tag MATH @tag VISUAL */
function _lvTextBlock(d, icon, extraCls) {
    const body = d.description || d.text || '';
    if (!body) return '';
    const cls = extraCls ? ` ${extraCls}` : '';
    return _lvWrap(`
        <div class="math-lv-text-icon${cls}">
            <span class="math-lv-illus-icon">${icon}</span>
            <span class="math-lv-illus-text">${_lvEsc(body)}</span>
        </div>
    `);
}

/** @tag MATH @tag VISUAL */
function _lvWordProblem(d) {
    const ctx = d.context || d.description || '';
    if (!ctx) return '';
    return _lvWrap(`
        <div class="math-lv-wp">
            <div class="math-lv-wp-label">Context</div>
            <div class="math-lv-wp-body">${_lvEsc(ctx)}</div>
        </div>
    `);
}
