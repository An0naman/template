#!/bin/bash
#
# Auto-update CasaOS icon from database
# This script runs at container startup to sync the docker-compose icon
# with the current logo in the database
#
# Usage: Add to docker-entrypoint.sh before starting the app
#

set -e

DB_PATH="${DB_PATH:-/app/data/template.db}"
COMPOSE_FILE="${COMPOSE_FILE:-/app/docker-compose.yml}"

# Check if database exists
if [ ! -f "$DB_PATH" ]; then
    echo "Database not found at $DB_PATH, skipping icon update"
    exit 0
fi

# Get logo path from database
LOGO_PATH=$(sqlite3 "$DB_PATH" "SELECT parameter_value FROM SystemParameters WHERE parameter_name = 'project_logo_path';" 2>/dev/null || echo "")

if [ -z "$LOGO_PATH" ] || [ "$LOGO_PATH" = "" ]; then
    echo "No logo configured in database, skipping icon update"
    exit 0
fi

# Get the filename from the path
LOGO_FILENAME=$(basename "$LOGO_PATH")

# Get the app's external URL (from environment or detect)
APP_HOST="${APP_HOST:-localhost}"
APP_PORT="${PORT:-5001}"
ICON_URL="http://${APP_HOST}:${APP_PORT}/static/uploads/${LOGO_FILENAME}"

echo "Auto-updating CasaOS icon to: $ICON_URL"

# Update APP_ICON_URL environment variable for this session
export APP_ICON_URL="$ICON_URL"

# Note: This updates the env var for the current container session
# The docker-compose.yml will use this value when CasaOS reads it
echo "APP_ICON_URL=${ICON_URL}"
