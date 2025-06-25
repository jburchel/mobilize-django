/**
 * Service Worker for Mobilize CRM
 * Implements caching strategies for improved performance and offline support
 */

const CACHE_VERSION = 'v1';
const CACHE_NAME = `mobilize-${CACHE_VERSION}`;
const RUNTIME_CACHE = 'mobilize-runtime';

// Files to cache on install
const STATIC_CACHE_URLS = [
    '/',
    '/static/css/base.min.css',
    '/static/js/lazy-loading.js',
    '/static/js/image-lazy-loader.js',
    '/static/images/logo.png',
    '/static/images/favicon.png',
    'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css',
    'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css',
];

// Cache strategies
const CACHE_STRATEGIES = {
    networkFirst: [
        '/api/',
        '/contacts/api/',
        '/churches/api/',
        '/tasks/api/',
        '/communications/api/',
    ],
    cacheFirst: [
        '/static/',
        'https://cdn.jsdelivr.net/',
        'https://cdnjs.cloudflare.com/',
        'https://code.jquery.com/',
    ],
    staleWhileRevalidate: [
        '/media/',
        '/images/',
    ],
};

// Install event - cache static assets
self.addEventListener('install', (event) => {
    console.log('[SW] Installing Service Worker');
    
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => {
                console.log('[SW] Caching static assets');
                return cache.addAll(STATIC_CACHE_URLS);
            })
            .then(() => self.skipWaiting())
            .catch(err => console.error('[SW] Cache install failed:', err))
    );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
    console.log('[SW] Activating Service Worker');
    
    event.waitUntil(
        caches.keys()
            .then(cacheNames => {
                return Promise.all(
                    cacheNames
                        .filter(cacheName => {
                            return cacheName.startsWith('mobilize-') && 
                                   cacheName !== CACHE_NAME;
                        })
                        .map(cacheName => {
                            console.log('[SW] Deleting old cache:', cacheName);
                            return caches.delete(cacheName);
                        })
                );
            })
            .then(() => self.clients.claim())
    );
});

// Fetch event - implement caching strategies
self.addEventListener('fetch', (event) => {
    const { request } = event;
    const url = new URL(request.url);
    
    // Skip non-GET requests
    if (request.method !== 'GET') {
        return;
    }
    
    // Determine caching strategy
    const strategy = getStrategy(url.pathname);
    
    event.respondWith(
        strategy(request).catch(() => {
            // If all else fails, return offline page if available
            if (request.destination === 'document') {
                return caches.match('/offline.html');
            }
        })
    );
});

// Caching strategies implementation
function getStrategy(pathname) {
    // Network first (API calls)
    for (const pattern of CACHE_STRATEGIES.networkFirst) {
        if (pathname.includes(pattern)) {
            return networkFirst;
        }
    }
    
    // Cache first (static assets)
    for (const pattern of CACHE_STRATEGIES.cacheFirst) {
        if (pathname.includes(pattern)) {
            return cacheFirst;
        }
    }
    
    // Stale while revalidate (images, media)
    for (const pattern of CACHE_STRATEGIES.staleWhileRevalidate) {
        if (pathname.includes(pattern)) {
            return staleWhileRevalidate;
        }
    }
    
    // Default to network first
    return networkFirst;
}

// Network first strategy - try network, fallback to cache
async function networkFirst(request) {
    try {
        const networkResponse = await fetch(request);
        
        // Cache successful responses
        if (networkResponse.ok) {
            const cache = await caches.open(RUNTIME_CACHE);
            cache.put(request, networkResponse.clone());
        }
        
        return networkResponse;
    } catch (error) {
        console.log('[SW] Network failed, trying cache:', error);
        const cachedResponse = await caches.match(request);
        
        if (cachedResponse) {
            return cachedResponse;
        }
        
        throw error;
    }
}

// Cache first strategy - try cache, fallback to network
async function cacheFirst(request) {
    const cachedResponse = await caches.match(request);
    
    if (cachedResponse) {
        // Return cached version immediately
        return cachedResponse;
    }
    
    // Not in cache, try network
    try {
        const networkResponse = await fetch(request);
        
        // Cache for next time
        if (networkResponse.ok) {
            const cache = await caches.open(CACHE_NAME);
            cache.put(request, networkResponse.clone());
        }
        
        return networkResponse;
    } catch (error) {
        console.error('[SW] Network request failed:', error);
        throw error;
    }
}

// Stale while revalidate - return cache immediately, update in background
async function staleWhileRevalidate(request) {
    const cache = await caches.open(RUNTIME_CACHE);
    const cachedResponse = await cache.match(request);
    
    // Fetch fresh version in background
    const fetchPromise = fetch(request).then(networkResponse => {
        if (networkResponse.ok) {
            cache.put(request, networkResponse.clone());
        }
        return networkResponse;
    });
    
    // Return cached version immediately if available
    return cachedResponse || fetchPromise;
}

// Message handling for cache management
self.addEventListener('message', (event) => {
    if (event.data.type === 'SKIP_WAITING') {
        self.skipWaiting();
    }
    
    if (event.data.type === 'CLEAR_CACHE') {
        event.waitUntil(
            caches.keys().then(cacheNames => {
                return Promise.all(
                    cacheNames.map(cacheName => caches.delete(cacheName))
                );
            })
        );
    }
});

// Background sync for offline form submissions
self.addEventListener('sync', (event) => {
    if (event.tag === 'sync-forms') {
        event.waitUntil(syncOfflineForms());
    }
});

async function syncOfflineForms() {
    // Get pending form submissions from IndexedDB
    // This would be implemented with actual form data storage
    console.log('[SW] Syncing offline forms');
}