#!/usr/bin/env python3
"""
Test script for Planning Assistant Feature
Tests context gathering, plan generation, and milestone application
"""

import os
import sys
import json
from datetime import datetime, timedelta

# Add the app directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.services.planning_service import get_planning_service
from app.db import get_db_connection

def test_context_gathering():
    """Test context gathering for an entry"""
    print("\n" + "="*60)
    print("TEST 1: Context Gathering")
    print("="*60)
    
    try:
        # Get a test entry (assuming entry ID 1 exists)
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, title, entry_type_id FROM Entry LIMIT 1")
        entry = cursor.fetchone()
        
        if not entry:
            print("❌ No entries found in database. Please create an entry first.")
            conn.close()
            return False
        
        entry_id = entry['id']
        print(f"✓ Testing with entry ID: {entry_id} - '{entry['title']}'")
        
        # Gather context
        planning_service = get_planning_service()
        context = planning_service.gather_entry_context(entry_id)
        
        if not context:
            print("❌ Failed to gather context")
            conn.close()
            return False
        
        print(f"\n✓ Context gathered successfully:")
        print(f"  - Entry Type: {context['entry'].get('entry_type_name')}")
        print(f"  - Current Status: {context['entry'].get('current_status')}")
        print(f"  - Available States: {len(context['available_states'])} states")
        print(f"  - Notes: {len(context['notes'])} notes")
        print(f"  - Custom Fields: {len(context['custom_fields'])} fields")
        print(f"  - Related Entries: {len(context['related_entries'])} entries")
        print(f"  - Existing Milestones: {len(context['existing_milestones'])} milestones")
        print(f"  - Similar Completed Entries: {len(context['similar_entries'])} entries")
        
        if context['available_states']:
            print(f"\n  Available Status Transitions:")
            for state in context['available_states']:
                print(f"    → {state['name']}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_plan_generation():
    """Test milestone plan generation"""
    print("\n" + "="*60)
    print("TEST 2: Plan Generation")
    print("="*60)
    
    try:
        # Get a test entry with end date capability
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT e.id, e.title, e.intended_end_date
            FROM Entry e
            JOIN EntryType et ON e.entry_type_id = et.id
            WHERE et.show_end_dates = 1
            LIMIT 1
        """)
        entry = cursor.fetchone()
        
        if not entry:
            print("❌ No entries with end dates found. Trying any entry...")
            cursor.execute("SELECT id, title FROM Entry LIMIT 1")
            entry = cursor.fetchone()
            
            if not entry:
                print("❌ No entries found in database.")
                conn.close()
                return False
        
        entry_id = entry['id']
        print(f"✓ Testing plan generation for entry ID: {entry_id} - '{entry['title']}'")
        
        # Generate plan
        planning_service = get_planning_service()
        
        # Check if AI is available
        if not planning_service.ai_service.is_available():
            print("⚠️  AI Service not available. Skipping plan generation test.")
            print("   (Configure GEMINI_API_KEY to enable this test)")
            conn.close()
            return True  # Not a failure, just skipped
        
        print("\n  Generating plan... (this may take a few seconds)")
        result = planning_service.generate_plan(entry_id, "Help me plan this project")
        
        if not result.get('success'):
            print(f"❌ Plan generation failed: {result.get('error')}")
            conn.close()
            return False
        
        plan = result['plan']
        print(f"\n✓ Plan generated successfully:")
        print(f"  - Title: {plan.get('title')}")
        print(f"  - Total Duration: {plan.get('duration_total_days')} days")
        print(f"  - Confidence: {plan.get('confidence', 0) * 100:.0f}%")
        print(f"  - Reasoning: {plan.get('reasoning', 'N/A')[:100]}...")
        print(f"  - Milestones: {len(plan.get('milestones', []))} milestones")
        
        if plan.get('milestones'):
            print(f"\n  Proposed Milestones:")
            for i, milestone in enumerate(plan['milestones'], 1):
                print(f"    {i}. {milestone.get('status_name')} - {milestone.get('target_date')}")
                print(f"       Duration: {milestone.get('duration_days')} days")
                print(f"       Notes: {milestone.get('notes', 'No notes')[:60]}...")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_plan_application():
    """Test applying a plan to create milestones"""
    print("\n" + "="*60)
    print("TEST 3: Plan Application")
    print("="*60)
    
    try:
        # Get or create a test entry
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT e.id, e.title, et.show_end_dates
            FROM Entry e
            JOIN EntryType et ON e.entry_type_id = et.id
            WHERE et.show_end_dates = 1
            LIMIT 1
        """)
        entry = cursor.fetchone()
        
        if not entry:
            print("❌ No entries with milestone support found.")
            conn.close()
            return False
        
        entry_id = entry['id']
        print(f"✓ Testing plan application for entry ID: {entry_id} - '{entry['title']}'")
        
        # Get available states for this entry
        cursor.execute("""
            SELECT e.entry_type_id FROM Entry e WHERE e.id = ?
        """, (entry_id,))
        entry_type_id = cursor.fetchone()['entry_type_id']
        
        cursor.execute("""
            SELECT id, name FROM EntryState
            WHERE entry_type_id = ?
            ORDER BY sort_order
            LIMIT 3
        """, (entry_type_id,))
        states = cursor.fetchall()
        
        if len(states) < 2:
            print("❌ Not enough states available to create test milestones.")
            conn.close()
            return False
        
        # Create a test plan
        today = datetime.now()
        test_plan = {
            'title': 'Test Milestone Plan',
            'duration_total_days': 14,
            'reasoning': 'This is a test plan',
            'confidence': 0.9,
            'milestones': [
                {
                    'state_id': states[1]['id'],
                    'status_name': states[1]['name'],
                    'target_date': (today + timedelta(days=7)).strftime('%Y-%m-%d'),
                    'duration_days': 7,
                    'notes': 'First test milestone'
                },
                {
                    'state_id': states[2]['id'] if len(states) > 2 else states[1]['id'],
                    'status_name': states[2]['name'] if len(states) > 2 else states[1]['name'],
                    'target_date': (today + timedelta(days=14)).strftime('%Y-%m-%d'),
                    'duration_days': 7,
                    'notes': 'Second test milestone'
                }
            ]
        }
        
        print(f"\n  Applying test plan with {len(test_plan['milestones'])} milestones...")
        
        # Apply the plan
        planning_service = get_planning_service()
        result = planning_service.apply_plan(entry_id, test_plan)
        
        if not result.get('success'):
            print(f"❌ Plan application failed: {result.get('error')}")
            conn.close()
            return False
        
        print(f"✓ Plan applied successfully!")
        print(f"  - {result['message']}")
        
        # Verify milestones were created
        cursor.execute("""
            SELECT esm.*, es.name as state_name
            FROM EntryStateMilestone esm
            JOIN EntryState es ON esm.target_state_id = es.id
            WHERE esm.entry_id = ?
            ORDER BY esm.target_date DESC
            LIMIT 5
        """, (entry_id,))
        
        milestones = cursor.fetchall()
        print(f"\n  Verified {len(milestones)} milestone(s) in database:")
        for ms in milestones:
            status = "✓ Completed" if ms['is_completed'] else "○ Pending"
            print(f"    {status} {ms['state_name']} - {ms['target_date']}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("PLANNING ASSISTANT FEATURE TEST SUITE")
    print("="*60)
    
    # Create app context
    app = create_app()
    
    with app.app_context():
        results = {
            'Context Gathering': test_context_gathering(),
            'Plan Generation': test_plan_generation(),
            'Plan Application': test_plan_application()
        }
        
        print("\n" + "="*60)
        print("TEST RESULTS SUMMARY")
        print("="*60)
        
        all_passed = True
        for test_name, result in results.items():
            status = "✓ PASSED" if result else "❌ FAILED"
            print(f"{test_name:<25} {status}")
            if not result:
                all_passed = False
        
        print("="*60)
        
        if all_passed:
            print("\n🎉 All tests passed!")
            return 0
        else:
            print("\n⚠️  Some tests failed. Check the output above for details.")
            return 1


if __name__ == '__main__':
    sys.exit(main())
