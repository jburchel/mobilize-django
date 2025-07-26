/**
 * Simple Table Sorting
 * Makes HTML tables sortable by clicking column headers
 */

function getCellValue(cell, dataType) {
    switch (dataType) {
        case 'number':
            return parseFloat(cell.textContent.replace(/[^\d.-]/g, '')) || 0;
            
        case 'priority':
            const priorityText = cell.textContent.toLowerCase().trim();
            return priorityText;
            
        case 'status':
            const statusText = cell.textContent.toLowerCase().trim();
            return statusText;
            
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

function sortTable(table, columnIndex, dataType) {
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    
    // Determine current sort direction
    const currentDir = table.dataset.sortDirection || 'asc';
    const currentCol = table.dataset.sortColumn;
    
    let newDirection = 'asc';
    if (currentCol == columnIndex && currentDir === 'asc') {
        newDirection = 'desc';
    }
    
    // Store sort state
    table.dataset.sortDirection = newDirection;
    table.dataset.sortColumn = columnIndex;
    
    // Sort rows
    rows.sort((a, b) => {
        const aCell = a.cells[columnIndex];
        const bCell = b.cells[columnIndex];
        
        let aValue = getCellValue(aCell, dataType);
        let bValue = getCellValue(bCell, dataType);
        
        // Handle null/undefined values
        if (aValue === null || aValue === undefined) return 1;
        if (bValue === null || bValue === undefined) return -1;
        
        let comparison = 0;
        
        switch (dataType) {
            case 'number':
                comparison = aValue - bValue;
                break;
            case 'priority':
                const priorityOrder = { 'high': 3, 'medium': 2, 'low': 1 };
                comparison = (priorityOrder[aValue] || 0) - (priorityOrder[bValue] || 0);
                break;
            case 'status':
                const statusOrder = { 'completed': 4, 'in progress': 3, 'in_progress': 3, 'pending': 2, 'overdue': 1 };
                comparison = (statusOrder[aValue] || 0) - (statusOrder[bValue] || 0);
                break;
            case 'date':
                comparison = new Date(aValue) - new Date(bValue);
                break;
            case 'text':
            case 'badge':
            default:
                comparison = aValue.localeCompare(bValue, undefined, { 
                    numeric: true, 
                    sensitivity: 'base' 
                });
                break;
        }
        
        return newDirection === 'asc' ? comparison : -comparison;
    });
    
    // Re-append sorted rows
    rows.forEach(row => tbody.appendChild(row));
}

function initializeSortableTables() {
    // Find all tables with sortable headers
    const tables = document.querySelectorAll('table[data-sortable-table]');
    
    tables.forEach(table => {
        const headers = table.querySelectorAll('thead th[data-sortable]');
        
        headers.forEach((header, columnIndex) => {
            // Skip if already initialized
            if (header.dataset.sortableInitialized) return;
            
            header.style.cursor = 'pointer';
            header.style.userSelect = 'none';
            header.dataset.sortableInitialized = 'true';
            
            header.addEventListener('click', function() {
                sortTable(table, columnIndex, header.dataset.sortable);
            });
        });
    });
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', initializeSortableTables);

// Re-initialize when new content is loaded (for dynamic tables)
window.reinitializeSortableTables = initializeSortableTables;