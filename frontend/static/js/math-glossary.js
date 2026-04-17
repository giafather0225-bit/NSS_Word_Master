/* ================================================================
   math-glossary.js — Math Glossary browser + term detail + TTS
   Section: Math
   Dependencies: core.js, tts-client.js (optional)
   API endpoints: /api/math/glossary/grades,
                  /api/math/glossary/{grade},
                  /api/math/glossary/{grade}/{term_id}
   ================================================================ */

// ── State ──────────────────────────────────────────────────

const glossaryState = {
    grade: 'G3',
    filter: '',
    category: '',
    categories: [],
};

// ── Entry ──────────────────────────────────────────────────

/** @tag MATH @tag GLOSSARY */
async function startMathGlossary(grade) {
    _showGlossaryStage();
    glossaryState.grade = grade || glossaryState.grade || 'G3';
    const stage = document.getElementById('stage');
    if (!stage) return;
    stage.innerHTML = `<div class="math-gloss"><p>Loading glossary…</p></div>`;
    try {
        const res = await fetch(`/api/math/glossary/${encodeURIComponent(glossaryState.grade)}`);
        if (!res.ok) throw new Error('bad response');
        const data = await res.json();
        glossaryState.categories = data.categories || [];
        _renderGlossaryList(data);
    } catch (err) {
        console.warn('[math] glossary load failed', err);
        stage.innerHTML = `<div class="math-gloss"><p class="math-err">Failed to load glossary.</p></div>`;
    }
}

// ── Stage helper ───────────────────────────────────────────

function _showGlossaryStage() {
    const stageCard = document.getElementById('stage-card');
    const idleWrap = document.getElementById('idle-wrapper');
    const homeDash = document.getElementById('home-dashboard');
    const topBar = document.querySelector('.top-bar');
    if (homeDash) homeDash.style.display = 'none';
    if (idleWrap) idleWrap.style.display = 'none';
    if (stageCard) { stageCard.classList.remove('hidden'); stageCard.style.display = ''; }
    if (topBar) topBar.style.display = '';
}

// ── List render ────────────────────────────────────────────

/** @tag MATH @tag GLOSSARY */
function _renderGlossaryList(data) {
    const stage = document.getElementById('stage');
    if (!stage) return;
    const filter = glossaryState.filter.toLowerCase();
    const catFilter = glossaryState.category;

    const catBtns = `
        <button class="math-gloss-cat ${!catFilter ? 'active' : ''}" data-cat="">All</button>
        ${glossaryState.categories.map(c =>
            `<button class="math-gloss-cat ${catFilter === c.name ? 'active' : ''}" data-cat="${_escAttrG(c.name)}">${_escG(c.name.replace(/_/g, ' '))}</button>`
        ).join('')}`;

    const sections = glossaryState.categories
        .filter(c => !catFilter || c.name === catFilter)
        .map(c => {
            const matches = (c.terms || []).filter(t => {
                if (!filter) return true;
                return t.term.toLowerCase().includes(filter)
                    || (t.kid_friendly || '').toLowerCase().includes(filter);
            });
            if (!matches.length) return '';
            return `
                <section class="math-gloss-section">
                    <h3 class="math-gloss-section-title">${_escG(c.name.replace(/_/g, ' '))}</h3>
                    <div class="math-gloss-grid">
                        ${matches.map(t => `
                            <button class="math-gloss-item" data-id="${_escAttrG(t.id)}">
                                <div class="math-gloss-term">${_escG(t.term)}</div>
                                <div class="math-gloss-kid">${_escG(t.kid_friendly || '')}</div>
                            </button>
                        `).join('')}
                    </div>
                </section>`;
        }).join('');

    stage.innerHTML = `
        <div class="math-gloss">
            <div class="math-gloss-header">
                <h2 class="math-gloss-title">📖 ${_escG(data.title || 'Glossary')}</h2>
                <input type="search" class="math-gloss-search" id="math-gloss-search"
                       placeholder="Search terms…" value="${_escAttrG(glossaryState.filter)}">
            </div>
            <div class="math-gloss-cats">${catBtns}</div>
            <div class="math-gloss-body">${sections || '<p class="empty">No matches.</p>'}</div>
        </div>`;

    // Wire
    const search = document.getElementById('math-gloss-search');
    if (search) {
        search.addEventListener('input', (e) => {
            glossaryState.filter = e.target.value;
            _renderGlossaryList(data);
            // Keep focus
            const s2 = document.getElementById('math-gloss-search');
            if (s2) { s2.focus(); s2.setSelectionRange(s2.value.length, s2.value.length); }
        });
    }
    stage.querySelectorAll('.math-gloss-cat').forEach(btn => {
        btn.addEventListener('click', () => {
            glossaryState.category = btn.dataset.cat;
            _renderGlossaryList(data);
        });
    });
    stage.querySelectorAll('.math-gloss-item').forEach(btn => {
        btn.addEventListener('click', () => _showGlossaryTerm(btn.dataset.id));
    });
}

// ── Term detail ────────────────────────────────────────────

/** @tag MATH @tag GLOSSARY */
async function _showGlossaryTerm(termId) {
    const overlay = document.createElement('div');
    overlay.className = 'math-gloss-modal';
    overlay.innerHTML = `
        <div class="math-gloss-modal-card">
            <button class="math-gloss-close" aria-label="Close">×</button>
            <div class="math-gloss-modal-body"><p>Loading…</p></div>
        </div>`;
    document.body.appendChild(overlay);
    overlay.addEventListener('click', (e) => {
        if (e.target === overlay || e.target.classList.contains('math-gloss-close')) {
            overlay.remove();
        }
    });

    try {
        const res = await fetch(`/api/math/glossary/${encodeURIComponent(glossaryState.grade)}/${encodeURIComponent(termId)}`);
        if (!res.ok) throw new Error('bad');
        const t = await res.json();
        const body = overlay.querySelector('.math-gloss-modal-body');
        body.innerHTML = `
            <div class="math-gloss-modal-head">
                <h2 class="math-gloss-modal-title">${_escG(t.term)}</h2>
                <button class="math-btn-ghost math-gloss-tts" id="math-gloss-tts">🔊 Listen</button>
            </div>
            <div class="math-gloss-modal-kid">${_escG(t.kid_friendly || '')}</div>
            <div class="math-gloss-modal-def">
                <strong>Definition:</strong> ${_escG(t.definition || '')}
            </div>
            ${t.example ? `<div class="math-gloss-modal-ex"><strong>Example:</strong> ${_escG(t.example)}</div>` : ''}
            ${t.visual_hint ? `<div class="math-gloss-modal-vis">${_escG(t.visual_hint)}</div>` : ''}
        `;
        const ttsBtn = document.getElementById('math-gloss-tts');
        if (ttsBtn) ttsBtn.addEventListener('click', () => _playGlossaryTTS(t));
        // Autoplay
        _playGlossaryTTS(t);
    } catch (err) {
        overlay.querySelector('.math-gloss-modal-body').innerHTML =
            '<p class="math-err">Failed to load term.</p>';
    }
}

// ── TTS ────────────────────────────────────────────────────

async function _playGlossaryTTS(term) {
    const text = `${term.term}. ${term.kid_friendly || term.definition || ''}. For example, ${term.example || ''}`;
    if (!text) return;
    try {
        if (typeof playTTS === 'function') {
            await playTTS(text);
            return;
        }
        const res = await fetch('/api/tts/speak', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text, voice: 'en-US-AriaNeural' }),
        });
        if (res.ok) {
            const blob = await res.blob();
            const url = URL.createObjectURL(blob);
            const audio = new Audio(url);
            audio.play();
            audio.onended = () => URL.revokeObjectURL(url);
        }
    } catch (err) {
        console.warn('[math] glossary TTS failed', err);
    }
}

// ── Escape helpers ─────────────────────────────────────────

function _escG(s) {
    const d = document.createElement('div');
    d.textContent = s == null ? '' : String(s);
    return d.innerHTML;
}
function _escAttrG(s) {
    return _escG(s).replace(/"/g, '&quot;');
}
