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
                return
            
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel(model_name)
            self.is_configured = True
            logger.info(f"Gemini AI successfully configured with model: {model_name}")
            
        except Exception as e:
            logger.error(f"Failed to configure Gemini AI: {str(e)}")
            self.is_configured = False
    
    def is_available(self) -> bool:
        """Check if AI service is available and configured"""
        # If not currently configured, try to reconfigure (picks up system parameter changes)
        if not self.is_configured:
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
        
        Requirements:
        - Keep it between 1-3 sentences
        - Be factual and informative
        - Include relevant details that would be useful in a database/inventory system
        - Use a professional, neutral tone
        - Don't include promotional language
        
        Focus on practical information that would help someone understand what this {entry_type} is and its key characteristics.
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
        
        Task: Please improve this description by making it clearer, more detailed, and better organized:
        
        Original description:
        {description}
        
        Guidelines:
        - Maintain the original meaning and intent
        - Improve clarity and readability
        - Add relevant details if the description seems incomplete
        - Fix any grammar or spelling issues
        - Organize information logically
        - Keep the tone professional and informative
        - Don't change factual information, only improve presentation
        - Make it more engaging while remaining accurate
        
        Return the improved version of the description.
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

# Global AI service instance
ai_service = AIService()

def get_ai_service() -> AIService:
    """Get the global AI service instance"""
    return ai_service
