# CasaOS Icon Auto-Update Scripts

Automatically update CasaOS app icons to use the dynamic `/api/logo` endpoint with the correct IP address.

## Overview

These scripts solve the problem of hardcoded icon URLs in CasaOS metadata by:
1. Detecting your server's current IP address
2. Updating CasaOS app metadata to use `http://<your-ip>:<port>/api/logo`
3. Supporting both single app updates and batch updates

## Scripts

### 1. `update_casaos_icon.sh` - Single App Updater

Updates the CasaOS icon for a specific app.

**Usage:**
```bash
sudo ./scripts/update_casaos_icon.sh [app_name] [port]
```

**Examples:**
```bash
# Update the 'template' app on port 5001
sudo ./scripts/update_casaos_icon.sh template 5001

# Update 'garden-management' app on port 5002
sudo ./scripts/update_casaos_icon.sh garden-management 5002
```

**Features:**
- ✅ Auto-detects primary network interface and IP
- ✅ Creates backup of original metadata
- ✅ Uses `jq` if available for safe JSON updates
- ✅ Falls back to `sed` if `jq` not installed
- ✅ Verifies changes before completing

### 2. `update_all_casaos_icons.sh` - Batch Updater

Scans all CasaOS apps and updates their icons automatically.

**Usage:**
```bash
sudo ./scripts/update_all_casaos_icons.sh
```

**Features:**
- ✅ Finds all CasaOS app metadata files
- ✅ Reads port from each app's metadata
- ✅ Updates all apps in one run
- ✅ Provides summary report

## Requirements

- Root/sudo access (needed to modify `/var/lib/casaos/apps/`)
- CasaOS installed and running
- `jq` (optional but recommended): `sudo apt install jq`

## When to Run

Run these scripts:
- **After initial deployment** - Set up icons for new apps
- **After network changes** - Update IPs when your server address changes
- **After CasaOS updates** - Restore custom icons if reset

## How It Works

1. Script detects your server's primary network interface (e.g., `wlp0s20f3`, `eth0`)
2. Reads the IP address from that interface (e.g., `192.168.68.107`)
3. Constructs icon URL: `http://192.168.68.107:5001/api/logo`
4. Updates `/var/lib/casaos/apps/<app>.json` with new icon URL
5. CasaOS fetches the logo from your app's `/api/logo` endpoint

## The `/api/logo` Endpoint

Each app provides a `/api/logo` endpoint that:
- Reads `project_logo_path` from SystemParameters
- Serves the logo file directly
- Returns 404 if no logo is configured

This means:
- Icons automatically update when you change the logo in Settings
- Each app shows its own configured logo
- No external dependencies or hardcoded URLs

## Troubleshooting

### Icons not showing after update

```bash
# Refresh CasaOS
sudo systemctl restart casaos

# Or check if the endpoint works
curl -I http://192.168.68.107:5001/api/logo
```

### Wrong IP detected

```bash
# Check available interfaces
ip addr show

# Manually specify in the script or edit METADATA_FILE directly
```

### App metadata not found

```bash
# List available apps
ls -1 /var/lib/casaos/apps/*.json | xargs -n1 basename
```

## Integration with Deployment

You can add icon updates to your deployment workflow:

```bash
# After deploying a new app
docker compose up -d
sudo ./scripts/update_casaos_icon.sh my-new-app 5003
```

Or run batch update after deploying multiple apps:

```bash
sudo ./scripts/update_all_casaos_icons.sh
```

## Backup & Restore

The script automatically creates backups:
```bash
/var/lib/casaos/apps/template.json.backup.20251113_122336
```

To restore:
```bash
sudo cp /var/lib/casaos/apps/template.json.backup.* /var/lib/casaos/apps/template.json
sudo systemctl restart casaos
```

## Related Files

- `/var/lib/casaos/apps/<app>.json` - CasaOS app metadata
- `app.json` - Template for new deployments (uses `/api/logo`)
- `docker-compose.yml` - Docker Compose with CasaOS metadata
- `app/__init__.py` - Contains `/api/logo` endpoint implementation

## Notes

- The `/api/logo` endpoint must be implemented in your app
- Logo path comes from `SystemParameters.project_logo_path`
- CasaOS may cache icons - hard refresh or restart if needed
- Changes take effect immediately but may require browser refresh
