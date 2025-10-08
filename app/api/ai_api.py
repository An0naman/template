"""
AI API Blueprint
Provides endpoints for AI-powered writing assistance
"""

from flask import Blueprint, request, jsonify, current_app
from app.services.ai_service import get_ai_service
import logging

logger = logging.getLogger(__name__)

ai_api_bp = Blueprint('ai_api', __name__)

@ai_api_bp.route('/ai/status', methods=['GET'])
def ai_status():
    """Check if AI service is available"""
    ai_service = get_ai_service()
    return jsonify({
        'available': ai_service.is_available(),
        'service': 'Google Gemini' if ai_service.is_available() else 'Not configured'
    })

@ai_api_bp.route('/ai/generate_description', methods=['POST'])
def generate_description():
    """Generate description for an entry"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        title = data.get('title', '').strip()
        entry_type = data.get('entry_type', '').strip()
        context = data.get('context', '').strip()
        
        if not title:
            return jsonify({'error': 'Title is required'}), 400
        
        if not entry_type:
            return jsonify({'error': 'Entry type is required'}), 400
        
        ai_service = get_ai_service()
        
        if not ai_service.is_available():
            return jsonify({'error': 'AI service is not available'}), 503
        
        description = ai_service.generate_description(title, entry_type, context)
        
        if description:
            return jsonify({
                'success': True,
                'description': description
            })
        else:
            return jsonify({'error': 'Failed to generate description'}), 500
            
    except Exception as e:
        logger.error(f"Error generating description: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@ai_api_bp.route('/ai/improve_description', methods=['POST'])
def improve_description():
    """Improve description content"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        description = data.get('description', '').strip()
        
        if not description:
            return jsonify({'error': 'Description content is required'}), 400
        
        ai_service = get_ai_service()
        
        if not ai_service.is_available():
            return jsonify({'error': 'AI service is not available'}), 503
        
        improved_description = ai_service.improve_description(description)
        
        if improved_description:
            return jsonify({
                'success': True,
                'improved_description': improved_description
            })
        else:
            return jsonify({'error': 'Failed to improve description'}), 500
            
    except Exception as e:
        logger.error(f"Error improving description: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@ai_api_bp.route('/ai/improve_note', methods=['POST'])
def improve_note():
    """Improve note content"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        note_content = data.get('content', '').strip()
        note_type = data.get('type', 'general').strip()
        
        if not note_content:
            return jsonify({'error': 'Note content is required'}), 400
        
        ai_service = get_ai_service()
        
        if not ai_service.is_available():
            return jsonify({'error': 'AI service is not available'}), 503
        
        improved_content = ai_service.improve_note(note_content, note_type)
        
        if improved_content:
            return jsonify({
                'success': True,
                'improved_content': improved_content
            })
        else:
            return jsonify({'error': 'Failed to improve note'}), 500
            
    except Exception as e:
        logger.error(f"Error improving note: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@ai_api_bp.route('/ai/generate_note', methods=['POST'])
def generate_note():
    """Generate note content based on entry and note type"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        title = data.get('title', '').strip()
        entry_type = data.get('entry_type', '').strip()
        note_type = data.get('note_type', 'general').strip()
        context = data.get('context', '').strip()
        
        if not title:
            return jsonify({'error': 'Title is required'}), 400
        
        if not entry_type:
            return jsonify({'error': 'Entry type is required'}), 400
        
        ai_service = get_ai_service()
        
        if not ai_service.is_available():
            return jsonify({'error': 'AI service is not available'}), 503
        
        note_content = ai_service.generate_note(title, entry_type, note_type, context)
        
        if note_content:
            return jsonify({
                'success': True,
                'note_content': note_content
            })
        else:
            return jsonify({'error': 'Failed to generate note content'}), 500
            
    except Exception as e:
        logger.error(f"Error generating note: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@ai_api_bp.route('/ai/generate_sql', methods=['POST'])
def generate_sql():
    """Generate SQL query from natural language"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        description = data.get('description', '').strip()
        table_info = data.get('table_info', '').strip()
        
        if not description:
            return jsonify({'error': 'Query description is required'}), 400
        
        ai_service = get_ai_service()
        
        if not ai_service.is_available():
            return jsonify({'error': 'AI service is not available'}), 503
        
        sql_query = ai_service.generate_sql_query(description, table_info)
        
        if sql_query:
            return jsonify({
                'success': True,
                'sql_query': sql_query
            })
        else:
            return jsonify({'error': 'Failed to generate SQL query'}), 500
            
    except Exception as e:
        logger.error(f"Error generating SQL: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@ai_api_bp.route('/ai/explain_sql', methods=['POST'])
def explain_sql():
    """Explain SQL query in plain English"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        sql_query = data.get('sql_query', '').strip()
        
        if not sql_query:
            return jsonify({'error': 'SQL query is required'}), 400
        
        ai_service = get_ai_service()
        
        if not ai_service.is_available():
            return jsonify({'error': 'AI service is not available'}), 503
        
        explanation = ai_service.explain_sql_query(sql_query)
        
        if explanation:
            return jsonify({
                'success': True,
                'explanation': explanation
            })
        else:
            return jsonify({'error': 'Failed to explain SQL query'}), 500
            
    except Exception as e:
        logger.error(f"Error explaining SQL: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@ai_api_bp.route('/ai/generate_theme', methods=['POST'])
def generate_theme():
    """Generate theme colors based on description"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        description = data.get('description', '').strip()
        style_preferences = data.get('style_preferences', '').strip()
        current_theme = data.get('current_theme')
        
        if not description:
            return jsonify({'error': 'Theme description is required'}), 400
        
        ai_service = get_ai_service()
        
        if not ai_service.is_available():
            return jsonify({'error': 'AI service is not available'}), 503
        
        theme_data = ai_service.generate_theme(description, style_preferences, current_theme)
        
        if theme_data:
            return jsonify({
                'success': True,
                'theme': theme_data
            })
        else:
            return jsonify({'error': 'Failed to generate theme'}), 500
            
    except Exception as e:
        logger.error(f"Error generating theme: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@ai_api_bp.route('/ai/chat_theme', methods=['POST'])
def chat_theme():
    """Conversational theme generation with chat history"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        user_message = data.get('message', '').strip()
        conversation_history = data.get('conversation_history', [])
        current_theme = data.get('current_theme')
        
        if not user_message:
            return jsonify({'error': 'Message is required'}), 400
        
        ai_service = get_ai_service()
        
        if not ai_service.is_available():
            return jsonify({'error': 'AI service is not available'}), 503
        
        # Use the chat method for theme generation
        response = ai_service.chat_theme_generation(user_message, conversation_history, current_theme)
        
        if response:
            return jsonify({
                'success': True,
                'response': response
            })
        else:
            return jsonify({'error': 'Failed to generate response'}), 500
            
    except Exception as e:
        logger.error(f"Error in chat theme: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@ai_api_bp.route('/ai/entry-chat', methods=['POST'])
def entry_chat():
    """Chat with AI about a specific entry with full context"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        entry_id = data.get('entry_id')
        user_message = data.get('message', '').strip()
        is_first_message = data.get('is_first_message', False)
        include_all_notes = data.get('include_all_notes', False)
        
        if not entry_id:
            return jsonify({'error': 'Entry ID is required'}), 400
        
        if not user_message:
            return jsonify({'error': 'Message is required'}), 400
        
        ai_service = get_ai_service()
        
        if not ai_service.is_available():
            return jsonify({'error': 'AI service is not available. Please configure Gemini API key in settings.'}), 503
        
        # Chat about the entry with full context
        response = ai_service.chat_about_entry(entry_id, user_message, is_first_message, include_all_notes)
        
        if response:
            return jsonify({
                'success': True,
                'response': response
            })
        else:
            return jsonify({'error': 'Failed to generate response'}), 500
            
    except Exception as e:
        logger.error(f"Error in entry chat: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500
