# Test Suite

This directory contains all test files organized by category.

## Directory Structure

### `/niimbot/`
Niimbot label printer tests:
- Bluetooth communication tests
- Label printing tests
- Device-specific tests (B1, D110)
- Protocol tests

### `/sensors/`
Sensor module tests:
- Sensor functionality tests
- Chart rendering tests
- Widget tests
- End-to-end sensor workflow tests

### `/labels/`
Label printing and processing tests.

### `/misc/`
Miscellaneous tests:
- API integration tests
- Dashboard tests
- Security tests
- Feature-specific tests
- HTML test files and artifacts

### Root Level Files
Tests in the root directory are organized test suites:
- `test_reminder_editing.py`
- `test_notifications.py`
- `test_new_features.py`
- etc.

## Running Tests

To run specific test categories:

```bash
# Run niimbot tests
python -m pytest tests/niimbot/

# Run sensor tests
python -m pytest tests/sensors/

# Run all tests
python -m pytest tests/
```

## Test Naming Convention

- `test_*.py` - Python test files
- `test_*.html` - HTML test pages
- `test_*.js` - JavaScript test files
