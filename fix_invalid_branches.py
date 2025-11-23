#!/usr/bin/env python3
"""
Fix invalid branch names in the Git database
"""
import sqlite3
import os
import sys

def fix_invalid_branches():
    """Fix invalid branch names in GitCommit table"""
    # Get database path
    db_path = os.path.join(os.path.dirname(__file__), 'instance', 'project_tracker.db')
    
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if GitCommit table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='GitCommit'")
    if not cursor.fetchone():
        print("GitCommit table not found. Git integration may not be set up yet.")
        conn.close()
        return
    
    # Find commits with invalid branch names
    cursor.execute("""
        SELECT id, branch, commit_hash 
        FROM GitCommit 
        WHERE branch IS NOT NULL 
        AND (branch LIKE '.%' OR branch LIKE '%/.%' OR branch = '')
    """)
    
    invalid_commits = cursor.fetchall()
    
    if not invalid_commits:
        print("No invalid branch names found.")
        conn.close()
        return
    
    print(f"Found {len(invalid_commits)} commits with invalid branch names:")
    for commit_id, branch, commit_hash in invalid_commits:
        print(f"  - Commit {commit_hash[:7]}: branch='{branch}'")
    
    # Update invalid branches to 'main'
    cursor.execute("""
        UPDATE GitCommit 
        SET branch = 'main'
        WHERE branch IS NOT NULL 
        AND (branch LIKE '.%' OR branch LIKE '%/.%' OR branch = '')
    """)
    
    conn.commit()
    print(f"\nUpdated {cursor.rowcount} commits with invalid branch names to 'main'")
    
    conn.close()
    print("Done!")

if __name__ == '__main__':
    fix_invalid_branches()
