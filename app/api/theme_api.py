from flask import Blueprint, request, jsonify, render_template, session, g, current_app
import sqlite3
import json

theme_api = Blueprint('theme_api', __name__)

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
                
                # Valid options validation
                valid_themes = ['default', 'emerald', 'purple', 'amber']
                valid_font_sizes = ['small', 'normal', 'large', 'extra-large']
                
                if theme not in valid_themes:
                    return jsonify({'error': 'Invalid theme selected'}), 400
                
                if font_size not in valid_font_sizes:
                    return jsonify({'error': 'Invalid font size selected'}), 400
                
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
                    'high_contrast': high_contrast
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
                for parameter_name, parameter_value in cursor.fetchall():
                    if parameter_name == 'theme_color_scheme':
                        settings['theme'] = parameter_value
                    elif parameter_name == 'theme_dark_mode':
                        settings['dark_mode'] = parameter_value.lower() == 'true'
                    elif parameter_name == 'theme_font_size':
                        settings['font_size'] = parameter_value
                    elif parameter_name == 'theme_high_contrast':
                        settings['high_contrast'] = parameter_value.lower() == 'true'
                
                # Set defaults if not found
                settings.setdefault('theme', 'default')
                settings.setdefault('dark_mode', False)
                settings.setdefault('font_size', 'normal')
                settings.setdefault('high_contrast', False)
                
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
        for parameter_name, parameter_value in cursor.fetchall():
            if parameter_name == 'theme_color_scheme':
                settings['current_theme'] = parameter_value
            elif parameter_name == 'theme_dark_mode':
                settings['dark_mode_enabled'] = parameter_value.lower() == 'true'
            elif parameter_name == 'theme_font_size':
                settings['font_size'] = parameter_value
            elif parameter_name == 'theme_high_contrast':
                settings['high_contrast_enabled'] = parameter_value.lower() == 'true'
        
        # Set defaults
        settings.setdefault('current_theme', 'default')
        settings.setdefault('dark_mode_enabled', False)
        settings.setdefault('font_size', 'normal')
        settings.setdefault('high_contrast_enabled', False)
        
        conn.close()
        return settings
        
    except Exception as e:
        # Return defaults on error
        return {
            'current_theme': 'default',
            'dark_mode_enabled': False,
            'font_size': 'normal',
            'high_contrast_enabled': False
        }


def generate_theme_css(settings=None):
    """Generate clean CSS variables based on theme settings"""
    if settings is None:
        settings = get_current_theme_settings()
    
    theme = settings.get('current_theme', 'default')
    dark_mode = settings.get('dark_mode_enabled', False)
    
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
        }
    }
    
    # Get colors for selected theme
    colors = color_schemes.get(theme, color_schemes['default'])
    
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
        else:  # default
            info_bg = "#0c2d48"
            info_border = "#1f6feb"
            info_text = "#79c0ff"
            
        css += f"""
            /* Dark Mode Colors */
            --theme-bg-body: #0d1117;
            --theme-bg-card: #161b22;
            --theme-bg-surface: #21262d;
            --theme-text: #f0f6fc;
            --theme-text-muted: #8b949e;
            --theme-border: #30363d;
            --theme-bg-info: {info_bg};
            --theme-border-info: {info_border};
            --theme-text-info: {info_text};
            
            /* Bootstrap CSS Variable Overrides */
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
        else:  # default
            info_bg = "#cff4fc"
            info_border = "#b6effb"
            info_text = "#055160"
            
        css += f"""
            /* Light Mode Colors */
            --theme-bg-body: #ffffff;
            --theme-bg-card: #ffffff;
            --theme-bg-surface: #f8f9fa;
            --theme-text: #212529;
            --theme-text-muted: #6c757d;
            --theme-border: #dee2e6;
            --theme-bg-info: {info_bg};
            --theme-border-info: {info_border};
            --theme-text-info: {info_text};
            
            /* Bootstrap CSS Variable Overrides */
            --bs-info: {colors['info']};
            --bs-info-rgb: 6, 182, 212;
            --bs-info-bg-subtle: {info_bg};
            --bs-info-border-subtle: {info_border};
            --bs-info-text-emphasis: {info_text};
        }}
        """
    
    return css
