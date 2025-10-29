/**
 * Milestone Templates Management
 * Handles template configuration, browsing, and importing
 */

(function() {
    'use strict';
    
    // Global state
    let currentEntryId = null;
    let currentTemplateStatus = null;
    let availableTemplates = [];
    let selectedTemplate = null;
    let currentMilestones = [];
    
    /**
     * Initialize template management for an entry
     */
    window.initMilestoneTemplates = function(entryId) {
        console.log('🎯 initMilestoneTemplates called with entryId:', entryId);
        console.log('🎯 Type of entryId:', typeof entryId);
        
        currentEntryId = entryId;
        
        console.log('🎯 currentEntryId is now set to:', currentEntryId);
        
        // Load current template status
        loadTemplateStatus();
        
        // Set up event listeners
        setupEventListeners();
    };
    
    /**
     * Load entry relationships for template discovery
     */
    async function loadEntryRelationships() {
        try {
            const response = await fetch(`/api/entries/${currentEntryId}/relationships`);
            if (!response.ok) {
                console.log('No relationships found or error loading');
                return;
            }
            
            const relationships = await response.json();
            console.log('📦 Current entry relationships:', relationships);
            console.log(`📦 Current entry ID: ${currentEntryId}`);
            
            const relationshipSelector = document.getElementById('relationshipSelector');
            const relationshipSection = document.getElementById('relationshipSelectorSection');
            
            if (!relationshipSelector) return;
            
            // Clear existing options (keep the first "Select..." option)
            relationshipSelector.innerHTML = '<option value="">Select a related entry...</option>';
            
            // Get parent entries (where current entry is linked TO)
            // E.g., Entry 94 (Sample) → Recipe 93 is a parent
            const parentEntries = new Map(); // entryId -> {title, relationshipLabel, relDefId}
            
            for (const rel of relationships) {
                const isCurrentSource = rel.source_entry_id === currentEntryId;
                const parentId = isCurrentSource ? rel.target_entry_id : rel.source_entry_id;
                const parentTitle = isCurrentSource ? rel.target_title : rel.source_title;
                
                console.log(`  Relationship: current=${currentEntryId} is ${isCurrentSource ? 'SOURCE' : 'TARGET'}, parent=${parentId} (${parentTitle})`);
                
                if (!parentEntries.has(parentId)) {
                    parentEntries.set(parentId, {
                        title: parentTitle,
                        relationshipLabel: rel.relationship_label,
                        relDefId: rel.relationship_type
                    });
                }
            }
            
            // Now find templates that share these same parents
            let hasTemplateEntries = false;
            const discoveredTemplates = [];
            
            for (const [parentId, parentInfo] of parentEntries) {
                console.log(`🔍 Checking for templates via parent ${parentId} (${parentInfo.title}), rel_def ${parentInfo.relDefId}`);
                // Query for templates that are shared via this parent entry
                try {
                    const templatesResponse = await fetch(`/api/templates/shared-via/${parentId}/${parentInfo.relDefId}`);
                    console.log(`   Response status: ${templatesResponse.status}`);
                    if (templatesResponse.ok) {
                        const templates = await templatesResponse.json();
                        console.log(`   Found ${templates.length} templates:`, templates);
                        
                        for (const template of templates) {
                            // Don't show current entry as a template option
                            if (template.template_entry_id !== currentEntryId) {
                                hasTemplateEntries = true;
                                
                                const option = document.createElement('option');
                                option.value = template.template_entry_id;
                                option.textContent = `${parentInfo.relationshipLabel}: ${template.template_name || template.entry_title} (via ${parentInfo.title})`;
                                option.dataset.templateName = template.template_name || 'Unnamed Template';
                                relationshipSelector.appendChild(option);
                                
                                discoveredTemplates.push({
                                    entry_id: template.template_entry_id,
                                    template_name: template.template_name,
                                    via_parent: parentInfo.title
                                });
                            }
                        }
                    }
                } catch (err) {
                    console.warn(`Could not check for templates via parent ${parentId}:`, err);
                }
            }
            
            console.log('Discovered templates via shared parents:', discoveredTemplates);
            
            // Show relationship selector if we have template entries
            if (hasTemplateEntries) {
                relationshipSection.style.display = 'block';
            }
            
        } catch (error) {
            console.error('Error loading entry relationships:', error);
        }
    }
    
    /**
     * Setup event listeners for template UI
     */
    function setupEventListeners() {
        // Template configuration modal
        const saveTemplateBtn = document.getElementById('saveTemplateConfigBtn');
        if (saveTemplateBtn) {
            saveTemplateBtn.addEventListener('click', saveTemplateConfiguration);
        }
        
        // Template browser
        const importBtn = document.getElementById('importTemplateBtn');
        if (importBtn) {
            importBtn.addEventListener('click', performTemplateImport);
        }
        
        // Relationship selector
        const relationshipSelector = document.getElementById('relationshipSelector');
        if (relationshipSelector) {
            relationshipSelector.addEventListener('change', async function() {
                const selectedEntryId = this.value;
                if (!selectedEntryId) return;
                
                // Load template from selected related entry
                document.getElementById('templatesLoadingState').style.display = 'block';
                document.getElementById('noTemplatesState').style.display = 'none';
                document.getElementById('templatesListState').style.display = 'none';
                
                try {
                    const response = await fetch(`/api/entries/${selectedEntryId}/milestone-template`);
                    if (response.ok) {
                        const templateData = await response.json();
                        console.log('📥 Template data received:', templateData);
                        
                        // Create a single-item template list
                        availableTemplates = [{
                            entry_id: parseInt(selectedEntryId),
                            template_name: templateData.template_name,
                            template_description: templateData.template_description,
                            entry_title: this.options[this.selectedIndex].text.split(': ')[1],
                            milestone_count: templateData.milestone_count || 0,
                            entry_type_name: templateData.entry_type_name,
                            owner_type_label: templateData.entry_type_name,  // Add this for consistency
                            milestones: templateData.milestones || [],
                            total_days: templateData.total_days || 0,
                            source: 'relationship'
                        }];
                        
                        console.log('📦 availableTemplates array:', availableTemplates);
                        renderTemplatesList();
                    }
                } catch (error) {
                    console.error('Error loading template from relationship:', error);
                    showNotification('Failed to load template from related entry', 'danger');
                    document.getElementById('templatesLoadingState').style.display = 'none';
                    document.getElementById('noTemplatesState').style.display = 'block';
                }
            });
        }
        
        // Import mode radio buttons
        const importModeRadios = document.querySelectorAll('input[name="importMode"]');
        importModeRadios.forEach(radio => {
            radio.addEventListener('change', updateImportModeHelp);
        });
    }
    
    /**
     * Load current template status for the entry
     */
    async function loadTemplateStatus() {
        try {
            const response = await fetch(`/api/entries/${currentEntryId}/milestone-template`);
            if (response.ok) {
                currentTemplateStatus = await response.json();
                updateTemplateUI();
            }
        } catch (error) {
            console.error('Error loading template status:', error);
        }
    }
    
    /**
     * Update UI based on current template status
     */
    function updateTemplateUI() {
        const statusBadge = document.getElementById('templateStatusBadge');
        if (statusBadge && currentTemplateStatus) {
            if (currentTemplateStatus.is_template) {
                statusBadge.style.display = 'inline-flex';
                statusBadge.querySelector('.template-name').textContent = currentTemplateStatus.template_name;
                
                const distBadge = statusBadge.querySelector('.distribution-badge');
                distBadge.textContent = currentTemplateStatus.distribution_status.replace('_', ' ');
                distBadge.className = 'badge distribution-badge ' + getDistributionBadgeClass(currentTemplateStatus.distribution_status);
            } else {
                statusBadge.style.display = 'none';
            }
        }
        
        // Update dropdown menu items
        updateTemplateDropdownMenu();
    }
    
    /**
     * Get badge class for distribution status
     */
    function getDistributionBadgeClass(status) {
        const classes = {
            'private': 'bg-secondary',
            'marked_for_distribution': 'bg-success',
            'distributed': 'bg-info'
        };
        return classes[status] || 'bg-secondary';
    }
    
    /**
     * Update template dropdown menu items based on current status
     */
    function updateTemplateDropdownMenu() {
        const configMenuItem = document.getElementById('configureTemplateMenuItem');
        const distributeMenuItem = document.getElementById('toggleDistributionMenuItem');
        
        if (configMenuItem && currentTemplateStatus) {
            const icon = configMenuItem.querySelector('i');
            const text = configMenuItem.querySelector('.menu-text');
            
            if (currentTemplateStatus.is_template) {
                icon.className = 'fas fa-cog me-2';
                text.textContent = 'Edit Template Settings';
            } else {
                icon.className = 'fas fa-layer-group me-2';
                text.textContent = 'Save as Template';
            }
        }
        
        if (distributeMenuItem && currentTemplateStatus) {
            if (currentTemplateStatus.is_template) {
                distributeMenuItem.style.display = 'block';
                const text = distributeMenuItem.querySelector('.menu-text');
                
                if (currentTemplateStatus.distribution_status === 'marked_for_distribution') {
                    text.textContent = 'Unmark for Distribution';
                } else {
                    text.textContent = 'Mark for Distribution';
                }
            } else {
                distributeMenuItem.style.display = 'none';
            }
        }
    }
    
    /**
     * Show template configuration modal
     */
    window.showTemplateConfigModal = async function() {
        // Load current milestones
        await loadCurrentMilestones();
        
        // Populate form with current template data
        const modal = new bootstrap.Modal(document.getElementById('templateConfigModal'));
        
        if (currentTemplateStatus && currentTemplateStatus.is_template) {
            document.getElementById('templateName').value = currentTemplateStatus.template_name || '';
            document.getElementById('templateDescription').value = currentTemplateStatus.template_description || '';
            document.getElementById('markForDistribution').checked = 
                currentTemplateStatus.distribution_status === 'marked_for_distribution';
        } else {
            document.getElementById('templateName').value = '';
            document.getElementById('templateDescription').value = '';
            document.getElementById('markForDistribution').checked = false;
        }
        
        // Show milestone preview
        renderMilestonePreview();
        
        // Load relationship types for sharing
        await loadRelationshipTypes();
        
        modal.show();
    };
    
    /**
     * Load current milestones for the entry
     */
    async function loadCurrentMilestones() {
        try {
            const response = await fetch(`/api/entries/${currentEntryId}/milestones`);
            console.log('Loading milestones for entry:', currentEntryId);
            console.log('Response status:', response.status);
            if (response.ok) {
                currentMilestones = await response.json();
                console.log('Loaded milestones:', currentMilestones);
            } else {
                console.error('Failed to load milestones, status:', response.status);
                currentMilestones = [];
            }
        } catch (error) {
            console.error('Error loading milestones:', error);
            currentMilestones = [];
        }
    }
    
    /**
     * Render milestone preview in template config modal
     */
    function renderMilestonePreview() {
        const previewContainer = document.getElementById('templateMilestonePreview');
        const countSpan = document.getElementById('templateMilestoneCount');
        
        console.log('Rendering milestone preview, count:', currentMilestones.length);
        console.log('Current milestones:', currentMilestones);
        
        if (!previewContainer) return;
        
        countSpan.textContent = currentMilestones.length;
        
        if (currentMilestones.length === 0) {
            previewContainer.innerHTML = `
                <div class="alert alert-warning mb-0">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    No milestones found. Please add milestones before creating a template.
                </div>
            `;
            document.getElementById('saveTemplateConfigBtn').disabled = true;
            return;
        }
        
        document.getElementById('saveTemplateConfigBtn').disabled = false;
        
        let html = '';
        currentMilestones.forEach((milestone, index) => {
            html += `
                <div class="milestone-item">
                    <span class="milestone-badge" style="background-color: ${milestone.target_state_color}">
                        ${milestone.order_position}
                    </span>
                    <span class="milestone-name">
                        ${escapeHtml(milestone.target_state_name)}
                    </span>
                    <span class="milestone-duration">
                        ${milestone.duration_days}d
                    </span>
                </div>
            `;
        });
        
        previewContainer.innerHTML = html;
    }
    
    /**
     * Save template configuration
     */
    async function saveTemplateConfiguration() {
        const templateName = document.getElementById('templateName').value.trim();
        const templateDescription = document.getElementById('templateDescription').value.trim();
        const markForDistribution = document.getElementById('markForDistribution').checked;
        
        // Get selected entries from window.templateSharingSelected
        // Flatten to array of {relationship_definition_id, source_entry_id} pairs
        const selectedSharing = [];
        if (window.templateSharingSelected) {
            for (const [relDefId, entries] of Object.entries(window.templateSharingSelected)) {
                for (const entry of entries) {
                    selectedSharing.push({
                        relationship_definition_id: parseInt(relDefId),
                        source_entry_id: entry.source_entry_id
                    });
                }
            }
        }
        
        if (!templateName) {
            showNotification('Please enter a template name', 'warning');
            return;
        }
        
        const btn = document.getElementById('saveTemplateConfigBtn');
        const originalText = btn.innerHTML;
        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Saving...';
        
        try {
            // Save template config
            const response = await fetch(`/api/entries/${currentEntryId}/milestone-template`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    is_template: true,
                    template_name: templateName,
                    template_description: templateDescription
                })
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Failed to save template');
            }
            
            // Set distribution status if checked
            if (markForDistribution) {
                await fetch(`/api/entries/${currentEntryId}/milestone-template/distribution`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        distribution_status: 'marked_for_distribution'
                    })
                });
            }
            
            // Save relationship sharing configuration (entry-level granular)
            await fetch(`/api/entries/${currentEntryId}/template-relationship-sharing`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    sharing: selectedSharing
                })
            });
            
            showNotification('Template saved successfully!', 'success');
            
            // Close modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('templateConfigModal'));
            modal.hide();
            
            // Reload template status
            await loadTemplateStatus();
            
        } catch (error) {
            console.error('Error saving template:', error);
            showNotification(error.message, 'danger');
        } finally {
            btn.disabled = false;
            btn.innerHTML = originalText;
        }
    }
    
    /**
     * Toggle template distribution status
     */
    window.toggleTemplateDistribution = async function() {
        if (!currentTemplateStatus || !currentTemplateStatus.is_template) {
            showNotification('Entry must be a template first', 'warning');
            return;
        }
        
        const isCurrentlyDistributed = currentTemplateStatus.distribution_status === 'marked_for_distribution';
        const newStatus = isCurrentlyDistributed ? 'private' : 'marked_for_distribution';
        
        try {
            const response = await fetch(`/api/entries/${currentEntryId}/milestone-template/distribution`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    distribution_status: newStatus
                })
            });
            
            if (!response.ok) {
                throw new Error('Failed to update distribution status');
            }
            
            const action = isCurrentlyDistributed ? 'unmarked from' : 'marked for';
            showNotification(`Template ${action} distribution`, 'success');
            
            // Reload template status
            await loadTemplateStatus();
            
        } catch (error) {
            console.error('Error toggling distribution:', error);
            showNotification('Failed to update distribution status', 'danger');
        }
    };
    
    /**
     * Show template browser modal
     */
    window.showTemplateBrowser = async function() {
        const modal = new bootstrap.Modal(document.getElementById('templateBrowserModal'));
        modal.show();
        
        // Reset state
        document.getElementById('templatesLoadingState').style.display = 'block';
        document.getElementById('noTemplatesState').style.display = 'none';
        document.getElementById('templatesListState').style.display = 'none';
        document.getElementById('importOptionsSection').style.display = 'none';
        document.getElementById('importTemplateBtn').style.display = 'none';
        document.getElementById('relationshipSelectorSection').style.display = 'none';
        selectedTemplate = null;
        
        // Load entry relationships for template discovery
        await loadEntryRelationships();
        
        // Note: We ONLY use relationship-based template discovery now
        // Templates must be explicitly shared via parent entries
        // The old type-based discovery is disabled to enforce proper sharing controls
        
        // Check if we found any templates via relationships
        const relationshipSelector = document.getElementById('relationshipSelector');
        const hasRelationshipTemplates = relationshipSelector && relationshipSelector.options.length > 1;
        
        if (!hasRelationshipTemplates) {
            document.getElementById('templatesLoadingState').style.display = 'none';
            document.getElementById('noTemplatesState').style.display = 'block';
        }
        
        // Don't load type-based templates anymore - relationship-based only
        availableTemplates = [];
    };
    
    /**
     * Render available templates list
     */
    function renderTemplatesList() {
        const listContainer = document.getElementById('templatesList');
        
        let html = '';
        availableTemplates.forEach(template => {
            const templateId = template.template_entry_id || template.entry_id;
            html += `
                <div class="template-card" data-template-id="${templateId}">
                    <div class="template-card-header">
                        <div class="template-info">
                            <h6 class="template-name">
                                <i class="fas fa-layer-group me-2"></i>
                                ${escapeHtml(template.template_name)}
                            </h6>
                            <small class="template-type">
                                From: ${escapeHtml(template.owner_type_label)}
                            </small>
                        </div>
                        <div class="template-stats">
                            <span class="badge bg-primary">
                                ${template.milestone_count} milestone${template.milestone_count !== 1 ? 's' : ''}
                            </span>
                        </div>
                    </div>
                    ${template.template_description ? `
                        <div class="template-card-body">
                            <p class="template-description">
                                ${escapeHtml(template.template_description)}
                            </p>
                        </div>
                    ` : ''}
                    <div class="template-milestones-preview">
                        <div class="milestone-timeline">
                            ${renderMilestoneTimeline(template.milestones, template.total_days)}
                        </div>
                        <small class="text-muted">
                            Total duration: ${template.total_days} day${template.total_days !== 1 ? 's' : ''}
                        </small>
                    </div>
                    <div class="entry-title">
                        <i class="fas fa-info-circle me-1"></i>
                        Source: ${escapeHtml(template.entry_title)}
                    </div>
                </div>
            `;
        });
        
        listContainer.innerHTML = html;
        
        // Add click handlers
        listContainer.querySelectorAll('.template-card').forEach(card => {
            card.addEventListener('click', function() {
                selectTemplate(parseInt(this.dataset.templateId));
            });
        });
        
        document.getElementById('templatesLoadingState').style.display = 'none';
        document.getElementById('templatesListState').style.display = 'block';
    }
    
    /**
     * Render milestone timeline visualization
     */
    function renderMilestoneTimeline(milestones, totalDays) {
        console.log('🎨 renderMilestoneTimeline called:', { milestones, totalDays });
        
        if (!milestones || milestones.length === 0) {
            console.log('⚠️ No milestones to render');
            return '';
        }
        
        let html = '';
        milestones.forEach(m => {
            const width = (m.duration_days / totalDays * 100);
            const label = width > 15 ? `${m.target_state_name} (${m.duration_days}d)` : '';
            
            html += `
                <div class="milestone-preview-item" 
                     style="width: ${width}%; background-color: ${m.target_state_color};"
                     title="${escapeHtml(m.target_state_name)} - ${m.duration_days} days">
                    <span class="milestone-label">${escapeHtml(label)}</span>
                </div>
            `;
        });
        
        console.log('✅ Timeline HTML generated:', html.substring(0, 200));
        return html;
    }
    
    /**
     * Select a template
     */
    function selectTemplate(templateId) {
        selectedTemplate = availableTemplates.find(t => 
            (t.template_entry_id === templateId) || (t.entry_id === templateId)
        );
        
        // Update UI
        document.querySelectorAll('.template-card').forEach(card => {
            card.classList.toggle('selected', parseInt(card.dataset.templateId) === templateId);
        });
        
        document.getElementById('importOptionsSection').style.display = 'block';
        document.getElementById('importTemplateBtn').style.display = 'inline-block';
        document.getElementById('importTemplateBtn').disabled = false;
    }
    
    /**
     * Update import mode help text
     */
    function updateImportModeHelp() {
        const mode = document.querySelector('input[name="importMode"]:checked').value;
        const helpText = document.getElementById('importModeHelp');
        
        if (mode === 'replace') {
            helpText.innerHTML = '⚠️ <strong>Replace:</strong> This will delete all existing milestones and replace them with the template';
        } else {
            helpText.innerHTML = 'ℹ️ <strong>Append:</strong> Template milestones will be added after your existing ones';
        }
    }
    
    /**
     * Perform template import
     */
    async function performTemplateImport() {
        if (!selectedTemplate) return;
        
        const importMode = document.querySelector('input[name="importMode"]:checked').value;
        
        // Confirmation for replace mode
        if (importMode === 'replace') {
            if (!confirm('Are you sure you want to replace all existing milestones? This cannot be undone.')) {
                return;
            }
        }
        
        const btn = document.getElementById('importTemplateBtn');
        const originalText = btn.innerHTML;
        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Importing...';
        
        try {
            // Handle both template_entry_id (from type-based) and entry_id (from relationship-based)
            const templateId = selectedTemplate.template_entry_id || selectedTemplate.entry_id;
            
            const response = await fetch(`/api/entries/${currentEntryId}/import-template`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    template_entry_id: templateId,
                    import_mode: importMode
                })
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Failed to import template');
            }
            
            const result = await response.json();
            showNotification(`Successfully imported ${result.imported_count} milestone(s)!`, 'success');
            
            // Close modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('templateBrowserModal'));
            modal.hide();
            
            // Reload the page to show new milestones
            setTimeout(() => {
                window.location.reload();
            }, 1000);
            
        } catch (error) {
            console.error('Error importing template:', error);
            showNotification(error.message, 'danger');
            btn.disabled = false;
            btn.innerHTML = originalText;
        }
    }
    
    /**
     * Load relationship types for template sharing
     */
    async function loadRelationshipTypes() {
        try {
            // Get the current entry's relationships
            const relationshipsResponse = await fetch(`/api/entries/${currentEntryId}/relationships`);
            if (!relationshipsResponse.ok) {
                console.warn('Could not load entry relationships');
                const container = document.getElementById('relationshipTypeSelect');
                if (container) {
                    container.innerHTML = '<option value="">No relationships found</option>';
                }
                return;
            }
            
            const relationships = await relationshipsResponse.json();
            
            console.log('📦 Relationships received:', relationships);
            console.log('📦 First relationship:', relationships[0]);
            
            if (relationships.length === 0) {
                const container = document.getElementById('relationshipTypeSelect');
                if (container) {
                    container.innerHTML = '<option value="">No relationships found. Create relationships first.</option>';
                }
                return;
            }
            
            // Group relationships by type
            const groupedRelationships = {};
            for (const rel of relationships) {
                console.log('🔍 Processing relationship:', rel);
                console.log('   - relationship_type:', rel.relationship_type);
                console.log('   - source_entry_id:', rel.source_entry_id);
                console.log('   - target_entry_id:', rel.target_entry_id);
                console.log('   - source_title:', rel.source_title);
                console.log('   - target_title:', rel.target_title);
                
                const relDefId = rel.relationship_type;
                if (!groupedRelationships[relDefId]) {
                    groupedRelationships[relDefId] = {
                        label: rel.relationship_label || 'Related',
                        entries: []
                    };
                }
                
                // Determine the "parent" entry (the one we're linked TO, not FROM)
                // If current entry is target, parent is source; if current is source, parent is target
                const isCurrentSource = rel.source_entry_id === currentEntryId;
                const parentEntry = {
                    id: isCurrentSource ? rel.target_entry_id : rel.source_entry_id,
                    title: isCurrentSource ? rel.target_title : rel.source_title,
                    relationshipId: rel.id
                };
                
                // Avoid duplicates
                if (!groupedRelationships[relDefId].entries.some(e => e.id === parentEntry.id)) {
                    groupedRelationships[relDefId].entries.push(parentEntry);
                }
            }
            
            // Store for later use
            window.templateSharingRelationships = groupedRelationships;
            
            // Load currently selected sharing config
            let selectedSharing = {};
            if (currentTemplateStatus && currentTemplateStatus.is_template) {
                try {
                    const sharingResponse = await fetch(`/api/entries/${currentEntryId}/template-relationship-sharing`);
                    if (sharingResponse.ok) {
                        const sharing = await sharingResponse.json();
                        // Group by relationship_definition_id and match with actual entries
                        for (const item of sharing) {
                            const relDefId = item.relationship_definition_id;
                            if (!selectedSharing[relDefId]) {
                                selectedSharing[relDefId] = [];
                            }
                            
                            // If source_entry_id exists, find the matching entry from our relationships
                            if (item.source_entry_id && groupedRelationships[relDefId]) {
                                const matchingEntry = groupedRelationships[relDefId].entries.find(
                                    e => e.id === item.source_entry_id
                                );
                                
                                if (matchingEntry) {
                                    selectedSharing[relDefId].push({
                                        relationship_definition_id: relDefId,
                                        source_entry_id: item.source_entry_id,
                                        title: matchingEntry.title
                                    });
                                }
                            }
                        }
                    }
                } catch (err) {
                    console.warn('Could not load template sharing config:', err);
                }
            }
            
            window.templateSharingSelected = selectedSharing;
            
            // Populate dropdown
            const select = document.getElementById('relationshipTypeSelect');
            select.innerHTML = '<option value="">Choose a relationship type...</option>' +
                Object.entries(groupedRelationships).map(([relDefId, group]) => {
                    return `<option value="${relDefId}">${escapeHtml(group.label)} (${group.entries.length})</option>`;
                }).join('');
            
            // Add change event listener
            select.addEventListener('change', function() {
                const relDefId = this.value;
                if (relDefId && groupedRelationships[relDefId]) {
                    showRelatedEntries(relDefId, groupedRelationships[relDefId]);
                } else {
                    document.getElementById('relatedEntriesList').style.display = 'none';
                }
            });
            
            // Restore UI state for saved selections
            if (Object.keys(selectedSharing).length > 0) {
                // Auto-select the first relationship type that has selections
                const firstRelDefId = Object.keys(selectedSharing)[0];
                if (firstRelDefId && groupedRelationships[firstRelDefId]) {
                    select.value = firstRelDefId;
                    showRelatedEntries(firstRelDefId, groupedRelationships[firstRelDefId]);
                    
                    // Wait for DOM to update, then check the boxes
                    setTimeout(() => {
                        const savedEntries = selectedSharing[firstRelDefId] || [];
                        savedEntries.forEach(item => {
                            const checkbox = document.getElementById(`entry_${firstRelDefId}_${item.source_entry_id}`);
                            if (checkbox) {
                                checkbox.checked = true;
                            }
                        });
                        updateSelectedCount(firstRelDefId);
                        updateSelectedSummary();
                    }, 100);
                }
            }
            
            // Show summary of currently selected entries
            updateSelectedSummary();
            
        } catch (error) {
            console.error('Error loading relationship types:', error);
        }
    }
    
    /**
     * Show related entries for a selected relationship type
     */
    function showRelatedEntries(relDefId, group) {
        const container = document.getElementById('relatedEntriesCheckboxes');
        const listDiv = document.getElementById('relatedEntriesList');
        
        // Check which entries are already selected for this relationship type
        const selectedForThisType = window.templateSharingSelected[relDefId] || [];
        
        container.innerHTML = group.entries.map(entry => {
            const isChecked = selectedForThisType.some(s => s.source_entry_id === entry.id);
            return `
                <div class="form-check">
                    <input class="form-check-input related-entry-checkbox" 
                           type="checkbox" 
                           value="${entry.id}"
                           data-rel-def-id="${relDefId}"
                           data-entry-title="${escapeHtml(entry.title)}"
                           id="entry_${relDefId}_${entry.id}"
                           ${isChecked ? 'checked' : ''}>
                    <label class="form-check-label" for="entry_${relDefId}_${entry.id}">
                        ${escapeHtml(entry.title)}
                    </label>
                </div>
            `;
        }).join('');
        
        listDiv.style.display = 'block';
        
        // Add change event listeners to update selection
        container.querySelectorAll('.related-entry-checkbox').forEach(cb => {
            cb.addEventListener('change', function() {
                const relDefId = this.dataset.relDefId;
                const entryId = parseInt(this.value);
                const entryTitle = this.dataset.entryTitle;
                
                if (!window.templateSharingSelected[relDefId]) {
                    window.templateSharingSelected[relDefId] = [];
                }
                
                if (this.checked) {
                    // Add to selection
                    if (!window.templateSharingSelected[relDefId].some(s => s.source_entry_id === entryId)) {
                        window.templateSharingSelected[relDefId].push({
                            relationship_definition_id: parseInt(relDefId),
                            source_entry_id: entryId,
                            title: entryTitle
                        });
                    }
                } else {
                    // Remove from selection
                    window.templateSharingSelected[relDefId] = window.templateSharingSelected[relDefId]
                        .filter(s => s.source_entry_id !== entryId);
                    
                    if (window.templateSharingSelected[relDefId].length === 0) {
                        delete window.templateSharingSelected[relDefId];
                    }
                }
                
                updateSelectedSummary();
            });
        });
        
        updateSelectedCount(relDefId);
    }
    
    /**
     * Update count of selected entries
     */
    function updateSelectedCount(relDefId) {
        const selected = window.templateSharingSelected[relDefId] || [];
        document.getElementById('selectedEntriesCount').textContent = selected.length;
    }
    
    /**
     * Update summary of all selected entries
     */
    function updateSelectedSummary() {
        const summaryDiv = document.getElementById('selectedRelationshipsSummary');
        
        if (!window.templateSharingSelected || Object.keys(window.templateSharingSelected).length === 0) {
            summaryDiv.innerHTML = '';
            return;
        }
        
        let totalCount = 0;
        const summaryItems = [];
        
        for (const [relDefId, entries] of Object.entries(window.templateSharingSelected)) {
            if (entries.length > 0) {
                const group = window.templateSharingRelationships[relDefId];
                const entryTitles = entries.map(e => e.title || 'Unknown').join(', ');
                summaryItems.push(`<strong>${group.label}:</strong> ${entryTitles}`);
                totalCount += entries.length;
            }
        }
        
        if (summaryItems.length > 0) {
            summaryDiv.innerHTML = `
                <div class="alert alert-info">
                    <h6><i class="fas fa-users me-2"></i>Template will be shared with ${totalCount} entry(ies):</h6>
                    <ul class="mb-0 mt-2">
                        ${summaryItems.map(item => `<li>${item}</li>`).join('')}
                    </ul>
                </div>
            `;
        } else {
            summaryDiv.innerHTML = '';
        }
    }
    
    /**
     * Utility: Escape HTML
     */
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    /**
     * Show notification
     */
    function showNotification(message, type = 'info') {
        // Use existing notification system if available
        if (window.showToast) {
            window.showToast(message, type);
        } else {
            alert(message);
        }
    }
    
})();
