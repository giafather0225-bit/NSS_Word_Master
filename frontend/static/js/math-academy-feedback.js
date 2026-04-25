/* ================================================================
   math-academy-feedback.js — Answer feedback overlay (Try/Practice)
   Section: Math
   Dependencies: math-academy.js (mathState), math-katex-utils.js (_mathEsc/_mathEscAttr)
   API endpoints: none (client-only rendering)
   ================================================================ */

/* global mathState, _mathEsc, _mathEscAttr */

// ── Feedback overlay ────────────────────────────────────────

/**
 * Show answer feedback overlay.
 * Supports three content variants (in priority order):
 *   1) Interactive step-by-step inputs (problem.interactive_steps) — Try wrong only
 *   2) Read-only solution steps list (result.solution_steps) — Try only
 *   3) CPA Fallback pictorial card (Practice wrong only)
 * @tag MATH @tag ACADEMY
 */
function showMathFeedback(result, problem, onNext) {
    const stage = document.getElementById('stage');
    if (!stage) return;

    // Remember the element that had focus so we can restore it on dismiss
    // (WCAG 2.4.3 Focus Order — keyboard users land back where they were).
    const prevFocus = document.activeElement;

    const overlay = document.createElement('div');
    overlay.className = 'math-feedback-overlay ' + (result.is_correct ? 'math-feedback-correct' : 'math-feedback-wrong');
    // ARIA: overlay behaves as a modal dialog — screen readers should
    // treat it as a focus boundary until dismissed.
    overlay.setAttribute('role', 'dialog');
    overlay.setAttribute('aria-modal', 'true');
    const titleId = 'math-feedback-title-' + Date.now();
    overlay.setAttribute('aria-labelledby', titleId);

    // Step-by-Step Solution is enabled ONLY in the Try stage (per spec).
    // For Pretest/Practice we keep the compact feedback (no steps list).
    const isTry = mathState && mathState.stage === 'try';
    const steps = Array.isArray(result.solution_steps) ? result.solution_steps : [];
    // Interactive steps (MATH_SPEC §Step-by-Step Solution UI):
    // problem.interactive_steps = [{prompt, inputs: [{label, correct}]}]
    // When present on a Try-stage wrong answer, overrides the read-only steps.
    const iSteps = problem && Array.isArray(problem.interactive_steps) ? problem.interactive_steps : [];
    const hasInteractive = isTry && !result.is_correct && iSteps.length > 0;
    const hasSteps = isTry && !hasInteractive && steps.length > 0;
    const autoOpen = hasSteps && !result.is_correct; // auto-open on wrong Try

    // CPA Fallback: for Practice wrong answers, show the relevant Pictorial card
    let cpaHtml = '';
    if (!result.is_correct && result._cpaFallback) {
        const c = result._cpaFallback;
        const vtype = c.visual_type;
        const vdata = c.visual_data || {};
        let cpaVisual = '';
        if (vtype === 'svg' || vtype === 'png') {
            const src = vdata.src || vdata.url || '';
            if (src) cpaVisual = `<div class="math-cpa-fallback-visual"><img src="${_mathEsc(src)}" alt="${_mathEsc(vdata.alt || c.title || '')}" /></div>`;
        } else if (vtype && vtype !== 'none' && typeof vdata.description === 'string' && vdata.description) {
            cpaVisual = `<div class="math-cpa-fallback-visual">${_mathEsc(vdata.description)}</div>`;
        }
        if (vtype === 'manipulative' || vtype === 'addition_table' || vtype === 'bar_model') {
            cpaVisual = '<div class="math-cpa-manip-slot" id="math-cpa-manip-slot"></div>';
        }
        cpaHtml = `
            <div class="math-cpa-fallback">
                <div class="math-cpa-fallback-label">\u{1F4A1} Remember the picture:</div>
                <div class="math-cpa-fallback-title">${_mathEsc(c.title || '')}</div>
                ${cpaVisual}
            </div>
        `;
    }

    const interactiveHtml = hasInteractive ? `
        <div class="math-steps math-steps-interactive" id="math-steps" data-open="1">
            <div class="math-steps-title">\u{1F4D6} Work through it step by step</div>
            <ol class="math-isteps-list">
                ${iSteps.map((s, si) => `
                    <li class="math-istep" data-si="${si}">
                        <div class="math-istep-prompt">${_mathEsc(s.prompt || '')}</div>
                        <div class="math-istep-inputs">
                            ${(s.inputs || []).map((inp, ii) => `
                                <label class="math-istep-input">
                                    <span class="math-istep-label">${_mathEsc(inp.label || '')}</span>
                                    <input type="text" class="math-input-field math-istep-field"
                                           data-si="${si}" data-ii="${ii}"
                                           data-correct="${_mathEscAttr(String(inp.correct))}"
                                           autocomplete="off">
                                    <span class="math-istep-mark" data-mark="${si}-${ii}"></span>
                                </label>
                            `).join('')}
                        </div>
                    </li>`).join('')}
            </ol>
            <button type="button" class="math-btn-secondary" id="math-istep-check">Check my work</button>
        </div>` : '';

    const stepsHtml = hasSteps ? `
        <div class="math-steps" id="math-steps" data-open="${autoOpen ? '1' : '0'}">
            <button type="button" class="math-btn-ghost math-steps-toggle" id="math-steps-toggle">
                ${autoOpen ? '\u{1F4D6} Step-by-step' : '\u{1F4D6} Show steps'}
            </button>
            <div class="math-steps-body" id="math-steps-body" style="${autoOpen ? '' : 'display:none;'}">
                <ol class="math-steps-list" id="math-steps-list"></ol>
                <button type="button" class="math-btn-secondary math-steps-next" id="math-steps-next">
                    Show next step
                </button>
            </div>
        </div>` : '';

    // M13: confetti burst on correct
    const confettiHtml = result.is_correct
        ? `<div class="math-confetti" aria-hidden="true"><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span></div>`
        : '';

    // Polite live-region announcement for screen readers.
    const liveMsg = result.is_correct ? 'Correct answer.' : 'Incorrect answer.';
    overlay.innerHTML = `
        ${confettiHtml}
        <div class="math-sr-only" role="status" aria-live="polite">${liveMsg}</div>
        <div class="math-feedback-card">
            <div class="math-feedback-result" id="${titleId}">${result.is_correct ? '\u2713 Correct!' : '\u2717 Not quite'}</div>
            ${!result.is_correct ? `<div class="math-feedback-answer">Answer: ${result.correct_answer}</div>` : ''}
            ${result.feedback ? `<div class="math-feedback-text">${_mathEsc(result.feedback)}</div>` : ''}
            ${interactiveHtml}
            ${stepsHtml}
            ${cpaHtml}
            <button class="math-btn-primary" id="math-feedback-next">Next</button>
        </div>
    `;

    stage.appendChild(overlay);

    // KaTeX: render math in feedback answer, feedback text, and any solution steps
    if (typeof window.mathRenderIn === 'function') window.mathRenderIn(overlay);

    if (result._cpaFallback) {
        const cpaSlot = document.getElementById('math-cpa-manip-slot');
        const c = result._cpaFallback;
        if (cpaSlot && typeof renderManipulative === 'function') {
            if (c.visual_type === 'manipulative') {
                renderManipulative(cpaSlot, c.visual_data || {});
            } else if (c.visual_type === 'addition_table') {
                renderManipulative(cpaSlot, { tool: 'addition_table', config: c.visual_data || {} });
            } else if (c.visual_type === 'bar_model') {
                renderManipulative(cpaSlot, { tool: 'bar_model', config: c.visual_data || {} });
            }
        }
    }

    if (hasInteractive) _wireInteractiveSteps(overlay);
    if (hasSteps) _wireReadOnlySteps(steps, autoOpen);

    const nextBtn = document.getElementById('math-feedback-next');
    // Autofocus the Continue button so keyboard users land on the primary action.
    // requestAnimationFrame lets the browser place the element before focus().
    requestAnimationFrame(() => {
        try { nextBtn.focus({ preventScroll: false }); } catch (_) { /* noop */ }
    });

    const dismiss = () => {
        document.removeEventListener('keydown', handler);
        overlay.remove();
        // Restore focus to the element that had it before we opened.
        if (prevFocus && typeof prevFocus.focus === 'function' && document.contains(prevFocus)) {
            try { prevFocus.focus({ preventScroll: true }); } catch (_) { /* noop */ }
        }
        onNext();
    };

    nextBtn.addEventListener('click', dismiss);

    // Keyboard: Enter continues (unless an input inside the overlay has focus),
    // Escape always dismisses.
    const handler = (e) => {
        if (e.key === 'Escape') {
            e.preventDefault();
            dismiss();
            return;
        }
        if (e.key === 'Enter'
            && !document.activeElement?.classList.contains('math-istep-field')
            && document.activeElement?.id !== 'math-steps-next') {
            dismiss();
        }
    };
    document.addEventListener('keydown', handler);
}

// ── Helpers ─────────────────────────────────────────────────

/** @tag MATH @tag ACADEMY */
function _wireInteractiveSteps(overlay) {
    const checkBtn = document.getElementById('math-istep-check');
    const fields = overlay.querySelectorAll('.math-istep-field');
    const normalize = (v) => String(v == null ? '' : v).trim().replace(/\s+/g, '').toLowerCase();
    const checkAll = () => {
        let allRight = true;
        let anyFilled = false;
        fields.forEach((f) => {
            const want = normalize(f.dataset.correct);
            const got = normalize(f.value);
            const mark = overlay.querySelector(`[data-mark="${f.dataset.si}-${f.dataset.ii}"]`);
            if (got === '') {
                if (mark) mark.textContent = '';
                f.classList.remove('math-istep-ok', 'math-istep-bad');
                allRight = false;
                return;
            }
            anyFilled = true;
            if (got === want) {
                if (mark) mark.textContent = '\u2713';
                f.classList.add('math-istep-ok');
                f.classList.remove('math-istep-bad');
            } else {
                if (mark) mark.textContent = '\u2717';
                f.classList.add('math-istep-bad');
                f.classList.remove('math-istep-ok');
                allRight = false;
            }
        });
        if (anyFilled && allRight && checkBtn) {
            checkBtn.textContent = '\u2713 All steps correct';
            checkBtn.disabled = true;
        }
    };
    if (checkBtn) checkBtn.addEventListener('click', checkAll);
    fields.forEach((f) => {
        f.addEventListener('keydown', (e) => { if (e.key === 'Enter') checkAll(); });
    });
}

/** @tag MATH @tag ACADEMY */
function _wireReadOnlySteps(steps, autoOpen) {
    let idx = 0;
    const listEl = document.getElementById('math-steps-list');
    const nextBtn = document.getElementById('math-steps-next');
    const toggleBtn = document.getElementById('math-steps-toggle');
    const bodyEl = document.getElementById('math-steps-body');
    const revealNext = () => {
        if (idx >= steps.length) return;
        const li = document.createElement('li');
        li.className = 'math-step';
        li.textContent = steps[idx];
        li.style.opacity = '0';
        listEl.appendChild(li);
        if (typeof window.mathRenderIn === 'function') window.mathRenderIn(li);
        requestAnimationFrame(() => {
            li.style.transition = 'opacity 0.25s ease';
            li.style.opacity = '1';
        });
        idx += 1;
        if (idx >= steps.length) {
            nextBtn.disabled = true;
            nextBtn.textContent = 'All steps shown';
        } else {
            nextBtn.textContent = `Show next step (${idx}/${steps.length})`;
        }
    };
    if (autoOpen) revealNext();
    nextBtn.addEventListener('click', revealNext);
    toggleBtn.addEventListener('click', () => {
        const open = bodyEl.style.display !== 'none';
        if (open) {
            bodyEl.style.display = 'none';
            toggleBtn.textContent = '\u{1F4D6} Show steps';
        } else {
            bodyEl.style.display = '';
            toggleBtn.textContent = '\u{1F4D6} Step-by-step';
            if (idx === 0) revealNext();
        }
    });
}
