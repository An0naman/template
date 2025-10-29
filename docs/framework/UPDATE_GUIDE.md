# Framework Update Guide

Complete guide for updating the framework and all app instances.

---

## Table of Contents

1. [Update Workflow](#update-workflow)
2. [Updating App Instances](#updating-app-instances)
3. [Version Management](#version-management)
4. [Rollback Procedures](#rollback-procedures)
5. [Bulk Updates](#bulk-updates)

---

## Update Workflow

### Framework Developer Workflow

When you improve the framework:

```
┌────────────────────────────────────────┐
│ 1. Develop Feature                     │
│    - Make changes in framework repo    │
│    - Test locally                      │
└────────────────┬───────────────────────┘
                 ↓
┌────────────────────────────────────────┐
│ 2. Commit & Push                       │
│    git add .                           │
│    git commit -m "Add feature"         │
│    git push origin main                │
└────────────────┬───────────────────────┘
                 ↓
┌────────────────────────────────────────┐
│ 3. Automatic Build (GitHub Actions)    │
│    - Builds Docker image               │
│    - Pushes to GHCR                    │
│    - Tags as :latest                   │
└────────────────┬───────────────────────┘
                 ↓
┌────────────────────────────────────────┐
│ 4. Create Release (optional)           │
│    git tag v1.2.0                      │
│    git push origin v1.2.0              │
│    - Creates versioned tags            │
│    - Generates changelog               │
└────────────────┬───────────────────────┘
                 ↓
┌────────────────────────────────────────┐
│ 5. App Instances Pull Update           │
│    Each app runs: ./update.sh          │
│    - Automatic backup                  │
│    - Pull new image                    │
│    - Restart containers                │
└────────────────────────────────────────┘
```

### Step-by-Step Framework Update

#### 1. Make Changes

```bash
cd /path/to/template

# Make your changes
vim app/routes/main_routes.py

# Test locally
python run.py
```

#### 2. Commit and Push

```bash
# Commit changes
git add .
git commit -m "Add feature: XYZ"
git push origin main
```

#### 3. Monitor Build

```bash
# View GitHub Actions
# https://github.com/An0naman/template/actions

# Or check locally after a minute
docker pull ghcr.io/an0naman/template:latest
```

#### 4. Create Release (for stable versions)

```bash
# Tag release
git tag -a v1.2.0 -m "Release 1.2.0: Added XYZ feature"
git push origin v1.2.0

# This creates:
# - ghcr.io/an0naman/template:v1.2.0
# - ghcr.io/an0naman/template:v1.2
# - ghcr.io/an0naman/template:v1
# - GitHub Release with changelog
```

---

## Updating App Instances

### Automated Update Script

Each app instance has an `update.sh` script:

```bash
cd ~/apps/homebrews
./update.sh
```

This script:
1. ✅ Creates timestamped backup
2. ✅ Pulls latest framework image
3. ✅ Stops current container
4. ✅ Starts new container
5. ✅ Waits for health check
6. ✅ Verifies update success
7. ✅ Rolls back on failure

### Manual Update

If you prefer manual control:

```bash
cd ~/apps/homebrews

# 1. Backup first
./backup.sh

# 2. Pull new image
docker-compose pull

# 3. Restart with new image
docker-compose down
docker-compose up -d

# 4. Check logs
docker-compose logs -f

# 5. Verify version
docker-compose exec app cat /app/VERSION
```

### Update Single App

```bash
cd ~/apps/homebrews
./update.sh
```

Output:
```
Template Framework Update Script
==================================

App Name: homebrews
Target Version: latest

Step 1: Creating backup...
✓ Backup created: backup-20251029-143022.tar.gz

Step 2: Pulling latest framework image...
✓ Image pulled

Step 3: Stopping container...
✓ Container stopped

Step 4: Starting updated container...
✓ Container started

Step 5: Running database migrations...
  Running migration: add_entry_level_template_sharing.py
    ↳ Applied successfully
✓ Applied 1 new migration(s)

Step 6: Waiting for app to be healthy...
✓ Container is running

Step 7: Verifying update...
Running version: v1.2.0

==================================
✓ Update completed successfully!
==================================

Backup saved to: backup-20251029-143022.tar.gz
```

### Migration Handling During Updates

The update script **automatically handles database migrations**:

1. **Before Update:** Creates timestamped backup
2. **After Image Pull:** New container starts with updated code
3. **Migration Phase:** Automatically runs all pending migrations
   - Detects all `.py` files in `/app/migrations/`
   - Executes each migration in order
   - Skips already-applied migrations
   - Reports success/failure for each
4. **Health Check:** Verifies app is running correctly
5. **Completion:** Reports total migrations applied

**Migration Output Examples:**

```
Step 5: Running database migrations...
  Running migration: add_entry_level_template_sharing.py
    ↳ Applied successfully
  Running migration: add_user_preferences_table.py
    ↳ Already applied
✓ Applied 1 new migration(s)
```

If no migrations are needed:
```
Step 5: Running database migrations...
✓ No new migrations to apply
```

**What if a migration fails?**

The update script will:
1. Show the error message from the migration
2. Continue with update (container runs old schema)
3. Display warning in summary
4. Provide manual migration instructions

You can then:
- Review the error and fix manually
- Restore backup if needed: `tar -xzf backup-*.tar.gz`
- Run migrations manually: `./run-migrations.sh`

### Manual Migration After Update

If you need to run migrations separately:

```bash
cd ~/apps/homebrews

# Run all pending migrations
./run-migrations.sh

# Output:
# Database Migration Runner
# ==========================
# 
# App Name: homebrews
# 
# Step 1: Creating database backup...
# ✓ Backup created: migration-backups/db-before-migration-20251029-150000.tar.gz
# 
# Step 2: Running database migrations...
# 
# [1] add_entry_level_template_sharing.py
#     ↳ Applied successfully
# 
# ==========================
# Migration Summary
# ==========================
# Total migrations found: 1
# Applied: 1
# Skipped: 0
# 
# ✓ All migrations completed successfully
```

---

## Version Management

### Using Latest (Rolling Release)

**In `.env`:**
```bash
VERSION=latest
```

**Pros:**
- Always get newest features
- Automatic bug fixes
- Simple management

**Cons:**
- Potential breaking changes
- Less predictable
- Need to watch for issues

**Best for:**
- Development environments
- Personal projects
- Apps you actively maintain

### Using Pinned Versions (Stable)

**In `.env`:**
```bash
VERSION=v1.2.0  # Specific version
# or
VERSION=v1.2    # Latest v1.2.x
# or
VERSION=v1      # Latest v1.x.x
```

**Pros:**
- Predictable behavior
- No surprise changes
- Controlled updates

**Cons:**
- Manual version bumps needed
- May miss bug fixes
- More maintenance

**Best for:**
- Production deployments
- Critical applications
- Shared infrastructure

### Version Update Strategy

#### Conservative Approach

```bash
# Pin to major.minor
VERSION=v1.2

# Updates automatically to v1.2.x patches
# Manual bump for v1.3.0
```

#### Balanced Approach

```bash
# Pin to major version
VERSION=v1

# Updates to v1.x.x automatically
# Manual bump for v2.0.0
```

#### Aggressive Approach

```bash
# Use latest
VERSION=latest

# Updates on every push
# Review changelog regularly
```

### Checking Available Versions

```bash
# List all available tags
docker pull ghcr.io/an0naman/template --all-tags

# Or check GitHub releases
# https://github.com/An0naman/template/releases

# Or use GitHub API
curl -s https://api.github.com/repos/An0naman/template/tags | \
  jq -r '.[].name'
```

### Testing New Versions

Before updating production:

```bash
# Create test instance
mkdir -p ~/apps/homebrews-test
cd ~/apps/homebrews-test

# Copy production config
cp ~/apps/homebrews/docker-compose.yml .
cp ~/apps/homebrews/.env .

# Change port and name
sed -i 's/PORT=5001/PORT=9001/' .env
sed -i 's/APP_NAME=homebrews/APP_NAME=homebrews-test/' .env

# Set new version
sed -i 's/VERSION=.*/VERSION=v1.3.0/' .env

# Start test instance
docker-compose up -d

# Test functionality
# ...

# If good, update production
cd ~/apps/homebrews
sed -i 's/VERSION=.*/VERSION=v1.3.0/' .env
./update.sh
```

---

## Rollback Procedures

### Automatic Rollback

The `update.sh` script automatically rolls back if the new container fails to start.

### Manual Rollback

#### Option 1: Restore from Backup

```bash
cd ~/apps/homebrews

# Stop current container
docker-compose down

# List backups
ls -lh backup-*.tar.gz

# Restore specific backup
tar -xzf backup-20251029-143022.tar.gz

# Restart
docker-compose up -d
```

**Note:** This restores both the database AND rolls back any migrations that were applied during the failed update.

#### Option 2: Restore Database Only (Keep Code)

If the code update is fine but a migration failed:

```bash
cd ~/apps/homebrews

# Stop app
docker-compose down

# List migration backups
ls -lh migration-backups/

# Restore database from before migration
tar -xzf migration-backups/db-before-migration-20251029-150000.tar.gz

# Restart with new code but old database schema
docker-compose up -d
```

**Warning:** This may cause errors if new code expects new schema. Only use if you know the specific migration that failed.

#### Option 3: Use Previous Image Version

```bash
cd ~/apps/homebrews

# Change to previous version
sed -i 's/VERSION=.*/VERSION=v1.1.0/' .env

# Pull old image and restart
docker-compose pull
docker-compose down
docker-compose up -d
```

This rolls back both code AND migrations (since old image doesn't have new migrations).

#### Option 4: Restore Specific Database

```bash
# Stop app
docker-compose down

# Backup current database (just in case)
cp data/homebrew.db data/homebrew.db.rollback-$(date +%Y%m%d)

# Restore from full backup
tar -xzf backup-20251029-143022.tar.gz data/homebrew.db

# Restart
docker-compose up -d
```

### Rollback Decision Matrix

| Scenario | Solution | Command |
|----------|----------|---------|
| Container won't start | Full restore from backup | `tar -xzf backup-*.tar.gz && docker-compose up -d` |
| Migration failed | Restore DB from migration-backup | `tar -xzf migration-backups/db-*.tar.gz` |
| New code has bugs | Revert to old version | Change `VERSION` in `.env` |
| Database corrupted | Restore full backup | `tar -xzf backup-*.tar.gz` |
| Need to test rollback | Create test instance first | Use different port/name |

### Emergency Rollback

If app won't start at all:

```bash
# Stop everything
docker-compose down

# Move broken data aside (don't delete yet!)
mv data data.broken-$(date +%Y%m%d)

# Restore from most recent backup
tar -xzf backup-20251029-143022.tar.gz

# Use previous framework version
sed -i 's/VERSION=.*/VERSION=v1.1.0/' .env

# Start fresh
docker-compose pull
docker-compose up -d

# Verify it works
docker-compose logs -f

# If successful, you can later delete data.broken-*
# If still broken, restore older backup
```

---

## Bulk Updates

### Update All Apps

Create `~/apps/update-all.sh`:

```bash
#!/bin/bash
# Update all app instances

APPS_DIR=~/apps
APPS=("homebrews" "projects" "recipes")

echo "Updating all Template Framework apps..."
echo "========================================"
echo ""

for app in "${APPS[@]}"; do
    echo "Updating: ${app}"
    cd "${APPS_DIR}/${app}"
    
    if [ -f "update.sh" ]; then
        ./update.sh
    else
        echo "Error: update.sh not found in ${app}"
    fi
    
    echo ""
    echo "---"
    echo ""
done

echo "All updates completed!"
```

Usage:
```bash
chmod +x ~/apps/update-all.sh
~/apps/update-all.sh
```

### Staggered Updates

Update one at a time with verification:

```bash
#!/bin/bash
# Staggered update with verification

APPS=("homebrews" "projects" "recipes")

for app in "${APPS[@]}"; do
    echo "Updating: ${app}"
    cd ~/apps/${app}
    ./update.sh
    
    echo ""
    echo "Verify ${app} is working correctly"
    echo "Press Enter to continue to next app, or Ctrl+C to stop"
    read
done
```

### Conditional Updates

Only update if new version available:

```bash
#!/bin/bash
# Check and update if newer version exists

cd ~/apps/homebrews

# Get current version
CURRENT=$(docker-compose exec -T app cat /app/VERSION 2>/dev/null)

# Get latest version
LATEST=$(docker run --rm ghcr.io/an0naman/template:latest cat /app/VERSION)

if [ "${CURRENT}" != "${LATEST}" ]; then
    echo "Update available: ${CURRENT} → ${LATEST}"
    ./update.sh
else
    echo "Already up to date: ${CURRENT}"
fi
```

---

## Best Practices

### 1. Always Backup Before Updates

```bash
# Automated in update.sh, but can do manually:
./backup.sh
./update.sh
```

### 2. Test Updates in Non-Production First

```bash
# Update test instance first
cd ~/apps/homebrews-test
./update.sh

# Verify functionality
# ...

# Then update production
cd ~/apps/homebrews
./update.sh
```

### 3. Monitor Logs During Updates

```bash
# In another terminal
docker-compose logs -f
```

### 4. Keep Backups

```bash
# Backups are kept in backups/ directory
# Last 10 are kept automatically
# Archive important ones elsewhere

mkdir -p ~/archive/homebrews-backups
cp backups/homebrews-*.tar.gz ~/archive/homebrews-backups/
```

### 5. Document Custom Changes

If you modify docker-compose.yml or .env:

```bash
# Keep notes
echo "Added custom volume mount on 2025-10-29" >> CHANGES.txt
```

---

## Troubleshooting Updates

### Update Fails

```bash
# Check logs
docker-compose logs

# Try pulling manually
docker pull ghcr.io/an0naman/template:latest

# Verify network connectivity
docker run --rm curlimages/curl:latest https://ghcr.io
```

### Container Won't Start After Update

```bash
# Check logs
docker-compose logs

# Rollback to previous version
echo "VERSION=v1.1.0" >> .env
docker-compose pull
docker-compose up -d
```

### Database Migration Issues

```bash
# Stop app
docker-compose down

# Backup database
cp data/template.db data/template.db.pre-update

# Check database
sqlite3 data/template.db "PRAGMA integrity_check;"

# Restore if needed
cp data/template.db.pre-update data/template.db
docker-compose up -d
```

---

## Update Notifications

### Get Notified of New Releases

Watch the GitHub repository:
1. Go to https://github.com/An0naman/template
2. Click "Watch" → "Custom" → "Releases"
3. Get email on new releases

### RSS Feed

Subscribe to releases:
```
https://github.com/An0naman/template/releases.atom
```

---

## Related Documentation

- [Deployment Guide](DEPLOYMENT_GUIDE.md) - Initial setup
- [Framework Usage](FRAMEWORK_USAGE.md) - Overview
- [Troubleshooting](../guides/TROUBLESHOOTING.md) - Common issues

---

**Questions?** Open an [issue](https://github.com/An0naman/template/issues) or check the [documentation](../README.md).
