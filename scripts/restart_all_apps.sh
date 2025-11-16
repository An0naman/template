#!/bin/bash
# Restart all downstream apps to apply the updated icon configurations

APPS_DIR="/home/an0naman/apps"

echo "======================================"
echo "Restarting All Apps"
echo "======================================"
echo ""

# Check if apps directory exists
if [ ! -d "$APPS_DIR" ]; then
    echo "Error: Apps directory not found: $APPS_DIR"
    exit 1
fi

# Counter for tracking
success_count=0
error_count=0

# Loop through all app directories
for app_dir in "$APPS_DIR"/*; do
    if [ -d "$app_dir" ]; then
        app_name=$(basename "$app_dir")
        compose_file="$app_dir/docker-compose.yml"
        
        if [ -f "$compose_file" ]; then
            echo "Restarting: $app_name"
            cd "$app_dir"
            
            # Restart the app
            docker-compose up -d 2>&1 | grep -E "(Started|Running|up-to-date)" | head -1
            
            if [ ${PIPESTATUS[0]} -eq 0 ]; then
                echo "  ✅ Restarted successfully"
                ((success_count++))
            else
                echo "  ❌ Error restarting"
                ((error_count++))
            fi
        else
            echo "⚠️  $app_name: No docker-compose.yml found"
        fi
        echo ""
    fi
done

echo "======================================"
echo "Summary:"
echo "  Successful: $success_count apps"
echo "  Errors:     $error_count apps"
echo "======================================"

if [ $success_count -gt 0 ]; then
    echo ""
    echo "✅ Apps restarted and now using Tailscale VPN IP for icons"
    echo "📱 Your phone should now see all app icons via VPN!"
fi

exit 0
