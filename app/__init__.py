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
    from .api.entry_api import entry_api_bp
    from .api.entry_type_api import entry_type_api_bp
    from .api.notes_api import notes_api_bp
    from .api.system_params_api import system_params_api_bp
    from .api.relationships_api import relationships_api_bp
    from .api.wikipedia_api import wikipedia_api_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(maintenance_bp)
    app.register_blueprint(entry_api_bp, url_prefix='/api')
    app.register_blueprint(entry_type_api_bp, url_prefix='/api')
    app.register_blueprint(notes_api_bp, url_prefix='/api')
    app.register_blueprint(system_params_api_bp, url_prefix='/api')
    app.register_blueprint(relationships_api_bp, url_prefix='/api')
    app.register_blueprint(wikipedia_api_bp, url_prefix='/api')

    app.logger.info("Blueprints registered.")

    return app