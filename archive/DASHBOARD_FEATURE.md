# Configurable Dashboard Feature

## Overview

The Dashboard feature provides a powerful, customizable analytics interface for visualizing and analyzing your project data. It supports multiple dashboard configurations, drag-and-drop widget placement, and various visualization types including charts, lists, and AI-powered insights.

## Features

### 🎯 Core Capabilities

1. **Multiple Dashboards**
   - Create unlimited dashboards
   - Set default dashboard
   - Switch between dashboards easily
   - Each dashboard has independent layout

2. **Widget Types**
   - **Entry Lists**: Display entries from saved searches
   - **Pie Charts**: Visualize entry state distribution
   - **Line Charts**: Plot sensor data trends over time
   - **Stat Cards**: Show single metric values
   - **AI Summaries**: Generate AI-powered insights

3. **Drag-and-Drop Layout**
   - Drag widgets to reposition
   - Resize widgets to fit your needs
   - 12-column responsive grid
   - Auto-save layout changes

4. **Data Sources**
   - **Saved Searches**: Use your existing saved searches as data sources
   - **Entry States**: Aggregate state information across entry types
   - **Sensor Data**: Real-time and historical sensor readings
   - **AI Analysis**: Contextual insights from Google Gemini

5. **Customization**
   - Widget titles and sizes
   - Refresh intervals
   - Color schemes (via theme system)
   - Flexible grid layouts

## Architecture

### Database Schema

#### Dashboard Table
```sql
CREATE TABLE Dashboard (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    is_default INTEGER DEFAULT 0,
    layout_config TEXT DEFAULT '{"cols": 12, "rowHeight": 100}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### DashboardWidget Table
```sql
CREATE TABLE DashboardWidget (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dashboard_id INTEGER NOT NULL,
    widget_type TEXT NOT NULL,
    title TEXT NOT NULL,
    position_x INTEGER DEFAULT 0,
    position_y INTEGER DEFAULT 0,
    width INTEGER DEFAULT 4,
    height INTEGER DEFAULT 2,
    config TEXT DEFAULT '{}',
    data_source_type TEXT,
    data_source_id INTEGER,
    refresh_interval INTEGER DEFAULT 300,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (dashboard_id) REFERENCES Dashboard(id) ON DELETE CASCADE
);
```

### Backend Components

1. **DashboardService** (`app/services/dashboard_service.py`)
   - Aggregates data from various sources
   - Handles data transformation for widgets
   - Generates AI summaries
   - Optimizes queries for performance

2. **Dashboard API** (`app/api/dashboard_api.py`)
   - RESTful endpoints for dashboard management
   - Widget CRUD operations
   - Data retrieval endpoints
   - Source discovery

3. **Routes** (`app/routes/main_routes.py`)
   - `/dashboard` - Main dashboard page

### Frontend Components

1. **Template** (`app/templates/dashboard.html`)
   - Responsive Bootstrap 5 layout
   - Gridstack.js integration
   - Chart.js for visualizations
   - Modal dialogs for configuration

2. **JavaScript** (`app/static/js/dashboard.js`)
   - Dashboard state management
   - Widget rendering logic
   - Drag-and-drop functionality
   - API communication
   - Chart rendering

## Usage Guide

### Creating Your First Dashboard

1. **Navigate to Dashboard**
   - Click "Dashboard" in navigation or go to `/dashboard`

2. **Create Dashboard**
   ```
   1. Click "New Dashboard" button
   2. Enter dashboard name (e.g., "Production Overview")
   3. Add optional description
   4. Check "Set as default" if desired
   5. Click "Create Dashboard"
   ```

3. **Add Widgets**
   ```
   1. Click "+ Add Widget" button
   2. Select widget type:
      - List: Show entries from a saved search
      - Pie Chart: State distribution
      - Line Chart: Sensor trends
      - Stat Card: Single metric
      - AI Summary: Intelligent insights
   3. Configure widget:
      - Set title
      - Choose data source (saved search)
      - Set dimensions (width/height)
   4. Click "Add Widget"
   ```

4. **Arrange Layout**
   ```
   1. Click "Edit Layout" button
   2. Drag widgets to reposition
   3. Resize widgets by dragging corners
   4. Click "Save Layout" when done
   ```

### Widget Configuration

#### Entry List Widget
- **Purpose**: Display entries matching a saved search
- **Data Source**: Saved Search
- **Configuration**: Select saved search
- **Display**: Clickable list with entry details

#### Pie Chart Widget
- **Purpose**: Visualize state distribution
- **Data Source**: Saved Search or Entry Type
- **Configuration**: Select data source
- **Display**: Interactive pie chart with legend

#### Line Chart Widget
- **Purpose**: Track sensor data over time
- **Data Source**: Saved Search + Sensor Type
- **Configuration**: 
  - Select saved search (for entries)
  - Select sensor type
  - Choose time range (1d, 7d, 30d, 90d, all)
- **Display**: Time-series line chart

#### Stat Card Widget
- **Purpose**: Display single metric
- **Data Source**: Saved Search
- **Configuration**: Select saved search, set label
- **Display**: Large number with label

#### AI Summary Widget
- **Purpose**: Generate intelligent insights
- **Data Source**: Saved Search
- **Configuration**: Select saved search
- **Requirements**: Gemini API key configured
- **Display**: Formatted text summary

### Best Practices

1. **Dashboard Organization**
   - Create separate dashboards for different purposes
   - Use descriptive names (e.g., "Daily Operations", "Quality Metrics")
   - Set your most-used dashboard as default

2. **Widget Placement**
   - Put most important widgets at the top
   - Group related widgets together
   - Use larger sizes for complex visualizations
   - Keep stat cards compact (2x2 or 3x2)

3. **Data Sources**
   - Create saved searches before building dashboards
   - Use descriptive search names
   - Test searches before using in widgets

4. **Performance**
   - Limit number of widgets per dashboard (10-15 recommended)
   - Use appropriate time ranges for sensor charts
   - Set refresh intervals based on data update frequency

5. **AI Summaries**
   - Configure Gemini API key in system settings
   - Use for high-level overviews
   - Combine with specific metric widgets

## API Reference

### Dashboard Endpoints

#### List All Dashboards
```http
GET /api/dashboards
```
**Response:**
```json
[
  {
    "id": 1,
    "name": "Production Dashboard",
    "description": "Overview of production entries",
    "is_default": true,
    "layout_config": {"cols": 12, "rowHeight": 100},
    "created_at": "2025-10-12T10:00:00",
    "updated_at": "2025-10-12T12:00:00"
  }
]
```

#### Get Dashboard with Widgets
```http
GET /api/dashboards/:id
```
**Response:**
```json
{
  "id": 1,
  "name": "Production Dashboard",
  "description": "...",
  "is_default": true,
  "layout_config": {...},
  "widgets": [
    {
      "id": 1,
      "widget_type": "list",
      "title": "Active Projects",
      "position_x": 0,
      "position_y": 0,
      "width": 6,
      "height": 3,
      "config": {},
      "data_source_type": "saved_search",
      "data_source_id": 5,
      "refresh_interval": 300
    }
  ]
}
```

#### Create Dashboard
```http
POST /api/dashboards
Content-Type: application/json

{
  "name": "New Dashboard",
  "description": "Description",
  "is_default": false,
  "layout_config": {"cols": 12, "rowHeight": 100}
}
```

#### Update Dashboard
```http
PUT /api/dashboards/:id
Content-Type: application/json

{
  "name": "Updated Name",
  "description": "Updated description"
}
```

#### Delete Dashboard
```http
DELETE /api/dashboards/:id
```

#### Set Default Dashboard
```http
POST /api/dashboards/:id/set_default
```

### Widget Endpoints

#### Add Widget to Dashboard
```http
POST /api/dashboards/:id/widgets
Content-Type: application/json

{
  "widget_type": "pie_chart",
  "title": "Entry States",
  "position_x": 0,
  "position_y": 0,
  "width": 6,
  "height": 3,
  "config": {},
  "data_source_type": "saved_search",
  "data_source_id": 1,
  "refresh_interval": 300
}
```

#### Update Widget
```http
PUT /api/widgets/:id
Content-Type: application/json

{
  "position_x": 6,
  "position_y": 0,
  "width": 4,
  "height": 2
}
```

#### Delete Widget
```http
DELETE /api/widgets/:id
```

#### Get Widget Data
```http
GET /api/widgets/:id/data
```

#### Get All Dashboard Data
```http
GET /api/dashboards/:id/data
```

#### Get Available Data Sources
```http
GET /api/dashboard_sources
```
**Response:**
```json
{
  "saved_searches": [
    {"id": 1, "name": "Active Projects"}
  ],
  "entry_types": [
    {"id": 1, "label": "Projects"}
  ],
  "sensor_types": [
    "Temperature",
    "Humidity",
    "Pressure"
  ]
}
```

## Integration with Other Features

### Saved Searches
- Dashboards rely heavily on saved searches
- Create searches on main page first
- Use descriptive names for easier selection
- Searches can be reused across multiple widgets

### Entry States
- Pie charts visualize state distribution
- States are defined per entry type
- Colors from entry states carry to charts

### Sensor Data
- Line charts display sensor readings
- Supports both legacy and shared sensor data
- Automatic numeric value extraction
- Configurable time ranges

### AI Service
- AI Summary widgets use Gemini API
- Contextual analysis of entries, notes, and sensor data
- Configurable via system parameters
- Graceful fallback when unavailable

## Troubleshooting

### Dashboard Not Loading
1. Check browser console for errors
2. Verify database tables exist (run `python test_dashboard.py`)
3. Ensure Flask app is running
4. Clear browser cache

### Widgets Not Displaying Data
1. Verify saved search exists and has results
2. Check data source configuration
3. Look for API errors in browser console
4. Refresh widget manually

### AI Summary Not Working
1. Verify Gemini API key is configured
2. Check system parameters in settings
3. Ensure saved search has entries
4. Look for API errors in logs

### Layout Not Saving
1. Ensure you're in edit mode
2. Click "Save Layout" button
3. Check browser console for errors
4. Verify API connectivity

### Charts Not Rendering
1. Check that Chart.js is loaded
2. Verify data format is correct
3. Ensure canvas element exists
4. Check browser console for errors

## Performance Considerations

1. **Widget Count**: Limit to 10-15 widgets per dashboard
2. **Refresh Intervals**: Set appropriately (300s default)
3. **Time Ranges**: Use shorter ranges for sensor charts
4. **Data Volume**: Large saved searches may impact performance
5. **AI Summaries**: Can be slower, use sparingly

## Future Enhancements

- [ ] Widget templates and presets
- [ ] Dashboard sharing and permissions
- [ ] Export dashboard to PDF/image
- [ ] Real-time data streaming
- [ ] Custom widget development API
- [ ] Dashboard themes and styling
- [ ] Mobile-optimized layouts
- [ ] Scheduled dashboard reports

## Files Modified/Created

### New Files
- `app/services/dashboard_service.py` - Dashboard data service
- `app/api/dashboard_api.py` - Dashboard REST API
- `app/templates/dashboard.html` - Dashboard UI template
- `app/static/js/dashboard.js` - Dashboard JavaScript
- `test_dashboard.py` - Testing script
- `DASHBOARD_FEATURE.md` - This documentation

### Modified Files
- `app/db.py` - Added Dashboard and DashboardWidget tables
- `app/__init__.py` - Registered dashboard API blueprint
- `app/routes/main_routes.py` - Added dashboard route

## Testing

Run the test script to verify installation:

```bash
python test_dashboard.py
```

Expected output:
```
🚀 Dashboard Feature Test
======================================================================

✅ Testing Imports...
  ✓ DashboardService imported successfully
  ✓ Dashboard API imported successfully

✅ Testing Database Tables...
  ✓ Dashboard table exists
  ✓ DashboardWidget table exists

✅ Testing DashboardService...
  ✓ get_saved_search_entries method exists
  ✓ get_state_distribution method exists
  ✓ get_sensor_data_trends method exists
  ✓ generate_ai_summary method exists
  ✓ get_widget_data method exists

📊 Test Summary
======================================================================
  ✅ PASS: Imports
  ✅ PASS: Database Tables
  ✅ PASS: Dashboard Service
  ✅ PASS: API Endpoints
  ✅ PASS: Static Files
  ✅ PASS: Template Files

  Total: 6/6 tests passed

🎉 All tests passed! Dashboard is ready to use.
```

## Support

For issues or questions:
1. Check this documentation
2. Run test script: `python test_dashboard.py`
3. Check application logs
4. Review browser console for errors

---

**Version**: 1.0.0  
**Date**: October 12, 2025  
**Author**: Dashboard Feature Implementation
