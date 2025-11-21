#!/usr/bin/env python3
"""
Quick Test: Apply Dashboard tables to all databases
"""
import sqlite3
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / 'data'

def test_auto_migrate():
    """Test the auto-migration on a specific database"""
    sys.path.insert(0, str(PROJECT_ROOT))
    
    from app.utils.auto_migrate import AutoMigration
    
    databases = list(DATA_DIR.glob('*.db'))
    print(f"Found {len(databases)} databases\n")
    
    results = {}
    for db_path in databases:
        if db_path.stat().st_size == 0:
            print(f"⊘ {db_path.name} - Empty database, skipping")
            results[db_path.name] = 'skipped'
            continue
            
        print(f"\n{'='*60}")
        print(f"Testing: {db_path.name}")
        print(f"{'='*60}")
        
        try:
            migrator = AutoMigration(db_path)
            success = migrator.run()
            
            # Check if Dashboard tables exist
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name IN ('Dashboard', 'DashboardWidget')
                ORDER BY name
            """)
            tables = [row[0] for row in cursor.fetchall()]
            conn.close()
            
            if len(tables) == 2:
                print(f"✓ {db_path.name} - Dashboard tables verified")
                results[db_path.name] = 'success'
            else:
                print(f"✗ {db_path.name} - Missing tables: {2-len(tables)}")
                results[db_path.name] = 'partial'
                
        except Exception as e:
            print(f"✗ {db_path.name} - Error: {e}")
            results[db_path.name] = 'failed'
    
    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    
    success_count = sum(1 for r in results.values() if r == 'success')
    total = len(results)
    
    for db_name, status in sorted(results.items()):
        icon = {'success': '✓', 'failed': '✗', 'partial': '⚠', 'skipped': '⊘'}[status]
        print(f"{icon} {db_name:20} - {status}")
    
    print(f"\n{success_count}/{total} databases successfully migrated")
    return success_count == total

if __name__ == '__main__':
    success = test_auto_migrate()
    sys.exit(0 if success else 1)
