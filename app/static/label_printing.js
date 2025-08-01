// Label Printing JavaScript
document.addEventListener('DOMContentLoaded', function() {
    const labelTypeSelect = document.getElementById('labelTypeSelect');
    const labelPositionSelect = document.getElementById('labelPositionSelect');
    const previewLabelBtn = document.getElementById('previewLabelBtn');
    const printLabelBtn = document.getElementById('printLabelBtn');
    const downloadLabelPdfBtn = document.getElementById('downloadLabelPdfBtn');
    const labelPreviewContainer = document.getElementById('labelPreviewContainer');
    const labelStatusMessage = document.getElementById('labelStatusMessage');

    // Check if all elements exist
    if (!labelTypeSelect || !labelPositionSelect || !previewLabelBtn || !printLabelBtn || !downloadLabelPdfBtn) {
        console.log('Label printing elements not found on this page');
        return;
    }

    // Get entry ID from the URL or a data attribute
    const entryId = window.location.pathname.split('/').pop();

    // Initialize label position options based on selected type
    function updateLabelPositions() {
        const labelType = labelTypeSelect.value;
        const maxPositions = labelType === '8_labels' ? 8 : 14;
        
        labelPositionSelect.innerHTML = '';
        for (let i = 1; i <= maxPositions; i++) {
            const option = document.createElement('option');
            option.value = i;
            option.textContent = `Position ${i}`;
            labelPositionSelect.appendChild(option);
        }
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
            
            const response = await fetch(`/api/entries/${entryId}/label_preview?label_type=${labelTypeSelect.value}`);
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
        try {
            displayLabelStatus('Generating print page...', 'alert-info');
            
            const response = await fetch(`/api/entries/${entryId}/print_label`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    label_type: labelTypeSelect.value,
                    position: parseInt(labelPositionSelect.value)
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
        try {
            displayLabelStatus('Generating PDF...', 'alert-info');
            
            const response = await fetch(`/api/entries/${entryId}/label_pdf`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    label_type: labelTypeSelect.value,
                    position: parseInt(labelPositionSelect.value)
                })
            });
            
            if (!response.ok) throw new Error('Failed to generate PDF');
            
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            a.download = `entry-${entryId}-label.pdf`;
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
