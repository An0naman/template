# Framework Deployment Guide

Complete guide for deploying and managing the Template Framework and app instances.

---

## Table of Contents

1. [Framework Publishing](#framework-publ4. Go to **Settings** → **Data Structure**
5. Create entry types and states

---

## Database Migrations

### What Are Migrations?

Database migrations are scripts that update your database schema when new features are added to the framework. The framework includes an automated migration system that runs when you update your app instance.

### Automatic Migrations (Recommended)

When you run `./update.sh`, migrations are **automatically applied** after pulling the new image:

```bash
cd ~/apps/homebrews
./update.sh

# Output includes:
# Step 5: Running database migrations...
#   Running migration: add_entry_level_template_sharing.py
#     ↳ Applied successfully
# ✓ Applied 1 new migration(s)
```

### Manual Migration Run

If you need to run migrations manually (e.g., after manual image update):

```bash
cd ~/apps/homebrews
./run-migrations.sh
```

This will:
1. ✅ Create automatic database backup before migrations
2. ✅ Run all pending migrations in order
3. ✅ Show detailed progress for each migration
4. ✅ Skip already-applied migrations
5. ✅ Provide rollback options if anything fails

### Migration Safety Features

**Automatic Backups:**
- Every migration run creates a timestamped backup
- Stored in `migration-backups/` directory
- Restore anytime: `tar -xzf migration-backups/db-before-migration-*.tar.gz`

**Idempotent Execution:**
- Migrations can be run multiple times safely
- Already-applied migrations are automatically skipped
- No duplicate data or schema conflicts

**Error Handling:**
- Failed migrations stop the process
- Clear error messages with troubleshooting steps
- Backup available for immediate rollback

### Checking Migration Status

**See which migrations exist:**
```bash
docker-compose exec homebrews ls -la /app/migrations/
```

**Check if a migration was applied:**
```bash
# Example: Check if source_entry_id column exists
docker-compose exec homebrews python -c "
import sqlite3
conn = sqlite3.connect('/app/data/homebrew.db')
cursor = conn.cursor()
cursor.execute('PRAGMA table_info(TemplateRelationshipSharing)')
columns = [row[1] for row in cursor.fetchall()]
print('source_entry_id' in columns)
"
```

### Current Migrations

The framework includes these migrations:

1. **add_entry_level_template_sharing.py** (Latest)
   - Adds `source_entry_id` column to `TemplateRelationshipSharing` table
   - Enables relationship-based template sharing via parent entries
   - Required for: Milestone template sharing feature
   - See: [RELATIONSHIP_TEMPLATE_SHARING_UPDATE.md](../../RELATIONSHIP_TEMPLATE_SHARING_UPDATE.md)

2. **[Other migrations as added]**
   - Additional migrations will be documented here

### Troubleshooting Migrations

**Migration fails with "database locked":**
```bash
# Stop the app first
docker-compose down
./run-migrations.sh
docker-compose up -d
```

**Migration fails with "no such table":**
- This usually means your database is from an older version
- Contact support or check framework documentation
- May need to run earlier migrations first

**Want to rollback a migration:**
```bash
# Restore from backup
cd ~/apps/homebrews
tar -xzf migration-backups/db-before-migration-YYYYMMDD-HHMMSS.tar.gz

# Restart container
docker-compose restart
```

**Need to force re-run a migration:**
```bash
# Manually execute specific migration
docker-compose exec homebrews python /app/migrations/add_entry_level_template_sharing.py
```

---

## Configuration

### Initial Configuration

1. **Access web interface**: 
   - Local: `http://localhost:PORT`
   - Network: `http://SERVER_IP:PORT` (accessible from any device)
   - CasaOS: Add as custom app with network URL
2. **Go to Settings** → **System Configuration**
3. **Configure**:
   - Project Name: "HomeBrews Inventory"
   - Entry Label (singular): "Brew"
   - Entry Label (plural): "Brews"
   - Theme: Choose colors
4. Go to **Settings** → **Data Structure**
5. Create entry types and states [Creating New App Instances](#creating-new-app-instances)
3. [Configuration](#configuration)
4. [Multiple App Setup](#multiple-app-setup)
5. [Advanced Scenarios](#advanced-scenarios)

---

## Framework Publishing

### Prerequisites

- Docker and Docker Buildx installed
- GitHub account with access to repository
- GitHub Container Registry access

### Option 1: Automatic Publishing (GitHub Actions)

The framework automatically builds and publishes when you push code:

```bash
# Make changes to framework
git add .
git commit -m "Add new feature"
git push origin main
```

GitHub Actions will:
- Build Docker image for amd64 and arm64
- Run tests
- Push to `ghcr.io/an0naman/template:latest`
- Create build summary

### Option 2: Tagged Releases

Create a version release:

```bash
# Tag your release
git tag -a v1.2.0 -m "Release version 1.2.0"
git push origin v1.2.0
```

This creates:
- `ghcr.io/an0naman/template:v1.2.0`
- `ghcr.io/an0naman/template:v1.2`
- `ghcr.io/an0naman/template:v1`
- `ghcr.io/an0naman/template:latest`
- GitHub Release with changelog

### Option 3: Manual Build

Use the provided script:

```bash
# Build and push manually
./scripts/build-and-push.sh v1.2.0

# Or development build
./scripts/build-and-push.sh dev
```

### Verify Publication

```bash
# Check available tags
docker pull ghcr.io/an0naman/template:latest
docker images ghcr.io/an0naman/template

# View on GitHub
# Visit: https://github.com/An0naman/template/pkgs/container/template
```

---

## Creating New App Instances

### Quick Start

```bash
# 1. Create app directory
mkdir -p ~/apps/homebrews
cd ~/apps/homebrews

# 2. Copy template files
cp -r /path/to/template/app-instance-template/* .
cp /path/to/template/app-instance-template/.* . 2>/dev/null || true

# 3. Configure environment
cp .env.example .env
nano .env  # Edit APP_NAME, PORT, etc.

# 4. Start app
docker-compose pull
docker-compose up -d

# 5. Access app
echo "Visit: http://localhost:$(grep PORT .env | cut -d'=' -f2)"
echo "Or from network: http://$(hostname -I | awk '{print $1}'):$(grep PORT .env | cut -d'=' -f2)"
```

### Detailed Steps

#### Step 1: Prepare Directory

```bash
# Choose a location for your apps
APP_BASE=~/apps

# Create directory for specific app
APP_NAME=homebrews  # Change this
mkdir -p ${APP_BASE}/${APP_NAME}
cd ${APP_BASE}/${APP_NAME}
```

#### Step 2: Get Template Files

Option A - Copy from framework repo:
```bash
TEMPLATE_PATH=/path/to/template/app-instance-template
cp -r ${TEMPLATE_PATH}/* .
cp ${TEMPLATE_PATH}/.env.example .env
cp ${TEMPLATE_PATH}/.gitignore .
```

Option B - Download from GitHub:
```bash
curl -L https://github.com/An0naman/template/archive/main.tar.gz | \
  tar xz --strip=2 template-main/app-instance-template
mv .env.example .env
```

#### Step 3: Configure Application

Edit `.env` file:

```bash
nano .env
```

Required settings:
```bash
APP_NAME=homebrews           # Unique container name
PORT=5001                    # External port (must be unique)
VERSION=latest               # Or specific version: v1.2.0
```

Optional settings:
```bash
NETWORK_RANGE=192.168.1.0/24    # For IoT devices
GEMINI_API_KEY=your-key         # For AI features
NTFY_TOPIC=homebrews-alerts     # For notifications
SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
DEBUG=false
```

#### Step 4: Start Application

```bash
# Pull framework image
docker-compose pull

# Start in detached mode
docker-compose up -d

# View logs
docker-compose logs -f
```

#### Step 5: Initial Configuration

1. **Access web interface**: 
   - Local: `http://localhost:PORT`
   - Network: `http://SERVER_IP:PORT` (accessible from any device)
   - CasaOS: Add as custom app with network URL
2. **Go to Settings** → **System Configuration**
3. **Configure**:
   - Project Name: "HomeBrews Inventory"
   - Entry Label (singular): "Brew"
   - Entry Label (plural): "Brews"
   - Theme: Choose colors
4. **Set up Entry Types** (Settings → Data Structure):
   - Beer, Wine, Mead, etc.
5. **Configure States** for each type:
   - Planning, Brewing, Fermenting, Bottled, etc.

---

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `APP_NAME` | Yes | myapp | Container name (must be unique) |
| `PORT` | Yes | 5001 | External port (must be unique) |
| `VERSION` | No | latest | Framework version to use |
| `NETWORK_RANGE` | No | 192.168.1.0/24 | Network for device discovery |
| `GEMINI_API_KEY` | No | - | Google Gemini API key |
| `NTFY_TOPIC` | No | - | Push notification topic |
| `NTFY_SERVER_URL` | No | https://ntfy.sh | Notification server |
| `SECRET_KEY` | No | auto | Flask secret key |
| `DEBUG` | No | false | Debug mode |

### Network Modes

**Bridge Mode** (default in template - CasaOS compatible):
```yaml
# network_mode: host  # Commented out
ports:
  - "${PORT:-5001}:${PORT:-5001}"
```
- ✅ **Pros**: Network accessible, CasaOS compatible, better isolation
- ⚠️ **Cons**: Bluetooth requires extra configuration
- 📱 **Use when**: Deploying on CasaOS or need network access
- 🌐 **Access**: `http://SERVER_IP:PORT` from any device

**Host Mode** (optional - for Bluetooth):
```yaml
network_mode: host
# ports:  # Not used with host mode
```
- ✅ **Pros**: Bluetooth works perfectly, easy device discovery
- ⚠️ **Cons**: Not accessible from CasaOS web UI, port conflicts possible
- 🖨️ **Use when**: You need Bluetooth (Niimbot printers) or IoT devices
- 🏠 **Access**: `http://localhost:PORT` (local server only)

> **Note**: The template now uses **bridge mode by default** for CasaOS compatibility. 
> If you need Bluetooth, uncomment `network_mode: host` and comment out the `ports:` section.

### Bluetooth Configuration

If you need full Bluetooth support (Niimbot printers):

1. Edit `docker-compose.yml`:
   ```yaml
   # Uncomment this:
   network_mode: host
   
   # Comment out this:
   # ports:
   #   - "${PORT:-5001}:${PORT:-5001}"
   ```

2. Keep these settings:
   ```yaml
network_mode: host
devices:
  - /dev/bus/usb:/dev/bus/usb
cap_add:
  - NET_ADMIN
  - SYS_ADMIN
  - NET_RAW
privileged: true
volumes:
  - /var/run/dbus:/var/run/dbus
  - /run/dbus:/run/dbus
  - /sys/class/bluetooth:/sys/class/bluetooth

# Add instead:
network_mode: bridge
ports:
  - "${PORT}:5001"
```

---

## Multiple App Setup

### Example: 3 Independent Apps

#### App 1: HomeBrews (Port 5001)

```bash
mkdir -p ~/apps/homebrews
cd ~/apps/homebrews
# ... copy template ...
cat > .env << EOF
APP_NAME=homebrews
PORT=5001
VERSION=latest
EOF
docker-compose up -d
```

#### App 2: Projects (Port 5002)

```bash
mkdir -p ~/apps/projects
cd ~/apps/projects
# ... copy template ...
cat > .env << EOF
APP_NAME=projects
PORT=5002
VERSION=latest
EOF
docker-compose up -d
```

#### App 3: Recipes (Port 5003)

```bash
mkdir -p ~/apps/recipes
cd ~/apps/recipes
# ... copy template ...
cat > .env << EOF
APP_NAME=recipes
PORT=5003
VERSION=latest
EOF
docker-compose up -d
```

### Bulk Operations Script

Create `~/apps/manage-all.sh`:

```bash
#!/bin/bash
# Manage all app instances

APPS_DIR=~/apps
ACTION=${1:-status}

for app in homebrews projects recipes; do
    echo "=== ${app} ==="
    cd ${APPS_DIR}/${app}
    
    case $ACTION in
        status)
            docker-compose ps
            ;;
        update)
            ./update.sh
            ;;
        backup)
            ./backup.sh
            ;;
        restart)
            docker-compose restart
            ;;
        logs)
            docker-compose logs --tail=20
            ;;
    esac
    echo ""
done
```

Usage:
```bash
chmod +x ~/apps/manage-all.sh
~/apps/manage-all.sh status   # Check all
~/apps/manage-all.sh update   # Update all
~/apps/manage-all.sh backup   # Backup all
```

---

## Advanced Scenarios

### Reverse Proxy with Caddy

Use domain names instead of ports:

```caddyfile
# /etc/caddy/Caddyfile

homebrews.example.com {
    reverse_proxy localhost:5001
}

projects.example.com {
    reverse_proxy localhost:5002
}

recipes.example.com {
    reverse_proxy localhost:5003
}
```

### Systemd Service

Auto-start on boot:

```bash
# Create service file
sudo tee /etc/systemd/system/template-homebrews.service << EOF
[Unit]
Description=Template Framework - HomeBrews
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/user/apps/homebrews
ExecStart=/usr/bin/docker-compose up -d
ExecStop=/usr/bin/docker-compose down

[Install]
WantedBy=multi-user.target
EOF

# Enable and start
sudo systemctl enable template-homebrews
sudo systemctl start template-homebrews
```

### Monitoring

Add to docker-compose.yml:

```yaml
services:
  app:
    # ... existing config ...
    labels:
      - "com.centurylinklabs.watchtower.enable=true"
      
  watchtower:
    image: containrrr/watchtower
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
    command: --interval 86400  # Check daily
```

### Remote Deployment

Deploy to remote server:

```bash
# Copy app directory
scp -r ~/apps/homebrews user@remote-server:~/apps/

# SSH and start
ssh user@remote-server
cd ~/apps/homebrews
docker-compose up -d
```

---

## Next Steps

- [Update Guide](UPDATE_GUIDE.md) - How to update apps
- [Backup Strategy](../guides/BACKUP_GUIDE.md) - Data protection
- [Troubleshooting](../guides/TROUBLESHOOTING.md) - Common issues

---

**Questions?** See the [Framework Usage Guide](FRAMEWORK_USAGE.md) or open an [issue](https://github.com/An0naman/template/issues).
