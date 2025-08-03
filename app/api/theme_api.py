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
            
            /* Enhanced color variations for better theme coverage */
            --theme-primary-rgb: {','.join(str(c) for c in _hex_to_rgb(colors['primary']))};
            --theme-secondary-rgb: {','.join(str(c) for c in _hex_to_rgb(colors['secondary']))};
            --theme-success-rgb: {','.join(str(c) for c in _hex_to_rgb(colors['success']))};
            --theme-danger-rgb: {','.join(str(c) for c in _hex_to_rgb(colors['danger']))};
            --theme-warning-rgb: {','.join(str(c) for c in _hex_to_rgb(colors['warning']))};
            --theme-info-rgb: {','.join(str(c) for c in _hex_to_rgb(colors['info']))};
            
            /* Derived color variations */
            --theme-primary-lighter: {_lighten_color(colors['primary'], 0.1)};
            --theme-primary-darker: {_darken_color(colors['primary'], 0.1)};
            --theme-secondary-hover: {_darken_color(colors['secondary'], 0.1)};
            --theme-success-hover: {_darken_color(colors['success'], 0.1)};
            --theme-danger-hover: {_darken_color(colors['danger'], 0.1)};
            --theme-warning-hover: {_darken_color(colors['warning'], 0.1)};
            --theme-info-hover: {_darken_color(colors['info'], 0.1)};
            
            /* Subtle color variations for backgrounds */
            --theme-primary-subtle: rgba({','.join(str(c) for c in _hex_to_rgb(colors['primary']))}, 0.1);
            --theme-secondary-subtle: rgba({','.join(str(c) for c in _hex_to_rgb(colors['secondary']))}, 0.1);
            --theme-success-subtle: rgba({','.join(str(c) for c in _hex_to_rgb(colors['success']))}, 0.1);
            --theme-danger-subtle: rgba({','.join(str(c) for c in _hex_to_rgb(colors['danger']))}, 0.1);
            --theme-warning-subtle: rgba({','.join(str(c) for c in _hex_to_rgb(colors['warning']))}, 0.1);
            --theme-info-subtle: rgba({','.join(str(c) for c in _hex_to_rgb(colors['info']))}, 0.1);
            
            /* Border variations */
            --theme-primary-border: rgba({','.join(str(c) for c in _hex_to_rgb(colors['primary']))}, 0.2);
            --theme-secondary-border: rgba({','.join(str(c) for c in _hex_to_rgb(colors['secondary']))}, 0.2);
            --theme-success-border: rgba({','.join(str(c) for c in _hex_to_rgb(colors['success']))}, 0.2);
            --theme-danger-border: rgba({','.join(str(c) for c in _hex_to_rgb(colors['danger']))}, 0.2);
            --theme-warning-border: rgba({','.join(str(c) for c in _hex_to_rgb(colors['warning']))}, 0.2);
            --theme-info-border: rgba({','.join(str(c) for c in _hex_to_rgb(colors['info']))}, 0.2);
            
            /* Focus ring color */
            --theme-focus-ring: rgba({','.join(str(c) for c in _hex_to_rgb(colors['primary']))}, 0.25);
            
            /* Entry status colors */
            --theme-status-active: {colors['success']};
            --theme-status-inactive: {colors['secondary']};
            --theme-status-pending: {colors['warning']};
            --theme-status-error: {colors['danger']};
            
            /* Priority levels for notes and notifications */
            --theme-priority-high: {colors['danger']};
            --theme-priority-medium: {colors['warning']};
            --theme-priority-low: {colors['info']};
            --theme-priority-info: {colors['info']};
            
            /* Table striping */
            --theme-table-stripe: rgba({','.join(str(c) for c in _hex_to_rgb(colors['primary']))}, 0.05);
            --theme-table-hover: rgba({','.join(str(c) for c in _hex_to_rgb(colors['primary']))}, 0.08);
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
            
            /* Enhanced dark mode color variations */
            --theme-bg-hover: {_lighten_color(dark_colors['bg_card'], 0.05)};
            --theme-bg-active: {_lighten_color(dark_colors['bg_surface'], 0.08)};
            --theme-text-emphasis: {_lighten_color(dark_colors['text'], 0.1)};
            --theme-border-subtle: {_darken_color(dark_colors['border'], 0.2)};
            --theme-shadow: rgba(0, 0, 0, 0.3);
            --theme-shadow-hover: rgba(0, 0, 0, 0.4);
            
            /* Alert and notification backgrounds for dark mode */
            --theme-alert-success-bg: rgba({','.join(str(c) for c in _hex_to_rgb(colors['success']))}, 0.15);
            --theme-alert-success-border: rgba({','.join(str(c) for c in _hex_to_rgb(colors['success']))}, 0.3);
            --theme-alert-success-text: {_lighten_color(colors['success'], 0.2)};
            --theme-alert-warning-bg: rgba({','.join(str(c) for c in _hex_to_rgb(colors['warning']))}, 0.15);
            --theme-alert-warning-border: rgba({','.join(str(c) for c in _hex_to_rgb(colors['warning']))}, 0.3);
            --theme-alert-warning-text: {_lighten_color(colors['warning'], 0.1)};
            --theme-alert-danger-bg: rgba({','.join(str(c) for c in _hex_to_rgb(colors['danger']))}, 0.15);
            --theme-alert-danger-border: rgba({','.join(str(c) for c in _hex_to_rgb(colors['danger']))}, 0.3);
            --theme-alert-danger-text: {_lighten_color(colors['danger'], 0.2)};
            
            /* Badge colors for dark mode */
            --theme-badge-primary-bg: {colors['primary']};
            --theme-badge-primary-text: white;
            --theme-badge-secondary-bg: {colors['secondary']};
            --theme-badge-secondary-text: white;
            --theme-badge-outline-primary: {colors['primary']};
            --theme-badge-outline-secondary: {colors['secondary']};
            
            /* Table enhancements for dark mode */
            --theme-table-header-bg: {_lighten_color(dark_colors['bg_surface'], 0.05)};
            --theme-table-border: {dark_colors['border']};
            --theme-table-row-hover: var(--theme-table-hover);
            
            /* Form control enhancements for dark mode */
            --theme-input-bg: {dark_colors['bg_card']};
            --theme-input-border: {dark_colors['border']};
            --theme-input-focus-border: {colors['primary']};
            --theme-input-focus-shadow: var(--theme-focus-ring);
            
            /* Progress bar colors for dark mode */
            --theme-progress-bg: {dark_colors['bg_surface']};
            --theme-progress-bar: {colors['primary']};
            
            /* Bootstrap CSS Variable Overrides */
            --bs-primary: {colors['primary']};
            --bs-primary-rgb: {','.join(str(c) for c in _hex_to_rgb(colors['primary']))};
            --bs-secondary: {colors['secondary']};
            --bs-secondary-rgb: {','.join(str(c) for c in _hex_to_rgb(colors['secondary']))};
            --bs-success: {colors['success']};
            --bs-success-rgb: {','.join(str(c) for c in _hex_to_rgb(colors['success']))};
            --bs-danger: {colors['danger']};
            --bs-danger-rgb: {','.join(str(c) for c in _hex_to_rgb(colors['danger']))};
            --bs-warning: {colors['warning']};
            --bs-warning-rgb: {','.join(str(c) for c in _hex_to_rgb(colors['warning']))};
            --bs-info: {colors['info']};
            --bs-info-rgb: {','.join(str(c) for c in _hex_to_rgb(colors['info']))};
            --bs-info-bg-subtle: {info_bg};
            --bs-info-border-subtle: {info_border};
            --bs-info-text-emphasis: {info_text};
            --bs-light: {dark_colors['bg_surface']};
            --bs-dark: {dark_colors['text']};
            --bs-body-bg: {dark_colors['bg_body']};
            --bs-body-color: {dark_colors['text']};
            --bs-border-color: {dark_colors['border']};
            --bs-secondary-bg: {dark_colors['bg_surface']};
            --bs-tertiary-bg: {_lighten_color(dark_colors['bg_surface'], 0.05)};
            --bs-focus-ring-color: var(--theme-focus-ring);
            --bs-form-valid-color: {colors['success']};
            --bs-form-invalid-color: {colors['danger']};
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
            
            /* Enhanced light mode color variations */
            --theme-bg-hover: {_darken_color(light_colors['bg_card'], 0.03)};
            --theme-bg-active: {_darken_color(light_colors['bg_surface'], 0.05)};
            --theme-text-emphasis: {_darken_color(light_colors['text'], 0.1)};
            --theme-border-subtle: {_lighten_color(light_colors['border'], 0.3)};
            --theme-shadow: rgba(0, 0, 0, 0.1);
            --theme-shadow-hover: rgba(0, 0, 0, 0.15);
            
            /* Alert and notification backgrounds for light mode */
            --theme-alert-success-bg: rgba({','.join(str(c) for c in _hex_to_rgb(colors['success']))}, 0.1);
            --theme-alert-success-border: rgba({','.join(str(c) for c in _hex_to_rgb(colors['success']))}, 0.2);
            --theme-alert-success-text: {_darken_color(colors['success'], 0.3)};
            --theme-alert-warning-bg: rgba({','.join(str(c) for c in _hex_to_rgb(colors['warning']))}, 0.1);
            --theme-alert-warning-border: rgba({','.join(str(c) for c in _hex_to_rgb(colors['warning']))}, 0.2);
            --theme-alert-warning-text: {_darken_color(colors['warning'], 0.3)};
            --theme-alert-danger-bg: rgba({','.join(str(c) for c in _hex_to_rgb(colors['danger']))}, 0.1);
            --theme-alert-danger-border: rgba({','.join(str(c) for c in _hex_to_rgb(colors['danger']))}, 0.2);
            --theme-alert-danger-text: {_darken_color(colors['danger'], 0.3)};
            
            /* Badge colors for light mode */
            --theme-badge-primary-bg: {colors['primary']};
            --theme-badge-primary-text: white;
            --theme-badge-secondary-bg: {colors['secondary']};
            --theme-badge-secondary-text: white;
            --theme-badge-outline-primary: {colors['primary']};
            --theme-badge-outline-secondary: {colors['secondary']};
            
            /* Table enhancements */
            --theme-table-header-bg: {_darken_color(light_colors['bg_surface'], 0.03)};
            --theme-table-border: {light_colors['border']};
            --theme-table-row-hover: var(--theme-table-hover);
            
            /* Form control enhancements */
            --theme-input-bg: {light_colors['bg_card']};
            --theme-input-border: {light_colors['border']};
            --theme-input-focus-border: {colors['primary']};
            --theme-input-focus-shadow: var(--theme-focus-ring);
            
            /* Progress bar colors */
            --theme-progress-bg: {light_colors['bg_surface']};
            --theme-progress-bar: {colors['primary']};
            
            /* Bootstrap CSS Variable Overrides */
            --bs-primary: {colors['primary']};
            --bs-primary-rgb: {','.join(str(c) for c in _hex_to_rgb(colors['primary']))};
            --bs-secondary: {colors['secondary']};
            --bs-secondary-rgb: {','.join(str(c) for c in _hex_to_rgb(colors['secondary']))};
            --bs-success: {colors['success']};
            --bs-success-rgb: {','.join(str(c) for c in _hex_to_rgb(colors['success']))};
            --bs-danger: {colors['danger']};
            --bs-danger-rgb: {','.join(str(c) for c in _hex_to_rgb(colors['danger']))};
            --bs-warning: {colors['warning']};
            --bs-warning-rgb: {','.join(str(c) for c in _hex_to_rgb(colors['warning']))};
            --bs-info: {colors['info']};
            --bs-info-rgb: {','.join(str(c) for c in _hex_to_rgb(colors['info']))};
            --bs-info-bg-subtle: {info_bg};
            --bs-info-border-subtle: {info_border};
            --bs-info-text-emphasis: {info_text};
            --bs-light: {light_colors['bg_surface']};
            --bs-dark: {light_colors['text']};
            --bs-body-bg: {light_colors['bg_body']};
            --bs-body-color: {light_colors['text']};
            --bs-border-color: {light_colors['border']};
            --bs-secondary-bg: {light_colors['bg_surface']};
            --bs-tertiary-bg: {_lighten_color(light_colors['bg_surface'], 0.1)};
            --bs-focus-ring-color: var(--theme-focus-ring);
            --bs-form-valid-color: {colors['success']};
            --bs-form-invalid-color: {colors['danger']};
        # App-specific component styles
        .btn-purple {{
            background-color: var(--bs-purple);
            border-color: var(--bs-purple);
            color: white;
        }}
        
        .btn-purple:hover {{
            background-color: var(--bs-purple-dark);
            border-color: var(--bs-purple-dark);
            color: white;
        }}
        
        /* Entry card enhancements */
        .card {{
            border: 1px solid var(--bs-border-color);
            border-radius: var(--bs-border-radius);
            box-shadow: 0 0.125rem 0.25rem var(--bs-box-shadow-sm);
        }}
        
        .card-header {{
            background-color: var(--bs-gray-100);
            border-bottom: 1px solid var(--bs-border-color);
        }}
        
        /* List group styling */
        .list-group-item {{
            border: 1px solid var(--bs-border-color);
            background-color: var(--bs-body-bg);
            color: var(--bs-body-color);
        }}
        
        .list-group-item:hover {{
            background-color: var(--bs-gray-50);
        }}
        
        /* Tab navigation */
        .nav-tabs .nav-link {{
            color: var(--bs-body-color);
            border: 1px solid transparent;
        }}
        
        .nav-tabs .nav-link:hover {{
            border-color: var(--bs-border-color);
            isolation: isolate;
        }}
        
        .nav-tabs .nav-link.active {{
            color: var(--bs-primary);
            background-color: var(--bs-body-bg);
            border-color: var(--bs-border-color) var(--bs-border-color) var(--bs-body-bg);
        }}
        
        /* File upload area */
        .border-dashed {{
            border-style: dashed !important;
        }}
        
        /* Quick stats cards */
        .card.border-primary {{
            border-color: var(--bs-primary) !important;
        }}
        
        .card.border-success {{
            border-color: var(--bs-success) !important;
        }}
        
        .card.border-warning {{
            border-color: var(--bs-warning) !important;
        }}
        
        .card.border-danger {{
            border-color: var(--bs-danger) !important;
        }}
        
        /* Alert enhancements */
        .alert {{
            border: 1px solid transparent;
            border-radius: var(--bs-border-radius);
        }}
        
        .alert-info {{
            color: var(--bs-info-text);
            background-color: var(--bs-info-bg-subtle);
            border-color: var(--bs-info-border-subtle);
        }}
        
        .alert-warning {{
            color: var(--bs-warning-text);
            background-color: var(--bs-warning-bg-subtle);
            border-color: var(--bs-warning-border-subtle);
        }}
        
        .alert-success {{
            color: var(--bs-success-text);
            background-color: var(--bs-success-bg-subtle);
            border-color: var(--bs-success-border-subtle);
        }}
        
        .alert-danger {{
            color: var(--bs-danger-text);
            background-color: var(--bs-danger-bg-subtle);
            border-color: var(--bs-danger-border-subtle);
        }}
        
        /* Badge text color adjustments */
        .badge.bg-warning {{
            color: var(--bs-dark) !important;
        }}
        
        /* Maintenance card styling */
        .card.border-warning {{
            border-color: var(--bs-warning) !important;
        }}
        
        .card-header.bg-warning {{
            background-color: var(--bs-warning) !important;
            color: var(--bs-dark);
        }}
        
        /* Progress bar theming */
        .progress {{
            background-color: var(--bs-gray-200);
            border-radius: var(--bs-border-radius);
        }}
        
        .progress-bar {{
            background-color: var(--bs-primary);
        }}
        
        .progress-bar.bg-success {{
            background-color: var(--bs-success) !important;
        }}
        
        .progress-bar.bg-warning {{
            background-color: var(--bs-warning) !important;
        }}
        
        .progress-bar.bg-danger {{
            background-color: var(--bs-danger) !important;
        }}
        
        /* Input group styling */
        .input-group .form-control {{
            border-right: 0;
        }}
        
        .input-group .btn {{
            border-left: 0;
        }}
        
        /* Dropdown menu theming */
        .dropdown-menu {{
            background-color: var(--bs-body-bg);
            border: 1px solid var(--bs-border-color);
            border-radius: var(--bs-border-radius);
            box-shadow: 0 0.5rem 1rem var(--bs-box-shadow);
        }}
        
        .dropdown-item {{
            color: var(--bs-body-color);
        }}
        
        .dropdown-item:hover,
        .dropdown-item:focus {{
            background-color: var(--bs-gray-100);
            color: var(--bs-body-color);
        }}
        
        .dropdown-divider {{
            border-top: 1px solid var(--bs-border-color);
        }}
        
        /* Table responsive theming */
        .table-responsive {{
            border: 1px solid var(--bs-border-color);
            border-radius: var(--bs-border-radius);
        }}
        
        .table th,
        .table td {{
            border-top: 1px solid var(--bs-border-color);
            color: var(--bs-body-color);
        }}
        
        .table thead th {{
            border-bottom: 2px solid var(--bs-border-color);
            background-color: var(--bs-gray-50);
        }}
        
        /* Preview card specific styling */
        .preview-card {{
            border: 1px solid var(--bs-border-color) !important;
            border-radius: var(--bs-border-radius) !important;
            background: var(--bs-body-bg) !important;
            color: var(--bs-body-color) !important;
        }}
        
        /* Button group radio styling */
        .btn-check:checked + .btn-outline-primary {{
            background-color: var(--bs-primary);
            border-color: var(--bs-primary);
            color: white;
        }}
        
        /* File attachment area */
        .border-2 {{
            border-width: 2px !important;
        }}
        
        /* Status badge colors for text readability */
        .badge.text-dark {{
            color: var(--bs-dark) !important;
        }}
        
        /* Focus ring colors for accessibility */
        .btn:focus,
        .form-control:focus,
        .form-select:focus {{
            box-shadow: 0 0 0 0.2rem var(--bs-primary-bg-subtle);
        }}
        
        .btn-outline-primary:focus {{
            box-shadow: 0 0 0 0.2rem var(--bs-primary-focus-ring);
        }}
        
        .btn-outline-secondary:focus {{
            box-shadow: 0 0 0 0.2rem var(--bs-secondary-focus-ring);
        }}
        
        .btn-outline-success:focus {{
            box-shadow: 0 0 0 0.2rem var(--bs-success-focus-ring);
        }}
        
        .btn-outline-danger:focus {{
            box-shadow: 0 0 0 0.2rem var(--bs-danger-focus-ring);
        }}
        
        /* Dark mode adjustments for preview elements */
        [data-bs-theme="dark"] .preview-card {{
            background: var(--bs-dark) !important;
            border-color: var(--bs-border-color-dark) !important;
            color: var(--bs-body-color-dark) !important;
        }}
        
        [data-bs-theme="dark"] .card-header {{
            background-color: var(--bs-gray-800) !important;
            border-color: var(--bs-border-color-dark) !important;
        }}
        
        [data-bs-theme="dark"] .list-group-item {{
            background-color: var(--bs-dark) !important;
            border-color: var(--bs-border-color-dark) !important;
            color: var(--bs-body-color-dark) !important;
        }}
        
        [data-bs-theme="dark"] .list-group-item:hover {{
            background-color: var(--bs-gray-800) !important;
        }}
        
        [data-bs-theme="dark"] .table th,
        [data-bs-theme="dark"] .table td {{
            border-color: var(--bs-border-color-dark) !important;
            color: var(--bs-body-color-dark) !important;
        }}
        
        [data-bs-theme="dark"] .table thead th {{
            background-color: var(--bs-gray-800) !important;
        }}
        
        [data-bs-theme="dark"] .dropdown-menu {{
            background-color: var(--bs-dark) !important;
            border-color: var(--bs-border-color-dark) !important;
        }}
        
        [data-bs-theme="dark"] .dropdown-item:hover,
        [data-bs-theme="dark"] .dropdown-item:focus {{
            background-color: var(--bs-gray-800) !important;
            color: var(--bs-body-color-dark) !important;
        }}
    }}
    """    # Add comprehensive CSS rules for better theme coverage
    css += """
        
        /* ========== ENHANCED COMPONENT STYLING ========== */
        
        /* Comprehensive Button Styling */
        .btn {
            transition: all 0.15s ease-in-out;
            font-weight: 500;
        }
        
        .btn-theme-primary {
            background-color: var(--theme-primary);
            border-color: var(--theme-primary);
            color: var(--theme-primary-text);
        }
        
        .btn-theme-primary:hover, .btn-theme-primary:focus, .btn-theme-primary:active {
            background-color: var(--theme-primary-hover);
            border-color: var(--theme-primary-hover);
            color: var(--theme-primary-text);
            transform: translateY(-1px);
            box-shadow: 0 3px 6px rgba(0, 0, 0, 0.16);
        }
        
        .btn-theme-secondary {
            background-color: var(--theme-secondary);
            border-color: var(--theme-secondary);
            color: white;
        }
        
        .btn-theme-secondary:hover, .btn-theme-secondary:focus, .btn-theme-secondary:active {
            background-color: var(--theme-secondary-hover);
            border-color: var(--theme-secondary-hover);
            color: white;
            transform: translateY(-1px);
        }
        
        /* Override Bootstrap danger button with theme colors */
        .btn-danger {
            background-color: var(--theme-danger) !important;
            border-color: var(--theme-danger) !important;
            color: white !important;
        }
        
        .btn-danger:hover, .btn-danger:focus, .btn-danger:active {
            background-color: var(--theme-danger-hover) !important;
            border-color: var(--theme-danger-hover) !important;
            color: white !important;
        }
        
        .btn-outline-danger {
            color: var(--theme-danger) !important;
            border-color: var(--theme-danger) !important;
            background-color: transparent !important;
        }
        
        .btn-outline-danger:hover, .btn-outline-danger:focus, .btn-outline-danger:active {
            background-color: var(--theme-danger) !important;
            border-color: var(--theme-danger) !important;
            color: white !important;
        }
        
        /* Override other Bootstrap button variants */
        .btn-success {
            background-color: var(--theme-success) !important;
            border-color: var(--theme-success) !important;
            color: white !important;
        }
        
        .btn-success:hover, .btn-success:focus, .btn-success:active {
            background-color: var(--theme-success-hover) !important;
            border-color: var(--theme-success-hover) !important;
            color: white !important;
        }
        
        .btn-warning {
            background-color: var(--theme-warning) !important;
            border-color: var(--theme-warning) !important;
            color: var(--theme-text) !important;
        }
        
        .btn-warning:hover, .btn-warning:focus, .btn-warning:active {
            background-color: var(--theme-warning-hover) !important;
            border-color: var(--theme-warning-hover) !important;
            color: var(--theme-text) !important;
        }
        
        .btn-info {
            background-color: var(--theme-info) !important;
            border-color: var(--theme-info) !important;
            color: white !important;
        }
        
        .btn-info:hover, .btn-info:focus, .btn-info:active {
            background-color: var(--theme-info-hover) !important;
            border-color: var(--theme-info-hover) !important;
            color: white !important;
        }
        
        .btn-outline-theme-primary {
            color: var(--theme-primary);
            border-color: var(--theme-primary);
            background-color: transparent;
        }
        
        .btn-outline-theme-primary:hover, .btn-outline-theme-primary:focus, .btn-outline-theme-primary:active {
            background-color: var(--theme-primary);
            border-color: var(--theme-primary);
            color: var(--theme-primary-text);
            transform: translateY(-1px);
        }
        
        /* Enhanced Badge Styling */
        .badge {
            font-weight: 500;
            letter-spacing: 0.025em;
        }
        
        .badge.bg-primary {
            background-color: var(--theme-badge-primary-bg) !important;
            color: var(--theme-badge-primary-text) !important;
        }
        
        .badge.bg-secondary {
            background-color: var(--theme-badge-secondary-bg) !important;
            color: var(--theme-badge-secondary-text) !important;
        }
        
        .badge.bg-success {
            background-color: var(--theme-success) !important;
            color: white !important;
        }
        
        .badge.bg-danger {
            background-color: var(--theme-danger) !important;
            color: white !important;
        }
        
        .badge.bg-warning {
            background-color: var(--theme-warning) !important;
            color: var(--theme-text) !important;
        }
        
        .badge.bg-info {
            background-color: var(--theme-info) !important;
            color: white !important;
        }
        
        .badge-outline-primary {
            color: var(--theme-badge-outline-primary);
            border: 1px solid var(--theme-badge-outline-primary);
            background-color: transparent;
        }
        
        .badge-outline-secondary {
            color: var(--theme-badge-outline-secondary);
            border: 1px solid var(--theme-badge-outline-secondary);
            background-color: transparent;
        }
        
        /* Enhanced Alert Styling */
        .alert {
            border-width: 1px;
            border-style: solid;
            border-radius: 0.5rem;
            margin-bottom: 1rem;
        }
        
        .alert-primary {
            background-color: var(--theme-primary-subtle);
            border-color: var(--theme-primary-border);
            color: var(--theme-primary);
        }
        
        .alert-secondary {
            background-color: var(--theme-secondary-subtle);
            border-color: var(--theme-secondary-border);
            color: var(--theme-secondary);
        }
        
        .alert-success {
            background-color: var(--theme-alert-success-bg);
            border-color: var(--theme-alert-success-border);
            color: var(--theme-alert-success-text);
        }
        
        .alert-danger {
            background-color: var(--theme-alert-danger-bg);
            border-color: var(--theme-alert-danger-border);
            color: var(--theme-alert-danger-text);
        }
        
        .alert-warning {
            background-color: var(--theme-alert-warning-bg);
            border-color: var(--theme-alert-warning-border);
            color: var(--theme-alert-warning-text);
        }
        
        .alert-info {
            background-color: var(--theme-bg-info);
            border-color: var(--theme-border-info);
            color: var(--theme-text-info);
        }
        
        /* Enhanced Table Styling */
        .table {
            color: var(--theme-text);
            border-color: var(--theme-table-border);
            background-color: var(--theme-bg-card);
        }
        
        .table th {
            background-color: var(--theme-table-header-bg);
            border-color: var(--theme-table-border);
            color: var(--theme-text);
            font-weight: 600;
            border-bottom: 2px solid var(--theme-table-border);
        }
        
        .table td {
            border-color: var(--theme-table-border);
            color: var(--theme-text);
            vertical-align: middle;
        }
        
        .table tbody tr:hover {
            background-color: var(--theme-table-row-hover);
        }
        
        .table-striped > tbody > tr:nth-of-type(odd) {
            background-color: var(--theme-table-stripe);
        }
        
        .table-bordered {
            border: 1px solid var(--theme-table-border);
        }
        
        .table-bordered th,
        .table-bordered td {
            border: 1px solid var(--theme-table-border);
        }
        
        /* Enhanced Form Control Styling */
        .form-control, .form-select {
            background-color: var(--theme-input-bg);
            border-color: var(--theme-input-border);
            color: var(--theme-text);
            transition: border-color 0.15s ease-in-out, box-shadow 0.15s ease-in-out;
        }
        
        .form-control:focus, .form-select:focus {
            background-color: var(--theme-input-bg);
            border-color: var(--theme-input-focus-border);
            color: var(--theme-text);
            box-shadow: 0 0 0 0.25rem var(--theme-input-focus-shadow);
            outline: 0;
        }
        
        .form-control:hover:not(:focus), .form-select:hover:not(:focus) {
            border-color: var(--theme-primary-lighter);
        }
        
        .form-label {
            color: var(--theme-text);
            font-weight: 500;
        }
        
        .form-text {
            color: var(--theme-text-muted);
        }
        
        /* Enhanced Progress Bar Styling */
        .progress {
            background-color: var(--theme-progress-bg);
            border-radius: 0.5rem;
            overflow: hidden;
        }
        
        .progress-bar {
            background-color: var(--theme-progress-bar);
            transition: width 0.6s ease;
        }
        
        .progress-bar.bg-success {
            background-color: var(--theme-success) !important;
        }
        
        .progress-bar.bg-warning {
            background-color: var(--theme-warning) !important;
        }
        
        .progress-bar.bg-danger {
            background-color: var(--theme-danger) !important;
        }
        
        .progress-bar.bg-info {
            background-color: var(--theme-info) !important;
        }
        
        /* Enhanced Card Styling */
        .card {
            background-color: var(--theme-bg-card);
            border-color: var(--theme-border);
            color: var(--theme-text);
            box-shadow: var(--theme-shadow);
            transition: box-shadow 0.15s ease-in-out;
        }
        
        .card:hover {
            box-shadow: var(--theme-shadow-hover);
        }
        
        .card-header {
            background-color: var(--theme-bg-surface);
            border-bottom-color: var(--theme-border);
            color: var(--theme-text);
            font-weight: 600;
        }
        
        .card-body {
            background-color: var(--theme-bg-card);
            color: var(--theme-text);
        }
        
        .card-footer {
            background-color: var(--theme-bg-surface);
            border-top-color: var(--theme-border);
            color: var(--theme-text-muted);
        }
        
        /* Enhanced Modal Styling */
        .modal-content {
            background-color: var(--theme-bg-card);
            border-color: var(--theme-border);
            color: var(--theme-text);
            box-shadow: var(--theme-shadow-hover);
        }
        
        .modal-header {
            background-color: var(--theme-bg-surface);
            border-bottom-color: var(--theme-border);
            color: var(--theme-text);
        }
        
        .modal-title {
            color: var(--theme-text);
            font-weight: 600;
        }
        
        .modal-body {
            background-color: var(--theme-bg-card);
            color: var(--theme-text);
        }
        
        .modal-footer {
            background-color: var(--theme-bg-surface);
            border-top-color: var(--theme-border);
        }
        
        /* Enhanced List Group Styling */
        .list-group-item {
            background-color: var(--theme-bg-card);
            border-color: var(--theme-border);
            color: var(--theme-text);
        }
        
        .list-group-item:hover {
            background-color: var(--theme-bg-hover);
        }
        
        .list-group-item.active {
            background-color: var(--theme-primary);
            border-color: var(--theme-primary);
            color: var(--theme-primary-text);
        }
        
        /* Enhanced Navigation Styling */
        .nav-tabs {
            border-bottom-color: var(--theme-border);
        }
        
        .nav-tabs .nav-link {
            color: var(--theme-text-muted);
            border-color: transparent;
            transition: all 0.15s ease-in-out;
        }
        
        .nav-tabs .nav-link:hover {
            border-color: var(--theme-border) var(--theme-border) var(--theme-border);
            color: var(--theme-text);
        }
        
        .nav-tabs .nav-link.active {
            color: var(--theme-text);
            background-color: var(--theme-bg-card);
            border-color: var(--theme-border) var(--theme-border) var(--theme-bg-card);
        }
        
        /* Enhanced Dropdown Styling */
        .dropdown-menu {
            background-color: var(--theme-bg-card);
            border-color: var(--theme-border);
            box-shadow: var(--theme-shadow-hover);
        }
        
        .dropdown-item {
            color: var(--theme-text);
            transition: background-color 0.15s ease-in-out;
        }
        
        .dropdown-item:hover, .dropdown-item:focus {
            background-color: var(--theme-bg-hover);
            color: var(--theme-text);
        }
        
        .dropdown-item.active {
            background-color: var(--theme-primary);
            color: var(--theme-primary-text);
        }
        
        /* Enhanced Pagination Styling */
        .page-item .page-link {
            background-color: var(--theme-bg-card);
            border-color: var(--theme-border);
            color: var(--theme-primary);
            transition: all 0.15s ease-in-out;
        }
        
        .page-item:hover .page-link {
            background-color: var(--theme-bg-hover);
            border-color: var(--theme-primary-border);
            color: var(--theme-primary);
        }
        
        .page-item.active .page-link {
            background-color: var(--theme-primary);
            border-color: var(--theme-primary);
            color: var(--theme-primary-text);
        }
        
        .page-item.disabled .page-link {
            background-color: var(--theme-bg-surface);
            border-color: var(--theme-border);
            color: var(--theme-text-muted);
        }
        
        /* Enhanced Breadcrumb Styling */
        .breadcrumb {
            background-color: var(--theme-bg-surface);
            border-radius: 0.5rem;
            padding: 0.75rem 1rem;
        }
        
        .breadcrumb-item a {
            color: var(--theme-primary);
            text-decoration: none;
        }
        
        .breadcrumb-item a:hover {
            color: var(--theme-primary-hover);
            text-decoration: underline;
        }
        
        .breadcrumb-item.active {
            color: var(--theme-text-muted);
        }
        
        /* Enhanced Accordion Styling */
        .accordion-item {
            background-color: var(--theme-bg-card);
            border-color: var(--theme-border);
        }
        
        .accordion-button {
            background-color: var(--theme-bg-card);
            color: var(--theme-text);
            border: none;
            transition: background-color 0.15s ease-in-out;
        }
        
        .accordion-button:hover {
            background-color: var(--theme-bg-hover);
        }
        
        .accordion-button:not(.collapsed) {
            background-color: var(--theme-bg-surface);
            color: var(--theme-primary);
            box-shadow: none;
        }
        
        .accordion-body {
            background-color: var(--theme-bg-card);
            color: var(--theme-text);
        }
        
        /* Entry Status Indicators */
        .status-active {
            color: var(--theme-status-active);
        }
        
        .status-inactive {
            color: var(--theme-status-inactive);
        }
        
        .status-pending {
            color: var(--theme-status-pending);
        }
        
        .status-error {
            color: var(--theme-status-error);
        }
        
        /* Priority Indicators */
        .priority-high {
            color: var(--theme-priority-high);
        }
        
        .priority-medium {
            color: var(--theme-priority-medium);
        }
        
        .priority-low {
            color: var(--theme-priority-low);
        }
        
        .priority-info {
            color: var(--theme-priority-info);
        }
        
        /* Enhanced Spinner/Loading Styling */
        .spinner-border {
            color: var(--theme-primary);
        }
        
        .spinner-border-sm {
            color: var(--theme-primary);
        }
        
        /* Enhanced Toast Styling */
        .toast {
            background-color: var(--theme-bg-card);
            border-color: var(--theme-border);
            color: var(--theme-text);
            box-shadow: var(--theme-shadow);
        }
        
        .toast-header {
            background-color: var(--theme-bg-surface);
            border-bottom-color: var(--theme-border);
            color: var(--theme-text);
        }
        
        .toast-body {
            color: var(--theme-text);
        }
        
        /* Enhanced Tooltip Styling */
        .tooltip .tooltip-inner {
            background-color: var(--theme-text);
            color: var(--theme-bg-card);
            border-radius: 0.375rem;
        }
        
        /* Enhanced Popover Styling */
        .popover {
            background-color: var(--theme-bg-card);
            border-color: var(--theme-border);
            box-shadow: var(--theme-shadow-hover);
        }
        
        .popover-header {
            background-color: var(--theme-bg-surface);
            border-bottom-color: var(--theme-border);
            color: var(--theme-text);
            font-weight: 600;
        }
        
        .popover-body {
            color: var(--theme-text);
        }
        
        /* Application-specific component enhancements */
        .entry-item {
            border-left: 4px solid var(--theme-primary);
            transition: all 0.2s ease;
        }
        
        .entry-item:hover {
            border-left-color: var(--theme-primary-hover);
            box-shadow: var(--theme-shadow-hover);
            transform: translateY(-1px);
        }
        
        .note-item {
            border-left: 4px solid var(--theme-info);
        }
        
        .note-item.priority-high {
            border-left-color: var(--theme-priority-high);
        }
        
        .note-item.priority-medium {
            border-left-color: var(--theme-priority-medium);
        }
        
        .note-item.priority-low {
            border-left-color: var(--theme-priority-low);
        }
        
        .relationship-item {
            border: 1px solid var(--theme-border);
            border-radius: 0.5rem;
            transition: all 0.2s ease;
        }
        
        .relationship-item:hover {
            border-color: var(--theme-primary);
            box-shadow: var(--theme-shadow);
        }
        
        .sensor-data-item {
            border-left: 3px solid var(--theme-success);
        }
        
        .sensor-data-item.warning {
            border-left-color: var(--theme-warning);
        }
        
        .sensor-data-item.critical {
            border-left-color: var(--theme-danger);
        }
        
        /* Enhanced focus management */
        *:focus {
            outline: 2px solid var(--theme-primary);
            outline-offset: 2px;
        }
        
        .btn:focus, .form-control:focus, .form-select:focus {
            box-shadow: 0 0 0 0.25rem var(--theme-focus-ring);
        }
        
        /* Responsive enhancements */
        @media (max-width: 768px) {
            .btn-group {
                display: flex;
                flex-direction: column;
                width: 100%;
            }
            
            .btn-group .btn {
                border-radius: 0.375rem !important;
                margin-bottom: 0.25rem;
            }
            
            .table-responsive {
                border-radius: 0.5rem;
            }
        }
        
        /* Print mode optimizations */
        @media print {
            .entry-item, .note-item, .relationship-item {
                border-left-color: #000 !important;
                box-shadow: none !important;
                background-color: #fff !important;
                color: #000 !important;
            }
            
            .btn, .modal, .dropdown {
                display: none !important;
            }
        }
    """
    
    return css
