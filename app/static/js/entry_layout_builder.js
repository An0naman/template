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
let autoSaveTimer = null;
let sectionAutoSaveTimer = null;
let autoSaveInFlight = null;
let isRenderingLayout = false;
let hasPendingLayoutChanges = false;
const AUTO_SAVE_DELAY = 700;

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
    'drawio': 'fa-project-diagram',
    'photo_gallery': 'fa-images'
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

    gridStack.on('change', (_event, items) => {
        if (!editMode || isRenderingLayout || !Array.isArray(items) || items.length === 0) {
            return;
        }

        hasPendingLayoutChanges = true;
        scheduleLayoutAutoSave();
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

    isRenderingLayout = true;

    try {
        // Clear grid
        gridStack.removeAll();

        // Filter sections by active tab
        const sectionsInTab = currentLayout.sections.filter(s => (s.tab_id || 'main') === activeTab);

        // Add sections to grid
        sectionsInTab.forEach(section => {
            addSectionToGrid(section);
        });
    } finally {
        isRenderingLayout = false;
    }

    applyEditModeState();
}

function updateEditModeIndicator(message, icon = 'fa-edit') {
    const indicator = document.getElementById('editModeIndicator');
    if (!indicator) {
        return;
    }

    indicator.innerHTML = `<i class="fas ${icon} me-2"></i>${message}`;
}

function collectGridChanges() {
    const items = gridStack?.engine?.nodes || [];

    return items.map(item => ({
        id: parseInt(item.el.querySelector('[data-section-id]').getAttribute('data-section-id')),
        position_x: item.x,
        position_y: item.y,
        width: item.w,
        height: item.h
    }));
}

function applyEditModeState() {
    const toggleBtn = document.getElementById('toggleEditBtn');
    const saveBtn = document.getElementById('saveLayoutBtn');
    const indicator = document.getElementById('editModeIndicator');

    if (!toggleBtn || !saveBtn || !indicator || !gridStack) {
        return;
    }

    gridStack.enableMove(editMode);
    gridStack.enableResize(editMode);

    if (editMode) {
        toggleBtn.innerHTML = '<i class="fas fa-check me-1"></i>Done';
        toggleBtn.classList.remove('btn-outline-primary', 'btn-outline-danger');
        toggleBtn.classList.add('btn-outline-success');
        saveBtn.style.display = 'inline-block';
        if (!saveBtn.disabled) {
            saveBtn.innerHTML = '<i class="fas fa-save me-1"></i>Save Now';
        }
        indicator.style.display = 'block';
        updateEditModeIndicator(
            (hasPendingLayoutChanges || autoSaveInFlight)
                ? 'Edit Mode Active • saving changes automatically…'
                : 'Edit Mode Active • changes auto-save',
            (hasPendingLayoutChanges || autoSaveInFlight) ? 'fa-spinner fa-spin' : 'fa-edit'
        );
    } else {
        toggleBtn.innerHTML = '<i class="fas fa-edit me-1"></i>Edit Layout';
        toggleBtn.classList.remove('btn-outline-success', 'btn-outline-danger');
        toggleBtn.classList.add('btn-outline-primary');
        saveBtn.style.display = 'none';
        saveBtn.disabled = false;
        saveBtn.innerHTML = '<i class="fas fa-save me-1"></i>Save Now';
        indicator.style.display = 'none';
    }

    document.querySelectorAll('.delete-section-btn').forEach(btn => {
        btn.style.display = editMode ? 'inline-block' : 'none';
    });
}

function applySectionUpdatesLocally(sectionId, updates) {
    if (!currentLayout?.sections) {
        return null;
    }

    const normalizedUpdates = { ...updates };

    if (typeof normalizedUpdates.is_visible !== 'undefined') {
        normalizedUpdates.is_visible = Boolean(Number(normalizedUpdates.is_visible));
    }
    if (typeof normalizedUpdates.is_collapsible !== 'undefined') {
        normalizedUpdates.is_collapsible = Boolean(Number(normalizedUpdates.is_collapsible));
    }
    if (typeof normalizedUpdates.default_collapsed !== 'undefined') {
        normalizedUpdates.default_collapsed = Boolean(Number(normalizedUpdates.default_collapsed));
    }
    if (typeof normalizedUpdates.config === 'string') {
        try {
            normalizedUpdates.config = JSON.parse(normalizedUpdates.config);
        } catch {
            // Leave as-is if not valid JSON
        }
    }

    const sectionIndex = currentLayout.sections.findIndex(s => s.id === sectionId);
    if (sectionIndex === -1) {
        return null;
    }

    currentLayout.sections[sectionIndex] = {
        ...currentLayout.sections[sectionIndex],
        ...normalizedUpdates
    };

    if (selectedSection?.id === sectionId) {
        selectedSection = currentLayout.sections[sectionIndex];
    }

    return currentLayout.sections[sectionIndex];
}

function scheduleLayoutAutoSave() {
    if (!editMode) {
        return;
    }

    updateEditModeIndicator('Edit Mode Active • saving changes automatically…', 'fa-spinner fa-spin');

    if (autoSaveTimer) {
        clearTimeout(autoSaveTimer);
    }

    autoSaveTimer = setTimeout(() => {
        saveLayout({ silent: true });
    }, AUTO_SAVE_DELAY);
}

function scheduleSectionPropertyAutoSave() {
    if (!editMode || !selectedSection) {
        return;
    }

    if (sectionAutoSaveTimer) {
        clearTimeout(sectionAutoSaveTimer);
    }

    sectionAutoSaveTimer = setTimeout(() => {
        saveSectionProperties({ silent: true, keepSelection: true });
    }, 250);
}

function attachPropertyAutosave(section) {
    const fieldIds = [
        'sectionTitleInput',
        'sectionTabSelect',
        'sectionWidthInput',
        'sectionHeightInput',
        'sectionVisibleSwitch',
        'sectionCollapsibleSwitch',
        'sectionCollapsedSwitch',
        'promptGeneralChat',
        'promptDescription',
        'promptNoteComposer',
        'promptDiagram',
        'promptPlanning',
        'photoGalleryImages',
        'photoGalleryInterval',
        'photoGalleryFitMode',
        'photoGalleryAutoplay',
        'photoGalleryPauseOnHover',
        'photoGalleryShowControls',
        'photoGalleryShowIndicators'
    ];

    fieldIds.forEach(fieldId => {
        const element = document.getElementById(fieldId);
        if (!element) {
            return;
        }

        element.addEventListener('change', () => {
            if (selectedSection?.id === section.id) {
                scheduleSectionPropertyAutoSave();
            }
        });
    });
}

function renderPhotoGalleryConfig(section) {
    const config = typeof section.config === 'string' ? JSON.parse(section.config || '{}') : (section.config || {});
    const imageUrls = Array.isArray(config.image_urls) ? config.image_urls : [];
    const interval = Number(config.rotation_interval_seconds || 5);
    const fitMode = config.fit_mode || 'cover';

    return `
        <hr class="my-3">
        <div class="mb-3">
            <h6 class="text-primary">
                <i class="fas fa-images me-2"></i>Gallery Configuration
            </h6>
            <small class="text-muted">Add nominated image URLs or upload paths and configure rotation.</small>
        </div>

        <div class="mb-3">
            <label class="form-label small fw-bold" for="photoGalleryImages">
                <i class="fas fa-list me-1"></i>Nominated Images
            </label>
            <textarea class="form-control form-control-sm font-monospace"
                      id="photoGalleryImages" rows="5"
                      placeholder="One image URL/path per line\nExample:\n/static/uploads/note_12_example.jpg\nhttps://example.com/gallery/photo1.jpg">${imageUrls.join('\n')}</textarea>
            <small class="text-muted">Supports full URLs, <code>/static/...</code>, or <code>uploads/...</code> paths.</small>
        </div>

        <div class="mb-3">
            <label class="form-label small fw-bold" for="photoGalleryInterval">Rotation Interval (seconds)</label>
            <input type="number" class="form-control form-control-sm" id="photoGalleryInterval" min="1" max="120" value="${interval}">
        </div>

        <div class="mb-3">
            <label class="form-label small fw-bold" for="photoGalleryFitMode">Image Fit Mode</label>
            <select class="form-select form-select-sm" id="photoGalleryFitMode">
                <option value="cover" ${fitMode === 'cover' ? 'selected' : ''}>Cover</option>
                <option value="contain" ${fitMode === 'contain' ? 'selected' : ''}>Contain</option>
            </select>
        </div>

        <div class="form-check form-switch mb-2">
            <input class="form-check-input" type="checkbox" id="photoGalleryAutoplay" ${config.autoplay !== false ? 'checked' : ''}>
            <label class="form-check-label" for="photoGalleryAutoplay">Autoplay</label>
        </div>
        <div class="form-check form-switch mb-2">
            <input class="form-check-input" type="checkbox" id="photoGalleryPauseOnHover" ${config.pause_on_hover !== false ? 'checked' : ''}>
            <label class="form-check-label" for="photoGalleryPauseOnHover">Pause on Hover</label>
        </div>
        <div class="form-check form-switch mb-2">
            <input class="form-check-input" type="checkbox" id="photoGalleryShowControls" ${config.show_controls !== false ? 'checked' : ''}>
            <label class="form-check-label" for="photoGalleryShowControls">Show Prev/Next Controls</label>
        </div>
        <div class="form-check form-switch mb-3">
            <input class="form-check-input" type="checkbox" id="photoGalleryShowIndicators" ${config.show_indicators !== false ? 'checked' : ''}>
            <label class="form-check-label" for="photoGalleryShowIndicators">Show Slide Indicators</label>
        </div>
    `;
}

// Render header section configuration
function renderHeaderConfig(section) {
    const config = typeof section.config === 'string' ? JSON.parse(section.config || '{}') : (section.config || {});
    const showDates = config.show_dates !== false;
    const showStatus = config.show_status !== false;
    const showDescription = config.show_description !== false;

    return `
        <hr class="my-3">
        <div class="mb-3">
            <h6 class="text-info">
                <i class="fas fa-sliders-h me-2"></i>Header Display Options
            </h6>
            <small class="text-muted">Choose which fields to show in the header section</small>
        </div>

        <div class="form-check form-switch mb-2">
            <input class="form-check-input" type="checkbox" id="headerShowDates" ${showDates ? 'checked' : ''}>
            <label class="form-check-label" for="headerShowDates">
                <i class="fas fa-calendar me-1"></i>Show Dates (Created, Commenced)
            </label>
        </div>
        <div class="form-check form-switch mb-2">
            <input class="form-check-input" type="checkbox" id="headerShowStatus" ${showStatus ? 'checked' : ''}>
            <label class="form-check-label" for="headerShowStatus">
                <i class="fas fa-flag me-1"></i>Show Status
            </label>
        </div>
        <div class="form-check form-switch mb-3">
            <input class="form-check-input" type="checkbox" id="headerShowDescription" ${showDescription ? 'checked' : ''}>
            <label class="form-check-label" for="headerShowDescription">
                <i class="fas fa-align-left me-1"></i>Show Description
            </label>
        </div>
    `;
}

// Render custom fields section configuration
function renderCustomFieldsConfig(section) {
    const config = typeof section.config === 'string' ? JSON.parse(section.config || '{}') : (section.config || {});
    const columnCount = config.column_count || 2;
    const hiddenFields = config.hidden_fields || [];
    const fieldOrder = config.field_order || [];

    let fieldListHtml = '';
    
    // Get custom column values from the current entry context if available
    // This is a simplified version - in production you'd fetch this data
    fieldListHtml = `
        <div class="card card-sm border-secondary mb-3">
            <div class="card-body p-2">
                <small class="text-muted d-block mb-2">
                    <i class="fas fa-info-circle me-1"></i>
                    Field visibility and order can be configured when viewing an entry with custom fields.
                </small>
                <small class="text-secondary">
                    Right-click a field in the entry view to configure its visibility.
                </small>
            </div>
        </div>
    `;

    return `
        <hr class="my-3">
        <div class="mb-3">
            <h6 class="text-success">
                <i class="fas fa-columns me-2"></i>Custom Fields Layout
            </h6>
            <small class="text-muted">Configure the layout and display of custom fields</small>
        </div>

        <div class="mb-3">
            <label for="customFieldsColumnCount" class="form-label small">
                <i class="fas fa-th me-1"></i>Number of Columns
            </label>
            <select class="form-select form-select-sm" id="customFieldsColumnCount">
                <option value="1" ${columnCount === 1 ? 'selected' : ''}>1 Column (Full Width)</option>
                <option value="2" ${columnCount === 2 ? 'selected' : ''}>2 Columns</option>
                <option value="3" ${columnCount === 3 ? 'selected' : ''}>3 Columns</option>
                <option value="4" ${columnCount === 4 ? 'selected' : ''}>4 Columns</option>
                <option value="6" ${columnCount === 6 ? 'selected' : ''}>6 Columns (Compact)</option>
            </select>
            <small class="text-muted d-block mt-1">Choose how many columns to display custom fields across</small>
        </div>

        <div class="form-check form-switch mb-2">
            <input class="form-check-input" type="checkbox" id="customFieldsAlwaysEdit" ${config.always_editable !== false ? 'checked' : ''}>
            <label class="form-check-label" for="customFieldsAlwaysEdit">
                <i class="fas fa-pen me-1"></i>Always Editable
            </label>
            <small class="text-muted d-block ms-4">Fields are editable without needing to enter edit mode</small>
        </div>

        <div class="form-check form-switch mb-3">
            <input class="form-check-input" type="checkbox" id="customFieldsShowLabels" ${config.show_labels !== false ? 'checked' : ''}>
            <label class="form-check-label" for="customFieldsShowLabels">
                <i class="fas fa-tag me-1"></i>Show Field Labels
            </label>
            <small class="text-muted d-block ms-4">Display field names/labels above inputs</small>
        </div>

        <div class="alert alert-info alert-sm p-2 small">
            <i class="fas fa-info-circle me-1"></i>
            These settings control the appearance and behavior of assigned custom columns in this section.
        </div>
    `;
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
                            style="display: ${editMode ? 'inline-block' : 'none'};">
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
async function toggleEditMode() {
    if (!editMode) {
        editMode = true;
        applyEditModeState();
        return;
    }

    if (autoSaveTimer) {
        clearTimeout(autoSaveTimer);
        autoSaveTimer = null;
    }

    if (sectionAutoSaveTimer) {
        clearTimeout(sectionAutoSaveTimer);
        sectionAutoSaveTimer = null;
        await saveSectionProperties({ silent: true, keepSelection: true });
    }

    await saveLayout({ silent: true });

    editMode = false;
    applyEditModeState();
}

// Save layout
async function saveLayout(options = {}) {
    const { silent = false } = options;

    try {
        if (!editMode && !silent) {
            showNotification('Enable edit mode first', 'warning');
            return false;
        }

        if (autoSaveInFlight) {
            await autoSaveInFlight;
            return true;
        }

        const sections = collectGridChanges();
        if (sections.length === 0) {
            hasPendingLayoutChanges = false;
            return true;
        }

        const saveBtn = document.getElementById('saveLayoutBtn');
        if (saveBtn && editMode) {
            saveBtn.disabled = true;
            saveBtn.innerHTML = `<i class="fas fa-spinner fa-spin me-1"></i>${silent ? 'Saving…' : 'Saving Now'}`;
        }

        autoSaveInFlight = fetch(`/api/entry-layouts/${currentLayout.id}/sections/positions`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ sections })
        });

        const response = await autoSaveInFlight;

        if (!response.ok) {
            throw new Error('Failed to save layout');
        }

        sections.forEach(section => applySectionUpdatesLocally(section.id, section));
        hasPendingLayoutChanges = false;

        if (editMode) {
            updateEditModeIndicator('Edit Mode Active • changes auto-save');
        }

        if (!silent) {
            showBanner('Layout saved successfully', 'success');
        }

        return true;
    } catch (error) {
        console.error('Error saving layout:', error);
        showBanner('Failed to save layout', 'error');
        return false;
    } finally {
        autoSaveInFlight = null;
        const saveBtn = document.getElementById('saveLayoutBtn');
        if (saveBtn && editMode) {
            saveBtn.disabled = false;
            saveBtn.innerHTML = '<i class="fas fa-save me-1"></i>Save Now';
        }
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
        
        showBanner('Layout reset to default', 'success');
        
        // Reload layout
        await loadLayout(currentLayout.entry_type_id);
        
    } catch (error) {
        console.error('Error resetting layout:', error);
        showBanner('Failed to reset layout', 'error');
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
        
        showBanner(`Section "${sectionTemplate.default_title}" added to ${tabLabel} tab`, 'success');
        
        // Reload layout (which will stay on current tab)
        await loadLayout(currentLayout.entry_type_id);
        
    } catch (error) {
        console.error('Error adding section:', error);
        showBanner('Failed to add section', 'error');
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
        
        showBanner(`Section ${newVisibility ? 'shown' : 'hidden'}`, 'success');
        
        // Reload layout
        await loadLayout(currentLayout.entry_type_id);
        
    } catch (error) {
        console.error('Error toggling visibility:', error);
        showBanner('Failed to update section visibility', 'error');
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
        
        showBanner('Section deleted', 'success');

        if (selectedSection?.id === sectionId) {
            clearSectionSelection();
        }
        
        // Reload layout while preserving edit mode
        await loadLayout(currentLayout.entry_type_id);
        
    } catch (error) {
        console.error('Error deleting section:', error);
        showBanner('Failed to delete section', 'error');
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
            <div class="small text-success mt-2">
                <i class="fas fa-wand-magic-sparkles me-1"></i>Changes auto-save when you update a field.
            </div>
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
        
        ${section.section_type === 'header' ? renderHeaderConfig(section) : ''}
        ${section.section_type === 'form_fields' ? renderCustomFieldsConfig(section) : ''}
        ${section.section_type === 'ai_assistant' ? renderAiAssistantConfig(section) : ''}
        ${section.section_type === 'photo_gallery' ? renderPhotoGalleryConfig(section) : ''}
        
        <div class="d-grid gap-2">
            <button class="btn btn-primary btn-sm" onclick="saveSectionProperties()">
                <i class="fas fa-save me-1"></i>Save Now
            </button>
            <button class="btn btn-outline-secondary btn-sm" onclick="clearSectionSelection()">
                <i class="fas fa-times me-1"></i>Close
            </button>
        </div>
    `;

    attachPropertyAutosave(section);
}

// Save section properties
async function saveSectionProperties(options = {}) {
    if (!selectedSection) {
        return;
    }

    const { silent = false, keepSelection = true } = options;
    const originalSection = { ...selectedSection };

    const updates = {
        title: document.getElementById('sectionTitleInput').value,
        tab_id: document.getElementById('sectionTabSelect').value,
        is_visible: document.getElementById('sectionVisibleSwitch').checked ? 1 : 0,
        is_collapsible: document.getElementById('sectionCollapsibleSwitch').checked ? 1 : 0,
        width: parseInt(document.getElementById('sectionWidthInput').value),
        height: parseInt(document.getElementById('sectionHeightInput').value)
    };

    if (document.getElementById('sectionCollapsedSwitch')) {
        updates.default_collapsed = document.getElementById('sectionCollapsedSwitch').checked ? 1 : 0;
    }

    // If Header section, save display options in config
    if (selectedSection.section_type === 'header') {
        const config = typeof selectedSection.config === 'string' ?
            JSON.parse(selectedSection.config || '{}') : (selectedSection.config || {});

        config.show_dates = document.getElementById('headerShowDates')?.checked ?? true;
        config.show_status = document.getElementById('headerShowStatus')?.checked ?? true;
        config.show_description = document.getElementById('headerShowDescription')?.checked ?? true;

        updates.config = JSON.stringify(config);
    }

    // If Custom Fields section, save display options in config
    if (selectedSection.section_type === 'form_fields') {
        const config = typeof selectedSection.config === 'string' ?
            JSON.parse(selectedSection.config || '{}') : (selectedSection.config || {});

        config.column_count = parseInt(document.getElementById('customFieldsColumnCount')?.value || '2', 10);
        config.always_editable = document.getElementById('customFieldsAlwaysEdit')?.checked ?? true;
        config.show_labels = document.getElementById('customFieldsShowLabels')?.checked ?? true;

        updates.config = JSON.stringify(config);
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

    if (selectedSection.section_type === 'photo_gallery') {
        const config = typeof selectedSection.config === 'string' ?
            JSON.parse(selectedSection.config || '{}') : (selectedSection.config || {});

        const imageLines = (document.getElementById('photoGalleryImages')?.value || '')
            .split('\n')
            .map(line => line.trim())
            .filter(Boolean);

        config.image_urls = imageLines;
        config.rotation_interval_seconds = Math.max(1, parseInt(document.getElementById('photoGalleryInterval')?.value || '5', 10));
        config.fit_mode = document.getElementById('photoGalleryFitMode')?.value || 'cover';
        config.autoplay = Boolean(document.getElementById('photoGalleryAutoplay')?.checked);
        config.pause_on_hover = Boolean(document.getElementById('photoGalleryPauseOnHover')?.checked);
        config.show_controls = Boolean(document.getElementById('photoGalleryShowControls')?.checked);
        config.show_indicators = Boolean(document.getElementById('photoGalleryShowIndicators')?.checked);

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

        const updatedSection = applySectionUpdatesLocally(selectedSection.id, updates);
        const changedTab = originalSection.tab_id !== updatedSection?.tab_id;
        const changedVisibility = Boolean(originalSection.is_visible) !== Boolean(updatedSection?.is_visible);
        const changedSize = originalSection.width !== updatedSection?.width || originalSection.height !== updatedSection?.height;
        const changedTitle = originalSection.title !== updatedSection?.title;

        if (changedSize) {
            const gridItem = document.getElementById(`section-${selectedSection.id}`);
            if (gridItem) {
                gridStack.update(gridItem, {
                    w: updates.width,
                    h: updates.height
                });
            }
        }

        if (changedTab) {
            activeTab = updatedSection?.tab_id || activeTab;
        }

        if (changedTab || changedVisibility || changedTitle) {
            renderLayout();
        }

        if (!silent) {
            showBanner('Section properties saved', 'success');
        }

        if (keepSelection && updatedSection) {
            renderSectionProperties(updatedSection);
        } else if (!silent) {
            clearSectionSelection();
        }

    } catch (error) {
        console.error('Error saving section properties:', error);
        showBanner('Failed to save section properties', 'error');
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
            ${editMode ? `
                <div class="d-inline-flex align-items-center gap-1 ms-2">
                    <button class="btn btn-sm btn-link p-0 text-primary"
                            onclick="renameTab(event, '${tab.tab_id}')"
                            title="Rename tab">
                        <i class="fas fa-pen"></i>
                    </button>
                    ${tab.tab_id !== 'main' && tab.tab_id !== 'drawio' ? `
                        <button class="btn btn-sm btn-link p-0 text-danger" 
                                onclick="deleteTab(event, ${tab.id})" 
                                title="Delete tab">
                            <i class="fas fa-times"></i>
                        </button>
                    ` : ''}
                </div>
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
async function switchTab(tabId) {
    if (tabId === activeTab) {
        return;
    }

    if (sectionAutoSaveTimer) {
        clearTimeout(sectionAutoSaveTimer);
        sectionAutoSaveTimer = null;
        await saveSectionProperties({ silent: true, keepSelection: true });
    }

    if (editMode && (hasPendingLayoutChanges || autoSaveTimer || autoSaveInFlight)) {
        if (autoSaveTimer) {
            clearTimeout(autoSaveTimer);
            autoSaveTimer = null;
        }

        await saveLayout({ silent: true });
    }

    activeTab = tabId;
    renderTabs();
    renderLayout();

    if (selectedSection) {
        const refreshedSection = currentLayout.sections.find(s => s.id === selectedSection.id);
        if (refreshedSection && (refreshedSection.tab_id || 'main') === activeTab) {
            renderSectionProperties(refreshedSection);
        } else {
            clearSectionSelection();
        }
    }
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
        
        showBanner('Tab created successfully', 'success');
        
        // Reload layout
        await loadLayout(currentLayout.entry_type_id);
        
    } catch (error) {
        console.error('Error creating tab:', error);
        showBanner('Failed to create tab', 'error');
    }
}

// Update a tab
async function updateTab(tabId, tabData) {
    try {
        const response = await fetch(`/api/entry-layout-tabs/${tabId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(tabData)
        });

        if (!response.ok) {
            throw new Error('Failed to update tab');
        }

        showBanner('Tab updated successfully', 'success');
        await loadLayout(currentLayout.entry_type_id);
    } catch (error) {
        console.error('Error updating tab:', error);
        showBanner('Failed to update tab', 'error');
    }
}

// Rename tab
function renameTab(event, tabKey) {
    event.stopPropagation();

    const tab = currentTabs.find(t => t.tab_id === tabKey);
    if (!tab || !tab.id) {
        showBanner('This tab cannot be renamed right now', 'error');
        return;
    }

    const newLabel = prompt('Rename tab:', tab.tab_label || '');
    if (!newLabel) {
        return;
    }

    const trimmedLabel = newLabel.trim();
    if (!trimmedLabel || trimmedLabel === tab.tab_label) {
        return;
    }

    updateTab(tab.id, { tab_label: trimmedLabel });
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
        
        showBanner('Tab deleted successfully', 'success');
        
        // Switch to main tab if deleted tab was active
        const deletedTab = currentTabs.find(t => t.id === tabId);
        if (deletedTab && deletedTab.tab_id === activeTab) {
            activeTab = 'main';
        }
        
        // Reload layout
        await loadLayout(currentLayout.entry_type_id);
        
    } catch (error) {
        console.error('Error deleting tab:', error);
        showBanner('Failed to delete tab', 'error');
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
