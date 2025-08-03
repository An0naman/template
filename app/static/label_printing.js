// Label Printing JavaScript
document.addEventListener('DOMContentLoaded', function() {
    const labelTypeSelect = document.getElementById('labelTypeSelect');
    const labelPositionContainer = document.getElementById('labelPositionContainer');
    const labelRotationSelect = document.getElementById('labelRotationSelect');
    const previewLabelBtn = document.getElementById('previewLabelBtn');
    const printLabelBtn = document.getElementById('printLabelBtn');
    const downloadLabelPdfBtn = document.getElementById('downloadLabelPdfBtn');
    const labelPreviewContainer = document.getElementById('labelPreviewContainer');
    const labelStatusMessage = document.getElementById('labelStatusMessage');

    // Check if all elements exist
    if (!labelTypeSelect || !labelPositionContainer || !previewLabelBtn || !printLabelBtn || !downloadLabelPdfBtn) {
        console.log('Label printing elements not found on this page');
        return;
    }

    // Get entry ID from the URL or a data attribute
    const entryId = window.location.pathname.split('/').pop();
    
    // Store selected positions
    let selectedPositions = new Set();

    // Initialize label position grid based on selected type
    function updateLabelPositions() {
        const labelType = labelTypeSelect.value;
        const config = labelType === '8_labels' ? 
            { rows: 4, cols: 2, name: '8 Labels (2x4)' } : 
            { rows: 7, cols: 2, name: '14 Labels (2x7)' };
        
        selectedPositions.clear();
        
        labelPositionContainer.innerHTML = `
            <div class="mb-2">
                <strong>Select Label Positions:</strong>
                <small class="text-muted ms-2">(${config.name})</small>
            </div>
            <div class="label-grid">
                ${generateLabelGrid(config.rows, config.cols)}
            </div>
            <div class="mt-2">
                <button type="button" class="btn btn-sm btn-theme-secondary me-2" id="selectAllLabels">
                    Select All
                </button>
                <button type="button" class="btn btn-sm btn-theme-secondary" id="clearAllLabels">
                    Clear All
                </button>
                <small class="text-muted ms-3">Selected: <span id="selectedCount">0</span></small>
            </div>
        `;
        
        // Add click handlers for grid positions
        setupPositionHandlers();
        
        // Update rotation options based on label type
        updateRotationOptions();
    }
    
    // Update rotation options based on label type
    function updateRotationOptions() {
        if (!labelRotationSelect) return;
        
        const labelType = labelTypeSelect.value;
        const is14Labels = labelType === '14_labels';
        
        // Get the 90-degree option
        const option90 = labelRotationSelect.querySelector('option[value="90"]');
        
        if (is14Labels) {
            // For 14-label sheets, disable 90-degree rotation and force to 0
            if (option90) {
                option90.disabled = true;
                option90.style.display = 'none';
            }
            labelRotationSelect.value = '0';
            
            // Add a note about why rotation is disabled
            let noteElement = document.getElementById('rotationNote');
            if (!noteElement) {
                noteElement = document.createElement('small');
                noteElement.id = 'rotationNote';
                noteElement.className = 'text-muted';
                labelRotationSelect.parentNode.appendChild(noteElement);
            }
            noteElement.textContent = 'Rotation disabled for 14-label sheets';
            noteElement.style.display = 'block';
        } else {
            // For 8-label sheets, enable 90-degree rotation
            if (option90) {
                option90.disabled = false;
                option90.style.display = 'block';
            }
            
            // Hide the note
            const noteElement = document.getElementById('rotationNote');
            if (noteElement) {
                noteElement.style.display = 'none';
            }
        }
    }
    
    function generateLabelGrid(rows, cols) {
        let grid = '<div class="label-grid-container">';
        let position = 1;
        
        for (let row = 0; row < rows; row++) {
            grid += '<div class="label-row">';
            for (let col = 0; col < cols; col++) {
                grid += `
                    <div class="label-position" data-position="${position}" title="Position ${position}">
                        ${position}
                    </div>
                `;
                position++;
            }
            grid += '</div>';
        }
        grid += '</div>';
        return grid;
    }
    
    function setupPositionHandlers() {
        const positions = document.querySelectorAll('.label-position');
        const selectAllBtn = document.getElementById('selectAllLabels');
        const clearAllBtn = document.getElementById('clearAllLabels');
        const selectedCountSpan = document.getElementById('selectedCount');
        
        positions.forEach(pos => {
            pos.addEventListener('click', () => {
                const position = parseInt(pos.dataset.position);
                if (selectedPositions.has(position)) {
                    selectedPositions.delete(position);
                    pos.classList.remove('selected');
                } else {
                    selectedPositions.add(position);
                    pos.classList.add('selected');
                }
                selectedCountSpan.textContent = selectedPositions.size;
            });
        });
        
        selectAllBtn.addEventListener('click', () => {
            positions.forEach(pos => {
                const position = parseInt(pos.dataset.position);
                selectedPositions.add(position);
                pos.classList.add('selected');
            });
            selectedCountSpan.textContent = selectedPositions.size;
        });
        
        clearAllBtn.addEventListener('click', () => {
            selectedPositions.clear();
            positions.forEach(pos => pos.classList.remove('selected'));
            selectedCountSpan.textContent = '0';
        });
    }

    function displayLabelStatus(message, alertClass) {
        labelStatusMessage.className = `alert ${alertClass}`;
        labelStatusMessage.textContent = message;
        labelStatusMessage.classList.remove('d-none');
        
        if (alertClass === 'alert-success') {
            setTimeout(() => {
                labelStatusMessage.classList.add('d-none');
            }, 3000);
        }
    }

    // Event listeners
    labelTypeSelect.addEventListener('change', updateLabelPositions);

    previewLabelBtn.addEventListener('click', async () => {
        try {
            displayLabelStatus('Generating preview...', 'alert-info');
            
            const rotation = labelRotationSelect ? parseInt(labelRotationSelect.value) : 0;
            const response = await fetch(`/api/entries/${entryId}/label_preview?label_type=${labelTypeSelect.value}&rotation=${rotation}`);
            if (!response.ok) throw new Error('Failed to generate preview');
            
            const data = await response.json();
            
            labelPreviewContainer.innerHTML = `
                <img src="${data.label_preview}" alt="Label Preview" class="img-fluid border rounded" style="max-width: 300px;">
            `;
            
            displayLabelStatus('Preview generated successfully!', 'alert-success');
            
        } catch (error) {
            console.error('Error generating preview:', error);
            displayLabelStatus('Failed to generate preview: ' + error.message, 'alert-danger');
        }
    });

    printLabelBtn.addEventListener('click', async () => {
        if (selectedPositions.size === 0) {
            displayLabelStatus('Please select at least one label position', 'alert-warning');
            return;
        }
        
        try {
            displayLabelStatus('Generating print page...', 'alert-info');
            
            const rotation = labelRotationSelect ? parseInt(labelRotationSelect.value) : 0;
            const response = await fetch(`/api/entries/${entryId}/print_labels`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    label_type: labelTypeSelect.value,
                    positions: Array.from(selectedPositions),
                    rotation: rotation
                })
            });
            
            if (!response.ok) throw new Error('Failed to generate print page');
            
            const data = await response.json();
            
            // Open in new window for printing
            const printWindow = window.open('', '_blank');
            const printContent = `
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Print Labels</title>
                    <style>
                        @page { margin: 0; }
                        body { margin: 0; padding: 0; }
                        img { width: 100%; height: auto; }
                    </style>
                </head>
                <body>
                    <img src="${data.print_page}" alt="Labels for Printing">
                </body>
                </html>
            `;
            printWindow.document.write(printContent);
            printWindow.document.close();
            
            displayLabelStatus('Print page opened in new window!', 'alert-success');
            
        } catch (error) {
            console.error('Error generating print page:', error);
            displayLabelStatus('Failed to generate print page: ' + error.message, 'alert-danger');
        }
    });

    downloadLabelPdfBtn.addEventListener('click', async () => {
        if (selectedPositions.size === 0) {
            displayLabelStatus('Please select at least one label position', 'alert-warning');
            return;
        }
        
        try {
            displayLabelStatus('Generating PDF...', 'alert-info');
            
            const rotation = labelRotationSelect ? parseInt(labelRotationSelect.value) : 0;
            const response = await fetch(`/api/entries/${entryId}/labels_pdf`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    label_type: labelTypeSelect.value,
                    positions: Array.from(selectedPositions),
                    rotation: rotation
                })
            });
            
            if (!response.ok) throw new Error('Failed to generate PDF');
            
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            a.download = `entry-${entryId}-labels.pdf`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            
            displayLabelStatus('PDF downloaded successfully!', 'alert-success');
            
        } catch (error) {
            console.error('Error downloading PDF:', error);
            displayLabelStatus('Failed to download PDF: ' + error.message, 'alert-danger');
        }
    });

    // Initialize label positions on page load
    updateLabelPositions();
    console.log('Label printing initialized successfully');
});
