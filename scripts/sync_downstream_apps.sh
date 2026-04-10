#!/bin/bash
# Sync the latest app-instance template defaults into all ~/apps/* deployments.

set -euo pipefail

TEMPLATE_DIR="${1:-/home/an0naman/Documents/GitHub/template/app-instance-template}"
APPS_DIR="${2:-$HOME/apps}"

if [ ! -d "$TEMPLATE_DIR" ]; then
    echo "Template directory not found: $TEMPLATE_DIR" >&2
    exit 1
fi

if [ ! -d "$APPS_DIR" ]; then
    echo "Apps directory not found: $APPS_DIR" >&2
    exit 1
fi

append_if_missing() {
    local env_file="$1"
    local key="$2"
    local value="${3-}"

    touch "$env_file"
    if ! grep -q "^${key}=" "$env_file"; then
        printf "%s=%s\n" "$key" "$value" >> "$env_file"
    fi
}

for app_dir in "$APPS_DIR"/*; do
    [ -d "$app_dir" ] || continue
    [ -f "$app_dir/docker-compose.yml" ] || continue

    app_name="$(basename "$app_dir")"
    env_file="$app_dir/.env"
    port="$(grep '^PORT=' "$env_file" 2>/dev/null | tail -n1 | cut -d= -f2- || true)"
    if [ -z "$port" ]; then
        port="$(grep -Eo '[0-9]{4,5}:[0-9]{4,5}' "$app_dir/docker-compose.yml" | head -n1 | cut -d: -f1 || true)"
    fi
    port="${port:-5001}"

    echo "==> Syncing $app_name (port ${port})"

    append_if_missing "$env_file" "APP_NAME" "$app_name"
    append_if_missing "$env_file" "PORT" "$port"
    append_if_missing "$env_file" "VERSION" "latest"
    append_if_missing "$env_file" "NETWORK_RANGE" "192.168.1.0/24"
    append_if_missing "$env_file" "AI_PROVIDER" ""
    append_if_missing "$env_file" "GEMINI_API_KEY" ""
    append_if_missing "$env_file" "OLLAMA_BASE_URL" ""
    append_if_missing "$env_file" "OLLAMA_MODEL_NAME" ""
    append_if_missing "$env_file" "NTFY_TOPIC" ""
    append_if_missing "$env_file" "NTFY_SERVER_URL" "https://ntfy.sh"
    append_if_missing "$env_file" "NTFY_AUTH_TOKEN" ""
    append_if_missing "$env_file" "SECRET_KEY" "change-this-in-production"
    append_if_missing "$env_file" "DEBUG" "false"
    append_if_missing "$env_file" "WATCHTOWER_POLL_INTERVAL" "300"
    append_if_missing "$env_file" "WATCHTOWER_NOTIFICATIONS" ""
    append_if_missing "$env_file" "WATCHTOWER_NOTIFICATION_URL" ""
    append_if_missing "$env_file" "TZ" "UTC"
    append_if_missing "$env_file" "TEMPLATE_SOURCE_DIR" "$TEMPLATE_DIR"

    cp "$TEMPLATE_DIR/sync-instance-config.py" "$app_dir/sync-instance-config.py"
    cp "$TEMPLATE_DIR/update.sh" "$app_dir/update.sh"
    cp "$TEMPLATE_DIR/run-migrations.sh" "$app_dir/run-migrations.sh"
    cp "$TEMPLATE_DIR/backup.sh" "$app_dir/backup.sh"
    chmod +x "$app_dir/update.sh" "$app_dir/run-migrations.sh" "$app_dir/backup.sh" "$app_dir/sync-instance-config.py"

    (
        cd "$app_dir"
        python3 ./sync-instance-config.py
        if command -v docker-compose >/dev/null 2>&1; then
            docker-compose up -d
        else
            docker compose up -d
        fi
    )
done

echo "All downstream apps synced."
