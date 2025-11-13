#!/bin/bash
#
# Add Uploads Volume to Existing Deployments
# This script updates docker-compose.yml files to include the uploads volume mount
#
# Usage: ./add_uploads_volume.sh <app_directory>
#   Example: ./add_uploads_volume.sh /home/an0naman/apps/devops
#

APP_DIR="$1"

if [ -z "$APP_DIR" ]; then
    echo "Usage: $0 <app_directory>"
    echo "Example: $0 /home/an0naman/apps/devops"
    exit 1
fi

if [ ! -d "$APP_DIR" ]; then
    echo "Error: Directory not found: $APP_DIR"
    exit 1
fi

COMPOSE_FILE="$APP_DIR/docker-compose.yml"

if [ ! -f "$COMPOSE_FILE" ]; then
    echo "Error: docker-compose.yml not found in $APP_DIR"
    exit 1
fi

echo "Updating $COMPOSE_FILE..."

# Create uploads directory if it doesn't exist
mkdir -p "$APP_DIR/uploads"

# Check if uploads volume already exists
if grep -q "uploads:/app/app/static/uploads" "$COMPOSE_FILE"; then
    echo "✓ Uploads volume already exists"
    exit 0
fi

# Backup the original file
cp "$COMPOSE_FILE" "$COMPOSE_FILE.backup.$(date +%Y%m%d_%H%M%S)"
echo "✓ Created backup"

# Add uploads volume mount after the data volume
sed -i '/target: \/app\/data/a\    - type: bind\n      source: '"$APP_DIR"'/uploads\n      target: /app/app/static/uploads\n      bind:\n        create_host_path: true' "$COMPOSE_FILE"

echo "✓ Added uploads volume mount"
echo ""
echo "Next steps:"
echo "1. cd $APP_DIR"
echo "2. docker compose down && docker compose up -d"
echo "3. Re-upload your logo in the app settings"
