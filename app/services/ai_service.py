"""
AI Service for Google Gemini API Integration
Provides writing assistance for descriptions, notes, and SQL queries.
"""

import os
import logging
from typing import Optional, Dict, Any
import google.generativeai as genai
from flask import current_app
import json
import json

logger = logging.getLogger(__name__)

class AIService:
    """Service for interacting with Google's Gemini AI API"""
    
    def __init__(self):
        self.model = None
        self.is_configured = False
        self._last_api_key = None
        self._last_model_name = None
        self._configure()
    
    def _configure(self):
        """Configure the Gemini AI model"""
        try:
            # Check environment variable first, then system parameters
            api_key = os.getenv('GEMINI_API_KEY')
            model_name = 'gemini-1.5-flash'  # Default model name
            
            if not api_key:
                # Try to get from system parameters
                try:
                    from ..db import get_system_parameters
                    params = get_system_parameters()
                    api_key = params.get('gemini_api_key', '')
                    model_name = params.get('gemini_model_name', 'gemini-1.5-flash')
                except Exception as e:
                    logger.warning(f"Could not access system parameters: {e}")
            else:
                # If API key from environment, still try to get model name from system parameters
                try:
                    from ..db import get_system_parameters
                    params = get_system_parameters()
                    model_name = params.get('gemini_model_name', 'gemini-1.5-flash')
                except Exception as e:
                    logger.warning(f"Could not access system parameters for model name: {e}")
            
            if not api_key:
                logger.warning("GEMINI_API_KEY not found in environment or system parameters. AI features will be disabled.")
                self.is_configured = False
                self.model = None
                self._last_api_key = None
                self._last_model_name = None
                return
            
            # Check if configuration has changed
            config_changed = (api_key != self._last_api_key or model_name != self._last_model_name)
            
            if config_changed or not self.is_configured:
                genai.configure(api_key=api_key)
                self.model = genai.GenerativeModel(model_name)
                self.is_configured = True
                self._last_api_key = api_key
                self._last_model_name = model_name
                logger.info(f"Gemini AI successfully configured with model: {model_name}")
            
        except Exception as e:
            logger.error(f"Failed to configure Gemini AI: {str(e)}")
            self.is_configured = False
            self.model = None
    
    def reconfigure(self):
        """Force reconfiguration of the AI service (useful when settings change)"""
        logger.info("Forcing AI service reconfiguration...")
        self._configure()
        return self.is_configured
    
    def is_available(self) -> bool:
        """Check if AI service is available and configured"""
        # Always try to reconfigure to pick up any system parameter changes
        # This is lightweight if nothing changed
        self._configure()
        return self.is_configured and self.model is not None
    
    def _get_base_prompt(self) -> str:
        """Get the base prompt from system parameters"""
        try:
            from ..db import get_system_parameters
            params = get_system_parameters()
            return params.get('gemini_base_prompt', 'You are a helpful assistant for a project management application. Please provide clear, concise, and well-structured responses.')
        except Exception as e:
            logger.warning(f"Could not access base prompt from system parameters: {e}")
            return 'You are a helpful assistant for a project management application. Please provide clear, concise, and well-structured responses.'
    
    def _get_note_type_base_prompt(self, note_type: str) -> str:
        """Get note type-specific base prompt or fallback to general base prompt"""
        try:
            from ..db import get_system_parameters
            params = get_system_parameters()
            
            # Get custom note types configuration
            custom_note_types_str = params.get('custom_note_types', '{}')
            try:
                custom_note_types_config = json.loads(custom_note_types_str)
            except json.JSONDecodeError:
                # Handle legacy format (array) or invalid JSON
                custom_note_types_config = {}
            
            # First check for default note type prompts
            if isinstance(custom_note_types_config, dict) and 'default_prompts' in custom_note_types_config:
                default_prompts = custom_note_types_config['default_prompts']
                if note_type in default_prompts:
                    base_prompt = default_prompts[note_type].strip()
                    if base_prompt:
                        return base_prompt
            
            # Then check for custom note types (legacy format or new format)
            custom_note_types = []
            if isinstance(custom_note_types_config, list):
                # Legacy format - array of note types
                custom_note_types = custom_note_types_config
            elif isinstance(custom_note_types_config, dict) and 'custom_types' in custom_note_types_config:
                # New format - with custom_types array
                custom_note_types = custom_note_types_config['custom_types']
            
            # Look for matching custom note type with base_prompt
            for note_type_config in custom_note_types:
                if note_type_config.get('name', '').lower() == note_type.lower():
                    base_prompt = note_type_config.get('base_prompt', '').strip()
                    if base_prompt:
                        return base_prompt
            
            # Fallback to general base prompt
            return self._get_base_prompt()
            
        except Exception as e:
            logger.warning(f"Could not access note type base prompt for '{note_type}': {e}")
            return self._get_base_prompt()
    
    def generate_description(self, title: str, entry_type: str, context: str = "") -> Optional[str]:
        """
        Generate a description for an entry based on title and type
        
        Args:
            title: The title/name of the entry
            entry_type: The type of entry (e.g., Recipe, Ingredient, Equipment)
            context: Additional context information
            
        Returns:
            Generated description or None if failed
        """
        if not self.is_available():
            return None
        
        try:
            prompt = self._build_description_prompt(title, entry_type, context)
            response = self.model.generate_content(prompt)
            
            if response and response.text:
                return response.text.strip()
            
        except Exception as e:
            logger.error(f"Failed to generate description: {str(e)}")
        
        return None
    
    def generate_note(self, title: str, entry_type: str, note_type: str = "general", context: str = "") -> Optional[str]:
        """
        Generate note content based on title, entry type, and note type
        
        Args:
            title: The entry title
            entry_type: The type of entry
            note_type: The type of note to generate
            context: Additional context or existing content
            
        Returns:
            Generated note content or None if failed
        """
        if not self.is_available():
            return None
        
        try:
            prompt = self._build_note_generation_prompt(title, entry_type, note_type, context)
            response = self.model.generate_content(prompt)
            
            if response and response.text:
                return response.text.strip()
                
        except Exception as e:
            logger.error(f"Failed to generate note: {str(e)}")
        
        return None
    
    def generate_theme(self, description: str, style_preferences: str = "", current_theme: dict = None) -> Optional[Dict[str, Any]]:
        """
        Generate theme colors based on description and preferences
        
        Args:
            description: Description of the desired theme (e.g., "warm sunset colors", "corporate professional")
            style_preferences: Additional style preferences (e.g., "high contrast", "minimal")
            current_theme: Current theme settings to reference
            
        Returns:
            Dictionary with theme colors and metadata or None if failed
        """
        if not self.is_available():
            return None
        
        try:
            prompt = self._build_theme_generation_prompt(description, style_preferences, current_theme)
            response = self.model.generate_content(prompt)
            
            if response and response.text:
                # Parse the JSON response
                try:
                    theme_data = json.loads(response.text.strip())
                    return theme_data
                except json.JSONDecodeError:
                    # If JSON parsing fails, try to extract hex colors manually
                    return self._extract_colors_from_text(response.text)
                
        except Exception as e:
            logger.error(f"Failed to generate theme: {str(e)}")
        
        return None
    
    def chat_theme_generation(self, user_message: str, conversation_history: list = None, current_theme: dict = None) -> Optional[Dict[str, Any]]:
        """
        Generate theme-related responses with conversation context
        
        Args:
            user_message: The user's current message
            conversation_history: List of previous messages [{'role': 'user'|'assistant', 'content': 'text'}]
            current_theme: Current theme settings to reference
            
        Returns:
            Dictionary with response and optional theme data or None if failed
        """
        if not self.is_available():
            return None
        
        try:
            prompt = self._build_chat_theme_prompt(user_message, conversation_history or [], current_theme)
            response = self.model.generate_content(prompt)
            
            if response and response.text:
                response_text = response.text.strip()
                logger.info(f"AI Chat Response: {response_text[:100]}...")  # Log first 100 chars
                
                # Remove markdown code blocks if present
                if response_text.startswith('```json'):
                    response_text = response_text.replace('```json', '').replace('```', '').strip()
                elif response_text.startswith('```'):
                    response_text = response_text.replace('```', '').strip()
                
                # Parse the JSON response (should always be theme JSON now)
                try:
                    json_response = json.loads(response_text)
                    logger.info(f"Successfully parsed theme JSON: {json_response.get('name', 'Unknown')}")
                    # Ensure it has the correct type
                    if 'type' not in json_response:
                        json_response['type'] = 'theme'
                    return json_response
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse JSON response: {e}")
                    logger.error(f"Raw response: {response_text}")
                    # Return an error theme instead
                    return {
                        'type': 'message',
                        'content': f"I generated a theme but there was a formatting issue. Here's what I created: {response_text[:200]}..."
                    }
                
        except Exception as e:
            logger.error(f"Failed to generate chat response: {str(e)}")
        
        return None

    def improve_note(self, note_content: str, note_type: str = "general") -> Optional[str]:
        """
        Improve or expand a note's content
        
        Args:
            note_content: The existing note content
            note_type: The type of note (general, technical, observation, etc.)
            
        Returns:
            Improved note content or None if failed
        """
        if not self.is_available():
            return None
        
        try:
            prompt = self._build_note_improvement_prompt(note_content, note_type)
            response = self.model.generate_content(prompt)
            
            if response and response.text:
                return response.text.strip()
                
        except Exception as e:
            logger.error(f"Failed to improve note: {str(e)}")
        
        return None
    
    def improve_description(self, description: str) -> Optional[str]:
        """
        Improve or enhance a description's content
        
        Args:
            description: The existing description content
            
        Returns:
            Improved description or None if failed
        """
        if not self.is_available():
            return None
        
        try:
            prompt = self._build_description_improvement_prompt(description)
            response = self.model.generate_content(prompt)
            
            if response and response.text:
                return response.text.strip()
                
        except Exception as e:
            logger.error(f"Failed to improve description: {str(e)}")
        
        return None
    
    def generate_sql_query(self, description: str, table_info: str = "") -> Optional[str]:
        """
        Generate SQL query based on natural language description
        
        Args:
            description: Natural language description of what the query should do
            table_info: Information about available tables and columns
            
        Returns:
            SQL query or None if failed
        """
        if not self.is_available():
            return None
        
        try:
            prompt = self._build_sql_prompt(description, table_info)
            response = self.model.generate_content(prompt)
            
            if response and response.text:
                # Extract SQL from response (remove markdown formatting if present)
                sql = response.text.strip()
                if sql.startswith('```sql'):
                    sql = sql[6:]
                if sql.endswith('```'):
                    sql = sql[:-3]
                return sql.strip()
                
        except Exception as e:
            logger.error(f"Failed to generate SQL query: {str(e)}")
        
        return None
    
    def explain_sql_query(self, sql_query: str) -> Optional[str]:
        """
        Explain what a SQL query does in plain English
        
        Args:
            sql_query: The SQL query to explain
            
        Returns:
            Explanation of the query or None if failed
        """
        if not self.is_available():
            return None
        
        try:
            prompt = self._build_sql_explanation_prompt(sql_query)
            response = self.model.generate_content(prompt)
            
            if response and response.text:
                return response.text.strip()
                
        except Exception as e:
            logger.error(f"Failed to explain SQL query: {str(e)}")
        
        return None
    
    def _build_sql_explanation_prompt(self, sql_query: str) -> str:
        """Build prompt for SQL explanation"""
        base_prompt = self._get_base_prompt()
        
        prompt = f"""
        {base_prompt}
        
        Task: Please explain this SQL query in simple, clear language:
        
        ```sql
        {sql_query}
        ```
        
        Explain:
        1. What data it retrieves
        2. Any filtering or conditions
        3. How the results are organized
        4. The purpose of the query
        
        Keep the explanation concise and easy to understand.
        """
        return prompt
    
    def _build_description_prompt(self, title: str, entry_type: str, context: str) -> str:
        """Build prompt for description generation"""
        base_prompt = self._get_base_prompt()
        
        prompt = f"""
        {base_prompt}
        
        Task: Generate a concise, informative description for a {entry_type} named "{title}".
        
        {f"Additional context: {context}" if context else ""}
        
        CRITICAL FORMATTING RULES (MUST FOLLOW):
        1. Use HYPHENS (-) for ALL bullet points - NEVER use asterisks (*)
        2. NO conversational text - return ONLY the description content
        3. NO introductory phrases like "Here's a description" or "This is"
        4. Start directly with the content
        
        Example of CORRECT bullet formatting:
        - First point
        - Second point
          - Sub-point (indented with hyphen)
        
        Example of INCORRECT (DO NOT DO THIS):
        * First point (WRONG - uses asterisk)
        • First point (WRONG - uses bullet character)
        Here's a description: ... (WRONG - conversational intro)
        
        Requirements:
        - Be factual and informative
        - Include relevant details for a database/inventory system
        - Use professional, neutral tone
        - Use Markdown formatting when helpful (headings, bold, lists)
        - ALWAYS use hyphens (-) for bullet lists
        
        Return ONLY the description content with NO conversational wrapper text.
        """
        return prompt
    
    def _build_note_improvement_prompt(self, note_content: str, note_type: str) -> str:
        """Build prompt for note improvement"""
        base_prompt = self._get_note_type_base_prompt(note_type)
        
        prompt = f"""
        {base_prompt}
        
        Task: Please improve this {note_type} note by making it clearer, more detailed, and better organized:
        
        Original note:
        {note_content}
        
        Guidelines:
        - Maintain the original meaning and intent
        - Improve clarity and readability
        - Add relevant details if the note seems incomplete
        - Fix any grammar or spelling issues
        - Organize information logically
        - Keep the tone appropriate for a {note_type} note
        - Don't change factual information, only improve presentation
        
        Return the improved version of the note.
        """
        return prompt
    
    def _build_description_improvement_prompt(self, description: str) -> str:
        """Build prompt for description improvement"""
        base_prompt = self._get_base_prompt()
        
        prompt = f"""
        {base_prompt}
        
        Task: Improve this description by making it clearer, more detailed, and better organized.
        
        Original description:
        {description}
        
        CRITICAL FORMATTING RULES (MUST FOLLOW):
        1. Use HYPHENS (-) for ALL bullet points - NEVER use asterisks (*)
        2. NO conversational text - return ONLY the improved description
        3. NO phrases like "Here's an improved version" or "I've updated"
        4. Start directly with the improved content
        
        Example of CORRECT bullet formatting:
        - First point
        - Second point
          - Sub-point (indented with hyphen)
        
        Example of INCORRECT (DO NOT DO THIS):
        * First point (WRONG - uses asterisk)
        Here's an improved version: ... (WRONG - conversational intro)
        
        Guidelines:
        - Maintain the original meaning and intent
        - Improve clarity and readability
        - Add relevant details if incomplete
        - Fix grammar or spelling issues
        - Organize information logically
        - Use Markdown formatting (headings, bold, lists with hyphens)
        - Keep tone professional and informative
        - ALWAYS use hyphens (-) for bullet lists, NEVER asterisks (*)
        
        Return ONLY the improved description content with NO conversational wrapper.
        """
        return prompt
    
    def _build_note_generation_prompt(self, title: str, entry_type: str, note_type: str, context: str = "") -> str:
        """Build prompt for note generation with note type-specific guidance"""
        base_prompt = self._get_note_type_base_prompt(note_type)
        
        context_section = ""
        if context:
            context_section = f"""
        
        Additional context:
        {context}
        """
        
        prompt = f"""
        {base_prompt}
        
        Task: Generate content for a {note_type} note based on the following information:
        
        Entry Title: {title}
        Entry Type: {entry_type}
        Note Type: {note_type}{context_section}
        
        Guidelines:
        - Create relevant and useful content appropriate for a {note_type} note
        - Make it specific to the entry "{title}" of type "{entry_type}"
        - Keep the tone and format appropriate for the note type
        - Be concise but informative
        - If context is provided, build upon it rather than repeating it
        
        Generate the note content:
        """
        return prompt
    
    def _build_theme_generation_prompt(self, description: str, style_preferences: str, current_theme: dict) -> str:
        """Build prompt for theme generation"""
        base_prompt = self._get_base_prompt()
        
        current_theme_info = ""
        if current_theme:
            current_theme_info = f"\nCurrent theme for reference:\n{json.dumps(current_theme, indent=2)}"
        
        style_info = f"\nStyle preferences: {style_preferences}" if style_preferences else ""
        
        prompt = f"""
        {base_prompt}
        
        Task: Generate a complete color theme based on this description: "{description}"
        {style_info}
        {current_theme_info}
        
        Requirements:
        - Generate a cohesive color palette with proper contrast ratios
        - Include colors for: background, text, primary, secondary, accent, borders, cards, surfaces
        - All colors must be in HEX format (#RRGGBB)
        - Ensure accessibility (WCAG 2.1 AA compliance for text contrast)
        - Create both light and dark mode variations when appropriate
        - Include a brief explanation of the color choices
        
        Respond with ONLY a valid JSON object in this exact format:
        {{
            "name": "Theme Name",
            "description": "Brief description of the theme",
            "colors": {{
                "primary": "#hexcode",
                "secondary": "#hexcode", 
                "accent": "#hexcode",
                "background": "#hexcode",
                "surface": "#hexcode",
                "text": "#hexcode",
                "text_secondary": "#hexcode",
                "border": "#hexcode",
                "card_bg": "#hexcode",
                "success": "#hexcode",
                "warning": "#hexcode",
                "danger": "#hexcode",
                "info": "#hexcode"
            }},
            "dark_mode_colors": {{
                "primary": "#hexcode",
                "secondary": "#hexcode",
                "accent": "#hexcode", 
                "background": "#hexcode",
                "surface": "#hexcode",
                "text": "#hexcode",
                "text_secondary": "#hexcode",
                "border": "#hexcode",
                "card_bg": "#hexcode",
                "success": "#hexcode",
                "warning": "#hexcode",
                "danger": "#hexcode",
                "info": "#hexcode"
            }},
            "rationale": "Explanation of color choices and design philosophy"
        }}
        """
        return prompt
    
    def _build_chat_theme_prompt(self, user_message: str, conversation_history: list, current_theme: dict) -> str:
        """Build prompt for conversational theme generation"""
        base_prompt = self._get_base_prompt()
        
        current_theme_info = ""
        if current_theme:
            current_theme_info = f"\nCurrent theme for reference:\n{json.dumps(current_theme, indent=2)}"
        
        # Build conversation context
        conversation_context = ""
        if conversation_history:
            conversation_context = "\nConversation history:\n"
            for msg in conversation_history[-6:]:  # Keep last 6 messages for context
                role = msg.get('role', 'user')
                content = msg.get('content', '')
                conversation_context += f"{role.title()}: {content}\n"
        
        prompt = f"""
        {base_prompt}
        
        You are a theme generation system. Your ONLY job is to generate theme color JSON based on user requests.
        
        {conversation_context}
        {current_theme_info}
        
        User request: "{user_message}"
        
        CRITICAL: You must ALWAYS respond with ONLY valid JSON in this exact format. Do not include any other text, explanations, or markdown formatting:

        {{
            "type": "theme",
            "name": "Theme Name Based On Request",
            "description": "Brief description of the theme",
            "colors": {{
                "primary": "#hexcode",
                "secondary": "#hexcode",
                "accent": "#hexcode",
                "background": "#ffffff",
                "surface": "#f8f9fa",
                "text": "#212529",
                "text_secondary": "#6c757d",
                "border": "#dee2e6",
                "card_bg": "#ffffff",
                "success": "#28a745",
                "warning": "#ffc107",
                "danger": "#dc3545",
                "info": "#17a2b8"
            }},
            "dark_mode_colors": {{
                "primary": "#hexcode",
                "secondary": "#hexcode",
                "accent": "#hexcode",
                "background": "#1a1a1a",
                "surface": "#2d2d2d",
                "text": "#ffffff",
                "text_secondary": "#aaaaaa",
                "border": "#444444",
                "card_bg": "#262626",
                "success": "#198754",
                "warning": "#ffc107",
                "danger": "#dc3545",
                "info": "#0dcaf0"
            }},
            "rationale": "Brief explanation of color choices and how they relate to the user's request"
        }}
        
        Rules:
        1. Always generate both light and dark mode colors
        2. Ensure good contrast ratios for accessibility
        3. Use the conversation history to understand context and modifications
        4. If modifying an existing theme, base changes on the current theme provided
        5. Make colors cohesive and aesthetically pleasing
        6. Respond with ONLY the JSON - no other text or formatting
        """
        return prompt

    def _extract_colors_from_text(self, text: str) -> Dict[str, Any]:
        """Extract hex colors from text if JSON parsing fails"""
        import re
        hex_pattern = r'#[A-Fa-f0-9]{6}'
        colors = re.findall(hex_pattern, text)
        
        if len(colors) >= 8:
            return {
                "name": "AI Generated Theme",
                "description": "Theme generated from AI response",
                "colors": {
                    "primary": colors[0] if len(colors) > 0 else "#007bff",
                    "secondary": colors[1] if len(colors) > 1 else "#6c757d",
                    "accent": colors[2] if len(colors) > 2 else "#28a745",
                    "background": colors[3] if len(colors) > 3 else "#ffffff",
                    "surface": colors[4] if len(colors) > 4 else "#f8f9fa",
                    "text": colors[5] if len(colors) > 5 else "#212529",
                    "text_secondary": colors[6] if len(colors) > 6 else "#6c757d",
                    "border": colors[7] if len(colors) > 7 else "#dee2e6",
                    "card_bg": colors[8] if len(colors) > 8 else "#ffffff",
                    "success": "#28a745",
                    "warning": "#ffc107", 
                    "danger": "#dc3545",
                    "info": "#17a2b8"
                },
                "rationale": "Theme colors extracted from AI response"
            }
        
        return None

    def _build_sql_prompt(self, description: str, table_info: str) -> str:
        """Build prompt for SQL generation"""
        base_prompt = self._get_base_prompt()
        
        prompt = f"""
        {base_prompt}
        
        Task: Generate a SQL query based on this description: "{description}"
        
        {f"Available tables and columns: {table_info}" if table_info else ""}
        
        Requirements:
        - Generate valid SQL syntax
        - Use appropriate SELECT, WHERE, JOIN, GROUP BY, ORDER BY clauses as needed
        - Include comments for complex parts
        - Optimize for readability
        - Return only the SQL query, properly formatted
        
        If the request is unclear or lacks sufficient information, generate the best possible query based on common database patterns.
        """
        return prompt

    def _gather_entry_context(self, entry_id: int, include_all_notes: bool = False) -> Dict[str, Any]:
        """Gather comprehensive context about an entry for AI chat"""
        from flask import g
        from datetime import datetime, timedelta
        import json
        
        context = {}
        context['include_all_notes'] = include_all_notes
        
        try:
            conn = g.get('db')
            if not conn:
                from ..db import get_connection
                conn = get_connection()
            
            cursor = conn.cursor()
            
            # Get entry details
            cursor.execute('''
                SELECT 
                    e.id, e.title, e.description, e.created_at,
                    e.intended_end_date, e.actual_end_date, e.status,
                    et.name AS entry_type_name, et.singular_label, et.plural_label,
                    et.has_sensors, et.show_end_dates
                FROM Entry e
                JOIN EntryType et ON e.entry_type_id = et.id
                WHERE e.id = ?
            ''', (entry_id,))
            
            entry = cursor.fetchone()
            if not entry:
                return {'error': 'Entry not found'}
            
            # Convert Row to dict for easier access
            entry_dict = dict(entry)
            
            context['title'] = entry_dict['title']
            context['description'] = entry_dict['description'] or 'No description provided'
            context['entry_type'] = entry_dict['singular_label']
            context['entry_type_name'] = entry_dict['entry_type_name']
            context['status'] = entry_dict.get('status', 'active')
            context['created_at'] = entry_dict['created_at']
            
            # Get entry type description for additional context
            cursor.execute('''
                SELECT description
                FROM EntryType
                WHERE name = ?
            ''', (entry_dict['entry_type_name'],))
            
            entry_type_row = cursor.fetchone()
            if entry_type_row:
                entry_type_dict = dict(entry_type_row)
                context['entry_type_description'] = entry_type_dict.get('description', '')
            
            # Calculate how long the entry has been active
            try:
                created_date = datetime.fromisoformat(entry_dict['created_at'])
                days_active = (datetime.now() - created_date).days
                context['days_active'] = days_active
                context['created_date_formatted'] = created_date.strftime('%B %d, %Y')
            except:
                context['days_active'] = 0
                context['created_date_formatted'] = 'Unknown'
            
            # Check for end dates
            if entry_dict.get('show_end_dates'):
                context['has_end_dates'] = True
                context['intended_end_date'] = entry_dict.get('intended_end_date')
                context['actual_end_date'] = entry_dict.get('actual_end_date')
                
                # Calculate days until/past intended end date
                if entry_dict.get('intended_end_date'):
                    try:
                        intended_date = datetime.fromisoformat(entry_dict['intended_end_date'])
                        days_diff = (intended_date - datetime.now()).days
                        if days_diff > 0:
                            context['days_until_end'] = days_diff
                        elif days_diff < 0:
                            context['days_overdue'] = abs(days_diff)
                    except:
                        pass
            
            # Get notes count and types (including shared notes)
            # Notes are associated with this entry if:
            # 1. entry_id matches, OR
            # 2. entry_id is in the associated_entry_ids JSON array
            cursor.execute('''
                SELECT COUNT(*) as count, type
                FROM Note
                WHERE entry_id = ? 
                   OR (associated_entry_ids IS NOT NULL 
                       AND associated_entry_ids != '[]' 
                       AND json_array_length(associated_entry_ids) > 0
                       AND EXISTS (
                           SELECT 1 FROM json_each(associated_entry_ids) 
                           WHERE value = ?
                       ))
                GROUP BY type
            ''', (entry_id, entry_id))
            
            notes_by_type = cursor.fetchall()
            context['total_notes'] = sum(row['count'] for row in notes_by_type)
            context['notes_by_type'] = {row['type']: row['count'] for row in notes_by_type}
            
            # Get recent notes (including shared notes)
            cursor.execute('''
                SELECT note_title, note_text, type, created_at, entry_id, associated_entry_ids, file_paths
                FROM Note
                WHERE entry_id = ? 
                   OR (associated_entry_ids IS NOT NULL 
                       AND associated_entry_ids != '[]' 
                       AND json_array_length(associated_entry_ids) > 0
                       AND EXISTS (
                           SELECT 1 FROM json_each(associated_entry_ids) 
                           WHERE value = ?
                       ))
                ORDER BY created_at DESC
                LIMIT 5
            ''', (entry_id, entry_id))
            
            recent_notes = cursor.fetchall()
            context['recent_notes'] = []
            for note in recent_notes:
                # Safely parse file_paths (can be JSON array or comma-separated string)
                attachments = []
                if note['file_paths']:
                    try:
                        # Try JSON first
                        attachments = json.loads(note['file_paths'])
                    except (json.JSONDecodeError, TypeError):
                        # Fall back to comma-separated string
                        if isinstance(note['file_paths'], str) and ',' in note['file_paths']:
                            attachments = [f.strip() for f in note['file_paths'].split(',')]
                        elif isinstance(note['file_paths'], str) and note['file_paths']:
                            attachments = [note['file_paths']]
                
                context['recent_notes'].append({
                    'title': note['note_title'] or 'Untitled',
                    'type': note['type'],
                    'preview': note['note_text'][:100] + '...' if len(note['note_text']) > 100 else note['note_text'],
                    'is_shared': note['entry_id'] != entry_id,  # Mark if it's a shared note
                    'attachments': attachments
                })
            
            # Get all notes content if requested (including shared notes)
            if include_all_notes and context['total_notes'] > 0:
                cursor.execute('''
                    SELECT note_title, note_text, type, created_at, entry_id, associated_entry_ids, file_paths
                    FROM Note
                    WHERE entry_id = ? 
                       OR (associated_entry_ids IS NOT NULL 
                           AND associated_entry_ids != '[]' 
                           AND json_array_length(associated_entry_ids) > 0
                           AND EXISTS (
                               SELECT 1 FROM json_each(associated_entry_ids) 
                               WHERE value = ?
                           ))
                    ORDER BY created_at DESC
                ''', (entry_id, entry_id))
                
                all_notes = cursor.fetchall()
                context['all_notes'] = []
                for note in all_notes:
                    # Safely parse file_paths (can be JSON array or comma-separated string)
                    attachments = []
                    if note['file_paths']:
                        try:
                            # Try JSON first
                            attachments = json.loads(note['file_paths'])
                        except (json.JSONDecodeError, TypeError):
                            # Fall back to comma-separated string
                            if isinstance(note['file_paths'], str) and ',' in note['file_paths']:
                                attachments = [f.strip() for f in note['file_paths'].split(',')]
                            elif isinstance(note['file_paths'], str) and note['file_paths']:
                                attachments = [note['file_paths']]
                    
                    context['all_notes'].append({
                        'title': note['note_title'] or 'Untitled',
                        'type': note['type'],
                        'content': note['note_text'],
                        'created_at': note['created_at'],
                        'is_shared': note['entry_id'] != entry_id,  # Mark if it's a shared note
                        'attachments': attachments
                    })
            
            # Get relationships with descriptions (both directions)
            # First get outgoing relationships (where this entry is the source)
            cursor.execute('''
                SELECT 
                    er.id, er.target_entry_id as related_id, er.relationship_type,
                    e2.title AS related_title, 
                    e2.description AS related_description,
                    et2.singular_label AS related_type,
                    rd.name AS relationship_name,
                    'outgoing' as direction
                FROM EntryRelationship er
                JOIN Entry e2 ON er.target_entry_id = e2.id
                JOIN EntryType et2 ON e2.entry_type_id = et2.id
                LEFT JOIN RelationshipDefinition rd ON er.relationship_type = rd.id
                WHERE er.source_entry_id = ?
            ''', (entry_id,))
            
            outgoing_relationships = cursor.fetchall()
            
            # Then get incoming relationships (where this entry is the target)
            cursor.execute('''
                SELECT 
                    er.id, er.source_entry_id as related_id, er.relationship_type,
                    e2.title AS related_title, 
                    e2.description AS related_description,
                    et2.singular_label AS related_type,
                    rd.name AS relationship_name,
                    'incoming' as direction
                FROM EntryRelationship er
                JOIN Entry e2 ON er.source_entry_id = e2.id
                JOIN EntryType et2 ON e2.entry_type_id = et2.id
                LEFT JOIN RelationshipDefinition rd ON er.relationship_type = rd.id
                WHERE er.target_entry_id = ?
            ''', (entry_id,))
            
            incoming_relationships = cursor.fetchall()
            
            # Combine both directions
            all_relationships = list(outgoing_relationships) + list(incoming_relationships)
            context['relationships_count'] = len(all_relationships)
            context['relationships'] = [
                {
                    'title': dict(rel)['related_title'],
                    'type': dict(rel)['related_type'],
                    'relationship_type': dict(rel).get('relationship_name', 'Related to'),
                    'description': dict(rel).get('related_description', '')[:200] + '...' if dict(rel).get('related_description') and len(dict(rel).get('related_description', '')) > 200 else dict(rel).get('related_description', ''),
                    'direction': dict(rel).get('direction', 'unknown')
                }
                for rel in all_relationships  # Include all relationships
            ]
            
            # Get sensor data if applicable
            if entry_dict.get('has_sensors'):
                cursor.execute('''
                    SELECT COUNT(*) as count, sensor_type
                    FROM SensorData
                    WHERE entry_id = ?
                    GROUP BY sensor_type
                ''', (entry_id,))
                
                sensor_data = cursor.fetchall()
                context['has_sensor_data'] = True
                context['sensor_types'] = {row['sensor_type']: row['count'] for row in sensor_data}
                context['total_sensor_readings'] = sum(row['count'] for row in sensor_data)
            
            # Get project description from system parameters
            try:
                cursor.execute('''
                    SELECT parameter_value 
                    FROM SystemParameters 
                    WHERE parameter_name = 'project_description'
                ''')
                project_desc = cursor.fetchone()
                if project_desc:
                    context['project_description'] = project_desc['parameter_value']
            except:
                pass
            
            return context
            
        except Exception as e:
            logger.error(f"Error gathering entry context: {str(e)}")
            return {'error': str(e)}

    def _get_sensor_data_details(self, entry_id: int, sensor_type: str = None, limit: int = 100) -> Dict[str, Any]:
        """Get detailed sensor data for analysis"""
        from flask import g
        import statistics
        
        try:
            conn = g.get('db')
            if not conn:
                from ..db import get_connection
                conn = get_connection()
            
            cursor = conn.cursor()
            
            # Build query based on whether sensor_type is specified
            if sensor_type:
                cursor.execute('''
                    SELECT sensor_type, value, recorded_at
                    FROM SensorData
                    WHERE entry_id = ? AND sensor_type = ?
                    ORDER BY recorded_at DESC
                    LIMIT ?
                ''', (entry_id, sensor_type, limit))
            else:
                cursor.execute('''
                    SELECT sensor_type, value, recorded_at
                    FROM SensorData
                    WHERE entry_id = ?
                    ORDER BY recorded_at DESC
                    LIMIT ?
                ''', (entry_id, limit))
            
            readings = cursor.fetchall()
            
            if not readings:
                return {'error': 'No sensor data found'}
            
            # Organize data by sensor type
            sensor_data = {}
            for reading in readings:
                reading_dict = dict(reading)
                s_type = reading_dict['sensor_type']
                
                if s_type not in sensor_data:
                    sensor_data[s_type] = {
                        'values': [],
                        'timestamps': [],
                        'count': 0,
                        'unit': None
                    }
                
                try:
                    # Try to extract numeric value from string (e.g., "24.05C" -> 24.05)
                    value_str = str(reading_dict['value']).strip()
                    
                    # Try direct conversion first
                    try:
                        value = float(value_str)
                        sensor_data[s_type]['values'].append(value)
                        sensor_data[s_type]['timestamps'].append(reading_dict['recorded_at'])
                        sensor_data[s_type]['count'] += 1
                    except ValueError:
                        # Extract numeric part using regex
                        import re
                        # Match numeric value (including decimals and negative numbers)
                        match = re.search(r'[-+]?\d*\.?\d+', value_str)
                        if match:
                            value = float(match.group())
                            sensor_data[s_type]['values'].append(value)
                            sensor_data[s_type]['timestamps'].append(reading_dict['recorded_at'])
                            sensor_data[s_type]['count'] += 1
                            
                            # Try to extract unit (everything after the number)
                            unit_match = re.search(r'[-+]?\d*\.?\d+\s*([A-Za-z%°]+)', value_str)
                            if unit_match and not sensor_data[s_type]['unit']:
                                sensor_data[s_type]['unit'] = unit_match.group(1)
                        else:
                            # Really not numeric, just count it
                            sensor_data[s_type]['count'] += 1
                except (ValueError, TypeError, AttributeError):
                    # If not numeric, just count it
                    sensor_data[s_type]['count'] += 1
            
            # Calculate statistics for each sensor type
            result = {}
            for s_type, data in sensor_data.items():
                if data['values']:
                    result[s_type] = {
                        'count': data['count'],
                        'latest': data['values'][0] if data['values'] else None,
                        'average': statistics.mean(data['values']),
                        'min': min(data['values']),
                        'max': max(data['values']),
                        'median': statistics.median(data['values']),
                        'unit': data.get('unit', '')
                    }
                    
                    # Add standard deviation if we have enough data
                    if len(data['values']) > 1:
                        result[s_type]['std_dev'] = statistics.stdev(data['values'])
                    
                    # Add recent readings (last 5)
                    result[s_type]['recent_readings'] = [
                        {'value': v, 'time': t} 
                        for v, t in zip(data['values'][:5], data['timestamps'][:5])
                    ]
                else:
                    result[s_type] = {
                        'count': data['count'],
                        'note': 'Non-numeric data'
                    }
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting sensor data details: {str(e)}")
            return {'error': str(e)}

    def _should_fetch_sensor_details(self, message: str) -> bool:
        """Determine if the user's message requires detailed sensor data"""
        sensor_keywords = [
            'average', 'mean', 'median', 'temperature', 'humidity', 'pressure',
            'sensor', 'reading', 'value', 'data', 'min', 'max', 'highest', 'lowest',
            'recent', 'latest', 'current', 'measurement', 'statistics', 'trend'
        ]
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in sensor_keywords)

    def chat_about_entry(self, entry_id: int, user_message: str, is_first_message: bool = False, include_all_notes: bool = False) -> Optional[str]:
        """Chat with AI about a specific entry with full context"""
        if not self.is_available():
            return None
        
        try:
            # Gather entry context
            context = self._gather_entry_context(entry_id, include_all_notes)
            
            if 'error' in context:
                return f"I apologize, but I encountered an error accessing this entry: {context['error']}"
            
            # Build context prompt
            base_prompt = self._get_base_prompt()
            project_desc = context.get('project_description', 'a project management application')
            
            # Get current date/time for the AI
            from datetime import datetime
            current_datetime = datetime.now()
            current_date_str = current_datetime.strftime('%Y-%m-%d')
            current_time_str = current_datetime.strftime('%H:%M:%S')
            current_full_str = current_datetime.strftime('%Y-%m-%d %H:%M:%S')
            
            context_prompt = f"""
{base_prompt}

You are an AI assistant helping with {project_desc}.

**Current Date/Time:** {current_full_str} (Use this for any date/time calculations)

You are currently discussing the following entry:

**Entry Title:** {context['title']}
**Type:** {context['entry_type']}
**Status:** {context['status']}
**Description:** {context['description']}
**Created Date:** {context['created_at']} (formatted: {context['created_date_formatted']}, which was {context['days_active']} days ago)
"""
            
            # Add entry type description if available
            if context.get('entry_type_description'):
                context_prompt += f"\n**About {context['entry_type']} entries:** {context['entry_type_description']}\n"
            
            # Add end date information if applicable
            if context.get('has_end_dates'):
                if context.get('intended_end_date'):
                    context_prompt += f"**Intended End Date:** {context['intended_end_date']}\n"
                    if context.get('days_until_end'):
                        context_prompt += f"  → {context['days_until_end']} days remaining\n"
                    elif context.get('days_overdue'):
                        context_prompt += f"  → {context['days_overdue']} days overdue\n"
                if context.get('actual_end_date'):
                    context_prompt += f"**Actual End Date:** {context['actual_end_date']}\n"
            
            # Add notes information
            if context['total_notes'] > 0:
                context_prompt += f"\n**Notes:** {context['total_notes']} total notes"
                if context['notes_by_type']:
                    types_str = ', '.join([f"{count} {type_name}" for type_name, count in context['notes_by_type'].items()])
                    context_prompt += f" ({types_str})"
                context_prompt += "\n"
                
                # If user requested all notes, include full content
                if context.get('all_notes'):
                    context_prompt += "\n**All Notes (Full Content - includes shared notes):**\n"
                    for note in context['all_notes']:
                        shared_indicator = " [SHARED]" if note.get('is_shared') else ""
                        attachment_info = ""
                        if note.get('attachments'):
                            file_names = [path.split('/')[-1] for path in note['attachments']]
                            attachment_info = f"  Attachments: {', '.join(file_names)}\n"
                        context_prompt += f"\n  [{note['type']}] {note['title']}{shared_indicator}\n"
                        context_prompt += f"  Created: {note['created_at']}\n"
                        if attachment_info:
                            context_prompt += attachment_info
                        context_prompt += f"  Content: {note['content']}\n"
                        context_prompt += "  " + "-" * 50 + "\n"
                elif context.get('recent_notes'):
                    context_prompt += "\n**Recent Notes (Preview - includes shared notes):**\n"
                    for note in context['recent_notes'][:3]:
                        shared_indicator = " [SHARED]" if note.get('is_shared') else ""
                        attachment_info = ""
                        if note.get('attachments'):
                            file_count = len(note['attachments'])
                            file_names = [path.split('/')[-1] for path in note['attachments']]
                            attachment_info = f" [{file_count} file{'s' if file_count > 1 else ''}: {', '.join(file_names)}]"
                        context_prompt += f"  - [{note['type']}] {note['title']}{shared_indicator}{attachment_info}: {note['preview']}\n"
            
            # Add relationships with descriptions
            if context['relationships_count'] > 0:
                context_prompt += f"\n**Related Entries:** {context['relationships_count']} relationships (both incoming and outgoing)"
                if context.get('relationships'):
                    context_prompt += "\n"
                    for rel in context['relationships']:
                        direction_indicator = "→" if rel.get('direction') == 'outgoing' else "←"
                        context_prompt += f"  {direction_indicator} {rel['relationship_type']}: {rel['title']} ({rel['type']})"
                        if rel.get('description'):
                            context_prompt += f" - {rel['description']}"
                        context_prompt += "\n"
            
            # Add sensor data - fetch detailed data if user is asking sensor-related questions
            if context.get('has_sensor_data') and context['total_sensor_readings'] > 0:
                context_prompt += f"\n**Sensor Data:** {context['total_sensor_readings']} total readings"
                if context.get('sensor_types'):
                    types_str = ', '.join([f"{count} {sensor_type}" for sensor_type, count in context['sensor_types'].items()])
                    context_prompt += f" ({types_str})"
                context_prompt += "\n"
                
                # If user is asking about sensor data, fetch detailed statistics
                if self._should_fetch_sensor_details(user_message):
                    sensor_details = self._get_sensor_data_details(entry_id, limit=100)
                    if 'error' not in sensor_details:
                        context_prompt += "\n**Detailed Sensor Statistics:**\n"
                        for sensor_type, stats in sensor_details.items():
                            context_prompt += f"\n  {sensor_type}:\n"
                            if 'average' in stats:
                                unit = stats.get('unit', '')
                                context_prompt += f"    - Latest: {stats['latest']:.2f}{unit}\n"
                                context_prompt += f"    - Average: {stats['average']:.2f}{unit} (based on {stats['count']} readings)\n"
                                context_prompt += f"    - Min: {stats['min']:.2f}{unit}, Max: {stats['max']:.2f}{unit}\n"
                                context_prompt += f"    - Median: {stats['median']:.2f}{unit}\n"
                                if 'std_dev' in stats:
                                    context_prompt += f"    - Std Dev: {stats['std_dev']:.2f}{unit}\n"
                                if 'recent_readings' in stats:
                                    context_prompt += f"    - Recent readings (with timestamps):\n"
                                    for r in stats['recent_readings'][:5]:
                                        # Format timestamp nicely
                                        try:
                                            from datetime import datetime
                                            dt = datetime.fromisoformat(r['time'])
                                            time_str = dt.strftime('%Y-%m-%d %H:%M:%S')
                                        except:
                                            time_str = r['time']
                                        context_prompt += f"      • {r['value']:.2f}{unit} at {time_str}\n"
                            else:
                                context_prompt += f"    - {stats.get('note', 'Data available')}\n"
            
            # Add greeting for first message
            if is_first_message:
                context_prompt += f"\n\nUser's first message: {user_message}\n\n"
                context_prompt += """Please provide a helpful, friendly response that:
1. Briefly acknowledges the entry details
2. Highlights interesting or important aspects (like overdue dates, recent activity, etc.)
3. Offers to help with questions or provide insights
4. Keep your response concise but informative"""
            else:
                context_prompt += f"\n\nUser's question: {user_message}\n\n"
                context_prompt += "Please provide a helpful response based on the entry context above."
            
            # Generate response
            response = self.model.generate_content(context_prompt)
            
            if response and response.text:
                return response.text.strip()
            
            return None
            
        except Exception as e:
            logger.error(f"Error in chat_about_entry: {str(e)}")
            return f"I apologize, but I encountered an error: {str(e)}"
    
    def compose_note(self, entry_id: int, user_message: str, note_context: dict = None, attachment_files: list = None, chat_history: list = None) -> Optional[Dict[str, Any]]:
        """
        Compose a note for an entry based on user's intent and context
        
        Args:
            entry_id: The ID of the entry to create the note for
            user_message: The user's message describing what they want in the note
            note_context: Additional context including note type, current draft, etc.
            attachment_files: List of files user wants to include (file info for AI to interpret)
            chat_history: Previous conversation messages for context
            
        Returns:
            Dictionary with proposed note structure or None if failed
        """
        if not self.is_available():
            logger.warning("AI service not available - check GEMINI_API_KEY")
            return {'error': 'AI service is not available. Please check configuration.'}
        
        try:
            # Check if user is asking about existing note attachments
            asking_about_attachments = any(keyword in user_message.lower() for keyword in [
                'previous note', 'existing note', 'attachment', 'photo', 'image', 'picture'
            ])
            
            logger.info(f"User message: '{user_message}' - asking_about_attachments: {asking_about_attachments}")
            
            # Gather entry context (include all notes if asking about attachments)
            context = self._gather_entry_context(entry_id, include_all_notes=asking_about_attachments)
            
            if 'error' in context:
                return {'error': context['error']}
            
            # Get available note types for this entry
            note_types = self._get_entry_note_types(entry_id)
            logger.info(f"Note types for entry {entry_id}: {note_types}")
            
            # Build related entries summary from context (which already has this data)
            related_entries = "No related entries."
            if context.get('relationships_count', 0) > 0 and context.get('relationships'):
                related_entries_list = []
                for rel in context['relationships']:
                    # Extract entry ID from the relationship data
                    # We need to query to get the ID since context doesn't include it
                    related_entries_list.append(
                        f"  - {rel['title']} ({rel['type']}) - {rel['relationship_type']}"
                    )
                related_entries = '\n'.join(related_entries_list)
                
                # Now get the actual IDs for these entries
                try:
                    from flask import g
                    if 'db' not in g:
                        from ..db import get_connection
                        g.db = get_connection()
                    
                    cursor = g.db.cursor()
                    # Get all related entry IDs with their details
                    cursor.execute('''
                        SELECT 
                            e2.id,
                            e2.title,
                            et2.singular_label as type,
                            COALESCE(rd.name, 'Related to') as relationship_type
                        FROM EntryRelationship er
                        JOIN Entry e2 ON (
                            CASE 
                                WHEN er.source_entry_id = ? THEN er.target_entry_id
                                ELSE er.source_entry_id
                            END = e2.id
                        )
                        JOIN EntryType et2 ON e2.entry_type_id = et2.id
                        LEFT JOIN RelationshipDefinition rd ON er.relationship_type = rd.id
                        WHERE er.source_entry_id = ? OR er.target_entry_id = ?
                        LIMIT 50
                    ''', (entry_id, entry_id, entry_id))
                    
                    rows = cursor.fetchall()
                    if rows:
                        related_entries_list = []
                        for row in rows:
                            related_entries_list.append(
                                f"  - ID {row['id']}: {row['title']} ({row['type']}) - {row['relationship_type']}"
                            )
                        related_entries = '\n'.join(related_entries_list)
                except Exception as e:
                    logger.error(f"Error getting related entry IDs: {e}")
            
            logger.info(f"Related entries for entry {entry_id}: {related_entries}")
            
            # Build prompt for note composition
            base_prompt = self._get_base_prompt()
            
            from datetime import datetime
            current_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            prompt = f"""
{base_prompt}

You are helping compose a note for an entry in a project management application.

**Current Date/Time:** {current_datetime}

**Entry Context:**
- Title: {context['title']}
- Type: {context['entry_type']}
- Status: {context['status']}
- Description: {context['description']}
- Existing Notes: {context.get('total_notes', 0)} notes already exist
- Recent Notes: {', '.join([n['title'] for n in context.get('recent_notes', [])[:3]])} (most recent 3)

**Available Note Types:** {', '.join(note_types)}

**Related Entries Available for Association:**
{related_entries}

IMPORTANT: These entries are already related to the current entry. You can associate this note with any of them if relevant.
When user mentions any of these entries by name or refers to them contextually, include their ID in associated_entry_ids.
"""
            
            # Add conversation history if provided
            if chat_history and len(chat_history) > 0:
                prompt += "\n**Previous Conversation:**\n"
                # Include last 5 exchanges to keep context manageable
                for msg in chat_history[-10:]:
                    role = "User" if msg['role'] == 'user' else "Assistant"
                    prompt += f"{role}: {msg['content']}\n"
                prompt += "\n"
            
            prompt += f"""
**User's Current Request:**
{user_message}
"""
            
            # Add context about existing draft if provided
            if note_context and 'current_draft' in note_context:
                prompt += f"""
**Current Draft:**
{json.dumps(note_context['current_draft'], indent=2)}

**User wants to refine this draft. Apply their requested changes.**
- If they ask to change note type, update the note_type field to match their request
- If they ask to modify content, update note_text accordingly
- If they want to add/remove links or associations, update those fields
- You can change ANY aspect of the note based on user feedback
"""
            else:
                prompt += """
**Task:** Based on the user's request, propose a complete note structure.

**CRITICAL: When NOT to create a note:**
- If user is asking a QUESTION about existing notes/data (e.g., "Can you see...", "What are...", "Show me...")
- If user wants to VIEW information, not CREATE a note
- If user is exploring/understanding the data

**In these cases, respond with:**
{
  "reasoning": "User is asking a question, not requesting note creation. They should ask this in the general chat, not in note composer mode.",
  "error": "This appears to be a question rather than a note creation request. Please exit note composer mode and ask your question in the general chat, or tell me what note you'd like to create."
}

**When TO create a note:**
- User explicitly asks to "create", "write", "compose", "document", "add", "record" a note
- User describes what should be in a new note
- User provides content for documentation
"""
            
            # Add attachment context if files are provided
            image_count = 0
            if attachment_files:
                prompt += f"""
**User has attached {len(attachment_files)} file(s) to this message:**
"""
                for i, file_info in enumerate(attachment_files, 1):
                    prompt += f"  {i}. {file_info.get('filename', 'Unknown')} ({file_info.get('type', 'Unknown type')})\n"
                    if file_info.get('preview'):
                        prompt += f"     Preview: {file_info['preview']}\n"
                    if file_info.get('type', '').startswith('image/'):
                        image_count += 1
                
                if image_count > 0:
                    prompt += f"\n**IMPORTANT:** {image_count} image(s) are included below for you to analyze. Read any text, measurements, or data visible in the images.\n"
            
            # Add context about existing note attachments if loaded
            if asking_about_attachments and context.get('all_notes'):
                existing_images = []
                for note in context['all_notes']:
                    if note.get('attachments'):
                        for file_path in note['attachments']:
                            if any(file_path.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp']):
                                existing_images.append((note['title'], file_path.split('/')[-1]))
                
                if existing_images:
                    prompt += f"""
**Images from existing notes (included below for analysis ONLY - will NOT be attached to new note):**
"""
                    for note_title, filename in existing_images:
                        prompt += f"  - {filename} (from note: {note_title})\n"
                    
                    prompt += f"\n**IMPORTANT:** These {len(existing_images)} image(s) from previous notes are included below for you to analyze and extract data from. However, they will NOT be attached to the new note you're composing - they're just for reference. Extract any relevant data (readings, measurements, text, etc.) and include it in the note_text.\n"
            
            prompt += """
Please respond with a JSON object containing the proposed note structure:

{
  "note_type": "one of the available note types",
  "note_title": "a clear, descriptive title",
  "note_text": "the main body of the note (can use markdown)",
  "url_bookmarks": [
    {"friendly_name": "Link name", "url": "https://example.com"}
  ],
  "associated_entry_ids": [list of entry IDs to associate with, if relevant],
  "reasoning": "brief explanation of your choices"
}

CRITICAL RULES FOR URL BOOKMARKS:
- ONLY include URLs if:
  a) The user explicitly provided them in their message, OR
  b) The user asks for Wikipedia/reference links and you can construct accurate Wikipedia URLs
- For Wikipedia links: Use format https://en.wikipedia.org/wiki/Article_Name (replace spaces with underscores)
- DO NOT generate fake URLs or use placeholder domains (example.com, etc.)
- If user asks for a link but didn't provide URL and it's not Wikipedia, leave url_bookmarks EMPTY []
- If user wants to link to another entry in this system, use associated_entry_ids instead of url_bookmarks
- Only suggest Wikipedia URLs if you're confident the article exists (common topics, ingredients, etc.)
- For product links, manufacturer sites, or specific resources: DO NOT invent URLs - ask user to provide them

CRITICAL RULES FOR ENTRY ASSOCIATIONS:
- ACTIVELY look for opportunities to associate this note with related entries
- If user mentions any entry name from the "Related Entries" list, include that entry's ID
- If note content is about/references any related entry, include its ID
- If user says "link to X entry" or "associate with Y", find that entry and include its ID
- Multiple associations are encouraged when relevant
- This creates cross-references that help users navigate between related items

CRITICAL RULES FOR NOTE TYPE:
- When user asks to change note type (e.g., "make this a Recipe note", "change to Technical"), UPDATE the note_type field
- Note type changes should be honored immediately - don't keep the old type
- Available types are listed above - choose from that list ONLY
- If user says "change type to X" or "make this a X note", set note_type to "X" (if it's in the available list)
- In refinement conversations, note_type can change as easily as any other field

Other Important Rules:
- Make the note_text comprehensive but concise
- Use markdown formatting where appropriate (bullet points, headers, etc.)
- In reasoning, mention which entries you're associating and why
- Mention in reasoning if you changed the note type based on user request
- Mention in reasoning if user requested links but didn't provide URLs

Respond ONLY with the JSON object, no additional text.
"""
            
            # Log the key parts of the prompt for debugging
            logger.info(f"Sending to AI - Available Note Types: {', '.join(note_types)}")
            logger.info(f"Sending to AI - Related Entries Count: {related_entries.count('ID')}")
            
            # Build content list for multimodal request (text + images)
            content_parts = [prompt]
            
            # Add image files if provided
            if attachment_files:
                import base64
                import os
                from PIL import Image
                
                for file_info in attachment_files:
                    file_data = file_info.get('data')  # Base64 encoded data
                    file_type = file_info.get('type', '')
                    
                    if file_data and file_type.startswith('image/'):
                        try:
                            # Extract base64 data (remove data:image/...;base64, prefix if present)
                            if ',' in file_data:
                                file_data = file_data.split(',', 1)[1]
                            
                            # Decode base64 to bytes
                            image_bytes = base64.b64decode(file_data)
                            
                            # Load image with PIL
                            from io import BytesIO
                            image = Image.open(BytesIO(image_bytes))
                            
                            # Add image to content parts
                            content_parts.append(image)
                            logger.info(f"Added image to AI request: {file_info.get('filename', 'unknown')}")
                        except Exception as e:
                            logger.error(f"Failed to process image {file_info.get('filename')}: {e}")
            
            # Load images from existing notes if user is asking about them
            logger.info(f"asking_about_attachments={asking_about_attachments}, has all_notes={bool(context.get('all_notes'))}")
            if asking_about_attachments and context.get('all_notes'):
                import os
                from PIL import Image
                
                logger.info(f"Found {len(context['all_notes'])} notes to check for attachments")
                images_loaded = 0
                max_images = 10  # Limit to prevent API overload
                
                for note in context['all_notes']:
                    if images_loaded >= max_images:
                        logger.warning(f"Reached maximum image limit ({max_images}), skipping remaining images")
                        break
                        
                    logger.info(f"Checking note: {note.get('title')} - attachments: {note.get('attachments')}")
                    if note.get('attachments'):
                        for file_path in note['attachments']:
                            if images_loaded >= max_images:
                                break
                                
                            try:
                                # Build full path to uploaded file
                                full_path = os.path.join('/app/app/static', file_path.lstrip('/'))
                                
                                # Check if file exists
                                if not os.path.exists(full_path):
                                    logger.warning(f"Image file not found: {full_path}")
                                    continue
                                
                                # Check if it's an image
                                if any(file_path.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp']):
                                    # Load image with PIL
                                    image = Image.open(full_path)
                                    content_parts.append(image)
                                    images_loaded += 1
                                    logger.info(f"Added existing note image to AI request: {file_path}")
                            except Exception as e:
                                logger.error(f"Failed to load existing note image {file_path}: {e}")
            
            # Send to Gemini with multimodal content
            logger.info(f"Sending to Gemini with {len(content_parts)} content parts ({len(content_parts) - 1} images)")
            try:
                response = self.model.generate_content(content_parts)
            except Exception as e:
                logger.error(f"Gemini API error: {e}")
                return {'error': f'AI service error: {str(e)}'}
            
            if response and response.text:
                response_text = response.text.strip()
                
                # Remove markdown code blocks if present
                if response_text.startswith('```json'):
                    response_text = response_text.replace('```json', '').replace('```', '').strip()
                elif response_text.startswith('```'):
                    response_text = response_text.replace('```', '').strip()
                
                try:
                    note_proposal = json.loads(response_text)
                    return note_proposal
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse note composition JSON: {e}")
                    logger.error(f"Raw response: {response_text}")
                    return {'error': 'Failed to parse AI response'}
            
            return None
            
        except Exception as e:
            logger.error(f"Error in compose_note: {str(e)}")
            return {'error': str(e)}
    
    def _get_entry_note_types(self, entry_id: int) -> list:
        """Get available note types for an entry"""
        try:
            from flask import g, current_app
            import sqlite3
            
            if 'db' not in g:
                db_path = current_app.config['DATABASE_PATH']
                g.db = sqlite3.connect(db_path)
                g.db.row_factory = sqlite3.Row
            
            cursor = g.db.cursor()
            cursor.execute('''
                SELECT et.note_types
                FROM Entry e
                JOIN EntryType et ON e.entry_type_id = et.id
                WHERE e.id = ?
            ''', (entry_id,))
            
            row = cursor.fetchone()
            if row and row['note_types']:
                # Split comma-separated note types
                return [nt.strip() for nt in row['note_types'].split(',')]
            
            return ['General']  # Default fallback
            
        except Exception as e:
            logger.error(f"Error getting note types: {e}")
            return ['General']
    
    def _get_related_entries_summary(self, entry_id: int) -> str:
        """Get a summary of related entries for context"""
        try:
            from flask import g, current_app
            import sqlite3
            
            if 'db' not in g:
                db_path = current_app.config['DATABASE_PATH']
                g.db = sqlite3.connect(db_path)
                g.db.row_factory = sqlite3.Row
            
            cursor = g.db.cursor()
            cursor.execute('''
                SELECT 
                    e2.id,
                    e2.title,
                    et2.singular_label as type,
                    r.relationship_type
                FROM EntryRelationship r
                JOIN Entry e2 ON (
                    CASE 
                        WHEN r.from_entry_id = ? THEN r.to_entry_id
                        ELSE r.from_entry_id
                    END = e2.id
                )
                JOIN EntryType et2 ON e2.entry_type_id = et2.id
                WHERE r.from_entry_id = ? OR r.to_entry_id = ?
                LIMIT 20
            ''', (entry_id, entry_id, entry_id))
            
            rows = cursor.fetchall()
            
            if not rows:
                return "No related entries."
            
            summary = []
            for row in rows:
                summary.append(f"  - ID {row['id']}: {row['title']} ({row['type']}) - {row['relationship_type']}")
            
            return '\n'.join(summary)
            
        except Exception as e:
            logger.error(f"Error getting related entries: {e}")
            return "Error fetching related entries."
    
    def generate_diagram(self, user_request: str, current_diagram: Optional[str] = None, entry_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        Generate or modify Draw.io diagram based on natural language request
        
        Args:
            user_request: Natural language description of what to create/modify
            current_diagram: Existing diagram XML (if modifying)
            entry_id: Optional entry ID for context
            
        Returns:
            Dictionary with 'diagram_xml' and 'explanation' or None if failed
        """
        if not self.is_available():
            return None
        
        try:
            # Build the system prompt for diagram generation
            system_prompt = self._build_diagram_system_prompt()
            
            # Build user prompt
            user_prompt = f"""User Request: {user_request}

"""
            
            if current_diagram and current_diagram.strip():
                user_prompt += f"""Current Diagram XML:
```xml
{current_diagram}
```

Please modify this diagram according to the user's request. Preserve existing elements unless explicitly asked to remove them.
"""
            else:
                user_prompt += "Please create a new diagram from scratch based on this request.\n"
            
            # Add entry context if available
            if entry_id:
                try:
                    from ..db import get_db
                    db = get_db()
                    cursor = db.cursor()
                    cursor.execute('''
                        SELECT e.title, e.description, et.singular_label as type
                        FROM Entry e
                        JOIN EntryType et ON e.entry_type_id = et.id
                        WHERE e.id = ?
                    ''', (entry_id,))
                    entry = cursor.fetchone()
                    if entry:
                        user_prompt += f"\n**Entry Context:**\n"
                        user_prompt += f"Title: {entry['title']}\n"
                        user_prompt += f"Type: {entry['type']}\n"
                        if entry['description']:
                            user_prompt += f"Description: {entry['description']}\n"
                except Exception as e:
                    logger.warning(f"Could not fetch entry context: {e}")
            
            user_prompt += """
**Instructions:**
1. Generate valid mxGraph XML for Draw.io
2. Use appropriate shapes and connectors
3. Position elements logically (use reasonable x,y coordinates)
4. Include proper styling (colors, borders, text)
5. Return ONLY the XML within <mxGraphModel> tags
6. Provide a brief explanation of what you created/modified
"""
            
            # Generate diagram using AI
            response = self.model.generate_content(
                [system_prompt, user_prompt],
                generation_config={
                    'temperature': 0.3,  # Lower temperature for more consistent XML output
                    'top_p': 0.95,
                    'max_output_tokens': 4096,
                }
            )
            
            if response and response.text:
                response_text = response.text.strip()
                
                # Extract XML from response
                diagram_xml = self._extract_diagram_xml(response_text)
                explanation = self._extract_explanation(response_text)
                
                if diagram_xml:
                    return {
                        'diagram_xml': diagram_xml,
                        'explanation': explanation or 'Diagram generated successfully'
                    }
                else:
                    logger.error("No valid diagram XML found in AI response")
                    return None
            
        except Exception as e:
            logger.error(f"Failed to generate diagram: {str(e)}", exc_info=True)
        
        return None
    
    def _build_diagram_system_prompt(self) -> str:
        """Build system prompt for diagram generation with mxGraph XML format guide"""
        return """You are an expert at creating Draw.io diagrams using mxGraph XML format.

**mxGraph XML Structure:**
```xml
<mxGraphModel>
  <root>
    <mxCell id="0"/>
    <mxCell id="1" parent="0"/>
    <!-- Shapes/nodes -->
    <mxCell id="2" value="Label Text" style="shape=rectangle;fillColor=#dae8fc;strokeColor=#6c8ebf;" vertex="1" parent="1">
      <mxGeometry x="100" y="100" width="120" height="60" as="geometry"/>
    </mxCell>
    <!-- Edges/connections -->
    <mxCell id="3" value="" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;" edge="1" parent="1" source="2" target="4">
      <mxGeometry relative="1" as="geometry"/>
    </mxCell>
  </root>
</mxGraphModel>
```

**Common Shapes:**
- rectangle: Standard box
- ellipse: Circle/oval
- rhombus: Diamond (for decisions)
- cylinder: Database
- hexagon: Process
- parallelogram: Input/Output
- cloud: Cloud storage
- actor: Stick figure person
- process: Rounded rectangle

**Common Styles:**
- fillColor=#dae8fc (light blue)
- fillColor=#d5e8d4 (light green)
- fillColor=#fff2cc (light yellow)
- fillColor=#f8cecc (light red)
- strokeColor=#6c8ebf (blue border)
- strokeColor=#82b366 (green border)
- rounded=1 (rounded corners)
- dashed=1 (dashed line)
- html=1 (enable HTML labels)

**Edge Styles:**
- edgeStyle=orthogonalEdgeStyle (right angles)
- edgeStyle=elbowEdgeStyle (elbow connectors)
- curved=1 (curved lines)
- endArrow=classic (arrow at end)
- endArrow=none (no arrow)

**Positioning Tips:**
- Use x,y coordinates for placement (origin is top-left)
- Spread elements 150-200 pixels apart for clarity
- Standard box size: 120x60
- Standard spacing: 200 pixels horizontal, 150 pixels vertical

**Your Task:**
Generate valid mxGraph XML based on user requests. Be creative but ensure:
1. All cell IDs are unique
2. Proper parent-child relationships (parent="1" for shapes, source/target for edges)
3. Reasonable positioning and sizing
4. Appropriate colors and styles
5. Clear, readable labels

Return your response in this format:
```xml
<mxGraphModel>
  ... your diagram XML ...
</mxGraphModel>
```

Then provide a brief explanation of what you created."""

    def _extract_diagram_xml(self, text: str) -> Optional[str]:
        """Extract mxGraph XML from AI response"""
        import re
        
        # Try to find XML within code blocks
        xml_match = re.search(r'```(?:xml)?\s*(<mxGraphModel>.*?</mxGraphModel>)\s*```', text, re.DOTALL)
        if xml_match:
            return xml_match.group(1).strip()
        
        # Try to find XML directly
        xml_match = re.search(r'(<mxGraphModel>.*?</mxGraphModel>)', text, re.DOTALL)
        if xml_match:
            return xml_match.group(1).strip()
        
        return None
    
    def _extract_explanation(self, text: str) -> Optional[str]:
        """Extract explanation text from AI response (text after XML)"""
        import re
        
        # Remove XML blocks
        cleaned_text = re.sub(r'```(?:xml)?\s*<mxGraphModel>.*?</mxGraphModel>\s*```', '', text, flags=re.DOTALL)
        cleaned_text = re.sub(r'<mxGraphModel>.*?</mxGraphModel>', '', cleaned_text, flags=re.DOTALL)
        
        # Clean up remaining text
        explanation = cleaned_text.strip()
        
        # Remove common prefixes
        explanation = re.sub(r'^(Here\'s|I\'ve created|I\'ve modified|Explanation:|Sure[,!]?\s*)', '', explanation, flags=re.IGNORECASE)
        
        return explanation.strip() if explanation else None

# Global AI service instance
ai_service = AIService()

def get_ai_service() -> AIService:
    """Get the global AI service instance"""
    return ai_service
