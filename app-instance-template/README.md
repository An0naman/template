# App Instance Template

This template provides everything you need to deploy a new instance of the Template Framework.

## Quick Start

### 1. Copy This Template

```bash
# Create your app directory
mkdir ~/apps/my-app
cd ~/apps/my-app

# Copy template files
cp /path/to/template/app-instance-template/* .
cp /path/to/template/app-instance-template/.env.example .env
cp /path/to/template/app-instance-template/.gitignore .
```

### 2. Configure Environment

Edit `.env` file:

```bash
# Edit with your settings
nano .env
```

Required settings:
- `APP_NAME`: Unique container name (e.g., "homebrews", "projects")
- `PORT`: External port (e.g., 5001, 5002, 5003)
- `VERSION`: Framework version to use (e.g., "latest", "v1.0.0")

Optional settings:
- `NETWORK_RANGE`: For ESP32 device discovery
- `GEMINI_API_KEY`: For AI features
- `NTFY_TOPIC`: For push notifications

### 3. Start Your App

```bash
# Pull latest framework image
docker-compose pull

# Start the app
docker-compose up -d

# View logs
docker-compose logs -f
```

### 4. Access Your App

**Local Access:**
- `http://localhost:PORT` (use the port from your `.env`)

**Network Access (from any device):**
- `http://YOUR_SERVER_IP:PORT`
- Works with CasaOS, mobile devices, or any computer on your network

**Example:**
```bash
# If your server IP is 192.168.1.100 and PORT=5001
http://192.168.1.100:5001
```

> **Note**: Apps use bridge networking by default, making them accessible from anywhere on your network and CasaOS compatible.

### 5. Configure via UI

1. Go to **Settings** → **System Configuration**
2. Set your project name and labels
3. Configure entry types and states
4. Choose your theme
5. Set up notifications (optional)

## File Structure

```
my-app/
├── docker-compose.yml    # Docker configuration
├── .env                  # Environment variables
├── .gitignore           # Git ignore rules
├── data/                # App data (auto-created)
│   ├── template.db      # SQLite database
│   └── uploads/         # File uploads
├── backup.sh            # Backup script
├── update.sh            # Update script
└── README.md            # This file
```

## Common Commands

### Start/Stop

```bash
# Start
docker-compose up -d

# Stop
docker-compose down

# Restart
docker-compose restart

# View logs
docker-compose logs -f
```

### Update Framework

```bash
# Run update script
./update.sh

# Or manually:
docker-compose pull
docker-compose up -d
```

### Backup

```bash
# Run backup script
./backup.sh

# Or manually:
tar -czf backup-$(date +%Y%m%d).tar.gz data/
```

### Restore

```bash
# Extract backup
tar -xzf backup-YYYYMMDD.tar.gz

# Restart app
docker-compose restart
```

## Updating

To update to the latest framework version:

```bash
./update.sh
```

This will:
1. Create a backup
2. Pull the latest image
3. Restart the container
4. Verify health

## Troubleshooting

### App Not Accessible from Network/CasaOS

The app uses **bridge mode** by default (CasaOS compatible). If you can't access it:

1. Check container is running: `docker-compose ps`
2. Verify port mapping: `docker ps | grep <APP_NAME>`
3. Check firewall: `sudo ufw allow <PORT>/tcp`
4. Test locally first: `curl http://localhost:<PORT>/api/health`

### Need Bluetooth Support?

If you need Bluetooth (Niimbot printers), edit `docker-compose.yml`:

```yaml
# Uncomment this line:
network_mode: host

# Comment out these lines:
# ports:
#   - "${PORT:-5001}:${PORT:-5001}"
```

Then restart:
```bash
docker-compose down
docker-compose up -d
```

**Note**: With host mode, the app won't be accessible from CasaOS web UI, only from localhost on the server.

### Port Already in Use

Change the `PORT` in `.env` and restart:

```bash
docker-compose down
# Edit .env
docker-compose up -d
```

### View Logs

```bash
docker-compose logs -f
```

### Reset Database

```bash
# Backup first!
./backup.sh

# Remove database
rm data/template.db

# Restart (will create new DB)
docker-compose restart
```

### Check Container Status

```bash
docker-compose ps
docker-compose logs
```

## Support

- Framework Repository: https://github.com/An0naman/template
- Documentation: https://github.com/An0naman/template/tree/main/docs
- Issues: https://github.com/An0naman/template/issues

## Version Information

This instance uses the Template Framework.

Check your version:
```bash
docker-compose exec app cat /app/VERSION
```

Check available versions:
```bash
# View all tags
docker images ghcr.io/an0naman/template
```
