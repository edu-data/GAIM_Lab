// GAIM Lab Service Worker — PWA 오프라인 리포트 열람
const CACHE_NAME = 'gaim-lab-v71'
const STATIC_ASSETS = [
    '/',
    '/index.html',
    '/manifest.json',
]

// Install — cache static assets
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            return cache.addAll(STATIC_ASSETS)
        })
    )
    self.skipWaiting()
})

// Activate — clean old caches
self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((keys) => {
            return Promise.all(
                keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))
            )
        })
    )
    self.clients.claim()
})

// Fetch — network first, cache fallback (for HTML reports)
self.addEventListener('fetch', (event) => {
    const { request } = event

    // Skip non-GET requests
    if (request.method !== 'GET') return

    // API calls — network only
    if (request.url.includes('/api/')) return

    // HTML reports from /output/ — cache first for offline viewing
    if (request.url.includes('/output/') && request.url.endsWith('.html')) {
        event.respondWith(
            caches.open(CACHE_NAME).then((cache) => {
                return fetch(request).then((response) => {
                    cache.put(request, response.clone())
                    return response
                }).catch(() => {
                    return cache.match(request)
                })
            })
        )
        return
    }

    // Static assets — stale-while-revalidate
    event.respondWith(
        caches.match(request).then((cached) => {
            const networked = fetch(request).then((response) => {
                const clone = response.clone()
                caches.open(CACHE_NAME).then((cache) => cache.put(request, clone))
                return response
            }).catch(() => cached)

            return cached || networked
        })
    )
})
