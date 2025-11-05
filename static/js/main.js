// UMSC Sacco Management System - Main JavaScript

// Sidebar Toggle Functionality
function toggleSidebarCollapse() {
    const sidebar = document.querySelector('.sidebar');
    const mainContent = document.querySelector('.main-content');
    const navbar = document.querySelector('.navbar');
    const collapseIcon = document.getElementById('collapse-icon');
    
    if (sidebar.classList.contains('collapsed')) {
        sidebar.classList.remove('collapsed');
        collapseIcon.classList.remove('bx-chevron-right');
        collapseIcon.classList.add('bx-chevron-left');
    } else {
        sidebar.classList.add('collapsed');
        collapseIcon.classList.remove('bx-chevron-left');
        collapseIcon.classList.add('bx-chevron-right');
    }
}

// Mobile Sidebar Toggle
function toggleSidebar() {
    const sidebar = document.querySelector('.sidebar');
    sidebar.classList.toggle('show');
}

// Close mobile sidebar when clicking outside
document.addEventListener('click', function(event) {
    const sidebar = document.querySelector('.sidebar');
    const sidebarToggle = document.querySelector('.sidebar-toggle');
    
    if (window.innerWidth <= 768) {
        if (!sidebar.contains(event.target) && !sidebarToggle.contains(event.target)) {
            sidebar.classList.remove('show');
        }
    }
});

// DataTables Mobile Enhancement
function enhanceDataTablesMobile() {
    if (window.innerWidth <= 768) {
        // Hide default DataTables controls
        $('.dataTables_wrapper .dataTables_length').hide();
        $('.dataTables_wrapper .dataTables_filter').hide();
        $('.dataTables_wrapper .dataTables_info').hide();
        $('.dataTables_wrapper .dataTables_paginate').hide();
        
        // Add mobile controls if they don't exist
        if ($('.mobile-dt-controls').length === 0) {
            $('.dataTables_wrapper').before(`
                <div class="mobile-dt-controls">
                    <div class="d-flex gap-2">
                        <button class="btn btn-sm btn-outline-primary" onclick="refreshTable()">
                            <i class='bx bx-refresh'></i> Refresh
                        </button>
                        <button class="btn btn-sm btn-outline-secondary" onclick="exportTable()">
                            <i class='bx bx-download'></i> Export
                        </button>
                    </div>
                    <div class="table-info">
                        <small class="text-muted">Swipe to see more columns</small>
                    </div>
                </div>
            `);
        }
        
        // Add mobile pagination if it doesn't exist
        if ($('.mobile-pagination').length === 0) {
            $('.dataTables_wrapper').after(`
                <div class="mobile-pagination">
                    <button class="btn btn-sm btn-outline-primary" onclick="previousPage()">
                        <i class='bx bx-chevron-left'></i>
                    </button>
                    <span class="page-info">Page 1 of 1</span>
                    <button class="btn btn-sm btn-outline-primary" onclick="nextPage()">
                        <i class='bx bx-chevron-right'></i>
                    </button>
                </div>
            `);
        }
    } else {
        // Show default controls on desktop
        $('.dataTables_wrapper .dataTables_length').show();
        $('.dataTables_wrapper .dataTables_filter').show();
        $('.dataTables_wrapper .dataTables_info').show();
        $('.dataTables_wrapper .dataTables_paginate').show();
        
        // Remove mobile controls
        $('.mobile-dt-controls').remove();
        $('.mobile-pagination').remove();
    }
}

// Mobile DataTable Functions
function refreshTable() {
    if (typeof table !== 'undefined') {
        table.ajax.reload();
    }
}

function exportTable() {
    if (typeof table !== 'undefined') {
        table.button('.buttons-excel').trigger();
    }
}

function previousPage() {
    if (typeof table !== 'undefined') {
        table.page('previous').draw('page');
    }
}

function nextPage() {
    if (typeof table !== 'undefined') {
        table.page('next').draw('page');
    }
}

// System Admin Dashboard Functions
function viewSaccoDetails(saccoId) {
    console.log('Viewing Sacco details for ID:', saccoId);
    // Implement view Sacco details functionality
}

function editSacco(saccoId) {
    console.log('Editing Sacco with ID:', saccoId);
    // Implement edit Sacco functionality
}

function manageUsers(saccoId) {
    console.log('Managing users for Sacco ID:', saccoId);
    // Implement manage users functionality
}

function generateReport(saccoId) {
    console.log('Generating report for Sacco ID:', saccoId);
    // Implement generate report functionality
}

function generateSystemReport() {
    console.log('Generating system-wide report');
    // Implement system-wide report generation
}

function viewSystemAnalytics() {
    console.log('Viewing system analytics');
    // Implement analytics dashboard
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', function() {
    // Initialize DataTables mobile enhancement
    setTimeout(enhanceDataTablesMobile, 500);
    
    // Initialize any other components
    initializeComponents();
});

// Initialize components
function initializeComponents() {
    // Add any initialization code here
    console.log('UMSC Sacco Management System initialized');
}

// Run on window resize
window.addEventListener('resize', function() {
    setTimeout(enhanceDataTablesMobile, 100);
});

