// Initialization for sensor section moved out of template
document.addEventListener('DOMContentLoaded', function() {
    // FIRST: Set currentEntryId from data attribute
    const sensorsSection = document.querySelector('[data-entry-id]');
    if (sensorsSection) {
        const id = sensorsSection.getAttribute('data-entry-id');
        if (id) {
            window.currentEntryId = parseInt(id, 10);
            console.log('Sensor section: Entry ID set to', window.currentEntryId);
        }
    }

    // THEN: Initialize the sensor section (requires currentEntryId)
    if (typeof initializeSensorSection === 'function' && window.currentEntryId) {
        initializeSensorSection();
    } else if (!window.currentEntryId) {
        console.error('Sensor section: Entry ID not found');
    }

    // Toggle device info icon
    const deviceCollapse = document.getElementById('deviceInfo');
    if (deviceCollapse) {
        deviceCollapse.addEventListener('show.bs.collapse', function () {
            const icon = document.getElementById('deviceInfoIcon');
            if (icon) icon.classList.replace('fa-chevron-right', 'fa-chevron-down');
        });
        deviceCollapse.addEventListener('hide.bs.collapse', function () {
            const icon = document.getElementById('deviceInfoIcon');
            if (icon) icon.classList.replace('fa-chevron-down', 'fa-chevron-right');
        });
    }
});
