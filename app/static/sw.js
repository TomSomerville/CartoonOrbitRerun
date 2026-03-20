// Bump this version to force all clients to drop the old cache immediately.
const CACHE_NAME = 'cor-assets-v2';
const MAX_AGE_MS = 7 * 24 * 60 * 60 * 1000; // 7 days

function shouldCache(url) {
    try {
        const path = new URL(url).pathname;
        return (
            path.startsWith('/static/') ||
            path.startsWith('/ctoon-img/') ||
            path.startsWith('/czone-bg/')
        );
    } catch {
        return false;
    }
}

// Activate immediately — don't wait for existing tabs to close.
self.addEventListener('install', () => self.skipWaiting());

// On activate: purge any old-version caches, then take control of all clients.
self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys()
            .then((keys) => Promise.all(
                keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k))
            ))
            .then(() => self.clients.claim())
    );
});

self.addEventListener('fetch', (event) => {
    if (event.request.method !== 'GET') return;
    if (!shouldCache(event.request.url)) return;
    event.respondWith(cacheFirst(event.request));
});

async function cacheFirst(request) {
    const cache  = await caches.open(CACHE_NAME);
    const cached = await cache.match(request);

    if (cached) {
        // Use our own timestamp header — never rely on the server's Date header.
        const cachedAt = cached.headers.get('X-SW-Cached-At');
        if (cachedAt) {
            const age = Date.now() - parseInt(cachedAt, 10);
            if (age < MAX_AGE_MS) {
                return cached; // Fresh — serve straight from cache.
            }
            // Expired — fall through and re-fetch.
        } else {
            // Legacy entry with no timestamp (e.g. from v1): treat as expired.
        }
    }

    // Cache miss or expired: fetch from network.
    try {
        const networkRes = await fetch(request);

        if (networkRes.ok) {
            // Build a new Response that's identical to the network response but
            // carries our own cache timestamp. We must clone the body because a
            // Response body can only be read once.
            const body    = await networkRes.clone().blob();
            const headers = new Headers(networkRes.headers);
            headers.set('X-SW-Cached-At', String(Date.now()));

            cache.put(request, new Response(body, {
                status:     networkRes.status,
                statusText: networkRes.statusText,
                headers,
            }));
        }

        // Return the original network response to the page.
        return networkRes;
    } catch (err) {
        // Network unavailable — return stale cached copy rather than an error.
        if (cached) return cached;
        throw err;
    }
}
