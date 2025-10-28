// Entry Layout Builder JavaScript
// Manages the drag-and-drop interface for configuring entry type layouts

let gridStack = null;
let editMode = false;
let currentLayout = null;
let currentEntryType = null;
let selectedSection = null;
let availableSectionTypes = [];

// Section type icons mapping
const SECTION_ICONS = {
    'header': 'fa-heading',
    'notes': 'fa-sticky-note',
    'relationships': 'fa-project-diagram',
    'labels': 'fa-tags',
    'sensors': 'fa-thermometer-half',
    'reminders': 'fa-bell',
    'ai_assistant': 'fa-robot',
    'attachments': 'fa-paperclip',
    'form_fields': 'fa-wpforms',
    'qr_code': 'fa-qrcode',
    'label_printing': 'fa-print',
    'relationship_opportunities': 'fa-share-alt',
    'timeline': 'fa-stream'
};

// Initialize layout builder
function initializeLayoutBuilder(entryTypeId, entryTypeData) {
    currentEntryType = entryTypeData;
    
    // Initialize GridStack
    gridStack = GridStack.init({
        column: 12,
        cellHeight: 80,
        margin: 10,
        float: false,
        disableResize: true,
        disableDrag: true,
        animate: true,
        handle: '.section-header'
    });
    
    // Load available section types
    loadAvailableSections();
    
    // Load current layout
    loadLayout(entryTypeId);
    
    // Setup event listeners
    setupEventListeners();
}

// Setup event listeners
function setupEventListeners() {
    document.getElementById('toggleEditBtn').addEventListener('click', toggleEditMode);
    document.getElementById('saveLayoutBtn').addEventListener('click', saveLayout);
    document.getElementById('resetLayoutBtn').addEventListener('click', resetLayout);
}

// Load available section types
async function loadAvailableSections() {
    try {
        const response = await fetch('/api/entry-layouts/available-sections');
        
        if (!response.ok) {
            throw new Error('Failed to load available sections');
        }
        
        availableSectionTypes = await response.json();
        renderSectionPalette();
        
    } catch (error) {
        console.error('Error loading available sections:', error);
        showNotification('Failed to load available sections', 'error');
    }
}

// Render section palette
function renderSectionPalette() {
    const palette = document.getElementById('sectionPalette');
    
    if (availableSectionTypes.length === 0) {
        palette.innerHTML = '<p class="text-muted small">No sections available</p>';
        return;
    }
    
    palette.innerHTML = availableSectionTypes.map(section => {
        const icon = SECTION_ICONS[section.section_type] || 'fa-square';
        return `
            <div class="palette-section-item" onclick="addSectionFromPalette('${section.section_type}')">
                <i class="fas ${icon}"></i>
                <span>${section.default_title}</span>
            </div>
        `;
    }).join('');
}

// Load layout for entry type
async function loadLayout(entryTypeId) {
    try {
        const response = await fetch(`/api/entry-types/${entryTypeId}/layout`);
        
        if (!response.ok) {
            throw new Error('Failed to load layout');
        }
        
        currentLayout = await response.json();
        renderLayout();
        
    } catch (error) {
        console.error('Error loading layout:', error);
        showNotification('Failed to load layout', 'error');
    }
}

// Render layout
function renderLayout() {
    if (!currentLayout || !currentLayout.sections) {
        return;
    }
    
    // Clear grid
    gridStack.removeAll();
    
    // Add sections to grid
    currentLayout.sections.forEach(section => {
        addSectionToGrid(section);
    });
}

// Add section to grid
function addSectionToGrid(sectionData) {
    const icon = SECTION_ICONS[sectionData.section_type] || 'fa-square';
    const visibilityClass = !sectionData.is_visible ? 'hidden-section' : '';
    
    const content = `
        <div class="layout-section ${visibilityClass}" data-section-id="${sectionData.id}">
            <div class="section-header">
                <div class="section-title">
                    <i class="fas ${icon}"></i>
                    <span>${sectionData.title}</span>
                    <span class="badge section-type-badge bg-secondary">${sectionData.section_type}</span>
                </div>
                <div class="section-actions">
                    <button class="btn btn-sm btn-outline-${sectionData.is_visible ? 'success' : 'secondary'}" 
                            onclick="toggleSectionVisibility(${sectionData.id})" 
                            title="${sectionData.is_visible ? 'Hide' : 'Show'} section">
                        <i class="fas fa-eye${sectionData.is_visible ? '' : '-slash'}"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-primary" 
                            onclick="selectSection(${sectionData.id})" 
                            title="Configure">
                        <i class="fas fa-cog"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-danger delete-section-btn" 
                            onclick="deleteSection(${sectionData.id})" 
                            title="Delete"
                            style="display: none;">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
            <div class="section-body">
                <div>
                    <i class="fas ${icon} fa-2x mb-2 opacity-25"></i>
                    <div class="small">${sectionData.section_type}</div>
                    <div class="small text-muted">${sectionData.width} × ${sectionData.height}</div>
                </div>
            </div>
        </div>
    `;
    
    gridStack.addWidget({
        x: sectionData.position_x,
        y: sectionData.position_y,
        w: sectionData.width,
        h: sectionData.height,
        content: content,
        id: `section-${sectionData.id}`
    });
}

// Toggle edit mode
function toggleEditMode() {
    editMode = !editMode;
    
    const toggleBtn = document.getElementById('toggleEditBtn');
    const saveBtn = document.getElementById('saveLayoutBtn');
    const indicator = document.getElementById('editModeIndicator');
    
    if (editMode) {
        // Enable editing
        gridStack.enableMove(true);
        gridStack.enableResize(true);
        toggleBtn.innerHTML = '<i class="fas fa-times me-1"></i>Cancel';
        toggleBtn.classList.remove('btn-outline-primary');
        toggleBtn.classList.add('btn-outline-danger');
        saveBtn.style.display = 'inline-block';
        indicator.style.display = 'block';
        
        // Show delete buttons
        document.querySelectorAll('.delete-section-btn').forEach(btn => {
            btn.style.display = 'inline-block';
        });
        
    } else {
        // Disable editing
        gridStack.enableMove(false);
        gridStack.enableResize(false);
        toggleBtn.innerHTML = '<i class="fas fa-edit me-1"></i>Edit Layout';
        toggleBtn.classList.remove('btn-outline-danger');
        toggleBtn.classList.add('btn-outline-primary');
        saveBtn.style.display = 'none';
        indicator.style.display = 'none';
        
        // Hide delete buttons
        document.querySelectorAll('.delete-section-btn').forEach(btn => {
            btn.style.display = 'none';
        });
        
        // Reload layout to discard changes
        loadLayout(currentLayout.entry_type_id);
    }
}

// Save layout
async function saveLayout() {
    try {
        if (!editMode) {
            showNotification('Enable edit mode first', 'warning');
            return;
        }
        
        // Collect current grid positions
        const sections = [];
        const items = gridStack.engine.nodes;
        
        items.forEach(item => {
            const sectionId = parseInt(item.el.querySelector('[data-section-id]').getAttribute('data-section-id'));
            
            console.log(`Section ${sectionId}: x=${item.x}, y=${item.y}, w=${item.w}, h=${item.h}`);
            
            sections.push({
                id: sectionId,
                position_x: item.x,
                position_y: item.y,
                width: item.w,
                height: item.h
            });
        });
        
        console.log('Saving sections:', sections);
        
        // Update section positions
        const response = await fetch(`/api/entry-layouts/${currentLayout.id}/sections/positions`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ sections: sections })
        });
        
        if (!response.ok) {
            throw new Error('Failed to save layout');
        }
        
        const result = await response.json();
        console.log('Save response:', result);
        
        showNotification('Layout saved successfully', 'success');
        
        // Exit edit mode
        toggleEditMode();
        
        // Reload layout
        await loadLayout(currentLayout.entry_type_id);
        
    } catch (error) {
        console.error('Error saving layout:', error);
        showNotification('Failed to save layout', 'error');
    }
}

// Reset layout to default
async function resetLayout() {
    if (!confirm('Are you sure you want to reset this layout to default? This cannot be undone.')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/entry-types/${currentLayout.entry_type_id}/layout/reset`, {
            method: 'POST'
        });
        
        if (!response.ok) {
            throw new Error('Failed to reset layout');
        }
        
        showNotification('Layout reset to default', 'success');
        
        // Reload layout
        await loadLayout(currentLayout.entry_type_id);
        
    } catch (error) {
        console.error('Error resetting layout:', error);
        showNotification('Failed to reset layout', 'error');
    }
}

// Add section from palette
async function addSectionFromPalette(sectionType) {
    if (!editMode) {
        showNotification('Enable edit mode first', 'warning');
        return;
    }
    
    // Check if section already exists
    const existingSection = currentLayout.sections.find(s => s.section_type === sectionType);
    if (existingSection) {
        showNotification('This section already exists in the layout', 'warning');
        return;
    }
    
    // Get default configuration for this section type
    const sectionTemplate = availableSectionTypes.find(s => s.section_type === sectionType);
    
    if (!sectionTemplate) {
        showNotification('Section type not found', 'error');
        return;
    }
    
    try {
        // Add section via API
        const response = await fetch(`/api/entry-layouts/${currentLayout.id}/sections`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                section_type: sectionType,
                title: sectionTemplate.default_title,
                width: sectionTemplate.default_width,
                height: sectionTemplate.default_height,
                is_collapsible: sectionTemplate.is_collapsible,
                config: sectionTemplate.default_config
            })
        });
        
        if (!response.ok) {
            throw new Error('Failed to add section');
        }
        
        const result = await response.json();
        
        showNotification(`Section "${sectionTemplate.default_title}" added`, 'success');
        
        // Reload layout
        await loadLayout(currentLayout.entry_type_id);
        
    } catch (error) {
        console.error('Error adding section:', error);
        showNotification('Failed to add section', 'error');
    }
}

// Toggle section visibility
async function toggleSectionVisibility(sectionId) {
    const section = currentLayout.sections.find(s => s.id === sectionId);
    
    if (!section) {
        return;
    }
    
    const newVisibility = !section.is_visible;
    
    try {
        const response = await fetch(`/api/entry-layouts/${currentLayout.id}/sections/${sectionId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ is_visible: newVisibility ? 1 : 0 })
        });
        
        if (!response.ok) {
            throw new Error('Failed to update section visibility');
        }
        
        showNotification(`Section ${newVisibility ? 'shown' : 'hidden'}`, 'success');
        
        // Reload layout
        await loadLayout(currentLayout.entry_type_id);
        
    } catch (error) {
        console.error('Error toggling visibility:', error);
        showNotification('Failed to update section visibility', 'error');
    }
}

// Delete section
async function deleteSection(sectionId) {
    if (!confirm('Are you sure you want to delete this section?')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/entry-layouts/${currentLayout.id}/sections/${sectionId}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) {
            throw new Error('Failed to delete section');
        }
        
        showNotification('Section deleted', 'success');
        
        // Reload layout
        await loadLayout(currentLayout.entry_type_id);
        
    } catch (error) {
        console.error('Error deleting section:', error);
        showNotification('Failed to delete section', 'error');
    }
}

// Select section for configuration
function selectSection(sectionId) {
    const section = currentLayout.sections.find(s => s.id === sectionId);
    
    if (!section) {
        return;
    }
    
    selectedSection = section;
    renderSectionProperties(section);
}

// Render section properties panel
function renderSectionProperties(section) {
    const panel = document.getElementById('propertiesContent');
    const icon = SECTION_ICONS[section.section_type] || 'fa-square';
    
    panel.innerHTML = `
        <div class="mb-3">
            <h6 class="d-flex align-items-center gap-2">
                <i class="fas ${icon}"></i>
                <span>${section.title}</span>
            </h6>
            <small class="text-muted">${section.section_type}</small>
        </div>
        
        <div class="mb-3">
            <label class="form-label">Section Title</label>
            <input type="text" class="form-control form-control-sm" 
                   id="sectionTitleInput" value="${section.title}">
        </div>
        
        <div class="mb-3">
            <label class="form-label">Position & Size</label>
            <div class="row g-2">
                <div class="col-6">
                    <input type="number" class="form-control form-control-sm" 
                           id="sectionWidthInput" value="${section.width}" min="1" max="12">
                    <small class="text-muted">Width (cols)</small>
                </div>
                <div class="col-6">
                    <input type="number" class="form-control form-control-sm" 
                           id="sectionHeightInput" value="${section.height}" min="1" max="20">
                    <small class="text-muted">Min Height (rows)</small>
                </div>
            </div>
            <div class="mt-2">
                <input type="number" class="form-control form-control-sm" 
                       id="sectionMaxHeightInput" value="${section.max_height || ''}" 
                       min="${section.height}" placeholder="No limit">
                <small class="text-muted">Max Height (rows) - Optional, must be ≥ min height</small>
            </div>
            <small class="text-muted">Drag corners or enter values</small>
        </div>
        
        <div class="mb-3">
            <div class="form-check form-switch">
                <input class="form-check-input" type="checkbox" 
                       id="sectionVisibleSwitch" ${section.is_visible ? 'checked' : ''}>
                <label class="form-check-label" for="sectionVisibleSwitch">
                    Visible
                </label>
            </div>
        </div>
        
        <div class="mb-3">
            <div class="form-check form-switch">
                <input class="form-check-input" type="checkbox" 
                       id="sectionCollapsibleSwitch" ${section.is_collapsible ? 'checked' : ''}>
                <label class="form-check-label" for="sectionCollapsibleSwitch">
                    Collapsible
                </label>
            </div>
        </div>
        
        ${section.is_collapsible ? `
        <div class="mb-3">
            <div class="form-check form-switch">
                <input class="form-check-input" type="checkbox" 
                       id="sectionCollapsedSwitch" ${section.default_collapsed ? 'checked' : ''}>
                <label class="form-check-label" for="sectionCollapsedSwitch">
                    Start Collapsed
                </label>
            </div>
        </div>
        ` : ''}
        
        <div class="d-grid gap-2">
            <button class="btn btn-primary btn-sm" onclick="saveSectionProperties()">
                <i class="fas fa-save me-1"></i>Save Properties
            </button>
            <button class="btn btn-outline-secondary btn-sm" onclick="clearSectionSelection()">
                <i class="fas fa-times me-1"></i>Cancel
            </button>
        </div>
    `;
    
    // Add event listener to update max height min value when height changes
    setTimeout(() => {
        const heightInput = document.getElementById('sectionHeightInput');
        const maxHeightInput = document.getElementById('sectionMaxHeightInput');
        if (heightInput && maxHeightInput) {
            heightInput.addEventListener('input', () => {
                maxHeightInput.min = heightInput.value;
            });
        }
    }, 0);
}

// Save section properties
async function saveSectionProperties() {
    if (!selectedSection) {
        return;
    }
    
    const updates = {
        title: document.getElementById('sectionTitleInput').value,
        is_visible: document.getElementById('sectionVisibleSwitch').checked ? 1 : 0,
        is_collapsible: document.getElementById('sectionCollapsibleSwitch').checked ? 1 : 0,
        width: parseInt(document.getElementById('sectionWidthInput').value),
        height: parseInt(document.getElementById('sectionHeightInput').value),
        max_height: document.getElementById('sectionMaxHeightInput').value ? 
                    parseInt(document.getElementById('sectionMaxHeightInput').value) : null
    };
    
    // Validate max_height is >= height
    if (updates.max_height && updates.max_height < updates.height) {
        alert('Max height must be greater than or equal to min height');
        return;
    }
    
    if (selectedSection.is_collapsible) {
        updates.default_collapsed = document.getElementById('sectionCollapsedSwitch').checked ? 1 : 0;
    }
    
    try {
        const response = await fetch(`/api/entry-layouts/${currentLayout.id}/sections/${selectedSection.id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(updates)
        });
        
        if (!response.ok) {
            throw new Error('Failed to save section properties');
        }
        
        // Update the grid item size if width or height changed
        if (updates.width || updates.height) {
            const gridItem = document.getElementById(`section-${selectedSection.id}`);
            if (gridItem) {
                gridStack.update(gridItem, {
                    w: updates.width,
                    h: updates.height
                });
            }
        }
        
        showNotification('Section properties saved', 'success');
        
        // Reload layout
        await loadLayout(currentLayout.entry_type_id);
        clearSectionSelection();
        
    } catch (error) {
        console.error('Error saving section properties:', error);
        showNotification('Failed to save section properties', 'error');
    }
}

// Clear section selection
function clearSectionSelection() {
    selectedSection = null;
    document.getElementById('propertiesContent').innerHTML = `
        <p class="text-muted text-center">
            <i class="fas fa-hand-pointer fa-2x mb-2 d-block"></i>
            Select a section to configure its properties
        </p>
    `;
}
