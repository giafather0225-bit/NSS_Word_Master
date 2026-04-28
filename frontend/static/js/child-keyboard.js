/* ================================================================
   child-keyboard.js — Global keyboard shortcuts for the learning shell
   Section: System / Navigation
   Dependencies: STAGE (core.js), currentItem/apiWordOnly/isStageUnlocked/jumpToStage (core.js, child.js)
   API endpoints: none
   ================================================================ */

/**
 * Register global keyboard shortcuts (Space, Esc, 1–5, ⌘L, ⌘\, ⌘,).
 * @tag NAVIGATION SYSTEM
 */
function initKeyboardShortcuts() {
    document.addEventListener('keydown', (e) => {
        const active = document.activeElement;
        const inInput = active && (
            active.tagName === 'INPUT' ||
            active.tagName === 'TEXTAREA' ||
            active.isContentEditable
        );

        if (e.code === 'Space' && !inInput) {
            e.preventDefault();
            const item = typeof currentItem === 'function' && currentItem();
            if (item && typeof apiWordOnly === 'function') {
                apiWordOnly(item.answer);
            } else {
                const soundBtn = document.querySelector('[data-action="sound"], #btn-sound, .st-btn.sound');
                if (soundBtn) soundBtn.click();
            }
        }

        if (e.key === 'Escape') {
            const modals = [
                document.getElementById('preview-modal'),
                document.getElementById('tutor-modal'),
                document.getElementById('magic-overlay'),
            ];
            for (const el of modals) {
                if (el && !el.hidden && el.style.display !== 'none') {
                    el.hidden = true;
                    el.style.display = 'none';
                    break;
                }
            }
        }

        if (!inInput && e.key >= '1' && e.key <= '5') {
            const stageMap = { '1': STAGE.PREVIEW, '2': STAGE.A, '3': STAGE.B, '4': STAGE.C, '5': STAGE.D };
            const target = stageMap[e.key];
            if (target && isStageUnlocked(target)) {
                e.preventDefault();
                jumpToStage(target);
            }
        }

        if (e.metaKey && e.key === 'l') {
            e.preventDefault();
            const sel = document.getElementById('lesson-select');
            if (sel && sel.options.length > 1) {
                const next = (sel.selectedIndex + 1) % sel.options.length || 1;
                sel.selectedIndex = next;
                sel.dispatchEvent(new Event('change'));
            }
        }

        if (e.metaKey && e.key === '\\') {
            e.preventDefault();
            document.getElementById('sidebar').classList.toggle('collapsed');
        }

        if (e.metaKey && e.key === ',') {
            e.preventDefault();
            document.getElementById('btn-parent')?.click();
        }
    });
}

/**
 * Open Parent Dashboard from home dashboard gear button.
 * Delegates to the sidebar #btn-parent click handler.
 * @tag PARENT HOME_DASHBOARD
 */
function openParentDashboard() {
    if (typeof openParentPanel === 'function') {
        openParentPanel();
    } else {
        document.getElementById('btn-parent')?.click();
    }
}
