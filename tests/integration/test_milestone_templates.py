#!/usr/bin/env python3
"""
Test script for Milestone Templates feature
Tests the complete workflow of creating and using templates
"""

import requests
import json
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:5001"  # Using local template container
ENTRY_ID_SOURCE = 85  # Entry to use as template source (has milestones, type 9)
ENTRY_ID_TARGET = 94  # Entry to import template into (should accept the template)

def test_milestone_templates():
    """Test the milestone templates feature end-to-end"""
    print("=" * 60)
    print("MILESTONE TEMPLATES FEATURE TEST")
    print("=" * 60)
    
    # Step 1: Check if entry has milestones
    print("\n1. Checking source entry milestones...")
    response = requests.get(f"{BASE_URL}/api/entries/{ENTRY_ID_SOURCE}/milestones")
    if response.ok:
        milestones = response.json()
        print(f"   ✓ Found {len(milestones)} milestone(s) in source entry")
        if len(milestones) == 0:
            print("   ⚠️ Please add milestones to the source entry first!")
            return False
    else:
        print(f"   ❌ Failed to get milestones: {response.status_code}")
        return False
    
    # Step 2: Mark entry as template
    print("\n2. Marking entry as milestone template...")
    response = requests.put(
        f"{BASE_URL}/api/entries/{ENTRY_ID_SOURCE}/milestone-template",
        headers={'Content-Type': 'application/json'},
        json={
            'is_template': True,
            'template_name': 'Test Software Release Template',
            'template_description': 'Standard process for software releases'
        }
    )
    
    if response.ok:
        result = response.json()
        print(f"   ✓ Entry marked as template: {result['template_name']}")
    else:
        print(f"   ❌ Failed to mark as template: {response.status_code}")
        print(f"   Response: {response.text}")
        return False
    
    # Step 3: Set distribution status
    print("\n3. Marking template for distribution...")
    response = requests.put(
        f"{BASE_URL}/api/entries/{ENTRY_ID_SOURCE}/milestone-template/distribution",
        headers={'Content-Type': 'application/json'},
        json={
            'distribution_status': 'marked_for_distribution'
        }
    )
    
    if response.ok:
        print("   ✓ Template marked for distribution")
    else:
        print(f"   ❌ Failed to set distribution status: {response.status_code}")
        return False
    
    # Step 4: Get template status
    print("\n4. Verifying template status...")
    response = requests.get(f"{BASE_URL}/api/entries/{ENTRY_ID_SOURCE}/milestone-template")
    if response.ok:
        status = response.json()
        print(f"   ✓ Template Name: {status['template_name']}")
        print(f"   ✓ Distribution Status: {status['distribution_status']}")
        print(f"   ✓ Milestone Count: {status['milestone_count']}")
    else:
        print(f"   ❌ Failed to get template status: {response.status_code}")
        return False
    
    # Step 5: Get available templates for target entry
    print(f"\n5. Checking available templates for entry {ENTRY_ID_TARGET}...")
    response = requests.get(f"{BASE_URL}/api/entries/{ENTRY_ID_TARGET}/available-templates")
    if response.ok:
        available = response.json()
        print(f"   ✓ Found {len(available)} available template(s)")
        for tmpl in available:
            print(f"      - {tmpl['template_name']} ({tmpl['milestone_count']} milestones)")
    else:
        print(f"   ❌ Failed to get available templates: {response.status_code}")
        print(f"   Response: {response.text}")
        return False
    
    # Step 6: Import template to target entry
    print(f"\n6. Importing template into entry {ENTRY_ID_TARGET}...")
    response = requests.post(
        f"{BASE_URL}/api/entries/{ENTRY_ID_TARGET}/import-template",
        headers={'Content-Type': 'application/json'},
        json={
            'template_entry_id': ENTRY_ID_SOURCE,
            'import_mode': 'replace'
        }
    )
    
    if response.ok:
        result = response.json()
        print(f"   ✓ Template imported successfully!")
        print(f"   ✓ Imported {result['imported_count']} milestone(s)")
        print(f"   ✓ Import mode: {result['import_mode']}")
    else:
        print(f"   ❌ Failed to import template: {response.status_code}")
        print(f"   Response: {response.text}")
        return False
    
    # Step 7: Verify imported milestones
    print(f"\n7. Verifying imported milestones in entry {ENTRY_ID_TARGET}...")
    response = requests.get(f"{BASE_URL}/api/entries/{ENTRY_ID_TARGET}/milestones")
    if response.ok:
        imported_milestones = response.json()
        print(f"   ✓ Target entry now has {len(imported_milestones)} milestone(s)")
        for m in imported_milestones:
            print(f"      {m['order_position']}. {m['target_state_name']} ({m['duration_days']}d)")
    else:
        print(f"   ❌ Failed to verify milestones: {response.status_code}")
        return False
    
    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED!")
    print("=" * 60)
    print("\nFeature is working correctly!")
    return True


def test_entry_type_relationships():
    """Test entry type relationship management"""
    print("\n" + "=" * 60)
    print("ENTRY TYPE RELATIONSHIPS TEST")
    print("=" * 60)
    
    # Get all entry types
    print("\n1. Getting all entry types...")
    response = requests.get(f"{BASE_URL}/api/entry-types")
    if not response.ok:
        print(f"   ❌ Failed to get entry types: {response.status_code}")
        return False
    
    entry_types = response.json()
    print(f"   ✓ Found {len(entry_types)} entry type(s)")
    
    if len(entry_types) < 2:
        print("   ⚠️ Need at least 2 entry types to test relationships!")
        return False
    
    type1_id = entry_types[0]['id']
    type2_id = entry_types[1]['id']
    
    print(f"   Using types: {entry_types[0]['name']} and {entry_types[1]['name']}")
    
    # Create a relationship
    print("\n2. Creating relationship...")
    response = requests.post(
        f"{BASE_URL}/api/entry-types/relationships",
        headers={'Content-Type': 'application/json'},
        json={
            'from_type_id': type1_id,
            'to_type_id': type2_id,
            'relationship_type': 'bidirectional',
            'can_share_templates': True
        }
    )
    
    if response.ok:
        result = response.json()
        rel_id = result['relationship']['id']
        print(f"   ✓ Relationship created (ID: {rel_id})")
    elif response.status_code == 409:
        print("   ℹ️ Relationship already exists")
        # Get existing relationships
        response = requests.get(f"{BASE_URL}/api/entry-types/relationships")
        if response.ok:
            relationships = response.json()
            rel_id = relationships[0]['id'] if relationships else None
        else:
            return False
    else:
        print(f"   ❌ Failed to create relationship: {response.status_code}")
        print(f"   Response: {response.text}")
        return False
    
    # Get relationships for a type
    print(f"\n3. Getting relationships for type {type1_id}...")
    response = requests.get(f"{BASE_URL}/api/entry-types/{type1_id}/relationships")
    if response.ok:
        result = response.json()
        print(f"   ✓ Type has {len(result['relationships'])} relationship(s)")
    else:
        print(f"   ❌ Failed to get relationships: {response.status_code}")
        return False
    
    print("\n" + "=" * 60)
    print("✅ RELATIONSHIP TESTS PASSED!")
    print("=" * 60)
    return True


if __name__ == '__main__':
    print("\n🧪 Testing Milestone Templates Feature\n")
    
    # Test entry type relationships first
    if not test_entry_type_relationships():
        print("\n❌ Entry type relationship tests failed!")
        exit(1)
    
    # Then test template functionality
    if not test_milestone_templates():
        print("\n❌ Milestone template tests failed!")
        exit(1)
    
    print("\n✅ All feature tests completed successfully!")
    print("\n📝 Next steps:")
    print("   1. Test the UI in the browser at http://localhost:5000")
    print("   2. Create an entry with milestones")
    print("   3. Use Template → Save as Template")
    print("   4. Mark for Distribution")
    print("   5. Go to another entry and Import from Template")
    print("\n")
