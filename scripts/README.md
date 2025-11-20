# Scripts Directory

This directory contains utility and development scripts organized by category.

## Directory Structure

### `/debug/`
Debug and diagnostic scripts:
- `debug_*.py` - Debug utilities
- `diagnose_*.py` - Diagnostic tools
- `check_*.py` - Data verification scripts

### `/bluetooth/`
Bluetooth and hardware communication scripts:
- `capture_niimbot_protocol.py` - Protocol capture
- `find_rfcomm_address.py` - Device discovery
- `monitor_*.sh` - Bluetooth monitoring
- `pair_*.sh` - Device pairing utilities
- `scan_*.py` - Device scanning
- `btmon_capture.txt` - Capture logs

### `/utilities/`
General utility scripts:
- `apply_*.py` - Data migration utilities
- `setup_*.py` - Setup scripts
- `flask_init_db.py` - Database initialization
- `init_db*.py` - Database setup
- `validate_*.py` - Validation utilities
- Various shell scripts

### Root Level Scripts
Main operational scripts remain in the scripts root:
- `add_uploads_volume.sh`
- `add_watchtower.sh`
- `bump_version.sh`
- `create-new-app.sh`
- `update_casaos_icon.sh`
- etc.

## Usage

Most scripts can be run directly:

```bash
# Debug scripts
python scripts/debug/diagnose_sensor_notifications.py

# Bluetooth utilities
bash scripts/bluetooth/monitor_bt_v2.sh

# Utilities
python scripts/utilities/setup_ai.py
```

## Notes

- Debug scripts are temporary and may be removed or updated frequently
- Bluetooth scripts require appropriate hardware and permissions
- Utility scripts may modify database or system configuration
