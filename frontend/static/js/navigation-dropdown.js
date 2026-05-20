/* ================================================================
   navigation-dropdown.js — Custom lesson/textbook dropdown UIs and OCR button.
   Section: English / Navigation
   Dependencies: navigation.js, core.js
   API endpoints: /api/study/:subject/:textbook/:lesson,
                  /api/lessons/ingest_disk/:lesson
   Split from navigation.js (2026-05-20) when that file exceeded ~500 lines.
   ================================================================ */

// ─── Lesson-dropdown custom UI ────────────────────────────────
/**
 * Initialise the custom lesson-dropdown UI that mirrors the hidden <select>.
 * @tag NAVIGATION SIDEBAR
 */
function initLessonDropdownUI() {
    const sel      = document.getElementById('lesson-select');
    const display  = document.getElementById('sb-lesson-name');
    const dropdown = document.getElementById('sb-lesson-dropdown');
    if (!sel || !display || !dropdown) return;

    const nameEl = display.querySelector('.sb-tb-name-text');

    function cleanText(t) {
        return t.replace(/^\[done\]\s*/, '').replace(/\s*·\s*$/, '').trim();
    }

    function sync() {
        const opt = sel.options[sel.selectedIndex];
        if (nameEl) nameEl.textContent = (opt && opt.value) ? cleanText(opt.text) : '—';
    }

    function buildDropdown() {
        dropdown.innerHTML = '';
        const cur = sel.value;
        Array.from(sel.options).filter(o => o.value).forEach(opt => {
            const item = document.createElement('div');
            item.className = 'sb-tb-option' + (opt.value === cur ? ' selected' : '');
            item.textContent = cleanText(opt.text);
            item.addEventListener('click', () => {
                sel.value = opt.value;
                sel.dispatchEvent(new Event('change'));
                closeDropdown();
            });
            dropdown.appendChild(item);
        });
    }

    function positionDropdown() {
        const rect = display.getBoundingClientRect();
        const availableBelow = window.innerHeight - rect.bottom - 8;
        dropdown.style.top       = (rect.bottom + 4) + 'px';
        dropdown.style.left      = rect.left + 'px';
        dropdown.style.width     = rect.width + 'px';
        dropdown.style.maxHeight = Math.min(360, availableBelow) + 'px';
    }

    function openDropdown() {
        buildDropdown();
        positionDropdown();
        dropdown.classList.add('open');
        display.classList.add('open');
    }

    function closeDropdown() {
        dropdown.classList.remove('open');
        display.classList.remove('open');
    }

    display.addEventListener('click', e => {
        e.stopPropagation();
        dropdown.classList.contains('open') ? closeDropdown() : openDropdown();
    });

    document.addEventListener('click', closeDropdown);

    function syncIdleCard() {
        const opt = sel.options[sel.selectedIndex];
        const nameIdleEl = document.getElementById('idle-lesson-name');
        const metaEl = document.getElementById('idle-lesson-meta');
        if (!nameIdleEl) return;
        if (opt && opt.value) {
            nameIdleEl.textContent = cleanText(opt.text);
            if (metaEl) {
                if (items && items.length) {
                    metaEl.textContent = items.length + ' words · 5 steps';
                } else {
                    metaEl.textContent = 'Loading...';
                    var _sub = typeof currentSubject !== 'undefined' ? currentSubject : 'English';
                    var _tb  = typeof currentTextbook !== 'undefined' ? currentTextbook : 'Voca_8000';
                    fetch('/api/study/' + encodeURIComponent(_sub) + '/' + encodeURIComponent(_tb) + '/' + encodeURIComponent(opt.value))
                        .then(function(r) { return r.json(); })
                        .then(function(d) {
                            var cnt = (d.items && d.items.length) ? d.items.length : 0;
                            metaEl.textContent = cnt + ' words · 5 steps';
                        })
                        .catch(function() { metaEl.textContent = '0 words · 5 steps'; });
                }
            }
        } else {
            nameIdleEl.textContent = 'Select a lesson to begin';
            if (metaEl) metaEl.textContent = '';
        }
    }

    sel.addEventListener('change', () => {
        sync();
        syncIdleCard();
        if (dropdown.classList.contains('open')) buildDropdown();
    });
    new MutationObserver(() => {
        sync();
        syncIdleCard();
        if (dropdown.classList.contains('open')) buildDropdown();
    }).observe(sel, { childList: true, subtree: true });
    sync();
    syncIdleCard();
}

/**
 * Initialise the custom textbook-dropdown UI that mirrors the hidden <select>.
 * @tag NAVIGATION SIDEBAR
 */
function initTextbookDropdownUI() {
    const sel      = document.getElementById('textbook-select');
    const display  = document.getElementById('sb-textbook-name');
    const dropdown = document.getElementById('sb-tb-dropdown');
    if (!sel || !display || !dropdown) return;

    const nameEl = display.querySelector('.sb-tb-name-text');

    function sync() {
        const opt = sel.options[sel.selectedIndex];
        if (nameEl) nameEl.textContent = (opt && opt.value) ? opt.text : '—';
    }

    function buildDropdown() {
        dropdown.innerHTML = '';
        const cur = sel.value;
        Array.from(sel.options).filter(o => o.value).forEach(opt => {
            const item = document.createElement('div');
            item.className = 'sb-tb-option' + (opt.value === cur ? ' selected' : '');
            item.textContent = opt.text;
            item.addEventListener('click', () => {
                sel.value = opt.value;
                sel.dispatchEvent(new Event('change'));
                closeDropdown();
            });
            dropdown.appendChild(item);
        });
    }

    function positionDropdown() {
        const rect = display.getBoundingClientRect();
        const availableBelow = window.innerHeight - rect.bottom - 8;
        dropdown.style.top       = (rect.bottom + 4) + 'px';
        dropdown.style.left      = rect.left + 'px';
        dropdown.style.width     = rect.width + 'px';
        dropdown.style.maxHeight = Math.min(360, availableBelow) + 'px';
    }

    function openDropdown() {
        buildDropdown();
        positionDropdown();
        dropdown.classList.add('open');
        display.classList.add('open');
    }

    function closeDropdown() {
        dropdown.classList.remove('open');
        display.classList.remove('open');
    }

    display.addEventListener('click', e => {
        e.stopPropagation();
        dropdown.classList.contains('open') ? closeDropdown() : openDropdown();
    });

    document.addEventListener('click', closeDropdown);

    sel.addEventListener('change', sync);
    new MutationObserver(() => {
        sync();
        if (dropdown.classList.contains('open')) buildDropdown();
    }).observe(sel, { childList: true, subtree: true });
    sync();
}

/**
 * Initialise the OCR "Register (image → words)" button.
 * Hides itself when the lesson is already ready, shows and triggers OCR otherwise.
 * @tag OCR NAVIGATION
 */
function initOcrButton() {
    const ocrBtn = document.getElementById('btn-ocr');
    if (!ocrBtn) return;

    function updateOcrBtn() {
        const sel = document.getElementById('lesson-select');
        if (!sel || !sel.value) { ocrBtn.style.display = 'none'; return; }
        const opt = sel.options[sel.selectedIndex];
        const isReady = opt && opt.dataset.ready !== 'false';
        ocrBtn.style.display = isReady ? 'none' : 'block';
        ocrBtn.dataset.lesson = sel.value;
    }

    const lessonSel = document.getElementById('lesson-select');
    if (lessonSel) lessonSel.addEventListener('change', () => setTimeout(updateOcrBtn, 50));
    updateOcrBtn();

    ocrBtn.addEventListener('click', async () => {
        const lesson = ocrBtn.dataset.lesson;
        if (!lesson) return;
        ocrBtn.textContent = '⏳ Running OCR… (30–60 s)';
        ocrBtn.classList.add('loading');
        ocrBtn.disabled = true;
        try {
            const res = await fetch(`/api/lessons/ingest_disk/${encodeURIComponent(lesson)}`, {
                method: 'POST'
            });
            const data = await res.json();
            if (!res.ok) throw new Error(data.detail || 'OCR failed');
            ocrBtn.innerHTML = `<i data-lucide="check"></i> ${data.words} words registered!`;
            ocrBtn.style.borderColor = 'var(--color-success)';
            ocrBtn.style.color = 'var(--color-success-ink)';
            if (typeof lucide !== 'undefined') lucide.createIcons();
            setTimeout(() => { window.location.reload(); }, 1500);
        } catch (err) {
            ocrBtn.innerHTML = `<i data-lucide="x-circle"></i> Error: ${escapeHtml(err.message || 'Unknown error')}`;
            if (typeof lucide !== 'undefined') lucide.createIcons();
            ocrBtn.classList.remove('loading');
            ocrBtn.disabled = false;
        }
    });
}
