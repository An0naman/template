// Label Printing JavaScript
document.addEventListener('DOMContentLoaded', function() {
    const labelTypeSelect = document.getElementById('labelTypeSelect');
    const labelPositionContainer = document.getElementById('labelPositionContainer');
    const labelRotationSelect = document.getElementById('labelRotationSelect');
    const printLabelBtn = document.getElementById('printLabelBtn');
    const downloadLabelPdfBtn = document.getElementById('downloadLabelPdfBtn');
    const labelPreviewContainer = document.getElementById('labelPreviewContainer');
    const labelStatusMessage = document.getElementById('labelStatusMessage');

    // Check if all elements exist
    if (!labelTypeSelect || !labelPositionContainer || !printLabelBtn || !downloadLabelPdfBtn) {
        console.log('Label printing elements not found on this page');
        return;
    }

    // Get entry ID from the URL or a data attribute
    const entryId = window.location.pathname.split('/').pop();
    
    // Store selected positions
    let selectedPositions = new Set();
    
    // Niimbot printer state
    let niimbotPrinters = [];
    let selectedPrinter = null;

    // Initialize label position grid based on selected type
    function updateLabelPositions() {
        const labelType = labelTypeSelect.value;
        
        // Check if this is a Niimbot printer type
        if (labelType.startsWith('niimbot_')) {
            setupNiimbotInterface(labelType);
            return;
        }
        
        // Regular sheet label logic
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
    
    // ============================================================================
    // Niimbot Printer Functions
    // ============================================================================
    
    function setupNiimbotInterface(labelType) {
        const printerModel = labelType.replace('niimbot_', '');
        
        labelPositionContainer.innerHTML = `
            <div class="niimbot-interface">
                <div class="mb-3">
                    <strong>Niimbot ${printerModel.toUpperCase()} Printer</strong>
                    <p class="text-muted small">Print labels directly to your Bluetooth label printer</p>
                </div>
                
                <div class="mb-3">
                    <label class="form-label">Label Size:</label>
                    <select class="form-select" id="niimbotLabelSize">
                        <option value="60x30mm" selected>60mm × 30mm</option>
                        <option value="30x15mm">30mm × 15mm</option>
                        <option value="40x12mm">40mm × 12mm</option>
                        <option value="50x14mm">50mm × 14mm</option>
                        <option value="75x12mm">75mm × 12mm</option>
                    </select>
                </div>
                
                <div class="mb-3">
                    <label class="form-label">Print Density (1-5):</label>
                    <input type="range" class="form-range" id="niimbotDensity" min="1" max="5" value="3">
                    <div class="d-flex justify-content-between">
                        <small>Light</small>
                        <small id="densityValue">3</small>
                        <small>Dark</small>
                    </div>
                </div>
                
                <div class="mb-3">
                    <label class="form-label">Quantity:</label>
                    <input type="number" class="form-control" id="niimbotQuantity" min="1" max="10" value="1">
                </div>
                
                <div class="mb-3">
                    <button type="button" class="btn btn-theme-primary w-100" id="discoverPrintersBtn">
                        <i class="bi bi-bluetooth"></i> Discover Printers
                    </button>
                </div>
                
                <div id="printerListContainer" class="mb-3" style="display:none;">
                    <label class="form-label">Available Printers:</label>
                    <div id="printerList" class="list-group"></div>
                </div>
                
                <div id="selectedPrinterInfo" class="alert alert-info" style="display:none;">
                    <strong>Selected Printer:</strong>
                    <div id="printerName"></div>
                    <small class="text-muted" id="printerAddress"></small>
                </div>
            </div>
        `;
        
        // Setup event listeners for Niimbot controls
        setupNiimbotEventListeners(printerModel);
        
        // Hide rotation controls for Niimbot
        if (labelRotationSelect) {
            labelRotationSelect.closest('.mb-3')?.style.setProperty('display', 'none');
        }
    }
    
    function setupNiimbotEventListeners(printerModel) {
        // Density slider
        const densitySlider = document.getElementById('niimbotDensity');
        const densityValue = document.getElementById('densityValue');
        if (densitySlider && densityValue) {
            densitySlider.addEventListener('input', (e) => {
                densityValue.textContent = e.target.value;
            });
        }
        
        // Label size selector - auto-preview when changed
        const labelSizeSelect = document.getElementById('niimbotLabelSize');
        if (labelSizeSelect) {
            labelSizeSelect.addEventListener('change', () => {
                autoPreviewLabel();
            });
        }
        
        // Discover printers button
        const discoverBtn = document.getElementById('discoverPrintersBtn');
        if (discoverBtn) {
            discoverBtn.addEventListener('click', () => discoverNiimbotPrinters(printerModel));
        }
        
        // Auto-load preview for Niimbot interface
        setTimeout(autoPreviewLabel, 100);
    }
    
    async function discoverNiimbotPrinters(printerModel) {
        const discoverBtn = document.getElementById('discoverPrintersBtn');
        const printerListContainer = document.getElementById('printerListContainer');
        const printerList = document.getElementById('printerList');
        
        try {
            discoverBtn.disabled = true;
            discoverBtn.innerHTML = '<i class="bi bi-bluetooth"></i> Scanning...';
            displayLabelStatus('Scanning for Niimbot printers...', 'alert-info');
            
            const response = await fetch('/api/niimbot/discover?timeout=10');
            if (!response.ok) throw new Error('Failed to discover printers');
            
            const data = await response.json();
            
            if (!data.success) {
                throw new Error(data.error || 'Discovery failed');
            }
            
            niimbotPrinters = data.printers || [];
            
            if (niimbotPrinters.length === 0) {
                displayLabelStatus('No Niimbot printers found. Make sure your printer is on and nearby.', 'alert-warning');
                printerListContainer.style.display = 'none';
            } else {
                displayLabelStatus(`Found ${niimbotPrinters.length} printer(s)`, 'alert-success');
                printerListContainer.style.display = 'block';
                
                // Display printer list
                printerList.innerHTML = niimbotPrinters.map((printer, index) => `
                    <a href="#" class="list-group-item list-group-item-action printer-item" data-index="${index}">
                        <div class="d-flex w-100 justify-content-between">
                            <h6 class="mb-1">${printer.name}</h6>
                            ${printer.rssi ? `<small class="text-muted">Signal: ${printer.rssi} dBm</small>` : ''}
                        </div>
                        <small class="text-muted">${printer.address}</small>
                    </a>
                `).join('');
                
                // Add click handlers for printer selection
                document.querySelectorAll('.printer-item').forEach(item => {
                    item.addEventListener('click', (e) => {
                        e.preventDefault();
                        const index = parseInt(e.currentTarget.dataset.index);
                        selectPrinter(niimbotPrinters[index]);
                    });
                });
            }
            
        } catch (error) {
            console.error('Error discovering printers:', error);
            displayLabelStatus('Error: ' + error.message, 'alert-danger');
        } finally {
            discoverBtn.disabled = false;
            discoverBtn.innerHTML = '<i class="bi bi-bluetooth"></i> Discover Printers';
        }
    }
    
    function selectPrinter(printer) {
        selectedPrinter = printer;
        
        const selectedInfo = document.getElementById('selectedPrinterInfo');
        const printerName = document.getElementById('printerName');
        const printerAddress = document.getElementById('printerAddress');
        
        printerName.textContent = printer.name;
        printerAddress.textContent = printer.address;
        selectedInfo.style.display = 'block';
        
        // Highlight selected printer
        document.querySelectorAll('.printer-item').forEach(item => {
            item.classList.remove('active');
        });
        event.currentTarget.classList.add('active');
        
        displayLabelStatus(`Selected: ${printer.name}`, 'alert-success');
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
    
    // Add rotation change listener for sheet labels auto-preview
    if (labelRotationSelect) {
        labelRotationSelect.addEventListener('change', () => {
            const labelType = labelTypeSelect.value;
            // Only auto-preview for sheet labels (Niimbot doesn't use rotation dropdown)
            if (!labelType.startsWith('niimbot_')) {
                setTimeout(autoPreviewLabel, 100);
            }
        });
    }

    printLabelBtn.addEventListener('click', async () => {
        const labelType = labelTypeSelect.value;
        
        // Check if this is a Niimbot printer
        if (labelType.startsWith('niimbot_')) {
            await printToNiimbot();
            return;
        }
        
        // Original sheet label printing logic
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
                    label_type: labelType,
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
    
    async function printToNiimbot() {
        if (!selectedPrinter) {
            displayLabelStatus('Please select a printer first', 'alert-warning');
            return;
        }
        
        try {
            displayLabelStatus('Preparing label for printing...', 'alert-info');
            
            const labelType = labelTypeSelect.value;
            const printerModel = labelType.replace('niimbot_', '');
            const labelSize = document.getElementById('niimbotLabelSize')?.value || '50x14mm';
            const density = parseInt(document.getElementById('niimbotDensity')?.value || 3);
            const quantity = parseInt(document.getElementById('niimbotQuantity')?.value || 1);
            
            // Get the image from the preview container
            const img = labelPreviewContainer.querySelector('img');
            if (!img || !img.src) {
                throw new Error('No preview available. Please generate a preview first.');
            }
            
            // Extract base64 data from the img src (format: "data:image/png;base64,...")
            const imageData = img.src.split(',')[1]; // Remove "data:image/png;base64," prefix
            
            displayLabelStatus('Sending to printer...', 'alert-info');
            
            const response = await fetch(`/api/niimbot/print_image`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    printer_address: selectedPrinter.address,
                    printer_model: printerModel,
                    image_data: imageData,
                    density: density,
                    quantity: quantity
                })
            });
            
            const data = await response.json();
            
            if (!data.success) {
                throw new Error(data.error || 'Print failed');
            }
            
            displayLabelStatus(data.message || 'Print successful!', 'alert-success');
            
        } catch (error) {
            console.error('Error printing to Niimbot:', error);
            displayLabelStatus('Print failed: ' + error.message, 'alert-danger');
        }
    }

    downloadLabelPdfBtn.addEventListener('click', async () => {
        const labelType = labelTypeSelect.value;
        
        // Niimbot printers don't support PDF download
        if (labelType.startsWith('niimbot_')) {
            displayLabelStatus('PDF download not available for Niimbot printers. Use direct printing instead.', 'alert-info');
            return;
        }
        
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
                    label_type: labelType,
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

    // Auto-preview function for all label types
    async function autoPreviewLabel() {
        const labelType = labelTypeSelect.value;
        
        try {
            // Show loading state
            labelPreviewContainer.innerHTML = `
                <div class="text-center py-4">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">Loading preview...</span>
                    </div>
                    <p class="mt-2 text-muted">Generating preview...</p>
                </div>
            `;
            
            const rotation = labelRotationSelect ? parseInt(labelRotationSelect.value) : 0;
            
            // Different handling for Niimbot vs sheet labels
            if (labelType.startsWith('niimbot_')) {
                // Niimbot labels - use backend-generated preview with styling params
                const labelSize = document.getElementById('niimbotLabelSize')?.value || '60x30mm';
                
                // Fetch system parameters to apply configured styling
                const paramsResponse = await fetch('/api/system_params');
                const systemParams = await paramsResponse.json();
                
                // Build query string with label size-specific settings
                const sizePrefix = `label_${labelSize}_`;
                const params = new URLSearchParams({
                    label_size: labelSize,
                    rotation: rotation,
                    label_type: labelType
                });
                
                // Add size-specific or default label settings
                const settingsToApply = [
                    'label_font_size', 'label_title_font_size', 'label_border_style',
                    'label_text_wrap', 'label_include_qr_code', 'label_qr_size', 
                    'label_qr_code_prefix', 'label_qr_position', 'label_include_logo', 
                    'label_logo_position'
                ];
                
                for (const setting of settingsToApply) {
                    // Try size-specific first
                    const sizeSpecificKey = setting.replace('label_', sizePrefix);
                    if (systemParams[sizeSpecificKey] !== undefined) {
                        params.append(setting, systemParams[sizeSpecificKey]);
                    } else if (systemParams[setting] !== undefined) {
                        // Fallback to default
                        params.append(setting, systemParams[setting]);
                    }
                }
                
                const response = await fetch(`/api/niimbot/preview/${entryId}?${params.toString()}`);
                
                if (!response.ok) throw new Error('Failed to generate preview');
                
                const data = await response.json();
                
                labelPreviewContainer.innerHTML = `
                    <img src="${data.label_preview}" alt="Label Preview" class="img-fluid border rounded" style="max-width: 500px;">
                `;
            } else {
                // Sheet labels - use sheet label preview endpoint
                const response = await fetch(`/api/entries/${entryId}/label_preview?label_type=${labelType}&rotation=${rotation}`);
                
                if (!response.ok) throw new Error('Failed to generate preview');
                
                const data = await response.json();
                
                labelPreviewContainer.innerHTML = `
                    <img src="${data.label_preview}" alt="Label Preview" class="img-fluid border rounded" style="max-width: 500px;">
                `;
            }
        } catch (error) {
            console.error('Error generating auto-preview:', error);
            labelPreviewContainer.innerHTML = `
                <div class="alert alert-warning">
                    <i class="bi bi-exclamation-triangle"></i> 
                    Preview unavailable: ${error.message}
                </div>
            `;
        }
    }
    
    // Canvas-based preview rendering (same logic as settings page)
    async function renderCanvasPreview(printerType, labelSize, rotation, systemParams, entryData) {
        // Extract settings for this label size
        const sizePrefix = `label_${labelSize}_`;
        const settings = {};
        
        // Get size-specific settings
        for (const [key, value] of Object.entries(systemParams)) {
            if (key.startsWith(sizePrefix) && !key.includes('_r90_')) {
                const settingName = key.replace(sizePrefix, '');
                settings[settingName] = value;
            }
        }
        
        // Fallback to default label_ settings if no size-specific ones exist
        if (Object.keys(settings).length === 0) {
            for (const [key, value] of Object.entries(systemParams)) {
                if (key.startsWith('label_') && !key.includes('_r90_') && !key.match(/label_\d/)) {
                    const settingName = key.replace('label_', '');
                    settings[settingName] = value;
                }
            }
        }
        
        // Parse settings with defaults
        const titleFontSize = parseInt(settings.title_font_size) || 14;
        const bodyFontSize = parseInt(settings.font_size) || 10;
        const borderStyle = settings.border_style || 'simple';
        const includeQr = settings.include_qr_code === 'true' || settings.include_qr_code === true;
        const qrSize = settings.qr_size || 'medium';
        const qrPosition = settings.qr_position || 'right';
        const includeLogo = settings.include_logo === 'true' || settings.include_logo === true;
        const logoPosition = settings.logo_position || 'top-left';
        const qrPrefix = settings.qr_code_prefix || systemParams.label_qr_code_prefix || '';
        
        // Create canvas for preview
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        
        // Set canvas size based on label type
        let width, height;
        const sizes = {
            // B1 sizes
            '60x30mm': [Math.round(60 * 203 / 25.4), Math.round(30 * 203 / 25.4)],
            '40x24mm': [Math.round(40 * 203 / 25.4), Math.round(24 * 203 / 25.4)],
            '40x20mm': [Math.round(40 * 203 / 25.4), Math.round(20 * 203 / 25.4)],
            '30x15mm': [Math.round(30 * 203 / 25.4), Math.round(15 * 203 / 25.4)],
            '30x12mm': [Math.round(30 * 203 / 25.4), Math.round(12 * 203 / 25.4)],
            // D110 sizes
            '75x12mm': [Math.round(75 * 203 / 25.4), Math.round(12 * 203 / 25.4)],
            '50x14mm': [Math.round(50 * 203 / 25.4), Math.round(14 * 203 / 25.4)],
            '40x12mm': [Math.round(40 * 203 / 25.4), Math.round(12 * 203 / 25.4)],
        };
        [width, height] = sizes[labelSize] || [384, 237];
        
        // If rotated, swap width and height
        if (rotation === 90) {
            [width, height] = [height, width];
        }
        
        canvas.width = width;
        canvas.height = height;
        
        // White background
        ctx.fillStyle = 'white';
        ctx.fillRect(0, 0, width, height);
        
        // Draw border
        ctx.strokeStyle = 'black';
        const margin = 10;
        if (borderStyle === 'simple') {
            ctx.lineWidth = 1;
            ctx.strokeRect(margin, margin, width - margin * 2, height - margin * 2);
        } else if (borderStyle === 'thick') {
            ctx.lineWidth = 3;
            ctx.strokeRect(margin, margin, width - margin * 2, height - margin * 2);
        } else if (borderStyle === 'double') {
            ctx.lineWidth = 1;
            ctx.strokeRect(margin, margin, width - margin * 2, height - margin * 2);
            ctx.strokeRect(margin + 3, margin + 3, width - (margin + 3) * 2, height - (margin + 3) * 2);
        } else if (borderStyle === 'rounded') {
            const radius = 5;
            ctx.lineWidth = 1;
            ctx.beginPath();
            ctx.moveTo(margin + radius, margin);
            ctx.lineTo(width - margin - radius, margin);
            ctx.quadraticCurveTo(width - margin, margin, width - margin, margin + radius);
            ctx.lineTo(width - margin, height - margin - radius);
            ctx.quadraticCurveTo(width - margin, height - margin, width - margin - radius, height - margin);
            ctx.lineTo(margin + radius, height - margin);
            ctx.quadraticCurveTo(margin, height - margin, margin, height - margin - radius);
            ctx.lineTo(margin, margin + radius);
            ctx.quadraticCurveTo(margin, margin, margin + radius, margin);
            ctx.stroke();
        } else if (borderStyle === 'dashed') {
            ctx.lineWidth = 1;
            ctx.setLineDash([5, 3]);
            ctx.strokeRect(margin, margin, width - margin * 2, height - margin * 2);
            ctx.setLineDash([]);
        } else if (borderStyle === 'dotted') {
            ctx.lineWidth = 1;
            ctx.setLineDash([2, 2]);
            ctx.strokeRect(margin, margin, width - margin * 2, height - margin * 2);
            ctx.setLineDash([]);
        } else if (borderStyle === 'decorative') {
            ctx.lineWidth = 1;
            ctx.strokeRect(margin, margin, width - margin * 2, height - margin * 2);
            const cornerSize = 15;
            ctx.lineWidth = 2;
            // Corners
            ctx.beginPath();
            ctx.moveTo(margin, margin + cornerSize);
            ctx.lineTo(margin, margin);
            ctx.lineTo(margin + cornerSize, margin);
            ctx.stroke();
            ctx.beginPath();
            ctx.moveTo(width - margin - cornerSize, margin);
            ctx.lineTo(width - margin, margin);
            ctx.lineTo(width - margin, margin + cornerSize);
            ctx.stroke();
            ctx.beginPath();
            ctx.moveTo(width - margin, height - margin - cornerSize);
            ctx.lineTo(width - margin, height - margin);
            ctx.lineTo(width - margin - cornerSize, height - margin);
            ctx.stroke();
            ctx.beginPath();
            ctx.moveTo(margin + cornerSize, height - margin);
            ctx.lineTo(margin, height - margin);
            ctx.lineTo(margin, height - margin - cornerSize);
            ctx.stroke();
        } else if (borderStyle === 'shadow') {
            ctx.lineWidth = 1;
            ctx.strokeStyle = '#ccc';
            ctx.strokeRect(margin + 2, margin + 2, width - margin * 2, height - margin * 2);
            ctx.strokeStyle = '#999';
            ctx.strokeRect(margin + 1, margin + 1, width - margin * 2, height - margin * 2);
            ctx.strokeStyle = 'black';
            ctx.strokeRect(margin, margin, width - margin * 2, height - margin * 2);
        }
        
        // Helper function to wrap text
        function wrapText(context, text, x, y, maxWidth, lineHeight) {
            const words = text.split(' ');
            let line = '';
            let lines = [];
            
            for (let n = 0; n < words.length; n++) {
                const testLine = line + words[n] + ' ';
                const metrics = context.measureText(testLine);
                const testWidth = metrics.width;
                
                if (testWidth > maxWidth && n > 0) {
                    lines.push(line);
                    line = words[n] + ' ';
                } else {
                    line = testLine;
                }
            }
            lines.push(line);
            
            for (let i = 0; i < lines.length; i++) {
                context.fillText(lines[i], x, y + (i * lineHeight));
            }
            
            return lines.length * lineHeight;
        }
        
        // Calculate QR and logo positions
        let textMaxWidth = width - (margin * 2) - 10;
        let textStartX = margin + 5;
        let textStartY = margin + 5;
        let qrX = 0, qrY = 0, qrPixels = 0;
        let logoX = 0, logoY = 0, logoPixels = 0;
        
        // Pre-calculate QR position
        if (includeQr) {
            const qrSizes = { 'small': 50, 'medium': 70, 'large': 90 };
            qrPixels = Math.min(qrSizes[qrSize] || 70, Math.min(height * 0.5, width * 0.3));
            
            switch(qrPosition) {
                case 'left':
                    qrX = margin + 5;
                    qrY = margin + ((height - margin * 2 - qrPixels) / 2);
                    break;
                case 'top-left':
                    qrX = margin + 5;
                    qrY = margin + 5;
                    break;
                case 'top-right':
                    qrX = width - qrPixels - margin - 5;
                    qrY = margin + 5;
                    break;
                case 'bottom-right':
                    qrX = width - qrPixels - margin - 5;
                    qrY = height - qrPixels - margin - 5;
                    break;
                case 'bottom-left':
                    qrX = margin + 5;
                    qrY = height - qrPixels - margin - 5;
                    break;
                case 'right':
                default:
                    qrX = width - qrPixels - margin - 5;
                    qrY = margin + ((height - margin * 2 - qrPixels) / 2);
                    break;
            }
        }
        
        // Pre-calculate logo position
        if (includeLogo) {
            logoPixels = Math.min(60, Math.min(height * 0.3, width * 0.2));
            
            switch(logoPosition) {
                case 'top-left':
                    logoX = margin + 5;
                    logoY = margin + 5;
                    break;
                case 'top-right':
                    logoX = width - logoPixels - margin - 5;
                    logoY = margin + 5;
                    break;
                case 'left':
                    logoX = margin + 5;
                    logoY = margin + ((height - margin * 2 - logoPixels) / 2);
                    break;
                case 'bottom-left':
                default:
                    logoX = margin + 5;
                    logoY = height - logoPixels - margin - 5;
                    break;
            }
        }
        
        // Adjust text area for overlapping elements
        const textAreaTop = margin + 5;
        const textAreaBottom = height - margin - 30;
        const textAreaLeft = margin + 5;
        const textAreaRight = width - margin - 5;
        
        if (includeQr) {
            const qrRight = qrX + qrPixels;
            const qrBottom = qrY + qrPixels;
            
            if (qrX < textAreaLeft + 50 && qrY < textAreaBottom && qrBottom > textAreaTop) {
                textStartX = Math.max(textStartX, qrRight + 10);
                textMaxWidth = width - textStartX - margin - 5;
            }
            
            if (qrRight > textAreaRight - 50 && qrY < textAreaBottom && qrBottom > textAreaTop) {
                textMaxWidth = qrX - textStartX - 10;
            }
        }
        
        if (includeLogo) {
            const logoRight = logoX + logoPixels;
            const logoBottom = logoY + logoPixels;
            
            if (logoX < textAreaLeft + 50 && logoY < textAreaBottom && logoBottom > textAreaTop) {
                const logoEnd = logoRight + 10;
                if (logoEnd > textStartX) {
                    textStartX = logoEnd;
                    textMaxWidth = width - textStartX - margin - 5;
                    
                    if (includeQr) {
                        const qrRight = qrX + qrPixels;
                        if (qrRight > textAreaRight - 50) {
                            textMaxWidth = qrX - textStartX - 10;
                        }
                    }
                }
            }
            
            if (logoRight > textAreaRight - 50 && logoY < textAreaBottom && logoBottom > textAreaTop) {
                textMaxWidth = Math.min(textMaxWidth, logoX - textStartX - 10);
            }
        }
        
        // Draw text content with real entry data
        ctx.fillStyle = 'black';
        ctx.font = `bold ${titleFontSize}px Arial`;
        let currentY = textStartY + titleFontSize;
        
        // Title from entry
        const title = entryData?.title || 'Sample Product Title';
        const titleHeight = wrapText(ctx, title, textStartX, currentY, textMaxWidth, titleFontSize + 4);
        currentY += titleHeight + 5;
        
        // Entry type and ID
        ctx.font = `${bodyFontSize}px Arial`;
        ctx.fillStyle = '#555';
        const entryType = entryData?.entry_type_label || 'Product';
        const entryId = entryData?.id || '123';
        const status = entryData?.status || 'Unknown';
        const entryInfo = `${entryType} #${entryId}\nStatus: ${status}`;
        const entryHeight = wrapText(ctx, entryInfo, textStartX, currentY, textMaxWidth, bodyFontSize + 4);
        currentY += entryHeight + 3;
        
        // Description (truncated to fit)
        ctx.fillStyle = '#666';
        const description = entryData?.description || 'Sample description text that wraps properly';
        const descHeight = wrapText(ctx, description, textStartX, currentY, textMaxWidth, bodyFontSize + 4);
        
        // Draw logo placeholder
        if (includeLogo) {
            ctx.fillStyle = '#e8f5e9';
            ctx.fillRect(logoX, logoY, logoPixels, logoPixels);
            ctx.strokeStyle = '#4caf50';
            ctx.lineWidth = 2;
            ctx.strokeRect(logoX, logoY, logoPixels, logoPixels);
            ctx.fillStyle = '#4caf50';
            ctx.font = 'bold 10px Arial';
            ctx.textAlign = 'center';
            ctx.fillText('LOGO', logoX + logoPixels/2, logoY + logoPixels/2);
            ctx.textAlign = 'left';
        }
        
        
        // Draw QR code (load from backend API)
        if (includeQr && entryData?.id) {
            try {
                console.log('Loading QR code from backend for entry:', entryData.id);
                
                // Load QR code image from backend
                const qrImageUrl = `/api/qr_code/${entryData.id}?size=${qrPixels}`;
                const qrImage = new Image();
                
                await new Promise((resolve, reject) => {
                    qrImage.onload = resolve;
                    qrImage.onerror = reject;
                    qrImage.src = qrImageUrl;
                });
                
                ctx.drawImage(qrImage, qrX, qrY, qrPixels, qrPixels);
                console.log('QR code drawn successfully at', qrX, qrY, qrPixels);
            } catch (error) {
                console.error('Error loading QR code:', error);
                // Fallback to placeholder
                ctx.fillStyle = '#ddd';
                ctx.fillRect(qrX, qrY, qrPixels, qrPixels);
                ctx.strokeStyle = '#999';
                ctx.strokeRect(qrX, qrY, qrPixels, qrPixels);
                ctx.fillStyle = '#666';
                ctx.font = '10px Arial';
                ctx.textAlign = 'center';
                ctx.fillText('QR', qrX + qrPixels/2, qrY + qrPixels/2);
                ctx.textAlign = 'left';
            }
        } else if (includeQr) {
            // No entry data - show placeholder
            console.log('Showing QR placeholder - No entry data');
            ctx.fillStyle = '#ddd';
            ctx.fillRect(qrX, qrY, qrPixels, qrPixels);
            ctx.strokeStyle = '#999';
            ctx.strokeRect(qrX, qrY, qrPixels, qrPixels);
            ctx.fillStyle = '#666';
            ctx.font = '10px Arial';
            ctx.textAlign = 'center';
            ctx.fillText('QR', qrX + qrPixels/2, qrY + qrPixels/2);
            ctx.textAlign = 'left';
        }
        
                // Draw date at bottom - use entry dates
        ctx.fillStyle = '#888';
        ctx.font = `${bodyFontSize}px Arial`;
        let dateX = margin + 5;
        let dateY = height - margin - 5;
        
        // Get date from entry (prefer intended_end_date, then actual_end_date, then created_at)
        let dateText = '2025-10-24';
        if (entryData?.intended_end_date) {
            dateText = entryData.intended_end_date.split('T')[0];
        } else if (entryData?.actual_end_date) {
            dateText = entryData.actual_end_date.split('T')[0];
        } else if (entryData?.created_at) {
            dateText = entryData.created_at.split('T')[0];
        }
        
        const dateWidth = ctx.measureText(dateText).width;
        
        // Avoid overlapping with logo/QR at bottom
        const dateBounds = { left: dateX, right: dateX + dateWidth, top: dateY - bodyFontSize, bottom: dateY };
        
        if (includeLogo) {
            const logoBounds = { left: logoX, right: logoX + logoPixels, top: logoY, bottom: logoY + logoPixels };
            if (!(dateBounds.right < logoBounds.left || dateBounds.left > logoBounds.right ||
                  dateBounds.bottom < logoBounds.top || dateBounds.top > logoBounds.bottom)) {
                if (logoPosition === 'bottom-left') {
                    dateX = logoX + logoPixels + 5;
                }
            }
        }
        
        if (includeQr) {
            const qrBounds = { left: qrX, right: qrX + qrPixels, top: qrY, bottom: qrY + qrPixels };
            dateBounds.left = dateX;
            dateBounds.right = dateX + dateWidth;
            if (!(dateBounds.right < qrBounds.left || dateBounds.left > qrBounds.right ||
                  dateBounds.bottom < qrBounds.top || dateBounds.top > qrBounds.bottom)) {
                if (qrPosition === 'bottom-left') {
                    dateX = qrX + qrPixels + 5;
                } else if (qrPosition === 'bottom-right') {
                    dateX = qrX - dateWidth - 5;
                }
            }
        }
        
        ctx.fillText(dateText, dateX, dateY);
        
        // Display canvas
        labelPreviewContainer.innerHTML = '';
        const maxWidth = 500;
        const maxHeight = 400;
        
        if (width > maxWidth || height > maxHeight) {
            const scale = Math.min(maxWidth / width, maxHeight / height);
            canvas.style.width = Math.round(width * scale) + 'px';
            canvas.style.height = Math.round(height * scale) + 'px';
        }
        
        labelPreviewContainer.appendChild(canvas);
        
        console.log(`Canvas preview rendered: ${borderStyle} border, QR: ${includeQr ? qrPosition : 'none'}, Logo: ${includeLogo ? logoPosition : 'none'}`);
    }
    
    // Add event listener for label type changes to auto-preview
    labelTypeSelect.addEventListener('change', () => {
        updateLabelPositions();
        // Auto-preview after a short delay to let UI update
        setTimeout(autoPreviewLabel, 100);
    });
    
    // Initialize label positions on page load
    updateLabelPositions();
    
    // Auto-load preview after a short delay to ensure entry data is loaded
    setTimeout(autoPreviewLabel, 200);
    
    console.log('Label printing initialized successfully');
});
