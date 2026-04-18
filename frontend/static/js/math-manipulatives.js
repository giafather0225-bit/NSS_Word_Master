/* ================================================================
   math-manipulatives.js — Virtual manipulatives (5 interactive tools)
   Section: Math
   Dependencies: core.js
   API endpoints: none (pure UI)

   Usage:
     renderManipulative(containerEl, { tool: 'number_line', config: {...} })

   Tools:
     number_line   — draggable marker on a number line, supports hops
     base10_blocks — place-value blocks (hundreds/tens/ones)
     fraction_bar  — split a bar into fractional parts, shade some
     array_grid    — rows × cols dot grid for multiplication
     ten_frame     — 10-dot frame(s) for counting / addition
   ================================================================ */

/** @tag MATH @tag MANIPULATIVE */
function renderManipulative(container, spec) {
    if (!container) return;
    const tool = spec && spec.tool;
    const cfg = (spec && spec.config) || {};
    container.innerHTML = '';
    container.classList.add('math-manip');
    switch (tool) {
        case 'number_line':   return _renderNumberLine(container, cfg);
        case 'base10_blocks': return _renderBase10(container, cfg);
        case 'fraction_bar':  return _renderFractionBar(container, cfg);
        case 'array_grid':    return _renderArrayGrid(container, cfg);
        case 'ten_frame':     return _renderTenFrame(container, cfg);
        case 'addition_table':return _renderAdditionTable(container, cfg);
        case 'bar_model':     return _renderBarModel(container, cfg);
        default:
            container.textContent = typeof spec === 'string' ? spec : '';
    }
}

// ── 1. Number Line ─────────────────────────────────────────

/** @tag MATH @tag MANIPULATIVE @tag NUMBER_LINE */
function _renderNumberLine(container, cfg) {
    const min = cfg.min != null ? cfg.min : 0;
    const max = cfg.max != null ? cfg.max : 20;
    const step = cfg.step || 1;
    const start = cfg.start != null ? cfg.start : min;
    const width = 520, height = 96, pad = 28;

    container.innerHTML = `
        <div class="math-manip-head">
            <span class="math-manip-label">Number line</span>
            <span class="math-manip-value" data-role="value">${start}</span>
        </div>
        <svg viewBox="0 0 ${width} ${height}" class="math-manip-svg" data-role="svg">
            <line x1="${pad}" y1="60" x2="${width - pad}" y2="60" stroke="var(--math-primary)" stroke-width="2"/>
        </svg>
        <div class="math-manip-actions">
            <button class="math-btn-ghost" data-role="hop-back">− ${step}</button>
            <button class="math-btn-ghost" data-role="hop-fwd">+ ${step}</button>
            <button class="math-btn-ghost" data-role="reset">Reset</button>
        </div>
    `;

    const svg = container.querySelector('[data-role="svg"]');
    const valueEl = container.querySelector('[data-role="value"]');
    const span = max - min;
    const xFor = (n) => pad + ((n - min) / span) * (width - pad * 2);

    // Ticks
    for (let n = min; n <= max; n += step) {
        const x = xFor(n);
        const t = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        t.setAttribute('x1', x); t.setAttribute('x2', x);
        t.setAttribute('y1', 54); t.setAttribute('y2', 66);
        t.setAttribute('stroke', 'rgba(0,0,0,0.25)');
        t.setAttribute('stroke-width', '2');
        svg.appendChild(t);
        const lbl = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        lbl.setAttribute('x', x); lbl.setAttribute('y', 84);
        lbl.setAttribute('text-anchor', 'middle');
        lbl.setAttribute('font-size', '12');
        lbl.setAttribute('fill', 'var(--text-secondary)');
        lbl.textContent = String(n);
        svg.appendChild(lbl);
    }

    // Marker
    const marker = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
    marker.setAttribute('r', '10');
    marker.setAttribute('fill', 'var(--math-accent-pink)');
    marker.setAttribute('stroke', 'white');
    marker.setAttribute('stroke-width', '3');
    marker.setAttribute('cy', '60');
    marker.setAttribute('cx', xFor(start));
    marker.style.cursor = 'grab';
    svg.appendChild(marker);

    let current = start;
    const snap = (x) => {
        const rel = Math.max(pad, Math.min(width - pad, x));
        const n = Math.round(((rel - pad) / (width - pad * 2)) * span / step) * step + min;
        return Math.max(min, Math.min(max, n));
    };
    const setValue = (n) => {
        current = n;
        marker.setAttribute('cx', xFor(n));
        valueEl.textContent = String(n);
    };

    // Drag
    let dragging = false;
    const toSVG = (evt) => {
        const pt = svg.createSVGPoint();
        pt.x = evt.clientX; pt.y = evt.clientY;
        return pt.matrixTransform(svg.getScreenCTM().inverse());
    };
    marker.addEventListener('pointerdown', (e) => { dragging = true; marker.setPointerCapture(e.pointerId); });
    marker.addEventListener('pointerup',   (e) => { dragging = false; marker.releasePointerCapture(e.pointerId); });
    marker.addEventListener('pointermove', (e) => {
        if (!dragging) return;
        const p = toSVG(e);
        setValue(snap(p.x));
    });

    container.querySelector('[data-role="hop-fwd"]').addEventListener('click', () => {
        setValue(Math.min(max, current + step));
    });
    container.querySelector('[data-role="hop-back"]').addEventListener('click', () => {
        setValue(Math.max(min, current - step));
    });
    container.querySelector('[data-role="reset"]').addEventListener('click', () => setValue(start));
}

// ── 2. Base-10 Blocks ──────────────────────────────────────

/** @tag MATH @tag MANIPULATIVE @tag BASE10 */
function _renderBase10(container, cfg) {
    let value = cfg.start || 0;
    const max = cfg.max || 999;

    container.innerHTML = `
        <div class="math-manip-head">
            <span class="math-manip-label">Base-10 blocks</span>
            <span class="math-manip-value" data-role="value">${value}</span>
        </div>
        <div class="math-b10-grid">
            <div class="math-b10-col">
                <div class="math-b10-title">Hundreds</div>
                <div class="math-b10-tray" data-place="100"></div>
                <div class="math-b10-controls">
                    <button class="math-btn-ghost" data-delta="100">+100</button>
                    <button class="math-btn-ghost" data-delta="-100">−100</button>
                </div>
            </div>
            <div class="math-b10-col">
                <div class="math-b10-title">Tens</div>
                <div class="math-b10-tray" data-place="10"></div>
                <div class="math-b10-controls">
                    <button class="math-btn-ghost" data-delta="10">+10</button>
                    <button class="math-btn-ghost" data-delta="-10">−10</button>
                </div>
            </div>
            <div class="math-b10-col">
                <div class="math-b10-title">Ones</div>
                <div class="math-b10-tray" data-place="1"></div>
                <div class="math-b10-controls">
                    <button class="math-btn-ghost" data-delta="1">+1</button>
                    <button class="math-btn-ghost" data-delta="-1">−1</button>
                </div>
            </div>
        </div>
        <div class="math-manip-actions">
            <button class="math-btn-ghost" data-role="reset">Reset</button>
        </div>
    `;

    const valueEl = container.querySelector('[data-role="value"]');
    const redraw = () => {
        valueEl.textContent = String(value);
        const h = Math.floor(value / 100);
        const t = Math.floor((value % 100) / 10);
        const o = value % 10;
        const paint = (place, count, cls) => {
            const tray = container.querySelector(`[data-place="${place}"]`);
            tray.innerHTML = '';
            for (let i = 0; i < count; i++) {
                const b = document.createElement('div');
                b.className = `math-b10-block ${cls}`;
                tray.appendChild(b);
            }
        };
        paint(100, h, 'math-b10-hundred');
        paint(10,  t, 'math-b10-ten');
        paint(1,   o, 'math-b10-one');
    };
    redraw();

    container.querySelectorAll('[data-delta]').forEach(btn => {
        btn.addEventListener('click', () => {
            const d = parseInt(btn.dataset.delta, 10);
            value = Math.max(0, Math.min(max, value + d));
            redraw();
        });
    });
    container.querySelector('[data-role="reset"]').addEventListener('click', () => {
        value = cfg.start || 0;
        redraw();
    });
}

// ── 3. Fraction Bar ────────────────────────────────────────

/** @tag MATH @tag MANIPULATIVE @tag FRACTION */
function _renderFractionBar(container, cfg) {
    let denom = cfg.denominator || 4;
    let numer = cfg.numerator != null ? cfg.numerator : 1;
    const maxDenom = cfg.maxDenominator || 12;

    container.innerHTML = `
        <div class="math-manip-head">
            <span class="math-manip-label">Fraction</span>
            <span class="math-manip-value" data-role="value">${numer}/${denom}</span>
        </div>
        <div class="math-frac-bar" data-role="bar"></div>
        <div class="math-manip-actions">
            <button class="math-btn-ghost" data-role="d-minus">− parts</button>
            <button class="math-btn-ghost" data-role="d-plus">+ parts</button>
            <button class="math-btn-ghost" data-role="clear">Clear</button>
        </div>
    `;

    const bar = container.querySelector('[data-role="bar"]');
    const valEl = container.querySelector('[data-role="value"]');
    const shaded = new Set();

    const redraw = () => {
        bar.innerHTML = '';
        for (let i = 0; i < denom; i++) {
            const seg = document.createElement('div');
            seg.className = 'math-frac-seg';
            if (shaded.has(i)) seg.classList.add('shaded');
            seg.addEventListener('click', () => {
                if (shaded.has(i)) shaded.delete(i); else shaded.add(i);
                redraw();
            });
            bar.appendChild(seg);
        }
        valEl.textContent = `${shaded.size}/${denom}`;
    };
    // Pre-shade initial numer
    for (let i = 0; i < numer && i < denom; i++) shaded.add(i);
    redraw();

    container.querySelector('[data-role="d-plus"]').addEventListener('click', () => {
        if (denom < maxDenom) { denom += 1; [...shaded].forEach(i => { if (i >= denom) shaded.delete(i); }); redraw(); }
    });
    container.querySelector('[data-role="d-minus"]').addEventListener('click', () => {
        if (denom > 1) { denom -= 1; [...shaded].forEach(i => { if (i >= denom) shaded.delete(i); }); redraw(); }
    });
    container.querySelector('[data-role="clear"]').addEventListener('click', () => { shaded.clear(); redraw(); });
}

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
