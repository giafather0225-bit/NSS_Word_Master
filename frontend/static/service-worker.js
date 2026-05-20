/* ================================================================
   service-worker.js — GIA Learning PWA offline-lite cache
   Section: System
   Dependencies: none
   API endpoints: passively caches GET /api/math/* (read-only)
   ================================================================ */

/** @tag SYSTEM @tag PWA @tag OFFLINE */
const SW_VERSION = 'gia-sw-v11';
const STATIC_CACHE = `${SW_VERSION}-static`;
const DATA_CACHE   = `${SW_VERSION}-data`;

// App shell: cached on install. Entries are stored under their pathname
// only — the `?v=…` cache-busters that `build.sh` rewrites in child.html
// are normalised away at lookup time via `ignoreSearch: true` in the
// cacheFirst handler. This lets a fresh deploy's `?v=4c7a5441` request
// still serve the previously precached file when the user is offline.
const APP_SHELL = [
    // Core stylesheets
    '/static/css/theme.css',
    '/static/css/base.css',
    '/static/css/layout.css',
    '/static/css/components.css',
    '/static/css/utilities.css',
    '/static/css/legacy-app.css',
    '/static/css/main-shell.css',
    '/static/css/main-idle.css',
    '/static/css/main-topbar.css',
    '/static/css/main-stage.css',
    '/static/css/main-responsive.css',
    '/static/css/main-layout.css',
    '/static/css/toast.css',
    // Home + the primary subjects (Home is the default landing view;
    // CKLA + Diary are the most common navigation targets).
    '/static/css/home.css',
    '/static/css/daily-words.css',
    '/static/css/ckla.css',
    '/static/css/diary.css',
    '/static/css/diary-home.css',
    // Math academy core
    '/static/css/math-academy-sidebar.css',
    '/static/css/math-academy-stages.css',
    '/static/css/math-academy-fluency.css',
    '/static/css/math-academy-modes.css',
    '/static/css/math-academy-content.css',
    '/static/css/math-academy-anim.css',
    // Core JS (loaded before bundle-a in child.html)
    '/static/js/core.js',
    '/static/js/core-fx.js',
    '/static/js/core-stage.js',
    '/static/js/tts-client.js',
    '/static/js/navigation.js',
    // Feature bundles
    '/static/js/bundle-a.min.js',
    '/static/js/bundle-b.min.js',
];

// Precache APP_SHELL on install so the app boots offline after the very
// first visit, then skipWaiting so the new SW activates immediately.
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(STATIC_CACHE)
            .then((cache) => cache.addAll(APP_SHELL))
            .catch(() => {})
            .then(() => self.skipWaiting())
    );
});

// On activate, drop only caches from *previous* SW versions. The current
// version's STATIC_CACHE and DATA_CACHE are kept so that data the user
// already downloaded (CKLA lessons, math sets, etc.) survives SW updates.
self.addEventListener('activate', (event) => {
    const keep = new Set([STATIC_CACHE, DATA_CACHE]);
    event.waitUntil(
        caches.keys()
            .then((keys) => Promise.all(
                keys.filter((k) => !keep.has(k)).map((k) => caches.delete(k))
            ))
            .then(() => self.clients.claim())
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
    // CKLA — read-only catalog + lesson content. POSTs (submit, mark-done)
    // are filtered out by the method !== 'GET' guard above.
    if (p.startsWith('/api/academy/ckla/')) return true;
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
    // ignoreSearch so a fresh ?v=… cache-buster still matches the
    // previously precached pathname-only entry from APP_SHELL.
    const cached = await cache.match(req, { ignoreSearch: true });
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
