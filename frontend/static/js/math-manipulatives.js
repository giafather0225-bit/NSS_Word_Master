/* ================================================================
   math-manipulatives.js — Virtual manipulatives dispatcher + tools 1–3
   Section: Math
   Dependencies: core.js, math-manipulatives-2.js (tools 4–7)
   API endpoints: none (pure UI)

   Usage:
     renderManipulative(containerEl, { tool: 'number_line', config: {...} })

   Tools in this file:
     number_line   — draggable marker on a number line, supports hops
     base10_blocks — place-value blocks (hundreds/tens/ones)
     fraction_bar  — split a bar into fractional parts, shade some
   Tools in math-manipulatives-2.js:
     array_grid, ten_frame, addition_table, bar_model
   ================================================================ */

/* global _renderArrayGrid, _renderTenFrame, _renderAdditionTable, _renderBarModel */

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

