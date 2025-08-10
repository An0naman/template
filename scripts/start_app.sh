#!/bin/bash

# Start the Flask application with proper virtual environment
# Usage: ./start_app.sh [port]

cd "$(dirname "$0")"

# Set default port
PORT=${1:-5002}

echo "Starting Flask application on port $PORT..."
echo "Virtual environment: $(pwd)/.venv/bin/python"
echo ""
echo "Application will be available at:"
echo "  http://localhost:$PORT/"
echo "  http://127.0.0.1:$PORT/"
echo ""
echo "Press Ctrl+C to stop the application"
echo ""

# Activate virtual environment and start the app
export PORT=$PORT
exec ./.venv/bin/python run.py
