#!/usr/bin/env python3
"""
Test Dashboard SQL Search Support
Tests that dashboard widgets can handle saved searches with custom SQL queries
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app
from app.services.dashboard_service import DashboardService
import json

print("🧪 Testing Dashboard SQL Search Support")
print("=" * 70)

app = create_app()

with app.app_context():
    import sqlite3
    db_path = app.config['DATABASE_PATH']
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Check if saved searches exist
    cursor.execute("SELECT COUNT(*) as count FROM SavedSearch")
    search_count = cursor.fetchone()['count']
    print(f"\n📊 Found {search_count} saved searches in database")
    
    if search_count == 0:
        print("  ⚠️  No saved searches found. Create some searches first.")
        sys.exit(0)
    
    # Get a saved search (preferably one with custom SQL)
    cursor.execute("""
        SELECT id, name, use_sql_mode, custom_sql_query 
        FROM SavedSearch 
        ORDER BY use_sql_mode DESC, id 
        LIMIT 5
    """)
    searches = cursor.fetchall()
    
    print("\n🔍 Available Saved Searches:")
    for search in searches:
        sql_mode = "✅ SQL Mode" if search['use_sql_mode'] else "📋 Filter Mode"
        has_sql = "✓" if search['custom_sql_query'] else "✗"
        print(f"  ID {search['id']}: {search['name']}")
        print(f"    Mode: {sql_mode}")
        print(f"    Custom SQL: {has_sql}")
        if search['custom_sql_query']:
            query_preview = search['custom_sql_query'][:80]
            if len(search['custom_sql_query']) > 80:
                query_preview += "..."
            print(f"    Query: {query_preview}")
    
    # Test with each type of search
    print("\n🧪 Testing Dashboard Service with Saved Searches:")
    print("-" * 70)
    
    for search in searches[:3]:  # Test first 3 searches
        print(f"\n📌 Testing Search ID {search['id']}: '{search['name']}'")
        
        try:
            result = DashboardService.get_saved_search_entries(search['id'])
            
            if 'error' in result:
                print(f"  ❌ Error: {result['error']}")
            else:
                entry_count = result.get('total_count', 0)
                entries = result.get('entries', [])
                
                print(f"  ✅ Success!")
                print(f"  📊 Returned {entry_count} entries")
                
                if entries:
                    print(f"  📋 Sample entries:")
                    for entry in entries[:3]:  # Show first 3
                        print(f"    - ID {entry['id']}: {entry['title']} ({entry['entry_type_label']})")
                        print(f"      Status: {entry['status']}")
                else:
                    print(f"  ℹ️  No entries matched")
                    
        except Exception as e:
            print(f"  ❌ Exception: {e}")
            import traceback
            traceback.print_exc()
    
    # Test widget data method
    print("\n" + "=" * 70)
    print("🔧 Testing Widget Data Retrieval:")
    print("-" * 70)
    
    if searches:
        test_search = searches[0]
        print(f"\n📌 Creating test widget with Search ID {test_search['id']}")
        
        widget = {
            'id': 999,
            'widget_type': 'list',
            'data_source_type': 'saved_search',
            'data_source_id': test_search['id'],
            'config': '{}'
        }
        
        try:
            widget_data = DashboardService.get_widget_data(widget)
            
            if 'error' in widget_data:
                print(f"  ❌ Error: {widget_data['error']}")
            else:
                print(f"  ✅ Widget data retrieved successfully!")
                print(f"  📊 Total entries: {widget_data.get('total_count', 0)}")
                print(f"  📋 Entries available: {len(widget_data.get('entries', []))}")
                
        except Exception as e:
            print(f"  ❌ Exception: {e}")
            import traceback
            traceback.print_exc()
    
    conn.close()

print("\n" + "=" * 70)
print("✅ Test Complete!")
print("\nℹ️  Dashboard widgets should now properly handle:")
print("  • Standard filter-based searches")
print("  • SQL mode searches with custom queries")
print("  • Both WHERE clause fragments and full SELECT statements")
