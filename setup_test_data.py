#!/usr/bin/env python3
"""
Setup test data for milestone templates testing
Creates entry types, entries, and milestones
"""

import requests
import json

BASE_URL = "http://localhost:5999"

def setup_test_data():
    print("=" * 60)
    print("SETTING UP TEST DATA FOR MILESTONE TEMPLATES")
    print("=" * 60)
    
    # Step 1: Create entry types
    print("\n1. Creating entry types...")
    entry_types = [
        {"entry_type": "Project", "color": "#007bff"},
        {"entry_type": "Product Launch", "color": "#28a745"}
    ]
    
    created_types = []
    for et in entry_types:
        response = requests.post(f"{BASE_URL}/api/entry-types", json=et)
        if response.ok:
            data = response.json()
            created_types.append(data)
            print(f"   ✓ Created entry type: {et['entry_type']} (ID: {data['id']})")
        else:
            print(f"   ⚠️ Failed to create {et['entry_type']}: {response.text}")
    
    if len(created_types) < 2:
        print("   ❌ Need at least 2 entry types!")
        return False
    
    # Step 2: Create entries
    print("\n2. Creating entries...")
    entries = [
        {
            "entry_name": "Template Source Entry",
            "entry_type_id": created_types[0]['id'],
            "description": "This will be used as a template"
        },
        {
            "entry_name": "Target Entry",
            "entry_type_id": created_types[0]['id'],
            "description": "Will import template here"
        }
    ]
    
    created_entries = []
    for entry in entries:
        response = requests.post(f"{BASE_URL}/api/entries", json=entry)
        if response.ok:
            data = response.json()
            created_entries.append(data)
            print(f"   ✓ Created entry: {entry['entry_name']} (ID: {data['id']})")
        else:
            print(f"   ⚠️ Failed to create entry: {response.text}")
    
    if len(created_entries) < 2:
        print("   ❌ Need at least 2 entries!")
        return False
    
    # Step 3: Add milestones to source entry
    print("\n3. Adding milestones to source entry...")
    milestones = [
        {
            "milestone_order": 1,
            "milestone_title": "Planning Phase",
            "milestone_state": "completed",
            "milestone_days": 7
        },
        {
            "milestone_order": 2,
            "milestone_title": "Development",
            "milestone_state": "in_progress",
            "milestone_days": 14
        },
        {
            "milestone_order": 3,
            "milestone_title": "Testing",
            "milestone_state": "pending",
            "milestone_days": 7
        },
        {
            "milestone_order": 4,
            "milestone_title": "Deployment",
            "milestone_state": "pending",
            "milestone_days": 3
        }
    ]
    
    for milestone in milestones:
        response = requests.post(
            f"{BASE_URL}/api/entries/{created_entries[0]['id']}/milestones",
            json=milestone
        )
        if response.ok:
            print(f"   ✓ Added milestone: {milestone['milestone_title']}")
        else:
            print(f"   ⚠️ Failed to add milestone: {response.text}")
    
    # Step 4: Create entry type relationship
    print("\n4. Creating entry type relationship...")
    relationship = {
        "source_entry_type_id": created_types[0]['id'],
        "target_entry_type_id": created_types[0]['id'],
        "relationship_type": "bidirectional"
    }
    
    response = requests.post(f"{BASE_URL}/api/entry-types/relationships", json=relationship)
    if response.ok:
        print(f"   ✓ Created relationship between {created_types[0]['entry_type']} types")
    else:
        print(f"   ⚠️ Failed to create relationship: {response.text}")
    
    print("\n" + "=" * 60)
    print("✅ TEST DATA SETUP COMPLETE!")
    print("=" * 60)
    print(f"\n📝 Test Configuration:")
    print(f"   Source Entry ID: {created_entries[0]['id']}")
    print(f"   Target Entry ID: {created_entries[1]['id']}")
    print(f"   Entry Type ID: {created_types[0]['id']}")
    print(f"\n🧪 You can now run: python test_milestone_templates.py")
    print(f"   (Update ENTRY_ID_SOURCE={created_entries[0]['id']} and ENTRY_ID_TARGET={created_entries[1]['id']})")
    
    return True

if __name__ == "__main__":
    try:
        setup_test_data()
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to the server. Is it running on port 5999?")
    except Exception as e:
        print(f"❌ Error: {e}")
