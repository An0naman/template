# Watchtower Quick Reference

## 🚀 Quick Start

### New Apps (Already Included!)
```bash
cp -r app-instance-template ~/apps/myapp
cd ~/apps/myapp
cp .env.example .env
# Edit .env
docker-compose up -d
```

### Existing Apps (Add Watchtower)
```bash
./scripts/add_watchtower.sh ~/apps/myapp
```

## ⚙️ Configuration (.env)

```bash
# Update frequency
WATCHTOWER_POLL_INTERVAL=300  # 5 minutes (default)

# Notifications (optional)
WATCHTOWER_NOTIFICATIONS=shoutrrr
WATCHTOWER_NOTIFICATION_URL=ntfy://ntfy.sh/your-topic
```

## 📊 Monitoring

```bash
# View logs
docker logs -f myapp-watchtower

# Check status
docker ps | grep watchtower

# Force manual check
docker exec myapp-watchtower /watchtower --run-once
```

## 🔧 Common Configurations

### Development (Fast Updates)
```bash
VERSION=latest
WATCHTOWER_POLL_INTERVAL=300  # 5 minutes
```

### Production (Scheduled)
```bash
VERSION=v1  # Stable branch
# In docker-compose.yml:
- WATCHTOWER_SCHEDULE=0 0 2 * * *  # Daily at 2 AM
```

### Critical (Manual Only)
```bash
VERSION=v1.0.0  # Pinned version
# Remove watchtower service from docker-compose.yml
```

## 🔔 Notification Examples

### ntfy.sh (Easiest)
```bash
WATCHTOWER_NOTIFICATION_URL=ntfy://ntfy.sh/myapp-updates
```

### Email
```bash
WATCHTOWER_NOTIFICATION_URL=smtp://user:pass@smtp.gmail.com:587/?from=sender@gmail.com&to=recipient@example.com
```

### Discord
```bash
WATCHTOWER_NOTIFICATION_URL=discord://token@webhookid
```

### Multiple Services
```bash
WATCHTOWER_NOTIFICATION_URL=ntfy://ntfy.sh/topic discord://token@id
```

## 🐛 Troubleshooting

### Updates Not Working?
```bash
# 1. Check watchtower is running
docker ps | grep watchtower

# 2. Check logs
docker logs myapp-watchtower

# 3. Verify label
docker inspect myapp | grep watchtower

# 4. Manual update test
docker pull ghcr.io/an0naman/template:latest
docker-compose up -d
```

### Container Won't Start?
```bash
# 1. Check logs
docker logs myapp

# 2. Rollback
VERSION=v1.0.0  # Set in .env
docker-compose up -d
```

## 🎯 Update Flow

```
Commit → GitHub Actions → Published → Watchtower → Updated
(0 min)     (2-3 min)     (instant)   (5-10 min)   (done!)
```

**Total: 5-10 minutes** from commit to all apps updated! 🚀

## 📚 Full Documentation

- **[AUTO_UPDATE.md](docs/framework/AUTO_UPDATE.md)** - Complete guide
- **[WATCHTOWER_IMPLEMENTATION_COMPLETE.md](WATCHTOWER_IMPLEMENTATION_COMPLETE.md)** - Implementation summary

## 🎉 That's It!

Commit your code and watch it automatically deploy to all your apps!
