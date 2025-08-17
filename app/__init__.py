# template_app/app/__init__.py
import sqlite3
from flask import Flask, g
import os
import logging

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


    # --- Register Blueprints ---
    from .routes.main_routes import main_bp
    from .routes.maintenance_routes import maintenance_bp
    
    # Import all API blueprints
    from .api.entry_api import entry_api_bp
    from .api.entry_type_api import entry_type_api_bp
    from .api.notes_api import notes_api_bp
    from .api.system_params_api import system_params_api_bp
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

    # Register all blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(maintenance_bp)
    app.register_blueprint(entry_api_bp, url_prefix='/api')
    app.register_blueprint(entry_type_api_bp, url_prefix='/api')
    app.register_blueprint(notes_api_bp, url_prefix='/api')
    app.register_blueprint(system_params_api_bp, url_prefix='/api')
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

    return app