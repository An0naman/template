# template_app/app/__init__.py
import sqlite3
from flask import Flask, g
import os
import logging

# Get project root for version file access
PROJECT_ROOT = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

def create_app():
    # Corrected Flask app initialization to point to 'templates' and 'static'
    # within the 'app' package.
    app = Flask(__name__, instance_relative_config=True)

    # Load configuration from config.py
    app.config.from_object('app.config')

    # Ensure the instance folder exists (for config, if needed)
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # --- Configure Logging ---
    log_dir = app.config.get('LOG_DIR', 'logs')
    os.makedirs(log_dir, exist_ok=True) # Ensure the logs directory exists

    # App-specific error log
    logging.basicConfig(filename=os.path.join(log_dir, 'app_errors.log'), level=logging.ERROR,
                        format='%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')

    # Flask's default logger for INFO messages
    file_handler = logging.FileHandler(os.path.join(log_dir, 'flask_info.log'))
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO) # Set default level for Flask's logger (e.g., for info messages)

    app.logger.info("Flask app initialized and logging configured.")

    # Import and register database functions
    from .db import get_connection, init_db
    
    # Run auto-migrations to ensure schema is up-to-date
    try:
        from .utils.auto_migrate import run_auto_migration
        if os.path.exists(app.config['DATABASE_PATH']):
            app.logger.info("Running auto-migration check...")
            run_auto_migration(app.config['DATABASE_PATH'])
    except Exception as e:
        app.logger.warning(f"Auto-migration check failed (non-critical): {e}")

    def get_db():
        if 'db' not in g:
            g.db = get_connection() # Use the get_connection from db.py
            g.db.row_factory = sqlite3.Row # Allows accessing columns by name, crucial for dict-like access
        return g.db

    @app.teardown_appcontext
    def close_db(e=None):
        db = g.pop('db', None)
        if db is not None:
            db.close()

    # Import helper functions that need app context or db
    from .db import get_system_parameters # Now lives in db.py or a database utility module

    # Make get_db and get_system_parameters available globally in templates
    app.jinja_env.globals.update(get_system_parameters=get_system_parameters)

    # Add route to serve uploaded files from /app/uploads at /static/uploads URL
    @app.route('/static/uploads/<path:filename>')
    def serve_uploads(filename):
        """Serve uploaded files from the persistent uploads volume"""
        from flask import send_from_directory
        import os
        
        uploads_dir = '/app/uploads'
        return send_from_directory(uploads_dir, filename)
    
    # Add route for serving logo for CasaOS and other external use
    @app.route('/api/logo')
    def serve_logo():
        """Serve the project logo from system parameters"""
        from flask import send_file, jsonify
        import os
        
        params = get_system_parameters()
        logo_path = params.get('project_logo_path')
        
        if not logo_path:
            # Return a 404 or default icon
            return jsonify({'error': 'No logo configured'}), 404
        
        # Logo is stored in /app/uploads and accessed via /static/uploads
        if logo_path.startswith('/static/uploads/'):
            filename = logo_path.replace('/static/uploads/', '')
            full_path = os.path.join('/app/uploads', filename)
        else:
            # Fallback for old paths
            full_path = os.path.join(app.root_path, 'static', 'uploads', logo_path)
        
        if not os.path.exists(full_path):
            return jsonify({'error': 'Logo file not found'}), 404
        
        return send_file(full_path)

    # --- Register Blueprints ---
    from .routes.main_routes import main_bp
    from .routes.maintenance_routes import maintenance_bp
    from .routes.printer_routes import printer_bp
    
    # Import all API blueprints
    from .api.entry_api import entry_api_bp
    from .api.entry_type_api import entry_type_api_bp
    from .api.entry_state_api import entry_state_api_bp
    from .api.notes_api import notes_api_bp
    from .api.note_bindings_api import note_bindings_bp
    from .api.system_params_api import system_params_api_bp
    from .api.search_params_api import search_params_api_bp
    from .api.relationships_api import relationships_api_bp
    from .api.shared_relationships_api import shared_relationships_api_bp
    from .api.wikipedia_api import wikipedia_api_bp
    from .api.notifications_api import notifications_api_bp
    from .api.labels_api import labels_api_bp
    from .api.cron_api import cron_api_bp
    from .api.theme_api import theme_api
    from .api.device_api import device_api_bp
    from .api.sql_api import sql_api_bp
    from .api.ntfy_api import ntfy_api_bp
    from .api.ai_api import ai_api_bp
    from .api.user_preferences_api import user_preferences_api_bp
    from .api.units_api import units_api_bp
    from .api.units_management_api import units_management_bp
    from .api.shared_sensor_api import shared_sensor_api_bp
    from .api.range_sensor_api import range_sensor_api
    from .api.saved_search_api import saved_search_api_bp
    from .api.dashboard_api import dashboard_api_bp
    from .api.entry_layout_api import entry_layout_api_bp
    from .api.milestone_api import milestone_api_bp
    from .api.health_api import health_api_bp
    from .api.milestone_template_api import milestone_template_api_bp
    from .api.entry_type_relationship_api import entry_type_relationship_api_bp
    from .api.planning_api import planning_api_bp
    from .api.kanban_api import kanban_api_bp
    from .api.sensor_master_api import sensor_master_api_bp
    
    # Import Git integration blueprints
    from .api.git_api import git_api_bp
    from .routes.git_routes import git_routes_bp
    from .routes.strava_routes import strava_routes_bp

    # Register all blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(maintenance_bp)
    app.register_blueprint(printer_bp)  # Printer routes (already has /api/printer prefix)
    app.register_blueprint(entry_api_bp, url_prefix='/api')
    app.register_blueprint(entry_type_api_bp, url_prefix='/api')
    app.register_blueprint(entry_state_api_bp, url_prefix='/api')
    app.register_blueprint(notes_api_bp, url_prefix='/api')
    app.register_blueprint(note_bindings_bp, url_prefix='/api')
    app.register_blueprint(system_params_api_bp, url_prefix='/api')
    app.register_blueprint(search_params_api_bp, url_prefix='/api')
    app.register_blueprint(relationships_api_bp, url_prefix='/api')
    app.register_blueprint(shared_relationships_api_bp, url_prefix='/api')
    app.register_blueprint(wikipedia_api_bp, url_prefix='/api')
    app.register_blueprint(notifications_api_bp, url_prefix='/api')
    app.register_blueprint(labels_api_bp, url_prefix='/api')
    app.register_blueprint(cron_api_bp, url_prefix='/api')
    app.register_blueprint(theme_api, url_prefix='/api')
    app.register_blueprint(device_api_bp, url_prefix='/api')
    app.register_blueprint(sql_api_bp, url_prefix='/api')
    app.register_blueprint(ntfy_api_bp, url_prefix='/api')
    app.register_blueprint(ai_api_bp, url_prefix='/api')
    app.register_blueprint(user_preferences_api_bp, url_prefix='/api')
    app.register_blueprint(units_api_bp)
    app.register_blueprint(units_management_bp)
    app.register_blueprint(shared_sensor_api_bp, url_prefix='/api')
    app.register_blueprint(range_sensor_api, url_prefix='/api')
    app.register_blueprint(saved_search_api_bp, url_prefix='/api')
    app.register_blueprint(dashboard_api_bp, url_prefix='/api')
    app.register_blueprint(entry_layout_api_bp, url_prefix='/api')
    app.register_blueprint(milestone_api_bp, url_prefix='/api')
    app.register_blueprint(health_api_bp, url_prefix='/api')
    app.register_blueprint(milestone_template_api_bp, url_prefix='/api')
    app.register_blueprint(entry_type_relationship_api_bp, url_prefix='/api')
    app.register_blueprint(planning_api_bp)
    app.register_blueprint(kanban_api_bp, url_prefix='/api')
    app.register_blueprint(sensor_master_api_bp, url_prefix='/api')
    
    # Register Git integration blueprints
    app.register_blueprint(git_api_bp)  # API routes have /api prefix in the blueprint
    app.register_blueprint(git_routes_bp)  # Page routes
    app.register_blueprint(strava_routes_bp)  # Strava routes

    app.logger.info("Blueprints registered.")

    # Add theme context processor
    @app.context_processor
    def inject_theme():
        try:
            from .api.theme_api import get_current_theme_settings, generate_theme_css
            theme_settings = get_current_theme_settings()
            theme_css = generate_theme_css(theme_settings)
            return {
                'theme_css': theme_css,
                'theme_settings': theme_settings
            }
        except Exception as e:
            app.logger.error(f"Error injecting theme context: {e}")
            return {
                'theme_css': '',
                'theme_settings': {
                    'primary_color': '#0d6efd',
                    'accent_color': '#6c757d',
                    'theme_mode': 'light'
                }
            }
    
    # Add version context processor
    @app.context_processor
    def inject_version():
        try:
            version_file = os.path.join(PROJECT_ROOT, 'VERSION')
            if os.path.exists(version_file):
                with open(version_file, 'r') as f:
                    app_version = f.read().strip()
            else:
                app_version = '1.0.0'
            return {'app_version': app_version}
        except Exception as e:
            app.logger.error(f"Error reading version file: {e}")
            return {'app_version': '1.0.0'}

    # Initialize and start the task scheduler
    from .scheduler import scheduler
    scheduler.init_app(app)
    
    # Start scheduler in production or when not in debug mode
    if not app.debug or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        scheduler.start()
        app.logger.info("Task scheduler started.")

    # Initialize and start the device polling scheduler
    from .device_scheduler import DevicePollingScheduler
    device_scheduler = DevicePollingScheduler()
    device_scheduler.init_app(app)
    
    # Start device scheduler in production or when not in debug mode
    if not app.debug or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        device_scheduler.start()
        app.logger.info("Device polling scheduler started.")
        
        # Reconfigure AI service now that app context is available
        # This allows it to read API keys from the database
        # Only run in the main process (not the reloader parent process)
        with app.app_context():
            from .services.ai_service import get_ai_service
            ai_service = get_ai_service()
            ai_service.reconfigure()
            app.logger.info(f"AI service configured - Gemini: {ai_service.is_configured}, Groq: {ai_service.groq_configured}")

    return app