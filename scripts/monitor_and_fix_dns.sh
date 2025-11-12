#!/bin/bash
# Monitor Docker events and fix DNS when containers are updated

SCRIPT_PATH="/home/an0naman/Documents/GitHub/template/scripts/fix_dns_all_apps.py"
LOG_FILE="/var/log/docker-dns-fixer.log"

echo "[$(date)] Docker DNS fixer started" >> "$LOG_FILE"

# Monitor Docker events for container starts (which happen after watchtower updates)
docker events --filter 'type=container' --filter 'event=start' --format '{{.Actor.Attributes.name}}' | while read container_name
do
    # Skip watchtower containers
    if [[ "$container_name" == *"watchtower"* ]]; then
        continue
    fi
    
    echo "[$(date)] Container started: $container_name" >> "$LOG_FILE"
    
    # Wait a moment for container to be ready
    sleep 2
    
    # Test if DNS is working
    if docker exec "$container_name" python3 -c "import socket; socket.gethostbyname('google.com')" 2>&1 | grep -q "Temporary failure"; then
        echo "[$(date)] DNS issue detected in $container_name, running fix..." >> "$LOG_FILE"
        
        # Run the fix script
        python3 "$SCRIPT_PATH" >> "$LOG_FILE" 2>&1
        
        echo "[$(date)] Fix completed" >> "$LOG_FILE"
        break  # Only fix once, the script handles all apps
    else
        echo "[$(date)] DNS OK in $container_name" >> "$LOG_FILE"
    fi
done
