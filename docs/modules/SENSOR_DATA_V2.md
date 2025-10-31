# Sensor Data Module (Entry v2)

## Overview

The Sensor Data module provides comprehensive IoT sensor data management for Entry v2, including real-time visualization, CRUD operations, time-series analysis, and device integration.

## Architecture

### Component Structure

```
Sensor Data Module
├── Templates
│   ├── _sensors_section.html      # Main UI section
│   └── _sensors_modals.html        # CRUD modals
├── Static Assets
│   ├── css/sections/sensors.css    # Section styling
│   ├── js/sections/
│   │   ├── _sensors_functions.js   # Core logic (~780 lines)
│   │   └── sensors_init.js         # Bootstrap script
├── Backend
│   ├── api/shared_sensor_api.py    # REST endpoints
│   └── services/shared_sensor_service.py  # Business logic
└── Database
    ├── SharedSensorData            # Main sensor table
    ├── SensorDataEntryLinks        # Entry associations
    └── SensorDataEntryRanges       # Range-based data
```

### Design Patterns

- **Modular Sections**: Self-contained UI component included in Entry v2
- **Service Layer**: Business logic separated from API controllers
- **Static Assets**: JavaScript and CSS served from static directory (no inline Jinja)
- **REST API**: Standard HTTP methods for CRUD operations
- **Responsive Design**: Bootstrap 5 with mobile-first approach

## Features

### 1. Data Visualization

#### Chart.js Integration
- **Multi-series line charts** for different sensor types
- **Time-series support** with date-fns adapter
- **Interactive tooltips** showing precise values
- **Zoom capability** on X-axis for detailed analysis
- **Responsive canvas** adapts to screen size

#### Statistics Panel
- **Current reading**: Latest value for quick reference
- **Average**: Mean value over selected time range
- **Maximum**: Peak reading
- **Minimum**: Lowest reading
- **Color-coded cards**: Visual differentiation

### 2. Data Management

#### CRUD Operations
- **Create**: Add sensor readings manually or from devices
- **Read**: View readings in chart/table format
- **Update**: Edit existing readings (value, timestamp, metadata)
- **Delete**: Remove erroneous readings with confirmation

#### Filtering & Time Ranges
- **Sensor Type**: Filter by specific sensor (Temperature, Humidity, etc.)
- **Preset Ranges**: 24h, 7d, 30d, 90d
- **Custom Range**: Pick start/end dates
- **Real-time Updates**: Auto-refresh at configurable intervals

### 3. Device Integration

#### Source Tracking
- **Device ID**: Hardware sensor identifiers
- **Source Type**: manual, device, api, stream
- **Metadata**: JSON field for custom attributes
- **Device List**: Summary of all data sources

### 4. User Interface

#### Layout
- **Card-based design**: Bootstrap theme integration
- **Collapsible sections**: Device info, table view
- **Modal dialogs**: Non-intrusive CRUD forms
- **Responsive grid**: Mobile and desktop optimized

#### Controls
- **Dropdown selectors**: Sensor type and time range
- **Action buttons**: Add, refresh, configure, export
- **Pagination**: Table navigation for large datasets
- **Toggle views**: Chart vs. table display

## API Reference

### Base URL
```
/api
```

### Endpoints

#### 1. Get Sensor Data for Entry
```http
GET /api/entry/<entry_id>/sensor-data
```

**Query Parameters:**
- `sensor_type` (optional): Filter by sensor type (e.g., "Temperature")
- `start_date` (optional): ISO 8601 datetime string
- `end_date` (optional): ISO 8601 datetime string
- `limit` (optional): Maximum readings to return
- `include_stats` (optional): Include statistics (true/false)

**Response:**
```json
{
  "readings": [
    {
      "id": 123,
      "sensor_type": "Temperature",
      "value": 22.5,
      "unit": "°C",
      "recorded_at": "2025-10-31T10:30:00Z",
      "source_type": "device",
      "source_id": "sensor_01",
      "metadata": {"location": "Room A"}
    }
  ],
  "statistics": {
    "Temperature": {
      "count": 48,
      "current": 22.5,
      "average": 21.8,
      "min": 19.2,
      "max": 24.1,
      "range": 4.9
    }
  }
}
```

#### 2. Get Available Sensor Types
```http
GET /api/entry/<entry_id>/sensor-types
```

**Response:**
```json
{
  "sensor_types": ["Temperature", "Humidity", "Pressure", "pH", "Light", "CO2"],
  "enabled_types": ["Temperature", "Humidity"],
  "active_types": ["Temperature"]
}
```

#### 3. Create Sensor Reading
```http
POST /api/shared_sensor_data
```

**Request Body:**
```json
{
  "sensor_type": "Temperature",
  "value": 22.5,
  "unit": "°C",
  "entry_ids": [1, 2],
  "recorded_at": "2025-10-31T10:30:00Z",
  "source_type": "device",
  "source_id": "sensor_01",
  "metadata": {"notes": "Manual reading"}
}
```

**Response:**
```json
{
  "id": 123,
  "message": "Sensor data created successfully"
}
```

#### 4. Update Sensor Reading
```http
PUT /api/shared_sensor_data/<sensor_id>
```

**Request Body:**
```json
{
  "value": 23.0,
  "unit": "°C",
  "recorded_at": "2025-10-31T10:35:00Z",
  "metadata": {"notes": "Corrected value"}
}
```

**Response:**
```json
{
  "message": "Sensor data updated successfully"
}
```

#### 5. Delete Sensor Reading
```http
DELETE /api/shared_sensor_data/<sensor_id>
```

**Response:**
```json
{
  "message": "Sensor data deleted successfully"
}
```

## Service Layer

### SharedSensorDataService

#### Methods

##### format_readings_for_chart(readings: List[Dict]) -> Dict
Formats sensor readings into Chart.js-compatible datasets.

**Input:**
```python
readings = [
    {"sensor_type": "Temperature", "value": 22.5, "recorded_at": "2025-10-31T10:00:00Z"},
    {"sensor_type": "Temperature", "value": 23.0, "recorded_at": "2025-10-31T11:00:00Z"}
]
```

**Output:**
```python
{
    "Temperature": {
        "label": "Temperature",
        "data": [
            {"x": "2025-10-31T10:00:00Z", "y": 22.5},
            {"x": "2025-10-31T11:00:00Z", "y": 23.0}
        ]
    }
}
```

##### aggregate_statistics(readings: List[Dict]) -> Dict
Calculates statistics across all readings and per sensor type.

**Output:**
```python
{
    "overall": {"count": 100, "average": 22.3, "min": 18.5, "max": 26.1},
    "Temperature": {"count": 50, "average": 22.5, "min": 19.0, "max": 25.0},
    "Humidity": {"count": 50, "average": 55.2, "min": 45.0, "max": 65.0}
}
```

## Frontend Integration

### Initialization

The sensor section auto-initializes on page load via `sensors_init.js`:

```javascript
document.addEventListener('DOMContentLoaded', function() {
    const sectionDiv = document.querySelector('[data-entry-id]');
    if (sectionDiv) {
        window.currentEntryId = sectionDiv.dataset.entryId;
        initializeSensorSection();
    }
});
```

### Key Functions

#### initializeSensorSection()
Bootstraps the entire sensor section:
1. Loads sensor types for the entry type
2. Fetches initial sensor data
3. Sets up form handlers
4. Configures auto-refresh

#### loadSensorData()
Fetches sensor data from API with current filters:
- Builds query parameters
- Updates chart, table, stats, and device list
- Handles loading states and errors

#### updateChart()
Renders Chart.js visualization:
- Groups data by sensor type
- Applies consistent colors
- Configures time axis
- Enables zoom interaction

### Event Handlers

All event handlers are automatically wired in `wireUpControls()`:
- Sensor type selector change
- Time range selector change
- Custom date inputs
- Refresh button
- Table toggle button
- Auto-refresh checkbox

### Global Exposure

Key functions are exposed to window scope for template access:
```javascript
window.initializeSensorSection
window.refreshSensorData
window.editSensorReading
window.deleteSensorReadingConfirm
window.changePage
window.toggleDataTable
window.showNotification
```

## Customization

### Adding New Sensor Types

1. **Register Type** (if using automatic registration):
   ```python
   # In migrations or utils
   register_sensor_type("CO2", "ppm", "Air quality")
   ```

2. **Update Color Mapping** (optional):
   ```javascript
   // In _sensors_functions.js
   function getColorForSensorType(type, alpha = 1) {
       const colors = {
           'CO2': `rgba(100, 200, 100, ${alpha})`,
           // ... other types
       };
       return colors[type] || default_color;
   }
   ```

### Custom Styling

Override styles in your theme or add to `sensors.css`:

```css
/* Custom stat card colors */
.sensor-stat-card.temperature {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

/* Chart container sizing */
#chartContainer {
    min-height: 300px;
    max-height: 600px;
}
```

### Auto-Refresh Configuration

Set defaults in the configure modal or via JavaScript:

```javascript
// In sensors_init.js or custom script
window.addEventListener('DOMContentLoaded', function() {
    document.getElementById('autoRefresh').checked = true;
    document.getElementById('autoRefreshInterval').value = 30; // seconds
    checkAutoRefresh();
});
```

## Troubleshooting

### Chart Not Rendering

**Symptoms:** Empty chart area, no error messages

**Causes & Solutions:**
1. **Missing Chart.js**: Ensure CDN is loaded in template
   ```html
   <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
   <script src="https://cdn.jsdelivr.net/npm/chartjs-adapter-date-fns/..."></script>
   ```

2. **No data available**: Check API response in browser console
   ```javascript
   // Open DevTools → Network → Filter by "sensor-data"
   ```

3. **Canvas not found**: Verify template includes `<canvas id="sensorChart"></canvas>`

### API Errors

**Symptoms:** 404, 500, or network errors in console

**Causes & Solutions:**
1. **Blueprint not registered**: Check `app/__init__.py`
   ```python
   from app.api.shared_sensor_api import shared_sensor_api_bp
   app.register_blueprint(shared_sensor_api_bp, url_prefix='/api')
   ```

2. **Entry ID undefined**: Verify `data-entry-id="{{ entry.id }}"` in template

3. **CORS issues** (if using separate frontend):
   ```python
   from flask_cors import CORS
   CORS(app, resources={r"/api/*": {"origins": "*"}})
   ```

### Data Not Updating

**Symptoms:** Stale data, changes not reflected

**Causes & Solutions:**
1. **Auto-refresh disabled**: Enable in configure modal
2. **Caching**: Hard refresh browser (Ctrl+Shift+R)
3. **Database not updated**: Check SQLite file permissions
4. **Service layer not called**: Verify API endpoints call service methods

### Modal Not Opening

**Symptoms:** Click "Add Data" but nothing happens

**Causes & Solutions:**
1. **Bootstrap JS not loaded**: Ensure Bootstrap bundle is included
   ```html
   <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
   ```

2. **Modal HTML missing**: Verify `{% include 'sections/_sensors_modals.html' %}`

3. **Conflicting event handlers**: Check for duplicate includes

### Mobile Display Issues

**Symptoms:** Layout broken on mobile devices

**Causes & Solutions:**
1. **Responsive CSS not loaded**: Check `sensors.css` is included
2. **Grid breakpoints**: Adjust Bootstrap column classes
   ```html
   <div class="col-md-6 col-12">  <!-- Stack on mobile -->
   ```

3. **Chart overflow**: Add max-width to chart container
   ```css
   #chartContainer { max-width: 100%; overflow-x: auto; }
   ```

## Testing

### Unit Tests

```python
# tests/test_sensor_service.py
def test_format_readings_for_chart():
    service = SharedSensorDataService()
    readings = [{"sensor_type": "Temperature", "value": 22.5, ...}]
    result = service.format_readings_for_chart(readings)
    assert "Temperature" in result
    assert len(result["Temperature"]["data"]) == 1
```

### Integration Tests

```python
# tests/test_sensor_api.py
def test_get_sensor_data(client):
    response = client.get('/api/entry/1/sensor-data')
    assert response.status_code == 200
    assert 'readings' in response.json
```

### E2E Tests

Run the provided test suite:
```bash
# Make sure server is running first
python run.py &

# Run E2E tests
python test_sensor_module_e2e.py
```

### Static Validation

```bash
python validate_sensor_module.py
```

## Performance Considerations

### Database Optimization

1. **Indexes**: Ensure indexes on frequently queried columns
   ```sql
   CREATE INDEX idx_sensor_entry ON SensorDataEntryLinks(entry_id, sensor_data_id);
   CREATE INDEX idx_sensor_recorded ON SharedSensorData(recorded_at);
   ```

2. **Limit results**: Use pagination and time range filters
   ```javascript
   // Default to last 7 days
   loadSensorData({ timeRange: '7d', limit: 1000 });
   ```

### Frontend Optimization

1. **Debounce updates**: Avoid excessive API calls
   ```javascript
   let updateTimeout;
   function onCustomDateChange() {
       clearTimeout(updateTimeout);
       updateTimeout = setTimeout(loadSensorData, 500);
   }
   ```

2. **Chart data limits**: Downsample for large datasets
   ```javascript
   if (readings.length > 1000) {
       readings = downsample(readings, 1000);
   }
   ```

3. **Lazy loading**: Load device list only when expanded

## Security

### Input Validation

All API endpoints validate input:
- Sensor type: whitelist of allowed types
- Value: numeric validation
- Timestamps: ISO 8601 format
- Entry IDs: integer validation

### Authorization

Implement entry-level access control:
```python
@shared_sensor_api_bp.route('/entry/<int:entry_id>/sensor-data')
def get_sensor_data(entry_id):
    # Verify user has access to this entry
    if not can_access_entry(current_user, entry_id):
        return jsonify({"error": "Unauthorized"}), 403
    # ... rest of endpoint
```

### SQL Injection Prevention

Use parameterized queries (SQLAlchemy ORM):
```python
# SAFE - parameterized
SharedSensorData.query.filter_by(entry_id=entry_id).all()

# UNSAFE - string concatenation (don't do this)
# db.execute(f"SELECT * FROM sensor WHERE entry_id={entry_id}")
```

## Future Enhancements

### Planned Features
- [ ] Real-time WebSocket streaming for live updates
- [ ] Advanced aggregation (hourly/daily rollups)
- [ ] Alert thresholds with notifications
- [ ] CSV/Excel export functionality
- [ ] Bulk import from CSV
- [ ] Sensor calibration tracking
- [ ] Data retention policies
- [ ] Historical comparison views

### API Improvements
- [ ] GraphQL endpoint for complex queries
- [ ] Rate limiting for API endpoints
- [ ] Caching layer (Redis) for frequent queries
- [ ] Batch operations endpoint

### UI Enhancements
- [ ] Draggable time range selector
- [ ] Multiple chart types (bar, scatter, heatmap)
- [ ] Dark mode color scheme
- [ ] Keyboard shortcuts
- [ ] Accessibility improvements (ARIA labels)

## Contributing

When contributing to the sensor module:

1. **Follow patterns**: Use existing service/API structure
2. **Test thoroughly**: Add unit + integration tests
3. **Document changes**: Update this doc + inline comments
4. **Validate static files**: Run validation script
5. **Check responsiveness**: Test on mobile + desktop

## License

Part of the main project - see LICENSE file in repository root.

## Support

For issues or questions:
- Check troubleshooting section above
- Review browser console for errors
- Inspect Network tab for API responses
- Check server logs for backend errors

---

**Version:** 1.0  
**Last Updated:** October 31, 2025  
**Module Status:** Production Ready ✅
