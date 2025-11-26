#!/bin/bash
# Update all downstream app icons to use Tailscale VPN IP instead of local IP
# This makes apps accessible via VPN (e.g., from your phone)

TAILSCALE_IP="100.84.208.29"
LOCAL_IP="192.168.68.110"
APPS_DIR="/home/an0naman/apps"

echo "======================================"
echo "Updating App Icons for VPN Access"
echo "======================================"
echo "Changing from: $LOCAL_IP"
echo "         to:   $TAILSCALE_IP"
echo ""

# Check if apps directory exists
if [ ! -d "$APPS_DIR" ]; then
    echo "Error: Apps directory not found: $APPS_DIR"
    exit 1
fi

# Counter for tracking
updated_count=0
skipped_count=0
error_count=0

# Loop through all app directories
for app_dir in "$APPS_DIR"/*; do
    if [ -d "$app_dir" ]; then
        app_name=$(basename "$app_dir")
        compose_file="$app_dir/docker-compose.yml"
        
        if [ -f "$compose_file" ]; then
            echo "Processing: $app_name"
            
            # Check if file contains the local IP
            if grep -q "$LOCAL_IP" "$compose_file"; then
                # Create backup
                cp "$compose_file" "$compose_file.backup.$(date +%Y%m%d_%H%M%S)"
                
                # Replace local IP with Tailscale IP
                sed -i "s|http://$LOCAL_IP:|http://$TAILSCALE_IP:|g" "$compose_file"
                
                if [ $? -eq 0 ]; then
                    echo "  ✅ Updated icon URL"
                    ((updated_count++))
                else
                    echo "  ❌ Error updating file"
                    ((error_count++))
                fi
            else
                echo "  ⏭️  No local IP found (already updated or different config)"
                ((skipped_count++))
            fi
        else
            echo "  ⚠️  No docker-compose.yml found"
            ((skipped_count++))
        fi
        echo ""
    fi
done

echo "======================================"
echo "Summary:"
echo "  Updated:  $updated_count apps"
echo "  Skipped:  $skipped_count apps"
echo "  Errors:   $error_count apps"
echo "======================================"
echo ""

if [ $updated_count -gt 0 ]; then
    echo "📝 Next Steps:"
    echo "1. Review changes in updated apps"
    echo "2. Restart apps to apply changes:"
    echo "   cd /home/an0naman/apps/<app-name> && docker-compose up -d"
    echo ""
    echo "Or restart all apps at once:"
    echo "   for app in $APPS_DIR/*/; do cd \"\$app\" && docker-compose up -d; done"
    echo ""
    echo "💡 Backups saved with .backup.<timestamp> extension"
fi

exit 0
