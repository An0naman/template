// Dashboard JavaScript
// Manages dashboard creation, widget rendering, and interactions

let currentDashboard = null;
let gridStack = null;
let editMode = false;
let availableSources = null;
let widgetCharts = {}; // Store Chart.js instances

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    initializeDashboard();
    setupEventListeners();
    loadDashboards();
    loadDataSources();
});

// ============================================================================
// Initialization
// ============================================================================

function initializeDashboard() {
    // Initialize GridStack
    gridStack = GridStack.init({
        column: 12,
        cellHeight: 100,
        margin: 10,
        float: false,
        disableResize: true,
        disableDrag: true,
        animate: true
    });
}

function setupEventListeners() {
    // Dashboard controls
    document.getElementById('dashboardSelect').addEventListener('change', handleDashboardChange);
    document.getElementById('newDashboardBtn').addEventListener('click', showNewDashboardModal);
    document.getElementById('createFirstDashboard').addEventListener('click', showNewDashboardModal);
    document.getElementById('saveDashboardBtn').addEventListener('click', createDashboard);
    document.getElementById('setDefaultDashboardBtn').addEventListener('click', setDashboardAsDefault);
    document.getElementById('deleteDashboardBtn').addEventListener('click', deleteDashboard);
    document.getElementById('editModeBtn').addEventListener('click', toggleEditMode);
    document.getElementById('refreshAllBtn').addEventListener('click', refreshAllWidgets);
    
    // Widget controls
    document.getElementById('addWidgetBtn').addEventListener('click', showAddWidgetModal);
    document.getElementById('saveWidgetBtn').addEventListener('click', addWidget);
    document.getElementById('widgetType').addEventListener('change', handleWidgetTypeChange);
    
    // Chart attribute change handler
    const chartAttributeSelect = document.getElementById('chartAttribute');
    if (chartAttributeSelect) {
        chartAttributeSelect.addEventListener('change', handleChartAttributeChange);
    }
    
    // Event delegation for widget buttons (since they're dynamically created)
    document.addEventListener('click', function(e) {
        // Handle refresh widget button
        if (e.target.closest('.refresh-widget-btn')) {
            const btn = e.target.closest('.refresh-widget-btn');
            const widgetId = parseInt(btn.dataset.widgetId);
            refreshWidget(widgetId);
        }
        
        // Handle force refresh widget button (AI summary only)
        if (e.target.closest('.force-refresh-widget-btn')) {
            const btn = e.target.closest('.force-refresh-widget-btn');
            const widgetId = parseInt(btn.dataset.widgetId);
            refreshWidget(widgetId, true); // true = force refresh
        }
        
        // Handle edit widget button
        if (e.target.closest('.edit-widget-btn')) {
            console.log('Edit button clicked');
            const btn = e.target.closest('.edit-widget-btn');
            const widgetId = parseInt(btn.dataset.widgetId);
            console.log('Editing widget ID:', widgetId);
            editWidget(widgetId);
        }
        
        // Handle delete widget button
        if (e.target.closest('.delete-widget-btn')) {
            const btn = e.target.closest('.delete-widget-btn');
            const widgetId = parseInt(btn.dataset.widgetId);
            deleteWidget(widgetId);
        }
    });
}

// ============================================================================
// Dashboard Management
// ============================================================================

async function loadDashboards() {
    try {
        const response = await fetch('/api/dashboards');
        const dashboards = await response.json();
        
        const select = document.getElementById('dashboardSelect');
        select.innerHTML = '<option value="">Select a dashboard...</option>';
        
        dashboards.forEach(dashboard => {
            const option = document.createElement('option');
            option.value = dashboard.id;
            option.textContent = dashboard.name + (dashboard.is_default ? ' (Default)' : '');
            select.appendChild(option);
        });
        
        // Load default dashboard if exists
        const defaultDashboard = dashboards.find(d => d.is_default);
        if (defaultDashboard) {
            select.value = defaultDashboard.id;
            await loadDashboard(defaultDashboard.id);
        } else if (dashboards.length === 0) {
            showEmptyState();
        }
        
    } catch (error) {
        console.error('Error loading dashboards:', error);
        showNotification('Failed to load dashboards', 'error');
    }
}

async function handleDashboardChange(event) {
    const dashboardId = event.target.value;
    if (dashboardId) {
        await loadDashboard(dashboardId);
    } else {
        showEmptyState();
    }
}

async function loadDashboard(dashboardId) {
    try {
        const response = await fetch(`/api/dashboards/${dashboardId}`);
        if (!response.ok) throw new Error('Failed to load dashboard');
        
        currentDashboard = await response.json();
        
        // Update dashboard title with selected dashboard name
        const titleElement = document.getElementById('dashboardTitleText');
        if (titleElement && currentDashboard.name) {
            titleElement.textContent = currentDashboard.name;
        }
        
        // Clear existing widgets
        gridStack.removeAll();
        clearCharts();
        
        // Hide empty state
        document.getElementById('emptyState').style.display = 'none';
        document.getElementById('dashboardGrid').style.display = 'block';
        
        // Update buttons based on dashboard state
        updateDashboardButtons();
        
        // Load widgets
        if (currentDashboard.widgets && currentDashboard.widgets.length > 0) {
            currentDashboard.widgets.forEach(widget => {
                addWidgetToGrid(widget);
            });
            
            // Load data for all widgets
            await loadAllWidgetData();
        }
        
    } catch (error) {
        console.error('Error loading dashboard:', error);
        showNotification('Failed to load dashboard', 'error');
    }
}

function showNewDashboardModal() {
    document.getElementById('newDashboardForm').reset();
    const modal = new bootstrap.Modal(document.getElementById('newDashboardModal'));
    modal.show();
}

async function createDashboard() {
    const name = document.getElementById('dashboardName').value.trim();
    const description = document.getElementById('dashboardDescription').value.trim();
    const isDefault = document.getElementById('dashboardIsDefault').checked;
    
    if (!name) {
        showNotification('Please enter a dashboard name', 'warning');
        return;
    }
    
    try {
        const response = await fetch('/api/dashboards', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, description, is_default: isDefault })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to create dashboard');
        }
        
        const result = await response.json();
        
        // Close modal
        bootstrap.Modal.getInstance(document.getElementById('newDashboardModal')).hide();
        
        // Reload dashboards
        await loadDashboards();
        
        // Select new dashboard
        document.getElementById('dashboardSelect').value = result.id;
        await loadDashboard(result.id);
        
        showBanner('Dashboard created successfully', 'success');
        
    } catch (error) {
        console.error('Error creating dashboard:', error);
        showBanner(error.message, 'error');
    }
}

async function setDashboardAsDefault() {
    if (!currentDashboard) return;
    
    try {
        const response = await fetch(`/api/dashboards/${currentDashboard.id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ is_default: true })
        });
        
        if (!response.ok) throw new Error('Failed to set default dashboard');
        
        // Reload dashboards to update the display
        await loadDashboards();
        
        // Re-select current dashboard
        document.getElementById('dashboardSelect').value = currentDashboard.id;
        
        showBanner('Dashboard set as default successfully', 'success');
        
        // Update button visibility
        updateDashboardButtons();
        
    } catch (error) {
        console.error('Error setting default dashboard:', error);
        showBanner('Failed to set default dashboard', 'error');
    }
}

async function deleteDashboard() {
    if (!currentDashboard) return;
    
    if (!confirm(`Are you sure you want to delete "${currentDashboard.name}"?`)) {
        return;
    }
    
    try {
        const response = await fetch(`/api/dashboards/${currentDashboard.id}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) throw new Error('Failed to delete dashboard');
        
        currentDashboard = null;
        await loadDashboards();
        showEmptyState();
        
        showBanner('Dashboard deleted successfully', 'success');
        
    } catch (error) {
        console.error('Error deleting dashboard:', error);
        showBanner('Failed to delete dashboard', 'error');
    }
}

function updateDashboardButtons() {
    if (currentDashboard) {
        document.getElementById('deleteDashboardBtn').style.display = 'inline-block';
        // Show "Set as Default" button only if not already default
        const setDefaultBtn = document.getElementById('setDefaultDashboardBtn');
        if (currentDashboard.is_default) {
            setDefaultBtn.style.display = 'none';
        } else {
            setDefaultBtn.style.display = 'inline-block';
        }
    } else {
        document.getElementById('deleteDashboardBtn').style.display = 'none';
        document.getElementById('setDefaultDashboardBtn').style.display = 'none';
    }
}

function showEmptyState() {
    // Reset dashboard title to default
    const titleElement = document.getElementById('dashboardTitleText');
    if (titleElement) {
        titleElement.textContent = 'Dashboard';
    }
    
    document.getElementById('emptyState').style.display = 'block';
    document.getElementById('dashboardGrid').style.display = 'none';
    document.getElementById('deleteDashboardBtn').style.display = 'none';
    document.getElementById('setDefaultDashboardBtn').style.display = 'none';
    gridStack.removeAll();
    clearCharts();
}

// ============================================================================
// Widget Management
// ============================================================================

async function loadDataSources() {
    try {
        const response = await fetch('/api/dashboard_sources');
        availableSources = await response.json();
    } catch (error) {
        console.error('Error loading data sources:', error);
    }
}

async function showAddWidgetModal() {
    if (!currentDashboard) {
        showNotification('Please select or create a dashboard first', 'warning');
        return;
    }
    
    // Reset form and button
    document.getElementById('addWidgetForm').reset();
    document.getElementById('dataSourceConfig').style.display = 'none';
    const saveBtn = document.getElementById('saveWidgetBtn');
    delete saveBtn.dataset.editingWidgetId;
    saveBtn.textContent = 'Add Widget';
    
    // Reload data sources to get latest saved searches
    await loadDataSources();
    
    // Populate saved searches
    if (availableSources && availableSources.saved_searches) {
        const select = document.getElementById('savedSearchSelect');
        select.innerHTML = '<option value="">Select saved search...</option>';
        availableSources.saved_searches.forEach(search => {
            const option = document.createElement('option');
            option.value = search.id;
            option.textContent = search.name;
            select.appendChild(option);
        });
    }
    
    // Populate sensor types
    if (availableSources && availableSources.sensor_types) {
        const select = document.getElementById('sensorTypeSelect');
        select.innerHTML = '<option value="">Select sensor type...</option>';
        availableSources.sensor_types.forEach(sensorType => {
            const option = document.createElement('option');
            option.value = sensorType;
            option.textContent = sensorType;
            select.appendChild(option);
        });
    }
    
    const modal = new bootstrap.Modal(document.getElementById('addWidgetModal'));
    modal.show();
}

function handleWidgetTypeChange(event) {
    // Handle both event object and direct calls
    const widgetType = event ? event.target.value : document.getElementById('widgetType').value;
    const dataSourceConfig = document.getElementById('dataSourceConfig');
    const savedSearchConfig = document.getElementById('savedSearchConfig');
    const sensorDataConfig = document.getElementById('sensorDataConfig');
    const aiSummaryPromptConfig = document.getElementById('aiSummaryPromptConfig');
    const chartConfig = document.getElementById('chartConfig');
    
    // Hide all configs
    savedSearchConfig.style.display = 'none';
    sensorDataConfig.style.display = 'none';
    dataSourceConfig.style.display = 'none';
    aiSummaryPromptConfig.style.display = 'none';
    if (chartConfig) chartConfig.style.display = 'none';
    
    // Show relevant config based on widget type
    if (widgetType === 'list' || widgetType === 'ai_summary' || widgetType === 'stat_card') {
        dataSourceConfig.style.display = 'block';
        savedSearchConfig.style.display = 'block';
        
        // Show AI prompt config only for AI summary widgets
        if (widgetType === 'ai_summary') {
            aiSummaryPromptConfig.style.display = 'block';
        }
    } else if (widgetType === 'line_chart') {
        dataSourceConfig.style.display = 'block';
        savedSearchConfig.style.display = 'block';
        sensorDataConfig.style.display = 'block';
    } else if (widgetType === 'chart') {
        if (chartConfig) chartConfig.style.display = 'block';
        dataSourceConfig.style.display = 'block';
        savedSearchConfig.style.display = 'block';
    }
}

function handleChartAttributeChange(event) {
    const attribute = event ? event.target.value : document.getElementById('chartAttribute').value;
    const timelineOptions = document.getElementById('timelineOptions');
    
    if (timelineOptions) {
        // Show timeline options for date/timeline attribute
        if (attribute === 'date_timeline') {
            timelineOptions.style.display = 'block';
        } else {
            timelineOptions.style.display = 'none';
        }
    }
}

async function addWidget() {
    if (!currentDashboard) return;
    
    const saveBtn = document.getElementById('saveWidgetBtn');
    const editingWidgetId = saveBtn.dataset.editingWidgetId;
    const isEditing = !!editingWidgetId;
    
    const widgetType = document.getElementById('widgetType').value;
    const title = document.getElementById('widgetTitle').value.trim();
    const width = parseInt(document.getElementById('widgetWidth').value);
    const height = parseInt(document.getElementById('widgetHeight').value);
    
    if (!widgetType || !title) {
        showNotification('Please fill in all required fields', 'warning');
        return;
    }
    
    const widgetData = {
        widget_type: widgetType,
        title: title,
        width: width,
        height: height,
        config: {}
    };
    
    // Only set position for new widgets
    if (!isEditing) {
        widgetData.position_x = 0;
        widgetData.position_y = 0;
    }
    
    // Set data source based on widget type
    if (widgetType === 'list' || widgetType === 'ai_summary' || widgetType === 'stat_card') {
        const savedSearchId = document.getElementById('savedSearchSelect').value;
        if (savedSearchId) {
            widgetData.data_source_type = 'saved_search';
            widgetData.data_source_id = parseInt(savedSearchId);
        }
        
        // Add custom prompt for AI summary widgets
        if (widgetType === 'ai_summary') {
            const customPrompt = document.getElementById('widgetCustomPrompt').value.trim();
            if (customPrompt) {
                widgetData.config.custom_prompt = customPrompt;
            }
        }
    }
    
    if (widgetType === 'chart') {
        const savedSearchId = document.getElementById('savedSearchSelect').value;
        const chartType = document.getElementById('chartType').value;
        const chartAttribute = document.getElementById('chartAttribute').value;
        
        if (savedSearchId && chartType && chartAttribute) {
            widgetData.data_source_type = 'saved_search';
            widgetData.data_source_id = parseInt(savedSearchId);
            widgetData.config.chart_type = chartType;
            widgetData.config.chart_attribute = chartAttribute;
            
            // Add timeline options for date/timeline attribute
            if (chartAttribute === 'date_timeline') {
                const dateField = document.getElementById('dateField').value;
                const timelineGrouping = document.getElementById('timelineGrouping').value;
                widgetData.config.date_field = dateField;
                widgetData.config.timeline_grouping = timelineGrouping;
            }
        } else {
            showNotification('Please select chart type, attribute, and data source', 'warning');
            return;
        }
    }
    
    if (widgetType === 'line_chart') {
        const savedSearchId = document.getElementById('savedSearchSelect').value;
        const sensorType = document.getElementById('sensorTypeSelect').value;
        const timeRange = document.getElementById('timeRangeSelect').value;
        
        if (savedSearchId && sensorType) {
            widgetData.data_source_type = 'sensor_data';
            widgetData.data_source_id = parseInt(savedSearchId);
            widgetData.config = {
                sensor_type: sensorType,
                time_range: timeRange
            };
        }
    }
    
    try {
        let response;
        if (isEditing) {
            // Update existing widget
            response = await fetch(`/api/widgets/${editingWidgetId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(widgetData)
            });
        } else {
            // Create new widget
            response = await fetch(`/api/dashboards/${currentDashboard.id}/widgets`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(widgetData)
            });
        }
        
        if (!response.ok) throw new Error(`Failed to ${isEditing ? 'update' : 'add'} widget`);
        
        // Close modal and reset
        const modal = bootstrap.Modal.getInstance(document.getElementById('addWidgetModal'));
        modal.hide();
        delete saveBtn.dataset.editingWidgetId;
        saveBtn.textContent = 'Add Widget';
        
        // Reload dashboard
        await loadDashboard(currentDashboard.id);
        
        showBanner(`Widget ${isEditing ? 'updated' : 'added'} successfully`, 'success');
        
    } catch (error) {
        console.error(`Error ${isEditing ? 'updating' : 'adding'} widget:`, error);
        showBanner(`Failed to ${isEditing ? 'update' : 'add'} widget`, 'error');
    }
}

async function editWidget(widgetId) {
    // Find the widget in current dashboard
    const widget = currentDashboard.widgets.find(w => w.id === widgetId);
    if (!widget) {
        showBanner('Widget not found', 'error');
        return;
    }
    
    // Load data sources first
    await loadDataSources();
    
    // Populate saved searches dropdown
    if (availableSources && availableSources.saved_searches) {
        const select = document.getElementById('savedSearchSelect');
        select.innerHTML = '<option value="">Select saved search...</option>';
        availableSources.saved_searches.forEach(search => {
            const option = document.createElement('option');
            option.value = search.id;
            option.textContent = search.name;
            select.appendChild(option);
        });
    }
    
    // Populate sensor types dropdown
    if (availableSources && availableSources.sensor_types) {
        const select = document.getElementById('sensorTypeSelect');
        select.innerHTML = '<option value="">Select sensor type...</option>';
        availableSources.sensor_types.forEach(sensorType => {
            const option = document.createElement('option');
            option.value = sensorType;
            option.textContent = sensorType;
            select.appendChild(option);
        });
    }
    
    // Populate the form with current values
    document.getElementById('widgetTitle').value = widget.title;
    document.getElementById('widgetType').value = widget.widget_type;
    document.getElementById('widgetWidth').value = widget.width;
    document.getElementById('widgetHeight').value = widget.height;
    
    // Trigger change event to show appropriate data source options
    handleWidgetTypeChange();
    
    // Set data source based on type
    if (widget.data_source_type === 'saved_search' || widget.data_source_type === 'entry_states') {
        const savedSearchSelect = document.getElementById('savedSearchSelect');
        if (savedSearchSelect && widget.data_source_id) {
            savedSearchSelect.value = widget.data_source_id;
        }
    }
    
    // For line charts, also set sensor config
    if (widget.widget_type === 'line_chart' && widget.config) {
        try {
            const config = typeof widget.config === 'string' ? JSON.parse(widget.config) : widget.config;
            if (config.sensor_type) {
                const sensorTypeSelect = document.getElementById('sensorTypeSelect');
                if (sensorTypeSelect) sensorTypeSelect.value = config.sensor_type;
            }
            if (config.time_range) {
                const timeRangeSelect = document.getElementById('timeRangeSelect');
                if (timeRangeSelect) timeRangeSelect.value = config.time_range;
            }
        } catch (e) {
            console.error('Error parsing widget config:', e);
        }
    }
    
    // For AI summary widgets, load custom prompt
    if (widget.widget_type === 'ai_summary' && widget.config) {
        try {
            const config = typeof widget.config === 'string' ? JSON.parse(widget.config) : widget.config;
            if (config.custom_prompt) {
                const customPromptTextarea = document.getElementById('widgetCustomPrompt');
                if (customPromptTextarea) customPromptTextarea.value = config.custom_prompt;
            }
        } catch (e) {
            console.error('Error parsing widget config for custom prompt:', e);
        }
    }
    
    // For chart widgets, load chart configuration
    if (widget.widget_type === 'chart' && widget.config) {
        try {
            const config = typeof widget.config === 'string' ? JSON.parse(widget.config) : widget.config;
            if (config.chart_type) {
                const chartTypeSelect = document.getElementById('chartType');
                if (chartTypeSelect) chartTypeSelect.value = config.chart_type;
            }
            if (config.chart_attribute) {
                const chartAttributeSelect = document.getElementById('chartAttribute');
                if (chartAttributeSelect) {
                    chartAttributeSelect.value = config.chart_attribute;
                    // Trigger change to show/hide timeline options
                    handleChartAttributeChange({ target: { value: config.chart_attribute } });
                }
            }
            if (config.date_field) {
                const dateFieldSelect = document.getElementById('dateField');
                if (dateFieldSelect) dateFieldSelect.value = config.date_field;
            }
            if (config.timeline_grouping) {
                const timelineGroupingSelect = document.getElementById('timelineGrouping');
                if (timelineGroupingSelect) timelineGroupingSelect.value = config.timeline_grouping;
            }
        } catch (e) {
            console.error('Error parsing widget config for chart:', e);
        }
    }
    
    // Store the widget ID for updating
    document.getElementById('saveWidgetBtn').dataset.editingWidgetId = widgetId;
    document.getElementById('saveWidgetBtn').textContent = 'Update Widget';
    
    // Show the modal
    const modal = new bootstrap.Modal(document.getElementById('addWidgetModal'));
    modal.show();
}

async function deleteWidget(widgetId) {
    if (!confirm('Are you sure you want to delete this widget?')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/widgets/${widgetId}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) throw new Error('Failed to delete widget');
        
        // Reload dashboard
        await loadDashboard(currentDashboard.id);
        
        showBanner('Widget deleted successfully', 'success');
        
    } catch (error) {
        console.error('Error deleting widget:', error);
        showBanner('Failed to delete widget', 'error');
    }
}

// ============================================================================
// Widget Rendering
// ============================================================================

function addWidgetToGrid(widget) {
    const isAISummary = widget.widget_type === 'ai_summary';
    const widgetHtml = `
        <div class="dashboard-widget">
            <div class="widget-header">
                <h6 class="widget-title">${widget.title}</h6>
                <div class="widget-actions">
                    <button class="btn btn-sm btn-link text-muted refresh-widget-btn" data-widget-id="${widget.id}" title="Refresh${isAISummary ? ' (uses cached if available)' : ''}">
                        <i class="fas fa-sync"></i>
                    </button>
                    ${isAISummary ? `
                    <button class="btn btn-sm btn-link text-warning force-refresh-widget-btn" data-widget-id="${widget.id}" title="Force Regenerate AI Summary">
                        <i class="fas fa-bolt"></i>
                    </button>
                    ` : ''}
                    <button class="btn btn-sm btn-link text-primary edit-widget-btn" data-widget-id="${widget.id}" title="Edit">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn btn-sm btn-link text-danger delete-widget-btn" data-widget-id="${widget.id}" title="Delete" style="display: ${editMode ? 'inline-block' : 'none'};">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
            <div class="widget-body" id="widget-body-${widget.id}">
                <div class="widget-loading">
                    <i class="fas fa-spinner fa-spin"></i> Loading...
                </div>
            </div>
        </div>
    `;
    
    gridStack.addWidget({
        w: widget.width,
        h: widget.height,
        x: widget.position_x,
        y: widget.position_y,
        content: widgetHtml,
        id: `widget-${widget.id}`
    });
}

async function loadAllWidgetData() {
    if (!currentDashboard || !currentDashboard.widgets) return;
    
    // Load all widgets in parallel so fast widgets don't wait for slow ones (like AI summary)
    const loadPromises = currentDashboard.widgets.map(widget => loadWidgetData(widget));
    await Promise.allSettled(loadPromises); // Use allSettled so one failure doesn't stop others
}

async function loadWidgetData(widget) {
    try {
        const response = await fetch(`/api/widgets/${widget.id}/data`);
        if (!response.ok) throw new Error('Failed to load widget data');
        
        const data = await response.json();
        renderWidget(widget, data);
        
    } catch (error) {
        console.error(`Error loading widget ${widget.id} data:`, error);
        const bodyEl = document.getElementById(`widget-body-${widget.id}`);
        if (bodyEl) {
            bodyEl.innerHTML = '<div class="text-danger text-center p-3">Error loading widget data</div>';
        }
    }
}

function renderWidget(widget, data) {
    const bodyEl = document.getElementById(`widget-body-${widget.id}`);
    if (!bodyEl) return;
    
    switch (widget.widget_type) {
        case 'list':
            renderListWidget(bodyEl, data);
            break;
        case 'chart':
            renderChart(bodyEl, widget.id, widget, data);
            break;
        case 'pie_chart':
            // Legacy support - convert to chart
            renderPieChart(bodyEl, widget.id, data);
            break;
        case 'line_chart':
            renderLineChart(bodyEl, widget.id, data);
            break;
        case 'stat_card':
            renderStatCard(bodyEl, data);
            break;
        case 'ai_summary':
            renderAISummary(bodyEl, data);
            break;
        default:
            bodyEl.innerHTML = '<div class="text-muted">Unknown widget type</div>';
    }
}

function renderListWidget(bodyEl, data) {
    if (data.error) {
        bodyEl.innerHTML = `<div class="text-danger">${data.error}</div>`;
        return;
    }
    
    if (!data.entries || data.entries.length === 0) {
        bodyEl.innerHTML = '<div class="text-muted text-center p-3">No entries found</div>';
        return;
    }
    
    let html = '';
    data.entries.forEach(entry => {
        html += `
            <div class="entry-list-item" data-entry-id="${entry.id}" style="cursor: pointer;">
                <div class="entry-title">${entry.title}</div>
                <div class="entry-meta">
                    <span class="badge bg-secondary">${entry.entry_type_label}</span>
                    <span class="badge bg-primary">${entry.status || 'Unknown'}</span>
                    ${entry.created_at ? `<small class="ms-2">${new Date(entry.created_at).toLocaleDateString()}</small>` : ''}
                </div>
            </div>
        `;
    });
    
    bodyEl.innerHTML = html;
    
    // Add click handlers for entry items
    bodyEl.querySelectorAll('.entry-list-item').forEach(item => {
        item.addEventListener('click', function() {
            const entryId = this.dataset.entryId;
            window.location.href = `/entry/${entryId}`;
        });
    });
}

function renderPieChart(bodyEl, widgetId, data) {
    if (data.error || !data.states || data.states.length === 0) {
        bodyEl.innerHTML = '<div class="text-muted text-center p-3">No data available</div>';
        return;
    }
    
    const canvasId = `chart-${widgetId}`;
    bodyEl.innerHTML = `<div class="chart-container"><canvas id="${canvasId}"></canvas></div>`;
    
    const ctx = document.getElementById(canvasId).getContext('2d');
    
    // Destroy existing chart if exists
    if (widgetCharts[widgetId]) {
        widgetCharts[widgetId].destroy();
    }
    
    widgetCharts[widgetId] = new Chart(ctx, {
        type: 'pie',
        data: {
            labels: data.states.map(s => s.name),
            datasets: [{
                data: data.states.map(s => s.count),
                backgroundColor: data.states.map(s => s.color),
                borderWidth: 2,
                borderColor: '#fff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 10,
                        usePointStyle: true
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.parsed || 0;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = ((value / total) * 100).toFixed(1);
                            return `${label}: ${value} (${percentage}%)`;
                        }
                    }
                }
            }
        }
    });
}

function renderChart(bodyEl, widgetId, widget, data) {
    if (data.error || !data.categories || data.categories.length === 0) {
        bodyEl.innerHTML = '<div class="text-muted text-center p-3">No data available</div>';
        return;
    }
    
    // Get chart configuration from widget config
    const config = typeof widget.config === 'string' ? JSON.parse(widget.config) : widget.config;
    const chartType = config.chart_type || 'pie';
    
    const canvasId = `chart-${widgetId}`;
    bodyEl.innerHTML = `<div class="chart-container"><canvas id="${canvasId}"></canvas></div>`;
    
    const ctx = document.getElementById(canvasId).getContext('2d');
    
    // Destroy existing chart if exists
    if (widgetCharts[widgetId]) {
        widgetCharts[widgetId].destroy();
    }
    
    // Check if this is a timeline chart
    const isTimeline = data.is_timeline || false;
    
    // Prepare data based on chart type
    const chartData = {
        labels: data.categories.map(c => c.name),
        datasets: [{
            label: data.attribute_label || 'Count',
            data: data.categories.map(c => c.count),
            backgroundColor: isTimeline 
                ? (chartType === 'line' ? 'rgba(75, 192, 192, 0.2)' : 'rgba(54, 162, 235, 0.8)')
                : data.categories.map(c => c.color || generateColor(c.name)),
            borderWidth: chartType === 'pie' || chartType === 'doughnut' || chartType === 'polarArea' ? 2 : 1,
            borderColor: isTimeline && chartType === 'line' 
                ? 'rgba(75, 192, 192, 1)' 
                : (chartType === 'pie' || chartType === 'doughnut' || chartType === 'polarArea' ? '#fff' : 'rgba(54, 162, 235, 1)'),
            tension: chartType === 'line' ? 0.4 : 0,
            fill: chartType === 'line' && isTimeline
        }]
    };
    
    // Configure options based on chart type
    const chartOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                position: chartType === 'bar' ? 'top' : 'bottom',
                labels: {
                    padding: 10,
                    usePointStyle: true
                }
            },
            tooltip: {
                callbacks: {
                    label: function(context) {
                        const label = context.label || '';
                        const value = context.parsed || context.parsed.y || 0;
                        const total = context.dataset.data.reduce((a, b) => a + b, 0);
                        const percentage = ((value / total) * 100).toFixed(1);
                        return `${label}: ${value} (${percentage}%)`;
                    }
                }
            }
        }
    };
    
    // Add scales for bar and line charts
    if (chartType === 'bar' || chartType === 'line') {
        chartOptions.scales = {
            y: {
                beginAtZero: true,
                ticks: {
                    precision: 0
                }
            }
        };
    }
    
    widgetCharts[widgetId] = new Chart(ctx, {
        type: chartType,
        data: chartData,
        options: chartOptions
    });
}

// Helper function to generate colors for categories
function generateColor(name) {
    // Simple hash function to generate consistent colors
    let hash = 0;
    for (let i = 0; i < name.length; i++) {
        hash = name.charCodeAt(i) + ((hash << 5) - hash);
    }
    const hue = hash % 360;
    return `hsl(${hue}, 70%, 60%)`;
}

function renderLineChart(bodyEl, widgetId, data) {
    if (data.error || !data.data_points || data.data_points.length === 0) {
        bodyEl.innerHTML = '<div class="text-muted text-center p-3">No sensor data available</div>';
        return;
    }
    
    const canvasId = `chart-${widgetId}`;
    bodyEl.innerHTML = `<div class="chart-container"><canvas id="${canvasId}"></canvas></div>`;
    
    const ctx = document.getElementById(canvasId).getContext('2d');
    
    // Destroy existing chart if exists
    if (widgetCharts[widgetId]) {
        widgetCharts[widgetId].destroy();
    }
    
    widgetCharts[widgetId] = new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.data_points.map(p => new Date(p.timestamp).toLocaleString()),
            datasets: [{
                label: data.sensor_type,
                data: data.data_points.map(p => p.value),
                borderColor: 'rgb(75, 192, 192)',
                backgroundColor: 'rgba(75, 192, 192, 0.2)',
                tension: 0.1,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    position: 'top'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `${context.dataset.label}: ${context.parsed.y}`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    display: true,
                    title: {
                        display: true,
                        text: 'Time'
                    }
                },
                y: {
                    display: true,
                    title: {
                        display: true,
                        text: 'Value'
                    }
                }
            }
        }
    });
}

function renderStatCard(bodyEl, data) {
    if (data.error) {
        bodyEl.innerHTML = `<div class="text-danger">${data.error}</div>`;
        return;
    }
    
    bodyEl.innerHTML = `
        <div class="stat-card">
            <div class="stat-value">${data.value || 0}</div>
            <div class="stat-label">${data.label || 'Total'}</div>
        </div>
    `;
}

function renderAISummary(bodyEl, data) {
    // Show loading state if summary is being generated
    if (data.loading || (!data.summary && !data.error && !data.available)) {
        bodyEl.innerHTML = `
            <div class="text-center p-4">
                <i class="fas fa-spinner fa-spin fa-2x mb-3"></i>
                <p class="text-muted">Generating AI summary...</p>
            </div>
        `;
        return;
    }
    
    if (!data.available) {
        bodyEl.innerHTML = `<div class="alert alert-warning">${data.summary || 'AI service is not available'}</div>`;
        return;
    }
    
    if (data.error) {
        bodyEl.innerHTML = `<div class="alert alert-danger">${data.error}</div>`;
        return;
    }
    
    if (!data.summary) {
        bodyEl.innerHTML = `<div class="alert alert-info">No summary available yet. Please refresh the widget.</div>`;
        return;
    }
    
    // Simple markdown-like formatting
    let summary = data.summary;
    
    // Convert markdown headers
    summary = summary.replace(/^### (.*$)/gim, '<h5>$1</h5>');
    summary = summary.replace(/^## (.*$)/gim, '<h4>$1</h4>');
    summary = summary.replace(/^# (.*$)/gim, '<h3>$1</h3>');
    
    // Convert bold
    summary = summary.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    
    // Convert lists
    summary = summary.replace(/^\* (.*$)/gim, '<li>$1</li>');
    summary = summary.replace(/^- (.*$)/gim, '<li>$1</li>');
    
    // Wrap consecutive <li> in <ul>
    summary = summary.replace(/(<li>.*<\/li>(\n)?)+/g, '<ul>$&</ul>');
    
    // Convert line breaks to paragraphs
    const lines = summary.split('\n');
    let html = '<div class="ai-summary" style="line-height: 1.6; font-size: 0.95rem;">';
    let inList = false;
    
    for (let line of lines) {
        line = line.trim();
        if (!line) continue;
        
        // Check if it's already formatted HTML
        if (line.match(/^<(h[3-5]|ul|li|strong)/)) {
            html += line + '\n';
        } else {
            html += `<p class="mb-2">${line}</p>`;
        }
    }
    
    html += '</div>';
    
    // Add metadata footer with cache status
    if (data.context || data.cached !== undefined) {
        html += `<div class="text-muted small mt-3 pt-2 border-top d-flex justify-content-between align-items-center">
            <div>
                <i class="fas fa-info-circle me-1"></i>
                ${data.context ? `Based on ${data.context.total_entries} entries across ${data.context.states} states` : ''}
                ${data.cached ? `<span class="badge bg-success ms-2"><i class="fas fa-check-circle me-1"></i>Cached (Today)</span>` : ''}
                ${data.generated_date ? `<span class="text-muted ms-2">Generated: ${data.generated_date}</span>` : ''}
            </div>
        </div>`;
    }
    
    bodyEl.innerHTML = html;
}

// ============================================================================
// Edit Mode
// ============================================================================

function toggleEditMode() {
    editMode = !editMode;
    const btn = document.getElementById('editModeBtn');
    
    if (editMode) {
        btn.classList.remove('btn-outline-primary');
        btn.classList.add('btn-primary');
        btn.innerHTML = '<i class="fas fa-save me-1"></i>Save Layout';
        
        // Enable drag and resize
        gridStack.enableMove(true);
        gridStack.enableResize(true);
        
        // Show delete buttons on all widgets
        document.querySelectorAll('.widget-actions button[title="Delete"]').forEach(btn => {
            btn.style.display = 'inline-block';
        });
        
    } else {
        btn.classList.remove('btn-primary');
        btn.classList.add('btn-outline-primary');
        btn.innerHTML = '<i class="fas fa-edit me-1"></i>Edit Layout';
        
        // Disable drag and resize
        gridStack.enableMove(false);
        gridStack.enableResize(false);
        
        // Hide delete buttons
        document.querySelectorAll('.widget-actions button[title="Delete"]').forEach(btn => {
            btn.style.display = 'none';
        });
        
        // Save positions
        saveWidgetPositions();
    }
}

async function saveWidgetPositions() {
    if (!currentDashboard) return;
    
    const widgets = gridStack.getGridItems();
    const updates = [];
    
    console.log(`Saving layout for ${widgets.length} widgets...`);
    
    for (const el of widgets) {
        // Debug: check what we're getting
        console.log('Element:', el);
        console.log('Element.id:', el.id);
        console.log('Element.getAttribute("id"):', el.getAttribute('id'));
        console.log('Element.getAttribute("gs-id"):', el.getAttribute('gs-id'));
        
        // Try different ways to get the ID
        let elementId = el.id || el.getAttribute('id') || el.getAttribute('gs-id');
        console.log('Using elementId:', elementId);
        
        if (!elementId || !elementId.includes('widget-')) {
            console.error('Cannot extract widget ID from element:', el);
            continue;
        }
        
        const widgetId = parseInt(elementId.replace('widget-', ''));
        const node = el.gridstackNode;
        
        if (isNaN(widgetId)) {
            console.error('Invalid widget ID extracted:', widgetId, 'from', elementId);
            continue;
        }
        
        const layoutData = {
            position_x: node.x,
            position_y: node.y,
            width: node.w,
            height: node.h
        };
        
        console.log(`Widget ${widgetId} layout:`, layoutData);
        
        updates.push(fetch(`/api/widgets/${widgetId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(layoutData)
        }));
    }
    
    try {
        await Promise.all(updates);
        console.log('All widget layouts saved successfully');
        showBanner('Layout saved successfully', 'success');
    } catch (error) {
        console.error('Error saving layout:', error);
        showBanner('Failed to save layout', 'error');
    }
}

// ============================================================================
// Refresh Functions
// ============================================================================

async function refreshWidget(widgetId, forceRefresh = false) {
    const widget = currentDashboard.widgets.find(w => w.id === widgetId);
    if (!widget) return;
    
    const bodyEl = document.getElementById(`widget-body-${widgetId}`);
    if (bodyEl) {
        if (widget.widget_type === 'ai_summary' && forceRefresh) {
            bodyEl.innerHTML = '<div class="widget-loading"><i class="fas fa-spinner fa-spin"></i> Regenerating AI summary...</div>';
        } else {
            bodyEl.innerHTML = '<div class="widget-loading"><i class="fas fa-spinner fa-spin"></i> Loading...</div>';
        }
    }
    
    // For AI summary widgets with force refresh, add query parameter
    if (widget.widget_type === 'ai_summary' && forceRefresh) {
        try {
            const response = await fetch(`/api/widgets/${widget.id}/data?force_refresh=true`);
            if (!response.ok) throw new Error('Failed to load widget data');
            
            const data = await response.json();
            renderWidget(widget, data);
            
            showBanner('AI summary regenerated', 'success');
        } catch (error) {
            console.error(`Error loading widget ${widget.id} data:`, error);
            if (bodyEl) {
                bodyEl.innerHTML = '<div class="text-danger text-center p-3">Error loading widget data</div>';
            }
        }
    } else {
        await loadWidgetData(widget);
    }
}

async function refreshAllWidgets() {
    if (!currentDashboard) return;
    
    const btn = document.getElementById('refreshAllBtn');
    const icon = btn.querySelector('i');
    icon.classList.add('fa-spin');
    
    await loadAllWidgetData();
    
    icon.classList.remove('fa-spin');
    showBanner('All widgets refreshed', 'success');
}

// ============================================================================
// Utility Functions
// ============================================================================

function clearCharts() {
    Object.values(widgetCharts).forEach(chart => {
        if (chart) chart.destroy();
    });
    widgetCharts = {};
}

function showNotification(message, type = 'info') {
    // Create a simple toast notification
    const toast = document.createElement('div');
    toast.className = `alert alert-${type === 'error' ? 'danger' : type} position-fixed top-0 end-0 m-3`;
    toast.style.zIndex = '9999';
    toast.textContent = message;
    
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.remove();
    }, 3000);
}
