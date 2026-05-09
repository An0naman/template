#!/bin/bash
# Update script for app instances
# Safely updates to latest framework version with backup and template sync

set -euo pipefail

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}Template Framework Update Script${NC}"
echo "=================================="
echo ""

# Detect docker compose command
if command -v docker-compose >/dev/null 2>&1; then
    COMPOSE_CMD=(docker-compose)
elif docker compose version >/dev/null 2>&1; then
    COMPOSE_CMD=(docker compose)
else
    echo -e "${RED}Error: docker-compose / docker compose not found${NC}"
    exit 1
fi

compose() {
    "${COMPOSE_CMD[@]}" "$@"
}

append_if_missing() {
    local key="$1"
    local value="${2-}"
    touch .env
    if ! grep -q "^${key}=" .env; then
        printf "%s=%s\n" "$key" "$value" >> .env
    fi
}

sync_template_defaults() {
    local template_dir=""
    local candidate=""

    for candidate in \
        "${TEMPLATE_SOURCE_DIR:-}" \
        "${FRAMEWORK_TEMPLATE_DIR:-}" \
        "/home/an0naman/Documents/GitHub/template/app-instance-template" \
        "$HOME/Documents/GitHub/template/app-instance-template"; do
        if [ -n "$candidate" ] && [ -f "$candidate/.env.example" ] && [ -f "$candidate/docker-compose.yml" ]; then
            template_dir="$candidate"
            break
        fi
    done

    if [ -z "$template_dir" ]; then
        echo -e "${YELLOW}Warning: no template source directory found; skipping compose sync${NC}"
        return 0
    fi

    echo -e "${YELLOW}Step 0: Syncing template defaults...${NC}"

    local app_dir_name="$(basename "$PWD")"
    local current_port
    current_port="$(grep '^PORT=' .env 2>/dev/null | tail -n1 | cut -d'=' -f2- || true)"
    if [ -z "$current_port" ] && [ -f docker-compose.yml ]; then
        current_port="$(grep -Eo '[0-9]{4,5}:[0-9]{4,5}' docker-compose.yml | head -n1 | cut -d: -f1 || true)"
    fi
    current_port="${current_port:-5001}"

    append_if_missing "APP_NAME" "$app_dir_name"
    append_if_missing "PORT" "$current_port"
    append_if_missing "VERSION" "latest"
    append_if_missing "NETWORK_RANGE" "192.168.1.0/24"
    append_if_missing "AI_PROVIDER" ""
    append_if_missing "GEMINI_API_KEY" ""
    append_if_missing "OLLAMA_BASE_URL" ""
    append_if_missing "OLLAMA_MODEL_NAME" ""
    append_if_missing "NTFY_TOPIC" ""
    append_if_missing "NTFY_SERVER_URL" "https://ntfy.sh"
    append_if_missing "NTFY_AUTH_TOKEN" ""
    append_if_missing "SECRET_KEY" "change-this-in-production"
    append_if_missing "DEBUG" "false"
    append_if_missing "WATCHTOWER_POLL_INTERVAL" "300"
    append_if_missing "DOCKER_API_VERSION" "1.41"
    append_if_missing "WATCHTOWER_NOTIFICATIONS" ""
    append_if_missing "WATCHTOWER_NOTIFICATION_URL" ""
    append_if_missing "TZ" "UTC"
    append_if_missing "TEMPLATE_SOURCE_DIR" "$template_dir"

    if [ -f "$template_dir/sync-instance-config.py" ]; then
        cp "$template_dir/sync-instance-config.py" ./sync-instance-config.py
        chmod +x ./sync-instance-config.py
        python3 ./sync-instance-config.py
        echo -e "${GREEN}✓ docker-compose.yml synced with current template defaults${NC}"
    fi

    for helper in backup.sh run-migrations.sh README.md .gitignore; do
        if [ -f "$template_dir/$helper" ]; then
            cp "$template_dir/$helper" "./$helper"
        fi
    done

    if [ -f "$template_dir/update.sh" ]; then
        cp "$template_dir/update.sh" ./update.sh
    fi

    chmod +x ./backup.sh ./run-migrations.sh ./update.sh ./sync-instance-config.py 2>/dev/null || true
    echo ""
}

detect_app_service() {
    local services
    services="$(compose config --services 2>/dev/null || true)"

    if echo "$services" | grep -qx "app"; then
        echo "app"
        return 0
    fi

    if [ -n "${APP_NAME:-}" ] && echo "$services" | grep -qx "${APP_NAME}"; then
        echo "${APP_NAME}"
        return 0
    fi

    echo "$services" | grep -v '^watchtower$' | head -n1
}

# Check if we're in the right directory
if [ ! -f "docker-compose.yml" ]; then
    echo -e "${RED}Error: docker-compose.yml not found${NC}"
    echo "Please run this script from your app instance directory"
    exit 1
fi

# Load environment variables
if [ -f ".env" ]; then
    set -a
    source .env
    set +a
else
    echo -e "${YELLOW}Warning: .env file not found, creating one with defaults${NC}"
    touch .env
fi

sync_template_defaults

set -a
source .env
set +a

APP_NAME=${APP_NAME:-$(basename "$PWD")}
VERSION=${VERSION:-latest}
APP_SERVICE="$(detect_app_service)"

if [ -z "$APP_SERVICE" ]; then
    echo -e "${RED}Error: could not determine the app service name from docker-compose.yml${NC}"
    exit 1
fi

echo "App Name: ${APP_NAME}"
echo "Target Version: ${VERSION}"
echo "Compose Service: ${APP_SERVICE}"
echo ""

# Step 1: Create backup
echo -e "${YELLOW}Step 1: Creating backup...${NC}"
BACKUP_FILE="backup-$(date +%Y%m%d-%H%M%S).tar.gz"
if [ -d "data" ]; then
    tar -czf "${BACKUP_FILE}" data/ 2>/dev/null || echo "Backup created with warnings"
    echo -e "${GREEN}✓ Backup created: ${BACKUP_FILE}${NC}"
else
    echo -e "${YELLOW}⚠ No data directory found, skipping backup${NC}"
fi
echo ""

# Step 2: Pull latest image
echo -e "${YELLOW}Step 2: Pulling latest framework image...${NC}"
compose pull
echo -e "${GREEN}✓ Image pulled${NC}"
echo ""

# Step 3: Stop and remove old container
echo -e "${YELLOW}Step 3: Stopping container...${NC}"
compose down
echo -e "${GREEN}✓ Container stopped${NC}"
echo ""

# Step 4: Start with new image
echo -e "${YELLOW}Step 4: Starting updated container...${NC}"
compose up -d
echo -e "${GREEN}✓ Container started${NC}"
echo ""

# Step 5: Run database migrations
echo -e "${YELLOW}Step 5: Running database migrations...${NC}"
sleep 5

if compose exec -T "$APP_SERVICE" test -d /app/migrations 2>/dev/null; then
    MIGRATION_COUNT=0
    for migration in $(compose exec -T "$APP_SERVICE" sh -c "find /app/migrations -name '*.py' -not -path '*/__pycache__/*' | sort" 2>/dev/null || echo ""); do
        if [ -n "$migration" ]; then
            MIGRATION_NAME=$(basename "$migration")
            echo "  Running migration: ${MIGRATION_NAME}"
            if compose exec -T "$APP_SERVICE" python "$migration" 2>&1 | tee /tmp/migration_output.txt; then
                if grep -q "already exists\|Skipping migration\|Migration not needed" /tmp/migration_output.txt; then
                    echo "    ↳ Already applied"
                else
                    echo "    ↳ Applied successfully"
                    MIGRATION_COUNT=$((MIGRATION_COUNT + 1))
                fi
            else
                echo -e "    ${RED}↳ Failed${NC}"
                echo -e "${RED}Migration failed. Check logs for details.${NC}"
            fi
        fi
    done

    if [ "$MIGRATION_COUNT" -gt 0 ]; then
        echo -e "${GREEN}✓ Applied ${MIGRATION_COUNT} new migration(s)${NC}"
    else
        echo -e "${GREEN}✓ No new migrations to apply${NC}"
    fi
else
    echo "  No migrations directory found, skipping..."
fi
echo ""

# Step 6: Wait for health check
echo -e "${YELLOW}Step 6: Waiting for app to be healthy...${NC}"
sleep 5

if compose ps --status running | grep -q "$APP_SERVICE"; then
    echo -e "${GREEN}✓ Container is running${NC}"
else
    echo -e "${RED}✗ Container failed to start${NC}"
    echo ""
    echo "Rolling back..."
    compose down
    echo ""
    echo "Check logs with: ${COMPOSE_CMD[*]} logs"
    echo "Restore backup with: tar -xzf ${BACKUP_FILE}"
    exit 1
fi

echo ""
echo -e "${YELLOW}Step 7: Verifying update...${NC}"
CURRENT_VERSION=$(compose exec -T "$APP_SERVICE" cat /app/VERSION 2>/dev/null || echo "unknown")
echo "Running version: ${CURRENT_VERSION}"
echo ""

echo -e "${GREEN}=================================="
echo "✓ Update completed successfully!"
echo "==================================${NC}"
echo ""
echo "Backup saved to: ${BACKUP_FILE}"
echo ""
echo "View logs with: ${COMPOSE_CMD[*]} logs -f"
echo "Check status with: ${COMPOSE_CMD[*]} ps"
echo ""