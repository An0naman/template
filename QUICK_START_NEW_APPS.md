# 🚀 Quick Guide: Spinning Up New Apps

**Status**: ✅ Ready to deploy!  
**Date**: November 8, 2025

---

## Current Setup

You have everything ready:
- ✅ Framework builds automatically via GitHub Actions
- ✅ Images push to `ghcr.io/an0naman/template:latest`
- ✅ Watchtower auto-updates all apps
- ✅ Template ready at `app-instance-template/`

**Current apps:**
- `devops` (port 5001 or similar)
- `projects` (port 5002 or similar)

---

## Method 1: Using the Creation Script (Easiest! 🎯)

I just created a script that does everything for you:

```bash
cd ~/Documents/GitHub/template
./create-new-app.sh
```

This will:
1. Ask you for the app name (e.g., "homebrews", "inventory", "recipes")
2. Ask you for the port (e.g., 5003, 5004)
3. Create the directory structure
4. Configure everything automatically
5. Tell you exactly what to do next!

**Then just:**
```bash
cd ~/apps/your-new-app
docker-compose pull
docker-compose up -d
```

Done! 🎉

---

## Method 2: Manual Setup (Step-by-Step)

### Step 1: Create App Directory

```bash
# Choose your app name
APP_NAME=homebrews  # Change this!
PORT=5003           # Use an available port

# Create directory
mkdir -p ~/apps/${APP_NAME}
cd ~/apps/${APP_NAME}
```

### Step 2: Copy Template Files

```bash
# Copy from template
cp ~/Documents/GitHub/template/app-instance-template/* .
cp ~/Documents/GitHub/template/app-instance-template/.env.example .env
cp ~/Documents/GitHub/template/app-instance-template/.gitignore .
```

### Step 3: Configure Your App

```bash
# Edit the configuration
nano .env
```

**Update these values:**
```bash
APP_NAME=homebrews    # Your app name
PORT=5003             # Your chosen port
VERSION=latest        # Framework version
```

**Optional settings:**
```bash
# For IoT devices
NETWORK_RANGE=192.168.68.0/24

# For AI features
GEMINI_API_KEY=your-api-key

# For notifications
NTFY_TOPIC=homebrews-alerts
NTFY_SERVER_URL=https://ntfy.sh
```

### Step 4: Start Your App

```bash
# Pull the latest framework image
docker-compose pull

# Start the app
docker-compose up -d

# Check it's running
docker-compose ps

# View logs
docker-compose logs -f
```

### Step 5: Access Your App

**Locally:**
```
http://localhost:5003
```

**From other devices on your network:**
```
http://YOUR_SERVER_IP:5003
```

Find your IP:
```bash
hostname -I | awk '{print $1}'
```

---

## Initial Configuration

Once your app is running:

1. **Open the web interface** in your browser
2. **Go to Settings** → **System Configuration**
3. **Configure your app:**
   - Project Name: "HomeBrews Inventory"
   - Entry Label (singular): "Brew"
   - Entry Label (plural): "Brews"
   - Choose your theme colors
4. **Set up Data Structure** (Settings → Data Structure):
   - Add Entry Types (e.g., Beer, Wine, Mead)
   - Add States (e.g., Brewing, Fermenting, Bottled)
5. **Start using it!**

---

## Auto-Update is Already Working! 🎉

Your apps will automatically update when you push code to GitHub:

```
You push code → GitHub Actions builds → Image published → Watchtower updates all apps
     (0 min)         (2-3 min)              (instant)              (~5 min)
```

**Total time: ~5-10 minutes from push to all apps updated!**

---

## Managing Multiple Apps

### Check Status of All Apps

```bash
cd ~/apps
for app in */; do
    echo "=== ${app} ==="
    cd ~/apps/${app}
    docker-compose ps
done
```

### Update All Apps Manually (if needed)

```bash
cd ~/apps
for app in */; do
    echo "=== Updating ${app} ==="
    cd ~/apps/${app}
    ./update.sh
done
```

### Backup All Apps

```bash
cd ~/apps
for app in */; do
    echo "=== Backing up ${app} ==="
    cd ~/apps/${app}
    ./backup.sh
done
```

---

## Example: Creating a "HomeBrews" App

```bash
# 1. Use the creation script
cd ~/Documents/GitHub/template
./create-new-app.sh

# When prompted:
#   App name: homebrews
#   Port: 5003

# 2. Review the configuration
nano ~/apps/homebrews/.env

# 3. Start the app
cd ~/apps/homebrews
docker-compose pull
docker-compose up -d

# 4. Access it
xdg-open http://localhost:5003

# 5. Configure via web interface
# - Project Name: "HomeBrews Inventory"
# - Entry Types: Beer, Wine, Mead
# - States: Planning, Brewing, Fermenting, Bottled, Consumed
```

---

## Port Reference

Keep track of your ports:

| App      | Port | Purpose              |
|----------|------|----------------------|
| devops   | 5001 | DevOps tracking      |
| projects | 5002 | Project management   |
| ?        | 5003 | Available            |
| ?        | 5004 | Available            |
| ?        | 5005 | Available            |

---

## Useful Commands

### View App Logs
```bash
cd ~/apps/your-app
docker-compose logs -f
```

### Restart an App
```bash
cd ~/apps/your-app
docker-compose restart
```

### Stop an App
```bash
cd ~/apps/your-app
docker-compose down
```

### Update an App Manually
```bash
cd ~/apps/your-app
./update.sh
```

### Backup an App
```bash
cd ~/apps/your-app
./backup.sh
```

### Check App Version
```bash
cd ~/apps/your-app
docker-compose images
```

---

## Troubleshooting

### Port Already in Use
```bash
# Check what's using the port
sudo netstat -tlnp | grep :5003

# Choose a different port in .env
```

### Can't Access from Network
```bash
# Check firewall
sudo ufw status

# Allow the port
sudo ufw allow 5003
```

### App Won't Start
```bash
# View logs
cd ~/apps/your-app
docker-compose logs

# Check if port is available
docker-compose ps
```

### Watchtower Not Updating
```bash
# Check watchtower logs
cd ~/apps/your-app
docker logs your-app-watchtower -f

# Manually trigger update
cd ~/apps/your-app
./update.sh
```

---

## Next Steps

1. **Create your first new app** using the script
2. **Configure it** via the web interface
3. **Test auto-update** by making a small change and pushing to GitHub
4. **Monitor watchtower logs** to see it auto-update

---

## Summary

✅ **You're ready!** Just run:
```bash
cd ~/Documents/GitHub/template
./create-new-app.sh
```

Everything is automated:
- ✅ GitHub Actions builds your framework
- ✅ Watchtower auto-updates all apps
- ✅ Each app is independent with its own database
- ✅ All apps share the same framework code

**You can now spin up as many apps as you want!** 🚀
