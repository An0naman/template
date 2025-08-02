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
    """Generate CSS variables based on theme settings"""
    if settings is None:
        settings = get_current_theme_settings()
    
    theme = settings.get('current_theme', 'default')
    dark_mode = settings.get('dark_mode_enabled', False)
    font_size = settings.get('font_size', 'normal')
    high_contrast = settings.get('high_contrast_enabled', False)
    
    # Color schemes
    color_schemes = {
        'default': {
            'primary': '#0d6efd',
            'secondary': '#6c757d',
            'success': '#198754',
            'danger': '#dc3545',
            'warning': '#ffc107',
            'info': '#0dcaf0'
        },
        'emerald': {
            'primary': '#10b981',
            'secondary': '#6b7280',
            'success': '#059669',
            'danger': '#ef4444',
            'warning': '#f59e0b',
            'info': '#06b6d4'
        },
        'purple': {
            'primary': '#8b5cf6',
            'secondary': '#6b7280',
            'success': '#10b981',
            'danger': '#ef4444',
            'warning': '#f59e0b',
            'info': '#06b6d4'
        },
        'amber': {
            'primary': '#f59e0b',
            'secondary': '#6b7280',
            'success': '#10b981',
            'danger': '#ef4444',
            'warning': '#d97706',
            'info': '#06b6d4'
        }
    }
    
    # Font sizes
    font_sizes = {
        'small': '14px',
        'normal': '16px',
        'large': '18px',
        'extra-large': '20px'
    }
    
    # Background colors for dark mode
    bg_colors = {
        'body': '#ffffff' if not dark_mode else '#121212',
        'surface': '#f8f9fa' if not dark_mode else '#1e1e1e',
        'card': '#ffffff' if not dark_mode else '#2d2d2d',
        'text': '#212529' if not dark_mode else '#ffffff',
        'text-muted': '#6c757d' if not dark_mode else '#b0b0b0'
    }
    
    colors = color_schemes.get(theme, color_schemes['default'])
    base_font_size = font_sizes.get(font_size, font_sizes['normal'])
    
    css = f"""
    :root {{
        --bs-primary: {colors['primary']};
        --bs-secondary: {colors['secondary']};
        --bs-success: {colors['success']};
        --bs-danger: {colors['danger']};
        --bs-warning: {colors['warning']};
        --bs-info: {colors['info']};
        
        --theme-bg-body: {bg_colors['body']};
        --theme-bg-surface: {bg_colors['surface']};
        --theme-bg-card: {bg_colors['card']};
        --theme-text: {bg_colors['text']};
        --theme-text-muted: {bg_colors['text-muted']};
        
        --theme-font-size: {base_font_size};
        
        {'--theme-contrast: 1.5;' if high_contrast else '--theme-contrast: 1;'}
    }}
    
    body {{
        background-color: var(--theme-bg-body) !important;
        color: var(--theme-text) !important;
        font-size: var(--theme-font-size) !important;
        filter: contrast(var(--theme-contrast));
    }}
    
    .card, .bg-white {{
        background-color: var(--theme-bg-card) !important;
        color: var(--theme-text) !important;
    }}
    
    .bg-light {{
        background-color: var(--theme-bg-surface) !important;
    }}
    
    .text-muted {{
        color: var(--theme-text-muted) !important;
    }}
    
    /* Maintain maintenance module colors */
    .maintenance-module,
    .maintenance-module * {{
        filter: none !important;
    }}
    """
    
    return css
