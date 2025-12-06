# template_app/app/config.py
import os

# Get the project root directory (where run.py is located)
PROJECT_ROOT = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

# Database configuration
DATABASE = 'template.db'
DATABASE_PATH = os.path.join(PROJECT_ROOT, 'data', DATABASE)

# Ensure data directory exists
os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)

# Secret key for session management (IMPORTANT: Change this in production!)
SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')

# Logging directory (relative to project root)
LOG_DIR = os.path.join(PROJECT_ROOT, 'logs')
os.makedirs(LOG_DIR, exist_ok=True)

# Application host and port for development
HOST = os.environ.get('HOST', '0.0.0.0')
PORT = int(os.environ.get('PORT', 5001))
DEBUG = os.environ.get('DEBUG', 'True').lower() == 'true'

# File upload configuration
# Use /app/uploads if it exists (Docker volume), otherwise fallback to local static folder
if os.path.exists('/app/uploads'):
    UPLOAD_FOLDER = '/app/uploads'
else:
    UPLOAD_FOLDER = os.path.join(PROJECT_ROOT, 'app', 'static', 'uploads')

MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB max file size
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ntfy Push Notification Configuration
# These can be overridden by environment variables
NTFY_SERVER_URL = os.environ.get('NTFY_SERVER_URL', 'https://ntfy.sh')
NTFY_TOPIC = os.environ.get('NTFY_TOPIC')  # No default - must be configured
NTFY_AUTH_TOKEN = os.environ.get('NTFY_AUTH_TOKEN')  # Optional for private topics