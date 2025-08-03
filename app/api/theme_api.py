from flask import Blueprint, request, jsonify, render_template, session, g, current_app
import sqlite3
import json

theme_api = Blueprint('theme_api', __name__)

def _hex_to_rgb(hex_color):
    """Convert hex color to RGB tuple"""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def _rgb_to_hex(rgb):
    """Convert RGB tuple to hex color"""
    return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"

def _lighten_color(hex_color, factor):
    """Lighten a hex color by a factor (0.0 = no change, 1.0 = white)"""
    try:
        r, g, b = _hex_to_rgb(hex_color)
        r = int(r + (255 - r) * factor)
        g = int(g + (255 - g) * factor)
        b = int(b + (255 - b) * factor)
        return _rgb_to_hex((min(255, r), min(255, g), min(255, b)))
    except:
        return hex_color  # Return original on error

def _darken_color(hex_color, factor):
    """Darken a hex color by a factor (0.0 = no change, 1.0 = black)"""
    try:
        r, g, b = _hex_to_rgb(hex_color)
        r = int(r * (1 - factor))
        g = int(g * (1 - factor))
        b = int(b * (1 - factor))
        return _rgb_to_hex((max(0, r), max(0, g), max(0, b)))
    except:
        return hex_color  # Return original on error

def get_db():
    """Get database connection using flexible configuration approach"""
    if 'db' not in g:
        # Try DATABASE_PATH first (Docker/production), then DATABASE (local dev)
        db_path = current_app.config.get('DATABASE_PATH')
        if not db_path:
            db_path = current_app.config.get('DATABASE', 'template.db')
        
        current_app.logger.info(f"Theme API connecting to database: {db_path}")
        g.db = sqlite3.connect(db_path)
        g.db.row_factory = sqlite3.Row
    return g.db

@theme_api.route('/theme_settings', methods=['GET', 'POST'])
def handle_theme_settings():
    try:
        db = get_db()
        
        if request.method == 'POST':
            try:
                data = request.json
                
                if not data:
                    return jsonify({'error': 'No JSON data provided'}), 400
                
                # Validate input data
                theme = data.get('theme', 'default')
                dark_mode = bool(data.get('dark_mode', False))
                font_size = data.get('font_size', 'normal')
                high_contrast = bool(data.get('high_contrast', False))
                custom_colors = data.get('custom_colors', {})
                custom_light_mode = data.get('custom_light_mode', {})
                custom_dark_mode = data.get('custom_dark_mode', {})
                
                # Valid options validation
                valid_themes = ['default', 'emerald', 'purple', 'amber', 'custom']
                valid_font_sizes = ['small', 'normal', 'large', 'extra-large']
                
                if theme not in valid_themes:
                    return jsonify({'error': 'Invalid theme selected'}), 400
                
                if font_size not in valid_font_sizes:
                    return jsonify({'error': 'Invalid font size selected'}), 400
                
                # Validate custom colors if theme is custom
                if theme == 'custom' and custom_colors:
                    valid_color_keys = ['primary', 'primary_hover', 'secondary', 'success', 'danger', 'warning', 'info']
                    for key, value in custom_colors.items():
                        if key not in valid_color_keys:
                            return jsonify({'error': f'Invalid custom color key: {key}'}), 400
                        # Basic hex color validation
                        if not value.startswith('#') or len(value) != 7:
                            return jsonify({'error': f'Invalid color format for {key}. Use hex format like #000000'}), 400
                
                # Validate custom light/dark mode colors
                valid_mode_keys = ['bg_body', 'bg_card', 'bg_surface', 'text', 'text_muted', 'border']
                for mode_name, mode_colors in [('light', custom_light_mode), ('dark', custom_dark_mode)]:
                    for key, value in mode_colors.items():
                        if key not in valid_mode_keys:
                            return jsonify({'error': f'Invalid custom {mode_name} mode color key: {key}'}), 400
                        if not value.startswith('#') or len(value) != 7:
                            return jsonify({'error': f'Invalid {mode_name} mode color format for {key}. Use hex format like #000000'}), 400
                
                # Store theme settings in database
                cursor = db.cursor()
                
                # Check if theme settings exist
                cursor.execute("SELECT COUNT(*) FROM SystemParameters WHERE parameter_name LIKE 'theme_%'")
                existing_count = cursor.fetchone()[0]
                
                # Save or update theme settings
                theme_settings = [
                    ('theme_color_scheme', theme),
                    ('theme_dark_mode', str(dark_mode)),
                    ('theme_font_size', font_size),
                    ('theme_high_contrast', str(high_contrast))
                ]
                
                # Add custom colors if theme is custom
                if theme == 'custom' and custom_colors:
                    theme_settings.append(('theme_custom_colors', json.dumps(custom_colors)))
                elif theme != 'custom':
                    # Clear custom colors if switching away from custom theme
                    cursor.execute("DELETE FROM SystemParameters WHERE parameter_name = 'theme_custom_colors'")
                
                # Add custom light/dark mode colors
                if custom_light_mode:
                    theme_settings.append(('theme_custom_light_mode', json.dumps(custom_light_mode)))
                else:
                    cursor.execute("DELETE FROM SystemParameters WHERE parameter_name = 'theme_custom_light_mode'")
                    
                if custom_dark_mode:
                    theme_settings.append(('theme_custom_dark_mode', json.dumps(custom_dark_mode)))
                else:
                    cursor.execute("DELETE FROM SystemParameters WHERE parameter_name = 'theme_custom_dark_mode'")
                
                for param_name, param_value in theme_settings:
                    cursor.execute("""
                        INSERT OR REPLACE INTO SystemParameters (parameter_name, parameter_value)
                        VALUES (?, ?)
                    """, (param_name, param_value))
                
                db.commit()
                
                # Update session for immediate effect
                session['theme_settings'] = {
                    'theme': theme,
                    'dark_mode': dark_mode,
                    'font_size': font_size,
                    'high_contrast': high_contrast,
                    'custom_colors': custom_colors if theme == 'custom' else {},
                    'custom_light_mode': custom_light_mode,
                    'custom_dark_mode': custom_dark_mode
                }
                
                return jsonify({
                    'success': True,
                    'message': 'Theme settings saved successfully'
                })
                
            except Exception as e:
                db.rollback()
                return jsonify({'error': f'Database error: {str(e)}'}), 500
        
        else:  # GET request
            try:
                cursor = db.cursor()
                
                # Retrieve current theme settings
                cursor.execute("""
                    SELECT parameter_name, parameter_value FROM SystemParameters 
                    WHERE parameter_name LIKE 'theme_%'
                """)
                
                settings = {}
                custom_colors = {}
                custom_light_mode = {}
                custom_dark_mode = {}
                
                for parameter_name, parameter_value in cursor.fetchall():
                    if parameter_name == 'theme_color_scheme':
                        settings['theme'] = parameter_value
                    elif parameter_name == 'theme_dark_mode':
                        settings['dark_mode'] = parameter_value.lower() == 'true'
                    elif parameter_name == 'theme_font_size':
                        settings['font_size'] = parameter_value
                    elif parameter_name == 'theme_high_contrast':
                        settings['high_contrast'] = parameter_value.lower() == 'true'
                    elif parameter_name == 'theme_custom_colors':
                        try:
                            custom_colors = json.loads(parameter_value)
                        except (json.JSONDecodeError, TypeError):
                            custom_colors = {}
                    elif parameter_name == 'theme_custom_light_mode':
                        try:
                            custom_light_mode = json.loads(parameter_value)
                        except (json.JSONDecodeError, TypeError):
                            custom_light_mode = {}
                    elif parameter_name == 'theme_custom_dark_mode':
                        try:
                            custom_dark_mode = json.loads(parameter_value)
                        except (json.JSONDecodeError, TypeError):
                            custom_dark_mode = {}
                
                # Set defaults if not found
                settings.setdefault('theme', 'default')
                settings.setdefault('dark_mode', False)
                settings.setdefault('font_size', 'normal')
                settings.setdefault('high_contrast', False)
                settings['custom_colors'] = custom_colors
                settings['custom_light_mode'] = custom_light_mode
                settings['custom_dark_mode'] = custom_dark_mode
                
                return jsonify(settings)
                
            except Exception as e:
                return jsonify({'error': f'Database error: {str(e)}'}), 500
                
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500


def get_current_theme_settings():
    """Helper function to get current theme settings for template rendering"""
    try:
        # Try DATABASE_PATH first (Docker/production), then DATABASE (local dev)
        db_path = current_app.config.get('DATABASE_PATH')
        if not db_path:
            db_path = current_app.config.get('DATABASE', 'template.db')
            
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT parameter_name, parameter_value FROM SystemParameters 
            WHERE parameter_name LIKE 'theme_%'
        """)
        
        settings = {}
        custom_colors = {}
        custom_light_mode = {}
        custom_dark_mode = {}
        
        for parameter_name, parameter_value in cursor.fetchall():
            if parameter_name == 'theme_color_scheme':
                settings['current_theme'] = parameter_value
            elif parameter_name == 'theme_dark_mode':
                settings['dark_mode_enabled'] = parameter_value.lower() == 'true'
            elif parameter_name == 'theme_font_size':
                settings['font_size'] = parameter_value
            elif parameter_name == 'theme_high_contrast':
                settings['high_contrast_enabled'] = parameter_value.lower() == 'true'
            elif parameter_name == 'theme_custom_colors':
                try:
                    custom_colors = json.loads(parameter_value)
                except (json.JSONDecodeError, TypeError):
                    custom_colors = {}
            elif parameter_name == 'theme_custom_light_mode':
                try:
                    custom_light_mode = json.loads(parameter_value)
                except (json.JSONDecodeError, TypeError):
                    custom_light_mode = {}
            elif parameter_name == 'theme_custom_dark_mode':
                try:
                    custom_dark_mode = json.loads(parameter_value)
                except (json.JSONDecodeError, TypeError):
                    custom_dark_mode = {}
        
        # Set defaults
        settings.setdefault('current_theme', 'default')
        settings.setdefault('dark_mode_enabled', False)
        settings.setdefault('font_size', 'normal')
        settings.setdefault('high_contrast_enabled', False)
        settings['custom_colors'] = custom_colors
        settings['custom_light_mode'] = custom_light_mode
        settings['custom_dark_mode'] = custom_dark_mode
        
        conn.close()
        return settings
        
    except Exception as e:
        # Return defaults on error
        return {
            'current_theme': 'default',
            'dark_mode_enabled': False,
            'font_size': 'normal',
            'high_contrast_enabled': False,
            'custom_colors': {},
            'custom_light_mode': {},
            'custom_dark_mode': {}
        }


def generate_theme_css(settings=None):
    """Generate clean CSS variables based on theme settings"""
    if settings is None:
        settings = get_current_theme_settings()
    
    theme = settings.get('current_theme', 'default')
    dark_mode = settings.get('dark_mode_enabled', False)
    custom_colors = settings.get('custom_colors', {})
    custom_light_mode = settings.get('custom_light_mode', {})
    custom_dark_mode = settings.get('custom_dark_mode', {})
    
    # Define color schemes
    color_schemes = {
        'default': {
            'primary': '#0d6efd',
            'primary_hover': '#0b5ed7',
            'secondary': '#6c757d',
            'success': '#198754',
            'danger': '#dc3545',
            'warning': '#ffc107',
            'info': '#0dcaf0'
        },
        'emerald': {
            'primary': '#10b981',
            'primary_hover': '#059669',
            'secondary': '#6b7280',
            'success': '#059669',
            'danger': '#ef4444',
            'warning': '#f59e0b',
            'info': '#06b6d4'
        },
        'purple': {
            'primary': '#8b5cf6',
            'primary_hover': '#7c3aed',
            'secondary': '#6b7280',
            'success': '#10b981',
            'danger': '#ef4444',
            'warning': '#f59e0b',
            'info': '#06b6d4'
        },
        'amber': {
            'primary': '#f59e0b',
            'primary_hover': '#d97706',
            'secondary': '#6b7280',
            'success': '#10b981',
            'danger': '#ef4444',
            'warning': '#f97316',
            'info': '#06b6d4'
        },
        'custom': {
            'primary': '#0d6efd',
            'primary_hover': '#0b5ed7',
            'secondary': '#6c757d',
            'success': '#198754',
            'danger': '#dc3545',
            'warning': '#ffc107',
            'info': '#0dcaf0'
        }
    }
    
    # Get colors for selected theme
    colors = color_schemes.get(theme, color_schemes['default'])
    
    # Override with custom colors if using custom theme
    if theme == 'custom' and custom_colors:
        colors.update(custom_colors)
    
    # Define default light/dark mode colors
    default_light_mode = {
        'bg_body': '#ffffff',
        'bg_card': '#ffffff', 
        'bg_surface': '#f8f9fa',
        'text': '#212529',
        'text_muted': '#6c757d',
        'border': '#dee2e6'
    }
    
    default_dark_mode = {
        'bg_body': '#0d1117',
        'bg_card': '#161b22',
        'bg_surface': '#21262d', 
        'text': '#f0f6fc',
        'text_muted': '#8b949e',
        'border': '#30363d'
    }
    
    # Base CSS with theme variables
    css = f"""
        :root {{
            /* Theme Colors */
            --theme-primary: {colors['primary']};
            --theme-primary-hover: {colors['primary_hover']};
            --theme-secondary: {colors['secondary']};
            --theme-success: {colors['success']};
            --theme-danger: {colors['danger']};
            --theme-warning: {colors['warning']};
            --theme-info: {colors['info']};
            
            /* Primary text color for buttons */
            --theme-primary-text: white;
    """
    
    # Add dark mode or light mode specific variables
    if dark_mode:
        # Use custom dark mode colors or defaults
        dark_colors = default_dark_mode.copy()
        if custom_dark_mode:
            dark_colors.update(custom_dark_mode)
            
        # Calculate theme-appropriate dark mode info colors based on selected theme
        if theme == 'emerald':
            info_bg = "#0a2f23"
            info_border = "#059669" 
            info_text = "#6ee7b7"
        elif theme == 'purple':
            info_bg = "#2d1b3d"
            info_border = "#7c3aed"
            info_text = "#c4b5fd"
        elif theme == 'amber':
            info_bg = "#3d2f1a"
            info_border = "#d97706"
            info_text = "#fbbf24"
        elif theme == 'custom':
            # Generate appropriate dark mode colors for custom theme
            primary_color = colors['primary']
            info_bg = _darken_color(primary_color, 0.8)
            info_border = colors['primary']
            info_text = _lighten_color(primary_color, 0.3)
        else:  # default
            info_bg = "#0c2d48"
            info_border = "#1f6feb"
            info_text = "#79c0ff"
            
        css += f"""
            /* Dark Mode Colors */
            --theme-bg-body: {dark_colors['bg_body']};
            --theme-bg-card: {dark_colors['bg_card']};
            --theme-bg-surface: {dark_colors['bg_surface']};
            --theme-text: {dark_colors['text']};
            --theme-text-muted: {dark_colors['text_muted']};
            --theme-border: {dark_colors['border']};
            --theme-bg-info: {info_bg};
            --theme-border-info: {info_border};
            --theme-text-info: {info_text};
            
            /* Bootstrap CSS Variable Overrides */
            --bs-primary: {colors['primary']};
            --bs-secondary: {colors['secondary']};
            --bs-success: {colors['success']};
            --bs-danger: {colors['danger']};
            --bs-warning: {colors['warning']};
            --bs-info: {colors['info']};
            --bs-info-rgb: 6, 182, 212;
            --bs-info-bg-subtle: {info_bg};
            --bs-info-border-subtle: {info_border};
            --bs-info-text-emphasis: {info_text};
        }}
        
        /* Set dark mode for Bootstrap */
        html {{
            color-scheme: dark;
        }}
        
        [data-bs-theme="dark"] {{
            color-scheme: dark;
        }}
        """
    else:
        # Use custom light mode colors or defaults
        light_colors = default_light_mode.copy()
        if custom_light_mode:
            light_colors.update(custom_light_mode)
            
        # Calculate theme-appropriate light mode info colors based on selected theme
        if theme == 'emerald':
            info_bg = "#d1fae5"
            info_border = "#a7f3d0"
            info_text = "#064e3b"
        elif theme == 'purple':
            info_bg = "#ede9fe"
            info_border = "#c4b5fd"
            info_text = "#581c87"
        elif theme == 'amber':
            info_bg = "#fef3c7"
            info_border = "#fde68a"
            info_text = "#92400e"
        elif theme == 'custom':
            # Generate appropriate light mode colors for custom theme
            primary_color = colors['primary']
            info_bg = _lighten_color(primary_color, 0.85)
            info_border = _lighten_color(primary_color, 0.5)
            info_text = _darken_color(primary_color, 0.6)
        else:  # default
            info_bg = "#cff4fc"
            info_border = "#b6effb"
            info_text = "#055160"
            
        css += f"""
            /* Light Mode Colors */
            --theme-bg-body: {light_colors['bg_body']};
            --theme-bg-card: {light_colors['bg_card']};
            --theme-bg-surface: {light_colors['bg_surface']};
            --theme-text: {light_colors['text']};
            --theme-text-muted: {light_colors['text_muted']};
            --theme-border: {light_colors['border']};
            --theme-bg-info: {info_bg};
            --theme-border-info: {info_border};
            --theme-text-info: {info_text};
            
            /* Bootstrap CSS Variable Overrides */
            --bs-primary: {colors['primary']};
            --bs-secondary: {colors['secondary']};
            --bs-success: {colors['success']};
            --bs-danger: {colors['danger']};
            --bs-warning: {colors['warning']};
            --bs-info: {colors['info']};
            --bs-info-rgb: 6, 182, 212;
            --bs-info-bg-subtle: {info_bg};
            --bs-info-border-subtle: {info_border};
            --bs-info-text-emphasis: {info_text};
        }}
        """
    
    return css
