/**
 * Lazy Loading Implementation for Data Tables
 * Provides infinite scroll and dynamic data loading for better performance
 */

class LazyLoader {
    constructor(options) {
        this.tableBody = options.tableBody;
        this.apiUrl = options.apiUrl;
        this.perPage = options.perPage || 25;
        this.currentPage = 1;
        this.isLoading = false;
        this.hasMore = true;
        this.totalCount = 0;
        this.currentCount = 0;
        this.enableInfiniteScroll = options.enableInfiniteScroll !== false; // Default true
        this.searchParams = new URLSearchParams(window.location.search);
        
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
        // Create sentinel element at the bottom of the table
        const sentinel = document.createElement('tr');
        sentinel.id = 'load-more-sentinel';
        sentinel.style.height = '1px';
        this.tableBody.appendChild(sentinel);
        
        // Set up intersection observer
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
    
    createSentinel() {
        // Create sentinel element at the bottom of the table for manual pagination
        const sentinel = document.createElement('tr');
        sentinel.id = 'load-more-sentinel';
        sentinel.style.height = '1px';
        sentinel.style.display = 'none'; // Hide it for manual pagination
        this.tableBody.appendChild(sentinel);
    }
    
    initSearchHandlers() {
        // Debounce search input
        const searchInput = document.querySelector('input[name="q"]');
        if (searchInput) {
            let debounceTimer;
            searchInput.addEventListener('input', (e) => {
                clearTimeout(debounceTimer);
                debounceTimer = setTimeout(() => {
                    this.searchParams.set('q', e.target.value);
                    this.resetAndLoad();
                }, 300);
            });
        }
        
        // Handle filter changes
        const filterSelects = document.querySelectorAll('select[name="priority"]');
        filterSelects.forEach(select => {
            select.addEventListener('change', (e) => {
                if (e.target.value) {
                    this.searchParams.set('priority', e.target.value);
                } else {
                    this.searchParams.delete('priority');
                }
                this.resetAndLoad();
            });
        });
        
        // Handle pipeline stage filter
        const pipelineStageSelect = document.querySelector('select[name="pipeline_stage"]');
        if (pipelineStageSelect) {
            pipelineStageSelect.addEventListener('change', (e) => {
                if (e.target.value) {
                    this.searchParams.set('pipeline_stage', e.target.value);
                } else {
                    this.searchParams.delete('pipeline_stage');
                }
                this.resetAndLoad();
            });
        }
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
            
            // Render new rows
            this.renderRows(data.results);
            
            // Update pagination state
            this.currentPage++;
            this.hasMore = data.has_next;
            this.totalCount = data.total || 0;
            
            // Calculate current count more reliably
            this.updateCurrentCount();
            
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
        
        items.forEach(item => {
            const row = this.createRow(item);
            fragment.appendChild(row);
        });
        
        // Insert before the sentinel
        const sentinel = document.getElementById('load-more-sentinel');
        this.tableBody.insertBefore(fragment, sentinel);
        
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
        // Clear existing rows (except header and sentinel)
        const rows = this.tableBody.querySelectorAll('tr:not(#load-more-sentinel)');
        rows.forEach(row => row.remove());
        
        // Reset pagination
        this.currentPage = 1;
        this.hasMore = true;
        this.totalCount = 0;
        this.currentCount = 0;
        
        // Load first page
        this.loadMore();
    }
    
    showLoadingIndicator() {
        if (!this.loadingIndicator.parentNode) {
            const sentinel = document.getElementById('load-more-sentinel');
            this.tableBody.insertBefore(this.loadingIndicator, sentinel);
        }
        this.loadingIndicator.style.display = '';
    }
    
    hideLoadingIndicator() {
        this.loadingIndicator.style.display = 'none';
    }
    
    showError(message) {
        const errorRow = document.createElement('tr');
        errorRow.innerHTML = `
            <td colspan="7" class="text-center text-danger py-4">
                <i class="fas fa-exclamation-triangle me-2"></i>${message}
            </td>
        `;
        
        const sentinel = document.getElementById('load-more-sentinel');
        this.tableBody.insertBefore(errorRow, sentinel);
        
        // Remove error after 5 seconds
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
        // Count all table rows except system rows (sentinel and loading indicator)
        const allRows = this.tableBody.querySelectorAll('tr');
        let dataRows = 0;
        
        allRows.forEach(row => {
            if (row.id !== 'load-more-sentinel' && row.id !== 'loading-indicator') {
                dataRows++;
            }
        });
        
        this.currentCount = dataRows;
    }
    
    updatePaginationDisplay() {
        // Update pagination counts in the UI
        const currentCountSpan = document.getElementById('current-count');
        const totalCountSpan = document.getElementById('total-count');
        
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
}

// Export for use in templates
window.LazyLoader = LazyLoader;