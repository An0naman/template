# 🚀 Git Integration - Setup & Usage Guide

## 📋 Overview

The Git Integration feature transforms your Template framework into a **DevOps command center**, automatically tracking commits, branches, and development activity as searchable entries.

---

## ✅ What's Been Implemented

### **1. Core Components**
- ✅ `app/services/git_service.py` - Git operations (clone, sync, commit tracking)
- ✅ `app/api/git_api.py` - REST API endpoints for repository management
- ✅ `app/routes/git_routes.py` - Web routes for the DevOps dashboard
- ✅ `app/templates/git_dashboard.html` - Interactive UI for Git activity
- ✅ `migrations/add_git_integration.py` - Database schema (auto-runs on startup)

### **2. Database Tables**
- ✅ `GitRepository` - Repository configurations
- ✅ `GitCommit` - Commit history with stats
- ✅ `GitBranch` - Branch tracking

### **3. Dependencies**
- ✅ `GitPython>=3.1.40` - Git operations
- ✅ `cryptography>=41.0.0` - Credential encryption

---

## 🐳 Deployment (Docker - Automatic)

Since your framework uses Docker, everything is **automatic**:

### **Step 1: Rebuild the Docker Image**

```bash
cd /home/an0naman/Documents/GitHub/template

# Rebuild the image (dependencies install automatically)
docker-compose build

# Or if using docker build directly:
docker build -t template:latest .
```

### **Step 2: Start the Container**

```bash
# Restart with new image
docker-compose down
docker-compose up -d

# The migration will run automatically via docker-entrypoint.sh! ✨
```

### **Step 3: Verify Migration**

Check the logs to confirm migration ran:

```bash
docker-compose logs | grep -i git

# You should see:
# ✓ Created GitRepository table
# ✓ Created GitCommit table
# ✓ Created GitBranch table
# ✅ Git integration migration completed successfully!
```

---

## 🎯 Quick Start Guide

### **1. Access the DevOps Dashboard**

Navigate to: **http://localhost:5001/git**

Or from the Settings page → Git Integration → "Open DevOps Dashboard"

### **2. Add Your First Repository**

Click **"Add Repository"** and fill in:

```yaml
Repository Name: My Project
Repository URL: https://github.com/An0naman/template.git
Default Branch: main
Link to Entry Type: [Select an existing Entry Type]
✓ Enable auto-sync
✓ Auto-create entries from commits
```

**Supported Repository Types:**
- 🌐 Remote: `https://github.com/user/repo.git`
- 🏠 Local: `/path/to/local/repo`
- 🔐 Private repos: Add credentials in the form

### **3. Sync Commits**

Click the **"Sync"** button to fetch commits from the repository:

```
🔄 Syncing repository...
✅ Synced 47 new commits, skipped 0 existing
```

### **4. View Commits**

Your commits appear in the timeline:

```
📝 feat: Add user authentication with JWT tokens
   └─ a1b2c3d by an0naman | 2 hours ago
   └─ 5 files changed | +234 -12

📝 fix: Resolve database connection timeout
   └─ e4f5g6h by an0naman | 5 hours ago
   └─ 2 files changed | +15 -8
```

### **5. Create Entries from Commits**

- **Manual**: Click "View Details" → "Create Entry"
- **Automatic**: Enable "Auto-create entries" in repo settings

---

## 🎨 Features

### **1. Repository Management**

**Add Multiple Repositories:**
```
✓ template (main framework)
✓ homebrews (instance app)
✓ inventory (instance app)
```

**Per-Repository Settings:**
- Link to specific Entry Types
- Auto-sync interval (default: 15 minutes)
- Auto-create entries from commits
- Commit type filters (feat, fix, docs, refactor)

### **2. DevOps Dashboard**

**Statistics Cards:**
```
┌─────────────┬─────────────┬─────────────┬─────────────┐
│ 156         │ 12          │ 3           │ 12,847      │
│ Total       │ Today       │ Contributors│ Lines       │
│ Commits     │             │             │ Changed     │
└─────────────┴─────────────┴─────────────┴─────────────┘
```

**Commit Timeline:**
- Real-time commit feed
- File change statistics
- Author information
- Link to entries

**Branch Tracking:**
- Active branches
- Last commit per branch
- Branch-specific filtering

### **3. Entry Integration**

**Auto-Created Entries Include:**
```markdown
**Commit:** `a1b2c3d`
**Repository:** template
**Author:** an0naman <email@example.com>
**Date:** 2025-11-20 15:45:00

Full commit message here...

---
**Changes:**
- Files changed: 5
- Insertions: +234
- Deletions: -12
```

**Searchable:**
- Find commits by message
- Search by author
- Filter by date range
- Tag by commit type

### **4. Timeline Integration**

Git events appear in your existing timeline:

```
📅 Nov 20, 2025
├── 15:45 🐙 Git: Pushed 3 commits to feature/auth
├── 14:30 📝 Entry: Updated requirements document
├── 12:00 💬 Comment: "Need to review security"
└── 10:00 🔔 Reminder: Code review scheduled
```

---

## 🔧 Configuration

### **Entry Type Setup**

**Create a "Development" Entry Type:**

1. Go to Settings → Entry Types
2. Create new: **"Development Tasks"**
3. Configure in Git settings:
   - Link repository to this Entry Type
   - Enable auto-create entries

### **Commit Type Filtering**

Configure which commits create entries:

```python
# Default filters (comma-separated):
feat,fix,docs,refactor

# Skip: chore, style, test, build
```

### **Auto-Sync Interval**

Set how often to check for new commits:

```yaml
Default: 15 minutes
Minimum: 5 minutes
Maximum: 1440 minutes (24 hours)
```

---

## 📡 API Endpoints

### **Repository Management**

```bash
# List all repositories
GET /api/git/repositories

# Add repository
POST /api/git/repositories
{
  "name": "My Project",
  "url": "https://github.com/user/repo.git",
  "entry_type_id": 1,
  "auto_sync": true,
  "auto_create_entries": true
}

# Get repository details
GET /api/git/repositories/{repo_id}

# Sync repository
POST /api/git/repositories/{repo_id}/sync
```

### **Commit Operations**

```bash
# Get commits
GET /api/git/repositories/{repo_id}/commits?limit=50&branch=main

# Create entry from commit
POST /api/git/commits/{commit_hash}/create-entry
{
  "entry_type_id": 1
}

# Link entry to commit
POST /api/entries/{entry_id}/git/link
{
  "commit_hash": "a1b2c3d4..."
}
```

### **Statistics**

```bash
# Get repository stats
GET /api/git/repositories/{repo_id}/stats

# Get branches
GET /api/git/repositories/{repo_id}/branches
```

---

## 🔐 Security

### **Credential Storage**

Credentials are **encrypted at rest** using Fernet symmetric encryption:

```python
# Encryption key stored at: /app/instance/.git_key
# Automatically generated on first use
# Credentials never sent to client
```

### **Best Practices**

1. **Use Personal Access Tokens** instead of passwords
2. **GitHub**: Settings → Developer Settings → Personal Access Tokens
3. **GitLab**: Settings → Access Tokens
4. **Scope**: Read-only access is sufficient

### **Docker Volume Permissions**

```yaml
# docker-compose.yml
volumes:
  - ./data:/app/data  # Database & Git repos stored here
  - ./uploads:/app/uploads
```

---

## 🚀 Use Cases

### **1. Solo Developer**

Track your personal projects:
```
✓ Connect your main project repository
✓ Auto-create entries from commits
✓ Use AI to analyze development patterns
✓ Search commit history by keywords
```

### **2. Team Lead**

Monitor team activity:
```
✓ Multiple repositories per project
✓ View commits by developer
✓ Generate sprint reports
✓ Track bug fix velocity
```

### **3. Framework Instances**

Track each app separately:
```
template/           # Framework repo
├── homebrews/     # Instance 1 repo
├── inventory/     # Instance 2 repo
└── tasks/         # Instance 3 repo
```

Each instance can connect its own repository!

---

## 🐛 Troubleshooting

### **Migration Didn't Run**

Check migration logs:
```bash
docker-compose logs | grep -A 10 "Git integration migration"
```

Run manually if needed:
```bash
docker-compose exec app python migrations/add_git_integration.py
```

### **Can't Clone Repository**

**Error:** `Authentication failed`

**Solution:**
1. Use HTTPS with Personal Access Token
2. Or use SSH keys mounted in Docker:
```yaml
volumes:
  - ~/.ssh:/root/.ssh:ro
```

### **Commits Not Syncing**

1. Check repository URL is correct
2. Verify network connectivity from container
3. Check sync button for error messages
4. View logs: `docker-compose logs app`

### **Entries Not Auto-Creating**

Verify:
1. ✓ Repository has `entry_type_id` configured
2. ✓ "Auto-create entries" is enabled
3. ✓ Commit message matches filters (feat, fix, etc.)

---

## 📊 Example Workflow

### **Daily Development Routine**

```bash
# Morning
1. Open DevOps Dashboard
2. See yesterday's commits organized as entries
3. AI summarizes: "3 features, 2 bug fixes"
4. Add manual notes to auto-generated entries

# During Development
5. Code and commit as usual
6. Commits sync automatically every 15 min

# End of Day
7. Review timeline showing code + manual entries
8. Search: "authentication" to find related work
9. Export week's activity for standup
```

---

## 🎯 Next Steps

### **Recommended Enhancements**

1. **Connect Multiple Repos** - Track all your projects
2. **Configure Entry Types** - Separate features/bugs/docs
3. **Enable AI Analysis** - Let AI analyze commit patterns
4. **Set Up Webhooks** - Real-time sync from GitHub/GitLab
5. **Create Dashboards** - Visualize development metrics

### **Advanced Features (Future)**

- [ ] Pull Request tracking
- [ ] Code review integration
- [ ] Deployment tracking
- [ ] CI/CD pipeline status
- [ ] Issue tracker sync
- [ ] Time estimation from commits

---

## 📝 Summary

**What You Get:**

✅ Automatic commit tracking as entries  
✅ Development history preserved forever  
✅ Searchable code changes  
✅ Team activity monitoring  
✅ Integration with your existing Entry system  
✅ AI-powered code analysis  
✅ Zero-config Docker deployment  

**Access Points:**

- 🌐 Dashboard: `http://localhost:5001/git`
- ⚙️ Settings: Settings → Git Integration
- 🔍 Search: Search for commits like regular entries
- 📊 Timeline: See commits in unified timeline

---

## 🆘 Need Help?

1. **Check logs**: `docker-compose logs app`
2. **Verify migration**: `docker-compose logs | grep Git`
3. **Test API**: Visit `/api/git/repositories`
4. **Restart container**: `docker-compose restart`

**The migration and dependencies install automatically on container build!** 🎉
