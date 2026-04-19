/* ================================================================
   math-manipulatives-2.js — Virtual manipulatives (tools 4–7)
   Section: Math
   Dependencies: core.js
   Dispatcher: math-manipulatives.js (renderManipulative)
   API endpoints: none (pure UI)

   Tools in this file:
     array_grid     — rows × cols dot grid for multiplication
     ten_frame      — 10-dot frame(s) for counting / addition
     addition_table — 0–9 × 0–9 interactive table with highlights
     bar_model      — part-whole bar model with editable segments
   ================================================================ */

// ── 4. Array grid (multiplication) ─────────────────────────

/** @tag MATH @tag MANIPULATIVE @tag ARRAY */
function _renderArrayGrid(container, cfg) {
    let rows = cfg.rows != null ? cfg.rows : 3;
    let cols = cfg.cols != null ? cfg.cols : 4;
    const maxRows = cfg.maxRows || 12;
    const maxCols = cfg.maxCols || 12;

    container.innerHTML = `
        <div class="math-manip-head">
            <span class="math-manip-label">Array</span>
            <span class="math-manip-value" data-role="value">${rows} × ${cols} = ${rows * cols}</span>
        </div>
        <div class="math-arr-grid" data-role="grid"></div>
        <div class="math-manip-actions math-arr-controls">
            <div>
                <button class="math-btn-ghost" data-role="row-minus">− row</button>
                <button class="math-btn-ghost" data-role="row-plus">+ row</button>
            </div>
            <div>
                <button class="math-btn-ghost" data-role="col-minus">− col</button>
                <button class="math-btn-ghost" data-role="col-plus">+ col</button>
            </div>
        </div>
    `;

    const grid = container.querySelector('[data-role="grid"]');
    const valEl = container.querySelector('[data-role="value"]');
    const redraw = () => {
        grid.style.gridTemplateColumns = `repeat(${cols}, 22px)`;
        grid.innerHTML = '';
        for (let i = 0; i < rows * cols; i++) {
            const dot = document.createElement('div');
            dot.className = 'math-arr-dot';
            grid.appendChild(dot);
        }
        valEl.textContent = `${rows} × ${cols} = ${rows * cols}`;
    };
    redraw();

    container.querySelector('[data-role="row-plus"]').addEventListener('click', () => { if (rows < maxRows) { rows += 1; redraw(); } });
    container.querySelector('[data-role="row-minus"]').addEventListener('click', () => { if (rows > 1) { rows -= 1; redraw(); } });
    container.querySelector('[data-role="col-plus"]').addEventListener('click', () => { if (cols < maxCols) { cols += 1; redraw(); } });
    container.querySelector('[data-role="col-minus"]').addEventListener('click', () => { if (cols > 1) { cols -= 1; redraw(); } });
}

// ── 5. Ten Frame ───────────────────────────────────────────

/** @tag MATH @tag MANIPULATIVE @tag TEN_FRAME */
function _renderTenFrame(container, cfg) {
    const frames = cfg.frames || 1;
    let filled = cfg.start != null ? cfg.start : 0;
    const max = frames * 10;

    container.innerHTML = `
        <div class="math-manip-head">
            <span class="math-manip-label">Ten frame${frames > 1 ? 's' : ''}</span>
            <span class="math-manip-value" data-role="value">${filled}</span>
        </div>
        <div class="math-tf-wrap" data-role="frames"></div>
        <div class="math-manip-actions">
            <button class="math-btn-ghost" data-role="minus">− 1</button>
            <button class="math-btn-ghost" data-role="plus">+ 1</button>
            <button class="math-btn-ghost" data-role="reset">Reset</button>
        </div>
    `;

    const wrap = container.querySelector('[data-role="frames"]');
    const valEl = container.querySelector('[data-role="value"]');
    const redraw = () => {
        wrap.innerHTML = '';
        let remaining = filled;
        for (let f = 0; f < frames; f++) {
            const frame = document.createElement('div');
            frame.className = 'math-tf-frame';
            for (let i = 0; i < 10; i++) {
                const cell = document.createElement('div');
                cell.className = 'math-tf-cell';
                if (remaining > 0) {
                    const dot = document.createElement('div');
                    dot.className = 'math-tf-dot';
                    cell.appendChild(dot);
                    remaining -= 1;
                }
                cell.addEventListener('click', () => {
                    const idx = f * 10 + i;
                    filled = idx < filled ? idx : idx + 1;
                    filled = Math.max(0, Math.min(max, filled));
                    redraw();
                });
                frame.appendChild(cell);
            }
            wrap.appendChild(frame);
        }
        valEl.textContent = String(filled);
    };
    redraw();

    container.querySelector('[data-role="plus"]').addEventListener('click', () => { filled = Math.min(max, filled + 1); redraw(); });
    container.querySelector('[data-role="minus"]').addEventListener('click', () => { filled = Math.max(0, filled - 1); redraw(); });
    container.querySelector('[data-role="reset"]').addEventListener('click', () => { filled = cfg.start != null ? cfg.start : 0; redraw(); });
}

// ── 6. Addition Table (0-9 × 0-9) ──────────────────────────

/** @tag MATH @tag MANIPULATIVE @tag ADDITION_TABLE */
function _renderAdditionTable(container, cfg) {
    cfg = cfg || {};
    const hiRow = Number.isInteger(cfg.highlight_row) ? cfg.highlight_row : null;
    const hiCol = Number.isInteger(cfg.highlight_col) ? cfg.highlight_col : null;
    const hiCells = new Set(
        (Array.isArray(cfg.highlight_cells) ? cfg.highlight_cells : [])
            .map(p => Array.isArray(p) ? `${p[0]},${p[1]}` : '')
    );
    const colorEven = cfg.color_even || null;
    const colorOdd  = cfg.color_odd  || null;

    container.classList.add('math-manip');
    let html = `
        <div class="math-manip-head">
            <span class="math-manip-label">Addition table</span>
            <span class="math-manip-value" data-role="value">+</span>
        </div>
        <table class="math-addtbl"><thead><tr><th>+</th>`;
    for (let c = 0; c <= 9; c++) {
        const cls = (hiCol === c) ? 'math-addtbl-hi-col' : '';
        html += `<th class="${cls}">${c}</th>`;
    }
    html += `</tr></thead><tbody>`;
    for (let r = 0; r <= 9; r++) {
        const rowCls = (hiRow === r) ? 'math-addtbl-hi-row' : '';
        html += `<tr class="${rowCls}"><th class="${rowCls}">${r}</th>`;
        for (let c = 0; c <= 9; c++) {
            const sum = r + c;
            const classes = [];
            if (hiRow === r) classes.push('math-addtbl-hi-row');
            if (hiCol === c) classes.push('math-addtbl-hi-col');
            if (hiCells.has(`${r},${c}`)) classes.push('math-addtbl-hi-cell');
            const styles = [];
            if (colorEven && sum % 2 === 0) styles.push(`background:${colorEven}`);
            if (colorOdd  && sum % 2 === 1) styles.push(`background:${colorOdd}`);
            html += `<td class="${classes.join(' ')}"${styles.length ? ` style="${styles.join(';')}"` : ''} data-r="${r}" data-c="${c}">${sum}</td>`;
        }
        html += `</tr>`;
    }
    html += `</tbody></table>`;
    container.innerHTML = html;

    const valEl = container.querySelector('[data-role="value"]');
    container.querySelectorAll('td[data-r]').forEach(td => {
        td.addEventListener('click', () => {
            const r = td.dataset.r, c = td.dataset.c;
            valEl.textContent = `${r} + ${c} = ${Number(r) + Number(c)}`;
        });
    });
}

// ── 7. Bar Model (part-whole) ──────────────────────────────

/** @tag MATH @tag MANIPULATIVE @tag BAR_MODEL */
function _renderBarModel(container, cfg) {
    cfg = cfg || {};
    const parts = (Array.isArray(cfg.parts) ? cfg.parts : []).map((p, i) => ({
        label: (p && p.label != null) ? String(p.label) : `Part ${i + 1}`,
        value: (p && Number.isFinite(Number(p.value))) ? Number(p.value) : 0,
    }));
    if (parts.length === 0) {
        parts.push({ label: 'Part 1', value: 0 }, { label: 'Part 2', value: 0 });
    }
    const fixedTotal = Number.isFinite(Number(cfg.total)) ? Number(cfg.total) : null;

    const sumParts = () => parts.reduce((a, p) => a + (p.value || 0), 0);

    container.classList.add('math-manip');
    container.innerHTML = `
        <div class="math-manip-head">
            <span class="math-manip-label">Bar model</span>
            <span class="math-manip-value" data-role="value"></span>
        </div>
        <div class="math-bar-total" data-role="total"></div>
        <div class="math-bar-row" data-role="bar"></div>
        <div class="math-manip-actions">
            <button class="math-btn-ghost" data-role="add">+ part</button>
            <button class="math-btn-ghost" data-role="remove">− part</button>
            <button class="math-btn-ghost" data-role="reset">Reset</button>
        </div>
    `;

    const bar = container.querySelector('[data-role="bar"]');
    const totalEl = container.querySelector('[data-role="total"]');
    const valEl = container.querySelector('[data-role="value"]');
    const orig = parts.map(p => ({ ...p }));

    const redraw = () => {
        const curSum = sumParts();
        const scaleBase = fixedTotal != null ? Math.max(fixedTotal, curSum, 1) : Math.max(curSum, 1);
        bar.innerHTML = '';
        parts.forEach((p, i) => {
            const pct = (p.value / scaleBase) * 100;
            const seg = document.createElement('div');
            seg.className = 'math-bar-seg';
            seg.style.flex = `${Math.max(pct, 4)} 0 0`;
            seg.dataset.idx = i;
            seg.innerHTML = `<span class="math-bar-label">${_escBarModel(p.label)}</span><span class="math-bar-val">${p.value}</span>`;
            seg.addEventListener('click', () => {
                const raw = window.prompt(`Value for "${p.label}":`, String(p.value));
                if (raw == null) return;
                const n = Number(raw);
                if (!Number.isFinite(n) || n < 0) return;
                p.value = n;
                redraw();
            });
            bar.appendChild(seg);
        });
        if (fixedTotal != null && curSum < fixedTotal) {
            const gap = document.createElement('div');
            gap.className = 'math-bar-seg math-bar-seg-empty';
            gap.style.flex = `${((fixedTotal - curSum) / scaleBase) * 100} 0 0`;
            gap.textContent = `? (${fixedTotal - curSum})`;
            bar.appendChild(gap);
        }
        totalEl.textContent = fixedTotal != null
            ? `Total: ${fixedTotal}`
            : `Total: ${curSum}`;
        valEl.textContent = parts.map(p => p.value).join(' + ') + ` = ${curSum}`;
    };
    redraw();

    container.querySelector('[data-role="add"]').addEventListener('click', () => {
        parts.push({ label: `Part ${parts.length + 1}`, value: 0 });
        redraw();
    });
    container.querySelector('[data-role="remove"]').addEventListener('click', () => {
        if (parts.length > 1) { parts.pop(); redraw(); }
    });
    container.querySelector('[data-role="reset"]').addEventListener('click', () => {
        parts.length = 0;
        orig.forEach(p => parts.push({ ...p }));
        redraw();
    });
}

/** @tag MATH @tag MANIPULATIVE */
function _escBarModel(s) {
    return String(s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}
