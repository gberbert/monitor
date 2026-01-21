const CACHE_NAME = 'antigravity-vms-v1';
const ASSETS_TO_CACHE = [
    '/',
    '/index.html',
    '/dashboard.html',
    '/player.html',
    '/manifest.json',
    '/placeholder_error.png'
];

// Install Event: Cache Static Assets
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then((cache) => cache.addAll(ASSETS_TO_CACHE))
            .then(() => self.skipWaiting())
    );
});

// Activate Event: Cleanup Old Caches
self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((keyList) => {
            return Promise.all(keyList.map((key) => {
                if (key !== CACHE_NAME) {
                    return caches.delete(key);
                }
            }));
        }).then(() => self.clients.claim())
    );
});

// Fetch Event: Network First, Fallback to Cache (except for API/Video)
self.addEventListener('fetch', (event) => {
    const url = new URL(event.request.url);

    // IGNORE VIDEO STREAMS & API calls (Always Network Only)
    if (url.pathname.startsWith('/api') || url.searchParams.has('src')) {
        return; // Let browser handle normally (no service worker)
    }

    // For HTML/CSS/JS: Try Network first to get latest updates, fallback to cache if offline
    event.respondWith(
        fetch(event.request)
            .catch(() => {
                return caches.match(event.request);
            })
    );
});
