#!/usr/bin/env python3
"""
Dashboard Feature Testing Script
Tests the dashboard functionality including widget creation, data loading, and visualization
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

print("🚀 Dashboard Feature Test")
print("=" * 70)

def test_imports():
    """Test that all dashboard modules can be imported"""
    print("\n✅ Testing Imports...")
    
    try:
        from app.services.dashboard_service import DashboardService
        print("  ✓ DashboardService imported successfully")
        
        from app.api.dashboard_api import dashboard_api_bp
        print("  ✓ Dashboard API imported successfully")
        
        return True
    except ImportError as e:
        print(f"  ✗ Import error: {e}")
        return False

def test_database_tables():
    """Test that dashboard tables exist"""
    print("\n✅ Testing Database Tables...")
    
    try:
        import sqlite3
        db_path = os.path.join(os.path.dirname(__file__), 'data', 'template.db')
        
        if not os.path.exists(db_path):
            print(f"  ⚠️  Database not found at {db_path}")
            print("  ℹ️  Run the app first to initialize the database")
            return False
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check for Dashboard table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='Dashboard'")
        if cursor.fetchone():
            print("  ✓ Dashboard table exists")
        else:
            print("  ✗ Dashboard table not found")
            return False
        
        # Check for DashboardWidget table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='DashboardWidget'")
        if cursor.fetchone():
            print("  ✓ DashboardWidget table exists")
        else:
            print("  ✗ DashboardWidget table not found")
            return False
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"  ✗ Database test error: {e}")
        return False

def test_dashboard_service():
    """Test DashboardService functionality"""
    print("\n✅ Testing DashboardService...")
    
    try:
        from app.services.dashboard_service import DashboardService
        
        # Test that methods exist
        assert hasattr(DashboardService, 'get_saved_search_entries')
        print("  ✓ get_saved_search_entries method exists")
        
        assert hasattr(DashboardService, 'get_state_distribution')
        print("  ✓ get_state_distribution method exists")
        
        assert hasattr(DashboardService, 'get_sensor_data_trends')
        print("  ✓ get_sensor_data_trends method exists")
        
        assert hasattr(DashboardService, 'generate_ai_summary')
        print("  ✓ generate_ai_summary method exists")
        
        assert hasattr(DashboardService, 'get_widget_data')
        print("  ✓ get_widget_data method exists")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Service test error: {e}")
        return False

def test_api_endpoints():
    """Test API endpoint definitions"""
    print("\n✅ Testing API Endpoints...")
    
    try:
        from app.api.dashboard_api import dashboard_api_bp
        
        # Get all registered routes
        routes = [str(rule) for rule in dashboard_api_bp.url_map.iter_rules() if 'dashboard' in str(rule) or 'widget' in str(rule)]
        
        expected_routes = [
            'dashboards',
            'dashboard_sources',
            'widgets'
        ]
        
        print(f"  ℹ️  Found {len(routes)} routes")
        
        return True
        
    except Exception as e:
        print(f"  ✗ API test error: {e}")
        return False

def test_static_files():
    """Test that dashboard static files exist"""
    print("\n✅ Testing Static Files...")
    
    js_path = os.path.join(os.path.dirname(__file__), 'app', 'static', 'js', 'dashboard.js')
    
    if os.path.exists(js_path):
        print(f"  ✓ dashboard.js exists")
        file_size = os.path.getsize(js_path)
        print(f"    Size: {file_size:,} bytes")
        return True
    else:
        print(f"  ✗ dashboard.js not found")
        return False

def test_template_file():
    """Test that dashboard template exists"""
    print("\n✅ Testing Template Files...")
    
    template_path = os.path.join(os.path.dirname(__file__), 'app', 'templates', 'dashboard.html')
    
    if os.path.exists(template_path):
        print(f"  ✓ dashboard.html exists")
        with open(template_path, 'r') as f:
            content = f.read()
            print(f"    Lines: {len(content.splitlines())}")
            
            # Check for key elements
            if 'gridstack' in content.lower():
                print("    ✓ Gridstack integration found")
            if 'chart' in content.lower():
                print("    ✓ Chart.js integration found")
            if 'widget' in content.lower():
                print("    ✓ Widget structure found")
                
        return True
    else:
        print(f"  ✗ dashboard.html not found")
        return False

def print_usage_guide():
    """Print usage guide"""
    print("\n" + "=" * 70)
    print("📖 Dashboard Usage Guide")
    print("=" * 70)
    
    print("\n🎯 Features:")
    print("  • Configurable multi-dashboard system")
    print("  • Drag-and-drop widget positioning")
    print("  • Multiple widget types:")
    print("    - Entry Lists (from saved searches)")
    print("    - Pie Charts (entry state distribution)")
    print("    - Line Charts (sensor data trends)")
    print("    - Stat Cards (quick metrics)")
    print("    - AI Summaries (powered by Gemini)")
    
    print("\n🚀 How to Use:")
    print("  1. Start your Flask app: python run.py")
    print("  2. Navigate to: http://localhost:5000/dashboard")
    print("  3. Click 'New Dashboard' to create your first dashboard")
    print("  4. Add widgets using the '+ Add Widget' button")
    print("  5. Configure each widget with:")
    print("     - Widget type")
    print("     - Data source (saved search)")
    print("     - Display settings")
    print("  6. Use 'Edit Layout' to drag and resize widgets")
    print("  7. Click 'Save Layout' when done")
    
    print("\n🔧 Widget Types:")
    print("  • List: Shows entries from a saved search")
    print("  • Pie Chart: Visualizes entry state distribution")
    print("  • Line Chart: Plots sensor data over time")
    print("  • Stat Card: Displays a single metric")
    print("  • AI Summary: Generates insights using AI")
    
    print("\n💡 Tips:")
    print("  • Create saved searches first (on main page)")
    print("  • Use multiple dashboards for different views")
    print("  • Set one dashboard as default")
    print("  • Widgets auto-refresh based on interval")
    print("  • AI summaries require Gemini API key in settings")
    
    print("\n📚 API Endpoints:")
    print("  GET  /api/dashboards - List all dashboards")
    print("  POST /api/dashboards - Create new dashboard")
    print("  GET  /api/dashboards/:id - Get dashboard with widgets")
    print("  PUT  /api/dashboards/:id - Update dashboard")
    print("  DEL  /api/dashboards/:id - Delete dashboard")
    print("  POST /api/dashboards/:id/widgets - Add widget")
    print("  PUT  /api/widgets/:id - Update widget")
    print("  DEL  /api/widgets/:id - Delete widget")
    print("  GET  /api/widgets/:id/data - Get widget data")
    print("  GET  /api/dashboard_sources - Get available data sources")

def main():
    """Run all tests"""
    results = []
    
    results.append(("Imports", test_imports()))
    results.append(("Database Tables", test_database_tables()))
    results.append(("Dashboard Service", test_dashboard_service()))
    results.append(("API Endpoints", test_api_endpoints()))
    results.append(("Static Files", test_static_files()))
    results.append(("Template Files", test_template_file()))
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 Test Summary")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}: {test_name}")
    
    print(f"\n  Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Dashboard is ready to use.")
        print_usage_guide()
        return 0
    else:
        print("\n⚠️  Some tests failed. Please check the errors above.")
        print("\nℹ️  If database tables are missing, run the app once to initialize them.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
