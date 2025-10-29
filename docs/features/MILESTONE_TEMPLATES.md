# Milestone Templates Feature

## Overview

Allow entries to save their milestone plans as templates that can be shared with related entry types. This enables reusable project planning across multiple entries.

## User Story

**As a user**, I want to:
1. Mark an entry's milestones as a template
2. Define which entry types can use these templates
3. Browse available templates when working on related entries
4. Import milestone plans from templates to new entries

## Architecture

### Database Schema Changes

#### 1. Add Template Flags to Entry Table

```sql
ALTER TABLE Entry ADD COLUMN is_milestone_template BOOLEAN DEFAULT 0;
ALTER TABLE Entry ADD COLUMN template_name TEXT;
ALTER TABLE Entry ADD COLUMN template_description TEXT;
```

- `is_milestone_template`: Whether this entry serves as a milestone template
- `template_name`: Friendly name for the template (e.g., "Standard Software Release")
- `template_description`: Description of what this template is for

#### 2. Create EntryTypeRelationship Table

```sql
CREATE TABLE EntryTypeRelationship (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    from_entry_type_id INTEGER NOT NULL,
    to_entry_type_id INTEGER NOT NULL,
    relationship_type TEXT NOT NULL, -- 'template_source', 'template_target', 'bidirectional'
    can_share_templates BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (from_entry_type_id) REFERENCES EntryType(id) ON DELETE CASCADE,
    FOREIGN KEY (to_entry_type_id) REFERENCES EntryType(id) ON DELETE CASCADE,
    UNIQUE(from_entry_type_id, to_entry_type_id)
);
```

This table defines which entry types can share milestone templates with each other.

#### 3. Add Template Distribution Flag

```sql
ALTER TABLE Entry ADD COLUMN template_distribution_status TEXT DEFAULT 'private';
-- Values: 'private', 'marked_for_distribution', 'distributed'
```

- `private`: Template is personal, not shared
- `marked_for_distribution`: Ready to be used by others
- `distributed`: Actively being used as a template source

### Database Migration Considerations

**For Docker App Instances:**
Each app instance has its own independent SQLite database (`data/template.db`). The migration must:
1. Run automatically on app startup
2. Be idempotent (safe to run multiple times)
3. Not break existing data
4. Work across all deployed instances

**Migration File**: `migrations/add_milestone_templates.py`

### API Endpoints

#### Template Management

```
GET    /api/entries/<entry_id>/milestone-template
  - Get template status and configuration
  - Response: { is_template, template_name, template_description, distribution_status, milestone_count }

PUT    /api/entries/<entry_id>/milestone-template
  - Mark/unmark entry as template
  - Body: { is_template, template_name, template_description }
  - Response: { success, message }

PUT    /api/entries/<entry_id>/milestone-template/distribution
  - Set distribution status
  - Body: { distribution_status: 'private' | 'marked_for_distribution' }
  - Response: { success, message }
```

#### Entry Type Relationships

```
GET    /api/entry-types/<type_id>/relationships
  - Get all entry types related to this one
  - Response: [{ id, name, relationship_type, can_share_templates }]

POST   /api/entry-types/relationships
  - Create relationship between entry types
  - Body: { from_type_id, to_type_id, relationship_type, can_share_templates }
  - Response: { success, relationship_id }

PUT    /api/entry-types/relationships/<rel_id>
  - Update relationship settings
  - Body: { can_share_templates }
  - Response: { success }

DELETE /api/entry-types/relationships/<rel_id>
  - Remove relationship
  - Response: { success }
```

#### Template Discovery & Import

```
GET    /api/entries/<entry_id>/available-templates
  - Get all templates available for this entry's type
  - Filters templates from related entry types
  - Response: [{ template_entry_id, template_name, description, milestone_count, owner_entry_type }]

POST   /api/entries/<entry_id>/import-template
  - Import milestones from a template
  - Body: { template_entry_id, import_mode: 'replace' | 'append' }
  - Response: { success, imported_count, milestones: [...] }
```

### UI Implementation

#### 1. Progress & Status Section Enhancement

**Location**: Entry details page, Progress & Status section

**New Controls**:

```html
<!-- Template Status Badge (shown when entry is a template) -->
<div class="template-status-badge" v-if="isTemplate">
    <i class="fas fa-layer-group"></i>
    <span>Milestone Template: {{ templateName }}</span>
    <span class="badge" :class="distributionBadgeClass">
        {{ distributionStatus }}
    </span>
</div>

<!-- Manage Milestones Button Enhancement -->
<div class="milestone-controls">
    <button class="btn btn-sm btn-outline-primary" id="manageMilestonesBtn">
        <i class="fas fa-diamond me-1"></i>
        <span>Manage Milestones</span>
    </button>
    
    <!-- Template Actions Dropdown -->
    <div class="btn-group">
        <button class="btn btn-sm btn-outline-secondary dropdown-toggle" 
                data-bs-toggle="dropdown">
            <i class="fas fa-layer-group me-1"></i>
            <span>Template</span>
        </button>
        <ul class="dropdown-menu">
            <li>
                <a class="dropdown-item" href="#" 
                   @click="configureAsTemplate">
                    <i class="fas fa-cog me-2"></i>
                    {{ isTemplate ? 'Edit Template Settings' : 'Save as Template' }}
                </a>
            </li>
            <li v-if="isTemplate">
                <a class="dropdown-item" href="#" 
                   @click="toggleDistribution">
                    <i class="fas fa-share-alt me-2"></i>
                    {{ distributionStatus === 'marked_for_distribution' ? 
                       'Unmark for Distribution' : 'Mark for Distribution' }}
                </a>
            </li>
            <li>
                <a class="dropdown-item" href="#" 
                   @click="browseTemplates">
                    <i class="fas fa-download me-2"></i>
                    Import from Template
                </a>
            </li>
        </ul>
    </div>
</div>
```

#### 2. Template Configuration Modal

```html
<div class="modal" id="templateConfigModal">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">
                    <i class="fas fa-layer-group me-2"></i>
                    Configure Milestone Template
                </h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body">
                <div class="alert alert-info">
                    <i class="fas fa-info-circle me-2"></i>
                    Mark this entry's milestone plan as a reusable template.
                </div>
                
                <div class="mb-3">
                    <label class="form-label">Template Name *</label>
                    <input type="text" class="form-control" 
                           v-model="templateConfig.name"
                           placeholder="e.g., Standard Software Release Process">
                    <small class="text-muted">
                        A descriptive name for this milestone plan
                    </small>
                </div>
                
                <div class="mb-3">
                    <label class="form-label">Description</label>
                    <textarea class="form-control" rows="3"
                              v-model="templateConfig.description"
                              placeholder="Describe when to use this template..."></textarea>
                </div>
                
                <div class="mb-3">
                    <label class="form-label">Current Milestones</label>
                    <div class="milestone-preview">
                        <div v-for="milestone in milestones" :key="milestone.id"
                             class="milestone-item">
                            <span class="milestone-badge" 
                                  :style="{backgroundColor: milestone.target_state_color}">
                                {{ milestone.order_position }}
                            </span>
                            <span class="milestone-name">
                                {{ milestone.target_state_name }}
                            </span>
                            <span class="milestone-duration">
                                {{ milestone.duration_days }}d
                            </span>
                        </div>
                    </div>
                    <small class="text-muted">
                        {{ milestones.length }} milestone(s) will be included
                    </small>
                </div>
                
                <div class="form-check">
                    <input class="form-check-input" type="checkbox" 
                           v-model="templateConfig.markForDistribution"
                           id="markForDistribution">
                    <label class="form-check-label" for="markForDistribution">
                        Mark for distribution immediately
                    </label>
                    <small class="form-text text-muted d-block">
                        Makes this template available to other entries of related types
                    </small>
                </div>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" 
                        data-bs-dismiss="modal">Cancel</button>
                <button type="button" class="btn btn-primary" 
                        @click="saveTemplateConfig">
                    <i class="fas fa-save me-2"></i>Save Template
                </button>
            </div>
        </div>
    </div>
</div>
```

#### 3. Template Browser Modal

```html
<div class="modal modal-lg" id="templateBrowserModal">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">
                    <i class="fas fa-download me-2"></i>
                    Import Milestone Template
                </h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body">
                <div v-if="availableTemplates.length === 0" 
                     class="alert alert-warning">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    No milestone templates available for this entry type.
                    <hr>
                    <small>
                        To create templates:
                        <ol>
                            <li>Define entry type relationships in Settings</li>
                            <li>Create milestones on an entry</li>
                            <li>Mark it as a template for distribution</li>
                        </ol>
                    </small>
                </div>
                
                <div v-else>
                    <p class="text-muted">
                        Select a template to import into this entry. 
                        You can choose to replace existing milestones or append to them.
                    </p>
                    
                    <div class="template-list">
                        <div v-for="template in availableTemplates" 
                             :key="template.template_entry_id"
                             class="template-card"
                             :class="{selected: selectedTemplate === template}"
                             @click="selectedTemplate = template">
                            
                            <div class="template-card-header">
                                <div class="template-info">
                                    <h6 class="template-name">
                                        <i class="fas fa-layer-group me-2"></i>
                                        {{ template.template_name }}
                                    </h6>
                                    <small class="template-type">
                                        From: {{ template.owner_entry_type }}
                                    </small>
                                </div>
                                <div class="template-stats">
                                    <span class="badge bg-primary">
                                        {{ template.milestone_count }} milestones
                                    </span>
                                </div>
                            </div>
                            
                            <div class="template-card-body" v-if="template.description">
                                <p class="template-description">
                                    {{ template.description }}
                                </p>
                            </div>
                            
                            <!-- Milestone Preview -->
                            <div class="template-milestones-preview" 
                                 v-if="selectedTemplate === template && template.milestones">
                                <div class="milestone-timeline">
                                    <div v-for="m in template.milestones" 
                                         :key="m.id"
                                         class="milestone-preview-item"
                                         :style="{width: (m.duration_days / template.total_days * 100) + '%',
                                                 backgroundColor: m.target_state_color}">
                                        <span class="milestone-label">
                                            {{ m.target_state_name }} ({{ m.duration_days }}d)
                                        </span>
                                    </div>
                                </div>
                                <small class="text-muted">
                                    Total duration: {{ template.total_days }} days
                                </small>
                            </div>
                        </div>
                    </div>
                    
                    <div class="mt-3" v-if="selectedTemplate">
                        <label class="form-label">Import Mode</label>
                        <div class="btn-group w-100" role="group">
                            <input type="radio" class="btn-check" 
                                   v-model="importMode" 
                                   value="replace" 
                                   id="importReplace">
                            <label class="btn btn-outline-primary" for="importReplace">
                                <i class="fas fa-trash-restore me-2"></i>
                                Replace Existing
                            </label>
                            
                            <input type="radio" class="btn-check" 
                                   v-model="importMode" 
                                   value="append" 
                                   id="importAppend">
                            <label class="btn btn-outline-primary" for="importAppend">
                                <i class="fas fa-plus me-2"></i>
                                Append to Existing
                            </label>
                        </div>
                        <small class="form-text text-muted d-block mt-1">
                            <span v-if="importMode === 'replace'">
                                ⚠️ This will delete all existing milestones and replace them with the template
                            </span>
                            <span v-else>
                                ℹ️ Template milestones will be added after your existing ones
                            </span>
                        </small>
                    </div>
                </div>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" 
                        data-bs-dismiss="modal">Cancel</button>
                <button type="button" class="btn btn-primary" 
                        @click="importTemplate"
                        :disabled="!selectedTemplate">
                    <i class="fas fa-download me-2"></i>
                    Import Template
                </button>
            </div>
        </div>
    </div>
</div>
```

#### 4. Entry Type Relationships Management (Settings)

**Location**: Settings → Data Structure → Entry Type Relationships

```html
<div class="card">
    <div class="card-header">
        <h5>
            <i class="fas fa-project-diagram me-2"></i>
            Entry Type Relationships
        </h5>
        <p class="text-muted mb-0">
            Define which entry types can share milestone templates
        </p>
    </div>
    <div class="card-body">
        <button class="btn btn-primary mb-3" @click="showAddRelationship">
            <i class="fas fa-plus me-2"></i>
            Add Relationship
        </button>
        
        <table class="table">
            <thead>
                <tr>
                    <th>From Type</th>
                    <th>To Type</th>
                    <th>Relationship</th>
                    <th>Share Templates</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody>
                <tr v-for="rel in relationships" :key="rel.id">
                    <td>{{ rel.from_type_name }}</td>
                    <td>{{ rel.to_type_name }}</td>
                    <td>
                        <span class="badge bg-info">
                            {{ rel.relationship_type }}
                        </span>
                    </td>
                    <td>
                        <div class="form-check form-switch">
                            <input class="form-check-input" 
                                   type="checkbox"
                                   v-model="rel.can_share_templates"
                                   @change="updateRelationship(rel)">
                        </div>
                    </td>
                    <td>
                        <button class="btn btn-sm btn-outline-danger" 
                                @click="deleteRelationship(rel.id)">
                            <i class="fas fa-trash"></i>
                        </button>
                    </td>
                </tr>
            </tbody>
        </table>
    </div>
</div>
```

### Workflow Examples

#### Example 1: Creating a Template

1. User creates an entry "Software Release v1.0" with milestones:
   - Planning (7 days)
   - Development (21 days)
   - Testing (7 days)
   - Deployment (2 days)

2. User clicks **Template** → **Save as Template**
3. Fills in:
   - Template Name: "Standard Software Release Process"
   - Description: "Use for all software releases"
   - ☑ Mark for distribution

4. System saves template configuration to Entry table
5. Template appears in template browser for related entry types

#### Example 2: Using a Template

1. User creates new entry "Mobile App Release v2.0"
2. Entry type is "Software Project" (related to "Release" type)
3. User clicks **Template** → **Import from Template**
4. Browses available templates:
   - Sees "Standard Software Release Process" (4 milestones, 37 days)
5. Selects template and chooses "Replace Existing"
6. Clicks "Import Template"
7. All 4 milestones are imported with original durations and states
8. User can adjust durations as needed for this specific release

#### Example 3: Managing Relationships

1. Admin goes to Settings → Entry Type Relationships
2. Clicks "Add Relationship"
3. Selects:
   - From: "Software Project"
   - To: "Release"
   - Relationship: "bidirectional"
   - ☑ Can share templates
4. Saves relationship
5. Now both types can share milestone templates

### Implementation Files

```
migrations/
  └── add_milestone_templates.py          # Database migration

app/api/
  ├── milestone_template_api.py           # Template CRUD endpoints
  └── entry_type_relationship_api.py      # Relationship management

app/templates/
  ├── modals/
  │   ├── template_config_modal.html      # Template configuration
  │   └── template_browser_modal.html     # Template import
  └── settings/
      └── entry_type_relationships.html   # Relationship management UI

app/static/js/
  ├── milestone_templates.js              # Template management logic
  └── entry_type_relationships.js         # Relationship UI logic

docs/features/
  └── MILESTONE_TEMPLATES.md              # This file
```

### Security Considerations

1. **Template Visibility**:
   - Templates are only visible to entries with related types
   - Private templates never appear in browser
   - Distribution flag must be explicitly set

2. **Import Validation**:
   - Verify template source entry exists
   - Check entry type relationship exists
   - Validate milestone data integrity
   - Prevent circular references

3. **Database Isolation**:
   - Each Docker app instance has independent database
   - Templates cannot cross app boundaries
   - No shared state between instances

### Docker Deployment Notes

**Migration Execution**:
- Migration runs on container startup
- Handled by `init_db()` in `app/db.py`
- Safe for rolling updates

**Data Persistence**:
- Templates stored in `data/template.db`
- Persisted via Docker volume mount
- Survives container restarts

**Multi-Instance Isolation**:
- Each app instance (homebrews, projects, etc.) has separate templates
- No cross-contamination between instances
- Templates are app-specific resources

### Testing Checklist

- [ ] Migration runs successfully on fresh database
- [ ] Migration runs successfully on existing database
- [ ] Template can be created from entry with milestones
- [ ] Template can be marked/unmarked for distribution
- [ ] Relationship can be created between entry types
- [ ] Templates only appear for related entry types
- [ ] Template import replaces existing milestones correctly
- [ ] Template import appends to existing milestones correctly
- [ ] Template UI shows correct status badges
- [ ] Settings page manages relationships correctly
- [ ] Works across Docker app instance restart
- [ ] Multiple instances don't interfere with each other

### Future Enhancements

1. **Template Versioning**: Track template changes over time
2. **Template Tags**: Categorize templates for easier discovery
3. **Template Sharing**: Export/import templates between app instances
4. **Template Analytics**: Track template usage and success rates
5. **Smart Recommendations**: Suggest templates based on entry type and history
6. **Template Variants**: Create template variations (optimistic/pessimistic timelines)
