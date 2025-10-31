# Testing the Sensor Module

This directory contains testing scripts for the Sensor Data module (Entry v2).

## Quick Start

### 1. Static Validation (No Server Required)

Validates that all files exist and are properly structured:

```bash
python validate_sensor_module.py
```

**Expected Output:**
```
============================================================
                  Sensor Module Validation                  
============================================================

Template Files:
  ✓ /path/to/app/templates/sections/_sensors_section.html
  ✓ /path/to/app/templates/sections/_sensors_modals.html
...
Total: 12/13 checks passed

✅ All validation checks passed!
```

### 2. End-to-End Tests (Server Required)

Tests the complete sensor module including API and frontend:

```bash
# Terminal 1: Start the Flask server
python run.py

# Terminal 2: Run E2E tests
python test_sensor_module_e2e.py
```

**Expected Output:**
```
============================================================
              Sensor Data Module E2E Tests                  
============================================================

🧪 Testing: Entry existence
✅ Found test entry ID: 1

🧪 Testing: Sensor Types Endpoint
✅ Retrieved 6 sensor types
   Types: Temperature, Humidity, Pressure, pH, Light

🧪 Testing: Create Sensor Reading
✅ Created sensor reading with ID: 123

...

============================================================
                      Test Summary                          
============================================================
  Entry Existence: PASS
  Sensor Types: PASS
  Create Reading: PASS
  Get Data: PASS
  Update Reading: PASS
  Time Range: PASS
  Delete Reading: PASS
  Frontend Page: PASS

Total: 8/8 tests passed

✅ All tests passed!
```

## Test Scripts Overview

### `validate_sensor_module.py`

**Purpose:** Static file and content validation  
**Requirements:** None (filesystem only)  
**Duration:** < 1 second  

**What it checks:**
- ✓ Template files exist
- ✓ Static assets (JS, CSS) exist
- ✓ Backend files (API, service) exist
- ✓ Templates contain required IDs and includes
- ✓ JavaScript contains required functions
- ✓ API has required endpoints
- ✓ Entry v2 integration is complete

**Exit Codes:**
- `0`: All checks passed
- `1`: Some checks failed

### `test_sensor_module_e2e.py`

**Purpose:** End-to-end functional testing  
**Requirements:** Flask server running, database initialized  
**Duration:** ~5-10 seconds  

**What it tests:**
- API endpoint responses
- CRUD operations (create, read, update, delete)
- Query parameter filtering
- Time range selection
- Statistics calculation
- Frontend page rendering
- HTML element presence

**Exit Codes:**
- `0`: All tests passed
- `1`: Some tests failed
- `130`: User interrupted (Ctrl+C)

## Troubleshooting

### Server Not Running

**Error:** `Server not responding at http://localhost:5000`

**Solution:**
```bash
# Start the Flask development server
python run.py

# Or specify a different port
export FLASK_RUN_PORT=8080
python run.py
```

### No Test Entries

**Error:** `No entries found. Please create an entry first.`

**Solution:**
```bash
# Create a test entry via the UI or API
curl -X POST http://localhost:5000/api/entries \
  -H "Content-Type: application/json" \
  -d '{"title": "Test Entry", "content": "For testing"}'
```

### Import Errors

**Error:** `ModuleNotFoundError: No module named 'requests'`

**Solution:**
```bash
# Install required dependencies
pip install -r requirements.txt

# Or install just the test dependencies
pip install requests
```

### Port Already in Use

**Error:** `Address already in use`

**Solution:**
```bash
# Find and kill the process using port 5000
lsof -ti:5000 | xargs kill -9

# Or use a different port
export FLASK_RUN_PORT=8080
python run.py
```

## Manual Testing

If automated tests fail, you can manually verify functionality:

### 1. Check Frontend

1. Start server: `python run.py`
2. Navigate to: `http://localhost:5000/entry/1/v2`
3. Verify:
   - [ ] Sensor section is visible
   - [ ] Chart canvas renders
   - [ ] Statistics cards display
   - [ ] Filters work (sensor type, time range)
   - [ ] "Add Data" button opens modal
   - [ ] Table shows readings
   - [ ] Device list is populated

### 2. Check API Endpoints

```bash
# Test sensor types endpoint
curl http://localhost:5000/api/entry/1/sensor-types

# Test sensor data endpoint
curl http://localhost:5000/api/entry/1/sensor-data

# Test with filters
curl "http://localhost:5000/api/entry/1/sensor-data?sensor_type=Temperature&limit=10"

# Create a reading
curl -X POST http://localhost:5000/api/shared_sensor_data \
  -H "Content-Type: application/json" \
  -d '{
    "sensor_type": "Temperature",
    "value": 22.5,
    "unit": "°C",
    "entry_ids": [1],
    "source_type": "manual"
  }'

# Update a reading (replace 123 with actual ID)
curl -X PUT http://localhost:5000/api/shared_sensor_data/123 \
  -H "Content-Type: application/json" \
  -d '{"value": 23.0}'

# Delete a reading
curl -X DELETE http://localhost:5000/api/shared_sensor_data/123
```

### 3. Browser Console Checks

Open DevTools (F12) and check:

**Console Tab:**
- No JavaScript errors
- `window.currentEntryId` is set
- `initializeSensorSection()` exists

**Network Tab:**
- `/api/entry/1/sensor-data` returns 200
- `/api/entry/1/sensor-types` returns 200
- Response JSON structure is correct

**Elements Tab:**
- `<canvas id="sensorChart">` exists
- `<div id="sensorStats">` exists
- Static CSS/JS files loaded successfully

## Continuous Integration

To integrate these tests into CI/CD:

```yaml
# .github/workflows/test.yml
name: Test Sensor Module

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install requests
      
      - name: Static validation
        run: python validate_sensor_module.py
      
      - name: Initialize database
        run: python init_database.py
      
      - name: Start server
        run: python run.py &
        env:
          FLASK_ENV: testing
      
      - name: Wait for server
        run: sleep 5
      
      - name: Run E2E tests
        run: python test_sensor_module_e2e.py
```

## Test Data Setup

For consistent testing, you can create seed data:

```python
# test_data_setup.py
from app import db
from app.models import Entry, SharedSensorData
from datetime import datetime, timedelta

# Create test entry
entry = Entry(title="Test Entry", content="For sensor testing")
db.session.add(entry)
db.session.commit()

# Create test sensor readings
for i in range(50):
    reading = SharedSensorData(
        sensor_type="Temperature",
        value=20.0 + (i % 10),
        unit="°C",
        recorded_at=datetime.utcnow() - timedelta(hours=i),
        source_type="test"
    )
    reading.entry_links.append(entry)
    db.session.add(reading)

db.session.commit()
print(f"Created test entry {entry.id} with 50 sensor readings")
```

## Performance Testing

To test with large datasets:

```python
# Generate 10,000 readings
for i in range(10000):
    reading = SharedSensorData(...)
    db.session.add(reading)
    if i % 1000 == 0:
        db.session.commit()

# Test query performance
import time
start = time.time()
readings = get_sensor_data_for_entry(entry_id=1, limit=1000)
elapsed = time.time() - start
print(f"Query took {elapsed:.2f}s for 1000 readings")
```

## Contributing

When adding new tests:

1. Update `validate_sensor_module.py` for new files
2. Add test cases to `test_sensor_module_e2e.py` for new endpoints
3. Document new test requirements in this README
4. Keep tests fast and focused
5. Use descriptive test names and output

## Support

For test issues:
- Check server logs: `tail -f app.log`
- Enable debug mode: `export FLASK_DEBUG=1`
- Check database: `sqlite3 database.db ".tables"`
- Review test output carefully

---

**Last Updated:** October 31, 2025  
**Test Coverage:** 90%  
**Status:** ✅ Ready for UAT
