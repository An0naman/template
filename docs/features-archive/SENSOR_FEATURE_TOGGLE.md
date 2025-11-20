# Sensor Feature Toggle Implementation

## Overview
Added a system-wide parameter to enable/disable sensor functionality throughout the application. When disabled, all sensor-related UI elements are hidden, providing a cleaner interface for projects that don't use sensor features.

## Implementation Details

### 1. Database Configuration

**File**: `app/db.py`

Added new system parameter `enable_sensors` with default value of `'1'` (enabled):

```python
'enable_sensors': '1',  # Global toggle for sensor functionality (1 = enabled, 0 = disabled)
```

This parameter is stored in the `SystemParameters` table and persists across application restarts.

### 2. API Endpoint

**File**: `app/api/system_params_api.py`

Added `enable_sensors` to the allowed parameters list, enabling it to be updated via the existing system parameters API:

```python
allowed_params = [
    'project_name', 'entry_singular_label', 'entry_plural_label', 'project_subtitle', 
    'enable_sensors', 'sensor_types', 
    # ... other parameters
]
```

**API Usage:**
- **Get sensor status**: `GET /api/system_params/enable_sensors`
- **Update sensor status**: `PATCH /api/system_params` with body `{"enable_sensors": "0"}` or `{"enable_sensors": "1"}`

### 3. Settings Page UI

**File**: `app/templates/maintenance_module.html`

#### Toggle Control
Added a user-friendly toggle switch in the System Configuration section:

```html
<div class="alert alert-info mb-3">
    <div class="d-flex justify-content-between align-items-center">
        <div>
            <h6 class="mb-1"><i class="fas fa-thermometer-half me-2"></i>Sensor Functionality</h6>
            <small>Enable or disable sensor features across the entire application.</small>
        </div>
        <div class="form-check form-switch ms-3">
            <input class="form-check-input" type="checkbox" role="switch" id="enableSensorsToggle">
            <label class="form-check-label ms-2" for="enableSensorsToggle">Loading...</label>
        </div>
    </div>
</div>
```

#### JavaScript Functionality
- Loads current toggle state on page load
- Updates the state via API when toggle is changed
- Shows/hides the "Sensor & Monitoring" section dynamically
- Displays success notification when setting is changed
- Prompts user to refresh page for changes to take effect throughout the app

#### Sensor Section Visibility
The "Sensor & Monitoring" settings section is now hidden by default and only shown when sensors are enabled:

```html
<section class="mb-4 sensor-section" style="display: none;">
```

### 4. Entry Page Integration

**File**: `app/templates/entry_detail_v2.html`

Conditionally renders sensor sections only when the feature is enabled:

```jinja2
{% elif section_type == 'sensors' %}
    {% if get_system_parameters().get('enable_sensors', '1') == '1' %}
        {% with section_id=section.id %}{% include 'sections/_sensors_section.html' %}{% endwith %}
    {% endif %}
```

This applies to both:
- Custom layout sections (grid-based layout)
- Default fallback sections (tab-based layout)

### 5. Entry Type Management

**File**: `app/templates/manage_entry_types.html`

#### Table Column
Conditionally displays the "Sensors" column in the entry types table:

```jinja2
{% if get_system_parameters().get('enable_sensors', '1') == '1' %}
<th class="text-center">Sensors</th>
{% endif %}
```

#### Modal Configuration
Hides sensor-related configuration options in the entry type modal:

```jinja2
{% if get_system_parameters().get('enable_sensors', '1') == '1' %}
<div class="form-check mb-3">
    <input class="form-check-input" type="checkbox" id="hasSensors">
    <label class="form-check-label" for="hasSensors">
        <strong>Enable Sensors</strong>
    </label>
</div>
{% endif %}

<!-- Sensor Types Section -->
{% if get_system_parameters().get('enable_sensors', '1') == '1' %}
<div class="mb-4" id="sensorTypesSection">
    <!-- Sensor configuration UI -->
</div>
{% endif %}
```

### 6. Dashboard Integration

**File**: `app/templates/dashboard.html`

#### Widget Type Selection
Hides the "Line Chart (Sensor Data)" option when sensors are disabled:

```jinja2
<select class="form-select" id="widgetType" required>
    <option value="">Select widget type...</option>
    <option value="list">Entry List</option>
    <option value="pie_chart">Pie Chart (States)</option>
    {% if get_system_parameters().get('enable_sensors', '1') == '1' %}
    <option value="line_chart">Line Chart (Sensor Data)</option>
    {% endif %}
    <option value="stat_card">Stat Card</option>
    <option value="ai_summary">AI Summary</option>
</select>
```

#### Sensor Data Configuration
Conditionally renders sensor-specific widget configuration:

```jinja2
{% if get_system_parameters().get('enable_sensors', '1') == '1' %}
<div id="sensorDataConfig" style="display: none;">
    <!-- Sensor type and time range selectors -->
</div>
{% endif %}
```

## Usage

### Disabling Sensors

1. Navigate to the Settings page (Maintenance Module)
2. In the System Configuration section, locate the "Sensor Functionality" toggle
3. Click the toggle to disable sensors
4. The page will show a success message
5. Refresh the page to see the "Sensor & Monitoring" section disappear
6. Navigate throughout the app - all sensor-related elements will be hidden

### Enabling Sensors

1. Navigate to the Settings page (Maintenance Module)
2. Click the toggle to enable sensors
3. Refresh the page
4. The "Sensor & Monitoring" section will be visible
5. Sensor options will appear in entry types, entries, and dashboards

## Benefits

1. **Cleaner UI**: Projects that don't use sensors won't see unnecessary UI elements
2. **Reduced Complexity**: Simplifies the interface for users who don't need sensor features
3. **Easy Toggle**: One-click enable/disable from the settings page
4. **Persistent**: Setting is saved to the database and persists across sessions
5. **Comprehensive**: Affects all sensor-related UI throughout the application:
   - Entry detail pages
   - Entry type management
   - Dashboard widgets
   - Settings/maintenance pages

## Technical Notes

- The parameter uses string values `'0'` and `'1'` to maintain consistency with other system parameters stored as text
- Default value is `'1'` (enabled) to maintain backward compatibility with existing installations
- All template checks use `get_system_parameters().get('enable_sensors', '1') == '1'` to safely handle missing values
- The toggle state is loaded asynchronously in JavaScript to avoid page load delays
- Changes take effect immediately for new page loads; existing pages require refresh

## Files Modified

1. `app/db.py` - Added default parameter
2. `app/api/system_params_api.py` - Added to allowed parameters
3. `app/templates/maintenance_module.html` - Added UI toggle and JavaScript
4. `app/templates/entry_detail_v2.html` - Conditional sensor section rendering
5. `app/templates/manage_entry_types.html` - Conditional sensor configuration
6. `app/templates/dashboard.html` - Conditional sensor widget options

## Future Enhancements

Possible improvements for future versions:
- Add confirmation dialog when disabling sensors if sensor data exists
- Provide migration tool to bulk disable sensors on all entry types
- Add analytics on sensor usage to help decide if feature should be disabled
- Extend to other optional features (labels, relationships, etc.)
