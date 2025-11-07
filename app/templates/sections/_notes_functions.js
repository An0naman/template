<script>
/**
 * Notes Section V2 - JavaScript Functions
 * Handles note creation, editing, display, search/filter, reminders, and attachments
 * AI functionality removed - use dedicated chatbot section for AI assistance
 */

(function() {
    'use strict';
    
    // Global variables for notes
    const entryId = {{ entry.id }};
    let allNotes = [];
    let filteredNotes = [];
    let loadedNotes = new Map();
    let currentNoteIdInModal = null;
    let bookmarkCounter = 0;
    let editBookmarkCounter = 0;
    let noteTypeColors = {}; // Store note type colors from configuration
    let imageViewerModal = null; // Bootstrap modal for image viewing
    
    // DOM Elements
    const toggleNewNoteBtn = document.getElementById('toggleNewNoteBtn');
    const toggleNewNoteText = document.getElementById('toggleNewNoteText');
    const newNoteFormV2 = document.getElementById('newNoteFormV2');
    const noteTitleInput = document.getElementById('noteTitleInput');
    const noteTypeSelect = document.getElementById('noteTypeSelect');
    const newNoteTextarea = document.getElementById('newNoteTextarea');
    const reminderDateInput = document.getElementById('reminderDateInput');
    const fileUploadInput = document.getElementById('fileUploadInput');
    const selectedFilesInfo = document.getElementById('selectedFilesInfo');
    const associatedEntriesSelect = document.getElementById('associatedEntriesSelect');
    const addBookmarkBtn = document.getElementById('addBookmarkBtn');
    const addNoteBtn = document.getElementById('addNoteBtn');
    const noteStatusMessage = document.getElementById('noteStatusMessage');
    const notesList = document.getElementById('notesList');
    const noNotesMessage = document.getElementById('noNotesMessage');
    
    // Search and filter elements
    const notesSearchInput = document.getElementById('notesSearchInput');
    const clearNotesSearch = document.getElementById('clearNotesSearch');
    const notesTypeFilter = document.getElementById('notesTypeFilter');
    const notesSortOrder = document.getElementById('notesSortOrder');
    const notesCount = document.getElementById('notesCount');
    
    // Modal elements - will be initialized later when Bootstrap is ready
    let noteDetailModal = null;
    const modalNoteTitle = document.getElementById('modalNoteTitle');
    const modalNoteType = document.getElementById('modalNoteType');
    const modalNoteCreated = document.getElementById('modalNoteCreated');
    const modalNoteContent = document.getElementById('modalNoteContent');
    const modalNoteFiles = document.getElementById('modalNoteFiles');
    const deleteNoteFromModalBtn = document.getElementById('deleteNoteFromModalBtn');
    
    // Initialize on page load or immediately if DOM is already ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            initializeNotesSection();
        });
    } else {
        // DOM is already ready, initialize immediately
        initializeNotesSection();
    }
    
    function initializeNotesSection() {
        console.log('Initializing Notes Section V2 for entry:', entryId);
        
        // Initialize Bootstrap modal when Bootstrap is ready
        if (typeof bootstrap !== 'undefined') {
            const modalElement = document.getElementById('noteDetailModal');
            if (modalElement) {
                noteDetailModal = new bootstrap.Modal(modalElement);
            }
            
            // Initialize image viewer modal
            const imageModalElement = document.getElementById('imageViewerModal');
            if (imageModalElement) {
                imageViewerModal = new bootstrap.Modal(imageModalElement);
            }
        }
        
        // Load note type colors from configuration
        loadNoteTypeColors();
        
        // Load note types
        loadNoteTypes();
        
        // Set up reminder date input
        setupReminderDateInput();
        
        // Load notes
        fetchNotes();
        
        // Set up event listeners
        setupEventListeners();
    }
    
    function setupEventListeners() {
        // Form collapse events
        const newNoteFormCollapseElement = document.getElementById('newNoteFormV2');
        if (newNoteFormCollapseElement) {
            newNoteFormCollapseElement.addEventListener('shown.bs.collapse', () => {
                if (toggleNewNoteText) toggleNewNoteText.textContent = 'Hide Form';
            });
            newNoteFormCollapseElement.addEventListener('hidden.bs.collapse', () => {
                if (toggleNewNoteText) toggleNewNoteText.textContent = 'Add Note';
            });
        }
        
        // File upload change
        if (fileUploadInput) fileUploadInput.addEventListener('change', handleFileSelection);
        
        // Add note button
        if (addNoteBtn) addNoteBtn.addEventListener('click', addNote);
        
        // Search and filter
        if (notesSearchInput) notesSearchInput.addEventListener('input', handleSearchInput);
        if (clearNotesSearch) clearNotesSearch.addEventListener('click', clearSearchAndFilter);
        if (notesTypeFilter) notesTypeFilter.addEventListener('change', applyNotesFilter);
        if (notesSortOrder) notesSortOrder.addEventListener('change', applyNotesFilter);
        
        // Bookmark buttons
        if (addBookmarkBtn) addBookmarkBtn.addEventListener('click', () => addBookmarkField());
        const editAddBookmarkBtn = document.getElementById('editAddBookmarkBtn');
        if (editAddBookmarkBtn) editAddBookmarkBtn.addEventListener('click', () => addEditBookmarkField());
        
        // Clear associations button
        const clearAssociationsBtn = document.getElementById('clearAssociationsBtn');
        if (clearAssociationsBtn) clearAssociationsBtn.addEventListener('click', clearAssociations);
        
        // Associated entries change
        if (associatedEntriesSelect) associatedEntriesSelect.addEventListener('change', updateSelectedAssociationsDisplay);
        
        // Modal events
        if (deleteNoteFromModalBtn) deleteNoteFromModalBtn.addEventListener('click', deleteNote);
        const editNoteContentBtn = document.getElementById('editNoteContentBtn');
        if (editNoteContentBtn) editNoteContentBtn.addEventListener('click', enterEditMode);
        const saveNoteContentBtn = document.getElementById('saveNoteContentBtn');
        if (saveNoteContentBtn) saveNoteContentBtn.addEventListener('click', saveNoteEdits);
        const cancelNoteContentEditBtn = document.getElementById('cancelNoteContentEditBtn');
        if (cancelNoteContentEditBtn) cancelNoteContentEditBtn.addEventListener('click', cancelEditMode);
        
        // Reminder edit buttons
        const editReminderBtn = document.getElementById('editReminderBtn');
        if (editReminderBtn) editReminderBtn.addEventListener('click', enterReminderEditMode);
        const saveReminderBtn = document.getElementById('saveReminderBtn');
        if (saveReminderBtn) saveReminderBtn.addEventListener('click', saveReminderEdit);
        const cancelReminderEditBtn = document.getElementById('cancelReminderEditBtn');
        if (cancelReminderEditBtn) cancelReminderEditBtn.addEventListener('click', cancelReminderEdit);
        const deleteReminderBtn = document.getElementById('deleteReminderBtn');
        if (deleteReminderBtn) deleteReminderBtn.addEventListener('click', deleteReminder);
        
        // Attachment management
        const addAttachmentsBtn = document.getElementById('addAttachmentsBtn');
        if (addAttachmentsBtn) addAttachmentsBtn.addEventListener('click', showAddAttachmentsForm);
        const uploadAdditionalFilesBtn = document.getElementById('uploadAdditionalFilesBtn');
        if (uploadAdditionalFilesBtn) uploadAdditionalFilesBtn.addEventListener('click', uploadAdditionalFiles);
        const cancelAddAttachmentsBtn = document.getElementById('cancelAddAttachmentsBtn');
        if (cancelAddAttachmentsBtn) cancelAddAttachmentsBtn.addEventListener('click', hideAddAttachmentsForm);
        
        // Set up event delegation for note cards (handles dynamic content)
        setupNoteCardEventDelegation();
    }
    
    function setupNoteCardEventDelegation() {
        // Use event delegation on notesList for all dynamic note card interactions
        if (!notesList) return;
        
        notesList.addEventListener('click', (event) => {
            const target = event.target;
            
            // Expand note button
            if (target.closest('.expand-note-btn')) {
                const card = target.closest('.note-card');
                toggleNoteExpanded(card, true);
                return;
            }
            
            // Collapse note button
            if (target.closest('.collapse-note-btn')) {
                const card = target.closest('.note-card');
                toggleNoteExpanded(card, false);
                return;
            }
            
            // Edit note button
            if (target.closest('.edit-note-inline-btn')) {
                const card = target.closest('.note-card');
                toggleNoteEditMode(card, true);
                return;
            }
            
            // Delete note button
            if (target.closest('.delete-note-inline-btn')) {
                const card = target.closest('.note-card');
                const noteId = parseInt(card.dataset.noteId);
                if (confirm('Are you sure you want to delete this note?')) {
                    deleteNote(noteId);
                }
                return;
            }
            
            // Save edit button
            if (target.closest('.save-note-inline-btn')) {
                const card = target.closest('.note-card');
                const noteId = parseInt(card.dataset.noteId);
                saveInlineEdit(card, noteId);
                return;
            }
            
            // Cancel edit button
            if (target.closest('.cancel-edit-inline-btn')) {
                const card = target.closest('.note-card');
                toggleNoteEditMode(card, false);
                return;
            }
            
            // Add bookmark button
            if (target.closest('.add-bookmark-inline-btn')) {
                const container = target.closest('.note-edit-view').querySelector('.inline-edit-bookmarks-container');
                addInlineBookmarkField(container);
                return;
            }
            
            // Remove bookmark button
            if (target.closest('.remove-bookmark-btn')) {
                const bookmarkEntry = target.closest('.bookmark-edit-entry');
                bookmarkEntry.remove();
                return;
            }
            
            // Remove attachment button
            if (target.closest('.remove-attachment-btn')) {
                const button = target.closest('.remove-attachment-btn');
                const fileIndex = parseInt(button.dataset.fileIndex);
                const fileName = button.dataset.fileName;
                const card = target.closest('.note-card');
                const noteId = parseInt(card.dataset.noteId);
                
                if (confirm(`Remove attachment: ${fileName}?`)) {
                    removeNoteAttachment(noteId, fileIndex, button.closest('.col'));
                }
                return;
            }
            
            // Toggle edit section buttons (for collapsible sections in edit mode)
            if (target.closest('.toggle-edit-section-btn')) {
                const button = target.closest('.toggle-edit-section-btn');
                const targetId = button.dataset.target;
                const targetSection = document.getElementById(targetId);
                const chevron = button.querySelector('.fa-chevron-down, .fa-chevron-up');
                
                if (targetSection) {
                    if (targetSection.style.display === 'none' || targetSection.style.display === '') {
                        targetSection.style.display = 'block';
                        if (chevron) {
                            chevron.classList.remove('fa-chevron-down');
                            chevron.classList.add('fa-chevron-up');
                        }
                    } else {
                        targetSection.style.display = 'none';
                        if (chevron) {
                            chevron.classList.remove('fa-chevron-up');
                            chevron.classList.add('fa-chevron-down');
                        }
                    }
                }
                return;
            }
        });
    }
    
    // Load note type colors from system configuration
    async function loadNoteTypeColors() {
        try {
            const response = await fetch('/api/system_params');
            const params = await response.json();
            
            // Default colors for built-in note types
            noteTypeColors = {
                'General': '#0dcaf0',
                'Info': '#0dcaf0',
                'Important': '#dc3545',
                'Critical': '#dc3545',
                'Warning': '#fd7e14',
                'Caution': '#ffc107',
                'Success': '#198754',
                'Completed': '#198754'
            };
            
            // Load custom note types and their colors
            if (params.custom_note_types) {
                try {
                    const customNotesConfig = JSON.parse(params.custom_note_types);
                    let customTypes = [];
                    
                    // Handle both old format (array) and new format (object with custom_types array)
                    if (Array.isArray(customNotesConfig)) {
                        customTypes = customNotesConfig;
                    } else if (customNotesConfig.custom_types && Array.isArray(customNotesConfig.custom_types)) {
                        customTypes = customNotesConfig.custom_types;
                    }
                    
                    // Add custom type colors
                    customTypes.forEach(noteType => {
                        if (noteType.name && noteType.color) {
                            noteTypeColors[noteType.name] = noteType.color;
                        }
                    });
                } catch (e) {
                    console.warn('Error parsing custom note types:', e);
                }
            }
            
            console.log('Loaded note type colors:', noteTypeColors);
        } catch (error) {
            console.error('Error loading note type colors:', error);
        }
    }
    
    // Load note types from entry configuration
    function loadNoteTypes() {
        const noteTypesRaw = "{{ entry.note_types | default('General', true) }}";
        console.log('Note types raw:', noteTypesRaw);
        
        // Split comma-separated string and clean up
        const noteTypes = noteTypesRaw.split(',').map(type => type.trim()).filter(type => type !== '');
        console.log('Parsed note types:', noteTypes);
        
        if (!noteTypeSelect) {
            console.error('noteTypeSelect element not found!');
            return;
        }
        
        noteTypeSelect.innerHTML = '';
        
        if (noteTypes.length === 0) {
            const option = document.createElement('option');
            option.value = 'General';
            option.textContent = 'General';
            noteTypeSelect.appendChild(option);
        } else {
            noteTypes.forEach(type => {
                const option = document.createElement('option');
                option.value = type;
                option.textContent = type;
                noteTypeSelect.appendChild(option);
            });
        }
    }
    
    // Setup reminder date input
    function setupReminderDateInput() {
        const now = new Date();
        now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
        reminderDateInput.min = now.toISOString().slice(0, 16);
        
        reminderDateInput.addEventListener('change', function() {
            const value = this.value;
            if (value && value.length === 10) {
                this.value = value + 'T01:00';
            } else if (value && value.includes('T') && value.split('T')[1] === '') {
                this.value = value + '01:00';
            }
        });
    }
    
    // Reminder quick actions
    window.setReminderToToday = function() {
        const today = new Date();
        today.setHours(today.getHours() + 1);
        today.setMinutes(0);
        today.setSeconds(0);
        today.setMilliseconds(0);
        today.setMinutes(today.getMinutes() - today.getTimezoneOffset());
        reminderDateInput.value = today.toISOString().slice(0, 16);
    };
    
    window.setReminderToTomorrow = function() {
        const tomorrow = new Date();
        tomorrow.setDate(tomorrow.getDate() + 1);
        tomorrow.setHours(1);
        tomorrow.setMinutes(0);
        tomorrow.setSeconds(0);
        tomorrow.setMilliseconds(0);
        tomorrow.setMinutes(tomorrow.getMinutes() - tomorrow.getTimezoneOffset());
        reminderDateInput.value = tomorrow.toISOString().slice(0, 16);
    };
    
    window.clearReminder = function() {
        reminderDateInput.value = '';
    };
    
    // File selection handler
    function handleFileSelection() {
        if (fileUploadInput.files.length > 0) {
            let fileList = Array.from(fileUploadInput.files).map(file => {
                const sizeInMB = (file.size / (1024 * 1024)).toFixed(2);
                return `${file.name} (${sizeInMB} MB)`;
            }).join(', ');
            selectedFilesInfo.innerHTML = `<strong>Selected:</strong> ${fileList}`;
            selectedFilesInfo.classList.remove('text-muted');
            selectedFilesInfo.classList.add('text-info');
        } else {
            selectedFilesInfo.textContent = 'No files selected.';
            selectedFilesInfo.classList.remove('text-info');
            selectedFilesInfo.classList.add('text-muted');
        }
    }
    
    // URL Bookmarks functionality
    function addBookmarkField(url = '', friendlyName = '') {
        const bookmarkId = ++bookmarkCounter;
        const bookmarkDiv = document.createElement('div');
        bookmarkDiv.className = 'bookmark-entry mb-2 p-2 border rounded';
        bookmarkDiv.dataset.bookmarkId = bookmarkId;
        
        bookmarkDiv.innerHTML = `
            <div class="row g-2">
                <div class="col-md-5">
                    <input type="text" class="form-control form-control-sm bookmark-name" 
                           placeholder="Friendly name" value="${friendlyName}">
                </div>
                <div class="col-md-6">
                    <input type="url" class="form-control form-control-sm bookmark-url" 
                           placeholder="https://example.com" value="${url}">
                </div>
                <div class="col-md-1">
                    <button type="button" class="btn btn-sm btn-outline-danger" 
                            onclick="removeBookmark(${bookmarkId})">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            </div>
        `;
        
        document.getElementById('urlBookmarksList').appendChild(bookmarkDiv);
    }
    
    window.removeBookmark = function(bookmarkId) {
        const bookmarkDiv = document.querySelector(`[data-bookmark-id="${bookmarkId}"]`);
        if (bookmarkDiv) {
            bookmarkDiv.remove();
        }
    };
    
    function getUrlBookmarks() {
        const bookmarks = [];
        document.querySelectorAll('.bookmark-entry').forEach(entry => {
            const nameInput = entry.querySelector('.bookmark-name');
            const urlInput = entry.querySelector('.bookmark-url');
            
            const friendlyName = nameInput.value.trim();
            const url = urlInput.value.trim();
            
            if (url && friendlyName) {
                bookmarks.push({
                    url: url,
                    friendly_name: friendlyName
                });
            }
        });
        return bookmarks;
    }
    
    function clearAllBookmarks() {
        document.getElementById('urlBookmarksList').innerHTML = '';
        bookmarkCounter = 0;
    }
    
    // Edit mode bookmarks
    function addEditBookmarkField(url = '', friendlyName = '') {
        editBookmarkCounter++;
        const container = document.getElementById('editUrlBookmarksList');
        
        const bookmarkDiv = document.createElement('div');
        bookmarkDiv.className = 'edit-bookmark-field mb-2 p-2 border rounded';
        bookmarkDiv.innerHTML = `
            <div class="row g-2">
                <div class="col-md-5">
                    <input type="text" class="form-control form-control-sm" placeholder="Friendly name" 
                           name="edit_bookmark_name_${editBookmarkCounter}" value="${friendlyName}">
                </div>
                <div class="col-md-5">
                    <input type="url" class="form-control form-control-sm" placeholder="https://example.com" 
                           name="edit_bookmark_url_${editBookmarkCounter}" value="${url}">
                </div>
                <div class="col-md-2">
                    <button type="button" class="btn btn-sm btn-outline-danger w-100" 
                            onclick="removeEditBookmark(this)">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
        `;
        
        container.appendChild(bookmarkDiv);
    }
    
    window.removeEditBookmark = function(button) {
        button.closest('.edit-bookmark-field').remove();
    };
    
    function getEditUrlBookmarks() {
        const bookmarks = [];
        const container = document.getElementById('editUrlBookmarksList');
        const bookmarkFields = container.querySelectorAll('.edit-bookmark-field');
        
        bookmarkFields.forEach(field => {
            const urlInput = field.querySelector('input[name^="edit_bookmark_url_"]');
            const nameInput = field.querySelector('input[name^="edit_bookmark_name_"]');
            
            if (urlInput && urlInput.value.trim()) {
                bookmarks.push({
                    url: urlInput.value.trim(),
                    friendly_name: nameInput ? nameInput.value.trim() : ''
                });
            }
        });
        return bookmarks;
    }
    
    function populateEditBookmarks(urlBookmarks) {
        document.getElementById('editUrlBookmarksList').innerHTML = '';
        editBookmarkCounter = 0;
        if (urlBookmarks && urlBookmarks.length > 0) {
            urlBookmarks.forEach(bookmark => {
                addEditBookmarkField(bookmark.url, bookmark.friendly_name);
            });
        }
    }
    
    // Associated entries functions
    function getSelectedAssociatedEntryIds() {
        const selected = Array.from(associatedEntriesSelect.selectedOptions);
        return selected.map(option => parseInt(option.value));
    }
    
    function updateSelectedAssociationsDisplay() {
        const selected = getSelectedAssociatedEntryIds();
        const display = document.getElementById('selectedAssociationsDisplay');
        const clearBtn = document.getElementById('clearAssociationsBtn');
        
        if (selected.length > 0) {
            display.textContent = `${selected.length} ${selected.length === 1 ? 'entry' : 'entries'} selected`;
            display.style.display = 'block';
            clearBtn.style.display = 'inline-block';
        } else {
            display.style.display = 'none';
            clearBtn.style.display = 'none';
        }
    }
    
    function clearAssociations() {
        Array.from(associatedEntriesSelect.options).forEach(option => {
            option.selected = false;
        });
        updateSelectedAssociationsDisplay();
    }
    
    // Add Note function
    async function addNote() {
        const noteTitle = noteTitleInput.value.trim();
        const noteText = newNoteTextarea.value.trim();
        const noteType = noteTypeSelect.value;
        let reminderDate = reminderDateInput.value;
        const files = fileUploadInput.files;
        
        if (!noteText) {
            displayStatus('Note content cannot be empty.', 'alert-warning');
            return;
        }
        
        // Validate file sizes
        const maxFileSize = {{ max_file_size }} * 1024 * 1024;
        const allowedExtensions = new Set({{ allowed_file_types.split(',')|map('trim')|map('lower')|list|tojson }});
        
        for (let file of files) {
            if (file.size > maxFileSize) {
                displayStatus(`File "${file.name}" is too large. Max size: {{ max_file_size }}MB.`, 'alert-warning');
                return;
            }
            
            const fileExtension = file.name.toLowerCase().split('.').pop();
            if (!allowedExtensions.has(fileExtension)) {
                displayStatus(`File "${file.name}" has an unsupported file type.`, 'alert-warning');
                return;
            }
        }
        
        // Validate reminder date
        if (reminderDate) {
            if (reminderDate.length === 10) {
                reminderDate = reminderDate + 'T01:00';
                reminderDateInput.value = reminderDate;
            } else if (reminderDate.includes('T') && reminderDate.split('T')[1] === '') {
                reminderDate = reminderDate + '01:00';
                reminderDateInput.value = reminderDate;
            }
            
            const reminderDateTime = new Date(reminderDate);
            const now = new Date();
            if (reminderDateTime <= now) {
                displayStatus('Reminder date must be in the future.', 'alert-warning');
                return;
            }
        }
        
        displayStatus('Adding note...', 'alert-info');
        
        try {
            const formData = new FormData();
            formData.append('note_title', noteTitle);
            formData.append('note_text', noteText);
            formData.append('note_type', noteType);
            
            const associatedEntryIds = getSelectedAssociatedEntryIds();
            if (associatedEntryIds.length > 0) {
                formData.append('associated_entry_ids', JSON.stringify(associatedEntryIds));
            }
            
            const bookmarks = getUrlBookmarks();
            if (bookmarks.length > 0) {
                formData.append('url_bookmarks', JSON.stringify(bookmarks));
            }
            
            if (reminderDate) {
                formData.append('reminder_date', reminderDate);
            }
            
            for (let file of files) {
                formData.append('files', file);
            }
            
            const response = await fetch(`/api/entries/${entryId}/notes`, {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            
            if (response.ok) {
                displayStatus('Note added successfully!', 'alert-success');
                resetForm();
                
                // Hide the form using Bootstrap collapse
                if (typeof bootstrap !== 'undefined' && newNoteFormV2) {
                    const bsCollapse = new bootstrap.Collapse(newNoteFormV2, { toggle: false });
                    bsCollapse.hide();
                }
                
                fetchNotes();
            } else {
                displayStatus(`Error: ${data.message || 'Failed to add note.'}`, 'alert-danger');
            }
        } catch (error) {
            console.error('Error adding note:', error);
            displayStatus('An unexpected error occurred.', 'alert-danger');
        }
    }
    
    function resetForm() {
        noteTitleInput.value = '';
        newNoteTextarea.value = '';
        reminderDateInput.value = '';
        noteTypeSelect.value = noteTypeSelect.options[0].value;
        fileUploadInput.value = '';
        selectedFilesInfo.textContent = 'No files selected.';
        selectedFilesInfo.classList.remove('text-info');
        selectedFilesInfo.classList.add('text-muted');
        clearAssociations();
        clearAllBookmarks();
    }
    
    function displayStatus(message, alertClass) {
        noteStatusMessage.innerHTML = `<div class="alert ${alertClass}">${message}</div>`;
        setTimeout(() => {
            if (alertClass === 'alert-success') {
                noteStatusMessage.innerHTML = '';
            }
        }, 3000);
    }
    
    // Fetch and display notes
    async function fetchNotes() {
        console.log('Fetching notes for entry:', entryId);
        noNotesMessage.textContent = 'Loading notes...';
        notesList.innerHTML = '';
        notesList.appendChild(noNotesMessage);
        
        try {
            const response = await fetch(`/api/entries/${entryId}/notes`);
            console.log('Notes API response status:', response.status);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const notes = await response.json();
            console.log('Loaded notes:', notes.length, notes);
            
            loadedNotes.clear();
            notes.forEach(note => {
                loadedNotes.set(parseInt(note.id), note);
            });
            
            allNotes = [...notes];
            updateNoteTypeFilter();
            applyNotesFilter();
            updateReminderProgressSummary(notes);
        } catch (error) {
            console.error('Error fetching notes:', error);
            noNotesMessage.textContent = 'Failed to load notes.';
            noNotesMessage.classList.add('text-danger');
        }
    }
    
    function displayNotes(notes) {
        notesList.innerHTML = '';
        
        // Cache notes for image gallery access
        window.notesCache = notes;
        
        if (notes.length === 0) {
            noNotesMessage.textContent = 'No notes found.';
            notesList.appendChild(noNotesMessage);
            return;
        }
        
        notes.forEach(note => {
            const noteItem = createNoteCard(note);
            notesList.appendChild(noteItem);
        });
    }
    
    async function removeNoteAttachment(noteId, fileIndex, elementToRemove) {
        try {
            const response = await fetch(`/api/notes/${noteId}/attachments/${fileIndex}`, {
                method: 'DELETE'
            });
            
            if (response.ok) {
                alert('Attachment removed successfully!');
                // Refresh the notes list to update file indices
                fetchNotes();
            } else {
                const data = await response.json();
                alert(`Error: ${data.error || 'Failed to remove attachment.'}`);
            }
        } catch (error) {
            console.error('Error removing attachment:', error);
            alert('An unexpected error occurred.');
        }
    }
    
    function toggleNoteExpanded(card, expand) {
        const collapsedView = card.querySelector('.note-collapsed-view');
        const expandedView = card.querySelector('.note-expanded-view');
        
        if (expand) {
            collapsedView.style.display = 'none';
            expandedView.style.display = 'block';
            // Smooth scroll to the expanded card
            card.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        } else {
            collapsedView.style.display = 'block';
            expandedView.style.display = 'none';
        }
    }
    
    async function toggleNoteEditMode(card, enterEdit) {
        const expandedView = card.querySelector('.note-expanded-view');
        const editView = card.querySelector('.note-edit-view');
        
        if (enterEdit) {
            expandedView.style.display = 'none';
            editView.style.display = 'block';
            
            // Load entries for associations dropdown
            const associationsSelect = editView.querySelector('.inline-edit-associations');
            if (associationsSelect && associationsSelect.options.length === 1) {
                await loadEntriesForAssociations(card, associationsSelect);
            }
            
            card.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        } else {
            expandedView.style.display = 'block';
            editView.style.display = 'none';
        }
    }
    
    async function loadEntriesForAssociations(card, selectElement) {
        const noteId = parseInt(card.dataset.noteId);
        const note = loadedNotes.get(noteId);
        
        try {
            const response = await fetch('/api/entries');
            if (!response.ok) throw new Error('Failed to load entries');
            
            const entries = await response.json();
            
            // Clear loading option
            selectElement.innerHTML = '';
            
            // Add entries as options
            entries.forEach(entry => {
                // Don't include the current entry
                if (entry.id !== entryId) {
                    const option = document.createElement('option');
                    option.value = entry.id;
                    option.textContent = `${entry.title} (${entry.entry_type_label || 'Entry'})`;
                    
                    // Pre-select if already associated
                    if (note.associated_entry_ids && note.associated_entry_ids.includes(entry.id)) {
                        option.selected = true;
                    }
                    
                    selectElement.appendChild(option);
                }
            });
            
        } catch (error) {
            console.error('Error loading entries:', error);
            selectElement.innerHTML = '<option value="" disabled>Error loading entries</option>';
        }
    }
    
    function addInlineBookmarkField(container) {
        const bookmarkCount = container.querySelectorAll('.bookmark-edit-entry').length;
        const bookmarkEntry = document.createElement('div');
        bookmarkEntry.className = 'bookmark-edit-entry mb-2 p-2 border rounded';
        bookmarkEntry.dataset.bookmarkIndex = bookmarkCount;
        
        bookmarkEntry.innerHTML = `
            <div class="row g-2">
                <div class="col-md-5">
                    <input type="text" class="form-control form-control-sm bookmark-name-input" placeholder="Name">
                </div>
                <div class="col-md-6">
                    <input type="url" class="form-control form-control-sm bookmark-url-input" placeholder="URL">
                </div>
                <div class="col-md-1">
                    <button type="button" class="btn btn-sm btn-danger remove-bookmark-btn" title="Remove">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            </div>
        `;
        
        // Remove "no bookmarks" message if present
        const noBookmarksMsg = container.querySelector('p.text-muted');
        if (noBookmarksMsg) {
            noBookmarksMsg.remove();
        }
        
        container.appendChild(bookmarkEntry);
    }
    
    function getInlineEditBookmarks(card) {
        const bookmarks = [];
        const bookmarkEntries = card.querySelectorAll('.bookmark-edit-entry');
        
        bookmarkEntries.forEach(entry => {
            const name = entry.querySelector('.bookmark-name-input').value.trim();
            const url = entry.querySelector('.bookmark-url-input').value.trim();
            
            if (url) {
                bookmarks.push({
                    friendly_name: name || null,
                    url: url
                });
            }
        });
        
        return bookmarks;
    }
    
    async function saveInlineEdit(card, noteId) {
        const titleInput = card.querySelector('.inline-edit-title');
        const textInput = card.querySelector('.inline-edit-text');
        const reminderInput = card.querySelector('.inline-edit-reminder');
        const filesInput = card.querySelector('.inline-edit-files');
        const associationsSelect = card.querySelector('.inline-edit-associations');
        
        const noteTitle = titleInput.value.trim();
        const noteText = textInput.value.trim();
        const bookmarks = getInlineEditBookmarks(card);
        const reminderDateTime = reminderInput ? reminderInput.value : null;
        const associatedEntryIds = associationsSelect ? Array.from(associationsSelect.selectedOptions).map(opt => parseInt(opt.value)) : [];
        
        if (!noteText) {
            alert('Note content cannot be empty.');
            return;
        }
        
        try {
            // Step 1: Update note content, bookmarks, and associations
            const formData = new FormData();
            formData.append('note_title', noteTitle);
            formData.append('note_text', noteText);
            formData.append('url_bookmarks', JSON.stringify(bookmarks));
            formData.append('associated_entry_ids', JSON.stringify(associatedEntryIds));
            
            const response = await fetch(`/api/notes/${noteId}`, {
                method: 'PUT',
                body: formData
            });
            
            if (!response.ok) {
                const data = await response.json().catch(() => ({}));
                throw new Error(data.error || `Server error: ${response.status}`);
            }
            
            // Step 2: Handle reminder separately if provided
            if (reminderDateTime) {
                const reminderResponse = await fetch(`/api/notes/${noteId}/reminder`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ scheduled_for: reminderDateTime })
                });
                
                if (!reminderResponse.ok) {
                    console.warn('Failed to update reminder, but note was saved');
                }
            }
            
            // Step 3: Handle file uploads separately if provided
            if (filesInput && filesInput.files.length > 0) {
                const filesFormData = new FormData();
                for (let i = 0; i < filesInput.files.length; i++) {
                    filesFormData.append('files', filesInput.files[i]);
                }
                
                const filesResponse = await fetch(`/api/notes/${noteId}/attachments`, {
                    method: 'POST',
                    body: filesFormData
                });
                
                if (!filesResponse.ok) {
                    console.warn('Failed to upload files, but note was saved');
                }
            }
            
            alert('Note updated successfully!');
            fetchNotes();
            
        } catch (error) {
            console.error('Error updating note:', error);
            alert('Error updating note: ' + error.message);
        }
    }
    
    function createNoteCard(note) {
        const noteItem = document.createElement('div');
        noteItem.classList.add('card', 'mb-3', 'note-card');
        noteItem.dataset.noteId = note.id;
        
        const borderColor = getNoteTypeColor(note.note_type);
        noteItem.style.borderLeft = `4px solid ${borderColor}`;
        
        // Build indicators
        let indicators = '';
        
        if (note.reminder) {
            const { icon, color, title } = getReminderIndicator(note.reminder);
            indicators += `<i class="${icon} ${color} ms-2" title="${title}"></i>`;
        }
        
        if (note.file_paths && note.file_paths.length > 0) {
            const fileCount = note.file_paths.length;
            indicators += `<i class="fas fa-paperclip text-info ms-2" title="${fileCount} file${fileCount > 1 ? 's' : ''}"></i>`;
        }
        
        if (note.associated_entry_ids && note.associated_entry_ids.length > 0) {
            indicators += `<i class="fas fa-sitemap text-primary ms-2" title="${note.associated_entry_ids.length} associated entries"></i>`;
        }
        
        const bookmarksDisplay = createBookmarksDisplay(note.url_bookmarks);
        
        // Get image attachments for preview
        const imageAttachments = note.file_paths ? note.file_paths.filter(filePath => {
            const fileExt = filePath.split('.').pop().toLowerCase();
            return ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'svg'].includes(fileExt);
        }) : [];
        
        const imagePreviewDisplay = imageAttachments.length > 0 ? `
            <div class="mb-2">
                <div class="d-flex gap-2 flex-wrap">
                    ${imageAttachments.slice(0, 3).map(imgPath => {
                        // Handle various path formats
                        let fullPath;
                        if (imgPath.startsWith('http://') || imgPath.startsWith('https://')) {
                            fullPath = imgPath;
                        } else if (imgPath.startsWith('/static/')) {
                            fullPath = imgPath;
                        } else if (imgPath.startsWith('uploads/')) {
                            fullPath = `/static/${imgPath}`;
                        } else {
                            fullPath = `/static/uploads/${imgPath}`;
                        }
                        const fileName = imgPath.split('/').pop();
                        return `<img src="${fullPath}" alt="Attachment" style="height: 80px; width: 80px; object-fit: cover; border-radius: 4px; cursor: pointer;" onclick="openImageInModal('${fullPath}', '${fileName.replace(/'/g, "\\'")}', ${note.id})" title="Click to view full size">`;
                    }).join('')}
                    ${imageAttachments.length > 3 ? `<div class="d-flex align-items-center justify-content-center" style="height: 80px; width: 80px; background: #f0f0f0; border-radius: 4px;"><small class="text-muted">+${imageAttachments.length - 3} more</small></div>` : ''}
                </div>
            </div>
        ` : '';
        
        // Create collapsed and expanded views
        noteItem.innerHTML = `
            <div class="card-body">
                <div class="note-collapsed-view">
                    <div class="d-flex justify-content-between align-items-start mb-2">
                        <h6 class="card-title mb-0">
                            ${note.note_title || 'Untitled'}
                            <small class="text-muted">(${note.note_type})</small>
                            ${indicators}
                        </h6>
                        <small class="text-muted text-nowrap ms-2">${new Date(note.created_at).toLocaleString()}</small>
                    </div>
                    ${imagePreviewDisplay}
                    <p class="card-text mb-2" style="white-space: pre-wrap;">${note.note_text}</p>
                    ${bookmarksDisplay}
                    <div class="mt-2">
                        <button type="button" class="btn btn-sm btn-primary expand-note-btn">
                            <i class="fas fa-chevron-down me-1"></i>Expand
                        </button>
                    </div>
                </div>
                
                <div class="note-expanded-view" style="display: none;">
                    <div class="d-flex justify-content-between align-items-start mb-3">
                        <h5 class="mb-0">
                            ${note.note_title || 'Untitled'}
                            <small class="text-muted">(${note.note_type})</small>
                            ${indicators}
                        </h5>
                        <button type="button" class="btn btn-sm btn-outline-secondary collapse-note-btn">
                            <i class="fas fa-chevron-up me-1"></i>Collapse
                        </button>
                    </div>
                    
                    <div class="mb-3">
                        <small class="text-muted">Created: ${new Date(note.created_at).toLocaleString()}</small>
                    </div>
                    
                    <div class="mb-3">
                        <h6>Content:</h6>
                        <div style="white-space: pre-wrap;">${note.note_text}</div>
                    </div>
                    
                    ${note.url_bookmarks && note.url_bookmarks.length > 0 ? `
                        <div class="mb-3">
                            <h6>Bookmarks:</h6>
                            <div class="list-group list-group-flush">
                                ${note.url_bookmarks.map(bookmark => `
                                    <a href="${bookmark.url}" target="_blank" class="list-group-item list-group-item-action">
                                        <i class="fas fa-external-link-alt me-2"></i>
                                        ${bookmark.friendly_name || bookmark.url}
                                        ${bookmark.friendly_name ? `<br><small class="text-muted">${bookmark.url}</small>` : ''}
                                    </a>
                                `).join('')}
                            </div>
                        </div>
                    ` : ''}
                    
                    ${note.reminder ? `
                        <div class="mb-3">
                            <h6><i class="fas fa-bell me-2"></i>Reminder:</h6>
                            <div class="alert alert-info">
                                <strong>Scheduled for:</strong> ${new Date(note.reminder.scheduled_for).toLocaleString()}<br>
                                <strong>Status:</strong> ${note.reminder.is_dismissed ? 'Dismissed' : note.reminder.is_read ? 'Completed' : 'Active'}
                            </div>
                        </div>
                    ` : ''}
                    
                    ${note.associated_entry_ids && note.associated_entry_ids.length > 0 ? `
                        <div class="mb-3">
                            <h6><i class="fas fa-sitemap me-2"></i>Associated Entries:</h6>
                            <p class="text-muted">This note is associated with ${note.associated_entry_ids.length} other ${note.associated_entry_ids.length === 1 ? 'entry' : 'entries'}.</p>
                        </div>
                    ` : ''}
                    
                    ${note.file_paths && note.file_paths.length > 0 ? `
                        <div class="mb-3">
                            <h6><i class="fas fa-paperclip me-2"></i>Attachments:</h6>
                            <div class="row row-cols-2 row-cols-md-3 g-2">
                                ${note.file_paths.map(filePath => {
                                    // Handle various path formats
                                    let fullPath;
                                    if (filePath.startsWith('http://') || filePath.startsWith('https://')) {
                                        fullPath = filePath;
                                    } else if (filePath.startsWith('/static/')) {
                                        fullPath = filePath;
                                    } else if (filePath.startsWith('uploads/')) {
                                        fullPath = `/static/${filePath}`;
                                    } else {
                                        fullPath = `/static/uploads/${filePath}`;
                                    }
                                    const fileName = filePath.split('/').pop();
                                    const fileExt = fileName.split('.').pop().toLowerCase();
                                    const fileIcon = getFileIcon(fileExt);
                                    const isImage = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'svg'].includes(fileExt);
                                    return `
                                        <div class="col">
                                            <div class="card h-100">
                                                ${isImage ? `
                                                    <img src="${fullPath}" class="card-img-top" alt="${fileName}" style="height: 150px; object-fit: cover; cursor: pointer;" onclick="openImageInModal('${fullPath}', '${fileName.replace(/'/g, "\\'")}', ${note.id})" title="Click to enlarge">
                                                ` : ''}
                                                <div class="card-body text-center p-2">
                                                    ${!isImage ? `<i class="${fileIcon} fa-2x mb-2"></i>` : ''}
                                                    <p class="small mb-1 text-truncate" title="${fileName}">${fileName}</p>
                                                    <a href="${fullPath}" target="_blank" class="btn btn-sm btn-outline-primary">
                                                        <i class="fas fa-${isImage ? 'download' : 'download'}"></i>
                                                    </a>
                                                </div>
                                            </div>
                                        </div>
                                    `;
                                }).join('')}
                            </div>
                        </div>
                    ` : ''}
                    
                    <div class="d-flex gap-2">
                        <button type="button" class="btn btn-sm btn-primary edit-note-inline-btn">
                            <i class="fas fa-edit me-1"></i>Edit
                        </button>
                        <button type="button" class="btn btn-sm btn-danger delete-note-inline-btn">
                            <i class="fas fa-trash me-1"></i>Delete
                        </button>
                    </div>
                </div>
                
                <div class="note-edit-view" style="display: none;">
                    <div class="d-flex justify-content-between align-items-start mb-3">
                        <h5 class="mb-0">
                            <i class="fas fa-edit me-2"></i>Edit Note
                        </h5>
                        <button type="button" class="btn btn-sm btn-outline-secondary cancel-edit-inline-btn">
                            <i class="fas fa-times me-1"></i>Cancel
                        </button>
                    </div>
                    
                    <div class="mb-3">
                        <label class="form-label">Title:</label>
                        <input type="text" class="form-control inline-edit-title" value="${(note.note_title || '').replace(/"/g, '&quot;')}">
                    </div>
                    
                    <div class="mb-3">
                        <label class="form-label">Content:</label>
                        <textarea class="form-control inline-edit-text" rows="4">${note.note_text}</textarea>
                    </div>
                    
                    <div class="mb-3">
                        <div class="d-flex flex-wrap gap-2">
                            <button type="button" class="btn btn-sm btn-outline-success toggle-edit-section-btn" 
                                    data-target="edit-bookmarks-${note.id}">
                                <i class="fas fa-bookmark me-1"></i>Bookmarks <i class="fas fa-chevron-down ms-1"></i>
                            </button>
                            <button type="button" class="btn btn-sm btn-outline-warning toggle-edit-section-btn" 
                                    data-target="edit-reminder-${note.id}">
                                <i class="fas fa-bell me-1"></i>Reminder <i class="fas fa-chevron-down ms-1"></i>
                            </button>
                            <button type="button" class="btn btn-sm btn-outline-info toggle-edit-section-btn" 
                                    data-target="edit-attachments-${note.id}">
                                <i class="fas fa-paperclip me-1"></i>Attachments <i class="fas fa-chevron-down ms-1"></i>
                            </button>
                            <button type="button" class="btn btn-sm btn-outline-primary toggle-edit-section-btn" 
                                    data-target="edit-associations-${note.id}">
                                <i class="fas fa-link me-1"></i>Associate <i class="fas fa-chevron-down ms-1"></i>
                            </button>
                        </div>
                    </div>
                    
                    <div class="edit-collapsible-section mb-3" id="edit-bookmarks-${note.id}" style="display: none;">
                        <div class="border rounded p-3 bg-light">
                            <label class="form-label">
                                <i class="fas fa-bookmark text-success me-1"></i>URL Bookmarks
                            </label>
                            <div class="inline-edit-bookmarks-container">
                                ${note.url_bookmarks && note.url_bookmarks.length > 0 ? note.url_bookmarks.map((bookmark, idx) => `
                                    <div class="bookmark-edit-entry mb-2 p-2 border rounded" data-bookmark-index="${idx}">
                                        <div class="row g-2">
                                            <div class="col-md-5">
                                                <input type="text" class="form-control form-control-sm bookmark-name-input" placeholder="Name" value="${(bookmark.friendly_name || '').replace(/"/g, '&quot;')}">
                                            </div>
                                            <div class="col-md-6">
                                                <input type="url" class="form-control form-control-sm bookmark-url-input" placeholder="URL" value="${(bookmark.url || '').replace(/"/g, '&quot;')}">
                                            </div>
                                            <div class="col-md-1">
                                                <button type="button" class="btn btn-sm btn-danger remove-bookmark-btn" title="Remove">
                                                    <i class="fas fa-times"></i>
                                                </button>
                                            </div>
                                        </div>
                                    </div>
                                `).join('') : '<p class="text-muted small">No bookmarks</p>'}
                            </div>
                            <button type="button" class="btn btn-sm btn-outline-success mt-2 add-bookmark-inline-btn">
                                <i class="fas fa-plus me-1"></i>Add Bookmark
                            </button>
                            <div class="form-text">
                                <i class="fas fa-info-circle me-1"></i> 
                                Add reference links with friendly names.
                            </div>
                        </div>
                    </div>
                    
                    <div class="edit-collapsible-section mb-3" id="edit-reminder-${note.id}" style="display: none;">
                        <div class="border rounded p-3 bg-light">
                            <label class="form-label">
                                <i class="fas fa-bell text-warning me-1"></i>Reminder Date & Time
                            </label>
                            <input type="datetime-local" class="form-control inline-edit-reminder" 
                                   value="${note.reminder ? new Date(note.reminder.scheduled_for).toISOString().slice(0, 16) : ''}">
                            <div class="form-text">
                                <i class="fas fa-info-circle me-1"></i> 
                                Set a specific date and time for this reminder. Leave empty to remove.
                            </div>
                            ${note.reminder ? `
                                <div class="mt-2 small text-info">
                                    <i class="fas fa-info-circle me-1"></i>
                                    Current status: ${note.reminder.is_dismissed ? 'Dismissed' : note.reminder.is_read ? 'Completed' : 'Active'}
                                </div>
                            ` : ''}
                        </div>
                    </div>
                    
                    <div class="edit-collapsible-section mb-3" id="edit-attachments-${note.id}" style="display: none;">
                        <div class="border rounded p-3 bg-light">
                            <label class="form-label">
                                <i class="fas fa-paperclip text-info me-1"></i>Attachments
                            </label>
                            ${note.file_paths && note.file_paths.length > 0 ? `
                                <div class="existing-attachments mb-2">
                                    <h6 class="small text-muted">Current Files:</h6>
                                    <div class="row row-cols-2 row-cols-md-3 g-2">
                                        ${note.file_paths.map((filePath, fileIndex) => {
                                            const fileName = filePath.split('/').pop();
                                            const fileExt = fileName.split('.').pop().toLowerCase();
                                            const fileIcon = getFileIcon(fileExt);
                                            return `
                                                <div class="col">
                                                    <div class="card h-100">
                                                        <div class="card-body text-center p-2">
                                                            <i class="${fileIcon} fa-lg mb-1"></i>
                                                            <p class="small mb-1 text-truncate">${fileName}</p>
                                                            <button type="button" class="btn btn-sm btn-danger remove-attachment-btn" data-file-index="${fileIndex}" data-file-name="${fileName}">
                                                                <i class="fas fa-times"></i>
                                                            </button>
                                                        </div>
                                                    </div>
                                                </div>
                                            `;
                                        }).join('')}
                                    </div>
                                </div>
                            ` : ''}
                            <label class="form-label ${note.file_paths && note.file_paths.length > 0 ? 'mt-2' : ''}">Add New Files:</label>
                            <input type="file" class="form-control inline-edit-files" multiple>
                            <div class="form-text">
                                <i class="fas fa-info-circle me-1"></i> 
                                Upload files to attach to this note. Existing files will be kept unless removed.
                            </div>
                        </div>
                    </div>
                    
                    <div class="edit-collapsible-section mb-3" id="edit-associations-${note.id}" style="display: none;">
                        <div class="border rounded p-3 bg-light">
                            <label class="form-label">
                                <i class="fas fa-link text-primary me-1"></i>Associate with Additional Entries
                            </label>
                            <select class="form-select inline-edit-associations" multiple size="4">
                                <option value="" disabled>Loading entries...</option>
                            </select>
                            <div class="form-text">
                                <i class="fas fa-info-circle me-1"></i>
                                Hold Ctrl/Cmd to select multiple entries. This note will appear in all selected entries.
                            </div>
                            ${note.associated_entry_ids && note.associated_entry_ids.length > 0 ? `
                                <div class="mt-2 small text-info">
                                    <i class="fas fa-info-circle me-1"></i>
                                    Currently associated with ${note.associated_entry_ids.length} ${note.associated_entry_ids.length === 1 ? 'entry' : 'entries'}
                                </div>
                            ` : ''}
                        </div>
                    </div>
                    
                    <div class="d-flex gap-2">
                        <button type="button" class="btn btn-sm btn-success save-note-inline-btn">
                            <i class="fas fa-save me-1"></i>Save Changes
                        </button>
                        <button type="button" class="btn btn-sm btn-secondary cancel-edit-inline-btn">
                            Cancel
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        return noteItem;
    }
    
    function getNoteTypeColor(noteType) {
        // Use loaded colors from configuration, fallback to default gray
        return noteTypeColors[noteType] || '#6c757d';
    }
    
    // Gallery state for image carousel
    let currentImageGallery = [];
    let currentImageIndex = 0;
    
    function openImageViewer(imageSrc, imageTitle, imageGallery = null, startIndex = 0) {
        // Open image in modal viewer with optional gallery/carousel support
        const imageElement = document.getElementById('imageViewerImg');
        const titleElement = document.getElementById('imageViewerTitle');
        const counterElement = document.getElementById('imageCounter');
        const prevBtn = document.getElementById('imagePrevBtn');
        const nextBtn = document.getElementById('imageNextBtn');
        
        if (imageElement && imageViewerModal) {
            // Set up gallery if provided
            if (imageGallery && Array.isArray(imageGallery) && imageGallery.length > 0) {
                currentImageGallery = imageGallery;
                currentImageIndex = startIndex;
            } else {
                // Single image mode
                currentImageGallery = [{ src: imageSrc, title: imageTitle }];
                currentImageIndex = 0;
            }
            
            // Display current image
            displayCurrentImage();
            
            // Show/hide navigation buttons
            if (currentImageGallery.length > 1) {
                prevBtn.style.display = 'block';
                nextBtn.style.display = 'block';
                counterElement.textContent = `(${currentImageIndex + 1} of ${currentImageGallery.length})`;
                
                // Update button states
                prevBtn.disabled = currentImageIndex === 0;
                nextBtn.disabled = currentImageIndex === currentImageGallery.length - 1;
            } else {
                prevBtn.style.display = 'none';
                nextBtn.style.display = 'none';
                counterElement.textContent = '';
            }
            
            imageViewerModal.show();
            
            // Add click handler to modal body to close when clicking outside image
            const modalBody = document.querySelector('#imageViewerModal .modal-body');
            if (modalBody) {
                const clickHandler = function(e) {
                    if (e.target === modalBody) {
                        imageViewerModal.hide();
                    }
                };
                modalBody.addEventListener('click', clickHandler, { once: true });
            }
        }
    }
    
    function displayCurrentImage() {
        const imageElement = document.getElementById('imageViewerImg');
        const titleElement = document.getElementById('imageViewerTitle');
        const counterElement = document.getElementById('imageCounter');
        const prevBtn = document.getElementById('imagePrevBtn');
        const nextBtn = document.getElementById('imageNextBtn');
        
        if (currentImageGallery.length > 0 && currentImageIndex >= 0 && currentImageIndex < currentImageGallery.length) {
            const currentImage = currentImageGallery[currentImageIndex];
            imageElement.src = currentImage.src;
            if (titleElement) {
                titleElement.textContent = currentImage.title || 'Image preview';
            }
            
            // Update counter
            if (currentImageGallery.length > 1) {
                counterElement.textContent = `(${currentImageIndex + 1} of ${currentImageGallery.length})`;
                prevBtn.disabled = currentImageIndex === 0;
                nextBtn.disabled = currentImageIndex === currentImageGallery.length - 1;
            }
        }
    }
    
    function navigateImage(direction) {
        if (direction === 'prev' && currentImageIndex > 0) {
            currentImageIndex--;
            displayCurrentImage();
        } else if (direction === 'next' && currentImageIndex < currentImageGallery.length - 1) {
            currentImageIndex++;
            displayCurrentImage();
        }
    }
    
    // Wire up navigation buttons (on DOMContentLoaded, after modal initialization)
    document.addEventListener('DOMContentLoaded', function() {
        const prevBtn = document.getElementById('imagePrevBtn');
        const nextBtn = document.getElementById('imageNextBtn');
        
        if (prevBtn) {
            prevBtn.addEventListener('click', () => navigateImage('prev'));
        }
        if (nextBtn) {
            nextBtn.addEventListener('click', () => navigateImage('next'));
        }
        
        // Keyboard navigation (arrow keys)
        document.addEventListener('keydown', function(e) {
            const modalElement = document.getElementById('imageViewerModal');
            if (modalElement && modalElement.classList.contains('show')) {
                if (e.key === 'ArrowLeft') {
                    navigateImage('prev');
                } else if (e.key === 'ArrowRight') {
                    navigateImage('next');
                }
            }
        });
    });
    
    function getReminderIndicator(reminder) {
        const reminderDate = new Date(reminder.scheduled_for);
        const now = new Date();
        const isPast = reminderDate <= now;
        const isRead = reminder.is_read;
        const isDismissed = reminder.is_dismissed;
        
        if (isDismissed) {
            return { icon: 'fas fa-bell-slash', color: 'text-muted', title: 'Reminder dismissed' };
        } else if (isPast && !isRead) {
            return { icon: 'fas fa-bell', color: 'text-danger', title: `Overdue: ${reminderDate.toLocaleString()}` };
        } else if (isPast && isRead) {
            return { icon: 'fas fa-check-circle', color: 'text-success', title: 'Reminder completed' };
        } else {
            return { icon: 'fas fa-bell', color: 'text-warning', title: `Reminder: ${reminderDate.toLocaleString()}` };
        }
    }
    
    function createBookmarksDisplay(bookmarks) {
        if (!bookmarks || bookmarks.length === 0) return '';
        
        let html = '<div class="mt-2"><small class="text-muted"><i class="fas fa-bookmark me-1"></i>Bookmarks:</small><br>';
        bookmarks.forEach(bookmark => {
            const displayName = bookmark.friendly_name || bookmark.url;
            html += `<a href="${bookmark.url}" target="_blank" class="text-decoration-none me-3">
                <small><i class="fas fa-external-link-alt me-1"></i>${displayName}</small>
            </a>`;
        });
        html += '</div>';
        return html;
    }
    
    // Open note details modal
    function openNoteDetails(noteId) {
        console.log('openNoteDetails called with noteId:', noteId);
        console.log('loadedNotes map:', loadedNotes);
        
        const note = loadedNotes.get(noteId);
        console.log('Retrieved note:', note);
        
        if (!note) {
            console.error('Note not found in loadedNotes map');
            alert('Could not load note details.');
            return;
        }
        
        currentNoteIdInModal = noteId;
        
        if (modalNoteTitle) modalNoteTitle.textContent = note.note_title || 'Untitled';
        if (modalNoteType) modalNoteType.textContent = note.note_type || 'General';
        if (modalNoteCreated) modalNoteCreated.textContent = new Date(note.created_at).toLocaleString();
        if (modalNoteContent) modalNoteContent.textContent = note.note_text;
        
        displayModalBookmarks(note.url_bookmarks);
        displayModalReminder(note.reminder);
        displayModalRelationships(note);
        displayModalFiles(note.file_paths);
        
        // Initialize modal if not already done
        if (!noteDetailModal && typeof bootstrap !== 'undefined') {
            console.log('Initializing Bootstrap modal...');
            const modalElement = document.getElementById('noteDetailModal');
            if (modalElement) {
                noteDetailModal = new bootstrap.Modal(modalElement);
                console.log('Modal initialized:', noteDetailModal);
            } else {
                console.error('Modal element not found');
            }
        }
        
        if (noteDetailModal) {
            console.log('Showing modal...');
            noteDetailModal.show();
        } else {
            console.error('Bootstrap modal not available');
            alert('Modal system not ready. Please try again.');
        }
    }
    
    function displayModalBookmarks(bookmarks) {
        const display = document.getElementById('modalBookmarksDisplay');
        const list = document.getElementById('modalBookmarksList');
        
        list.innerHTML = '';
        
        if (bookmarks && bookmarks.length > 0) {
            display.style.display = 'block';
            bookmarks.forEach(bookmark => {
                const item = document.createElement('a');
                item.href = bookmark.url;
                item.target = '_blank';
                item.className = 'list-group-item list-group-item-action';
                item.innerHTML = `
                    <i class="fas fa-external-link-alt me-2"></i>
                    ${bookmark.friendly_name || bookmark.url}
                    ${bookmark.friendly_name ? `<br><small class="text-muted">${bookmark.url}</small>` : ''}
                `;
                list.appendChild(item);
            });
        } else {
            display.style.display = 'none';
        }
    }
    
    function displayModalReminder(reminder) {
        const reminderSection = document.getElementById('modalNoteReminder');
        
        if (!reminder) {
            reminderSection.style.display = 'none';
            return;
        }
        
        reminderSection.style.display = 'block';
        const reminderDate = new Date(reminder.scheduled_for);
        document.getElementById('modalReminderDate').textContent = reminderDate.toLocaleString();
        
        const { badge, progressHtml } = getReminderStatus(reminder);
        document.getElementById('modalReminderStatus').className = `badge ${badge}`;
        document.getElementById('modalReminderStatus').textContent = badge.includes('danger') ? 'Overdue' : 
            badge.includes('success') ? 'Completed' : badge.includes('secondary') ? 'Dismissed' : 'Scheduled';
        document.getElementById('reminderProgress').innerHTML = progressHtml;
    }
    
    function getReminderStatus(reminder) {
        const reminderDate = new Date(reminder.scheduled_for);
        const now = new Date();
        const isPast = reminderDate <= now;
        
        if (reminder.is_dismissed) {
            return {
                badge: 'bg-secondary',
                progressHtml: '<small class="text-muted"><i class="fas fa-ban me-1"></i>Dismissed</small>'
            };
        } else if (isPast && !reminder.is_read) {
            const hours = Math.floor((now - reminderDate) / (1000 * 60 * 60));
            return {
                badge: 'bg-danger',
                progressHtml: `<small class="text-danger"><i class="fas fa-exclamation-triangle me-1"></i>Overdue by ${hours} hours</small>`
            };
        } else if (isPast && reminder.is_read) {
            return {
                badge: 'bg-success',
                progressHtml: '<small class="text-success"><i class="fas fa-check-circle me-1"></i>Completed</small>'
            };
        } else {
            const hours = Math.ceil((reminderDate - now) / (1000 * 60 * 60));
            return {
                badge: 'bg-warning text-dark',
                progressHtml: `<small class="text-info"><i class="fas fa-clock me-1"></i>Due in ${hours} hours</small>`
            };
        }
    }
    
    function displayModalRelationships(note) {
        const section = document.getElementById('modalNoteRelationships');
        
        if (note.associated_entry_ids && note.associated_entry_ids.length > 0) {
            section.style.display = 'block';
            document.getElementById('modalRelationshipDetails').innerHTML = `
                <small class="text-muted">
                    <i class="fas fa-sitemap me-1"></i>Associated with ${note.associated_entry_ids.length} other entries
                </small>
            `;
        } else {
            section.style.display = 'none';
        }
    }
    
    function displayModalFiles(filePaths) {
        if (!modalNoteFiles) return;
        
        modalNoteFiles.innerHTML = '';
        
        const noAttachmentsPlaceholder = document.getElementById('noAttachmentsPlaceholder');
        
        if (!filePaths || filePaths.length === 0) {
            if (noAttachmentsPlaceholder) {
                noAttachmentsPlaceholder.style.display = 'block';
            }
            return;
        }
        
        if (noAttachmentsPlaceholder) {
            noAttachmentsPlaceholder.style.display = 'none';
        }
        
        filePaths.forEach(filePath => {
            const fileName = filePath.split('/').pop();
            const fileExt = fileName.split('.').pop().toLowerCase();
            const fileIcon = getFileIcon(fileExt);
            
            const fileCard = document.createElement('div');
            fileCard.className = 'col';
            fileCard.innerHTML = `
                <div class="card h-100">
                    <div class="card-body text-center">
                        <i class="${fileIcon} fa-3x mb-2"></i>
                        <p class="small mb-0">${fileName}</p>
                        <a href="${filePath}" target="_blank" class="btn btn-sm btn-outline-primary mt-2">
                            <i class="fas fa-download me-1"></i>Download
                        </a>
                    </div>
                </div>
            `;
            modalNoteFiles.appendChild(fileCard);
        });
    }
    
    function getFileIcon(extension) {
        const icons = {
            'pdf': 'fas fa-file-pdf text-danger',
            'doc': 'fas fa-file-word text-primary',
            'docx': 'fas fa-file-word text-primary',
            'xls': 'fas fa-file-excel text-success',
            'xlsx': 'fas fa-file-excel text-success',
            'jpg': 'fas fa-file-image text-info',
            'jpeg': 'fas fa-file-image text-info',
            'png': 'fas fa-file-image text-info',
            'gif': 'fas fa-file-image text-info',
            'zip': 'fas fa-file-archive text-warning',
            'rar': 'fas fa-file-archive text-warning'
        };
        return icons[extension] || 'fas fa-file';
    }
    
    // Search and filter
    function handleSearchInput() {
        const searchTerm = notesSearchInput.value.trim();
        if (searchTerm) {
            clearNotesSearch.style.display = 'inline-block';
        } else {
            clearNotesSearch.style.display = 'none';
        }
        applyNotesFilter();
    }
    
    function clearSearchAndFilter() {
        notesSearchInput.value = '';
        clearNotesSearch.style.display = 'none';
        applyNotesFilter();
    }
    
    function updateNoteTypeFilter() {
        const noteTypes = [...new Set(allNotes.map(note => note.note_type || 'General'))];
        noteTypes.sort();
        
        notesTypeFilter.innerHTML = '<option value="">All Types</option>';
        noteTypes.forEach(type => {
            const option = document.createElement('option');
            option.value = type;
            option.textContent = type;
            notesTypeFilter.appendChild(option);
        });
    }
    
    function applyNotesFilter() {
        const searchTerm = notesSearchInput.value.toLowerCase().trim();
        const selectedType = notesTypeFilter.value;
        const sortOrder = notesSortOrder.value;
        
        filteredNotes = allNotes.filter(note => {
            const matchesSearch = !searchTerm ||
                (note.note_title && note.note_title.toLowerCase().includes(searchTerm)) ||
                (note.note_text && note.note_text.toLowerCase().includes(searchTerm));
            
            const matchesType = !selectedType || (note.note_type || 'General') === selectedType;
            
            return matchesSearch && matchesType;
        });
        
        sortNotes(filteredNotes, sortOrder);
        notesCount.textContent = filteredNotes.length;
        displayNotes(filteredNotes);
    }
    
    function sortNotes(notes, sortOrder) {
        switch (sortOrder) {
            case 'oldest':
                notes.sort((a, b) => new Date(a.created_at) - new Date(b.created_at));
                break;
            case 'title':
                notes.sort((a, b) => (a.note_title || '').localeCompare(b.note_title || ''));
                break;
            case 'newest':
            default:
                notes.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
                break;
        }
    }
    
    // Reminder progress summary
    function updateReminderProgressSummary(notes) {
        const summary = document.getElementById('reminderProgressSummary');
        const content = document.getElementById('reminderProgressContent');
        
        if (!summary || !content) return;
        
        const notesWithReminders = notes.filter(note => note.reminder);
        
        if (notesWithReminders.length === 0) {
            summary.style.display = 'none';
            return;
        }
        
        const now = new Date();
        let overdue = 0, upcoming = 0, completed = 0, dismissed = 0;
        
        notesWithReminders.forEach(note => {
            const reminderDate = new Date(note.reminder.scheduled_for);
            const isPast = reminderDate <= now;
            
            if (note.reminder.is_dismissed) dismissed++;
            else if (isPast && !note.reminder.is_read) overdue++;
            else if (isPast && note.reminder.is_read) completed++;
            else upcoming++;
        });
        
        let html = '<div class="d-flex flex-wrap gap-2">';
        if (overdue > 0) html += `<span class="badge bg-danger">${overdue} Overdue</span>`;
        if (upcoming > 0) html += `<span class="badge bg-warning text-dark">${upcoming} Upcoming</span>`;
        if (completed > 0) html += `<span class="badge bg-success">${completed} Completed</span>`;
        if (dismissed > 0) html += `<span class="badge bg-secondary">${dismissed} Dismissed</span>`;
        html += '</div>';
        
        content.innerHTML = html;
        summary.style.display = 'block';
    }
    
    // Edit note
    function enterEditMode() {
        const note = loadedNotes.get(currentNoteIdInModal);
        if (!note) return;
        
        document.getElementById('editNoteTitle').value = note.note_title || '';
        document.getElementById('editNoteText').value = note.note_text;
        populateEditBookmarks(note.url_bookmarks);
        
        document.getElementById('noteContentDisplay').style.display = 'none';
        document.getElementById('noteContentEditMode').style.display = 'block';
    }
    
    function cancelEditMode() {
        document.getElementById('noteContentDisplay').style.display = 'block';
        document.getElementById('noteContentEditMode').style.display = 'none';
    }
    
    async function saveNoteEdits() {
        const noteTitle = document.getElementById('editNoteTitle').value.trim();
        const noteText = document.getElementById('editNoteText').value.trim();
        const bookmarks = getEditUrlBookmarks();
        
        if (!noteText) {
            alert('Note content cannot be empty.');
            return;
        }
        
        try {
            const response = await fetch(`/api/entries/${entryId}/notes/${currentNoteIdInModal}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    note_title: noteTitle,
                    note_text: noteText,
                    url_bookmarks: bookmarks
                })
            });
            
            if (response.ok) {
                alert('Note updated successfully!');
                cancelEditMode();
                fetchNotes();
                noteDetailModal.hide();
            } else {
                const data = await response.json();
                alert(`Error: ${data.message || 'Failed to update note.'}`);
            }
        } catch (error) {
            console.error('Error updating note:', error);
            alert('An unexpected error occurred.');
        }
    }
    
    // Delete note
    async function deleteNote(noteId = null) {
        const noteIdToDelete = noteId || currentNoteIdInModal;
        if (!noteIdToDelete) return;
        
        try {
            const response = await fetch(`/api/notes/${noteIdToDelete}`, {
                method: 'DELETE'
            });
            
            if (response.ok) {
                alert('Note deleted successfully!');
                if (noteDetailModal && currentNoteIdInModal === noteIdToDelete) {
                    noteDetailModal.hide();
                }
                fetchNotes();
            } else {
                alert('Failed to delete note.');
            }
        } catch (error) {
            console.error('Error deleting note:', error);
            alert('An unexpected error occurred.');
        }
    }
    
    // Reminder editing
    function enterReminderEditMode() {
        const note = loadedNotes.get(currentNoteIdInModal);
        if (!note || !note.reminder) return;
        
        const reminderDate = new Date(note.reminder.scheduled_for);
        reminderDate.setMinutes(reminderDate.getMinutes() - reminderDate.getTimezoneOffset());
        document.getElementById('editReminderDateTime').value = reminderDate.toISOString().slice(0, 16);
        
        document.getElementById('reminderDisplayMode').style.display = 'none';
        document.getElementById('reminderEditMode').style.display = 'block';
    }
    
    function cancelReminderEdit() {
        document.getElementById('reminderDisplayMode').style.display = 'block';
        document.getElementById('reminderEditMode').style.display = 'none';
    }
    
    async function saveReminderEdit() {
        const reminderDateTime = document.getElementById('editReminderDateTime').value;
        
        if (!reminderDateTime) {
            alert('Please select a date and time.');
            return;
        }
        
        try {
            const response = await fetch(`/api/entries/${entryId}/notes/${currentNoteIdInModal}/reminder`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ reminder_date: reminderDateTime })
            });
            
            if (response.ok) {
                alert('Reminder updated successfully!');
                cancelReminderEdit();
                fetchNotes();
                noteDetailModal.hide();
            } else {
                alert('Failed to update reminder.');
            }
        } catch (error) {
            console.error('Error updating reminder:', error);
            alert('An unexpected error occurred.');
        }
    }
    
    async function deleteReminder() {
        if (!confirm('Remove this reminder?')) return;
        
        try {
            const response = await fetch(`/api/entries/${entryId}/notes/${currentNoteIdInModal}/reminder`, {
                method: 'DELETE'
            });
            
            if (response.ok) {
                alert('Reminder removed successfully!');
                cancelReminderEdit();
                fetchNotes();
                noteDetailModal.hide();
            } else {
                alert('Failed to remove reminder.');
            }
        } catch (error) {
            console.error('Error removing reminder:', error);
            alert('An unexpected error occurred.');
        }
    }
    
    // Attachment management
    function showAddAttachmentsForm() {
        document.getElementById('addAttachmentsForm').style.display = 'block';
    }
    
    function hideAddAttachmentsForm() {
        document.getElementById('addAttachmentsForm').style.display = 'none';
        document.getElementById('additionalFiles').value = '';
    }
    
    async function uploadAdditionalFiles() {
        const files = document.getElementById('additionalFiles').files;
        
        if (files.length === 0) {
            alert('Please select files to upload.');
            return;
        }
        
        const formData = new FormData();
        for (let file of files) {
            formData.append('files', file);
        }
        
        try {
            const response = await fetch(`/api/entries/${entryId}/notes/${currentNoteIdInModal}/files`, {
                method: 'POST',
                body: formData
            });
            
            if (response.ok) {
                alert('Files uploaded successfully!');
                hideAddAttachmentsForm();
                fetchNotes();
                noteDetailModal.hide();
            } else {
                alert('Failed to upload files.');
            }
        } catch (error) {
            console.error('Error uploading files:', error);
            alert('An unexpected error occurred.');
        }
    }
    
    // Expose image viewer function globally so it can be called from onclick attributes
    window.openImageInModal = function(imageSrc, imageTitle, noteId = null) {
        // If noteId is provided, find all images in that note to create a gallery
        let gallery = null;
        let startIndex = 0;
        
        if (noteId !== null) {
            const note = window.notesCache?.find(n => n.id === noteId);
            if (note && note.file_paths) {
                // Build gallery from all images in the note
                gallery = note.file_paths
                    .filter(filePath => {
                        const fileExt = filePath.split('.').pop().toLowerCase();
                        return ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'svg'].includes(fileExt);
                    })
                    .map(imgPath => {
                        // Handle various path formats
                        let fullPath;
                        if (imgPath.startsWith('http://') || imgPath.startsWith('https://')) {
                            fullPath = imgPath;
                        } else if (imgPath.startsWith('/static/')) {
                            fullPath = imgPath;
                        } else if (imgPath.startsWith('uploads/')) {
                            fullPath = `/static/${imgPath}`;
                        } else {
                            fullPath = `/static/uploads/${imgPath}`;
                        }
                        const fileName = imgPath.split('/').pop();
                        return { src: fullPath, title: fileName };
                    });
                
                // Find the index of the clicked image
                startIndex = gallery.findIndex(img => img.src === imageSrc);
                if (startIndex === -1) startIndex = 0;
            }
        }
        
        openImageViewer(imageSrc, imageTitle, gallery, startIndex);
    };
    
    // Store notes in window for gallery access
    window.notesCache = [];
    
})();
</script>
