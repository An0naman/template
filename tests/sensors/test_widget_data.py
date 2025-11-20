#!/usr/bin/env python3
"""Test widget data retrieval"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app
from app.services.dashboard_service import DashboardService
import json

app = create_app()

with app.app_context():
    # Simulate widget 11
    widget = {
        'id': 11,
        'widget_type': 'list',
        'data_source_type': 'saved_search',
        'data_source_id': 4,
        'config': '{}'
    }
    
    print("Testing widget data retrieval...")
    print(f"Widget: {json.dumps(widget, indent=2)}")
    print("\n" + "="*60)
    
    data = DashboardService.get_widget_data(widget)
    
    print(f"\nReturned data:")
    print(f"  Total entries: {data.get('total_count', 0)}")
    print(f"  Entries:")
    for entry in data.get('entries', []):
        print(f"    - ID {entry['id']}: {entry['title']} (status: {entry['status']})")
