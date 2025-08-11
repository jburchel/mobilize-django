/**
 * Lazy Loading Implementation for Data Tables
 * Provides infinite scroll and dynamic data loading for better performance
 */

 class LazyLoader {
    constructor(options) {
        this.tableBody = options.tableBody;
        this.cardContainer = options.cardContainer || null;
        this.apiUrl = options.apiUrl;
        this.perPage = options.perPage || 25;
        this.currentPage = 1;
        this.isLoading = false;
        this.hasMore = true;
        this.totalCount = 0;
        this.currentCount = 0;
        this.enableInfiniteScroll = options.enableInfiniteScroll !== false; // Default true
        this.persistViewKey = options.persistViewKey || null;
        const defaultRenderMode = options.renderMode || (window.matchMedia && window.matchMedia('(max-width: 767.98px)').matches ? 'card' : 'table');
        this.renderMode = this.loadPersistedRenderMode(defaultRenderMode);
        this.searchParams = new URLSearchParams(window.location.search);
        
        // Apply initial filters if provided
        if (options.filters) {
            Object.keys(options.filters).forEach(key => {
                if (options.filters[key]) {
                    this.searchParams.set(key, options.filters[key]);
                } else {
                    this.searchParams.delete(key);
                }
            });
        }
        
        // Create loading indicator
        this.loadingIndicator = this.createLoadingIndicator();
        
        // Initialize intersection observer for infinite scroll (only if enabled)
        if (this.enableInfiniteScroll) {
            this.initIntersectionObserver();
        } else {
            // Create sentinel even for manual pagination to ensure consistent DOM structure
            this.createSentinel();
        }
        
        // Initialize search/filter handlers
        this.initSearchHandlers();
    }
    
    createLoadingIndicator() {
        if (this.renderMode === 'card') {
            const indicator = document.createElement('div');
            indicator.id = 'loading-indicator';
            indicator.className = 'text-center py-3';
            indicator.innerHTML = `
                <div class="spinner-border spinner-border-sm text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <span class="ms-2">Loading more...</span>
            `;
            indicator.style.display = 'none';
            return indicator;
        }
        const indicator = document.createElement('tr');
        indicator.id = 'loading-indicator';
        indicator.innerHTML = `
            <td colspan="7" class="text-center py-4">
                <div class="spinner-border spinner-border-sm text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <span class="ms-2">Loading more...</span>
            </td>
        `;
        indicator.style.display = 'none';
        return indicator;
    }
    
    initIntersectionObserver() {
        // Create sentinel element at the bottom
        const sentinel = this.createSentinel();
        // Only set up observer if infinite scroll is enabled
        if (this.enableInfiniteScroll) {
            const observerOptions = {
                root: null,
                rootMargin: '100px',
                threshold: 0.1
            };
            this.observer = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting && !this.isLoading && this.hasMore) {
                        this.loadMore();
                    }
                });
            }, observerOptions);
            this.observer.observe(sentinel);
        }
    }
    
    createSentinel() {
        // Remove existing sentinel if any
        const existing = (this.renderMode === 'card' ? (this.cardContainer && this.cardContainer.querySelector('#load-more-sentinel')) : (this.tableBody && this.tableBody.querySelector('#load-more-sentinel')));
        if (existing && existing.parentNode) existing.parentNode.removeChild(existing);
        let sentinel;
        if (this.renderMode === 'card') {
            sentinel = document.createElement('div');
            sentinel.id = 'load-more-sentinel';
            sentinel.style.height = '1px';
            sentinel.style.display = this.enableInfiniteScroll ? '' : 'none';
            if (this.cardContainer) this.cardContainer.appendChild(sentinel);
        } else {
            sentinel = document.createElement('tr');
            sentinel.id = 'load-more-sentinel';
            sentinel.style.height = '1px';
            sentinel.style.display = this.enableInfiniteScroll ? '' : 'none';
            if (this.tableBody) this.tableBody.appendChild(sentinel);
        }
        return sentinel;
    }
    
    initSearchHandlers() {
        // Note: Search handlers are now managed in the template
        // This method is kept for compatibility but does nothing
        // to avoid duplicate event listeners
    }
    
    async loadMore() {
        if (this.isLoading || !this.hasMore) return;
        
        this.isLoading = true;
        this.showLoadingIndicator();
        
        try {
            // Build API URL with current search params
            const url = new URL(this.apiUrl, window.location.origin);
            url.searchParams.set('page', this.currentPage);
            url.searchParams.set('per_page', this.perPage);
            
            // Add search/filter params
            for (const [key, value] of this.searchParams) {
                if (key !== 'page') {
                    url.searchParams.set(key, value);
                }
            }
            
            const response = await fetch(url, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'Accept': 'application/json'
                }
            });
            
            if (!response.ok) {
                throw new Error('Failed to load data');
            }
            
            const data = await response.json();
            
            // Render new items
            this.renderRows(data.results);
            
            // Update pagination state
            this.currentPage++;
            this.hasMore = data.has_next;
            this.totalCount = data.total || 0;
            console.log('LazyLoader: Received total count:', this.totalCount);
            console.log('LazyLoader: Current count after renderRows:', this.currentCount);
            
            // Update pagination display
            this.updatePaginationDisplay();
            
            // Update URL without page reload
            this.updateUrl();
            
            // Trigger custom event for pagination updates
            window.dispatchEvent(new CustomEvent('lazyLoaderUpdate', {
                detail: {
                    total: this.totalCount,
                    loaded: this.currentCount,
                    hasMore: this.hasMore,
                    currentPage: this.currentPage
                }
            }));
            
        } catch (error) {
            console.error('Error loading data:', error);
            this.showError('Failed to load more items. Please try again.');
        } finally {
            this.isLoading = false;
            this.hideLoadingIndicator();
        }
    }
    
    renderRows(items) {
        const fragment = document.createDocumentFragment();
        if (this.renderMode === 'card') {
            items.forEach(item => {
                const card = this.createCard(item);
                fragment.appendChild(card);
            });
            const sentinel = this.cardContainer && this.cardContainer.querySelector('#load-more-sentinel');
            if (this.cardContainer && sentinel) {
                this.cardContainer.insertBefore(fragment, sentinel);
            }
        } else {
            items.forEach(item => {
                const row = this.createRow(item);
                fragment.appendChild(row);
            });
            const sentinel = this.tableBody && this.tableBody.querySelector('#load-more-sentinel');
            if (this.tableBody && sentinel) {
                this.tableBody.insertBefore(fragment, sentinel);
            }
        }
        
        // Update current count based on items actually rendered
        this.currentCount += items.length;
        
        // Update bulk selection handlers
        this.updateBulkSelectionHandlers();
    }
    
    createRow(item) {
        const row = document.createElement('tr');
        row.innerHTML = this.getRowTemplate(item);
        return row;
    }
    
    getRowTemplate(item) {
        // This should be customized based on the specific table type
        // For now, return a generic template that can be overridden
        return `
            <td>
                <input type="checkbox" name="contact_ids" value="${item.id}" class="form-check-input contact-checkbox">
            </td>
            <td>
                <a href="${item.detail_url}">${item.name}</a>
            </td>
            <td>${item.email || '-'}</td>
            <td>${item.phone || '-'}</td>
            <td>${this.getPriorityBadge(item.priority)}</td>
            <td>${this.getPipelineBadge(item.pipeline_stage)}</td>
            <td>${this.getActionButtons(item)}</td>
        `;
    }

    createCard(item) {
        const cardWrapper = document.createElement('div');
        cardWrapper.className = 'col-12 col-md-6 col-lg-4';
        cardWrapper.innerHTML = this.getCardTemplate(item);
        return cardWrapper;
    }

    getCardTemplate(item) {
        // Generic fallback card template; individual pages should override
        return `
            <div class="card list-card">
                <div class="card-body">
                    <div class="d-flex justify-content-between align-items-start">
                        <div>
                            <h6 class="mb-1"><a href="${item.detail_url}">${item.name || 'Item'}</a></h6>
                            ${item.email ? `<div class="small text-muted">${item.email}</div>` : ''}
                            ${item.phone ? `<div class="small text-muted">${item.phone}</div>` : ''}
                        </div>
                        <div>
                            ${this.getPriorityBadge(item.priority || item.priority_display || '')}
                        </div>
                    </div>
                    <div class="mt-2 d-flex justify-content-between align-items-center">
                        <div>${this.getPipelineBadge(item.pipeline_stage)}</div>
                        <div>${this.getActionButtons(item)}</div>
                    </div>
                </div>
            </div>
        `;
    }
    
    getPriorityBadge(priority) {
        const classes = {
            'high': 'bg-danger',
            'medium': 'bg-warning',
            'low': 'bg-success'
        };
        return `<span class="badge ${classes[priority] || 'bg-secondary'}">${priority || '-'}</span>`;
    }
    
    getPipelineBadge(stage) {
        const stages = {
            'promotion': { class: 'bg-primary', label: 'Promotion' },
            'information': { class: 'bg-info text-dark', label: 'Information' },
            'invitation': { class: 'bg-warning text-dark', label: 'Invitation' },
            'confirmation': { class: 'bg-success', label: 'Confirmation' },
            'automation': { class: 'bg-secondary', label: 'Automation' },
            'en42': { class: 'bg-dark', label: 'EN42' }
        };
        
        const stageInfo = stages[stage];
        if (stageInfo) {
            return `<span class="badge ${stageInfo.class}">${stageInfo.label}</span>`;
        }
        return '<span class="text-muted">-</span>';
    }
    
    getActionButtons(item) {
        return `
            <div class="btn-group btn-group-sm">
                <a href="${item.detail_url}" class="btn btn-outline-primary btn-sm">
                    <i class="fas fa-eye"></i>
                </a>
                <a href="${item.edit_url}" class="btn btn-outline-secondary btn-sm">
                    <i class="fas fa-edit"></i>
                </a>
                <a href="${item.delete_url}" class="btn btn-outline-danger btn-sm">
                    <i class="fas fa-trash"></i>
                </a>
            </div>
        `;
    }
    
    resetAndLoad() {
        // Clear existing items (except header and sentinel)
        if (this.renderMode === 'card') {
            if (this.cardContainer) {
                const cards = this.cardContainer.querySelectorAll('.col-12');
                cards.forEach(card => card.remove());
            }
        } else if (this.tableBody) {
            const rows = this.tableBody.querySelectorAll('tr:not(#load-more-sentinel)');
            rows.forEach(row => row.remove());
        }
        // Reset pagination
        this.currentPage = 1;
        this.hasMore = true;
        this.totalCount = 0;
        this.currentCount = 0;
        // Load first page
        this.loadMore();
    }
    
    showLoadingIndicator() {
        // Ensure indicator matches current mode
        if (this.loadingIndicator && this.loadingIndicator.tagName) {
            const isCardIndicator = this.renderMode === 'card' && this.loadingIndicator.tagName.toLowerCase() !== 'tr';
            const isTableIndicator = this.renderMode === 'table' && this.loadingIndicator.tagName.toLowerCase() === 'tr';
            if (!isCardIndicator && !isTableIndicator) {
                this.loadingIndicator.remove();
                this.loadingIndicator = this.createLoadingIndicator();
            }
        }
        if (!this.loadingIndicator.parentNode) {
            const sentinel = (this.renderMode === 'card')
                ? (this.cardContainer && this.cardContainer.querySelector('#load-more-sentinel'))
                : (this.tableBody && this.tableBody.querySelector('#load-more-sentinel'));
            if (this.renderMode === 'card' && this.cardContainer && sentinel) {
                this.cardContainer.insertBefore(this.loadingIndicator, sentinel);
            } else if (this.tableBody && sentinel) {
                this.tableBody.insertBefore(this.loadingIndicator, sentinel);
            }
        }
        this.loadingIndicator.style.display = '';
    }
    
    hideLoadingIndicator() {
        this.loadingIndicator.style.display = 'none';
    }
    
    showError(message) {
        if (this.renderMode === 'card') {
            const errorDiv = document.createElement('div');
            errorDiv.className = 'text-center text-danger py-3';
            errorDiv.innerHTML = `<i class="fas fa-exclamation-triangle me-2"></i>${message}`;
            const sentinel = this.cardContainer && this.cardContainer.querySelector('#load-more-sentinel');
            if (this.cardContainer && sentinel) this.cardContainer.insertBefore(errorDiv, sentinel);
            setTimeout(() => errorDiv.remove(), 5000);
            return;
        }
        const errorRow = document.createElement('tr');
        errorRow.innerHTML = `
            <td colspan="7" class="text-center text-danger py-4">
                <i class="fas fa-exclamation-triangle me-2"></i>${message}
            </td>
        `;
        const sentinel = this.tableBody && this.tableBody.querySelector('#load-more-sentinel');
        if (this.tableBody && sentinel) this.tableBody.insertBefore(errorRow, sentinel);
        setTimeout(() => errorRow.remove(), 5000);
    }
    
    updateUrl() {
        const url = new URL(window.location);
        url.searchParams.set('page', this.currentPage - 1);
        window.history.replaceState({}, '', url);
    }
    
    updateBulkSelectionHandlers() {
        // Re-initialize bulk selection handlers for new checkboxes
        const newCheckboxes = this.tableBody.querySelectorAll('.contact-checkbox:not([data-initialized])');
        newCheckboxes.forEach(checkbox => {
            checkbox.setAttribute('data-initialized', 'true');
            checkbox.addEventListener('change', () => {
                if (window.updateBulkOperations) {
                    window.updateBulkOperations();
                }
            });
        });
    }
    
    updateFilters(filters) {
        // Update search parameters with new filter values
        Object.keys(filters).forEach(key => {
            if (filters[key]) {
                this.searchParams.set(key, filters[key]);
            } else {
                this.searchParams.delete(key);
            }
        });
        
        // Reset pagination and reload data with new filters
        this.resetAndLoad();
    }
    
    updateCurrentCount() {
        // This method is deprecated - count is now updated incrementally in renderRows()
        // Keeping for backwards compatibility but now does nothing
        // The count is maintained by tracking items rendered, not counting DOM elements
    }
    
    updatePaginationDisplay() {
        // Update pagination counts in the UI
        const currentCountSpan = document.getElementById('current-count');
        const totalCountSpan = document.getElementById('total-count');
        
        console.log('LazyLoader: Updating pagination display - current:', this.currentCount, 'total:', this.totalCount);
        
        if (currentCountSpan) {
            currentCountSpan.textContent = this.currentCount;
        }
        
        if (totalCountSpan) {
            totalCountSpan.textContent = this.totalCount;
        }
        
        // Update load more button visibility (only if infinite scroll is disabled)
        if (!this.enableInfiniteScroll) {
            const loadMoreBtn = document.getElementById('load-more-btn');
            const endReachedSpan = document.getElementById('end-reached');
            
            if (loadMoreBtn && endReachedSpan) {
                if (this.hasMore && this.currentCount > 0) {
                    loadMoreBtn.style.display = 'inline-block';
                    endReachedSpan.style.display = 'none';
                } else {
                    loadMoreBtn.style.display = 'none';
                    if (this.currentCount >= this.totalCount && this.totalCount > 0) {
                        endReachedSpan.style.display = 'inline-block';
                    }
                }
            }
        }
    }

    setRenderMode(mode) {
        if (mode !== 'table' && mode !== 'card') return;
        if (this.renderMode === mode) return;
        this.renderMode = mode;
        this.persistRenderMode();
        // Recreate sentinel and indicator
        this.createSentinel();
        this.loadingIndicator && this.loadingIndicator.remove();
        this.loadingIndicator = this.createLoadingIndicator();
        // Reset and load into the appropriate container
        this.resetAndLoad();
    }

    loadPersistedRenderMode(defaultMode) {
        try {
            if (!this.persistViewKey) return defaultMode;
            const saved = localStorage.getItem(this.persistViewKey);
            if (saved === 'table' || saved === 'card') return saved;
        } catch (e) {}
        return defaultMode;
    }

    persistRenderMode() {
        try {
            if (this.persistViewKey) localStorage.setItem(this.persistViewKey, this.renderMode);
        } catch (e) {}
    }
}

// Export for use in templates
window.LazyLoader = LazyLoader;