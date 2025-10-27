// Sensor Data Section JavaScript Functions
// Complete implementation for sensor data loading, visualization, and management

// Global variables
let sensorChart = null;
let allSensorData = [];
let sensorDataCache = [];
let sensorDataRefreshInterval = null;
let isLoadingSensorData = false;

const SENSOR_REFRESH_INTERVAL = 60000; // 60 seconds
const MOBILE_DATA_LIMIT = 50;

// Check if mobile device
const isMobileDevice = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);

// ==================== DATA LOADING ====================

async function loadSensorData() {
    console.log('loadSensorData() called');
    
    // Prevent multiple simultaneous requests
    if (isLoadingSensorData) {
        console.log('Already loading sensor data, skipping...');
        return;
    }
    
    isLoadingSensorData = true;
    const sensorDataContainer = document.getElementById('sensorDataContainer');
    const loadingSensorData = document.getElementById('loadingSensorData');
    const loadingChart = document.getElementById('loadingChart');
    
    // Check if elements exist before proceeding
    if (!sensorDataContainer) {
        console.error('sensorDataContainer element not found');
        isLoadingSensorData = false;
        return;
    }
    
    try {
        if (loadingSensorData) loadingSensorData.style.display = 'block';
        if (loadingChart) loadingChart.style.display = 'block';
        
        console.log('Fetching sensor data from API...');
        const response = await fetch(`/api/entries/${entryId}/sensor_data`);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const sensorData = await response.json();
        console.log('Loaded sensor data:', sensorData.length, 'readings');
        
        // Store in cache
        sensorDataCache = sensorData;
        allSensorData = sensorData;
        
        // Render will trigger chart view automatically
        renderSensorData(sensorData);
        
    } catch (error) {
        console.error('Error loading sensor data:', error);
        sensorDataContainer.innerHTML = '<p class="text-danger"><i class="fas fa-exclamation-triangle me-2"></i>Error loading sensor data.</p>';
    } finally {
        if (loadingSensorData) loadingSensorData.style.display = 'none';
        if (loadingChart) loadingChart.style.display = 'none';
        isLoadingSensorData = false;
    }
}

function renderSensorData(sensorData) {
    const sensorDataContainer = document.getElementById('sensorDataContainer');
    
    // Store data globally for chart functionality
    allSensorData = sensorData;
    sensorDataCache = sensorData;
    
    console.log('renderSensorData called with', sensorData.length, 'records');
    
    // Manage performance alert
    showPerformanceAlertIfNeeded(sensorData.length);
    
    if (sensorData.length === 0) {
        sensorDataContainer.innerHTML = '<p class="text-muted text-center"><i class="fas fa-chart-line fa-2x mb-2 d-block opacity-50"></i>No sensor data recorded yet.</p>';
        const chartContainer = document.getElementById('sensorChartContainer');
        if (chartContainer) {
            const canvas = chartContainer.querySelector('canvas');
            if (canvas) canvas.style.display = 'none';
            const noDataMsg = chartContainer.querySelector('.no-data-message') || document.createElement('p');
            noDataMsg.className = 'text-muted text-center no-data-message';
            noDataMsg.innerHTML = '<i class="fas fa-chart-line fa-2x mb-2 d-block opacity-50"></i>No sensor data to display';
            chartContainer.appendChild(noDataMsg);
        }
        return;
    }

    // Always render table view for when user switches to it
    renderTableView(sensorData);
    
    // Update chart filters
    updateChartFilters(sensorData);
    
    // Show chart view by default (or if chart view is active)
    const chartViewBtn = document.getElementById('chartView');
    console.log('Chart view button:', chartViewBtn, 'checked:', chartViewBtn?.checked);
    if (!chartViewBtn || chartViewBtn.checked) {
        console.log('Rendering chart view after data load');
        // Use setTimeout to ensure DOM is fully ready and Chart.js is loaded
        setTimeout(() => {
            renderChartView();
        }, 100);
    } else {
        console.log('Skipping chart render - table view is active');
    }
}

function renderTableView(sensorData) {
    const sensorDataContainer = document.getElementById('sensorDataContainer');
    
    // Pagination variables
    const itemsPerPage = 10;
    const totalPages = Math.ceil(sensorData.length / itemsPerPage);
    let currentPage = parseInt(sensorDataContainer.dataset.currentPage || '1');
    
    // Ensure current page is valid
    if (currentPage > totalPages) currentPage = 1;
    if (currentPage < 1) currentPage = 1;
    
    // Calculate pagination slice
    const startIndex = (currentPage - 1) * itemsPerPage;
    const endIndex = Math.min(startIndex + itemsPerPage, sensorData.length);
    const paginatedData = sensorData.slice(startIndex, endIndex);
    
    const tableHtml = `
        <div class="d-flex justify-content-between align-items-center mb-3 flex-wrap gap-2">
            <span class="text-muted small">Showing ${startIndex + 1}-${endIndex} of ${sensorData.length} readings</span>
            ${totalPages > 1 ? `
                <nav aria-label="Sensor data pagination">
                    <ul class="pagination pagination-sm mb-0">
                        <li class="page-item ${currentPage === 1 ? 'disabled' : ''}">
                            <button class="page-link sensor-page-btn" data-page="${currentPage - 1}" ${currentPage === 1 ? 'disabled' : ''}>
                                <i class="fas fa-chevron-left"></i>
                            </button>
                        </li>
                        ${generatePaginationButtons(currentPage, totalPages)}
                        <li class="page-item ${currentPage === totalPages ? 'disabled' : ''}">
                            <button class="page-link sensor-page-btn" data-page="${currentPage + 1}" ${currentPage === totalPages ? 'disabled' : ''}>
                                <i class="fas fa-chevron-right"></i>
                            </button>
                        </li>
                    </ul>
                </nav>
            ` : ''}
        </div>
        <div class="table-responsive">
            <table class="table table-sm table-striped table-hover">
                <thead>
                    <tr>
                        <th>Sensor Type</th>
                        <th>Value</th>
                        <th>Recorded At</th>
                        <th width="100">Actions</th>
                    </tr>
                </thead>
                <tbody>
                    ${paginatedData.map(data => `
                        <tr>
                            <td><span class="badge bg-secondary">${data.sensor_type}</span></td>
                            <td><strong>${data.value}</strong></td>
                            <td><small>${formatSensorTimestamp(data.recorded_at)}</small></td>
                            <td>
                                <button class="btn btn-sm btn-outline-danger delete-sensor-btn" data-sensor-id="${data.id}" title="Delete reading">
                                    <i class="fas fa-trash-alt"></i>
                                </button>
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
    `;
    
    sensorDataContainer.innerHTML = tableHtml;
    sensorDataContainer.dataset.currentPage = currentPage;
    
    // Attach pagination event listeners
    const pageButtons = sensorDataContainer.querySelectorAll('.sensor-page-btn');
    pageButtons.forEach(button => {
        button.addEventListener('click', function() {
            const newPage = parseInt(this.dataset.page);
            sensorDataContainer.dataset.currentPage = newPage;
            renderTableView(sensorData);
        });
    });
    
    attachSensorDataEventListeners();
}

function generatePaginationButtons(currentPage, totalPages) {
    const maxButtons = 5;
    let buttons = '';
    
    if (totalPages <= maxButtons) {
        for (let i = 1; i <= totalPages; i++) {
            buttons += `
                <li class="page-item ${i === currentPage ? 'active' : ''}">
                    <button class="page-link sensor-page-btn" data-page="${i}">${i}</button>
                </li>
            `;
        }
    } else {
        let startPage, endPage;
        if (currentPage <= 3) {
            startPage = 1;
            endPage = maxButtons;
        } else if (currentPage >= totalPages - 2) {
            startPage = totalPages - maxButtons + 1;
            endPage = totalPages;
        } else {
            startPage = currentPage - 2;
            endPage = currentPage + 2;
        }
        
        for (let i = startPage; i <= endPage; i++) {
            buttons += `
                <li class="page-item ${i === currentPage ? 'active' : ''}">
                    <button class="page-link sensor-page-btn" data-page="${i}">${i}</button>
                </li>
            `;
        }
    }
    
    return buttons;
}

function attachSensorDataEventListeners() {
    // Delete sensor data buttons
    document.querySelectorAll('.delete-sensor-btn').forEach(button => {
        button.addEventListener('click', async function() {
            const sensorId = this.getAttribute('data-sensor-id');
            if (confirm('Are you sure you want to delete this sensor reading?')) {
                await deleteSensorData(sensorId);
            }
        });
    });
}

async function deleteSensorData(sensorId) {
    try {
        const response = await fetch(`/api/sensor_data/${sensorId}`, {
            method: 'DELETE'
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Failed to delete sensor data');
        }

        // Reload sensor data
        await loadSensorData();
        
    } catch (error) {
        console.error('Error deleting sensor data:', error);
        alert('Error deleting sensor reading: ' + error.message);
    }
}

// ==================== AUTO-REFRESH ====================

function startSensorDataAutoRefresh() {
    // Clear any existing interval
    if (sensorDataRefreshInterval) {
        clearInterval(sensorDataRefreshInterval);
    }
    
    // Only start auto-refresh if we have sensor data capability
    if (document.getElementById('sensorDataContainer')) {
        console.log('Starting sensor data auto-refresh (every 60 seconds)');
        
        // Update status indicator
        const statusElement = document.getElementById('autoRefreshStatus');
        if (statusElement) {
            statusElement.innerHTML = '<i class="fas fa-sync fa-spin me-1"></i>Auto-refresh: 60s';
        }
        
        sensorDataRefreshInterval = setInterval(async () => {
            try {
                if (statusElement) {
                    statusElement.innerHTML = '<i class="fas fa-sync fa-spin me-1"></i>Refreshing...';
                }
                
                await loadSensorData();
                
                if (statusElement) {
                    statusElement.innerHTML = '<i class="fas fa-sync fa-spin me-1"></i>Auto-refresh: 60s';
                }
            } catch (error) {
                console.error('Error during auto-refresh:', error);
                if (statusElement) {
                    statusElement.innerHTML = '<i class="fas fa-exclamation-triangle me-1"></i>Refresh error';
                }
            }
        }, SENSOR_REFRESH_INTERVAL);
    }
}

function stopSensorDataAutoRefresh() {
    if (sensorDataRefreshInterval) {
        clearInterval(sensorDataRefreshInterval);
        sensorDataRefreshInterval = null;
        console.log('Stopped sensor data auto-refresh');
        
        const statusElement = document.getElementById('autoRefreshStatus');
        if (statusElement) {
            statusElement.innerHTML = '<i class="fas fa-pause me-1"></i>Auto-refresh: Stopped';
        }
    }
}

// ==================== CHART RENDERING ====================

function renderChartView() {
    console.log('renderChartView() called');
    
    // Check if Chart.js is loaded
    if (typeof Chart === 'undefined') {
        console.error('Chart.js is not loaded!');
        return;
    }
    
    const canvas = document.getElementById('sensorChart');
    if (!canvas) {
        console.error('Chart canvas not found');
        return;
    }
    
    console.log('allSensorData:', allSensorData ? allSensorData.length : 'undefined');
    
    // Get filter values
    const chartType = document.getElementById('chartTypeSelect')?.value || 'line';
    const sensorType = document.getElementById('sensorTypeFilter')?.value || 'all';
    const timeRange = document.getElementById('timeRangeFilter')?.value || 'all';
    const dataLimit = document.getElementById('dataLimitFilter')?.value || '';
    
    console.log('Filters:', { chartType, sensorType, timeRange, dataLimit });
    
    // Filter data
    let filteredData = filterSensorData(allSensorData, sensorType, timeRange, dataLimit);
    
    console.log('Filtered data:', filteredData.length, 'records');
    
    // Hide loading message
    const loadingChart = document.getElementById('loadingChart');
    if (loadingChart) loadingChart.style.display = 'none';
    
    if (filteredData.length === 0) {
        destroyChart();
        canvas.style.display = 'none';
        showNoDataMessage();
        return;
    }
    
    canvas.style.display = 'block';
    hideNoDataMessage();
    
    // Prepare data for Chart.js
    const datasets = prepareChartDatasets(filteredData, chartType);
    
    // Destroy existing chart
    destroyChart();
    
    // Get theme colors
    const primaryColor = getComputedStyle(document.documentElement).getPropertyValue('--theme-primary') || '#0d6efd';
    const successColor = getComputedStyle(document.documentElement).getPropertyValue('--theme-success') || '#198754';
    const dangerColor = getComputedStyle(document.documentElement).getPropertyValue('--theme-danger') || '#dc3545';
    const warningColor = getComputedStyle(document.documentElement).getPropertyValue('--theme-warning') || '#ffc107';
    const infoColor = getComputedStyle(document.documentElement).getPropertyValue('--theme-info') || '#0dcaf0';
    
    const themeColors = [primaryColor, successColor, dangerColor, warningColor, infoColor];
    
    // Create new chart
    const ctx = canvas.getContext('2d');
    sensorChart = new Chart(ctx, {
        type: chartType,
        data: { datasets: datasets.map((ds, idx) => ({
            ...ds,
            borderColor: themeColors[idx % themeColors.length],
            backgroundColor: chartType === 'line' 
                ? themeColors[idx % themeColors.length] + '33'
                : themeColors[idx % themeColors.length],
            borderWidth: 2,
            pointRadius: chartType === 'scatter' ? 5 : 3,
            pointHoverRadius: chartType === 'scatter' ? 7 : 5,
            fill: chartType === 'line'
        })) },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            interaction: {
                mode: 'index',
                intersect: false,
            },
            plugins: {
                legend: {
                    display: datasets.length > 1,
                    position: 'top',
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `${context.dataset.label}: ${context.parsed.y}`;
                        },
                        title: function(context) {
                            return new Date(context[0].parsed.x).toLocaleString();
                        }
                    }
                }
            },
            scales: {
                x: {
                    type: 'time',
                    time: {
                        unit: getTimeUnit(timeRange),
                        displayFormats: {
                            hour: 'MMM d, HH:mm',
                            day: 'MMM d',
                            week: 'MMM d',
                            month: 'MMM yyyy'
                        }
                    },
                    title: {
                        display: true,
                        text: 'Time'
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Value'
                    }
                }
            }
        }
    });
}

function filterSensorData(data, sensorType, timeRange, dataLimit) {
    // Safety check
    if (!data || !Array.isArray(data)) {
        console.warn('filterSensorData called with invalid data:', data);
        return [];
    }
    
    let filtered = [...data];
    
    console.log('Filtering sensor data:', {
        totalRecords: data.length,
        sensorType: sensorType,
        timeRange: timeRange,
        dataLimit: dataLimit
    });
    
    // Filter by sensor type
    if (sensorType && sensorType !== 'all') {
        filtered = filtered.filter(d => d.sensor_type === sensorType);
        console.log(`After sensor type filter (${sensorType}):`, filtered.length);
    }
    
    // Filter by time range
    if (timeRange && timeRange !== 'all') {
        const now = new Date();
        let cutoffDate;
        
        switch(timeRange) {
            case '24h':
                cutoffDate = new Date(now.getTime() - 24 * 60 * 60 * 1000);
                break;
            case '7d':
                cutoffDate = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
                break;
            case '30d':
                cutoffDate = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
                break;
        }
        
        if (cutoffDate) {
            console.log('Cutoff date:', cutoffDate);
            console.log('Sample data dates:', filtered.slice(0, 3).map(d => d.recorded_at));
            filtered = filtered.filter(d => {
                const recordDate = new Date(d.recorded_at);
                return recordDate >= cutoffDate;
            });
            console.log(`After time range filter (${timeRange}):`, filtered.length);
        }
    }
    
    // Apply mobile limit if on mobile and no custom limit
    let limit = dataLimit ? parseInt(dataLimit) : null;
    if (isMobileDevice && !limit) {
        limit = MOBILE_DATA_LIMIT;
    }
    
    // Apply data limit (take most recent)
    if (limit && filtered.length > limit) {
        filtered = filtered.slice(-limit);
    }
    
    return filtered;
}

function prepareChartDatasets(data, chartType) {
    // Group by sensor type
    const grouped = {};
    data.forEach(d => {
        if (!grouped[d.sensor_type]) {
            grouped[d.sensor_type] = [];
        }
        grouped[d.sensor_type].push({
            x: new Date(d.recorded_at),
            y: parseFloat(d.value)
        });
    });
    
    // Create datasets
    return Object.keys(grouped).map(sensorType => ({
        label: sensorType,
        data: grouped[sensorType].sort((a, b) => a.x - b.x)
    }));
}

function getTimeUnit(timeRange) {
    switch(timeRange) {
        case '24h': return 'hour';
        case '7d': return 'day';
        case '30d': return 'day';
        default: return 'day';
    }
}

function destroyChart() {
    if (sensorChart) {
        sensorChart.destroy();
        sensorChart = null;
    }
}

function showNoDataMessage() {
    const chartContainer = document.getElementById('sensorChartContainer');
    if (chartContainer) {
        const existing = chartContainer.querySelector('.no-data-message');
        if (existing) existing.remove();
        
        const timeRange = document.getElementById('timeRangeFilter')?.value;
        const sensorType = document.getElementById('sensorTypeFilter')?.value;
        
        let message = 'No data available for selected filters';
        if (timeRange && timeRange !== 'all') {
            const ranges = {
                '24h': 'last 24 hours',
                '7d': 'last 7 days',
                '30d': 'last 30 days'
            };
            message = `No sensor data found in the ${ranges[timeRange] || 'selected time range'}`;
        }
        if (sensorType && sensorType !== 'all') {
            message += ` for sensor type "${sensorType}"`;
        }
        
        const msg = document.createElement('div');
        msg.className = 'alert alert-info no-data-message mt-3';
        msg.innerHTML = `
            <i class="fas fa-info-circle me-2"></i>
            <strong>${message}</strong>
            <br><small>Try selecting "All Time" or a different time range to see your data.</small>
        `;
        chartContainer.appendChild(msg);
    }
}

function hideNoDataMessage() {
    const chartContainer = document.getElementById('sensorChartContainer');
    if (chartContainer) {
        const msg = chartContainer.querySelector('.no-data-message');
        if (msg) msg.remove();
    }
}

// ==================== CHART FILTERS & PREFERENCES ====================

function updateChartFilters(sensorData) {
    const sensorTypeFilter = document.getElementById('sensorTypeFilter');
    if (!sensorTypeFilter) return;
    
    // Get unique sensor types
    const sensorTypes = [...new Set(sensorData.map(d => d.sensor_type))];
    
    // Keep current selection
    const currentSelection = sensorTypeFilter.value;
    
    // Rebuild options
    let options = '<option value="all">All Sensor Types</option>';
    sensorTypes.forEach(type => {
        options += `<option value="${type}">${type}</option>`;
    });
    
    sensorTypeFilter.innerHTML = options;
    
    // Restore selection if still valid
    if (sensorTypes.includes(currentSelection) || currentSelection === 'all') {
        sensorTypeFilter.value = currentSelection;
    }
}

function saveChartPreferences() {
    const prefs = {
        chartType: document.getElementById('chartTypeSelect')?.value,
        sensorType: document.getElementById('sensorTypeFilter')?.value,
        timeRange: document.getElementById('timeRangeFilter')?.value,
        dataLimit: document.getElementById('dataLimitFilter')?.value
    };
    
    localStorage.setItem(`sensorChartPrefs_${entryId}`, JSON.stringify(prefs));
    
    // Visual feedback
    const btn = event.target;
    const original = btn.innerHTML;
    btn.innerHTML = '<i class="fas fa-check me-1"></i>Saved!';
    btn.classList.add('btn-success');
    btn.classList.remove('btn-primary');
    
    setTimeout(() => {
        btn.innerHTML = original;
        btn.classList.remove('btn-success');
        btn.classList.add('btn-primary');
    }, 2000);
}

function loadChartPreferences() {
    const saved = localStorage.getItem(`sensorChartPrefs_${entryId}`);
    if (!saved) return;
    
    try {
        const prefs = JSON.parse(saved);
        
        if (prefs.chartType) {
            const el = document.getElementById('chartTypeSelect');
            if (el) el.value = prefs.chartType;
        }
        if (prefs.sensorType) {
            const el = document.getElementById('sensorTypeFilter');
            if (el) el.value = prefs.sensorType;
        }
        if (prefs.timeRange) {
            const el = document.getElementById('timeRangeFilter');
            if (el) el.value = prefs.timeRange;
        }
        if (prefs.dataLimit && !isMobileDevice) {
            const el = document.getElementById('dataLimitFilter');
            if (el) el.value = prefs.dataLimit;
        }
    } catch (e) {
        console.error('Error loading chart preferences:', e);
    }
}

function resetChartPreferences() {
    localStorage.removeItem(`sensorChartPrefs_${entryId}`);
    
    document.getElementById('chartTypeSelect').value = 'line';
    document.getElementById('sensorTypeFilter').value = 'all';
    document.getElementById('timeRangeFilter').value = '24h';
    document.getElementById('dataLimitFilter').value = '';
    
    renderChartView();
}

// ==================== HELPER FUNCTIONS ====================

function formatSensorTimestamp(timestamp) {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now - date;
    
    // Less than 1 minute
    if (diff < 60000) {
        return 'Just now';
    }
    // Less than 1 hour
    if (diff < 3600000) {
        const mins = Math.floor(diff / 60000);
        return `${mins} min${mins > 1 ? 's' : ''} ago`;
    }
    // Less than 24 hours
    if (diff < 86400000) {
        const hours = Math.floor(diff / 3600000);
        return `${hours} hour${hours > 1 ? 's' : ''} ago`;
    }
    // Otherwise show full date
    return date.toLocaleString();
}

function showPerformanceAlertIfNeeded(dataCount) {
    const alert = document.getElementById('performanceAlert');
    if (!alert) return;
    
    if (isMobileDevice && dataCount > 100) {
        alert.classList.remove('d-none');
        const msg = document.getElementById('performanceMessage');
        if (msg) {
            msg.textContent = `You have ${dataCount} sensor readings. For better performance on mobile, consider using the time range or data limit filters.`;
        }
    } else {
        alert.classList.add('d-none');
    }
}

function toggleSharedSensorDetails() {
    const details = document.getElementById('sharedSensorDetails');
    if (details) {
        details.style.display = details.style.display === 'none' ? 'block' : 'none';
    }
}

// ==================== DEVICE MANAGEMENT ====================

function openDeviceManagement() {
    const modalElement = document.getElementById('deviceManagementModal');
    const modal = bootstrap.Modal.getInstance(modalElement) || new bootstrap.Modal(modalElement);
    modal.show();
    loadDeviceManagementContent();
}

async function loadDeviceManagementContent() {
    try {
        const contentDiv = document.getElementById('deviceManagementContent');
        contentDiv.innerHTML = `
            <div class="text-center py-4">
                <i class="fas fa-spinner fa-spin fa-2x text-muted"></i>
                <p class="text-muted mt-2">Loading devices...</p>
            </div>
        `;

        const [devicesResponse, linkedDevicesResponse] = await Promise.all([
            fetch('/api/devices'),
            fetch(`/api/entries/${entryId}/linked-devices`)
        ]);

        if (!devicesResponse.ok) {
            throw new Error('Failed to load devices');
        }

        const devices = await devicesResponse.json();
        let linkedDevices = [];
        
        if (linkedDevicesResponse.ok) {
            const linkedData = await linkedDevicesResponse.json();
            linkedDevices = linkedData.linked_devices || [];
        }

        renderDeviceManagementInterface(devices, linkedDevices);

    } catch (error) {
        console.error('Error loading device management:', error);
        document.getElementById('deviceManagementContent').innerHTML = `
            <div class="alert alert-danger">
                <i class="fas fa-exclamation-triangle me-2"></i>
                Error loading devices: ${error.message}
            </div>
        `;
    }
}

function renderDeviceManagementInterface(devices, linkedDevices = []) {
    const contentDiv = document.getElementById('deviceManagementContent');
    const linkedDeviceIds = new Set(linkedDevices.map(d => d.id));
    
    let html = `
        <div class="mb-3">
            <div class="d-flex justify-content-between align-items-center">
                <div>
                    <h6 class="mb-1"><i class="fas fa-microchip me-2"></i>Available Devices</h6>
                    <small class="text-muted">${devices.length} device(s) found, ${linkedDevices.length} linked to this entry</small>
                </div>
                <a href="/manage_devices" target="_blank" class="btn btn-outline-primary btn-sm">
                    <i class="fas fa-external-link-alt me-1"></i>Manage All
                </a>
            </div>
        </div>
    `;

    if (devices.length === 0) {
        html += `
            <div class="alert alert-warning text-center">
                <i class="fas fa-exclamation-circle me-2"></i>
                <strong>No devices found</strong><br>
                <small>Add ESP32 devices to automatically collect sensor data</small>
                <br>
                <a href="/manage_devices" target="_blank" class="btn btn-primary btn-sm mt-2">
                    <i class="fas fa-plus me-1"></i>Add Devices
                </a>
            </div>
        `;
    } else {
        html += '<div class="list-group">';
        
        devices.forEach(device => {
            const isLinked = linkedDeviceIds.has(device.id);
            const statusColor = device.auto_polling ? 'success' : 'warning';
            const statusText = device.auto_polling ? 'Auto-polling' : 'Manual only';
            
            html += `
                <div class="list-group-item ${isLinked ? 'list-group-item-success' : ''}">
                    <div class="d-flex justify-content-between align-items-center">
                        <div class="flex-grow-1">
                            <div class="d-flex align-items-center mb-1 flex-wrap gap-2">
                                <h6 class="mb-0">${device.device_name}</h6>
                                <span class="badge bg-${statusColor}">${statusText}</span>
                                ${isLinked ? '<span class="badge bg-success"><i class="fas fa-link me-1"></i>Linked</span>' : ''}
                            </div>
                            <small class="text-muted d-block">
                                <i class="fas fa-network-wired me-1"></i>
                                <a href="http://${device.ip}" target="_blank" class="link-primary">
                                    ${device.ip} <i class="fas fa-external-link-alt ms-1"></i>
                                </a>
                                <span class="mx-2">|</span>
                                <i class="fas fa-microchip me-1"></i>${device.device_type}
                            </small>
                            ${device.last_poll_success ? 
                                `<small class="text-muted d-block">
                                    <i class="fas fa-clock me-1"></i>Last poll: ${new Date(device.last_poll_success).toLocaleString()}
                                </small>` 
                                : ''}
                        </div>
                        <div class="ms-3">
                            ${isLinked ? 
                                `<button class="btn btn-outline-danger btn-sm" onclick="unlinkDeviceFromEntry(${device.id})">
                                    <i class="fas fa-unlink me-1"></i>Unlink
                                </button>` :
                                `<button class="btn btn-success btn-sm" onclick="linkDeviceToEntry(${device.id})">
                                    <i class="fas fa-link me-1"></i>Link
                                </button>`
                            }
                        </div>
                    </div>
                </div>
            `;
        });
        
        html += '</div>';
    }

    contentDiv.innerHTML = html;
}

async function linkDeviceToEntry(deviceId) {
    try {
        const response = await fetch(`/api/devices/${deviceId}/link-entry`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ entry_id: entryId })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to link device');
        }

        alert('Device linked successfully! It will now automatically record sensor data to this entry.');
        loadDeviceManagementContent();

    } catch (error) {
        console.error('Error linking device:', error);
        alert('Error linking device: ' + error.message);
    }
}

async function unlinkDeviceFromEntry(deviceId) {
    try {
        if (!confirm('Unlink this device? It will stop automatically recording data to this entry.')) {
            return;
        }

        const response = await fetch(`/api/devices/${deviceId}/unlink-entry`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ entry_id: entryId })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to unlink device');
        }

        alert('Device unlinked successfully!');
        loadDeviceManagementContent();

    } catch (error) {
        console.error('Error unlinking device:', error);
        alert('Error unlinking device: ' + error.message);
    }
}

// ==================== INITIALIZATION ====================

function initializeSensorSection() {
    console.log('Initializing sensor section for entry:', entryId);
    
    // Setup view toggle
    const chartViewBtn = document.getElementById('chartView');
    const tableViewBtn = document.getElementById('tableView');
    
    if (chartViewBtn && tableViewBtn) {
        chartViewBtn.addEventListener('change', function() {
            if (this.checked) {
                document.getElementById('sensorChartContainer').style.display = 'block';
                document.getElementById('sensorDataContainer').style.display = 'none';
                if (allSensorData && allSensorData.length > 0) {
                    renderChartView();
                }
            }
        });
        
        tableViewBtn.addEventListener('change', function() {
            if (this.checked) {
                document.getElementById('sensorChartContainer').style.display = 'none';
                document.getElementById('sensorDataContainer').style.display = 'block';
                if (sensorDataCache.length > 0) {
                    renderTableView(sensorDataCache);
                }
            }
        });
    }
    
    // Setup chart controls
    const chartTypeSelect = document.getElementById('chartTypeSelect');
    const sensorTypeFilter = document.getElementById('sensorTypeFilter');
    const timeRangeFilter = document.getElementById('timeRangeFilter');
    const dataLimitFilter = document.getElementById('dataLimitFilter');
    
    if (chartTypeSelect) chartTypeSelect.addEventListener('change', () => {
        if (allSensorData && allSensorData.length > 0) renderChartView();
    });
    if (sensorTypeFilter) sensorTypeFilter.addEventListener('change', () => {
        if (allSensorData && allSensorData.length > 0) renderChartView();
    });
    if (timeRangeFilter) timeRangeFilter.addEventListener('change', () => {
        if (allSensorData && allSensorData.length > 0) renderChartView();
    });
    if (dataLimitFilter) dataLimitFilter.addEventListener('change', () => {
        if (allSensorData && allSensorData.length > 0) renderChartView();
    });
    
    // Apply mobile limit if on mobile
    if (isMobileDevice && dataLimitFilter) {
        dataLimitFilter.value = MOBILE_DATA_LIMIT;
        dataLimitFilter.max = MOBILE_DATA_LIMIT;
        
        // Show performance alert
        const perfAlert = document.getElementById('performanceAlert');
        if (perfAlert) {
            perfAlert.classList.remove('d-none');
        }
    }
    
    // DON'T load chart preferences here - let data load first with defaults
    // Preferences will be available for user to save after they see their data
    // loadChartPreferences();
    
    // Load initial sensor data (this will trigger chart rendering when complete)
    console.log('Loading initial sensor data...');
    loadSensorData();
    
    // Start auto-refresh
    startSensorDataAutoRefresh();
}

// Execute any registered callbacks when this script loads
if (typeof window.sensorSectionCallbacks !== 'undefined') {
    window.sensorSectionCallbacks.forEach(callback => callback());
}

// Cleanup on page unload
window.addEventListener('beforeunload', function() {
    stopSensorDataAutoRefresh();
    destroyChart();
});
