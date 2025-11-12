#!/usr/bin/env python3
"""
Fix DNS resolution in all app instances by adding IPv6 disable sysctls
"""

import os
import yaml
import subprocess
from pathlib import Path
from datetime import datetime

APPS_DIR = Path.home() / "apps"

def fix_app_dns(app_dir):
    """Add sysctls to disable IPv6 in a single app"""
    app_name = app_dir.name
    compose_file = app_dir / "docker-compose.yml"
    
    if not compose_file.exists():
        return False, "No docker-compose.yml found"
    
    # Read current compose file
    try:
        with open(compose_file, 'r') as f:
            data = yaml.safe_load(f)
    except Exception as e:
        return False, f"Failed to parse YAML: {e}"
    
    # Check if sysctls and dns_opt already exist
    app_service = data.get('services', {}).get('app', {})
    has_sysctls = 'sysctls' in app_service
    has_dns_opt = 'dns_opt' in app_service
    
    if has_sysctls and has_dns_opt:
        return True, "Already has sysctls and dns_opt configured"
    
    # Backup
    backup_file = compose_file.parent / f"docker-compose.yml.backup-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    subprocess.run(['cp', str(compose_file), str(backup_file)])
    
    # Add sysctls
    if 'services' not in data:
        data['services'] = {}
    if 'app' not in data['services']:
        return False, "No 'app' service found in docker-compose.yml"
    
    data['services']['app']['sysctls'] = {
        'net.ipv6.conf.all.disable_ipv6': 1,
        'net.ipv6.conf.default.disable_ipv6': 1
    }
    
    # Add dns_opt to prevent IPv6 DNS timeout issues
    data['services']['app']['dns_opt'] = [
        'single-request',
        'timeout:2',
        'attempts:3'
    ]
    
    # Write back
    with open(compose_file, 'w') as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)
    
    # Recreate container
    os.chdir(app_dir)
    subprocess.run(['docker-compose', 'down'], capture_output=True)
    subprocess.run(['docker-compose', 'up', '-d'], capture_output=True)
    
    return True, "Added sysctls and restarted"

def main():
    print("🔧 Fixing DNS resolution in all app instances...")
    print()
    
    if not APPS_DIR.exists():
        print(f"❌ Apps directory not found: {APPS_DIR}")
        return
    
    success_count = 0
    skip_count = 0
    error_count = 0
    
    for app_dir in sorted(APPS_DIR.iterdir()):
        if not app_dir.is_dir():
            continue
        
        print(f"Processing: {app_dir.name}")
        success, message = fix_app_dns(app_dir)
        
        if success:
            if "Already has" in message:
                print(f"  ✓ {message}")
                skip_count += 1
            else:
                print(f"  ✅ {message}")
                success_count += 1
        else:
            print(f"  ❌ {message}")
            error_count += 1
        print()
    
    print("=" * 50)
    print(f"✅ Fixed: {success_count}")
    print(f"⏭️  Skipped: {skip_count}")
    print(f"❌ Errors: {error_count}")
    print()
    print("Test DNS with:")
    print('  docker exec <container-name> python3 -c "import socket; print(socket.gethostbyname(\'generativelanguage.googleapis.com\'))"')

if __name__ == "__main__":
    main()
