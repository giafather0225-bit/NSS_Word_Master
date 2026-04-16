/* ================================================================
   service-worker.js — GIA Learning PWA Service Worker (minimal)
   Section: System
   Dependencies: none
   API endpoints: none
   ================================================================ */

// Minimal service worker for PWA install support
// Offline caching can be added later

/** @tag SYSTEM @tag PWA */
const CACHE_NAME = 'gia-v1';

self.addEventListener('install', () => {
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(clients.claim());
});

self.addEventListener('fetch', (event) => {
  // Network-first strategy (no caching yet)
  event.respondWith(fetch(event.request));
});
