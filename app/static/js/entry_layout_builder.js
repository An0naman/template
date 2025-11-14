// Entry Layout Builder JavaScript
// Manages the drag-and-drop interface for configuring entry type layouts

let gridStack = null;
let editMode = false;
let currentLayout = null;
let currentEntryType = null;
let selectedSection = null;
let availableSectionTypes = [];
let currentTabs = [];
let activeTab = 'main';

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
    'timeline': 'fa-stream',
    'drawio': 'fa-project-diagram'
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
        currentTabs = currentLayout.tabs || [];
        
        // Ensure active tab still exists, otherwise default to 'main'
        const tabExists = currentTabs.some(t => t.tab_id === activeTab);
        if (!tabExists && currentTabs.length > 0) {
            activeTab = currentTabs[0].tab_id || 'main';
        }
        
        // Render tabs UI
        renderTabs();
        
        // Render layout for active tab
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
    
    // Filter sections by active tab
    const sectionsInTab = currentLayout.sections.filter(s => (s.tab_id || 'main') === activeTab);
    
    // Add sections to grid
    sectionsInTab.forEach(section => {
        addSectionToGrid(section);
    });
}

// Add section to grid
function addSectionToGrid(sectionData) {
    const icon = SECTION_ICONS[sectionData.section_type] || 'fa-square';
    const visibilityClass = !sectionData.is_visible ? 'hidden-section' : '';
    
    // Count how many sections of this type exist (for instance numbering)
    const sameSectionTypes = currentLayout.sections.filter(s => 
        s.section_type === sectionData.section_type && 
        (s.tab_id || 'main') === (sectionData.tab_id || 'main')
    );
    const instanceNumber = sameSectionTypes.length > 1 ? 
        sameSectionTypes.findIndex(s => s.id === sectionData.id) + 1 : 
        null;
    
    const displayTitle = instanceNumber ? 
        `${sectionData.title} #${instanceNumber}` : 
        sectionData.title;
    
    const content = `
        <div class="layout-section ${visibilityClass}" data-section-id="${sectionData.id}">
            <div class="section-header">
                <div class="section-title">
                    <i class="fas ${icon}"></i>
                    <span>${displayTitle}</span>
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
    
    // Get default configuration for this section type
    const sectionTemplate = availableSectionTypes.find(s => s.section_type === sectionType);
    
    if (!sectionTemplate) {
        showNotification('Section type not found', 'error');
        return;
    }
    
    try {
        // Add section via API - add to currently active tab
        const response = await fetch(`/api/entry-layouts/${currentLayout.id}/sections`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                section_type: sectionType,
                title: sectionTemplate.default_title,
                width: sectionTemplate.default_width,
                height: sectionTemplate.default_height,
                is_collapsible: sectionTemplate.is_collapsible,
                config: sectionTemplate.default_config,
                tab_id: activeTab,  // Add to currently active tab
                tab_order: 999  // Add at the end
            })
        });
        
        if (!response.ok) {
            throw new Error('Failed to add section');
        }
        
        const result = await response.json();
        
        // Get the tab label for better notification
        const currentTabObj = currentTabs.find(t => t.tab_id === activeTab);
        const tabLabel = currentTabObj ? currentTabObj.tab_label : activeTab;
        
        showNotification(`Section "${sectionTemplate.default_title}" added to ${tabLabel} tab`, 'success');
        
        // Reload layout (which will stay on current tab)
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

// Render AI Assistant custom prompts configuration
function renderAiAssistantConfig(section) {
    const config = typeof section.config === 'string' ? JSON.parse(section.config || '{}') : section.config;
    
    return `
        <hr class="my-3">
        <div class="mb-3">
            <h6 class="text-warning">
                <i class="fas fa-magic me-2"></i>AI Chat Customization
            </h6>
            <small class="text-muted">Customize AI behavior for different chat modes</small>
        </div>
        
        <div class="mb-3">
            <label class="form-label small fw-bold">
                <i class="fas fa-comments me-1"></i>General Chat
            </label>
            <textarea class="form-control form-control-sm font-monospace" 
                      id="promptGeneralChat" rows="3" 
                      placeholder="e.g., 'You are a brewing expert. Focus on fermentation science and provide specific gravity calculations.'">${config.prompt_general_chat || ''}</textarea>
            <small class="text-muted">Default conversational mode</small>
        </div>
        
        <div class="mb-3">
            <label class="form-label small fw-bold">
                <i class="fas fa-file-text me-1"></i>Description Generation
            </label>
            <textarea class="form-control form-control-sm font-monospace" 
                      id="promptDescription" rows="3" 
                      placeholder="e.g., 'Focus on technical specifications, include relevant measurements and standards.'">${config.prompt_description || ''}</textarea>
            <small class="text-muted">When generating/improving descriptions</small>
        </div>
        
        <div class="mb-3">
            <label class="form-label small fw-bold">
                <i class="fas fa-sticky-note me-1"></i>Note Composer
            </label>
            <textarea class="form-control form-control-sm font-monospace" 
                      id="promptNoteComposer" rows="3" 
                      placeholder="e.g., 'Create detailed technical notes with step-by-step procedures.'">${config.prompt_note_composer || ''}</textarea>
            <small class="text-muted">When composing notes</small>
        </div>
        
        <div class="mb-3">
            <label class="form-label small fw-bold">
                <i class="fas fa-project-diagram me-1"></i>Diagram Editor
            </label>
            <textarea class="form-control form-control-sm font-monospace" 
                      id="promptDiagram" rows="3" 
                      placeholder="e.g., 'Create diagrams showing system architecture and data flow.'">${config.prompt_diagram || ''}</textarea>
            <small class="text-muted">When creating/editing diagrams</small>
        </div>
        
        <div class="mb-3">
            <label class="form-label small fw-bold">
                <i class="fas fa-calendar-check me-1"></i>Planning Mode
            </label>
            <textarea class="form-control form-control-sm font-monospace" 
                      id="promptPlanning" rows="3" 
                      placeholder="e.g., 'Plan milestones based on fermentation schedules and temperature curves.'">${config.prompt_planning || ''}</textarea>
            <small class="text-muted">When planning milestones</small>
        </div>
        
        <div class="alert alert-info alert-sm p-2 small">
            <i class="fas fa-info-circle me-1"></i>
            These prompts are combined with the base chat prompt to customize AI behavior for this specific section.
        </div>
    `;
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
            <label class="form-label">Tab</label>
            <select class="form-select form-select-sm" id="sectionTabSelect">
                ${currentTabs.map(tab => `
                    <option value="${tab.tab_id}" ${section.tab_id === tab.tab_id ? 'selected' : ''}>
                        ${tab.tab_label}
                    </option>
                `).join('')}
            </select>
            <small class="text-muted">Which tab this section appears on</small>
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
                    <small class="text-muted">Height (rows)</small>
                </div>
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
        
        ${section.section_type === 'ai_assistant' ? renderAiAssistantConfig(section) : ''}
        
        <div class="d-grid gap-2">
            <button class="btn btn-primary btn-sm" onclick="saveSectionProperties()">
                <i class="fas fa-save me-1"></i>Save Properties
            </button>
            <button class="btn btn-outline-secondary btn-sm" onclick="clearSectionSelection()">
                <i class="fas fa-times me-1"></i>Cancel
            </button>
        </div>
    `;
}

// Save section properties
async function saveSectionProperties() {
    if (!selectedSection) {
        return;
    }
    
    const updates = {
        title: document.getElementById('sectionTitleInput').value,
        tab_id: document.getElementById('sectionTabSelect').value,
        is_visible: document.getElementById('sectionVisibleSwitch').checked ? 1 : 0,
        is_collapsible: document.getElementById('sectionCollapsibleSwitch').checked ? 1 : 0,
        width: parseInt(document.getElementById('sectionWidthInput').value),
        height: parseInt(document.getElementById('sectionHeightInput').value)
    };
    
    if (selectedSection.is_collapsible) {
        updates.default_collapsed = document.getElementById('sectionCollapsedSwitch').checked ? 1 : 0;
    }
    
    // If AI Assistant section, save custom prompts in config
    if (selectedSection.section_type === 'ai_assistant') {
        const config = typeof selectedSection.config === 'string' ? 
            JSON.parse(selectedSection.config || '{}') : (selectedSection.config || {});
        
        config.prompt_general_chat = document.getElementById('promptGeneralChat')?.value || '';
        config.prompt_description = document.getElementById('promptDescription')?.value || '';
        config.prompt_note_composer = document.getElementById('promptNoteComposer')?.value || '';
        config.prompt_diagram = document.getElementById('promptDiagram')?.value || '';
        config.prompt_planning = document.getElementById('promptPlanning')?.value || '';
        
        updates.config = JSON.stringify(config);
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

// ============================================================================
// Tab Management Functions
// ============================================================================

// Render tabs UI
function renderTabs() {
    const tabsContainer = document.getElementById('tabsContainer');
    
    if (!tabsContainer || !currentTabs || currentTabs.length === 0) {
        return;
    }
    
    tabsContainer.innerHTML = currentTabs.map(tab => `
        <div class="tab-item ${tab.tab_id === activeTab ? 'active' : ''}" 
             onclick="switchTab('${tab.tab_id}')">
            <i class="fas ${tab.tab_icon || 'fa-folder'} me-2"></i>
            <span>${tab.tab_label}</span>
            ${tab.tab_id !== 'main' && editMode ? `
                <button class="btn btn-sm btn-link p-0 ms-2 text-danger" 
                        onclick="deleteTab(event, ${tab.id})" 
                        title="Delete tab">
                    <i class="fas fa-times"></i>
                </button>
            ` : ''}
        </div>
    `).join('');
    
    // Add "new tab" button in edit mode
    if (editMode) {
        tabsContainer.innerHTML += `
            <div class="tab-item tab-new" onclick="showCreateTabModal()">
                <i class="fas fa-plus me-2"></i>
                <span>New Tab</span>
            </div>
        `;
    }
}

// Switch active tab
function switchTab(tabId) {
    activeTab = tabId;
    renderTabs();
    renderLayout();
}

// Create new tab
async function createTab(tabData) {
    try {
        const response = await fetch(`/api/entry-layouts/${currentLayout.id}/tabs`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(tabData)
        });
        
        if (!response.ok) {
            throw new Error('Failed to create tab');
        }
        
        showNotification('Tab created successfully', 'success');
        
        // Reload layout
        await loadLayout(currentLayout.entry_type_id);
        
    } catch (error) {
        console.error('Error creating tab:', error);
        showNotification('Failed to create tab', 'error');
    }
}

// Delete tab
async function deleteTab(event, tabId) {
    event.stopPropagation();
    
    if (!confirm('Delete this tab? All sections in this tab will be moved to the Overview tab.')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/entry-layout-tabs/${tabId}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) {
            throw new Error('Failed to delete tab');
        }
        
        showNotification('Tab deleted successfully', 'success');
        
        // Switch to main tab if deleted tab was active
        const deletedTab = currentTabs.find(t => t.id === tabId);
        if (deletedTab && deletedTab.tab_id === activeTab) {
            activeTab = 'main';
        }
        
        // Reload layout
        await loadLayout(currentLayout.entry_type_id);
        
    } catch (error) {
        console.error('Error deleting tab:', error);
        showNotification('Failed to delete tab', 'error');
    }
}

// Show create tab modal
function showCreateTabModal() {
    const tabLabel = prompt('Enter tab name:');
    
    if (!tabLabel || tabLabel.trim() === '') {
        return;
    }
    
    // Generate tab_id from label
    const tabId = tabLabel.toLowerCase().replace(/[^a-z0-9]+/g, '_');
    
    // Icon selection (simplified for now)
    const iconOptions = {
        'sensors': 'fa-thermometer-half',
        'sensor': 'fa-thermometer-half',
        'history': 'fa-history',
        'timeline': 'fa-stream',
        'data': 'fa-database',
        'analytics': 'fa-chart-line',
        'details': 'fa-info-circle',
        'settings': 'fa-cog'
    };
    
    let icon = 'fa-folder';
    for (const [keyword, iconClass] of Object.entries(iconOptions)) {
        if (tabLabel.toLowerCase().includes(keyword)) {
            icon = iconClass;
            break;
        }
    }
    
    createTab({
        tab_id: tabId,
        tab_label: tabLabel,
        tab_icon: icon,
        display_order: currentTabs.length
    });
}
