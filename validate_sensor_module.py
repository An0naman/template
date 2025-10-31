#!/usr/bin/env python3
"""
Static File Validation for Sensor Module
Validates that all required files exist and are properly structured
"""

import os
import json
import sys
from pathlib import Path

# Color codes
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
BOLD = '\033[1m'
RESET = '\033[0m'


def check_file_exists(path: str) -> bool:
    """Check if a file exists"""
    exists = os.path.exists(path)
    status = f"{GREEN}✓{RESET}" if exists else f"{RED}✗{RESET}"
    print(f"  {status} {path}")
    return exists


def check_file_contains(path: str, searches: list) -> bool:
    """Check if file contains specific strings"""
    if not os.path.exists(path):
        return False
    
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    all_found = True
    for search_term in searches:
        if search_term in content:
            print(f"    {GREEN}✓{RESET} Contains: {search_term}")
        else:
            print(f"    {RED}✗{RESET} Missing: {search_term}")
            all_found = False
    
    return all_found


def validate_sensor_module():
    """Validate the sensor module files"""
    print(f"\n{BLUE}{BOLD}{'='*60}{RESET}")
    print(f"{BLUE}{BOLD}{'Sensor Module Validation'.center(60)}{RESET}")
    print(f"{BLUE}{BOLD}{'='*60}{RESET}\n")
    
    base_path = Path(__file__).parent
    results = {}
    
    # Check template files
    print(f"{BOLD}Template Files:{RESET}")
    results['sensor_section'] = check_file_exists(
        str(base_path / "app/templates/sections/_sensors_section.html")
    )
    results['sensor_modals'] = check_file_exists(
        str(base_path / "app/templates/sections/_sensors_modals.html")
    )
    
    # Check static files
    print(f"\n{BOLD}Static Files:{RESET}")
    results['sensor_css'] = check_file_exists(
        str(base_path / "app/static/css/sections/sensors.css")
    )
    results['sensor_js'] = check_file_exists(
        str(base_path / "app/static/js/sections/_sensors_functions.js")
    )
    results['sensor_init'] = check_file_exists(
        str(base_path / "app/static/js/sections/sensors_init.js")
    )
    
    # Check API file
    print(f"\n{BOLD}Backend Files:{RESET}")
    results['api_file'] = check_file_exists(
        str(base_path / "app/api/shared_sensor_api.py")
    )
    results['service_file'] = check_file_exists(
        str(base_path / "app/services/shared_sensor_service.py")
    )
    
    # Validate content of key files
    print(f"\n{BOLD}Content Validation:{RESET}")
    
    # Check sensor section template
    section_path = str(base_path / "app/templates/sections/_sensors_section.html")
    if os.path.exists(section_path):
        print(f"\n  Checking {BOLD}_sensors_section.html{RESET}:")
        results['section_content'] = check_file_contains(section_path, [
            'id="sensorChart"',
            'id="sensorStats"',
            'id="sensorTypeSelect"',
            'id="timeRangeSelect"',
            'data-entry-id',
            'css/sections/sensors.css',
            'js/sections/_sensors_functions.js',
            'js/sections/sensors_init.js'
        ])
    
    # Check modals template
    modals_path = str(base_path / "app/templates/sections/_sensors_modals.html")
    if os.path.exists(modals_path):
        print(f"\n  Checking {BOLD}_sensors_modals.html{RESET}:")
        results['modals_content'] = check_file_contains(modals_path, [
            'id="addSensorDataModal"',
            'id="editSensorDataModal"',
            'id="addSensorDataForm"',
            'id="editSensorDataForm"'
        ])
    
    # Check JavaScript file
    js_path = str(base_path / "app/static/js/sections/_sensors_functions.js")
    if os.path.exists(js_path):
        print(f"\n  Checking {BOLD}_sensors_functions.js{RESET}:")
        results['js_content'] = check_file_contains(js_path, [
            'initializeSensorSection',
            'loadSensorData',
            'updateChart',
            'addSensorReading',
            'updateSensorReading',
            'deleteSensorReading',
            'window.initializeSensorSection'
        ])
    
    # Check API file
    api_path = str(base_path / "app/api/shared_sensor_api.py")
    if os.path.exists(api_path):
        print(f"\n  Checking {BOLD}shared_sensor_api.py{RESET}:")
        results['api_content'] = check_file_contains(api_path, [
            '/api/entry/<int:entry_id>/sensor-data',
            '/api/entry/<int:entry_id>/sensor-types',
            '/api/shared_sensor_data/<int:sensor_id>',
            '@shared_sensor_api_bp.route'
        ])
    
    # Check service file
    service_path = str(base_path / "app/services/shared_sensor_service.py")
    if os.path.exists(service_path):
        print(f"\n  Checking {BOLD}shared_sensor_service.py{RESET}:")
        results['service_content'] = check_file_contains(service_path, [
            'format_readings_for_chart',
            'aggregate_statistics',
            'class SharedSensorDataService'
        ])
    
    # Check Entry v2 integration
    print(f"\n{BOLD}Entry v2 Integration:{RESET}")
    entry_v2_path = str(base_path / "app/templates/entry_detail_v2.html")
    if os.path.exists(entry_v2_path):
        print(f"\n  Checking {BOLD}entry_detail_v2.html{RESET}:")
        results['entry_integration'] = check_file_contains(entry_v2_path, [
            "include 'sections/_sensors_section.html'",
            "include 'sections/_sensors_modals.html'"
        ])
    
    # Print summary
    print(f"\n{BLUE}{BOLD}{'='*60}{RESET}")
    print(f"{BOLD}Summary:{RESET}")
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for check, result in results.items():
        status = f"{GREEN}PASS{RESET}" if result else f"{RED}FAIL{RESET}"
        print(f"  {check.replace('_', ' ').title()}: {status}")
    
    print(f"\n{BOLD}Total: {passed}/{total} checks passed{RESET}")
    
    if passed == total:
        print(f"\n{GREEN}{BOLD}✅ All validation checks passed!{RESET}")
        print(f"{GREEN}The sensor module is properly installed.{RESET}")
        return 0
    else:
        print(f"\n{RED}{BOLD}❌ Some validation checks failed{RESET}")
        print(f"{YELLOW}Please review the output above for details.{RESET}")
        return 1


if __name__ == "__main__":
    sys.exit(validate_sensor_module())
