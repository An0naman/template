# Testing Guide

## 🧪 Overview

The project maintains a comprehensive test suite organized by functionality. All tests are located in the `tests/` directory.

## 📂 Test Structure

```
tests/
├── integration/           # Integration tests for API and features
│   ├── test_api.py
│   ├── test_features.py
│   ├── test_notifications.py
│   └── ...
├── sensors/              # Sensor module specific tests
│   ├── test_sensor_module_e2e.py
│   └── ...
├── niimbot/              # Label printer hardware tests
│   ├── test_niimbot_print.py
│   └── ...
├── data/                 # Data processing and validation tests
│   ├── test_data_commands.py
│   └── ...
```

## 🚀 Running Tests

### Running All Tests
```bash
python -m pytest tests/
```

### Running Specific Categories

**Integration Tests**
```bash
python -m pytest tests/integration/
```

**Sensor Tests**
```bash
python -m pytest tests/sensors/
```

**Niimbot (Printer) Tests**
```bash
python -m pytest tests/niimbot/
```

## 🛠️ Test Categories

### Integration Tests (`tests/integration/`)
Tests that verify the interaction between different parts of the application, including API endpoints, database operations, and feature workflows.
- **API**: `test_api.py`, `test_user_preferences.py`
- **Features**: `test_features.py`, `test_ai_chatbot.py`, `test_git_integration.sh`
- **Dashboard**: `test_dashboard.py`
- **Security**: `test_security.py`
- **Heartbeat**: `test_heartbeat_detection.py`

### Sensor Tests (`tests/sensors/`)
Dedicated tests for the IoT sensor module, covering data collection, visualization, and device management.
- **End-to-End**: `test_sensor_module_e2e.py`
- **Performance**: `test_chart_performance.py`
- **Master Control**: `test_sensor_master_control.py`
- **Quick Test**: `test_sensor_quick.sh`

### Niimbot Tests (`tests/niimbot/`)
Hardware interface tests for Niimbot label printers.
- **Communication**: `test_niimbot_rfcomm.py`
- **Printing**: `test_niimbot_print.py`

### Data Tests (`tests/data/`)
Low-level tests for data processing, binary formats, and protocol validation.
- **Protocols**: `test_data_commands.py`
- **Hardware Data**: `test_bit_order.py`, `test_raw_pixels.py`
- **Fixes**: `test_hitradius_fix.sh`

## 📝 Writing New Tests

1. Identify the category (Integration, Sensor, Hardware, Data)
2. Create a new file in the appropriate directory
3. Use `pytest` fixtures for setup/teardown
4. Follow the naming convention `test_*.py`
