# template_app/run.py
from app import create_app
import os
import logging

# Set up a basic logger for the run.py script itself
# This is separate from the app's internal loggers
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Get the path to the current directory (where run.py is)
# This helps in locating the 'app' directory correctly
base_dir = os.path.abspath(os.path.dirname(__file__))
# print(f"Base Directory: {base_dir}") # For debugging path issues

app = create_app()

if __name__ == '__main__':
    # When running directly, ensure the database is initialized
    # This context is necessary for app.config and g.db to be available
    with app.app_context():
        # You can import init_db here or let create_app handle it,
        # but explicit call ensures it runs when run.py is executed.
        # Given db.py init_db already takes care of table creation,
        # calling it once at app startup in this way is reasonable for development.
        from app.db import init_db
        logging.info("Initializing database...")
        init_db()
        logging.info("Database initialized.")

    logging.info("Starting Flask application...")
    app.run(debug=app.config.get('DEBUG', True),
            host=app.config.get('HOST', '0.0.0.0'),
            port=app.config.get('PORT', 5001))