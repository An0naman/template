# Automatic Updates with Watchtower

This guide explains how the automatic update system works and how to configure it for your app instances.

## 📋 Table of Contents

- [Overview](#overview)
- [How It Works](#how-it-works)
- [Configuration](#configuration)
- [Notification Setup](#notification-setup)
- [Monitoring Updates](#monitoring-updates)
- [Troubleshooting](#troubleshooting)
- [Advanced Configuration](#advanced-configuration)

## Overview

Every app instance includes [Watchtower](https://containrrr.github.io/watchtower/), a container that automatically monitors and updates your Docker containers when new framework versions are released.

### Key Features

- ✅ **Fully Automatic**: Updates happen without any manual intervention
- ✅ **Fast**: Changes appear 5-10 minutes after framework updates
- ✅ **Safe**: Health checks ensure new versions work before completing update
- ✅ **Clean**: Old images are automatically removed to save disk space
- ✅ **Configurable**: Adjust update frequency and notification preferences
- ✅ **Selective**: Only updates containers you explicitly enable

## How It Works

```
┌──────────────────────────────────────────────────────────────┐
│ 1. Framework Maintainer Commits Code                         │
│    git push origin main                                       │
└────────────────────────────┬─────────────────────────────────┘
                             ↓
┌──────────────────────────────────────────────────────────────┐
│ 2. GitHub Actions Build & Publish (2-3 minutes)              │
│    - Builds Docker image                                      │
│    - Runs tests                                               │
│    - Publishes to ghcr.io/an0naman/template:latest          │
└────────────────────────────┬─────────────────────────────────┘
                             ↓
┌──────────────────────────────────────────────────────────────┐
│ 3. Watchtower Detects New Image (every 5 minutes by default) │
│    - Polls GitHub Container Registry                          │
│    - Compares image digest with running container             │
│    - Identifies update is available                           │
└────────────────────────────┬─────────────────────────────────┘
                             ↓
┌──────────────────────────────────────────────────────────────┐
│ 4. Automatic Update Process                                  │
│    - Pulls new image from registry                            │
│    - Stops old container gracefully                           │
│    - Starts new container with same configuration             │
│    - Waits for health check to pass                           │
│    - Removes old image (cleanup)                              │
│    - Sends notification (if configured)                       │
└──────────────────────────────────────────────────────────────┘
```

**Total Time**: ~5-10 minutes from framework commit to your app updated!

## Configuration

### Basic Settings

Edit your app's `.env` file:

```bash
# How often to check for updates (in seconds)
WATCHTOWER_POLL_INTERVAL=300  # Default: 5 minutes
```

### Update Frequency Options

```bash
# Very Aggressive (1 minute)
WATCHTOWER_POLL_INTERVAL=60

# Default (5 minutes) - Recommended
WATCHTOWER_POLL_INTERVAL=300

# Conservative (1 hour)
WATCHTOWER_POLL_INTERVAL=3600

# Daily (24 hours)
WATCHTOWER_POLL_INTERVAL=86400
```

### Scheduled Updates Only

If you prefer updates at specific times (e.g., 2 AM daily), modify `docker-compose.yml`:

```yaml
watchtower:
  environment:
    # Remove or comment out WATCHTOWER_POLL_INTERVAL
    # Add schedule in cron format
    - WATCHTOWER_SCHEDULE=0 0 2 * * *  # Daily at 2:00 AM
```

Cron format examples:
```bash
0 0 2 * * *      # Daily at 2:00 AM
0 0 2 * * 0      # Weekly on Sunday at 2:00 AM
0 0 2 1 * *      # Monthly on 1st at 2:00 AM
0 */6 * * *      # Every 6 hours
```

## Notification Setup

Get notified when updates happen!

### Using ntfy.sh (Easiest)

1. Choose a unique topic (e.g., `myapp-updates-abc123`)
2. Edit `.env`:

```bash
WATCHTOWER_NOTIFICATIONS=shoutrrr
WATCHTOWER_NOTIFICATION_URL=ntfy://ntfy.sh/myapp-updates-abc123
```

3. Subscribe on your phone:
   - Install [ntfy app](https://ntfy.sh) (iOS/Android)
   - Subscribe to your topic

### Using Email

```bash
WATCHTOWER_NOTIFICATIONS=shoutrrr
WATCHTOWER_NOTIFICATION_URL=smtp://username:password@smtp.gmail.com:587/?from=sender@gmail.com&to=recipient@example.com
```

### Using Discord

1. Create a webhook in your Discord server
2. Get webhook URL: `https://discord.com/api/webhooks/{id}/{token}`
3. Edit `.env`:

```bash
WATCHTOWER_NOTIFICATIONS=shoutrrr
WATCHTOWER_NOTIFICATION_URL=discord://{token}@{id}
```

### Using Slack

```bash
WATCHTOWER_NOTIFICATIONS=shoutrrr
WATCHTOWER_NOTIFICATION_URL=slack://token@channel
```

### Multiple Notification Services

Separate URLs with spaces:

```bash
WATCHTOWER_NOTIFICATION_URL=ntfy://ntfy.sh/topic discord://token@id
```

## Monitoring Updates

### View Watchtower Logs

```bash
# Real-time logs
docker logs -f myapp-watchtower

# Last 50 lines
docker logs --tail 50 myapp-watchtower

# Follow logs with timestamps
docker logs -f --timestamps myapp-watchtower
```

### Check When Container Was Updated

```bash
# See container creation time (when last updated)
docker inspect myapp | grep -A2 "Created"

# See image details
docker inspect myapp | grep -A5 "Image"
```

### List All Watchtower Containers

```bash
docker ps | grep watchtower
```

### Manual Update Check

Force watchtower to check immediately:

```bash
docker exec myapp-watchtower /watchtower --run-once
```

## Troubleshooting

### Updates Not Happening

**Check if watchtower is running:**
```bash
docker ps | grep watchtower
```

**Check watchtower logs for errors:**
```bash
docker logs myapp-watchtower
```

**Verify the app has the watchtower label:**
```bash
docker inspect myapp | grep watchtower
# Should show: "com.centurylinklabs.watchtower.enable": "true"
```

**Manually check for new images:**
```bash
docker pull ghcr.io/an0naman/template:latest
docker-compose up -d
```

### Update Failed / Container Won't Start

**View logs of the failed container:**
```bash
docker logs myapp
```

**Rollback to previous version:**
```bash
# Stop current container
docker-compose down

# Manually pull a specific older version
docker pull ghcr.io/an0naman/template:v1.0.0

# Edit .env to pin to that version
VERSION=v1.0.0

# Restart
docker-compose up -d
```

**Check health status:**
```bash
docker ps --format "table {{.Names}}\t{{.Status}}"
```

### Notifications Not Working

**Test the notification URL:**
```bash
# For ntfy.sh
curl -d "Test notification" ntfy.sh/your-topic

# Check watchtower logs for notification errors
docker logs myapp-watchtower | grep -i notification
```

### Too Many Notifications

Increase poll interval or use scheduled updates:

```bash
# Check every hour instead of every 5 minutes
WATCHTOWER_POLL_INTERVAL=3600
```

## Advanced Configuration

### Disable Auto-Updates for Specific App

Remove the label from `docker-compose.yml`:

```yaml
services:
  app:
    # Remove or comment out:
    # labels:
    #   - "com.centurylinklabs.watchtower.enable=true"
```

Then restart:
```bash
docker-compose up -d
```

### Update Multiple Apps Together

If you have multiple related apps, create a shared watchtower:

**Create `~/apps/shared-watchtower/docker-compose.yml`:**

```yaml
version: '3.8'

services:
  watchtower:
    image: containrrr/watchtower
    container_name: shared-watchtower
    restart: always
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
    environment:
      - WATCHTOWER_POLL_INTERVAL=300
      - WATCHTOWER_CLEANUP=true
      - WATCHTOWER_LABEL_ENABLE=true
      - WATCHTOWER_NOTIFICATIONS=shoutrrr
      - WATCHTOWER_NOTIFICATION_URL=ntfy://ntfy.sh/all-apps-updates
    command: --label-enable
```

Then remove individual watchtower services from each app's `docker-compose.yml` (but keep the labels).

### Pre/Post Update Scripts

Add lifecycle hooks in `docker-compose.yml`:

```yaml
services:
  app:
    labels:
      - "com.centurylinklabs.watchtower.enable=true"
      - "com.centurylinklabs.watchtower.lifecycle.pre-update=/app/scripts/backup.sh"
      - "com.centurylinklabs.watchtower.lifecycle.post-update=/app/scripts/verify.sh"
```

### Stop Updates During Maintenance Window

Temporarily disable watchtower:

```bash
# Pause watchtower
docker pause myapp-watchtower

# Resume later
docker unpause myapp-watchtower
```

### Resource Limits for Watchtower

Add to `docker-compose.yml` if needed:

```yaml
watchtower:
  deploy:
    resources:
      limits:
        cpus: '0.5'
        memory: 256M
```

## Best Practices

### 1. **Enable Notifications**
Stay informed when updates happen, especially for production apps.

### 2. **Monitor Logs Regularly**
Check watchtower logs weekly to ensure updates are working smoothly.

### 3. **Test Updates in Development First**
Run a dev instance with `VERSION=latest` to catch issues before production.

### 4. **Pin Production to Stable Versions**
For critical apps, use `VERSION=v1` or `VERSION=v1.0.0` instead of `latest`.

### 5. **Backup Before Major Updates**
Watchtower handles updates automatically, but maintain regular backups:

```bash
# Backup script
tar -czf backup-$(date +%Y%m%d).tar.gz ~/apps/myapp/data/
```

### 6. **Use Scheduled Updates for Production**
Consider using scheduled updates (e.g., 2 AM) instead of continuous polling for production apps.

### 7. **Set Appropriate Poll Intervals**
- Development: 300 seconds (5 minutes)
- Staging: 3600 seconds (1 hour)
- Production: Scheduled (daily at off-peak hours)

## Security Considerations

### Watchtower Access

Watchtower needs access to the Docker socket (`/var/run/docker.sock`). This is standard practice but means:

- Watchtower can manage any container on the host
- Only run watchtower on trusted systems
- Consider using labels to restrict which containers it can update

### Image Verification

Watchtower verifies images by digest, ensuring:
- You get the exact image from the registry
- No man-in-the-middle tampering
- Images match what the maintainer published

### Network Security

Watchtower only:
- Pulls images (read-only access to registry)
- Manages local containers (no external commands)
- Sends notifications (if configured)

## Disabling Auto-Updates

If you prefer manual updates:

### Option 1: Remove Watchtower Entirely

Edit `docker-compose.yml` and remove the entire `watchtower` service, then:

```bash
docker-compose up -d
```

### Option 2: Stop Watchtower

```bash
docker stop myapp-watchtower
docker rm myapp-watchtower
```

### Option 3: Set Very Long Poll Interval

```bash
# Check once per week
WATCHTOWER_POLL_INTERVAL=604800
```

Then manually update when ready:

```bash
cd ~/apps/myapp
docker-compose pull
docker-compose up -d
```

## Related Documentation

- [Deployment Guide](DEPLOYMENT_GUIDE.md) - Initial setup
- [Update Guide](UPDATE_GUIDE.md) - Manual update procedures
- [Framework Usage](FRAMEWORK_USAGE.md) - Complete framework documentation
- [Watchtower Documentation](https://containrrr.github.io/watchtower/) - Official docs

## Support

If you encounter issues with automatic updates:

1. Check the [Troubleshooting](#troubleshooting) section
2. Review watchtower logs: `docker logs myapp-watchtower`
3. Check framework issues: https://github.com/An0naman/template/issues
4. Refer to [Watchtower docs](https://containrrr.github.io/watchtower/)
