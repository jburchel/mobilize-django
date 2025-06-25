/**
 * Service Worker Registration for Mobilize CRM
 */

// Check if service workers are supported
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        registerServiceWorker();
    });
}

async function registerServiceWorker() {
    try {
        const registration = await navigator.serviceWorker.register('/static/sw.js', {
            scope: '/'
        });
        
        console.log('Service Worker registered successfully:', registration);
        
        // Handle updates
        registration.addEventListener('updatefound', () => {
            const newWorker = registration.installing;
            
            newWorker.addEventListener('statechange', () => {
                if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                    // New service worker available
                    showUpdateNotification();
                }
            });
        });
        
        // Check for updates periodically
        setInterval(() => {
            registration.update();
        }, 60 * 60 * 1000); // Check every hour
        
    } catch (error) {
        console.error('Service Worker registration failed:', error);
    }
}

function showUpdateNotification() {
    // Create update notification
    const notification = document.createElement('div');
    notification.className = 'sw-update-notification';
    notification.innerHTML = `
        <div class="alert alert-info alert-dismissible fade show position-fixed bottom-0 end-0 m-3" role="alert" style="z-index: 9999;">
            <strong>Update Available!</strong> A new version of the app is available.
            <button type="button" class="btn btn-sm btn-primary ms-2" onclick="updateServiceWorker()">Update Now</button>
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
    `;
    
    document.body.appendChild(notification);
}

window.updateServiceWorker = function() {
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.ready.then(registration => {
            registration.waiting.postMessage({ type: 'SKIP_WAITING' });
        });
        
        // Reload once the new service worker takes control
        navigator.serviceWorker.addEventListener('controllerchange', () => {
            window.location.reload();
        });
    }
};

// Cache management utilities
window.clearAppCache = async function() {
    if ('serviceWorker' in navigator) {
        const registration = await navigator.serviceWorker.ready;
        registration.active.postMessage({ type: 'CLEAR_CACHE' });
        console.log('Cache cleared');
    }
};

// Offline detection
window.addEventListener('online', () => {
    document.body.classList.remove('offline');
    showNotification('You are back online!', 'success');
});

window.addEventListener('offline', () => {
    document.body.classList.add('offline');
    showNotification('You are currently offline. Some features may be limited.', 'warning');
});

function showNotification(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed top-0 end-0 m-3`;
    alertDiv.style.zIndex = '9999';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    document.body.appendChild(alertDiv);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        alertDiv.remove();
    }, 5000);
}