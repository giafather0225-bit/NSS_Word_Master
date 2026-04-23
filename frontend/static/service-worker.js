/* ================================================================
   service-worker.js — GIA Learning PWA offline-lite cache
   Section: System
   Dependencies: none
   API endpoints: passively caches GET /api/math/* (read-only)
   ================================================================ */

/** @tag SYSTEM @tag PWA @tag OFFLINE */
const SW_VERSION = 'gia-sw-v5';
const STATIC_CACHE = `${SW_VERSION}-static`;
const DATA_CACHE   = `${SW_VERSION}-data`;

// App shell: cached on install. Keep list short — other assets are added
// on-demand via the runtime fetch handler (stale-while-revalidate).
const APP_SHELL = [
    '/static/css/theme.css',
    '/static/css/base.css?v=1',
    '/static/css/layout.css?v=1',
    '/static/css/components.css?v=1',
    '/static/css/utilities.css?v=1',
    '/static/css/legacy-app.css?v=1',
    '/static/css/main-shell.css?v=1',
    '/static/css/main-idle.css?v=1',
    '/static/css/main-topbar.css?v=1',
    '/static/css/main-stage.css?v=1',
    '/static/css/main-responsive.css?v=1',
    '/static/css/main-layout.css?v=1',
    '/static/css/math-academy-sidebar.css?v=1',
    '/static/css/math-academy-stages.css?v=1',
    '/static/css/math-academy-fluency.css?v=1',
    '/static/css/math-academy-modes.css?v=1',
    '/static/css/math-academy-content.css?v=1',
    '/static/css/math-academy-anim.css?v=1',
    '/static/css/toast.css?v=1',
    '/static/js/core.js?v=2',
    '/static/js/tts-client.js?v=1',
    '/static/js/navigation.js?v=1',
    '/static/js/math-academy.js?v=5',
    '/static/js/math-problem-ui.js?v=4',
    '/static/js/math-learn-cards.js?v=1',
    '/static/js/math-navigation.js?v=5',
];

// ── Install: pre-cache app shell ───────────────────────────
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(STATIC_CACHE)
            .then((cache) => cache.addAll(APP_SHELL).catch(() => Promise.resolve()))
            .then(() => self.skipWaiting())
    );
});

// ── Activate: clean old caches ─────────────────────────────
self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((keys) =>
            Promise.all(
                keys
                    .filter((k) => !k.startsWith(SW_VERSION))
                    .map((k) => caches.delete(k))
            )
        ).then(() => self.clients.claim())
    );
});

// ── Routing helpers ────────────────────────────────────────
function isStaticAsset(url) {
    return url.pathname.startsWith('/static/');
}

function isCacheableApi(url, method) {
    if (method !== 'GET') return false;
    const p = url.pathname;
    // Math
    if (p.startsWith('/api/math/academy/') && !p.endsWith('/submit-answer')) return true;
    if (p.startsWith('/api/math/glossary/')) return true;
    if (p.startsWith('/api/math/kangaroo/set')) return true;
    if (p === '/api/math/kangaroo/sets') return true;
    if (p === '/api/math/daily/today') return true;
    // English — read-only lesson data (safe to serve stale offline)
    if (p === '/api/subjects') return true;
    if (p.startsWith('/api/textbooks/')) return true;
    if (p.startsWith('/api/voca/')) return true;
    if (p.startsWith('/api/lessons/')) return true;
    if (p.startsWith('/api/study/')) return true;
    if (p.startsWith('/api/words/')) return true;
    if (p === '/api/daily-words/today' || p === '/api/daily-words/status') return true;
    if (p === '/api/daily-words/weekly-test') return true;
    return false;
}

// ── Fetch handler ─────────────────────────────────────────
self.addEventListener('fetch', (event) => {
    const req = event.request;
    const url = new URL(req.url);

    // Same-origin only.
    if (url.origin !== self.location.origin) return;

    if (isStaticAsset(url)) {
        event.respondWith(cacheFirst(req, STATIC_CACHE));
        return;
    }

    // HTML pages (/, /child, /parent, ...) — network-first with cache fallback
    // so the app shell is available offline after first visit.
    if (req.method === 'GET' && req.mode === 'navigate') {
        event.respondWith(networkFirst(req, STATIC_CACHE));
        return;
    }

    if (isCacheableApi(url, req.method)) {
        event.respondWith(staleWhileRevalidate(req, DATA_CACHE));
        return;
    }

    // Everything else: default network handling (do not intercept).
});

// ── Strategies ─────────────────────────────────────────────
async function cacheFirst(req, cacheName) {
    const cache = await caches.open(cacheName);
    const cached = await cache.match(req);
    if (cached) {
        fetch(req).then((res) => {
            if (res && res.ok) cache.put(req, res.clone());
        }).catch(() => {});
        return cached;
    }
    try {
        const res = await fetch(req);
        if (res && res.ok) cache.put(req, res.clone());
        return res;
    } catch (err) {
        return new Response('Offline', { status: 503, statusText: 'Offline' });
    }
}

async function networkFirst(req, cacheName) {
    const cache = await caches.open(cacheName);
    try {
        const res = await fetch(req);
        if (res && res.ok) cache.put(req, res.clone());
        return res;
    } catch {
        const cached = await cache.match(req);
        if (cached) return cached;
        return new Response('Offline — page not cached yet', { status: 503 });
    }
}

async function staleWhileRevalidate(req, cacheName) {
    const cache = await caches.open(cacheName);
    const cached = await cache.match(req);
    const fetchPromise = fetch(req).then((res) => {
        if (res && res.ok) cache.put(req, res.clone());
        return res;
    }).catch(() => null);

    if (cached) return cached;
    const network = await fetchPromise;
    if (network) return network;
    return new Response(JSON.stringify({ error: 'offline', cached: false }), {
        status: 503,
        headers: { 'Content-Type': 'application/json' },
    });
}
