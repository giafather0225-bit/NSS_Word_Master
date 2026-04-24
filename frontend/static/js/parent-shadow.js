/* ================================================================
   parent-shadow.js — Shadow AI Settings tab for Parent Dashboard
   Section: Parent
   Dependencies: parent-panel.js
   API endpoints: GET/POST /api/assistant/settings, GET /api/assistant/logs
   ================================================================ */

/** @tag PARENT AI_ASSISTANT */
async function _ppShadow(body) {
    body.innerHTML = `<p style="text-align:center;padding:40px;color:var(--text-secondary);">Loading…</p>`;

    const [settingsRes, logsRes, usageRes] = await Promise.all([
        fetch('/api/assistant/settings').then(r => r.json()).catch(() => ({})),
        fetch('/api/assistant/logs?limit=30').then(r => r.json()).catch(() => []),
        fetch('/api/assistant/usage').then(r => r.json()).catch(() => ({})),
    ]);

    const s = settingsRes;
    const logs = Array.isArray(logsRes) ? logsRes : [];

    body.innerHTML = `
    <div style="padding:20px;max-width:600px;margin:0 auto;display:flex;flex-direction:column;gap:24px;">

      <!-- Status banner -->
      <div style="background:var(--color-primary-light);border-radius:var(--radius-md);padding:14px 16px;display:flex;justify-content:space-between;align-items:center;">
        <span style="font-size:var(--font-size-sm);color:var(--text-primary);font-weight:var(--font-weight-medium);">Shadow AI</span>
        <span style="font-size:var(--font-size-sm);color:var(--text-secondary);">
          Today: <strong>${usageRes.used_today ?? 0}/${usageRes.limit ?? 30}</strong> chats
        </span>
      </div>

      <!-- Gia Profile -->
      <div class="pp-section">
        <div class="pp-section-title">Gia's Profile</div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
          ${_shadowField('shadow_gia_name',  'Name',     s.shadow_gia_name  ?? 'Gia')}
          ${_shadowField('shadow_gia_age',   'Age',      s.shadow_gia_age   ?? '9')}
          ${_shadowField('shadow_gia_school','School',   s.shadow_gia_school ?? 'international school', 'col-span')}
          ${_shadowField('shadow_gia_interests','Interests (comma-separated)', s.shadow_gia_interests ?? 'reading, math, drawing', 'col-span')}
        </div>
      </div>

      <!-- Limits -->
      <div class="pp-section">
        <div class="pp-section-title">Limits</div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
          ${_shadowField('shadow_daily_limit',     'Daily chat limit',     s.shadow_daily_limit     ?? '30', '', 'number')}
          ${_shadowField('shadow_session_minutes', 'Session length (min)', s.shadow_session_minutes ?? '15', '', 'number')}
        </div>
      </div>

      <!-- Blocked Topics -->
      <div class="pp-section">
        <div class="pp-section-title">Blocked Topics</div>
        <p style="font-size:var(--font-size-sm);color:var(--text-secondary);margin:0 0 10px;">Extra topics Shadow should avoid (e.g. "games, YouTube, celebrities").</p>
        ${_shadowField('shadow_blocked_topics', 'Blocked topics', s.shadow_blocked_topics ?? '', 'col-span')}
      </div>

      <!-- Save button -->
      <button onclick="_ppShadowSave()" class="pp-action-btn" style="align-self:flex-start;">
        Save Settings
      </button>

      <!-- Chat Log -->
      <div class="pp-section">
        <div class="pp-section-title">Recent Chats</div>
        ${logs.length === 0
          ? `<p style="color:var(--text-hint);font-size:var(--font-size-sm);">No chats yet.</p>`
          : `<div style="display:flex;flex-direction:column;gap:8px;max-height:340px;overflow-y:auto;">
              ${logs.map(l => `
                <div style="border:1px solid var(--border-subtle);border-radius:var(--radius-md);padding:10px 12px;font-size:var(--font-size-sm);">
                  ${l.was_blocked ? `<span style="color:var(--color-error);font-weight:600;font-size:11px;">BLOCKED</span> ` : ''}
                  <span style="color:var(--text-hint);font-size:11px;">${l.created_at?.slice(0,16).replace('T',' ')}</span>
                  <div style="margin-top:4px;"><strong>Gia:</strong> ${_esc(l.user_message)}</div>
                  <div style="margin-top:2px;color:var(--text-secondary);"><strong>Shadow:</strong> ${_esc(l.assistant_reply)}</div>
                </div>`).join('')}
             </div>`
        }
      </div>

    </div>`;
}

function _shadowField(key, label, value, extraClass = '', type = 'text') {
    const span = extraClass === 'col-span' ? 'grid-column:1/-1;' : '';
    return `
      <label style="${span}display:flex;flex-direction:column;gap:4px;font-size:var(--font-size-sm);color:var(--text-secondary);">
        ${label}
        <input id="sf-${key}" type="${type}" value="${_esc(value)}"
          style="padding:8px 10px;border:1px solid var(--border-default);border-radius:var(--radius-sm);font-size:var(--font-size-sm);color:var(--text-primary);background:var(--bg-card);width:100%;box-sizing:border-box;">
      </label>`;
}

async function _ppShadowSave() {
    const keys = ['shadow_gia_name','shadow_gia_age','shadow_gia_school','shadow_gia_interests',
                  'shadow_daily_limit','shadow_session_minutes','shadow_blocked_topics'];
    const body = {};
    for (const k of keys) {
        const el = document.getElementById(`sf-${k}`);
        if (el) body[k] = el.value.trim();
    }
    try {
        const res = await fetch('/api/assistant/settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        });
        if (res.ok) {
            const btn = document.querySelector('[onclick="_ppShadowSave()"]');
            if (btn) { btn.textContent = 'Saved!'; setTimeout(() => btn.textContent = 'Save Settings', 2000); }
        }
    } catch (e) {
        alert('Save failed. Please try again.');
    }
}

function _esc(str) {
    return String(str ?? '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}
