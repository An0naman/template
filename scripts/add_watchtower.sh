#!/bin/bash

# Add Watchtower to Existing App Instance
# This script adds automatic update support to an existing app
# Usage: ./add_watchtower.sh /path/to/app

set -e

APP_DIR="${1:-.}"

if [ ! -f "$APP_DIR/docker-compose.yml" ]; then
    echo "❌ Error: No docker-compose.yml found in $APP_DIR"
    exit 1
fi

echo "🔧 Adding Watchtower to app in: $APP_DIR"
echo ""

# Backup existing files
echo "📦 Creating backup..."
cp "$APP_DIR/docker-compose.yml" "$APP_DIR/docker-compose.yml.backup.$(date +%Y%m%d_%H%M%S)"
if [ -f "$APP_DIR/.env" ]; then
    cp "$APP_DIR/.env" "$APP_DIR/.env.backup.$(date +%Y%m%d_%H%M%S)"
fi
echo "✅ Backup created"
echo ""

# Check if watchtower already exists
if grep -q "watchtower:" "$APP_DIR/docker-compose.yml"; then
    echo "⚠️  Watchtower service already exists in docker-compose.yml"
    echo "   Skipping docker-compose.yml modification"
else
    echo "📝 Adding watchtower service to docker-compose.yml..."
    
    # Check if app service has the label
    if ! grep -q "com.centurylinklabs.watchtower.enable" "$APP_DIR/docker-compose.yml"; then
        echo "⚠️  Warning: App service doesn't have watchtower label"
        echo "   You may need to manually add this to the 'app' service:"
        echo "   labels:"
        echo "     - \"com.centurylinklabs.watchtower.enable=true\""
        echo ""
    fi
    
    # Add watchtower service
    cat >> "$APP_DIR/docker-compose.yml" << 'EOF'

  # Watchtower - Automatic updates when new framework versions are released
  watchtower:
    image: containrrr/watchtower
    container_name: ${APP_NAME:-myapp}-watchtower
    restart: always
    
    volumes:
      # Docker socket for managing containers
      - /var/run/docker.sock:/var/run/docker.sock
    
    environment:
      # Check for updates every 5 minutes (300 seconds)
      - WATCHTOWER_POLL_INTERVAL=${WATCHTOWER_POLL_INTERVAL:-300}
      
      # Remove old images after updating
      - WATCHTOWER_CLEANUP=true
      
      # Only update running containers
      - WATCHTOWER_INCLUDE_STOPPED=false
      
      # Only update containers with the watchtower label
      - WATCHTOWER_LABEL_ENABLE=true
      
      # Optional: Send notifications on updates
      - WATCHTOWER_NOTIFICATIONS=${WATCHTOWER_NOTIFICATIONS:-}
      - WATCHTOWER_NOTIFICATION_URL=${WATCHTOWER_NOTIFICATION_URL:-}
      
      # Timezone for logs
      - TZ=${TZ:-UTC}
    
    # Only monitor containers with the watchtower label
    command: --label-enable
EOF
    echo "✅ Watchtower service added"
fi
echo ""

# Update .env file
if [ -f "$APP_DIR/.env" ]; then
    echo "📝 Updating .env file..."
    
    if grep -q "WATCHTOWER_POLL_INTERVAL" "$APP_DIR/.env"; then
        echo "   Watchtower settings already exist in .env"
    else
        cat >> "$APP_DIR/.env" << 'EOF'

# ============================================================================
# AUTOMATIC UPDATES (WATCHTOWER)
# ============================================================================

# How often to check for updates (in seconds)
# Default: 300 (5 minutes)
# Options: 60 (1 min), 300 (5 min), 3600 (1 hour), 86400 (daily)
WATCHTOWER_POLL_INTERVAL=300

# Notification service for update alerts (optional)
# Leave empty to disable notifications
WATCHTOWER_NOTIFICATIONS=

# Notification URL (examples):
# - ntfy.sh: ntfy://ntfy.sh/your-updates-topic
# - Email: smtp://user:password@host:port/?from=sender@example.com&to=recipient@example.com
WATCHTOWER_NOTIFICATION_URL=

# Timezone for watchtower logs
TZ=UTC
EOF
        echo "✅ Watchtower settings added to .env"
    fi
else
    echo "⚠️  No .env file found - you may need to add watchtower environment variables"
fi
echo ""

# Restart services
echo "🚀 Restarting services..."
cd "$APP_DIR"
docker-compose up -d
echo "✅ Services restarted"
echo ""

# Show status
echo "📊 Status:"
docker-compose ps
echo ""

echo "🎉 Watchtower setup complete!"
echo ""
echo "Next steps:"
echo "1. Check watchtower logs: docker logs -f \$(docker ps | grep watchtower | awk '{print \$1}')"
echo "2. Configure notifications in .env (optional)"
echo "3. Monitor for automatic updates (next check in ~5 minutes)"
echo ""
echo "📚 Documentation: docs/framework/AUTO_UPDATE.md"
