/* ================================================================
   ckla.js — CKLA G3 domain/lesson navigation
   Section: Academy
   Dependencies: core.js
   API endpoints: /api/academy/ckla/domains, /api/academy/ckla/domains/{n}/lessons,
                  /api/academy/ckla/lessons/{id}
   ================================================================ */

/** @type {{ screen: string, domainNum: number|null, domainTitle: string }} */
let cklaNav = { screen: 'domains', domainNum: null, domainTitle: '' };


/* ── Entry / Exit ──────────────────────────────────────────────────────────── */

/** Show the CKLA view and render domain list. @tag ACADEMY CKLA */
function showCKLAView() {
  // Hide other English-mode views
  ['idle-wrapper', 'stage-card', 'daily-words-view'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.style.display = 'none';
  });
  const view = document.getElementById('ckla-view');
  if (view) { view.style.display = 'flex'; }
  // Sidebar: switch to English mode if needed
  if (typeof switchView === 'function') switchView('english');
  loadCKLADomains();
}

/** Return to the idle screen from CKLA. @tag ACADEMY CKLA */
function hideCKLAView() {
  const view = document.getElementById('ckla-view');
  if (view) view.style.display = 'none';
  const idle = document.getElementById('idle-wrapper');
  if (idle) idle.style.display = '';
}


/* ── Domain list ───────────────────────────────────────────────────────────── */

/** Fetch and render all 11 CKLA domains. @tag ACADEMY CKLA */
async function loadCKLADomains() {
  cklaNav.screen = 'domains';
  const view = document.getElementById('ckla-view');
  if (!view) return;
  view.innerHTML = '<div class="ckla-loading">Loading…</div>';
  try {
    const res = await fetch('/api/academy/ckla/domains');
    if (!res.ok) throw new Error('Failed to load');
    const domains = await res.json();
    _renderDomains(domains);
  } catch (e) {
    view.innerHTML = `<div class="ckla-empty">Could not load domains. ${e.message}</div>`;
  }
}

/** @tag ACADEMY CKLA */
function _renderDomains(domains) {
  const view = document.getElementById('ckla-view');
  view.innerHTML = `
    <div class="ckla-header">
      <button class="ckla-back-btn" onclick="hideCKLAView()">← Back</button>
      <h2 class="ckla-title">CKLA Grade 3</h2>
    </div>
    <div class="ckla-domain-grid">
      ${domains.map(d => `
        <div class="ckla-domain-card" onclick="loadCKLALessons(${d.domain_num})">
          <div class="ckla-domain-num">Domain ${d.domain_num}</div>
          <div class="ckla-domain-title">${d.title}</div>
          <div class="ckla-domain-lessons">${d.lesson_count} lessons</div>
        </div>
      `).join('')}
    </div>`;
}


/* ── Lesson list ───────────────────────────────────────────────────────────── */

/** Fetch and render lessons for one domain. @tag ACADEMY CKLA */
async function loadCKLALessons(domainNum) {
  cklaNav.screen = 'lessons';
  cklaNav.domainNum = domainNum;
  const view = document.getElementById('ckla-view');
  if (!view) return;
  view.innerHTML = '<div class="ckla-loading">Loading…</div>';
  try {
    const res = await fetch(`/api/academy/ckla/domains/${domainNum}/lessons`);
    if (!res.ok) throw new Error('Failed to load');
    const data = await res.json();
    cklaNav.domainTitle = data.domain.title;
    _renderLessons(data);
  } catch (e) {
    view.innerHTML = `<div class="ckla-empty">Could not load lessons. ${e.message}</div>`;
  }
}

/** @tag ACADEMY CKLA */
function _renderLessons(data) {
  const view = document.getElementById('ckla-view');
  const progressIcons = [
    { key: 'reading_done',         icon: '📖', label: 'Read' },
    { key: 'vocab_done',           icon: '📝', label: 'Words' },
    { key: 'questions_attempted',  icon: '❓', label: 'Q&A', isCount: true },
    { key: 'word_work_done',       icon: '⭐', label: 'WW' },
  ];

  view.innerHTML = `
    <div class="ckla-header">
      <button class="ckla-back-btn" onclick="loadCKLADomains()">← Domains</button>
      <h2 class="ckla-title">D${data.domain.domain_num}: ${data.domain.title}</h2>
    </div>
    <div class="ckla-lesson-list">
      ${data.lessons.map(l => {
        const p = l.progress;
        const chips = progressIcons.map(pi => {
          const done = pi.isCount ? (p[pi.key] > 0) : p[pi.key];
          return `<span class="ckla-chip ${done ? 'ckla-chip-done' : ''}" title="${pi.label}">${pi.icon}</span>`;
        }).join('');
        const isDone = p.completed;
        return `
          <div class="ckla-lesson-row${isDone ? ' ckla-lesson-done' : ''}"
               onclick="openCKLALesson(${l.id})">
            <div class="ckla-lesson-meta">
              <span class="ckla-lesson-num">Lesson ${l.lesson_num}</span>
              ${l.word_work_word ? `<span class="ckla-lesson-ww">★ ${l.word_work_word}</span>` : ''}
            </div>
            <div class="ckla-lesson-title">${l.title}</div>
            <div class="ckla-lesson-chips">${chips}</div>
          </div>`;
      }).join('')}
    </div>`;
}


/* ── Lesson detail ─────────────────────────────────────────────────────────── */

/** Fetch lesson data and enter lesson view (delegates to ckla-lesson.js). @tag ACADEMY CKLA */
async function openCKLALesson(lessonId) {
  cklaNav.screen = 'lesson';
  const view = document.getElementById('ckla-view');
  if (!view) return;
  view.innerHTML = '<div class="ckla-loading">Loading lesson…</div>';
  try {
    const res = await fetch(`/api/academy/ckla/lessons/${lessonId}`);
    if (!res.ok) throw new Error('Failed to load');
    const data = await res.json();
    renderCKLALesson(data);   // defined in ckla-lesson.js
  } catch (e) {
    view.innerHTML = `<div class="ckla-empty">Could not load lesson. ${e.message}</div>`;
  }
}
