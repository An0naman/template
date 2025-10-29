# Quick Start: Framework Setup

**Get your framework up and running in 5 minutes!**

---

## Step 1: Enable GitHub Actions (1 minute)

```bash
cd /path/to/template

# Commit workflow files
git add .github/workflows/
git commit -m "Add CI/CD workflows for framework"
git push origin main
```

✅ **Result:** GitHub Actions will automatically build your Docker image on every push.

---

## Step 2: Create First Release (2 minutes)

```bash
# Tag your current version
git tag -a v1.0.0 -m "Initial framework release"
git push origin v1.0.0
```

✅ **Result:** 
- Docker image published to `ghcr.io/an0naman/template:v1.0.0`
- Also tagged as `:latest`, `:v1.0`, `:v1`
- GitHub release created with changelog

---

## Step 3: Create Your First App (2 minutes)

```bash
# Create app directory
mkdir -p ~/apps/my-first-app
cd ~/apps/my-first-app

# Copy template files
cp -r /path/to/template/app-instance-template/* .
cp /path/to/template/app-instance-template/.env.example .env

# Configure
cat > .env << 'EOF'
APP_NAME=my-first-app
PORT=5001
VERSION=latest
SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
DEBUG=false
EOF

# Start
docker-compose pull
docker-compose up -d

# Check logs
docker-compose logs -f
```

✅ **Result:** Your first app is running and accessible from:
- **Localhost**: http://localhost:5001
- **Network**: http://YOUR_SERVER_IP:5001
- **CasaOS**: Add custom app with URL above

---

## Step 4: Configure App (In Browser)

1. Open http://localhost:5001 (or http://YOUR_SERVER_IP:5001 from any device)
2. Go to **Settings** → **System Configuration**
3. Set:
   - Project Name: "My Project"
   - Entry Labels
   - Theme colors
4. Go to **Settings** → **Data Structure**
5. Create entry types and states

✅ **Result:** Your app is configured and ready to use!

---

## Step 5: Test Updates (Optional)

```bash
# Make a change to framework
cd /path/to/template
echo "# Test change" >> README.md
git commit -am "Test framework update"
git push

# Wait 2-3 minutes for GitHub Actions

# Update your app
cd ~/apps/my-first-app
./update.sh
```

✅ **Result:** Your app is updated with the latest framework code!

---

## What's Next?

### Create More Apps

```bash
# App 2 on port 5002
mkdir -p ~/apps/second-app
cd ~/apps/second-app
# ... repeat Step 3 with PORT=5002 ...

# App 3 on port 5003
mkdir -p ~/apps/third-app
cd ~/apps/third-app
# ... repeat Step 3 with PORT=5003 ...
```

### Make Framework Improvements

```bash
cd /path/to/template

# Edit code
vim app/routes/main_routes.py

# Commit and push
git add .
git commit -m "Add new feature"
git push

# All apps can now update with ./update.sh
```

### Create Versioned Releases

```bash
# When ready for new version
git tag -a v1.1.0 -m "Version 1.1.0"
git push origin v1.1.0

# Apps can pin to this version:
# VERSION=v1.1.0 in .env
```

---

## Common Commands

### App Management

```bash
cd ~/apps/my-app

# Start
docker-compose up -d

# Stop
docker-compose down

# Restart
docker-compose restart

# View logs
docker-compose logs -f

# Check status
docker-compose ps
```

### Updates & Backups

```bash
# Update to latest
./update.sh

# Create backup
./backup.sh

# List backups
ls -lh backups/

# Restore backup
tar -xzf backups/my-app-20251029-143022.tar.gz
docker-compose restart
```

---

## Troubleshooting

### Port already in use

```bash
# Change port in .env
sed -i 's/PORT=5001/PORT=5002/' .env
docker-compose down
docker-compose up -d
```

### Can't pull image

```bash
# Login to GitHub Container Registry
echo $GITHUB_TOKEN | docker login ghcr.io -u $GITHUB_USERNAME --password-stdin

# Or make package public on GitHub
```

### Health check failing

```bash
# Check logs
docker-compose logs

# Check health directly
curl http://localhost:5001/api/health

# Restart
docker-compose restart
```

---

## Resources

- [Full Deployment Guide](DEPLOYMENT_GUIDE.md)
- [Update Guide](UPDATE_GUIDE.md)
- [Framework Usage](FRAMEWORK_USAGE.md)
- [Implementation Summary](IMPLEMENTATION_SUMMARY.md)

---

**🎉 You're all set!** Your framework is ready to power multiple apps.
