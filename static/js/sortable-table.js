/**
 * Sortable Table JavaScript
 * Makes HTML tables sortable by clicking column headers
 * Supports text, numbers, dates, and priority/status badges
 */

class SortableTable {
    constructor(tableSelector, options = {}) {
        this.table = document.querySelector(tableSelector);
        if (!this.table) {
            console.warn(`Table not found: ${tableSelector}`);
            return;
        }
        
        this.tbody = this.table.querySelector('tbody');
        this.headers = this.table.querySelectorAll('thead th[data-sortable]');
        this.currentSort = { column: null, direction: 'asc' };
        
        // Default options
        this.options = {
            ignoredColumns: [0], // Usually checkbox column
            ...options
        };
        
        this.init();
    }
    
    init() {
        this.headers.forEach((header, index) => {
            if (!this.options.ignoredColumns.includes(index)) {
                header.style.cursor = 'pointer';
                header.style.userSelect = 'none';
                header.addEventListener('click', () => this.sortByColumn(index));
                
                // Add sort indicator container
                if (!header.querySelector('.sort-indicator')) {
                    const indicator = document.createElement('span');
                    indicator.className = 'sort-indicator ms-1';
                    indicator.innerHTML = '<i class="fas fa-sort text-muted"></i>';
                    header.appendChild(indicator);
                }
            }
        });
    }
    
    sortByColumn(columnIndex) {
        const header = this.headers[columnIndex];
        const dataType = header.dataset.sortable;
        
        // Determine sort direction
        if (this.currentSort.column === columnIndex) {
            this.currentSort.direction = this.currentSort.direction === 'asc' ? 'desc' : 'asc';
        } else {
            this.currentSort.direction = 'asc';
        }
        this.currentSort.column = columnIndex;
        
        // Get all rows
        const rows = Array.from(this.tbody.querySelectorAll('tr'));
        
        // Sort rows
        rows.sort((a, b) => {
            const aCell = a.cells[columnIndex];
            const bCell = b.cells[columnIndex];
            
            let aValue = this.getCellValue(aCell, dataType);
            let bValue = this.getCellValue(bCell, dataType);
            
            // Handle null/undefined values
            if (aValue === null || aValue === undefined) return 1;
            if (bValue === null || bValue === undefined) return -1;
            
            let comparison = 0;
            
            switch (dataType) {
                case 'number':
                case 'priority':
                case 'status':
                    comparison = aValue - bValue;
                    break;
                case 'date':
                    comparison = new Date(aValue) - new Date(bValue);
                    break;
                case 'text':
                default:
                    comparison = aValue.localeCompare(bValue, undefined, { 
                        numeric: true, 
                        sensitivity: 'base' 
                    });
                    break;
            }
            
            return this.currentSort.direction === 'asc' ? comparison : -comparison;
        });
        
        // Re-append sorted rows
        rows.forEach(row => this.tbody.appendChild(row));
        
        // Update sort indicators
        this.updateSortIndicators();
    }
    
    getCellValue(cell, dataType) {
        switch (dataType) {
            case 'number':
                return parseFloat(cell.textContent.replace(/[^\d.-]/g, '')) || 0;
                
            case 'priority':
                const priorityText = cell.textContent.toLowerCase().trim();
                const priorityMap = { 'high': 3, 'medium': 2, 'low': 1 };
                return priorityMap[priorityText] || 0;
                
            case 'status':
                const statusText = cell.textContent.toLowerCase().trim();
                const statusMap = { 
                    'completed': 3, 
                    'in progress': 2, 
                    'in_progress': 2,
                    'pending': 1,
                    'overdue': 0
                };
                return statusMap[statusText] || 0;
                
            case 'date':
                // Try to extract date from text content or data attributes
                const dateText = cell.textContent.trim();
                const dateAttr = cell.dataset.date || cell.querySelector('[data-date]')?.dataset.date;
                return dateAttr || dateText;
                
            case 'badge':
                // For cells with badges, get the badge text
                const badge = cell.querySelector('.badge');
                return badge ? badge.textContent.toLowerCase().trim() : cell.textContent.toLowerCase().trim();
                
            case 'text':
            default:
                // Get text content, excluding any icons or extra elements
                let text = cell.textContent.trim();
                // Remove email/phone icons if present
                text = text.replace(/^\s*[\u{1F4E7}\u{1F4DE}\u{260E}]?\s*/u, '');
                return text.toLowerCase();
        }
    }
    
    updateSortIndicators() {
        // Reset all indicators
        this.headers.forEach((header, index) => {
            const indicator = header.querySelector('.sort-indicator i');
            if (indicator) {
                if (index === this.currentSort.column) {
                    indicator.className = this.currentSort.direction === 'asc' 
                        ? 'fas fa-sort-up text-primary' 
                        : 'fas fa-sort-down text-primary';
                } else {
                    indicator.className = 'fas fa-sort text-muted';
                }
            }
        });
    }
    
    // Public method to reset sorting
    resetSort() {
        this.currentSort = { column: null, direction: 'asc' };
        this.updateSortIndicators();
    }
}

// Auto-initialize for tables with data-sortable attribute
document.addEventListener('DOMContentLoaded', function() {
    const sortableTables = document.querySelectorAll('table[data-sortable-table]');
    sortableTables.forEach(table => {
        new SortableTable(`#${table.id}` || table, {
            ignoredColumns: [0] // Assume first column is checkbox
        });
    });
});

// Export for manual initialization
window.SortableTable = SortableTable;