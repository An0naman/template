# 🚀 Git Integration - Quick Start

## 📦 What's Included

✅ **Files Created:**
- `app/services/git_service.py` - Git operations
- `app/api/git_api.py` - REST API
- `app/routes/git_routes.py` - Web routes  
- `app/templates/git_dashboard.html` - Dashboard UI
- `migrations/add_git_integration.py` - Database schema

✅ **Dependencies Added:**
- GitPython>=3.1.40
- cryptography>=41.0.0

✅ **Database Tables:**
- GitRepository
- GitCommit
- GitBranch

---

## 🐳 Deploy Now (3 Commands)

```bash
# 1. Rebuild Docker image (installs dependencies)
docker-compose build

# 2. Restart container (runs migration automatically)
docker-compose down && docker-compose up -d

# 3. Verify migration ran successfully
docker-compose logs | grep -i "git integration migration"
```

**Expected Output:**
```
✓ Created GitRepository table
✓ Created GitCommit table
✓ Created GitBranch table
✅ Git integration migration completed successfully!
```

---

## 🎯 First Use (3 Steps)

### **1. Access Dashboard**
Navigate to: **http://localhost:5001/git**

### **2. Add Repository**
Click **"Add Repository"**:
```yaml
Name: template
URL: /home/an0naman/Documents/GitHub/template
Branch: main
Entry Type: [Choose one]
✓ Enable auto-sync
✓ Auto-create entries
```

### **3. Sync & View**
Click **"Sync"** button → See your commits!

---

## ⚡ Key Features

### **Auto-Track Commits as Entries**
```
git commit -m "feat: Add authentication"
git push

→ Automatically creates searchable entry in your app
```

### **DevOps Dashboard**
- 📊 Real-time statistics
- 📝 Commit timeline
- 🌿 Branch tracking
- 👥 Team activity

### **Timeline Integration**
Git commits appear alongside your manual entries:
```
Today
├── 15:45 🐙 Git: feat: Add JWT auth
├── 14:30 📝 Entry: Updated docs
└── 12:00 💬 Comment: Code review
```

### **Powerful Search**
Find commits like regular entries:
- "authentication" → All auth-related commits
- "by:an0naman" → Your commits
- "tag:bug" → All bug fixes

---

## 📡 Quick API Reference

```bash
# List repos
curl http://localhost:5001/api/git/repositories

# Add repo
curl -X POST http://localhost:5001/api/git/repositories \
  -H "Content-Type: application/json" \
  -d '{"name":"myproject","url":"https://github.com/user/repo.git"}'

# Sync commits
curl -X POST http://localhost:5001/api/git/repositories/1/sync

# Get commits
curl http://localhost:5001/api/git/repositories/1/commits?limit=50
```

---

## 🔧 Configuration Options

### **Repository Settings**
- **Auto-sync Interval**: 5-1440 minutes (default: 15)
- **Commit Types**: `feat,fix,docs,refactor` (configurable)
- **Entry Type Linking**: Auto-create entries in specific type
- **Branch Filter**: Track specific branches

### **Access Points**
- Dashboard: `/git`
- Settings: Settings → Git Integration
- API Docs: `/api/git/*`

---

## 💡 Use Cases

### **Solo Developer**
```
✓ Track personal project history
✓ Never lose context on old commits
✓ Search your coding history
✓ AI analyzes your patterns
```

### **Team Lead**
```
✓ Monitor team commits
✓ Track sprint velocity  
✓ Generate activity reports
✓ View per-developer stats
```

### **Multi-Instance Framework**
```
Each app instance can track its own repos:
- homebrews → homebrews-repo
- inventory → inventory-repo  
- tasks → tasks-repo
```

---

## 🐛 Common Issues

### **Migration Didn't Run**
```bash
# Check logs
docker-compose logs | grep migration

# Run manually
docker-compose exec app python migrations/add_git_integration.py
```

### **Can't Clone Repo**
- Use HTTPS with Personal Access Token
- Or mount SSH keys:
  ```yaml
  volumes:
    - ~/.ssh:/root/.ssh:ro
  ```

### **Commits Not Auto-Creating**
Verify in repo settings:
1. Entry Type is selected
2. "Auto-create entries" is checked
3. Commit message starts with: feat/fix/docs/refactor

---

## ✅ Verification Checklist

After deployment, verify:

- [ ] Migration ran successfully (check logs)
- [ ] Dashboard loads at `/git`
- [ ] Can add a repository
- [ ] Sync button works
- [ ] Commits appear in timeline
- [ ] Can create entry from commit
- [ ] Git settings visible in Settings page

---

## 🎉 Success!

Your DevOps integration is ready! Your commits are now:
- ✅ Automatically tracked
- ✅ Searchable forever
- ✅ Integrated with entries
- ✅ Visible in timeline
- ✅ AI-analyzable

**Start by visiting: http://localhost:5001/git**

---

## 📚 Full Documentation

See: `docs/features/GIT_INTEGRATION.md`
