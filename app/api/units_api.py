from flask import Blueprint, jsonify, request
from app.utils.units import get_unit_suggestions, get_unit_suggestions_by_category, suggest_units_for_relationship

units_api_bp = Blueprint('units_api', __name__)

@units_api_bp.route('/api/units/suggestions', methods=['GET'])
def get_units_suggestions():
    """Get all available unit suggestions"""
    try:
        # Check if client wants categorized results
        categorized = request.args.get('categorized', 'false').lower() == 'true'
        
        if categorized:
            suggestions = get_unit_suggestions_by_category()
        else:
            suggestions = get_unit_suggestions()
        
        return jsonify({
            'success': True,
            'units': suggestions
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@units_api_bp.route('/api/units/suggestions/relationship', methods=['POST'])
def get_relationship_unit_suggestions():
    """Get unit suggestions based on relationship context"""
    try:
        data = request.get_json()
        relationship_name = data.get('relationship_name', '')
        from_type = data.get('from_type', '')
        to_type = data.get('to_type', '')
        
        suggestions = suggest_units_for_relationship(
            relationship_name=relationship_name,
            from_type=from_type,
            to_type=to_type
        )
        
        return jsonify({
            'success': True,
            'suggestions': suggestions
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
