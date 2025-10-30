"""
Planning Service for Milestone Generation
Provides intelligent milestone planning based on entry context and AI assistance
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
from app.services.ai_service import get_ai_service
from app.db import get_connection

logger = logging.getLogger(__name__)


class PlanningService:
    """Service for generating and managing milestone plans"""
    
    def __init__(self):
        self.ai_service = get_ai_service()
    
    def gather_entry_context(self, entry_id: int) -> Dict[str, Any]:
        """
        Gather all relevant context for planning
        
        Args:
            entry_id: The entry to gather context for
            
        Returns:
            Dictionary containing all planning context
        """
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            # Get entry details
            cursor.execute("""
                SELECT e.*, et.name as entry_type_name, et.singular_label as entry_type_label,
                       es.name as current_status, es.color as status_color
                FROM Entry e
                JOIN EntryType et ON e.entry_type_id = et.id
                LEFT JOIN EntryState es ON es.entry_type_id = e.entry_type_id AND es.name = e.status
                WHERE e.id = ?
            """, (entry_id,))
            
            entry_row = cursor.fetchone()
            if not entry_row:
                return {}
            
            entry = dict(entry_row)
            
            # Get available states for this entry type
            cursor.execute("""
                SELECT id, name, color, category, display_order
                FROM EntryState
                WHERE entry_type_id = ?
                ORDER BY display_order
            """, (entry['entry_type_id'],))
            
            available_states = [dict(row) for row in cursor.fetchall()]
            
            # Get existing milestones
            cursor.execute("""
                SELECT esm.*, es.name as state_name, es.color as state_color,
                       date(e.created_at, '+' || esm.days_from_start || ' days') as target_date
                FROM EntryStateMilestone esm
                JOIN EntryState es ON esm.target_state_id = es.id
                JOIN Entry e ON esm.entry_id = e.id
                WHERE esm.entry_id = ? AND esm.is_completed = 0
                ORDER BY esm.order_position
            """, (entry_id,))
            
            existing_milestones = [dict(row) for row in cursor.fetchall()]
            
            # Get notes (last 20 to avoid overload)
            cursor.execute("""
                SELECT note_title as title, note_text as content, type as note_type, created_at
                FROM Note
                WHERE entry_id = ?
                ORDER BY created_at DESC
                LIMIT 20
            """, (entry_id,))
            
            notes = [dict(row) for row in cursor.fetchall()]
            
            # Get custom field values (if table exists)
            custom_fields = []
            try:
                cursor.execute("""
                    SELECT cf.label, cfv.value, cf.field_type
                    FROM CustomFieldValue cfv
                    JOIN CustomField cf ON cfv.field_id = cf.id
                    WHERE cfv.entry_id = ?
                """, (entry_id,))
                custom_fields = [dict(row) for row in cursor.fetchall()]
            except Exception:
                # Table doesn't exist, skip custom fields
                pass
            
            # Get related entries (if table exists)
            related_entries = []
            try:
                cursor.execute("""
                    SELECT e.id, e.title, et.name as entry_type_name
                    FROM EntryRelationship er
                    JOIN Entry e ON (er.source_entry_id = e.id OR er.target_entry_id = e.id)
                    JOIN EntryType et ON e.entry_type_id = et.id
                    WHERE (er.source_entry_id = ? OR er.target_entry_id = ?)
                      AND e.id != ?
                    LIMIT 10
                """, (entry_id, entry_id, entry_id))
                related_entries = [dict(row) for row in cursor.fetchall()]
            except Exception:
                # Table doesn't exist or query failed, skip relationships
                pass
            
            # Get sensor data summary (if available)
            sensor_summary = None
            try:
                cursor.execute("""
                    SELECT sensor_type, COUNT(*) as reading_count,
                           MIN(timestamp) as first_reading,
                           MAX(timestamp) as last_reading
                    FROM SensorData
                    WHERE entry_id = ?
                    GROUP BY sensor_type
                """, (entry_id,))
                
                sensor_summary = [dict(row) for row in cursor.fetchall()]
            except Exception:
                # Sensor table might not exist
                pass
            
            # Find similar completed entries for pattern learning
            try:
                cursor.execute("""
                    SELECT e.id, e.title, e.created_at, e.actual_end_date,
                           julianday(COALESCE(e.actual_end_date, e.created_at)) - julianday(e.created_at) as duration_days
                    FROM Entry e
                    JOIN EntryState es ON es.entry_type_id = e.entry_type_id AND es.name = e.status
                    WHERE e.entry_type_id = ?
                      AND es.name = 'Completed'
                      AND e.id != ?
                    ORDER BY e.actual_end_date DESC
                    LIMIT 5
                """, (entry['entry_type_id'], entry_id))
                
                similar_entries = [dict(row) for row in cursor.fetchall()]
            except Exception:
                # If query fails, just use empty list
                similar_entries = []
            
            conn.close()
            
            return {
                'entry': entry,
                'available_states': available_states,
                'existing_milestones': existing_milestones,
                'notes': notes,
                'custom_fields': custom_fields,
                'related_entries': related_entries,
                'sensor_summary': sensor_summary,
                'similar_entries': similar_entries
            }
            
        except Exception as e:
            logger.error(f"Error gathering entry context: {str(e)}")
            return {}
    
    def generate_plan(self, entry_id: int, user_prompt: str = "") -> Dict[str, Any]:
        """
        Generate a milestone plan using AI
        
        Args:
            entry_id: The entry to plan for
            user_prompt: Optional user instructions/preferences
            
        Returns:
            Dictionary containing proposed plan
        """
        if not self.ai_service.is_available():
            return {
                'success': False,
                'error': 'AI service is not available'
            }
        
        try:
            # Gather context
            context = self.gather_entry_context(entry_id)
            
            if not context:
                return {
                    'success': False,
                    'error': 'Could not gather entry context'
                }
            
            # Build prompt for AI
            prompt = self._build_planning_prompt(context, user_prompt)
            
            # Get AI response
            response = self.ai_service.model.generate_content(prompt)
            
            if not response or not response.text:
                return {
                    'success': False,
                    'error': 'No response from AI service'
                }
            
            # Parse the response
            plan = self._parse_ai_response(response.text, context)
            
            return {
                'success': True,
                'plan': plan,
                'context_summary': self._build_context_summary(context),
                'confidence': plan.get('confidence', 0.8)
            }
            
        except Exception as e:
            logger.error(f"Error generating plan: {str(e)}")
            return {
                'success': False,
                'error': f'Failed to generate plan: {str(e)}'
            }
    
    def _build_planning_prompt(self, context: Dict[str, Any], user_prompt: str) -> str:
        """Build the AI prompt for plan generation"""
        
        entry = context['entry']
        available_states = context['available_states']
        existing_milestones = context['existing_milestones']
        similar_entries = context['similar_entries']
        custom_fields = context['custom_fields']
        notes = context['notes']
        
        # Calculate average duration from similar entries
        avg_duration = None
        if similar_entries:
            durations = [e['duration_days'] for e in similar_entries if e.get('duration_days')]
            if durations:
                avg_duration = sum(durations) / len(durations)
        
        prompt = f"""You are an expert project planning assistant. Your task is to create a milestone plan for a project entry.

ENTRY INFORMATION:
- Title: {entry['title']}
- Type: {entry['entry_type_name']}
- Current Status: {entry['current_status']}
- Created: {entry['created_at']}
- Intended End Date: {entry.get('intended_end_date', 'Not set')}
- Description: {entry.get('description', 'No description')}

AVAILABLE STATUS TRANSITIONS:
"""
        
        # List available states
        current_found = False
        for state in available_states:
            if state['name'] == entry['current_status']:
                current_found = True
                prompt += f"- {state['name']} (CURRENT)\n"
            elif current_found:
                prompt += f"- {state['name']}\n"
        
        # Add custom field information
        if custom_fields:
            prompt += "\nCUSTOM FIELD DATA:\n"
            for field in custom_fields:
                prompt += f"- {field['label']}: {field['value']}\n"
        
        # Add notes context
        if notes:
            prompt += f"\nRECENT NOTES ({len(notes)} total):\n"
            for note in notes[:5]:  # Only include first 5
                prompt += f"- [{note['note_type']}] {note['title']}: {note['content'][:100]}\n"
        
        # Add historical context
        if similar_entries:
            prompt += f"\nHISTORICAL DATA:\n"
            prompt += f"Based on {len(similar_entries)} similar completed {entry['entry_type_name']} entries:\n"
            if avg_duration:
                prompt += f"- Average duration: {avg_duration:.1f} days\n"
            for sim in similar_entries[:3]:
                prompt += f"- '{sim['title']}' took {sim.get('duration_days', 'unknown'):.0f} days\n"
        
        # Add existing milestones if any
        if existing_milestones:
            prompt += f"\nEXISTING MILESTONES:\n"
            for ms in existing_milestones:
                prompt += f"- {ms['state_name']} on {ms['target_date']}\n"
        
        # Add user's specific request
        if user_prompt:
            prompt += f"\nUSER REQUEST:\n{user_prompt}\n"
        
        prompt += """

TASK:
Create a detailed milestone plan with realistic timelines. For each milestone, specify:
1. Target status name (must be from available states list)
2. Target date (format: YYYY-MM-DD)
3. Duration estimate in days
4. Brief notes explaining the reasoning

Consider:
- Current status and where to go next
- Intended end date as a constraint
- Typical timelines for this type of project
- Dependencies between phases
- Buffer time for unexpected delays

Respond ONLY with valid JSON in this exact format:
{
  "title": "Brief plan title",
  "duration_total_days": 21,
  "reasoning": "Overall explanation of the timeline",
  "confidence": 0.85,
  "milestones": [
    {
      "status_name": "Secondary Ferment",
      "target_date": "2025-11-08",
      "duration_days": 7,
      "notes": "Allow yeast to settle and flavors to develop"
    }
  ]
}

Generate the plan now:"""
        
        return prompt
    
    def _parse_ai_response(self, response_text: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Parse AI response into structured plan"""
        try:
            # Try to extract JSON from response
            # Sometimes AI wraps JSON in markdown code blocks
            text = response_text.strip()
            
            if '```json' in text:
                text = text.split('```json')[1].split('```')[0].strip()
            elif '```' in text:
                text = text.split('```')[1].split('```')[0].strip()
            
            plan = json.loads(text)
            
            # Validate and enrich the plan
            available_states = {s['name']: s for s in context['available_states']}
            
            for milestone in plan.get('milestones', []):
                # Add state_id if state exists
                state_name = milestone.get('status_name', '')
                if state_name in available_states:
                    milestone['state_id'] = available_states[state_name]['id']
                    milestone['state_color'] = available_states[state_name]['color']
                else:
                    logger.warning(f"Status '{state_name}' not found in available states")
            
            return plan
            
        except Exception as e:
            logger.error(f"Error parsing AI response: {str(e)}")
            logger.error(f"Response text: {response_text}")
            
            # Return a fallback plan
            return {
                'title': 'Basic Plan',
                'duration_total_days': 14,
                'reasoning': 'AI response could not be parsed. This is a basic fallback plan.',
                'confidence': 0.5,
                'milestones': [],
                'parse_error': str(e),
                'raw_response': response_text
            }
    
    def _build_context_summary(self, context: Dict[str, Any]) -> str:
        """Build a human-readable context summary"""
        entry = context['entry']
        summary_parts = []
        
        summary_parts.append(f"Analyzing {entry['entry_type_name']}: '{entry['title']}'")
        summary_parts.append(f"Current Status: {entry['current_status']}")
        
        if entry.get('intended_end_date'):
            summary_parts.append(f"Target End Date: {entry['intended_end_date']}")
        
        if context.get('existing_milestones'):
            summary_parts.append(f"{len(context['existing_milestones'])} existing milestones")
        
        if context.get('notes'):
            summary_parts.append(f"{len(context['notes'])} notes recorded")
        
        if context.get('similar_entries'):
            summary_parts.append(f"Found {len(context['similar_entries'])} similar completed entries")
        
        return " • ".join(summary_parts)
    
    def apply_plan(self, entry_id: int, plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply an approved plan by creating milestones
        
        Args:
            entry_id: The entry to apply plan to
            plan: The plan data with milestones
            
        Returns:
            Result dictionary with success status
        """
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            milestones = plan.get('milestones', [])
            
            if not milestones:
                return {
                    'success': False,
                    'error': 'No milestones in plan'
                }
            
            # Clear existing incomplete milestones before applying new plan
            cursor.execute("""
                DELETE FROM EntryStateMilestone
                WHERE entry_id = ? AND is_completed = 0
            """, (entry_id,))
            
            logger.info(f"Cleared existing incomplete milestones for entry {entry_id}")
            
            created_count = 0
            cumulative_days = 0
            for idx, milestone in enumerate(milestones):
                # Validate required fields
                if not milestone.get('state_id'):
                    logger.warning(f"Skipping invalid milestone: {milestone}")
                    continue
                
                # Calculate days_from_start
                duration = milestone.get('duration_days', 7)
                cumulative_days += duration
                
                # Create milestone
                cursor.execute("""
                    INSERT INTO EntryStateMilestone
                    (entry_id, target_state_id, days_from_start, duration_days, notes, is_completed, order_position)
                    VALUES (?, ?, ?, ?, ?, 0, ?)
                """, (
                    entry_id,
                    milestone['state_id'],
                    cumulative_days,
                    duration,
                    milestone.get('notes', ''),
                    idx
                ))
                
                created_count += 1
            
            conn.commit()
            
            # Create a system note documenting the plan application
            cursor.execute("""
                INSERT INTO Note (entry_id, note_title, note_text, type, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (
                entry_id,
                'Milestone Plan Applied',
                f"AI-generated milestone plan applied: {plan.get('title', 'Untitled Plan')}. {created_count} milestones created.",
                'System',
                datetime.now().isoformat()
            ))
            
            conn.commit()
            conn.close()
            
            return {
                'success': True,
                'milestones_created': created_count,
                'message': f'Successfully created {created_count} milestone(s)'
            }
            
        except Exception as e:
            logger.error(f"Error applying plan: {str(e)}")
            return {
                'success': False,
                'error': f'Failed to apply plan: {str(e)}'
            }


# Global service instance
_planning_service = None

def get_planning_service() -> PlanningService:
    """Get or create the global planning service instance"""
    global _planning_service
    if _planning_service is None:
        _planning_service = PlanningService()
    return _planning_service
