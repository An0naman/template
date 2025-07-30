# template_app/app/config.py
import os

# Database configuration
DATABASE = 'template.db'
# This path is relative to the project root where run.py is located.
# Adjust if your database file is elsewhere.
DATABASE_PATH = os.path.join(os.path.abspath(os.path.dirname(os.path.dirname(__file__))), DATABASE)


# Secret key for session management (IMPORTANT: Change this in production!)
SECRET_KEY = 'your_super_secret_key_please_change_this_for_security'

# Logging directory (relative to project root)
LOG_DIR = 'logs'

# Application host and port for development
HOST = os.environ.get('HOST', '0.0.0.0')
PORT = int(os.environ.get('PORT', 5001))
DEBUG = os.environ.get('DEBUG', 'True').lower() == 'true'