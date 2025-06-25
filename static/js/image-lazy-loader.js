/**
 * Image Lazy Loading Implementation
 * Loads images only when they're about to enter the viewport
 */

class ImageLazyLoader {
    constructor(options = {}) {
        this.imageSelector = options.imageSelector || 'img[data-lazy]';
        this.rootMargin = options.rootMargin || '50px';
        this.threshold = options.threshold || 0.01;
        this.loadedClass = options.loadedClass || 'lazy-loaded';
        this.loadingClass = options.loadingClass || 'lazy-loading';
        this.errorClass = options.errorClass || 'lazy-error';
        
        this.images = [];
        this.imageObserver = null;
        
        this.init();
    }
    
    init() {
        // Check if IntersectionObserver is supported
        if (!('IntersectionObserver' in window)) {
            // Fallback: load all images immediately
            this.loadAllImages();
            return;
        }
        
        // Set up the intersection observer
        this.setupObserver();
        
        // Find and observe all lazy images
        this.observeImages();
        
        // Handle dynamically added images
        this.setupMutationObserver();
    }
    
    setupObserver() {
        const observerOptions = {
            root: null,
            rootMargin: this.rootMargin,
            threshold: this.threshold
        };
        
        this.imageObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    this.loadImage(entry.target);
                }
            });
        }, observerOptions);
    }
    
    observeImages() {
        // Find all images with lazy loading attribute
        this.images = document.querySelectorAll(this.imageSelector);
        
        this.images.forEach(img => {
            // Add loading placeholder
            this.addPlaceholder(img);
            
            // Observe the image
            this.imageObserver.observe(img);
        });
    }
    
    loadImage(img) {
        // Get the actual image source
        const src = img.dataset.lazy;
        const srcset = img.dataset.lazySrcset;
        
        if (!src) return;
        
        // Add loading class
        img.classList.add(this.loadingClass);
        
        // Create a new image to preload
        const tempImg = new Image();
        
        // Handle successful load
        tempImg.onload = () => {
            // Set the actual source
            img.src = src;
            if (srcset) {
                img.srcset = srcset;
            }
            
            // Remove data attributes
            delete img.dataset.lazy;
            delete img.dataset.lazySrcset;
            
            // Update classes
            img.classList.remove(this.loadingClass);
            img.classList.add(this.loadedClass);
            
            // Stop observing this image
            this.imageObserver.unobserve(img);
            
            // Trigger custom event
            this.triggerEvent(img, 'lazyloaded');
        };
        
        // Handle load error
        tempImg.onerror = () => {
            img.classList.remove(this.loadingClass);
            img.classList.add(this.errorClass);
            
            // Set a fallback image if available
            if (img.dataset.lazyError) {
                img.src = img.dataset.lazyError;
            }
            
            // Stop observing this image
            this.imageObserver.unobserve(img);
            
            // Trigger custom event
            this.triggerEvent(img, 'lazyerror');
        };
        
        // Start loading
        tempImg.src = src;
    }
    
    addPlaceholder(img) {
        // If no placeholder is set, create a simple one
        if (!img.src && !img.dataset.lazyPlaceholder) {
            // Calculate aspect ratio if dimensions are known
            const width = img.getAttribute('width');
            const height = img.getAttribute('height');
            
            if (width && height) {
                const aspectRatio = (height / width) * 100;
                img.style.paddingBottom = `${aspectRatio}%`;
                img.style.height = '0';
                img.style.backgroundColor = '#f0f0f0';
            } else {
                // Default placeholder style
                img.style.minHeight = '200px';
                img.style.backgroundColor = '#f0f0f0';
            }
        } else if (img.dataset.lazyPlaceholder) {
            // Use custom placeholder
            img.src = img.dataset.lazyPlaceholder;
        }
    }
    
    setupMutationObserver() {
        // Watch for new images added to the DOM
        const mutationObserver = new MutationObserver((mutations) => {
            mutations.forEach(mutation => {
                mutation.addedNodes.forEach(node => {
                    if (node.nodeType === 1) { // Element node
                        // Check if it's a lazy image
                        if (node.matches && node.matches(this.imageSelector)) {
                            this.addPlaceholder(node);
                            this.imageObserver.observe(node);
                        }
                        
                        // Check for lazy images in descendants
                        const lazyImages = node.querySelectorAll ? 
                            node.querySelectorAll(this.imageSelector) : [];
                        lazyImages.forEach(img => {
                            this.addPlaceholder(img);
                            this.imageObserver.observe(img);
                        });
                    }
                });
            });
        });
        
        mutationObserver.observe(document.body, {
            childList: true,
            subtree: true
        });
    }
    
    loadAllImages() {
        // Fallback for browsers without IntersectionObserver
        const images = document.querySelectorAll(this.imageSelector);
        images.forEach(img => {
            const src = img.dataset.lazy;
            if (src) {
                img.src = src;
                img.classList.add(this.loadedClass);
            }
        });
    }
    
    triggerEvent(element, eventName) {
        const event = new CustomEvent(eventName, {
            detail: { element },
            bubbles: true,
            cancelable: true
        });
        element.dispatchEvent(event);
    }
    
    // Public method to manually load an image
    forceLoad(img) {
        if (img.dataset.lazy) {
            this.loadImage(img);
        }
    }
    
    // Public method to refresh observations
    refresh() {
        this.observeImages();
    }
}

// Auto-initialize on DOM ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.imageLazyLoader = new ImageLazyLoader();
    });
} else {
    window.imageLazyLoader = new ImageLazyLoader();
}

// Helper function to convert existing images to lazy loading
window.convertToLazyImage = function(img, options = {}) {
    if (!img.dataset.lazy && img.src) {
        // Store original source
        img.dataset.lazy = img.src;
        
        // Set placeholder
        if (options.placeholder) {
            img.src = options.placeholder;
        } else {
            img.removeAttribute('src');
        }
        
        // Refresh the lazy loader
        if (window.imageLazyLoader) {
            window.imageLazyLoader.refresh();
        }
    }
};