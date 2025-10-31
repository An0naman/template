// Template-level shim: real implementation lives in static/js/sections/_sensors_functions.js
// This empty file avoids duplicate definitions and Jinja-in-JS lint issues.

/* No runtime code */
    
    // Page numbers
    for (let i = 1; i <= totalPages; i++) {
        if (i === 1 || i === totalPages || (i >= currentPage - 2 && i <= currentPage + 2)) {
            const li = document.createElement('li');
            li.className = `page-item ${i === currentPage ? 'active' : ''}`;
            li.innerHTML = `<a class="page-link" href="#" onclick="changePage(${i}); return false;">${i}</a>`;
            pagination.appendChild(li);
        } else if (i === currentPage - 3 || i === currentPage + 3) {
            const li = document.createElement('li');
            li.className = 'page-item disabled';
            li.innerHTML = '<span class="page-link">...</span>';
            pagination.appendChild(li);
        }
    }
    
    // Next button
    const nextLi = document.createElement('li');
    nextLi.className = `page-item ${currentPage === totalPages ? 'disabled' : ''}`;
    nextLi.innerHTML = `<a class="page-link" href="#" onclick="changePage(${currentPage + 1}); return false;">Next</a>`;
    pagination.appendChild(nextLi);
}

/**
 * Change table page
 */
function changePage(page) {
    window.currentPage = page;
    updateTable(page);
}

/**
 * Update device list
 */
function updateDeviceList() {
    const deviceList = document.getElementById('deviceList');
    if (!deviceList) return;
    
    // Get unique devices/sources
    const sources = {};
    filteredData.forEach(reading => {
        const key = reading.source_id || reading.source_type;
        if (!sources[key]) {
            sources[key] = {
                type: reading.source_type,
                id: reading.source_id,
                count: 0,
                lastSeen: reading.recorded_at
            };
        }
        sources[key].count++;
        if (new Date(reading.recorded_at) > new Date(sources[key].lastSeen)) {
            sources[key].lastSeen = reading.recorded_at;
        }
    });
    
    // Build device list HTML
    const html = Object.entries(sources).map(([key, source]) => `
        <div class="d-flex justify-content-between align-items-center mb-2 pb-2 border-bottom">
            <div>
                <i class="fas fa-${source.type === 'device' ? 'microchip' : source.type === 'api' ? 'cloud' : 'user'} me-2"></i>
                <strong>${source.id || source.type}</strong>
            </div>
            <div class="text-muted">
                <span class="badge bg-secondary">${source.count} readings</span>
                <small class="ms-2">Last: ${formatTimestamp(source.lastSeen)}</small>
            </div>
        </div>
    `).join('');
    
    deviceList.innerHTML = html || '<p class="text-muted mb-0">No devices found</p>';
}

/**
 * Format timestamp for display
 */
function formatTimestamp(timestamp) {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

/**
 * Show/hide loading indicator
 */
function showLoading(show) {
    const loading = document.getElementById('loadingIndicator');
    const noData = document.getElementById('noDataMessage');
    const chartContainer = document.getElementById('chartContainer');
    const stats = document.getElementById('sensorStats');
    
    if (show) {
        loading.style.display = 'block';
        noData.style.display = 'none';
        chartContainer.style.display = 'none';
        stats.style.display = 'none';
    } else {
        loading.style.display = 'none';
    }
}

/**
 * Show no data message
 */
function showNoData() {
    document.getElementById('noDataMessage').style.display = 'block';
    document.getElementById('chartContainer').style.display = 'none';
    document.getElementById('sensorStats').style.display = 'none';
    document.getElementById('sensorDataTable').style.display = 'none';
}

/**
 * Event Handlers
 */

function onSensorTypeChange() {
    currentSensorType = document.getElementById('sensorTypeSelect').value;
    loadSensorData();
}

function onTimeRangeChange() {
    const select = document.getElementById('timeRangeSelect');
    currentTimeRange = select.value;
    
    // Show/hide custom date range inputs
    const customDateRange = document.getElementById('customDateRange');
    if (currentTimeRange === 'custom') {
        customDateRange.style.display = 'flex';
        // Set default values
        const now = new Date();
        const weekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
        document.getElementById('startDate').value = weekAgo.toISOString().slice(0, 16);
        document.getElementById('endDate').value = now.toISOString().slice(0, 16);
    } else {
        customDateRange.style.display = 'none';
        loadSensorData();
    }
}

function onCustomDateChange() {
    customStartDate = document.getElementById('startDate').value;
    customEndDate = document.getElementById('endDate').value;
    loadSensorData();
}

function refreshSensorData() {
    loadSensorData();
    showNotification('Sensor data refreshed', 'success');
}

function toggleDataTable() {
    const table = document.getElementById('sensorDataTable');
    const toggleText = document.getElementById('tableToggleText');
    
    if (table.style.display === 'none') {
        table.style.display = 'block';
        toggleText.textContent = 'Hide Table';
        updateTable(1);
    } else {
        table.style.display = 'none';
        toggleText.textContent = 'Show Table';
    }
}

/**
 * Setup form handlers
 */
function setupFormHandlers() {
    // Add sensor data form
    document.getElementById('addSensorDataForm').addEventListener('submit', async function(e) {
        e.preventDefault();
        await addSensorReading();
    });
    
    // Edit sensor data form
    document.getElementById('editSensorDataForm').addEventListener('submit', async function(e) {
        e.preventDefault();
        await updateSensorReading();
    });
    
    // Source type change
    document.getElementById('addSource').addEventListener('change', function() {
        const deviceSection = document.getElementById('deviceSourceSection');
        deviceSection.style.display = this.value === 'device' ? 'block' : 'none';
    });
}

/**
 * Add new sensor reading
 */
async function addSensorReading() {
    try {
        // Get form values
        const sensorType = document.getElementById('addNewSensorType').value || document.getElementById('addSensorType').value;
        const value = document.getElementById('addValue').value;
        const unit = document.getElementById('addUnit').value;
        const timestamp = document.getElementById('addTimestamp').value;
        const source = document.getElementById('addSource').value;
        const deviceId = document.getElementById('addDeviceId').value;
        const notes = document.getElementById('addNotes').value;
        
        if (!sensorType || !value) {
            showNotification('Please fill in all required fields', 'error');
            return;
        }
        
        // Build request payload
        const payload = {
            sensor_type: sensorType,
            value: value,
            unit: unit,
            entry_ids: [window.currentEntryId],
            recorded_at: timestamp || new Date().toISOString(),
            source_type: source,
            source_id: deviceId || null,
            metadata: notes ? { notes: notes } : {}
        };
        
        // Submit to API
        const response = await fetch('/api/shared_sensor_data', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to add sensor reading');
        }
        
        // Close modal and refresh
        bootstrap.Modal.getInstance(document.getElementById('addSensorDataModal')).hide();
        document.getElementById('addSensorDataForm').reset();
        
        await loadSensorData();
        showNotification('Sensor reading added successfully', 'success');
        
    } catch (error) {
        console.error('Error adding sensor reading:', error);
        showNotification(error.message, 'error');
    }
}

/**
 * Edit sensor reading
 */
async function editSensorReading(id) {
    // Find reading in data
    const reading = filteredData.find(r => r.id === id);
    if (!reading) return;
    
    // Populate edit form
    document.getElementById('editSensorId').value = reading.id;
    document.getElementById('editSensorType').value = reading.sensor_type;
    document.getElementById('editValue').value = reading.value;
    document.getElementById('editUnit').value = reading.unit || '';
    
    // Convert timestamp to local datetime format
    const date = new Date(reading.recorded_at);
    document.getElementById('editTimestamp').value = date.toISOString().slice(0, 16);
    
    document.getElementById('editNotes').value = reading.metadata?.notes || '';
    
    // Show modal
    new bootstrap.Modal(document.getElementById('editSensorDataModal')).show();
}

/**
 * Update sensor reading
 */
async function updateSensorReading() {
    try {
        const id = document.getElementById('editSensorId').value;
        const value = document.getElementById('editValue').value;
        const unit = document.getElementById('editUnit').value;
        const timestamp = document.getElementById('editTimestamp').value;
        const notes = document.getElementById('editNotes').value;
        
        const payload = {
            value: value,
            unit: unit,
            recorded_at: new Date(timestamp).toISOString(),
            metadata: notes ? { notes: notes } : {}
        };
        
        const response = await fetch(`/api/shared_sensor_data/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        
        if (!response.ok) throw new Error('Failed to update sensor reading');
        
        // Close modal and refresh
        bootstrap.Modal.getInstance(document.getElementById('editSensorDataModal')).hide();
        await loadSensorData();
        showNotification('Sensor reading updated successfully', 'success');
        
    } catch (error) {
        console.error('Error updating sensor reading:', error);
        showNotification(error.message, 'error');
    }
}

/**
 * Delete sensor reading with confirmation
 */
function deleteSensorReadingConfirm(id) {
    if (confirm('Are you sure you want to delete this sensor reading? This action cannot be undone.')) {
        deleteSensorReading(id);
    }
}

/**
 * Delete sensor reading
 */
async function deleteSensorReading(id = null) {
    try {
        // If no ID provided, get from edit form
        if (!id) {
            id = document.getElementById('editSensorId').value;
        }
        
        const response = await fetch(`/api/shared_sensor_data/${id}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) throw new Error('Failed to delete sensor reading');
        
        // Close modal if open and refresh
        const editModal = bootstrap.Modal.getInstance(document.getElementById('editSensorDataModal'));
        if (editModal) editModal.hide();
        
        await loadSensorData();
        showNotification('Sensor reading deleted successfully', 'success');
        
    } catch (error) {
        console.error('Error deleting sensor reading:', error);
        showNotification(error.message, 'error');
    }
}

/**
 * Check and enable auto-refresh if configured
 */
function checkAutoRefresh() {
    const autoRefresh = localStorage.getItem('sensorAutoRefresh') === 'true';
    if (autoRefresh) {
        autoRefreshInterval = setInterval(() => {
            loadSensorData();
        }, 60000); // 60 seconds
    }
}

/**
 * Show notification (uses global notification system if available)
 */
function showNotification(message, type = 'info') {
    if (typeof showToast === 'function') {
        showToast(message, type);
    } else {
        console.log(`[${type.toUpperCase()}] ${message}`);
    }
}

/**
 * Cleanup on page unload
 */
window.addEventListener('beforeunload', function() {
    if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
    }
    if (sensorChart) {
        sensorChart.destroy();
    }
});
