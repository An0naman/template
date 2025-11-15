"""
AI API Blueprint
Provides endpoints for AI-powered writing assistance
"""

from flask import Blueprint, request, jsonify, current_app, g
from app.services.ai_service import get_ai_service
import sqlite3
import logging

logger = logging.getLogger(__name__)

def get_db():
    if 'db' not in g:
        db_path = current_app.config['DATABASE_PATH']
        g.db = sqlite3.connect(db_path)
        g.db.row_factory = sqlite3.Row
    return g.db

ai_api_bp = Blueprint('ai_api', __name__)

@ai_api_bp.route('/ai/models', methods=['GET'])
def get_available_models():
    """Get list of available Gemini models"""
    try:
        import google.generativeai as genai
        
        # List of available Gemini models with metadata
        # Updated for Gemini 2.x series (current as of 2025)
        models = [
            {
                'id': 'gemini-2.5-flash',
                'name': 'Gemini 2.5 Flash',
                'description': 'Fast and efficient - Best for most use cases',
                'recommended': True
            },
            {
                'id': 'gemini-2.5-pro',
                'name': 'Gemini 2.5 Pro',
                'description': 'Most capable - Advanced reasoning',
                'recommended': False
            },
            {
                'id': 'gemini-2.0-flash',
                'name': 'Gemini 2.0 Flash',
                'description': 'Stable flash model',
                'recommended': False
            },
            {
                'id': 'gemini-flash-latest',
                'name': 'Gemini Flash (Latest)',
                'description': 'Auto-updates to latest flash model',
                'recommended': False
            }
        ]
        
        return jsonify({
            'models': models,
            'default': 'gemini-1.5-flash'
        })
        
    except Exception as e:
        logger.error(f"Failed to fetch models: {str(e)}")
        # Fallback to static list if API call fails
        return jsonify({
            'models': [
                {
                    'id': 'gemini-1.5-flash',
                    'name': 'Gemini 1.5 Flash',
                    'description': 'Fast and efficient',
                    'recommended': True
                }
            ],
            'default': 'gemini-1.5-flash'
        })

@ai_api_bp.route('/ai/status', methods=['GET'])
def ai_status():
    """Check if AI service is available"""
    ai_service = get_ai_service()
    return jsonify({
        'available': ai_service.is_available(),
        'service': 'Google Gemini' if ai_service.is_available() else 'Not configured'
    })

@ai_api_bp.route('/ai/reconfigure', methods=['POST'])
def reconfigure_ai():
    """Force reconfiguration of AI service (useful after settings change)"""
    try:
        ai_service = get_ai_service()
        success = ai_service.reconfigure()
        
        if success:
            return jsonify({
                'success': True,
                'message': 'AI service successfully reconfigured',
                'available': True
            })
        else:
            return jsonify({
                'success': False,
                'message': 'AI service reconfiguration failed - check API key configuration',
                'available': False
            })
    except Exception as e:
        logger.error(f"Error reconfiguring AI service: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

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
        diagram_xml = data.get('diagram_xml', '').strip()
        
        if not entry_id:
            return jsonify({'error': 'Entry ID is required'}), 400
        
        if not user_message:
            return jsonify({'error': 'Message is required'}), 400
        
        ai_service = get_ai_service()
        
        if not ai_service.is_available():
            return jsonify({'error': 'AI service is not available. Please configure Gemini API key in settings.'}), 503
        
        # Build debug info
        debug_info = {
            'entry_id': entry_id,
            'has_diagram': bool(diagram_xml),
            'entry_type': None,
            'action': None,
            'section_prompt': None,
            'prompt_layers': ['Base System Prompt', 'Chat Template']
        }
        
        # Get entry type for debug info
        try:
            from flask import g
            if 'db' not in g:
                db_path = current_app.config['DATABASE_PATH']
                g.db = sqlite3.connect(db_path)
                g.db.row_factory = sqlite3.Row
            
            cursor = g.db.cursor()
            cursor.execute('SELECT et.singular_label, et.custom_chat_prompt FROM Entry e JOIN EntryType et ON e.entry_type_id = et.id WHERE e.id = ?', (entry_id,))
            row = cursor.fetchone()
            if row:
                debug_info['entry_type'] = row['singular_label']
                if row['custom_chat_prompt']:
                    debug_info['section_prompt'] = row['custom_chat_prompt']
                    debug_info['prompt_layers'].append('Entry Type Custom Prompt')
        except Exception as e:
            logger.warning(f"Could not fetch entry type for debug info: {e}")
        
        # Build full prompt for debug
        from ..db import get_system_parameters
        params = get_system_parameters()
        
        # Get base prompt
        base_prompt = params.get('prompt_base', 'You are a helpful AI assistant.')
        
        # Get chat template  
        chat_template = params.get('prompt_chat', 'You are an AI assistant helping with {project_desc}.')
        
        # Build full prompt preview
        full_prompt_parts = [f"=== BASE SYSTEM PROMPT ===\n{base_prompt}\n"]
        full_prompt_parts.append(f"=== CHAT TEMPLATE ===\n{chat_template}\n")
        
        if debug_info.get('section_prompt'):
            full_prompt_parts.append(f"=== CUSTOM PROMPT ===\n{debug_info['section_prompt']}\n")
        
        full_prompt_parts.append(f"=== USER MESSAGE ===\n{user_message}")
        
        if diagram_xml:
            diagram_context = _extract_diagram_context(diagram_xml)
            full_prompt_parts.append(f"\n=== DIAGRAM CONTEXT ===\n{diagram_context}")
        
        debug_info['full_prompt'] = '\n'.join(full_prompt_parts)
        
        # If diagram XML is provided, include it in the context
        if diagram_xml:
            logger.info(f"Including diagram context with entry chat for entry {entry_id}")
            
            # Parse diagram to extract basic info
            diagram_context = _extract_diagram_context(diagram_xml)
            
            # Prepend diagram context to the user message
            enhanced_message = f"""[Context: The user has included their current Draw.io diagram with this message]

{diagram_context}

User's question/message: {user_message}"""
            
            response = ai_service.chat_about_entry(entry_id, enhanced_message, is_first_message, include_all_notes)
        else:
            # Chat about the entry with full context (no diagram)
            response = ai_service.chat_about_entry(entry_id, user_message, is_first_message, include_all_notes)
        
        if response:
            return jsonify({
                'success': True,
                'response': response,
                'debug_info': debug_info
            })
        else:
            return jsonify({'error': 'Failed to generate response'}), 500
            
    except Exception as e:
        logger.error(f"Error in entry chat: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

def _extract_diagram_context(diagram_xml: str) -> str:
    """Extract basic context from diagram XML for AI understanding"""
    import xml.etree.ElementTree as ET
    
    try:
        root = ET.fromstring(diagram_xml)
        
        # Count elements
        cells = root.findall('.//{http://www.jgraph.com/}mxCell') + root.findall('.//mxCell')
        vertices = [cell for cell in cells if cell.get('vertex') == '1']
        edges = [cell for cell in cells if cell.get('edge') == '1']
        
        # Extract labels
        labels = []
        for cell in cells:
            value = cell.get('value', '')
            if value and value.strip():
                labels.append(value.strip())
        
        # Build context string
        context_parts = []
        context_parts.append(f"Diagram structure: {len(vertices)} shapes/nodes, {len(edges)} connections")
        
        if labels:
            context_parts.append(f"Key elements/labels: {', '.join(labels[:15])}")  # Limit to first 15 labels
            if len(labels) > 15:
                context_parts.append(f"... and {len(labels) - 15} more elements")
        
        return "\n".join(context_parts)
        
    except Exception as e:
        logger.warning(f"Could not parse diagram XML: {str(e)}")
        return "Diagram included (structure could not be parsed)"


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
        diagram_xml = data.get('diagram_xml', '').strip()  # Optional diagram context
        
        if not message:
            return jsonify({'error': 'Message is required'}), 400
        
        ai_service = get_ai_service()
        
        if not ai_service.is_available():
            return jsonify({'error': 'AI service is not available. Please configure Gemini API key in settings.'}), 503
        
        # If diagram XML is provided, enhance the message with diagram context
        original_message = message
        if diagram_xml and not action:  # Only add diagram context for general chat, not for actions
            logger.info(f"Including diagram context with chat message")
            diagram_context = _extract_diagram_context(diagram_xml)
            message = f"""[Context: The user has included their current Draw.io diagram]

{diagram_context}

User's message: {original_message}"""
        
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
                cursor.execute('SELECT et.singular_label FROM Entry e JOIN EntryType et ON e.entry_type_id = et.id WHERE e.id = ?', (entry_id,))
                row = cursor.fetchone()
                if row:
                    entry_type = row['singular_label']
            except Exception as e:
                logger.warning(f"Could not fetch entry type: {e}")
        
        # Get section config for custom prompts
        section_config = data.get('section_config')
        
        if action == 'generate_description':
            # Generate new description
            generated = ai_service.generate_description(entry_title, entry_type, message, section_config)
            description_preview = clean_ai_response(generated) if generated else None
            ai_response = "I've generated a description for you. You can refine it by telling me what to change, or click 'Apply to Entry' when you're ready."
            
        elif action == 'improve_description':
            if not entry_description:
                return jsonify({'error': 'No description to improve'}), 400
            
            # Improve existing description
            improved = ai_service.improve_description(entry_description, section_config)
            description_preview = clean_ai_response(improved) if improved else None
            
            if description_preview:
                ai_response = "I've improved the description. Let me know if you'd like me to make any changes, or click 'Apply to Entry' to save it."
            else:
                ai_response = "I wasn't able to improve the description. Please try again."
            
        elif action == 'make_concise':
            if not entry_description:
                return jsonify({'error': 'No description to make concise'}), 400
            
            # Make description more concise
            improved = ai_service.improve_description(entry_description, section_config)
            description_preview = clean_ai_response(improved) if improved else None
            
            if description_preview:
                ai_response = "I've made the description more concise. Tell me if you want any adjustments, or click 'Apply to Entry' to save it."
            else:
                ai_response = "I wasn't able to make the description more concise. Please try again."
            
        elif action == 'add_details':
            if not entry_description:
                return jsonify({'error': 'No description to expand'}), 400
            
            # Add more details
            improved = ai_service.improve_description(entry_description, section_config)
            description_preview = clean_ai_response(improved) if improved else None
            
            if description_preview:
                ai_response = "I've added more details to the description. Let me know if you want further changes, or click 'Apply to Entry' when ready."
            else:
                ai_response = "I wasn't able to add more details. Please try again."
            
        elif action == 'wikipedia':
            # Fetch Wikipedia summary
            context = f"Provide a Wikipedia-style summary for: {entry_title}"
            generated = ai_service.generate_description(entry_title, entry_type, context, section_config)
            description_preview = clean_ai_response(generated) if generated else None
            ai_response = "I've created a Wikipedia-style description. You can refine it by asking me to make changes, or click 'Apply to Entry' to save it."
        
        elif action == 'compose_note':
            # Compose a note with AI assistance
            note_context = data.get('note_context', {})
            attachment_files = data.get('attachment_files', [])
            chat_history = data.get('chat_history', [])
            
            note_proposal = ai_service.compose_note(entry_id, message, note_context, attachment_files, chat_history)
            
            if note_proposal and 'error' not in note_proposal:
                # Return the note proposal as a special response type
                return jsonify({
                    'message': note_proposal.get('reasoning', "I've composed a note for you. You can continue chatting to refine it, or click 'Apply Note' when you're ready."),
                    'note_preview': note_proposal
                })
            else:
                ai_response = f"I wasn't able to compose the note: {note_proposal.get('error', 'Unknown error')}"
            
        elif action == 'refine_draft':
            # Refine an existing draft based on user feedback
            if not current_draft:
                return jsonify({'error': 'No draft to refine'}), 400
            
            # Use the improve_description with context from the user's message
            # The AI will take the current draft and apply the user's requested changes
            refined = ai_service.improve_description(f"{current_draft}\n\nUser feedback: {message}", section_config)
            description_preview = clean_ai_response(refined) if refined else None
            
            if description_preview:
                ai_response = f"I've updated the draft based on your feedback. Continue to refine it or click 'Apply to Entry' when you're satisfied."
            else:
                ai_response = "I wasn't able to refine the draft. Please try rephrasing your request."
            
        else:
            # General chat - just respond to the message
            ai_response = ai_service.chat_about_entry(
                entry_id, 
                message, 
                is_first_message=True, 
                include_all_notes=False,
                section_config=section_config,
                action=action
            ) if entry_id else message
        
        # Build debug info
        debug_info = {
            'entry_id': entry_id,
            'entry_type': entry_type,
            'action': action or 'general_chat',
            'has_diagram': bool(diagram_xml),
            'has_diagram_examples': False,
            'section_prompt': None,
            'prompt_layers': ['Base System Prompt'],
            'full_prompt': None
        }
        
        # Get system prompts for full prompt preview
        from ..db import get_system_parameters
        params = get_system_parameters()
        base_prompt = params.get('prompt_base', 'You are a helpful AI assistant.')
        
        # Check if section config has custom prompts
        if section_config:
            # Map action to config keys to show which prompt was used
            action_to_config_key = {
                'generate_description': 'prompt_description',
                'improve_description': 'prompt_description',
                'make_concise': 'prompt_description',
                'add_details': 'prompt_description',
                'compose_note': 'prompt_note_composer',
                'diagram': 'prompt_diagram',
                'planning': 'prompt_planning',
                None: 'prompt_general_chat'
            }
            config_key = action_to_config_key.get(action, 'prompt_general_chat')
            custom_prompt = section_config.get(config_key, '').strip()
            
            if custom_prompt:
                debug_info['section_prompt'] = custom_prompt
                debug_info['prompt_layers'].append('Section Custom Prompt')
            
            # Add template layer
            if action in ['generate_description', 'improve_description', 'make_concise', 'add_details']:
                debug_info['prompt_layers'].insert(1, 'Description Template')
            elif action == 'compose_note':
                debug_info['prompt_layers'].insert(1, 'Note Composer Template')
            elif action == 'diagram':
                debug_info['prompt_layers'].insert(1, 'Diagram Template')
            elif action == 'planning':
                debug_info['prompt_layers'].insert(1, 'Planning Template')
            else:
                debug_info['prompt_layers'].insert(1, 'Chat Template')
        
        # Build full prompt preview for debug
        full_prompt_parts = [f"=== BASE SYSTEM PROMPT ===\n{base_prompt}\n"]
        
        # Add template layer based on action
        if action in ['generate_description', 'improve_description', 'make_concise', 'add_details']:
            desc_template = params.get('prompt_description', '')
            if desc_template:
                full_prompt_parts.append(f"=== DESCRIPTION TEMPLATE ===\n{desc_template}\n")
        elif action == 'compose_note':
            note_template = params.get('prompt_note_composer', '')
            if note_template:
                full_prompt_parts.append(f"=== NOTE COMPOSER TEMPLATE ===\n{note_template}\n")
        elif action == 'diagram':
            diagram_template = params.get('prompt_diagram', '')
            if diagram_template:
                full_prompt_parts.append(f"=== DIAGRAM TEMPLATE ===\n{diagram_template}\n")
        else:
            chat_template = params.get('prompt_chat', '')
            if chat_template:
                full_prompt_parts.append(f"=== CHAT TEMPLATE ===\n{chat_template}\n")
        
        if debug_info.get('section_prompt'):
            full_prompt_parts.append(f"=== SECTION CUSTOM PROMPT ===\n{debug_info['section_prompt']}\n")
        
        full_prompt_parts.append(f"=== USER MESSAGE ===\n{message}")
        
        if diagram_xml:
            full_prompt_parts.append(f"\n=== DIAGRAM CONTEXT ===\n(Diagram XML included)")
        
        debug_info['full_prompt'] = '\n'.join(full_prompt_parts)
        
        # Build response
        response_data = {
            'message': ai_response or "I'm here to help! How can I assist you with this entry?",
            'debug_info': debug_info
        }
        
        if description_preview:
            response_data['description_preview'] = description_preview
        
        return jsonify(response_data)
            
    except Exception as e:
        logger.error(f"Error in AI chat: {str(e)}", exc_info=True)
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

@ai_api_bp.route('/ai/diagram/discuss', methods=['POST'])
def discuss_diagram():
    """Discuss diagram concepts without generating XML"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        message = data.get('message', '').strip()
        entry_id = data.get('entry_id')
        chat_history = data.get('chat_history', [])
        current_diagram = data.get('current_diagram', '')
        
        if not message:
            return jsonify({'error': 'Message is required'}), 400
        
        ai_service = get_ai_service()
        
        if not ai_service.is_available():
            return jsonify({'error': 'AI service is not available'}), 503
        
        # Build context message with system prompt
        system_context = """You are an expert technical diagram designer helping the user create diagrams.

Your approach:
- Be confident and proactive in suggesting concrete diagram structures
- Make informed assumptions based on context rather than asking excessive questions
- Propose specific layouts, components, and connections
- Focus on actionable guidance over questions

When you understand what's needed, end your response with: [READY_TO_GENERATE]

Do not generate diagram XML in this chat - just discuss the concept."""
        
        # Build full message with diagram context
        full_message = f"{system_context}\n\n"
        
        # Add current diagram if available
        if current_diagram and current_diagram.strip():
            from ..utils.diagram_utils import extract_diagram_structure, format_diagram_summary
            
            full_message += "\n**CURRENT DIAGRAM:**\nThe user already has this diagram:\n\n"
            
            # Add structured summary
            structure = extract_diagram_structure(current_diagram)
            summary = format_diagram_summary(structure)
            full_message += "Current Structure:\n"
            full_message += summary + "\n\n"
            
            # Add full XML
            full_message += "Full XML:\n```xml\n"
            full_message += current_diagram
            full_message += "\n```\n\n"
            full_message += "Use this as context when discussing modifications or improvements.\n\n"
        
        # Add diagram examples if available
        if entry_id:
            try:
                from ..utils.diagram_utils import extract_diagram_structure, format_diagram_summary
                
                examples = ai_service._get_diagram_examples_for_entry(entry_id)
                logger.info(f"[Diagram Discuss] Fetched {len(examples)} example(s) for entry {entry_id}")
                if examples:
                    full_message += f"\n**DIAGRAM EXAMPLES:**\nHere are {len(examples)} example diagrams for this entry type:\n\n"
                    for i, example in enumerate(examples, 1):
                        logger.info(f"[Diagram Discuss] Example {i}: {example.get('title', 'Unknown')} - XML length: {len(example.get('xml', ''))}")
                        full_message += f"Example {i}: {example['description']}\n"
                        full_message += f"(from entry: {example.get('title', 'Unknown')})\n\n"
                        
                        # Add structured summary first
                        structure = extract_diagram_structure(example['xml'])
                        summary = format_diagram_summary(structure)
                        full_message += "Structure Analysis:\n"
                        full_message += summary + "\n\n"
                        
                        # Then add full XML
                        full_message += "Full XML:\n```xml\n"
                        full_message += example['xml']
                        full_message += "\n```\n\n"
                    
                    # Add diagram generation rules (editable in system settings)
                    from ..db import get_system_parameters
                    params = get_system_parameters()
                    diagram_rules = params.get('prompt_diagram_rules', '')
                    if diagram_rules:
                        full_message += f"\n**DIAGRAM GENERATION RULES:**\n{diagram_rules}\n\n"
                else:
                    logger.info(f"[Diagram Discuss] No examples returned for entry {entry_id}")
            except Exception as e:
                logger.error(f"Could not fetch diagram examples: {e}", exc_info=True)
        
        full_message += f"User: {message}"
        
        response = ai_service.chat_about_entry(
            entry_id=entry_id,
            user_message=full_message,
            is_first_message=len(chat_history) == 0,
            include_all_notes=False
        )
        
        # Capture the actual prompt that was sent to the AI
        actual_prompt_sent = getattr(ai_service, '_last_prompt', None)
        
        if response:
            # Check if AI thinks we're ready to generate
            ready_to_generate = '[READY_TO_GENERATE]' in response
            clean_response = response.replace('[READY_TO_GENERATE]', '').strip()
            
            # Build debug info
            debug_info = {
                'entry_id': entry_id,
                'entry_type': None,
                'action': 'diagram_discussion',
                'has_diagram': bool(current_diagram),
                'has_diagram_examples': False,
                'section_prompt': None,
                'prompt_layers': ['Base System Prompt', 'Diagram Discussion Template']
            }
            
            # Get entry type
            try:
                from flask import g
                if 'db' not in g:
                    db_path = current_app.config['DATABASE_PATH']
                    g.db = sqlite3.connect(db_path)
                    g.db.row_factory = sqlite3.Row
                
                cursor = g.db.cursor()
                cursor.execute('SELECT et.singular_label, et.diagram_examples FROM Entry e JOIN EntryType et ON e.entry_type_id = et.id WHERE e.id = ?', (entry_id,))
                row = cursor.fetchone()
                if row:
                    debug_info['entry_type'] = row['singular_label']
                    if row['diagram_examples']:
                        import json
                        examples = json.loads(row['diagram_examples'])
                        if examples:
                            debug_info['has_diagram_examples'] = True
                            debug_info['diagram_examples_count'] = len(examples)
            except Exception as e:
                logger.warning(f"Could not fetch entry type for debug info: {e}")
            
            # Use the ACTUAL prompt that was sent to the AI (captured from ai_service)
            if actual_prompt_sent:
                debug_info['full_prompt'] = actual_prompt_sent
            else:
                # Fallback: if we couldn't capture it, note that
                debug_info['full_prompt'] = "Unable to capture actual prompt sent to AI"
            
            return jsonify({
                'success': True,
                'response': clean_response,
                'ready_to_generate': ready_to_generate,
                'debug_info': debug_info
            })
        
        return jsonify({'error': 'Failed to process message'}), 500
        
    except Exception as e:
        logger.error(f"Error in diagram discussion: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500


def _build_diagram_specification(chat_history, final_message):
    """Build diagram specification from conversation history"""
    # Include the actual conversation so the AI understands what to create
    spec_parts = []
    spec_parts.append("Based on our discussion, create a technical diagram with these requirements:")
    spec_parts.append("")
    
    # Include recent conversation messages for context
    if chat_history:
        spec_parts.append("**Discussion summary:**")
        # Include last 4 exchanges (8 messages)
        recent_messages = chat_history[-8:] if len(chat_history) > 8 else chat_history
        for msg in recent_messages:
            role = msg.get('role', 'user')
            content = msg.get('content', '')
            if role == 'user':
                # Only include user messages to keep it focused
                spec_parts.append(f"- User requested: {content}")
    
    spec_parts.append("")
    spec_parts.append("**Final instruction:**")
    spec_parts.append(final_message)
    spec_parts.append("")
    spec_parts.append("Create a clear, well-labeled diagram showing all the components and connections discussed.")
    
    return '\n'.join(spec_parts)


@ai_api_bp.route('/ai/diagram', methods=['POST'])
def generate_diagram():
    """Generate or modify Draw.io diagram based on natural language request"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        message = data.get('message', '').strip()
        entry_id = data.get('entry_id')
        chat_history = data.get('chat_history', [])
        current_diagram = data.get('current_diagram', '')
        
        if not message:
            return jsonify({'error': 'Message is required'}), 400
        
        ai_service = get_ai_service()
        
        if not ai_service.is_available():
            return jsonify({'error': 'AI service is not available'}), 503
        
        # Build a sanitized technical specification from chat history
        # This helps avoid safety filters by using generic technical terms
        diagram_spec = _build_diagram_specification(chat_history, message)
        
        logger.info(f"Generated diagram specification: {diagram_spec[:200]}...")
        
        # Generate diagram XML using sanitized specification
        result = ai_service.generate_diagram(diagram_spec, current_diagram, entry_id)
        
        if result:
            # Check if result contains an error (e.g., safety block)
            if 'error' in result:
                return jsonify({'error': result['error']}), 400
            
            # Success case
            if 'diagram_xml' in result:
                return jsonify({
                    'success': True,
                    'diagram_xml': result['diagram_xml'],
                    'explanation': result.get('explanation', 'Diagram updated successfully')
                })
        
        return jsonify({'error': 'Failed to generate diagram'}), 500
            
    except Exception as e:
        logger.error(f"Error generating diagram: {str(e)}", exc_info=True)
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


@ai_api_bp.route('/ai/diagram/analyze', methods=['POST'])
def analyze_diagram():
    """Analyze a Draw.io diagram XML and provide insights"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        diagram_xml = data.get('diagram_xml', '').strip()
        entry_id = data.get('entry_id')
        entry_context = data.get('entry_context', '')
        
        if not diagram_xml:
            return jsonify({'error': 'Diagram XML is required'}), 400
        
        ai_service = get_ai_service()
        
        if not ai_service.is_available():
            return jsonify({'error': 'AI service is not available'}), 503
        
        # Parse the diagram XML to extract meaningful information
        import xml.etree.ElementTree as ET
        
        try:
            root = ET.fromstring(diagram_xml)
            
            # Count elements
            cells = root.findall('.//{http://www.jgraph.com/}mxCell') + root.findall('.//mxCell')
            vertices = [cell for cell in cells if cell.get('vertex') == '1']
            edges = [cell for cell in cells if cell.get('edge') == '1']
            
            # Extract labels/text content
            labels = []
            for cell in cells:
                value = cell.get('value', '')
                if value:
                    labels.append(value)
            
            # Build analysis prompt
            analysis_prompt = f"""I'm sharing a Draw.io diagram from my project. Please analyze it and provide insights.

**Diagram Structure:**
- Total elements: {len(cells)}
- Shapes/Nodes: {len(vertices)}
- Connections/Edges: {len(edges)}
- Labels found: {', '.join(labels[:20]) if labels else 'None'}

**Entry Context:**
{entry_context if entry_context else 'No additional context provided'}

Please provide:
1. **What the diagram represents**: Summarize the main purpose and structure
2. **Key components**: List the main elements and their relationships
3. **Observations**: Any patterns, potential issues, or suggestions for improvement
4. **Questions**: Any clarifying questions about the diagram's purpose or design

Be concise and helpful. Focus on understanding what I've created and offering constructive feedback."""

            # Use the AI service to analyze
            response = ai_service.generate_response(analysis_prompt)
            
            if response:
                return jsonify({
                    'success': True,
                    'analysis': response,
                    'stats': {
                        'total_elements': len(cells),
                        'vertices': len(vertices),
                        'edges': len(edges),
                        'has_labels': len(labels) > 0
                    }
                })
            else:
                return jsonify({'error': 'Failed to generate analysis'}), 500
                
        except ET.ParseError as e:
            logger.error(f"XML Parse Error: {str(e)}")
            # If XML parsing fails, still try to analyze as plain text
            analysis_prompt = f"""I'm sharing a Draw.io diagram (as XML data). Please help me understand what I've created.

Here's a snippet of the diagram data:
{diagram_xml[:500]}...

Please provide:
1. What you can tell about this diagram from the XML structure
2. Any observations or suggestions

Keep your response concise and helpful."""
            
            response = ai_service.generate_response(analysis_prompt)
            
            if response:
                return jsonify({
                    'success': True,
                    'analysis': response,
                    'stats': {
                        'parse_error': True
                    }
                })
            else:
                return jsonify({'error': 'Failed to analyze diagram'}), 500
            
    except Exception as e:
        logger.error(f"Error analyzing diagram: {str(e)}", exc_info=True)
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500
