# Framework Usage Guide

How to use this repository as a framework/template for creating multiple independent applications.

## Concept

This repository serves as a **framework** that can be:
1. **Built into a Docker image** (published to registry)
2. **Reused by multiple apps** (each with separate data)
3. **Updated centrally** (all apps get improvements)

## Architecture

```
┌─────────────────────────────────────┐
│  FRAMEWORK (this repo)              │
│  ┌───────────────────────────────┐  │
│  │ Docker Image: template:latest │  │
│  │ - Flask application           │  │
│  │ - APIs & routes               │  │
│  │ - Templates & UI              │  │
│  │ - Database schema             │  │
│  └───────────────────────────────┘  │
└─────────────────────────────────────┘
              ↓
    ┌─────────┴─────────┐
    ↓                   ↓
┌──────────┐      ┌──────────┐
│  App 1   │      │  App 2   │
│ HomeBrews│      │ Projects │
├──────────┤      ├──────────┤
│ Port 5001│      │ Port 5002│
│ data/db  │      │ data/db  │
│ uploads/ │      │ uploads/ │
└──────────┘      └──────────┘
```

## Data Isolation

### What Each App Has Separately ✅

**Complete Isolation**:
- SQLite database file (`template.db`)
- User entries, notes, relationships
- System configuration (project name, labels, etc.)
- Uploaded files (logos, attachments)
- Notification rules
- Environment settings (port, API keys)

### What All Apps Share ✅

**From Framework Image**:
- Application code (Flask, APIs, business logic)
- HTML templates and UI
- JavaScript and CSS
- Database schema/migrations
- Python dependencies

---

## Setup Instructions

### Step 1: Publish Framework Image

From this repository:

```bash
# Build Docker image
docker build -t ghcr.io/an0naman/template:latest .

# Push to GitHub Container Registry
docker push ghcr.io/an0naman/template:latest

# Tag specific version for stability
docker tag ghcr.io/an0naman/template:latest ghcr.io/an0naman/template:v1.0.0
docker push ghcr.io/an0naman/template:v1.0.0
```

**Alternative**: Use Docker Hub instead of GHCR:
```bash
docker build -t an0naman/template:latest .
docker push an0naman/template:latest
```

### Step 2: Create App Instance

For each new app:

```bash
# Create directory
mkdir ~/apps/homebrews
cd ~/apps/homebrews

# Create docker-compose.yml
cat > docker-compose.yml << 'EOF'
version: '3.8'
services:
  app:
    image: ghcr.io/an0naman/template:latest
    container_name: homebrews
    restart: always
    ports:
      - "5001:5001"
    volumes:
      - ./data:/app/data
    environment:
      - FLASK_APP=run.py
      - PORT=5001
      - NETWORK_RANGE=192.168.68.0/24
EOF

# Create data directory
mkdir data

# Start app
docker-compose up -d
```

### Step 3: Configure App

1. **Access**: Open `http://localhost:5001`
2. **Settings**: Go to Settings → System Configuration
3. **Configure**:
   - Project name: "HomeBrews"
   - Entry types: Add "Beer", "Equipment", etc.
   - States: "Brewing", "Fermenting", "Bottled", "Consumed"
   - Theme: Choose colors
4. **Done**: Your app is ready!

---

## Multi-App Example

### App 1: HomeBrews (Port 5001)

```yaml
# ~/apps/homebrews/docker-compose.yml
version: '3.8'
services:
  homebrews:
    image: ghcr.io/an0naman/template:latest
    container_name: homebrews
    ports:
      - "5001:5001"
    volumes:
      - ./data:/app/data
    environment:
      - PORT=5001
```

**Data**: `~/apps/homebrews/data/template.db`
**URL**: `http://localhost:5001`

### App 2: Projects (Port 5002)

```yaml
# ~/apps/projects/docker-compose.yml
version: '3.8'
services:
  projects:
    image: ghcr.io/an0naman/template:latest
    container_name: projects
    ports:
      - "5002:5001"  # External:Internal
    volumes:
      - ./data:/app/data
    environment:
      - PORT=5001
```

**Data**: `~/apps/projects/data/template.db`
**URL**: `http://localhost:5002`

### App 3: Recipes (Port 5003)

```yaml
# ~/apps/recipes/docker-compose.yml
version: '3.8'
services:
  recipes:
    image: ghcr.io/an0naman/template:latest
    container_name: recipes
    ports:
      - "5003:5001"
    volumes:
      - ./data:/app/data
    environment:
      - PORT=5001
```

**Data**: `~/apps/recipes/data/template.db`
**URL**: `http://localhost:5003`

---

## Updating Framework

### When You Improve the Framework

From framework repository:

```bash
# Make changes to code
git add .
git commit -m "Add new feature"
git push

# Build and push new image
docker build -t ghcr.io/an0naman/template:latest .
docker push ghcr.io/an0naman/template:latest

# Optional: Tag version
docker tag ghcr.io/an0naman/template:latest ghcr.io/an0naman/template:v1.1.0
docker push ghcr.io/an0naman/template:v1.1.0
```

### Update All Apps

Each app pulls the latest image:

```bash
# App 1
cd ~/apps/homebrews
docker-compose pull
docker-compose up -d

# App 2
cd ~/apps/projects
docker-compose pull
docker-compose up -d

# App 3
cd ~/apps/recipes
docker-compose pull
docker-compose up -d
```

**All apps now have the new features!** 🎉

---

## Version Pinning

### For Production Stability

Pin specific versions instead of `latest`:

```yaml
# docker-compose.yml
services:
  app:
    image: ghcr.io/an0naman/template:v1.0.0  # Pinned version
```

**Benefits**:
- Predictable updates
- Test before upgrading
- Rollback if issues

**Upgrade Process**:
```bash
# Test new version in dev
docker pull ghcr.io/an0naman/template:v1.1.0

# Update docker-compose.yml version
# Then restart
docker-compose up -d
```

---

## Environment Variables

### Common Variables

```yaml
environment:
  # Required
  - FLASK_APP=run.py
  - PORT=5001
  
  # Optional
  - DEBUG=false
  - NETWORK_RANGE=192.168.1.0/24
  - GEMINI_API_KEY=your-api-key
  - NTFY_SERVER_URL=https://ntfy.sh
  - NTFY_TOPIC=myapp-notifications
  - SECRET_KEY=change-in-production
```

### Per-App Configuration

Most settings should be configured via **Settings UI**, not environment variables:
- Project name
- Entry types
- Theme colors
- Label settings
- Notification rules

**Why**: Settings in database persist across container restarts and are backed up with data.

---

## Backup & Restore

### Backup App Data

```bash
# Backup database and uploads
cd ~/apps/homebrews
tar -czf backup-$(date +%Y%m%d).tar.gz data/

# Store backup safely
mv backup-*.tar.gz ~/backups/
```

### Restore App Data

```bash
# Extract backup
cd ~/apps/homebrews
tar -xzf ~/backups/backup-20250129.tar.gz

# Restart app
docker-compose restart
```

### Automated Backups

Add cron job:
```bash
# Edit crontab
crontab -e

# Add daily backup at 2 AM
0 2 * * * cd ~/apps/homebrews && tar -czf ~/backups/homebrews-$(date +\%Y\%m\%d).tar.gz data/
```

---

## Migration & Cloning

### Clone Existing App

```bash
# Copy existing app
cp -r ~/apps/homebrews ~/apps/homebrews-2

# Change port in docker-compose.yml
cd ~/apps/homebrews-2
sed -i 's/5001:5001/5004:5001/' docker-compose.yml

# Start clone
docker-compose up -d
```

### Migrate Between Servers

```bash
# On source server
cd ~/apps/homebrews
tar -czf app-export.tar.gz docker-compose.yml data/

# Transfer to new server
scp app-export.tar.gz user@newserver:~/

# On new server
cd ~/apps
mkdir homebrews
cd homebrews
tar -xzf ~/app-export.tar.gz
docker-compose up -d
```

---

## Advanced Scenarios

### Shared Database (Advanced)

Multiple apps sharing one PostgreSQL database but separate schemas:

```yaml
# docker-compose.yml
version: '3.8'
services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_PASSWORD: secure_password
    volumes:
      - postgres_data:/var/lib/postgresql/data

  app1:
    image: ghcr.io/an0naman/template:latest
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres/app1_db
    depends_on:
      - postgres

  app2:
    image: ghcr.io/an0naman/template:latest
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres/app2_db
    depends_on:
      - postgres
```

**Note**: Requires code changes to support PostgreSQL (currently SQLite only).

### Reverse Proxy

Use Caddy/Nginx for domain-based routing:

```caddy
# Caddyfile
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

### Development Workflow

Override image with local code:

```yaml
# docker-compose.override.yml (development)
version: '3.8'
services:
  app:
    build: /path/to/framework/repo
    volumes:
      - /path/to/framework/repo/app:/app/app
    environment:
      - DEBUG=true
```

Run with override:
```bash
docker-compose -f docker-compose.yml -f docker-compose.override.yml up
```

---

## Best Practices

### 1. Version Management
- Tag framework releases semantically (v1.0.0, v1.1.0)
- Use `latest` for dev, pinned versions for production
- Document breaking changes in CHANGELOG.md

### 2. Data Management
- Backup data regularly (daily recommended)
- Store backups separately from app servers
- Test restore procedure

### 3. Configuration
- Use Settings UI for app-specific config
- Use environment variables for infrastructure (ports, keys)
- Document required environment variables

### 4. Security
- Change SECRET_KEY in production
- Use strong passwords for API keys
- Don't commit `.env` files to git
- Use HTTPS in production (reverse proxy)

### 5. Monitoring
- Check logs: `docker-compose logs -f`
- Monitor disk usage of data volumes
- Set up notifications for errors

---

## Troubleshooting

### App Won't Start

```bash
# Check logs
docker-compose logs

# Check if port is already in use
netstat -tulpn | grep 5001

# Verify data directory exists
ls -la data/
```

### Database Errors

```bash
# Check database file
file data/template.db

# Backup and reinitialize
mv data/template.db data/template.db.backup
docker-compose restart  # App will create new DB
```

### Updates Not Appearing

```bash
# Force pull latest image
docker-compose pull --ignore-pull-failures

# Remove old container
docker-compose down
docker-compose up -d

# Check image version
docker images | grep template
```

---

## App Instance Template

Create this starter template for quick app setup:

```
app-instance-template/
├── docker-compose.yml
├── .env.example
├── .gitignore
├── data/
│   └── .gitkeep
└── README.md
```

**docker-compose.yml**:
```yaml
version: '3.8'
services:
  app:
    image: ghcr.io/an0naman/template:${VERSION:-latest}
    container_name: ${APP_NAME:-myapp}
    restart: always
    ports:
      - "${PORT:-5001}:5001"
    volumes:
      - ./data:/app/data
    environment:
      - FLASK_APP=run.py
      - NETWORK_RANGE=${NETWORK_RANGE:-192.168.1.0/24}
      - GEMINI_API_KEY=${GEMINI_API_KEY}
```

**.env.example**:
```bash
APP_NAME=myapp
PORT=5001
VERSION=latest
NETWORK_RANGE=192.168.1.0/24
GEMINI_API_KEY=
```

---

## Summary

✅ **Framework is ready** - All reference data in SQL
✅ **Easy to deploy** - Simple docker-compose per app
✅ **Isolated data** - Each app has separate database
✅ **Centralized updates** - Improve once, update all
✅ **Scalable** - Spin up unlimited apps

**Next steps**:
1. Publish framework Docker image
2. Create app-instance-template repository
3. Document app-specific configuration
4. Set up automated backups

---

## Related Documentation

- [Auto-Update Guide](AUTO_UPDATE.md) - Automatic updates with Watchtower
- [Deployment Guide](DEPLOYMENT_GUIDE.md) - Production deployment
- [Update Guide](UPDATE_GUIDE.md) - Manual update procedures
- [Quick Start](QUICK_START.md) - 5-minute setup guide
- [Installation Guide](../setup/INSTALLATION.md) - Initial framework setup
- [Architecture](../development/ARCHITECTURE.md) - Technical details
- [API Reference](../guides/API_REFERENCE.md) - Integration options
