#!/usr/bin/env python3
"""Quick script to check entry 91's milestone eligibility"""

import sqlite3

conn = sqlite3.connect('data/app.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Check entry 91
cursor.execute("""
    SELECT e.id, e.title, e.show_end_dates, e.intended_end_date,
           et.name as entry_type_name, et.show_end_dates as type_show_end_dates,
           es.name as status_name
    FROM Entry e
    JOIN EntryType et ON e.entry_type_id = et.id
    JOIN EntryState es ON e.status_id = es.id
    WHERE e.id = 91
""")

entry = cursor.fetchone()

if entry:
    print("=" * 60)
    print("ENTRY 91 DIAGNOSIS")
    print("=" * 60)
    print(f"Title: {entry['title']}")
    print(f"Type: {entry['entry_type_name']}")
    print(f"Status: {entry['status_name']}")
    print(f"\nMilestone Configuration:")
    print(f"  Entry.show_end_dates: {entry['show_end_dates']}")
    print(f"  Entry.intended_end_date: {entry['intended_end_date']}")
    print(f"  EntryType.show_end_dates: {entry['type_show_end_dates']}")
    
    print("\n" + "=" * 60)
    print("PLANNING MODE AVAILABILITY CHECK")
    print("=" * 60)
    
    issues = []
    
    # Check conditions
    if not entry['type_show_end_dates']:
        issues.append("❌ EntryType.show_end_dates is disabled")
    else:
        print("✅ EntryType.show_end_dates is enabled")
    
    if not entry['intended_end_date']:
        issues.append("❌ Entry.intended_end_date is not set")
    else:
        print(f"✅ Entry.intended_end_date is set: {entry['intended_end_date']}")
    
    if entry['status_name'].lower() == 'completed':
        issues.append("❌ Entry status is 'Completed'")
    else:
        print(f"✅ Entry status is not completed: {entry['status_name']}")
    
    if not issues:
        print("\n🎉 Planning mode SHOULD be available!")
    else:
        print("\n⚠️  Planning mode NOT available due to:")
        for issue in issues:
            print(f"   {issue}")
    
    # Check for existing milestones
    cursor.execute("""
        SELECT COUNT(*) as count 
        FROM EntryStateMilestone 
        WHERE entry_id = 91 AND is_completed = 0
    """)
    milestone_count = cursor.fetchone()['count']
    print(f"\nExisting incomplete milestones: {milestone_count}")
    
else:
    print("❌ Entry 91 not found!")

conn.close()
