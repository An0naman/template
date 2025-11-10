#!/bin/bash
# Fix DNS resolution in all app instances by adding IPv6 disable sysctls

APPS_DIR=~/apps

echo "🔧 Fixing DNS resolution in all app instances..."
echo ""

for app_dir in "$APPS_DIR"/*; do
    if [ -d "$app_dir" ] && [ -f "$app_dir/docker-compose.yml" ]; then
        app_name=$(basename "$app_dir")
        echo "Processing: $app_name"
        
        # Check if sysctls already exists
        if grep -q "sysctls:" "$app_dir/docker-compose.yml"; then
            echo "  ✓ Already has sysctls configured"
        else
            # Backup
            cp "$app_dir/docker-compose.yml" "$app_dir/docker-compose.yml.backup-$(date +%Y%m%d-%H%M%S)"
            
            # Add sysctls after dns section
            sed -i '/dns:/,/^[[:space:]]*$/{ /^[[:space:]]*$/i\    \n    # Prefer IPv4 for DNS resolution (fixes Google API connectivity issues)\n    sysctls:\n      - net.ipv6.conf.all.disable_ipv6=1\n      - net.ipv6.conf.default.disable_ipv6=1
}' "$app_dir/docker-compose.yml"
            
            echo "  ✓ Added IPv6 disable sysctls"
            
            # Restart container
            cd "$app_dir"
            docker-compose up -d
            echo "  ✓ Restarted container"
        fi
        echo ""
    fi
done

echo "✅ All apps updated!"
echo ""
echo "Test with:"
echo "  docker exec <container-name> python3 -c \"import socket; print(socket.gethostbyname('generativelanguage.googleapis.com'))\""
