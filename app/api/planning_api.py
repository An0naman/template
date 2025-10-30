"""
Planning API Blueprint
Provides endpoints for AI-powered milestone planning
"""

from flask import Blueprint, request, jsonify
from app.services.planning_service import get_planning_service
import logging

logger = logging.getLogger(__name__)

planning_api_bp = Blueprint('planning_api', __name__)


@planning_api_bp.route('/api/entries/<int:entry_id>/generate_plan', methods=['POST'])
def generate_plan(entry_id):
    """
    Generate a milestone plan for an entry using AI
    
    Request body:
    {
        "prompt": "optional user instructions",
        "conversation_context": [...] // optional chat history
    }
    
    Response:
    {
        "success": true,
        "plan": {
            "title": "Plan name",
            "duration_total_days": 21,
            "reasoning": "Explanation",
            "confidence": 0.85,
            "milestones": [...]
        },
        "context_summary": "Summary of analysis"
    }
    """
    try:
        data = request.get_json() or {}
        user_prompt = data.get('prompt', '')
        
        planning_service = get_planning_service()
        result = planning_service.generate_plan(entry_id, user_prompt)
        
        if result.get('success'):
            return jsonify(result)
        else:
            return jsonify(result), 500
            
    except Exception as e:
        logger.error(f"Error in generate_plan endpoint: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Internal server error: {str(e)}'
        }), 500


@planning_api_bp.route('/api/entries/<int:entry_id>/apply_plan', methods=['POST'])
def apply_plan(entry_id):
    """
    Apply an approved milestone plan to an entry
    
    Request body:
    {
        "plan": {
            "milestones": [
                {
                    "state_id": 123,
                    "target_date": "2025-11-08",
                    "duration_days": 7,
                    "notes": "Reasoning"
                }
            ]
        }
    }
    
    Response:
    {
        "success": true,
        "milestones_created": 4,
        "message": "Successfully created 4 milestones"
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'plan' not in data:
            return jsonify({
                'success': False,
                'error': 'Plan data is required'
            }), 400
        
        plan = data['plan']
        
        planning_service = get_planning_service()
        result = planning_service.apply_plan(entry_id, plan)
        
        if result.get('success'):
            return jsonify(result)
        else:
            return jsonify(result), 500
            
    except Exception as e:
        logger.error(f"Error in apply_plan endpoint: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Internal server error: {str(e)}'
        }), 500


@planning_api_bp.route('/api/entries/<int:entry_id>/planning_context', methods=['GET'])
def get_planning_context(entry_id):
    """
    Get context information for planning (for debugging/preview)
    
    Response:
    {
        "entry": {...},
        "available_states": [...],
        "existing_milestones": [...],
        "notes": [...],
        "context_summary": "..."
    }
    """
    try:
        planning_service = get_planning_service()
        context = planning_service.gather_entry_context(entry_id)
        
        if context:
            return jsonify({
                'success': True,
                'context': context,
                'context_summary': planning_service._build_context_summary(context)
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Could not gather context'
            }), 404
            
    except Exception as e:
        logger.error(f"Error in get_planning_context endpoint: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Internal server error: {str(e)}'
        }), 500
