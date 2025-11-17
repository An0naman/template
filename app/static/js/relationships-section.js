/**
 * Relationships Section JavaScript for Entry Detail V2
 * Handles tab switching, hierarchy loading, AJAX operations, and interactions
 */

// Initialize the relationships section
function initializeRelationshipsSection(entryId) {
    console.log('Initializing relationships section for entry:', entryId);
    
    // Initialize tab switching
    initializeRelationshipTabs(entryId);
    
    // Initialize delete buttons
    initializeDeleteButtons(entryId);
    
    // Initialize edit buttons
    initializeEditButtons(entryId);
    
    // Initialize add relationship modal
    initializeAddRelationshipModal(entryId);
    
    // Initialize tree collapse/expand
    initializeTreeToggles();
}

// Initialize tab switching with lazy loading for hierarchy
function initializeRelationshipTabs(entryId) {
    const hierarchyTab = document.getElementById('hierarchy-tab-btn');
    
    if (hierarchyTab) {
        hierarchyTab.addEventListener('shown.bs.tab', function (e) {
            // Load hierarchy when tab is shown
            loadRelationshipHierarchy(entryId);
        });
    }
}

// Load relationship hierarchy via AJAX
function loadRelationshipHierarchy(entryId) {
    const loadingDiv = document.getElementById('hierarchy-loading');
    const contentDiv = document.getElementById('hierarchy-content');
    
    if (!loadingDiv || !contentDiv) return;
    
    // Check if already loaded
    if (contentDiv.dataset.loaded === 'true') {
        loadingDiv.style.display = 'none';
        contentDiv.style.display = 'block';
        return;
    }
    
    // Show loading state
    loadingDiv.style.display = 'flex';
    contentDiv.style.display = 'none';
    
    // Fetch hierarchy data
    fetch(`/api/entries/${entryId}/relationships/hierarchy`)
        .then(response => response.json())
        .then(data => {
            if (data.success || data.hierarchy) {
                const hierarchy = data.hierarchy || [];
                renderRelationshipTree(hierarchy, entryId, contentDiv);
                contentDiv.dataset.loaded = 'true';
            } else {
                throw new Error(data.error || 'Failed to load hierarchy');
            }
            
            loadingDiv.style.display = 'none';
            contentDiv.style.display = 'block';
        })
        .catch(error => {
            console.error('Error loading hierarchy:', error);
            contentDiv.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-exclamation-circle text-danger"></i>
                    <h6>Error Loading Hierarchy</h6>
                    <p class="text-muted">${error.message}</p>
                    <button class="btn btn-primary" onclick="retryLoadHierarchy(${entryId})">
                        <i class="fas fa-redo"></i> Retry
                    </button>
                </div>
            `;
            loadingDiv.style.display = 'none';
            contentDiv.style.display = 'block';
        });
}

// Retry loading hierarchy
function retryLoadHierarchy(entryId) {
    const contentDiv = document.getElementById('hierarchy-content');
    if (contentDiv) {
        contentDiv.dataset.loaded = 'false';
    }
    loadRelationshipHierarchy(entryId);
}

// Render relationship tree
function renderRelationshipTree(hierarchy, currentEntryId, container) {
    if (!hierarchy || hierarchy.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-sitemap"></i>
                <p class="text-muted">No hierarchical relationships found</p>
            </div>
        `;
        return;
    }
    
    const treeHtml = hierarchy.map(node => renderTreeNode(node, 0, currentEntryId)).join('');
    container.innerHTML = `<div class="relationship-tree">${treeHtml}</div>`;
    
    // Initialize tree toggles after rendering
    initializeTreeToggles();
}

// Render a single tree node (recursive)
function renderTreeNode(node, level, currentEntryId) {
    const isCurrent = node.id === currentEntryId;
    const isParent = node.is_parent || false;
    const hasChildren = node.children && node.children.length > 0;
    
    const nodeClasses = ['tree-node-content'];
    if (isCurrent) nodeClasses.push('current-entry');
    if (isParent) nodeClasses.push('parent-entry');
    
    let html = `
        <div class="tree-node level-${level}" data-entry-id="${node.id}" style="padding-left: ${level * 20}px;">
            <div class="${nodeClasses.join(' ')}">
    `;
    
    // Toggle button or spacer
    if (hasChildren) {
        html += `
            <button class="tree-toggle-btn" data-node-id="${node.id}">
                <i class="fas fa-chevron-down"></i>
            </button>
        `;
    } else {
        html += `<span class="tree-spacer"></span>`;
    }
    
    // Entry type icon
    html += `
        <span class="tree-entry-type" 
              style="color: ${node.entry_type.color};"
              title="${node.entry_type.label}">
            <i class="${node.entry_type.icon}"></i>
        </span>
    `;
    
    // Entry title and link
    html += `
        <a href="/entry/${node.id}" 
           class="tree-entry-link ${isCurrent ? 'fw-bold' : ''}"
           target="_blank">
            ${escapeHtml(node.title)}
    `;
    
    // Badges
    if (isCurrent) {
        html += `<span class="badge bg-success ms-2">Current</span>`;
    } else if (isParent) {
        html += `<span class="badge bg-info ms-2">Parent</span>`;
    }
    html += `</a>`;
    
    // Status badge
    if (node.status) {
        html += `
            <span class="status-badge status-${node.status.toLowerCase().replace(/\s+/g, '-')} ms-2">
                ${escapeHtml(node.status)}
            </span>
        `;
    }
    
    // Relationship type label
    if (node.relationship_type) {
        html += `
            <small class="text-muted ms-2">
                <i class="fas fa-link"></i> ${escapeHtml(node.relationship_type)}
            </small>
        `;
    }
    
    html += `</div>`; // Close tree-node-content
    
    // Children (recursive)
    if (hasChildren) {
        html += `<div class="tree-children" data-parent-id="${node.id}">`;
        for (const child of node.children) {
            html += renderTreeNode(child, level + 1, currentEntryId);
        }
        html += `</div>`;
    }
    
    html += `</div>`; // Close tree-node
    
    return html;
}

// Initialize tree toggle buttons
function initializeTreeToggles() {
    const toggleButtons = document.querySelectorAll('.tree-toggle-btn');
    
    toggleButtons.forEach(button => {
        // Remove existing listeners
        const newButton = button.cloneNode(true);
        button.parentNode.replaceChild(newButton, button);
        
        newButton.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            const nodeId = this.dataset.nodeId;
            const childrenDiv = document.querySelector(`.tree-children[data-parent-id="${nodeId}"]`);
            const icon = this.querySelector('i');
            
            if (childrenDiv) {
                childrenDiv.classList.toggle('collapsed');
                icon.style.transform = childrenDiv.classList.contains('collapsed') 
                    ? 'rotate(-90deg)' 
                    : 'rotate(0deg)';
            }
        });
    });
}

// Initialize delete relationship buttons
function initializeDeleteButtons(entryId) {
    const deleteButtons = document.querySelectorAll('.delete-relationship-btn');
    
    deleteButtons.forEach(button => {
        button.addEventListener('click', function() {
            const relationshipId = this.dataset.relationshipId;
            const entryTitle = this.dataset.entryTitle;
            
            if (confirm(`Are you sure you want to remove the relationship with "${entryTitle}"?`)) {
                deleteRelationship(relationshipId, entryId);
            }
        });
    });
}

// Delete a relationship
function deleteRelationship(relationshipId, entryId) {
    fetch(`/api/relationships/${relationshipId}`, {
        method: 'DELETE',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success || data.message) {
            // Remove the card from DOM
            const card = document.querySelector(`.relationship-card[data-relationship-id="${relationshipId}"]`);
            if (card) {
                card.style.transition = 'all 0.3s ease';
                card.style.opacity = '0';
                card.style.transform = 'scale(0.9)';
                setTimeout(() => card.remove(), 300);
            }
            
            // Show success message
            showBanner('Relationship deleted successfully', 'success');
            
            // Reload page after a short delay to update counts
            setTimeout(() => window.location.reload(), 1000);
        } else {
            throw new Error(data.error || 'Failed to delete relationship');
        }
    })
    .catch(error => {
        console.error('Error deleting relationship:', error);
        showNotification(error.message, 'error');
    });
}

// Initialize edit quantity/unit buttons
function initializeEditButtons(entryId) {
    const editButtons = document.querySelectorAll('.edit-relationship-btn');
    
    editButtons.forEach(button => {
        button.addEventListener('click', function() {
            const relationshipId = this.dataset.relationshipId;
            // TODO: Implement edit modal
            console.log('Edit relationship:', relationshipId);
        });
    });
}

// Initialize add relationship modal
function initializeAddRelationshipModal(entryId) {
    const modal = document.getElementById(`addRelationshipModal${entryId}`);
    if (!modal) {
        console.error('Modal not found:', `addRelationshipModal${entryId}`);
        return;
    }
    
    console.log('Modal found and initializing:', `addRelationshipModal${entryId}`);
    
    // Clean up any orphaned backdrops before showing modal
    modal.addEventListener('show.bs.modal', function() {
        console.log('Modal showing, loading definitions...');
        
        // Remove any orphaned backdrops
        const orphanedBackdrops = document.querySelectorAll('.modal-backdrop');
        orphanedBackdrops.forEach(backdrop => {
            if (!document.querySelector('.modal.show')) {
                backdrop.remove();
            }
        });
        
        loadRelationshipDefinitions(entryId);
    });
    
    // Fix backdrop z-index after modal is fully shown
    modal.addEventListener('shown.bs.modal', function() {
        console.log('Modal shown, fixing backdrop z-index...');
        
        // Force backdrop behind modal
        const backdrops = document.querySelectorAll('.modal-backdrop');
        backdrops.forEach(backdrop => {
            backdrop.style.zIndex = '1040';
        });
        
        // Ensure modal is on top
        modal.style.zIndex = '1050';
        const dialog = modal.querySelector('.modal-dialog');
        if (dialog) {
            dialog.style.zIndex = '1060';
        }
        
        // Log for debugging
        console.log('Backdrop count:', backdrops.length);
        console.log('Modal z-index:', modal.style.zIndex);
    });
    
    // Ensure modal is properly cleaned up when hidden
    modal.addEventListener('hidden.bs.modal', function() {
        console.log('Modal hidden, cleaning up...');
        
        // Remove all backdrops
        const backdrops = document.querySelectorAll('.modal-backdrop');
        backdrops.forEach(backdrop => backdrop.remove());
        
        // Remove modal-open class from body
        document.body.classList.remove('modal-open');
        document.body.style.overflow = '';
        document.body.style.paddingRight = '';
    });
    
    // Handle create new entry checkbox
    const createNewCheckbox = document.getElementById(`createNewEntry${entryId}`);
    const relatedEntrySelect = document.getElementById(`relatedEntry${entryId}`);
    const newEntryFields = document.getElementById(`newEntryFields${entryId}`);
    
    if (createNewCheckbox) {
        createNewCheckbox.addEventListener('change', function() {
            if (this.checked) {
                relatedEntrySelect.disabled = true;
                newEntryFields.style.display = 'block';
            } else {
                relatedEntrySelect.disabled = false;
                newEntryFields.style.display = 'none';
            }
        });
    }
    
    // Handle relationship definition change
    const definitionSelect = document.getElementById(`relationshipDefinition${entryId}`);
    const quantityUnitFields = document.getElementById(`quantityUnitFields${entryId}`);
    
    if (definitionSelect) {
        definitionSelect.addEventListener('change', function() {
            const selectedOption = this.options[this.selectedIndex];
            const allowQuantity = selectedOption.dataset.allowQuantity === 'true';
            
            if (allowQuantity && quantityUnitFields) {
                quantityUnitFields.style.display = 'block';
            } else if (quantityUnitFields) {
                quantityUnitFields.style.display = 'none';
            }
            
            // Load related entries based on selected definition
            const targetTypeId = selectedOption.dataset.targetTypeId;
            if (targetTypeId) {
                loadRelatedEntries(entryId, targetTypeId);
            }
        });
    }
    
    // Handle submit button
    const submitButton = document.getElementById(`submitRelationship${entryId}`);
    if (submitButton) {
        submitButton.addEventListener('click', function() {
            submitAddRelationship(entryId);
        });
    }
}

// Load relationship definitions for the entry
function loadRelationshipDefinitions(entryId) {
    const select = document.getElementById(`relationshipDefinition${entryId}`);
    if (!select) return;
    
    fetch('/api/relationship_definitions')
        .then(response => response.json())
        .then(definitions => {
            select.innerHTML = '<option value="">Select relationship type...</option>';
            
            definitions.forEach(def => {
                const option = document.createElement('option');
                option.value = def.id;
                option.textContent = `${def.label_from_side} → ${def.entry_type_to_label}`;
                option.dataset.allowQuantity = def.allow_quantity_unit;
                option.dataset.targetTypeId = def.entry_type_id_to;
                select.appendChild(option);
            });
        })
        .catch(error => {
            console.error('Error loading relationship definitions:', error);
            showNotification('Failed to load relationship types', 'error');
        });
}

// Load related entries based on target type
function loadRelatedEntries(entryId, targetTypeId) {
    const select = document.getElementById(`relatedEntry${entryId}`);
    if (!select) return;
    
    // TODO: Implement API endpoint to get entries by type
    // For now, just show a placeholder
    select.innerHTML = '<option value="">Search and select entry...</option>';
}

// Submit add relationship form
function submitAddRelationship(entryId) {
    const definitionId = document.getElementById(`relationshipDefinition${entryId}`).value;
    const createNew = document.getElementById(`createNewEntry${entryId}`).checked;
    
    if (!definitionId) {
        showNotification('Please select a relationship type', 'error');
        return;
    }
    
    const data = {
        definition_id: definitionId
    };
    
    if (createNew) {
        // Create new entry
        const title = document.getElementById(`newEntryTitle${entryId}`).value;
        const description = document.getElementById(`newEntryDescription${entryId}`).value;
        
        if (!title) {
            showNotification('Please enter a title for the new entry', 'error');
            return;
        }
        
        data.name = title;
        data.description = description;
        
        // Submit to new endpoint
        submitNewEntryRelationship(entryId, data);
    } else {
        // Add existing entry
        const relatedEntryId = document.getElementById(`relatedEntry${entryId}`).value;
        
        if (!relatedEntryId) {
            showNotification('Please select an entry', 'error');
            return;
        }
        
        data.related_entry_id = relatedEntryId;
        
        // Add quantity and unit if fields are visible
        const quantityField = document.getElementById(`relationshipQuantity${entryId}`);
        const unitField = document.getElementById(`relationshipUnit${entryId}`);
        
        if (quantityField && quantityField.offsetParent !== null) {
            data.quantity = quantityField.value;
            data.unit = unitField.value;
        }
        
        // Submit to existing endpoint
        submitExistingEntryRelationship(entryId, data);
    }
}

// Submit existing entry relationship
function submitExistingEntryRelationship(entryId, data) {
    fetch(`/api/entries/${entryId}/relationships`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(result => {
        if (result.success || result.message) {
            showBanner('Relationship added successfully', 'success');
            
            // Close modal
            const modal = bootstrap.Modal.getInstance(document.getElementById(`addRelationshipModal${entryId}`));
            if (modal) modal.hide();
            
            // Reload page to show new relationship
            setTimeout(() => window.location.reload(), 500);
        } else {
            throw new Error(result.error || 'Failed to add relationship');
        }
    })
    .catch(error => {
        console.error('Error adding relationship:', error);
        showNotification(error.message, 'error');
    });
}

// Submit new entry relationship
function submitNewEntryRelationship(entryId, data) {
    fetch(`/api/entries/${entryId}/relationships/new`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(result => {
        if (result.success || result.message) {
            showBanner('New entry and relationship created successfully', 'success');
            
            // Close modal
            const modal = bootstrap.Modal.getInstance(document.getElementById(`addRelationshipModal${entryId}`));
            if (modal) modal.hide();
            
            // Reload page to show new relationship
            setTimeout(() => window.location.reload(), 500);
        } else {
            throw new Error(result.error || 'Failed to create entry and relationship');
        }
    })
    .catch(error => {
        console.error('Error creating entry and relationship:', error);
        showNotification(error.message, 'error');
    });
}

// Show notification (assumes you have a notification system)
function showNotification(message, type = 'info') {
    // TODO: Integrate with your notification system
    console.log(`[${type.toUpperCase()}] ${message}`);
    
    // Fallback to alert if no notification system
    if (type === 'error') {
        alert(`Error: ${message}`);
    }
}

// Escape HTML to prevent XSS
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Export functions for global access
window.initializeRelationshipsSection = initializeRelationshipsSection;
window.retryLoadHierarchy = retryLoadHierarchy;
