"""
AI API Blueprint
Provides endpoints for AI-powered writing assistance
"""

from flask import Blueprint, request, jsonify, current_app
from app.services.ai_service import get_ai_service
import sqlite3
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

def clean_ai_response(text: str) -> str:
    """Remove conversational wrapper text from AI responses"""
    if not text:
        return text
    
    # List of common conversational prefixes to remove
    prefixes_to_remove = [
        "Here's an improved version of the description:",
        "Here's the improved description:",
        "Here's an improved description:",
        "Improved description:",
        "Here's a better version:",
        "Here is an improved version:",
        "Here's a more concise version:",
        "Concise version:",
        "Here's the concise description:",
        "Here's a more detailed version:",
        "Expanded version:",
        "Here's the detailed description:",
        "Here's the revised version:",
        "Revised:",
        "Updated version:",
        "Here is the improved version:",
        "Here is an improved version of the description:",
        "Here's",
        "Here is",
    ]
    
    cleaned = text.strip()
    
    # Try to remove prefixes (case-insensitive)
    for prefix in prefixes_to_remove:
        if cleaned.lower().startswith(prefix.lower()):
            cleaned = cleaned[len(prefix):].strip()
            # Remove leading colons or dashes
            cleaned = cleaned.lstrip(':').lstrip('-').strip()
            break
    
    # Remove any markdown triple backticks or code blocks
    if cleaned.startswith('```'):
        lines = cleaned.split('\n')
        if len(lines) > 2:
            # Remove first and last lines if they're code fence markers
            if lines[0].startswith('```') and lines[-1].startswith('```'):
                cleaned = '\n'.join(lines[1:-1])
    
    # Replace asterisks with hyphens for bullet points
    import re
    
    # Replace asterisks at start of lines (with optional whitespace)
    cleaned = re.sub(r'^(\s*)\*(\s+)', r'\1-\2', cleaned, flags=re.MULTILINE)
    
    # Replace asterisks after newlines
    cleaned = re.sub(r'(\n\s*)\*(\s+)', r'\1-\2', cleaned)
    
    # Replace any remaining asterisks that look like bullets (asterisk followed by space)
    cleaned = re.sub(r'\*(\s+)', r'-\1', cleaned)
    
    # Also handle bold/italic markdown - preserve those
    # Don't replace ** or * when used for emphasis (surrounded by non-whitespace)
    # This is already handled by the above patterns which require a space after *
    
    return cleaned.strip()


@ai_api_bp.route('/ai/chat', methods=['POST'])
def ai_chat():
    """AI assistant chat with description preview capability"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        message = data.get('message', '').strip()
        entry_id = data.get('entry_id')
        entry_title = data.get('entry_title', '').strip()
        entry_description = data.get('entry_description', '').strip()
        action = data.get('action', '').strip()
        current_draft = data.get('current_draft', '').strip()  # For draft refinement
        
        if not message:
            return jsonify({'error': 'Message is required'}), 400
        
        ai_service = get_ai_service()
        
        if not ai_service.is_available():
            return jsonify({'error': 'AI service is not available. Please configure Gemini API key in settings.'}), 503
        
        # Handle different actions
        description_preview = None
        ai_response = None
        entry_type = 'general'
        
        # Get entry type if entry_id is provided
        if entry_id:
            try:
                from flask import g
                if 'db' not in g:
                    db_path = current_app.config['DATABASE_PATH']
                    g.db = sqlite3.connect(db_path)
                    g.db.row_factory = sqlite3.Row
                
                cursor = g.db.cursor()
                cursor.execute('SELECT et.singular_label FROM entries e JOIN entry_types et ON e.entry_type_id = et.id WHERE e.id = ?', (entry_id,))
                row = cursor.fetchone()
                if row:
                    entry_type = row['singular_label']
            except Exception as e:
                logger.warning(f"Could not fetch entry type: {e}")
        
        if action == 'generate_description':
            # Generate new description
            generated = ai_service.generate_description(entry_title, entry_type, message)
            description_preview = clean_ai_response(generated) if generated else None
            ai_response = "I've generated a description for you. You can refine it by telling me what to change, or click 'Apply to Entry' when you're ready."
            
        elif action == 'improve_description':
            if not entry_description:
                return jsonify({'error': 'No description to improve'}), 400
            
            # Improve existing description
            improved = ai_service.improve_description(entry_description)
            description_preview = clean_ai_response(improved) if improved else None
            
            if description_preview:
                ai_response = "I've improved the description. Let me know if you'd like me to make any changes, or click 'Apply to Entry' to save it."
            else:
                ai_response = "I wasn't able to improve the description. Please try again."
            
        elif action == 'make_concise':
            if not entry_description:
                return jsonify({'error': 'No description to make concise'}), 400
            
            # Make description more concise
            improved = ai_service.improve_description(entry_description)
            description_preview = clean_ai_response(improved) if improved else None
            
            if description_preview:
                ai_response = "I've made the description more concise. Tell me if you want any adjustments, or click 'Apply to Entry' to save it."
            else:
                ai_response = "I wasn't able to make the description more concise. Please try again."
            
        elif action == 'add_details':
            if not entry_description:
                return jsonify({'error': 'No description to expand'}), 400
            
            # Add more details
            improved = ai_service.improve_description(entry_description)
            description_preview = clean_ai_response(improved) if improved else None
            
            if description_preview:
                ai_response = "I've added more details to the description. Let me know if you want further changes, or click 'Apply to Entry' when ready."
            else:
                ai_response = "I wasn't able to add more details. Please try again."
            
        elif action == 'wikipedia':
            # Fetch Wikipedia summary
            context = f"Provide a Wikipedia-style summary for: {entry_title}"
            generated = ai_service.generate_description(entry_title, entry_type, context)
            description_preview = clean_ai_response(generated) if generated else None
            ai_response = "I've created a Wikipedia-style description. You can refine it by asking me to make changes, or click 'Apply to Entry' to save it."
            
        elif action == 'refine_draft':
            # Refine an existing draft based on user feedback
            if not current_draft:
                return jsonify({'error': 'No draft to refine'}), 400
            
            # Use the improve_description with context from the user's message
            # The AI will take the current draft and apply the user's requested changes
            refined = ai_service.improve_description(f"{current_draft}\n\nUser feedback: {message}")
            description_preview = clean_ai_response(refined) if refined else None
            
            if description_preview:
                ai_response = f"I've updated the draft based on your feedback. Continue to refine it or click 'Apply to Entry' when you're satisfied."
            else:
                ai_response = "I wasn't able to refine the draft. Please try rephrasing your request."
            
        else:
            # General chat - just respond to the message
            ai_response = ai_service.chat_about_entry(entry_id, message, is_first_message=True, include_all_notes=False) if entry_id else message
        
        # Build response
        response_data = {
            'message': ai_response or "I'm here to help! How can I assist you with this entry?"
        }
        
        if description_preview:
            response_data['description_preview'] = description_preview
        
        return jsonify(response_data)
            
    except Exception as e:
        logger.error(f"Error in AI chat: {str(e)}", exc_info=True)
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500
