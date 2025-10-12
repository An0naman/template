/**
 * Hierarchical Relationship Filter System
 * Supports nested groups with AND/OR logic
 */

class HierarchicalFilterManager {
    constructor(containerId, noFiltersMessageId) {
        this.container = document.getElementById(containerId);
        this.noFiltersMessage = document.getElementById(noFiltersMessageId);
        this.filterTree = []; // Root level array of filters and groups
        this.relationshipDefinitions = [];
        this.allEntries = [];
        this.filterIdCounter = 1;
        this.selectedTypeId = null;
    }

    async loadData() {
        try {
            // Load relationship definitions
            const relDefResponse = await fetch('/api/relationship_definitions');
            if (relDefResponse.ok) {
                this.relationshipDefinitions = await relDefResponse.json();
            }
            
            // Load all entries for target selection
            const entriesResponse = await fetch('/api/entries');
            if (entriesResponse.ok) {
                this.allEntries = await entriesResponse.json();
            }
        } catch (error) {
            console.error('Error loading relationship data:', error);
        }
    }

    setSelectedTypeId(typeId) {
        this.selectedTypeId = typeId ? parseInt(typeId) : null;
    }

    addFilter(parentArray = null) {
        const filter = {
            type: 'filter',
            id: this.filterIdCounter++,
            relationship_def_id: null,
            target_entry_id: null,
            direction: 'to',
            operator: null // Will be set by UI
        };
        
        if (parentArray === null) {
            this.filterTree.push(filter);
        } else {
            parentArray.push(filter);
        }
        
        this.render();
        return filter;
    }

    addGroup(parentArray = null) {
        const group = {
            type: 'group',
            id: this.filterIdCounter++,
            operator: null, // Will be set by UI
            filters: []
        };
        
        if (parentArray === null) {
            this.filterTree.push(group);
        } else {
            parentArray.push(group);
        }
        
        this.render();
        return group;
    }

    removeItem(itemId, parentArray = null) {
        const array = parentArray || this.filterTree;
        const index = array.findIndex(item => item.id === itemId);
        
        if (index !== -1) {
            array.splice(index, 1);
            this.render();
            return true;
        }
        
        // Search in nested groups
        for (const item of array) {
            if (item.type === 'group') {
                if (this.removeItem(itemId, item.filters)) {
                    return true;
                }
            }
        }
        
        return false;
    }

    findItem(itemId, array = null) {
        const searchArray = array || this.filterTree;
        
        for (const item of searchArray) {
            if (item.id === itemId) {
                return item;
            }
            if (item.type === 'group') {
                const found = this.findItem(itemId, item.filters);
                if (found) return found;
            }
        }
        
        return null;
    }

    updateFilter(filterId, updates) {
        const filter = this.findItem(filterId);
        if (filter && filter.type === 'filter') {
            Object.assign(filter, updates);
        }
    }

    render() {
        // Clear container
        this.container.innerHTML = '';
        
        if (this.filterTree.length === 0) {
            this.noFiltersMessage.style.display = 'block';
            return;
        }
        
        this.noFiltersMessage.style.display = 'none';
        this.renderItems(this.filterTree, this.container, 0);
    }

    renderItems(items, parentElement, depth = 0) {
        items.forEach((item, index) => {
            // Create wrapper for operator + item
            const wrapper = document.createElement('div');
            wrapper.className = 'filter-tree-item';
            if (depth > 0) {
                wrapper.classList.add(`indent-level-${Math.min(depth, 3)}`);
            }
            
            // Add operator selector (except for first item)
            if (index > 0) {
                const operatorSpan = document.createElement('span');
                operatorSpan.className = `filter-operator operator-${(item.operator || 'and').toLowerCase()}`;
                operatorSpan.textContent = item.operator || 'AND';
                operatorSpan.title = 'Click to toggle AND/OR';
                operatorSpan.onclick = () => {
                    item.operator = item.operator === 'AND' ? 'OR' : 'AND';
                    this.render();
                    this.onFilterChange();
                };
                wrapper.appendChild(operatorSpan);
            }
            
            if (item.type === 'filter') {
                wrapper.appendChild(this.renderFilter(item, depth));
            } else if (item.type === 'group') {
                wrapper.appendChild(this.renderGroup(item, depth));
            }
            
            parentElement.appendChild(wrapper);
        });
    }

    renderFilter(filter, depth) {
        const filterDiv = document.createElement('div');
        filterDiv.className = 'filter-item';
        filterDiv.dataset.filterId = filter.id;
        
        // Get filtered relationship definitions
        let filteredRelationships = this.relationshipDefinitions;
        if (this.selectedTypeId) {
            filteredRelationships = this.relationshipDefinitions.filter(rd => 
                rd.entry_type_id_from === this.selectedTypeId || rd.entry_type_id_to === this.selectedTypeId
            );
        }
        
        filterDiv.innerHTML = `
            <div class="row g-2 align-items-center">
                <div class="col-md-4">
                    <label class="form-label small mb-1">Relationship Type</label>
                    <select class="form-select form-select-sm rel-type-select">
                        <option value="">Select relationship...</option>
                        ${filteredRelationships.map(rd => `
                            <option value="${rd.id}" 
                                    data-from-type="${rd.entry_type_id_from}" 
                                    data-to-type="${rd.entry_type_id_to}"
                                    ${filter.relationship_def_id == rd.id ? 'selected' : ''}>
                                ${rd.name}
                            </option>
                        `).join('')}
                    </select>
                </div>
                <div class="col-md-2">
                    <label class="form-label small mb-1">Direction</label>
                    <select class="form-select form-select-sm rel-direction-select">
                        <option value="to" ${filter.direction === 'to' ? 'selected' : ''}>→ To</option>
                        <option value="from" ${filter.direction === 'from' ? 'selected' : ''}>← From</option>
                    </select>
                </div>
                <div class="col-md-4">
                    <label class="form-label small mb-1">Target Entry</label>
                    <select class="form-select form-select-sm rel-target-select">
                        <option value="">Select entry...</option>
                    </select>
                </div>
                <div class="col-md-2 text-end">
                    <label class="form-label small mb-1 d-block">&nbsp;</label>
                    <button type="button" class="btn btn-sm btn-outline-danger remove-filter-btn">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
        `;
        
        // Setup event listeners
        const relTypeSelect = filterDiv.querySelector('.rel-type-select');
        const directionSelect = filterDiv.querySelector('.rel-direction-select');
        const targetSelect = filterDiv.querySelector('.rel-target-select');
        const removeBtn = filterDiv.querySelector('.remove-filter-btn');
        
        // Update target options based on relationship type
        const updateTargetOptions = () => {
            const selectedRelDef = this.relationshipDefinitions.find(rd => rd.id == relTypeSelect.value);
            if (!selectedRelDef) {
                targetSelect.innerHTML = `
                    <option value="">Select entry...</option>
                    ${this.allEntries.map(entry => `
                        <option value="${entry.id}">${entry.title} (${entry.entry_type_label || 'Unknown'})</option>
                    `).join('')}
                `;
                return;
            }
            
            const direction = directionSelect.value;
            const targetTypeId = direction === 'to' ? selectedRelDef.entry_type_id_to : selectedRelDef.entry_type_id_from;
            const filteredEntries = this.allEntries.filter(e => e.entry_type_id === targetTypeId);
            
            targetSelect.innerHTML = `
                <option value="">Select entry...</option>
                ${filteredEntries.map(entry => `
                    <option value="${entry.id}" ${filter.target_entry_id == entry.id ? 'selected' : ''}>
                        ${entry.title} (${entry.entry_type_label || 'Unknown'})
                    </option>
                `).join('')}
            `;
            
            // Restore selection if it was set
            if (filter.target_entry_id) {
                targetSelect.value = filter.target_entry_id;
            }
        };
        
        relTypeSelect.addEventListener('change', () => {
            filter.relationship_def_id = relTypeSelect.value ? parseInt(relTypeSelect.value) : null;
            updateTargetOptions();
            this.onFilterChange();
        });
        
        directionSelect.addEventListener('change', () => {
            filter.direction = directionSelect.value;
            updateTargetOptions();
            this.onFilterChange();
        });
        
        targetSelect.addEventListener('change', () => {
            filter.target_entry_id = targetSelect.value ? parseInt(targetSelect.value) : null;
            this.onFilterChange();
        });
        
        removeBtn.addEventListener('click', () => {
            this.removeItem(filter.id);
            this.onFilterChange();
        });
        
        // Initialize target options
        updateTargetOptions();
        
        return filterDiv;
    }

    renderGroup(group, depth) {
        const groupDiv = document.createElement('div');
        groupDiv.className = 'filter-group';
        groupDiv.dataset.groupId = group.id;
        
        // Group header with controls
        const header = document.createElement('div');
        header.className = 'filter-group-header';
        header.innerHTML = `
            <span class="badge bg-primary">
                <i class="fas fa-layer-group me-1"></i>Group
            </span>
            <div class="btn-group btn-group-sm">
                <button type="button" class="btn btn-sm btn-outline-primary add-filter-to-group-btn" title="Add filter to group">
                    <i class="fas fa-plus"></i> Filter
                </button>
                <button type="button" class="btn btn-sm btn-outline-secondary add-group-to-group-btn" title="Add nested group">
                    <i class="fas fa-layer-group"></i> Group
                </button>
                <button type="button" class="btn btn-sm btn-outline-danger remove-group-btn" title="Delete group">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        `;
        
        groupDiv.appendChild(header);
        
        // Group content
        const content = document.createElement('div');
        content.className = 'filter-group-content mt-2';
        
        if (group.filters.length === 0) {
            content.innerHTML = '<p class="text-muted small mb-0"><i class="fas fa-info-circle me-1"></i>Empty group - add filters or nested groups</p>';
        } else {
            this.renderItems(group.filters, content, depth + 1);
        }
        
        groupDiv.appendChild(content);
        
        // Event listeners
        header.querySelector('.add-filter-to-group-btn').addEventListener('click', () => {
            this.addFilter(group.filters);
            this.onFilterChange();
        });
        
        header.querySelector('.add-group-to-group-btn').addEventListener('click', () => {
            this.addGroup(group.filters);
            this.onFilterChange();
        });
        
        header.querySelector('.remove-group-btn').addEventListener('click', () => {
            this.removeItem(group.id);
            this.onFilterChange();
        });
        
        return groupDiv;
    }

    // Convert tree to flat array for API
    toFilterArray() {
        const result = [];
        this.flattenTree(this.filterTree, result);
        return result;
    }

    flattenTree(items, result, parentOperator = null) {
        items.forEach((item, index) => {
            if (item.type === 'filter' && item.relationship_def_id && item.target_entry_id) {
                result.push({
                    relationship_def_id: item.relationship_def_id,
                    target_entry_id: item.target_entry_id,
                    direction: item.direction,
                    operator: index === 0 ? parentOperator : item.operator
                });
            } else if (item.type === 'group' && item.filters.length > 0) {
                this.flattenTree(item.filters, result, index === 0 ? parentOperator : item.operator);
            }
        });
    }

    // Load tree from saved data
    loadTree(treeData) {
        this.filterTree = treeData || [];
        this.render();
    }

    // Export tree for saving
    exportTree() {
        return this.filterTree;
    }

    // Callback when filters change
    onFilterChange() {
        // Override this in implementation
    }

    clearAllFilters() {
        this.filterTree = [];
        this.render();
        this.onFilterChange();
    }
}

// Make it globally available
window.HierarchicalFilterManager = HierarchicalFilterManager;
