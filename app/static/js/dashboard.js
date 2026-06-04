// Dashboard JavaScript
// Manages dashboard creation, widget rendering, and interactions

let currentDashboard = null;
let gridStack = null;
let editMode = false;
let availableSources = null;
let widgetCharts = {}; // Store Chart.js instances
let gitWidgetFilters = {}; // Per-widget filter state for git commits widgets
let gitWidgetFreshUnlinked = {}; // Per-widget fresh unlinked commits from direct repo fetch

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
    // Initialize GridStack with responsive breakpoints
    gridStack = GridStack.init({
        column: 12,
        cellHeight: 100,
        margin: 10,
        float: false,
        disableResize: true,
        disableDrag: true,
        animate: true,
        // Responsive: stack widgets on mobile
        columnOpts: {
            breakpoints: [
                {w: 768, c: 1, margin: 5}  // 1 column on screens <= 768px (mobile) with reduced margin
            ]
        }
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
        if (select) {
            select.innerHTML = '<option value="">Select saved search...</option>';
            availableSources.saved_searches.forEach(search => {
                const option = document.createElement('option');
                option.value = search.id;
                option.textContent = search.name;
                select.appendChild(option);
            });
        }
    }
    
    // Populate sensor types (only if sensor elements exist in DOM)
    if (availableSources && availableSources.sensor_types) {
        const select = document.getElementById('sensorTypeSelect');
        if (select) {  // Check if element exists before accessing
            select.innerHTML = '<option value="">Select sensor type...</option>';
            availableSources.sensor_types.forEach(sensorType => {
                const option = document.createElement('option');
                option.value = sensorType;
                option.textContent = sensorType;
                select.appendChild(option);
            });
        }
    }
    
    // Populate entry metrics for entry_data_chart widgets
    loadEdWidgetMetrics();

    // Populate git repositories (only if git integration is enabled)
    const gitRepoSelect = document.getElementById('gitRepositorySelect');
    if (gitRepoSelect) {
        try {
            const res = await fetch('/api/git/repositories');
            if (res.ok) {
                const data = await res.json();
                gitRepoSelect.innerHTML = '<option value="">Select repository...</option>';
                if (data.success && data.repositories) {
                    data.repositories.forEach(repo => {
                        const option = document.createElement('option');
                        option.value = repo.id;
                        option.textContent = repo.name;
                        gitRepoSelect.appendChild(option);
                    });
                }
            }
        } catch (e) {
            console.warn('Could not load git repositories:', e);
        }
    }
    
    // Populate git repositories for chart widget (only if git integration is enabled)
    const gitChartRepoSelect = document.getElementById('gitChartRepositorySelect');
    if (gitChartRepoSelect) {
        try {
            const res = await fetch('/api/git/repositories');
            if (res.ok) {
                const data = await res.json();
                gitChartRepoSelect.innerHTML = '<option value="">Select repository...</option>';
                if (data.success && data.repositories) {
                    data.repositories.forEach(repo => {
                        const option = document.createElement('option');
                        option.value = repo.id;
                        option.textContent = repo.name;
                        gitChartRepoSelect.appendChild(option);
                    });
                }
            }
        } catch (e) {
            console.warn('Could not load git repositories for chart:', e);
        }
    }
    
    const modal = new bootstrap.Modal(document.getElementById('addWidgetModal'));
    modal.show();
}

function handleEdXAxisTypeChange() {
    const xAxisType = document.getElementById('edWidgetXAxisType');
    const fieldRow = document.getElementById('edWidgetXAxisFieldRow');
    const timeRangeRow = document.getElementById('edWidgetTimeRangeRow');
    if (!xAxisType) return;
    if (fieldRow) fieldRow.style.display = xAxisType.value === 'entry_field' ? 'block' : 'none';
    if (timeRangeRow) timeRangeRow.style.display = xAxisType.value === 'recorded_at' ? 'block' : 'none';
}

function handleEdRelDefChange() {
    const pivotId = document.getElementById('edWidgetPivotId').value;
    const relDefId = document.getElementById('edWidgetRelDef').value;
    if (pivotId) loadEdWidgetColumns(pivotId, relDefId);
}

async function loadEdWidgetColumns(pivotEntryId, relDefId) {
    const container = document.getElementById('entryColumnCheckboxes');
    if (!container) return;
    container.innerHTML = '<span class="text-muted small">Loading columns\u2026</span>';
    try {
        // Resolve related entry type from a sample related entry
        const relResp = await fetch(`/api/entries/${encodeURIComponent(pivotEntryId)}/relationships`);
        if (!relResp.ok) throw new Error('Could not load relationships');
        const rels = await relResp.json();
        const filtered = relDefId
            ? rels.filter(r => String(r.definition_id) === String(relDefId))
            : rels;
        if (!filtered.length) {
            container.innerHTML = '<span class="text-muted small">No related entries found.</span>';
            return;
        }
        // Use the first related entry to discover the related entry type
        const sampleEntryId = filtered[0].related_entry_id;
        const entryResp = await fetch(`/api/entries/${encodeURIComponent(sampleEntryId)}`);
        if (!entryResp.ok) throw new Error('Could not load entry');
        const entryData = await entryResp.json();
        const typeId = entryData.entry_type_id ?? entryData.entry?.entry_type_id;
        if (!typeId) throw new Error('Could not determine entry type');
        const colResp = await fetch(`/api/entry-types/${encodeURIComponent(typeId)}/custom-columns`);
        if (!colResp.ok) throw new Error('Could not load custom columns');
        const assignments = await colResp.json();
        const numericCols = assignments.filter(a => a.column && a.column.column_type === 'number');
        if (!numericCols.length) {
            container.innerHTML = '<span class="text-muted small">No numeric custom columns for this entry type.</span>';
            return;
        }
        container.innerHTML = numericCols.map(a => `
            <div class="form-check">
                <input class="form-check-input" type="checkbox" value="${a.column.id}"
                       id="edCol_${a.column.id}" checked>
                <label class="form-check-label" for="edCol_${a.column.id}">
                    ${a.column.label}${a.column.unit ? ` <small class="text-muted">(${a.column.unit})</small>` : ''}
                </label>
            </div>
        `).join('');
    } catch (e) {
        container.innerHTML = `<span class="text-danger small">${e.message || 'Could not load columns.'}</span>`;
    }
}

let _edPivotSearchTimer = null;
async function handleEdPivotSearch(query) {
    clearTimeout(_edPivotSearchTimer);
    const results = document.getElementById('edWidgetPivotResults');
    if (!query || query.length < 2) { if (results) results.style.display = 'none'; return; }
    _edPivotSearchTimer = setTimeout(async () => {
        try {
            const resp = await fetch(`/api/entries?search=${encodeURIComponent(query)}`);
            if (!resp.ok) return;
            const entries = await resp.json();
            if (!results) return;
            if (!entries.length) {
                results.innerHTML = '<div class="list-group-item list-group-item-action disabled text-muted small">No entries found</div>';
            } else {
                results.innerHTML = entries.slice(0, 20).map(e =>
                    `<button type="button" class="list-group-item list-group-item-action small py-1"
                             onclick="selectEdPivotEntry(${e.id}, ${JSON.stringify(e.title).replace(/"/g, '&quot;')})">
                        <strong>${e.title}</strong>
                        <span class="text-muted ms-1">${e.entry_type_label || ''}</span>
                     </button>`
                ).join('');
            }
            results.style.display = 'block';
        } catch (e) { console.error('Pivot entry search failed', e); }
    }, 300);
}

async function selectEdPivotEntry(entryId, entryTitle) {
    document.getElementById('edWidgetPivotId').value = entryId;
    document.getElementById('edWidgetPivotSearch').value = entryTitle;
    const nameDiv = document.getElementById('edWidgetPivotName');
    if (nameDiv) nameDiv.textContent = `Selected: ${entryTitle}`;
    const results = document.getElementById('edWidgetPivotResults');
    if (results) results.style.display = 'none';

    // Load relationship definitions available for this entry
    const relDefSel = document.getElementById('edWidgetRelDef');
    if (!relDefSel) return;
    relDefSel.innerHTML = '<option value="">Loading…</option>';
    try {
        const resp = await fetch(`/api/entries/${entryId}/relationships`);
        if (!resp.ok) throw new Error();
        const rels = await resp.json();
        const defsMap = {};
        rels.forEach(r => {
            if (!defsMap[r.definition_id]) {
                defsMap[r.definition_id] = { id: r.definition_id, label: r.relationship_label || r.definition_name };
            }
        });
        const defs = Object.values(defsMap);
        if (!defs.length) {
            relDefSel.innerHTML = '<option value="">No relationships found for this entry</option>';
        } else {
            relDefSel.innerHTML = '<option value="">All related entries</option>'
                + defs.map(d => `<option value="${d.id}">${d.label}</option>`).join('');
        }
    } catch (e) {
        relDefSel.innerHTML = '<option value="">Could not load relationships</option>';
    }
}

function handleWidgetTypeChange(event) {
    // Handle both event object and direct calls
    const widgetType = event ? event.target.value : document.getElementById('widgetType').value;
    const dataSourceConfig = document.getElementById('dataSourceConfig');
    const savedSearchConfig = document.getElementById('savedSearchConfig');
    const sensorDataConfig = document.getElementById('sensorDataConfig');
    const entryDataConfig = document.getElementById('entryDataConfig');
    const aiSummaryPromptConfig = document.getElementById('aiSummaryPromptConfig');
    const chartConfig = document.getElementById('chartConfig');
    
    // Hide all configs (check if they exist first)
    if (savedSearchConfig) savedSearchConfig.style.display = 'none';
    if (sensorDataConfig) sensorDataConfig.style.display = 'none';
    if (entryDataConfig) entryDataConfig.style.display = 'none';
    if (dataSourceConfig) dataSourceConfig.style.display = 'none';
    if (aiSummaryPromptConfig) aiSummaryPromptConfig.style.display = 'none';
    if (chartConfig) chartConfig.style.display = 'none';
    
    // Show relevant config based on widget type
    if (widgetType === 'list' || widgetType === 'ai_summary' || widgetType === 'stat_card') {
        if (dataSourceConfig) dataSourceConfig.style.display = 'block';
        if (savedSearchConfig) savedSearchConfig.style.display = 'block';
        
        // Show AI prompt config only for AI summary widgets
        if (widgetType === 'ai_summary' && aiSummaryPromptConfig) {
            aiSummaryPromptConfig.style.display = 'block';
        }
    } else if (widgetType === 'entry_data_chart') {
        if (entryDataConfig) entryDataConfig.style.display = 'block';
    } else if (widgetType === 'line_chart') {
        if (dataSourceConfig) dataSourceConfig.style.display = 'block';
        if (savedSearchConfig) savedSearchConfig.style.display = 'block';
        if (sensorDataConfig) {
            sensorDataConfig.style.display = 'block';
        } else {
            showNotification('Sensor data is not enabled in this app', 'warning');
        }
    } else if (widgetType === 'chart') {
        if (chartConfig) chartConfig.style.display = 'block';
        if (dataSourceConfig) dataSourceConfig.style.display = 'block';
        if (savedSearchConfig) savedSearchConfig.style.display = 'block';
    } else if (widgetType === 'git_commits') {
        const gitCommitsConfig = document.getElementById('gitCommitsConfig');
        if (gitCommitsConfig) {
            gitCommitsConfig.style.display = 'block';
        } else {
            // Git integration is not enabled
            showNotification('Git integration is not enabled. Please enable it in System Settings to use git widgets.', 'warning');
        }
    } else if (widgetType === 'git_commits_chart') {
        const gitCommitsChartConfig = document.getElementById('gitCommitsChartConfig');
        if (gitCommitsChartConfig) {
            gitCommitsChartConfig.style.display = 'block';
        } else {
            // Git integration is not enabled
            showNotification('Git integration is not enabled. Please enable it in System Settings to use git widgets.', 'warning');
        }
    }
}

function handleChartAttributeChange(event) {
    const attribute = event ? event.target.value : document.getElementById('chartAttribute').value;
    const timelineOptions = document.getElementById('timelineOptions');
    const customColumnOptions = document.getElementById('customColumnOptions');

    if (timelineOptions) timelineOptions.style.display = attribute === 'date_timeline' ? 'block' : 'none';
    if (customColumnOptions) {
        customColumnOptions.style.display = attribute === 'custom_column' ? 'block' : 'none';
        if (attribute === 'custom_column') loadChartSelectColumns();
    }
}

async function loadChartSelectColumns() {
    const sel = document.getElementById('chartCustomColumnId');
    if (!sel) return;
    sel.innerHTML = '<option value="">Loading\u2026</option>';
    try {
        const resp = await fetch('/api/custom-columns');
        if (!resp.ok) throw new Error();
        const cols = await resp.json();
        const selectCols = cols.filter(c => c.column_type === 'select');
        if (!selectCols.length) {
            sel.innerHTML = '<option value="">No select-type columns found</option>';
            return;
        }
        sel.innerHTML = selectCols.map(c =>
            `<option value="${c.id}">${c.label}</option>`
        ).join('');
    } catch (e) {
        sel.innerHTML = '<option value="">Could not load columns</option>';
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

            // Save custom column id for custom_column attribute
            if (chartAttribute === 'custom_column') {
                const colId = document.getElementById('chartCustomColumnId').value;
                if (!colId) {
                    showNotification('Please select a custom column', 'warning');
                    return;
                }
                widgetData.config.custom_column_id = parseInt(colId);
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

    if (widgetType === 'entry_data_chart') {
        const pivotId = document.getElementById('edWidgetPivotId').value;
        if (!pivotId) {
            showNotification('Please select a pivot entry', 'warning');
            return;
        }
        const relDefId = document.getElementById('edWidgetRelDef').value;
        const checkedCols = document.querySelectorAll('#entryColumnCheckboxes input[type=checkbox]:checked');
        const columnIds = Array.from(checkedCols).map(cb => parseInt(cb.value));
        if (!columnIds.length) {
            showNotification('Please select at least one column to plot', 'warning');
            return;
        }
        const xAxisType = document.getElementById('edWidgetXAxisType').value;
        const xAxisField = document.getElementById('edWidgetXAxisField').value;
        widgetData.data_source_type = 'entry_relationship';
        widgetData.data_source_id = parseInt(pivotId);
        widgetData.config = {
            data_mode: 'columns',
            column_ids: columnIds,
            relationship_definition_id: relDefId ? parseInt(relDefId) : null,
            x_axis_type: xAxisType,
            x_axis_field: xAxisField,
        };
    }
    
    if (widgetType === 'git_commits') {
        const repoSelect = document.getElementById('gitRepositorySelect');
        if (!repoSelect) {
            showNotification('Git integration is not enabled in this app', 'error');
            return;
        }
        
        const repoId = repoSelect.value;
        const commitLimit = document.getElementById('gitCommitLimit').value;
        
        if (repoId) {
            widgetData.data_source_type = 'git_repository';
            widgetData.data_source_id = parseInt(repoId);
            widgetData.config = {
                commit_limit: parseInt(commitLimit)
            };
        } else {
            showNotification('Please select a repository or configure one in Settings', 'warning');
            return;
        }
    }
    
    if (widgetType === 'git_commits_chart') {
        const repoSelect = document.getElementById('gitChartRepositorySelect');
        if (!repoSelect) {
            showNotification('Git integration is not enabled in this app', 'error');
            return;
        }
        
        const repoId = repoSelect.value;
        const grouping = document.getElementById('gitChartGrouping').value;
        const timeRange = document.getElementById('gitChartTimeRange').value;
        
        if (repoId) {
            widgetData.data_source_type = 'git_repository';
            widgetData.data_source_id = parseInt(repoId);
            widgetData.config = {
                grouping: grouping,
                time_range: parseInt(timeRange)
            };
        } else {
            showNotification('Please select a repository or configure one in Settings', 'warning');
            return;
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
    
    // Populate git repositories dropdown
    const gitRepoSelect = document.getElementById('gitRepositorySelect');
    if (gitRepoSelect) {
        try {
            const res = await fetch('/api/git/repositories');
            const data = await res.json();
            gitRepoSelect.innerHTML = '<option value="">Select repository...</option>';
            if (data.success && data.repositories) {
                data.repositories.forEach(repo => {
                    const option = document.createElement('option');
                    option.value = repo.id;
                    option.textContent = repo.name;
                    gitRepoSelect.appendChild(option);
                });
            }
        } catch (e) {
            console.warn('Could not load git repositories during edit', e);
        }
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
    
    // For sensor line charts, set sensor config
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

    // For entry data charts, restore metric selection and axis config
    if (widget.widget_type === 'entry_data_chart' && widget.config) {
        try {
            const config = typeof widget.config === 'string' ? JSON.parse(widget.config) : widget.config;
            if (widget.data_source_id) {
                document.getElementById('edWidgetPivotId').value = widget.data_source_id;
                fetch(`/api/entries/${widget.data_source_id}`).then(r => r.ok ? r.json() : null).then(data => {
                    if (!data) return;
                    document.getElementById('edWidgetPivotSearch').value = data.title || '';
                    const nameDiv = document.getElementById('edWidgetPivotName');
                    if (nameDiv) nameDiv.textContent = `Selected: ${data.title}`;
                    selectEdPivotEntry(widget.data_source_id, data.title).then(() => {
                        if (config.relationship_definition_id) {
                            const relDef = document.getElementById('edWidgetRelDef');
                            if (relDef) relDef.value = config.relationship_definition_id;
                        }
                        loadEdWidgetColumns(widget.data_source_id, config.relationship_definition_id).then(() => {
                            if (config.column_ids && Array.isArray(config.column_ids)) {
                                document.querySelectorAll('#entryColumnCheckboxes input[type=checkbox]').forEach(cb => cb.checked = false);
                                config.column_ids.forEach(id => {
                                    const cb = document.querySelector(`#entryColumnCheckboxes input[value="${id}"]`);
                                    if (cb) cb.checked = true;
                                });
                            }
                        });
                    });
                });
            }
            if (config.x_axis_type) {
                const xAxisType = document.getElementById('edWidgetXAxisType');
                if (xAxisType) { xAxisType.value = config.x_axis_type; handleEdXAxisTypeChange(); }
            }
            if (config.x_axis_field) {
                const xAxisField = document.getElementById('edWidgetXAxisField');
                if (xAxisField) xAxisField.value = config.x_axis_field;
            }
        } catch (e) {
            console.error('Error parsing entry_data_chart widget config:', e);
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
                    // Trigger change to show/hide sub-panels
                    handleChartAttributeChange({ target: { value: config.chart_attribute } });
                }
            }
            if (config.custom_column_id) {
                // Load select columns then restore the saved selection
                loadChartSelectColumns().then(() => {
                    const colSel = document.getElementById('chartCustomColumnId');
                    if (colSel) colSel.value = config.custom_column_id;
                });
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
    
    // For git commits widgets, load repository configuration
    if (widget.widget_type === 'git_commits') {
        // Set the repository select
        if (widget.data_source_type === 'git_repository' && widget.data_source_id) {
            const gitRepoSelect = document.getElementById('gitRepositorySelect');
            if (gitRepoSelect) {
                gitRepoSelect.value = widget.data_source_id;
            }
        }
        
        // Set commit limit if available in config
        if (widget.config) {
            try {
                const config = typeof widget.config === 'string' ? JSON.parse(widget.config) : widget.config;
                if (config.commit_limit) {
                    const commitLimitSelect = document.getElementById('gitCommitLimit');
                    if (commitLimitSelect) {
                        commitLimitSelect.value = config.commit_limit;
                    }
                }
            } catch (e) {
                console.error('Error parsing widget config for git commits:', e);
            }
        }
    }
    
    // For git commits chart widgets, load repository configuration
    if (widget.widget_type === 'git_commits_chart') {
        // Load git repositories into chart select
        const gitChartRepoSelect = document.getElementById('gitChartRepositorySelect');
        if (gitChartRepoSelect) {
            try {
                const res = await fetch('/api/git/repositories');
                const data = await res.json();
                gitChartRepoSelect.innerHTML = '<option value="">Select repository...</option>';
                if (data.success && data.repositories) {
                    data.repositories.forEach(repo => {
                        const option = document.createElement('option');
                        option.value = repo.id;
                        option.textContent = repo.name;
                        gitChartRepoSelect.appendChild(option);
                    });
                }
            } catch (e) {
                console.warn('Could not load git repositories for chart during edit', e);
            }
            
            // Set the selected repository
            if (widget.data_source_type === 'git_repository' && widget.data_source_id) {
                gitChartRepoSelect.value = widget.data_source_id;
            }
        }
        
        // Set chart configuration if available
        if (widget.config) {
            try {
                const config = typeof widget.config === 'string' ? JSON.parse(widget.config) : widget.config;
                if (config.grouping) {
                    const groupingSelect = document.getElementById('gitChartGrouping');
                    if (groupingSelect) {
                        groupingSelect.value = config.grouping;
                    }
                }
                if (config.time_range) {
                    const timeRangeSelect = document.getElementById('gitChartTimeRange');
                    if (timeRangeSelect) {
                        timeRangeSelect.value = config.time_range;
                    }
                }
            } catch (e) {
                console.error('Error parsing widget config for git commits chart:', e);
            }
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
        case 'entry_data_chart':
            renderEntryDataChart(bodyEl, widget.id, data);
            break;
        case 'stat_card':
            renderStatCard(bodyEl, data);
            break;
        case 'ai_summary':
            renderAISummary(bodyEl, data);
            break;
        case 'git_commits':
            renderGitCommits(bodyEl, data, widget);
            break;
        case 'git_commits_chart':
            renderGitCommitsChart(bodyEl, widget.id, data, widget);
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

async function loadEdWidgetMetrics() {
    const container = document.getElementById('entryMetricCheckboxes');
    if (!container) return;
    container.innerHTML = '<span class="text-muted small">Loading metrics…</span>';
    try {
        const res = await fetch('/api/entry-metrics');
        if (!res.ok) throw new Error('Failed to load metrics');
        const metrics = await res.json();
        if (!metrics.length) {
            container.innerHTML = '<span class="text-muted small">No metrics defined yet.</span>';
            return;
        }
        container.innerHTML = metrics.map(m => `
            <div class="form-check">
                <input class="form-check-input" type="checkbox" value="${m.id}" id="edMetric_${m.id}">
                <label class="form-check-label d-flex align-items-center gap-1" for="edMetric_${m.id}">
                    ${m.color ? `<span style="display:inline-block;width:12px;height:12px;border-radius:50%;background:${m.color}"></span>` : ''}
                    ${m.label || m.name}${m.unit ? ` <small class="text-muted">(${m.unit})</small>` : ''}
                </label>
            </div>
        `).join('');
    } catch (e) {
        container.innerHTML = '<span class="text-danger small">Could not load metrics.</span>';
    }
}

function renderEntryDataChart(bodyEl, widgetId, data) {
    if (data.error) {
        bodyEl.innerHTML = `<div class="text-danger p-3">${data.error}</div>`;
        return;
    }
    if (!data.series || data.series.length === 0 || data.series.every(s => s.data_points.length === 0)) {
        bodyEl.innerHTML = '<div class="text-muted text-center p-3">No data available</div>';
        return;
    }

    const canvasId = `chart-${widgetId}`;
    bodyEl.innerHTML = `<div class="chart-container"><canvas id="${canvasId}"></canvas></div>`;
    const ctx = document.getElementById(canvasId).getContext('2d');

    if (widgetCharts[widgetId]) widgetCharts[widgetId].destroy();

    const isTimeSeries = data.x_axis_type === 'recorded_at';
    const isCategorySeries = data.x_axis_type === 'category';
    const defaultColors = ['#4bc0c0','#ff6384','#36a2eb','#ffce56','#9966ff','#ff9f40','#c9cbcf'];

    // Build a union of all x-labels for category/entry-field axes
    let xLabels;
    if (!isTimeSeries) {
        const labelSet = new Set();
        data.series.forEach(s => s.data_points.forEach(p => labelSet.add(p.x)));
        xLabels = Array.from(labelSet);
        // Sort labels (string sort is fine for entry names / date strings)
        xLabels.sort();
    }

    const datasets = data.series.map((s, idx) => ({
        label: s.unit ? `${s.label} (${s.unit})` : s.label,
        data: isTimeSeries
            ? s.data_points.map(p => ({ x: p.x, y: p.y }))
            : s.data_points.map(p => ({ x: p.x, y: p.y })),
        borderColor: s.color || defaultColors[idx % defaultColors.length],
        backgroundColor: (s.color || defaultColors[idx % defaultColors.length]) + '33',
        tension: 0.1,
        fill: false,
        pointRadius: 3
    }));

    widgetCharts[widgetId] = new Chart(ctx, {
        type: 'line',
        data: {
            labels: isTimeSeries ? undefined : xLabels,
            datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: datasets.length > 1, position: 'top' },
                tooltip: {
                    callbacks: {
                        label: ctx => `${ctx.dataset.label}: ${ctx.parsed.y}`
                    }
                }
            },
            scales: {
                x: {
                    type: isTimeSeries ? 'time' : 'category',
                    display: true,
                    title: { display: true, text: data.x_axis_label || (isTimeSeries ? 'Time' : 'Entry') }
                },
                y: { display: true, title: { display: true, text: 'Value' } }
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

function renderGitCommits(bodyEl, data, widget) {
    const widgetId = widget.id;

    if (data.error) {
        bodyEl.innerHTML = `<div class="alert alert-danger">${data.error}</div>`;
        return;
    }

    const filterMode = gitWidgetFilters[widgetId] || 'all';
    const allCommits = (data.commits || []).map(normalizeGitCommitRecord);
    const filteredCommits = filterMode === 'unlinked'
        ? ((gitWidgetFreshUnlinked[widgetId] || allCommits.filter(commit => !commit.entry)).map(normalizeGitCommitRecord))
        : allCommits;

    renderGitFilterInHeader(bodyEl, data, widget);
    let html = '';
    
    if (!allCommits || allCommits.length === 0) {
        bodyEl.innerHTML = `
            <div class="text-center p-4 text-muted">
                <i class="fab fa-git-alt fa-3x mb-3 opacity-50"></i>
                <p>No commits found for this repository</p>
                <small>The repository may be empty or not yet synced</small>
            </div>
        `;
        return;
    }

    if (filteredCommits.length === 0) {
        bodyEl.innerHTML = `
            <div class="text-center p-3 text-muted">
                No unlinked commits found.
            </div>
        `;
        return;
    }
    
    html += '<div class="git-commits-list">';
    filteredCommits.forEach(commit => {
        const date = new Date(commit.commit_date);
        const dateStr = date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
        const shortHash = commit.commit_hash.substring(0, 7);
        
        // Determine entry status
        let entryStatusBadge = '';
        let actionButton = '';
        
        if (commit.entry) {
            // Commit is linked to an entry
            entryStatusBadge = `
                <span class="badge bg-success ms-2" title="Linked to entry">
                    <i class="fas fa-link"></i> ${escapeHtml(commit.entry.title)}
                </span>
            `;
            actionButton = `
                <button class="btn btn-sm btn-outline-secondary view-entry-btn" 
                        data-entry-id="${commit.entry.id}" 
                        title="View entry">
                    <i class="fas fa-external-link-alt"></i>
                </button>
                <button class="btn btn-sm btn-outline-danger unlink-commit-btn" 
                        data-commit-hash="${commit.commit_hash}" 
                        title="Unlink from entry">
                    <i class="fas fa-unlink"></i>
                </button>
            `;
        } else {
            // Commit not linked - show pending status
            entryStatusBadge = `
                <span class="badge bg-warning text-dark ms-2" title="Not linked to entry">
                    <i class="fas fa-exclamation-triangle"></i> Pending
                </span>
            `;
            actionButton = `
                <button class="btn btn-sm btn-primary link-commit-btn" 
                        data-commit-hash="${commit.commit_hash}"
                        data-commit-message="${escapeHtml(commit.message)}"
                        data-default-entry-type="${commit.default_entry_type_id || ''}"
                        data-allowed-statuses="${commit.repo_allowed_statuses || ''}"
                        title="Link or create entry">
                    <i class="fas fa-plus"></i> Link Entry
                </button>
            `;
        }
        
        html += `
            <div class="commit-item p-2 mb-2 border-bottom">
                <div class="d-flex justify-content-between align-items-start">
                    <div class="flex-grow-1">
                        <div class="commit-message fw-semibold">
                            ${escapeHtml(commit.message)}
                            ${entryStatusBadge}
                        </div>
                        <div class="commit-meta text-muted small mt-1">
                            <span class="commit-hash badge bg-light text-dark font-monospace">${shortHash}</span>
                            <span class="mx-1">•</span>
                            <span class="commit-author">${escapeHtml(commit.author || 'Unknown')}</span>
                            <span class="mx-1">•</span>
                            <span class="commit-date">${dateStr}</span>
                        </div>
                    </div>
                    <div class="commit-actions d-flex gap-1 ms-2">
                        ${actionButton}
                    </div>
                </div>
            </div>
        `;
    });
    html += '</div>';
    
    bodyEl.innerHTML = html;

    // Attach event listeners
    attachGitCommitEventListeners(bodyEl);
}

function normalizeGitCommitRecord(commit) {
    if (!commit) return commit;
    if (commit.entry) return commit;
    if (commit.entry_id) {
        return {
            ...commit,
            entry: {
                id: commit.entry_id,
                title: commit.entry_title || `Entry #${commit.entry_id}`
            }
        };
    }
    return commit;
}

function renderGitFilterInHeader(bodyEl, data, widget) {
    const widgetId = widget.id;
    const filterMode = gitWidgetFilters[widgetId] || 'all';
    const widgetEl = bodyEl.closest('.dashboard-widget');
    const actionsEl = widgetEl ? widgetEl.querySelector('.widget-actions') : null;
    if (!actionsEl) return;

    const existing = actionsEl.querySelector(`#git-filter-group-${widgetId}`);
    if (existing) existing.remove();

    const filterContainer = document.createElement('div');
    filterContainer.className = 'btn-group btn-group-sm me-1';
    filterContainer.id = `git-filter-group-${widgetId}`;
    filterContainer.setAttribute('role', 'group');
    filterContainer.setAttribute('aria-label', 'Git commits filter');
    filterContainer.innerHTML = `
        <button type="button" class="btn ${filterMode === 'all' ? 'btn-primary' : 'btn-outline-primary'} git-header-filter-all" data-widget-id="${widgetId}">All</button>
        <button type="button" class="btn ${filterMode === 'unlinked' ? 'btn-primary' : 'btn-outline-primary'} git-header-filter-unlinked" data-widget-id="${widgetId}">Unlinked</button>
    `;

    const firstBtn = actionsEl.querySelector('button');
    if (firstBtn) {
        actionsEl.insertBefore(filterContainer, firstBtn);
    } else {
        actionsEl.appendChild(filterContainer);
    }

    const allBtn = filterContainer.querySelector('.git-header-filter-all');
    const unlinkedBtn = filterContainer.querySelector('.git-header-filter-unlinked');

    if (allBtn) {
        allBtn.addEventListener('click', function() {
            gitWidgetFilters[widgetId] = 'all';
            renderGitCommits(bodyEl, data, widget);
        });
    }

    if (unlinkedBtn) {
        unlinkedBtn.addEventListener('click', async function() {
            gitWidgetFilters[widgetId] = 'unlinked';
            bodyEl.innerHTML = '<div class="widget-loading"><i class="fas fa-spinner fa-spin"></i> Fetching fresh unlinked commits...</div>';
            gitWidgetFreshUnlinked[widgetId] = await fetchFreshUnlinkedCommits(widget);
            renderGitCommits(bodyEl, data, widget);
        });
    }
}

async function fetchFreshUnlinkedCommits(widget) {
    try {
        const baseLimit = (() => {
            try {
                const cfg = typeof widget.config === 'string' ? JSON.parse(widget.config) : (widget.config || {});
                return parseInt(cfg.commit_limit || 10, 10);
            } catch (e) {
                return 10;
            }
        })();

        const limit = Math.max(baseLimit, 200);
        const response = await fetch(`/api/git/repositories/${widget.data_source_id}/commits?limit=${limit}&_=${Date.now()}`);
        const result = await response.json();

        if (!response.ok || !result.success || !Array.isArray(result.commits)) {
            return [];
        }

        return result.commits
            .map(normalizeGitCommitRecord)
            .filter(commit => !commit.entry);
    } catch (error) {
        console.error('Failed to fetch fresh unlinked commits:', error);
        return [];
    }
}

function renderGitCommitsChart(bodyEl, widgetId, data, widget) {
    if (data.error) {
        bodyEl.innerHTML = `<div class="alert alert-danger">${data.error}</div>`;
        return;
    }
    
    if (!data.success || !data.timeline) {
        bodyEl.innerHTML = '<div class="text-muted text-center p-3">No commit data available</div>';
        return;
    }
    
    // Clear any existing chart
    if (widgetCharts[widgetId]) {
        widgetCharts[widgetId].destroy();
        delete widgetCharts[widgetId];
    }
    
    // Create canvas for chart
    bodyEl.innerHTML = '<div class="chart-container"><canvas id="chart-' + widgetId + '"></canvas></div>';
    const canvas = document.getElementById('chart-' + widgetId);
    const ctx = canvas.getContext('2d');
    
    // Prepare chart data
    const labels = data.timeline.map(point => point.period);
    const values = data.timeline.map(point => point.count);
    
    // Create chart
    widgetCharts[widgetId] = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Commits',
                data: values,
                backgroundColor: 'rgba(111, 66, 193, 0.7)',
                borderColor: 'rgba(111, 66, 193, 1)',
                borderWidth: 1,
                borderRadius: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                title: {
                    display: true,
                    text: `Commit Activity - ${data.repository_name || 'Repository'}`,
                    color: getComputedStyle(document.documentElement).getPropertyValue('--bs-body-color').trim() || '#212529'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `${context.parsed.y} commit${context.parsed.y !== 1 ? 's' : ''}`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1,
                        color: getComputedStyle(document.documentElement).getPropertyValue('--bs-body-color').trim() || '#6c757d'
                    },
                    grid: {
                        color: getComputedStyle(document.documentElement).getPropertyValue('--bs-border-color').trim() || '#dee2e6'
                    }
                },
                x: {
                    ticks: {
                        color: getComputedStyle(document.documentElement).getPropertyValue('--bs-body-color').trim() || '#6c757d'
                    },
                    grid: {
                        color: getComputedStyle(document.documentElement).getPropertyValue('--bs-border-color').trim() || '#dee2e6'
                    }
                }
            }
        }
    });
}

// Helper function to escape HTML
function escapeHtml(text) {
    if (!text) return '';
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, m => map[m]);
}

// Attach event listeners for git commit actions
function attachGitCommitEventListeners(container) {
    // Link commit button
    container.querySelectorAll('.link-commit-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const commitHash = this.dataset.commitHash;
            const commitMessage = this.dataset.commitMessage;
            const defaultEntryType = this.dataset.defaultEntryType;
            const allowedStatuses = this.dataset.allowedStatuses;
            showLinkCommitModal(commitHash, commitMessage, defaultEntryType, allowedStatuses);
        });
    });
    
    // Unlink commit button
    container.querySelectorAll('.unlink-commit-btn').forEach(btn => {
        btn.addEventListener('click', async function() {
            const commitHash = this.dataset.commitHash;
            if (confirm('Are you sure you want to unlink this commit from its entry?')) {
                await unlinkCommit(commitHash);
            }
        });
    });
    
    // View entry button
    container.querySelectorAll('.view-entry-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const entryId = this.dataset.entryId;
            window.location.href = `/entry/${entryId}`;
        });
    });
}

async function showLinkCommitModal(commitHash, commitMessage, defaultEntryType, allowedStatuses) {
    // Load available entry types
    const entryTypesResponse = await fetch('/api/entry_types');
    const entryTypes = await entryTypesResponse.json();
    
    // Build modal HTML
    const modalHtml = `
        <div class="modal fade" id="linkCommitModal" tabindex="-1">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">Link Commit to Entry</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <p class="text-muted">Commit: <code>${commitHash.substring(0, 7)}</code></p>
                        <p><strong>${escapeHtml(commitMessage)}</strong></p>
                        
                        <ul class="nav nav-tabs mb-3" role="tablist">
                            <li class="nav-item">
                                <button class="nav-link active" data-bs-toggle="tab" data-bs-target="#linkExisting">Link Existing</button>
                            </li>
                            <li class="nav-item">
                                <button class="nav-link" data-bs-toggle="tab" data-bs-target="#createNew">Create New</button>
                            </li>
                        </ul>
                        
                        <div class="tab-content">
                            <div class="tab-pane fade show active" id="linkExisting">
                                <div class="mb-3">
                                    <label class="form-label">Filter Entries (Optional)</label>
                                    <input type="text" class="form-control" id="entrySearchInput" placeholder="Type to filter the list below...">
                                </div>
                                <div id="entrySearchResults" class="list-group" style="max-height: 350px; overflow-y: auto;">
                                    <div class="text-muted p-2">Loading entries...</div>
                                </div>
                            </div>
                            
                            <div class="tab-pane fade" id="createNew">
                                <div class="mb-3">
                                    <label class="form-label">Entry Type</label>
                                    <select class="form-select" id="newEntryType">
                                        <option value="">Select entry type...</option>
                                        ${entryTypes.map(et => 
                                            `<option value="${et.id}" ${et.id == defaultEntryType ? 'selected' : ''}>${et.singular_label}</option>`
                                        ).join('')}
                                    </select>
                                </div>
                                <div class="mb-3">
                                    <label class="form-label">Entry Title</label>
                                    <input type="text" class="form-control" id="newEntryTitle" value="${escapeHtml(commitMessage).substring(0, 200)}">
                                </div>
                                <div class="mb-3">
                                    <label class="form-label">Initial Status</label>
                                    <select class="form-select" id="newEntryStatus">
                                        <option value="">Select status...</option>
                                    </select>
                                    <small class="text-muted">Select an entry type first to load available statuses</small>
                                </div>
                                <button class="btn btn-primary" id="createEntryBtn">
                                    <i class="fas fa-plus"></i> Create Entry
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Remove existing modal if present
    const existingModal = document.getElementById('linkCommitModal');
    if (existingModal) existingModal.remove();
    
    // Add modal to page
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    
    const modal = new bootstrap.Modal(document.getElementById('linkCommitModal'));
    modal.show();
    
    // Setup search functionality
    setupEntrySearch(commitHash, defaultEntryType, allowedStatuses);
    
    // Setup entry type change handler to load states
    const entryTypeSelect = document.getElementById('newEntryType');
    const statusSelect = document.getElementById('newEntryStatus');
    
    async function loadStatesForEntryType(entryTypeId) {
        if (!entryTypeId) {
            statusSelect.innerHTML = '<option value="">Select status...</option>';
            return;
        }
        
        try {
            const response = await fetch(`/api/entry_types/${entryTypeId}/states`);
            const states = await response.json();
            
            if (states.length === 0) {
                statusSelect.innerHTML = '<option value="">No statuses available</option>';
                return;
            }
            
            // Find default state
            const defaultState = states.find(s => s.is_default);
            
            statusSelect.innerHTML = states.map(state => 
                `<option value="${state.name}" ${state.is_default ? 'selected' : ''}>${state.name}</option>`
            ).join('');
            
        } catch (error) {
            console.error('Error loading states:', error);
            statusSelect.innerHTML = '<option value="">Error loading statuses</option>';
        }
    }
    
    entryTypeSelect.addEventListener('change', function() {
        loadStatesForEntryType(this.value);
    });
    
    // Load states for default entry type if set
    if (defaultEntryType) {
        loadStatesForEntryType(defaultEntryType);
    }
    
    // Setup create entry button
    document.getElementById('createEntryBtn').addEventListener('click', async function() {
        const entryTypeId = document.getElementById('newEntryType').value;
        const title = document.getElementById('newEntryTitle').value;
        const status = document.getElementById('newEntryStatus').value;
        
        if (!entryTypeId) {
            showNotification('Please select an entry type', 'warning');
            return;
        }
        
        if (!title.trim()) {
            showNotification('Please enter a title', 'warning');
            return;
        }
        
        await createEntryFromCommit(commitHash, entryTypeId, title, status);
        modal.hide();
    });
}

function setupEntrySearch(commitHash, defaultEntryType = '', allowedStatuses = '') {
    const searchInput = document.getElementById('entrySearchInput');
    const resultsDiv = document.getElementById('entrySearchResults');
    
    // Function to load and display entries
    async function loadEntries(query = '') {
        try {
            // Build query parameters
            let queryParams = 'limit=50'; // Show more entries when not searching
            
            if (query) {
                queryParams += `&q=${encodeURIComponent(query)}`;
            }
            if (defaultEntryType) {
                queryParams += `&entry_type_id=${defaultEntryType}`;
            }
            if (allowedStatuses) {
                queryParams += `&statuses=${encodeURIComponent(allowedStatuses)}`;
            }
            
            const response = await fetch(`/api/entries/search?${queryParams}`);
            const entries = await response.json();
            
            if (entries.length === 0) {
                if (query) {
                    resultsDiv.innerHTML = '<div class="text-muted p-2">No entries found matching your search</div>';
                } else if (defaultEntryType || allowedStatuses) {
                    resultsDiv.innerHTML = '<div class="text-muted p-2">No entries found matching the configured criteria</div>';
                } else {
                    resultsDiv.innerHTML = '<div class="text-muted p-2">No entries available</div>';
                }
                return;
            }
            
            resultsDiv.innerHTML = entries.map(entry => `
                <button class="list-group-item list-group-item-action link-to-entry-btn" 
                        data-entry-id="${entry.id}">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <strong>${escapeHtml(entry.title)}</strong>
                            <br>
                            <small class="text-muted">${entry.entry_type_label || 'Entry'} • ${entry.status || 'No status'}</small>
                        </div>
                        <span class="badge bg-primary">Link</span>
                    </div>
                </button>
            `).join('');
            
            // Attach click handlers
            resultsDiv.querySelectorAll('.link-to-entry-btn').forEach(btn => {
                btn.addEventListener('click', async function() {
                    const entryId = this.dataset.entryId;
                    await linkCommitToEntry(commitHash, entryId);
                    bootstrap.Modal.getInstance(document.getElementById('linkCommitModal')).hide();
                });
            });
            
        } catch (error) {
            console.error('Error searching entries:', error);
            resultsDiv.innerHTML = '<div class="text-danger p-2">Error loading entries</div>';
        }
    }
    
    // Load entries immediately on modal open
    resultsDiv.innerHTML = '<div class="text-muted p-2"><i class="fas fa-spinner fa-spin me-2"></i>Loading entries...</div>';
    loadEntries();
    
    // Setup search functionality
    let searchTimeout;
    searchInput.addEventListener('input', function() {
        clearTimeout(searchTimeout);
        const query = this.value.trim();
        
        searchTimeout = setTimeout(() => {
            loadEntries(query);
        }, 300);
    });
}

async function linkCommitToEntry(commitHash, entryId) {
    try {
        const response = await fetch(`/api/entries/${entryId}/git/link`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ commit_hash: commitHash })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showBanner('Commit linked to entry successfully', 'success');
            // Reload the current dashboard to refresh widget data
            if (currentDashboard) {
                await loadDashboard(currentDashboard.id);
            }
        } else {
            showBanner(result.error || 'Failed to link commit', 'error');
        }
    } catch (error) {
        console.error('Error linking commit:', error);
        showBanner('Failed to link commit', 'error');
    }
}

async function unlinkCommit(commitHash) {
    try {
        const response = await fetch(`/api/git/commits/${commitHash}/unlink`, {
            method: 'POST'
        });
        
        const result = await response.json();
        
        if (result.success) {
            showBanner('Commit unlinked successfully', 'success');
            // Reload the current dashboard to refresh widget data
            if (currentDashboard) {
                await loadDashboard(currentDashboard.id);
            }
        } else {
            showBanner(result.error || 'Failed to unlink commit', 'error');
        }
    } catch (error) {
        console.error('Error unlinking commit:', error);
        showBanner('Failed to unlink commit', 'error');
    }
}

async function createEntryFromCommit(commitHash, entryTypeId, title, status = null) {
    try {
        const requestBody = { 
            entry_type_id: entryTypeId,
            title: title
        };
        
        // Add status if provided
        if (status) {
            requestBody.status = status;
        }
        
        const response = await fetch(`/api/git/commits/${commitHash}/create-entry`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestBody)
        });
        
        const result = await response.json();
        
        if (result.success) {
            showBanner('Entry created and linked successfully', 'success');
            // Reload the current dashboard to refresh widget data
            if (currentDashboard) {
                await loadDashboard(currentDashboard.id);
            }
        } else {
            showBanner(result.error || 'Failed to create entry', 'error');
        }
    } catch (error) {
        console.error('Error creating entry:', error);
        showBanner('Failed to create entry', 'error');
    }
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

function showBanner(message, type = 'info') {
    // Create a banner notification at the top of the page
    const banner = document.createElement('div');
    banner.className = `alert alert-${type === 'error' ? 'danger' : type === 'warning' ? 'warning' : type === 'success' ? 'success' : 'info'} alert-dismissible fade show position-fixed start-50 translate-middle-x`;
    banner.style.cssText = 'top: 20px; z-index: 9999; min-width: 300px; max-width: 600px;';
    banner.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    document.body.appendChild(banner);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        banner.classList.remove('show');
        setTimeout(() => banner.remove(), 150);
    }, 5000);
}
