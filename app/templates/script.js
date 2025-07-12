document.addEventListener('DOMContentLoaded', function() {
    // --- Global DOM Element References ---
    const entryTypeForm = document.getElementById('entryTypeForm');
    const entryTypeFormTitle = document.getElementById('entryTypeFormTitle');
    const saveEntryTypeBtn = document.getElementById('saveEntryTypeBtn');
    const cancelEditEntryTypeBtn = document.getElementById('cancelEditEntryTypeBtn');
    const entryTypeIsPrimaryCheckbox = document.getElementById('entryTypeIsPrimary');
    const entryTypeModal = new bootstrap.Modal(document.getElementById('entryTypeModal'));
    const entryTypesTableBody = document.getElementById('entryTypesTableBody');

    const manageRelationshipsModal = new bootstrap.Modal(document.getElementById('manageRelationshipsModal'));
    const relationshipDefinitionForm = document.getElementById('relationshipDefinitionForm');
    const relationshipFormTitle = document.getElementById('relationshipFormTitle');
    const saveRelationshipBtn = document.getElementById('saveRelationshipBtn');
    const cancelEditRelationshipBtn = document.getElementById('cancelEditRelationshipBtn');
    const showAddRelationshipFormBtn = document.getElementById('showAddRelationshipFormBtn');

    let allEntryTypes = []; // This array will store all fetched entry types

    // --- Function to Load Entry Types ---
    async function loadEntryTypes() {
        try {
            const response = await fetch('/api/entry_types');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            allEntryTypes = data; // Store the fetched entry types globally

            // Populate the Entry Types table
            if (entryTypesTableBody) {
                entryTypesTableBody.innerHTML = ''; // Clear existing rows
                if (data.length === 0) {
                    entryTypesTableBody.innerHTML = '<tr><td colspan="6" class="text-center text-muted">No entry types found.</td></tr>';
                }
                data.forEach(type => {
                    const row = entryTypesTableBody.insertRow();
                    row.insertCell().textContent = type.id;
                    row.insertCell().textContent = type.name;
                    row.insertCell().textContent = type.singular_label;
                    row.insertCell().textContent = type.plural_label;
                    row.insertCell().innerHTML = type.is_primary ? '<i class="fas fa-check-circle text-success"></i> Yes' : '<i class="fas fa-times-circle text-danger"></i> No';
                    const actionsCell = row.insertCell();

                    const editBtn = document.createElement('button');
                    editBtn.innerHTML = '<i class="fas fa-edit"></i> Edit';
                    editBtn.classList.add('btn', 'btn-sm', 'btn-outline-primary', 'me-1');
                    editBtn.onclick = () => editEntryType(type);
                    actionsCell.appendChild(editBtn);

                    const deleteBtn = document.createElement('button');
                    deleteBtn.innerHTML = '<i class="fas fa-trash-alt"></i> Delete';
                    deleteBtn.classList.add('btn', 'btn-sm', 'btn-outline-danger');
                    deleteBtn.onclick = () => deleteEntryType(type.id, type.name);
                    actionsCell.appendChild(deleteBtn);
                });
            }

            // Ensure relationship dropdowns are populated after entry types load
            populateRelationshipEntryTypeDropdowns();

        } catch (error) {
            console.error('Error loading entry types:', error);
            if (entryTypesTableBody) {
                entryTypesTableBody.innerHTML = '<tr><td colspan="6" class="text-center text-danger">Failed to load entry types. Please check server logs.</td></tr>';
            }
        }
    }

    function resetEntryTypeForm() {
        entryTypeForm.reset();
        document.getElementById('entryTypeId').value = '';
        entryTypeFormTitle.textContent = 'Add New Entry Type';
        saveEntryTypeBtn.innerHTML = '<i class="fas fa-plus-circle me-1"></i> Add Entry Type';
        saveEntryTypeBtn.classList.remove('btn-warning');
        saveEntryTypeBtn.classList.add('btn-primary');
        cancelEditEntryTypeBtn.style.display = 'none';
        document.getElementById('entryTypeName').readOnly = false;
        document.getElementById('entryTypeNoteTypes').value = 'General';
        entryTypeIsPrimaryCheckbox.checked = false;
    }

    document.getElementById('showAddEntryTypeFormBtn').addEventListener('click', function() {
        resetEntryTypeForm();
        entryTypeModal.show();
    });

    function editEntryType(type) {
        entryTypeFormTitle.textContent = `Edit Entry Type: ${type.name}`;
        saveEntryTypeBtn.innerHTML = '<i class="fas fa-save me-1"></i> Save Changes';
        saveEntryTypeBtn.classList.remove('btn-primary');
        saveEntryTypeBtn.classList.add('btn-warning');
        cancelEditEntryTypeBtn.style.display = 'inline-block';

        document.getElementById('entryTypeId').value = type.id;
        document.getElementById('entryTypeName').value = type.name;
        document.getElementById('entryTypeName').readOnly = true; // Prevent changing name for existing
        document.getElementById('entryTypeSingularLabel').value = type.singular_label;
        document.getElementById('entryTypePluralLabel').value = type.plural_label;
        document.getElementById('entryTypeDescription').value = type.description || '';
        document.getElementById('entryTypeNoteTypes').value = type.note_types || 'General';
        entryTypeIsPrimaryCheckbox.checked = type.is_primary === 1;

        entryTypeModal.show();
    }

    function deleteEntryType(id, name) {
        if (confirm(`Are you sure you want to delete the entry type "${name}"? This action cannot be undone and will fail if entries or relationship definitions are linked to it.`)) {
            fetch(`/api/entry_types/${id}`, {
                method: 'DELETE',
            })
            .then(response => response.json()) // Always parse JSON to get error messages
            .then(data => {
                if (data.message) {
                    alert(data.message);
                    loadEntryTypes(); // Reload the list
                } else if (data.error) {
                    alert('Error deleting entry type: ' + data.error);
                }
            })
            .catch(error => {
                console.error('Error deleting entry type:', error);
                alert('An error occurred while deleting the entry type.');
            });
        }
    }

    entryTypeForm.addEventListener('submit', function(event) {
        event.preventDefault();
        const id = document.getElementById('entryTypeId').value;
        const name = document.getElementById('entryTypeName').value;
        const singular_label = document.getElementById('entryTypeSingularLabel').value;
        const plural_label = document.getElementById('entryTypePluralLabel').value;
        const description = document.getElementById('entryTypeDescription').value;
        const note_types = document.getElementById('entryTypeNoteTypes').value;
        const is_primary = entryTypeIsPrimaryCheckbox.checked ? 1 : 0;

        const method = id ? 'PATCH' : 'POST';
        const url = id ? `/api/entry_types/${id}` : '/api/entry_types';

        fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ name, singular_label, plural_label, description, note_types, is_primary }),
        })
        .then(response => response.json())
        .then(data => {
            if (data.message) {
                alert(data.message);
                entryTypeModal.hide();
                resetEntryTypeForm();
                loadEntryTypes(); // Reload the list
            } else if (data.error) {
                alert('Error: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error submitting entry type:', error);
            alert('An error occurred while saving the entry type.');
        });
    });

    // --- Relationship Definition Management Functions ---

    // Show Manage Relationships Modal
    document.getElementById('showManageRelationshipsModalBtn').addEventListener('click', function() {
        loadRelationshipDefinitions(); // Load existing relationships
        populateRelationshipEntryTypeDropdowns(); // Ensure dropdowns are fresh
        manageRelationshipsModal.show();
    });

    // Populate From/To Entry Type Dropdowns in Relationship Form
    function populateRelationshipEntryTypeDropdowns() {
        const fromSelect = document.getElementById('entryTypeFrom');
        const toSelect = document.getElementById('entryTypeTo');
        // Store current selected values to restore after repopulating
        const currentFromValue = fromSelect.value;
        const currentToValue = toSelect.value;

        fromSelect.innerHTML = '<option value="">Select From Entry Type</option>';
        toSelect.innerHTML = '<option value="">Select To Entry Type</option>';

        allEntryTypes.forEach(type => {
            const optionFrom = document.createElement('option');
            optionFrom.value = type.id;
            optionFrom.textContent = type.singular_label;
            fromSelect.appendChild(optionFrom);

            const optionTo = document.createElement('option');
            optionTo.value = type.id;
            optionTo.textContent = type.singular_label;
            toSelect.appendChild(optionTo);
        });

        // Restore selected values if they existed
        if (currentFromValue) fromSelect.value = currentFromValue;
        if (currentToValue) toSelect.value = currentToValue;
    }

    // Load and display Relationship Definitions
    function loadRelationshipDefinitions() {
        fetch('/api/relationship_definitions')
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                const tableBody = document.getElementById('relationshipDefinitionsTableBody');
                tableBody.innerHTML = '';
                if (data.length === 0) {
                    tableBody.innerHTML = '<tr><td colspan="9" class="text-center text-muted">No relationship definitions found.</td></tr>';
                }
                data.forEach(def => {
                    const row = tableBody.insertRow();
                    row.insertCell().textContent = def.id;
                    row.insertCell().textContent = def.name;
                    row.insertCell().textContent = def.entry_type_from_label; // Use label from JOIN
                    row.insertCell().textContent = def.entry_type_to_label; // Use label from JOIN
                    row.insertCell().textContent = `${def.cardinality_from} : ${def.cardinality_to}`;
                    row.insertCell().textContent = `"${def.label_from_side}" / "${def.label_to_side}"`;
                    row.insertCell().innerHTML = def.allow_quantity_unit ? '<i class="fas fa-check-circle text-success" title="Allows Quantity/Unit"></i> Yes' : '<i class="fas fa-times-circle text-danger" title="No Quantity/Unit"></i> No';
                    row.insertCell().innerHTML = def.is_active ? '<i class="fas fa-check-circle text-success" title="Active"></i> Yes' : '<i class="fas fa-times-circle text-danger" title="Inactive"></i> No';

                    const actionsCell = row.insertCell();

                    const editBtn = document.createElement('button');
                    editBtn.innerHTML = '<i class="fas fa-edit"></i>';
                    editBtn.classList.add('btn', 'btn-sm', 'btn-outline-primary', 'btn-action');
                    editBtn.title = 'Edit Relationship Definition';
                    editBtn.onclick = () => editRelationshipDefinition(def);
                    actionsCell.appendChild(editBtn);

                    const deleteBtn = document.createElement('button');
                    deleteBtn.innerHTML = '<i class="fas fa-trash-alt"></i>';
                    deleteBtn.classList.add('btn', 'btn-sm', 'btn-outline-danger', 'btn-action');
                    deleteBtn.title = 'Delete Relationship Definition';
                    deleteBtn.onclick = () => deleteRelationshipDefinition(def.id, def.name);
                    actionsCell.appendChild(deleteBtn);
                });
            })
            .catch(error => {
                console.error('Error loading relationship definitions:', error);
                document.getElementById('relationshipDefinitionsTableBody').innerHTML =
                    '<tr><td colspan="9" class="text-center text-danger">Failed to load relationship definitions. Please check server logs.</td></tr>';
            });
    }

    // Reset Relationship Form
    function resetRelationshipForm() {
        relationshipDefinitionForm.reset();
        document.getElementById('relationshipDefId').value = '';
        relationshipFormTitle.textContent = 'Add New Relationship Definition';
        saveRelationshipBtn.innerHTML = '<i class="fas fa-save me-1"></i> Add Relationship';
        saveRelationshipBtn.classList.remove('btn-warning');
        saveRelationshipBtn.classList.add('btn-primary');
        cancelEditRelationshipBtn.style.display = 'none';
        document.getElementById('relationshipName').readOnly = false; // Enable name editing for new
        document.getElementById('allowQuantityUnit').checked = false;
        document.getElementById('isActiveRelationship').checked = true;
        // Re-populate dropdowns to ensure fresh options and default selections
        populateRelationshipEntryTypeDropdowns();
    }

    // Show Add Relationship Form (within the modal)
    showAddRelationshipFormBtn.addEventListener('click', function() {
        resetRelationshipForm();
        // No need to show modal again, it's already open. Just reset form.
    });

    // Edit Relationship Definition - Populates form for editing
    function editRelationshipDefinition(def) {
        relationshipFormTitle.textContent = `Edit Relationship: ${def.name}`;
        saveRelationshipBtn.innerHTML = '<i class="fas fa-save me-1"></i> Save Changes';
        saveRelationshipBtn.classList.remove('btn-primary');
        saveRelationshipBtn.classList.add('btn-warning');
        cancelEditRelationshipBtn.style.display = 'inline-block';

        document.getElementById('relationshipDefId').value = def.id;
        document.getElementById('relationshipName').value = def.name;
        document.getElementById('relationshipName').readOnly = true; // Prevent changing name for existing
        document.getElementById('relationshipDescription').value = def.description || '';
        document.getElementById('entryTypeFrom').value = def.entry_type_id_from;
        document.getElementById('entryTypeTo').value = def.entry_type_id_to;
        document.getElementById('cardinalityFrom').value = def.cardinality_from;
        document.getElementById('cardinalityTo').value = def.cardinality_to;
        document.getElementById('labelFromSide').value = def.label_from_side;
        document.getElementById('labelToSide').value = def.label_to_side;
        document.getElementById('allowQuantityUnit').checked = def.allow_quantity_unit;
        document.getElementById('isActiveRelationship').checked = def.is_active;
    }

    // Delete Relationship Definition - Sends DELETE request
    function deleteRelationshipDefinition(id, name) {
        if (confirm(`Are you sure you want to delete the relationship definition "${name}"? This action will remove the definition and will fail if any active relationships are using it.`)) {
            fetch(`/api/relationship_definitions/${id}`, {
                method: 'DELETE',
            })
            .then(response => response.json())
            .then(data => {
                if (data.message) {
                    alert(data.message);
                    loadRelationshipDefinitions(); // Reload the list
                } else if (data.error) {
                    alert('Error deleting relationship definition: ' + data.error);
                }
            })
            .catch(error => {
                console.error('Error deleting relationship definition:', error);
                alert('An error occurred while deleting the relationship definition.');
            });
        }
    }


    // Handle Relationship Form Submission (Add/Edit) - Sends POST/PATCH request
    relationshipDefinitionForm.addEventListener('submit', async function(event) {
        event.preventDefault();

        const id = document.getElementById('relationshipDefId').value;
        const name = document.getElementById('relationshipName').value;
        const description = document.getElementById('relationshipDescription').value;
        // Parse to integer as database expects INT FK
        const entry_type_id_from = parseInt(document.getElementById('entryTypeFrom').value);
        const entry_type_id_to = parseInt(document.getElementById('entryTypeTo').value);
        const cardinality_from = document.getElementById('cardinalityFrom').value;
        const cardinality_to = document.getElementById('cardinalityTo').value;
        const label_from_side = document.getElementById('labelFromSide').value;
        const label_to_side = document.getElementById('labelToSide').value;
        // Checkbox values are booleans
        const allow_quantity_unit = document.getElementById('allowQuantityUnit').checked;
        const is_active = document.getElementById('isActiveRelationship').checked;

        // Basic client-side validation
        if (!name || isNaN(entry_type_id_from) || isNaN(entry_type_id_to) || !cardinality_from || !cardinality_to || !label_from_side || !label_to_side) {
            alert('Please fill in all required fields for the relationship definition.');
            return;
        }

        const method = id ? 'PATCH' : 'POST';
        const url = id ? `/api/relationship_definitions/${id}` : '/api/relationship_definitions';

        try {
            const response = await fetch(url, {
                method: method,
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    name: name,
                    description: description,
                    entry_type_id_from: entry_type_id_from,
                    entry_type_id_to: entry_type_id_to,
                    cardinality_from: cardinality_from,
                    cardinality_to: cardinality_to,
                    label_from_side: label_from_side,
                    label_to_side: label_to_side,
                    allow_quantity_unit: allow_quantity_unit,
                    is_active: is_active
                }),
            });

            const data = await response.json();
            if (response.ok) {
                alert(data.message);
                resetRelationshipForm();
                loadRelationshipDefinitions(); // Reload the list
            } else {
                // Server returned an error (e.g., 400, 409, 500)
                alert('Error: ' + (data.error || 'Unknown error occurred on server.'));
            }
        } catch (error) {
            console.error('Error submitting relationship definition:', error);
            alert('An error occurred while saving the relationship definition. Check console for details.');
        }
    });

    // Initial load of entry types when the page loads
    loadEntryTypes();
    // Relationship definitions are loaded when the "Manage Relationships" modal is opened.
});