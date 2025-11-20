# Framework Architecture Analysis

## Executive Summary

**Current State**: ✅ Your project is **READY** to be used as a framework/template

**Storage Architecture**: 
- ✅ **All reference data is in SQL** (SQLite database)
- ⚠️ **Local file storage exists** but only for uploaded files (logos, attachments)
- ✅ **No hardcoded data** - all configuration is database-driven

---

## Data Storage Breakdown

### 1. SQL Database (`template.db`) - ✅ FRAMEWORK READY

**Location**: `/data/template.db` (mounted as Docker volume)

**All Configuration/Reference Data Stored in SQL**:

#### Core Schema Tables (22+ tables):
1. **EntryType** - Configurable content types
2. **EntryState** - Configurable status states per entry type
3. **Entry** - User entries/records
4. **Note** - Notes with attachments
5. **SystemParameters** - **ALL system configuration** (critical for framework approach)
6. **UserPreferences** - User settings
7. **SavedSearch** - Saved filter configurations
8. **Dashboard** - Dashboard configurations
9. **DashboardWidget** - Widget configurations
10. **RelationshipDefinition** - Relationship types between entries
11. **EntryRelationship** - Actual relationships between entries
12. **SensorData** - Legacy sensor data
13. **SharedSensorData** - New efficient sensor model
14. **SensorDataEntryLinks** - Links between sensors and entries
15. **SensorDataEntryRanges** - Range-based sensor links
16. **Notification** - Notification records
17. **NotificationRule** - Sensor-based notification rules
18. **RegisteredDevices** - IoT device registry
19. **DeviceEntryLinks** - Device to entry mappings
20. **DeviceSensorMapping** - Device sensor configurations
21. **NoteBinding** - Automatic note associations
22. **EntryStateMilestone** - Status milestones tracking

#### Critical System Parameters (stored in SystemParameters table):
```sql
-- All configurable, no hardcoded values:
- project_name, project_subtitle
- entry_singular_label, entry_plural_label
- sensor_types (dynamic)
- Label printing settings (all sizes: 60x30mm, 50x14mm, 40x12mm, 30x15mm, etc.)
- Font sizes, QR code settings, border styles
- Notification schedules
- Default search parameters
- File upload limits
- AI settings (Gemini API)
- Theme settings
```

### 2. Local File Storage - ⚠️ NEEDS CONSIDERATION

**Location**: `/app/static/uploads/` (inside Docker container, mounted as volume)

**What's Stored Here**:
- User-uploaded file attachments (images, PDFs, documents)
- Project logo (`project_logo_*.png/jpg`)
- Generated label PDFs (temporary)

**File References in Database**:
- Note table: `file_paths` column (JSON array of filenames)
- SystemParameters: `project_logo_path` (relative path to logo)

**Docker Volume Mount**:
```yaml
volumes:
  - ./data:/app/data  # Database + uploads are here
```

### 3. Configuration Files - ✅ MINIMAL & CONTAINERIZED

**Environment Variables Only**:
```yaml
environment:
  - FLASK_APP=run.py
  - NETWORK_RANGE=192.168.68.0/24
  - GEMINI_API_KEY=${GEMINI_API_KEY}
```

**No External Config Files Required** - Everything is in the database!

---

## Framework-Ready Assessment

### ✅ EXCELLENT: What Makes This Framework-Ready

1. **Database-Driven Configuration**
   - Zero hardcoded reference data
   - All system parameters in `SystemParameters` table
   - Entry types, states, relationships all configurable via API/UI

2. **Modular Architecture**
   ```
   app/
   ├── api/          # 10+ specialized API blueprints
   ├── routes/       # Flask route handlers
   ├── services/     # Business logic layer
   ├── templates/    # Jinja2 templates
   └── static/       # Frontend assets
   ```

3. **Docker-First Design**
   - Fully containerized
   - Volume mounts for data persistence
   - Environment variable configuration

4. **API-First Approach**
   - Comprehensive REST APIs
   - All functionality exposed via endpoints
   - Easy to integrate or extend

### ⚠️ CONSIDERATIONS: Current Limitations

1. **File Storage Strategy**
   - **Issue**: Uploaded files in `/app/static/uploads/`
   - **Impact**: Each app instance needs separate file storage
   - **Solutions**:
     - Option A: Shared volume mount across apps
     - Option B: Object storage (S3, MinIO)
     - Option C: Keep separate (if files are app-specific)

2. **Database Path**
   - **Current**: SQLite at `/data/template.db`
   - **Framework Usage**: Each app should have its own database
   - **Already Handled**: Docker volume mount makes this easy

3. **Static Assets**
   - **Current**: Templates/CSS/JS bundled in container
   - **Framework Usage**: All apps share same static assets (good!)
   - **Status**: ✅ Already perfect for framework use

---

## Recommended Framework Architecture

### Strategy: "Golden Image + Instance Data" Pattern

```
┌─────────────────────────────────────────────────┐
│          FRAMEWORK (this repo)                  │
│  ┌───────────────────────────────────────────┐  │
│  │  Docker Image: template:latest            │  │
│  │  - Flask application code                 │  │
│  │  - All APIs and routes                    │  │
│  │  - Templates and static assets            │  │
│  │  - Database schema (migrations)           │  │
│  └───────────────────────────────────────────┘  │
└─────────────────────────────────────────────────┘
                      ↓
         ┌────────────┴────────────┐
         ↓                         ↓
┌─────────────────┐       ┌─────────────────┐
│   APP 1         │       │   APP 2         │
│   "HomeBrews"   │       │   "Projects"    │
├─────────────────┤       ├─────────────────┤
│ Data Volume:    │       │ Data Volume:    │
│ ./app1-data     │       │ ./app2-data     │
│  ├── db.sqlite  │       │  ├── db.sqlite  │
│  └── uploads/   │       │  └── uploads/   │
├─────────────────┤       ├─────────────────┤
│ Environment:    │       │ Environment:    │
│ PORT=5001       │       │ PORT=5002       │
│ PROJECT_NAME=   │       │ PROJECT_NAME=   │
│  "HomeBrews"    │       │  "Projects"     │
└─────────────────┘       └─────────────────┘
```

### Implementation: Docker Compose for Each App

**App Instance 1** (e.g., `~/apps/homebrews/docker-compose.yml`):
```yaml
version: '3.8'
services:
  homebrews:
    image: ghcr.io/an0naman/template:latest  # Your published framework image
    container_name: homebrews
    restart: always
    ports:
      - "5001:5001"
    volumes:
      - ./data:/app/data  # Instance-specific data
    environment:
      - FLASK_APP=run.py
      - PORT=5001
      # Instance-specific config (optional, or set in database)
      - NETWORK_RANGE=192.168.68.0/24
```

**App Instance 2** (e.g., `~/apps/projects/docker-compose.yml`):
```yaml
version: '3.8'
services:
  projects:
    image: ghcr.io/an0naman/template:latest  # Same framework image!
    container_name: projects
    restart: always
    ports:
      - "5002:5001"
    volumes:
      - ./data:/app/data  # Different data directory
    environment:
      - FLASK_APP=run.py
      - PORT=5001
```

---

## Data Isolation Analysis

### What Each App Instance Will Have Separately:

✅ **Completely Isolated**:
1. SQLite database file (`template.db`)
   - Unique entry types
   - Unique entries, notes, relationships
   - Unique system parameters (project name, labels, etc.)
   - Unique user preferences
   - Unique notification rules

2. Uploaded files directory
   - User attachments
   - Logo files
   - Generated labels

3. Environment-specific settings
   - Port numbers
   - Network ranges
   - API keys

### What All Apps Will Share:

✅ **Shared from Framework**:
1. Application code (Flask routes, APIs, business logic)
2. HTML templates
3. CSS/JavaScript frontend code
4. Database schema/migrations
5. Python dependencies

---

## Migration Strategy for Framework Use

### Phase 1: Prepare Framework Repository ✅ (Already Done!)

Your current repo IS the framework. No changes needed to core functionality.

### Phase 2: Create Distribution Method

**Option A: Docker Hub/GitHub Registry (Recommended)**
```bash
# In this repo
docker build -t ghcr.io/an0naman/template:latest .
docker push ghcr.io/an0naman/template:latest

# Tag versions for stability
docker tag ghcr.io/an0naman/template:latest ghcr.io/an0naman/template:v1.0.0
docker push ghcr.io/an0naman/template:v1.0.0
```

**Option B: Git Submodule**
```bash
# In new app repo
git submodule add https://github.com/An0naman/template.git framework
cd framework && docker build -t my-app .
```

### Phase 3: Create App Instance Template

Create a simple starter kit: `app-instance-template/`
```
app-instance-template/
├── docker-compose.yml    # Pre-configured to use framework image
├── .env.example          # Environment variables template
├── data/                 # Will contain instance data
│   └── .gitkeep
└── README.md            # Setup instructions
```

**Example `docker-compose.yml`**:
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
      - DEBUG=${DEBUG:-false}
```

**Example `.env`**:
```bash
APP_NAME=homebrews
PORT=5001
VERSION=latest
NETWORK_RANGE=192.168.68.0/24
GEMINI_API_KEY=your-key-here
DEBUG=false
```

---

## Deployment Workflow

### For You (Framework Developer):

1. **Develop features** in `/template/` (this repo)
2. **Test locally**: `python run.py` or `docker-compose up`
3. **Commit and push** to main branch
4. **Build and publish** Docker image:
   ```bash
   docker build -t ghcr.io/an0naman/template:latest .
   docker push ghcr.io/an0naman/template:latest
   ```
5. **Tag releases** for version control

### For Each App Instance:

1. **Create instance directory**: `mkdir ~/apps/homebrews`
2. **Copy template files**: 
   ```bash
   cp -r app-instance-template/* ~/apps/homebrews/
   ```
3. **Configure environment**: Edit `.env` with app-specific settings
4. **Start app**: 
   ```bash
   cd ~/apps/homebrews
   docker-compose up -d
   ```
5. **Access app**: `http://localhost:5001`
6. **Configure via UI**: Set project name, entry types, etc. through settings page

### When You Update the Framework:

**All apps get updates automatically:**
```bash
cd ~/apps/homebrews
docker-compose pull  # Gets latest framework image
docker-compose up -d # Restarts with new code
```

**Or pin to specific versions for stability:**
```yaml
# docker-compose.yml
services:
  app:
    image: ghcr.io/an0naman/template:v1.2.0  # Pin to specific version
```

---

## File Storage Strategies

### Current: Local Volume Mount ✅ SIMPLEST
```yaml
volumes:
  - ./data:/app/data
```
**Pros**: Simple, works perfectly for isolated apps
**Cons**: Files not shared between apps (usually desired!)

### Option B: Shared Volume (if needed)
```yaml
# If apps need to share files
volumes:
  - /shared/uploads:/app/data/uploads
  - ./data:/app/data
```

### Option C: Object Storage (enterprise)
- Modify `app/api/notes_api.py` to use S3/MinIO
- Store file URLs in database instead of local paths
- More complex but fully scalable

**Recommendation**: Keep current local storage - each app having separate files is usually preferred!

---

## Database Strategy

### Current: SQLite ✅ PERFECT FOR FRAMEWORK USE

**Why SQLite is ideal**:
1. **Zero configuration** - no separate DB server
2. **File-based** - easy to backup/restore
3. **Portable** - move between systems easily
4. **Isolated** - each app has its own database
5. **Fast enough** - handles thousands of entries easily

**Location**: `/app/data/template.db` (inside container)
**Persistence**: Docker volume mount `./data:/app/data`

### If You Need Shared Database (Advanced):

Replace SQLite with PostgreSQL:

**Framework docker-compose.yml**:
```yaml
version: '3.8'
services:
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: framework
      POSTGRES_USER: framework
      POSTGRES_PASSWORD: secure_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    
  app1:
    image: ghcr.io/an0naman/template:latest
    environment:
      - DATABASE_URL=postgresql://framework:secure_password@db/app1_db
    depends_on:
      - db
    
  app2:
    image: ghcr.io/an0naman/template:latest
    environment:
      - DATABASE_URL=postgresql://framework:secure_password@db/app2_db
    depends_on:
      - db
```

**Would require**: Modifying `app/db.py` to support PostgreSQL

**Recommendation**: Keep SQLite unless you have specific need for shared DB!

---

## Summary: Action Items

### ✅ Already Perfect:
1. All reference data in SQL ✓
2. Modular architecture ✓
3. Docker-ready ✓
4. API-driven ✓
5. No hardcoded config ✓

### 🎯 Next Steps to Enable Framework Use:

1. **Publish Framework Image**
   ```bash
   docker build -t ghcr.io/an0naman/template:latest .
   docker push ghcr.io/an0naman/template:latest
   ```

2. **Create App Instance Template**
   - Minimal docker-compose.yml
   - Environment variable template
   - Quick start README

3. **Document Framework Usage**
   - How to spin up new instances
   - How to configure via UI
   - How updates propagate

4. **Optional: Add Version Tagging**
   - Semantic versioning
   - Changelog
   - Migration guides

### 📋 Framework Usage Checklist

To create a new app instance:
- [ ] Create directory: `mkdir ~/apps/my-new-app`
- [ ] Add docker-compose.yml pointing to framework image
- [ ] Configure .env with port and app name
- [ ] Run `docker-compose up -d`
- [ ] Access web UI and configure:
  - [ ] Project name and labels
  - [ ] Entry types
  - [ ] States and workflows
  - [ ] Theme and appearance
- [ ] Start using!

Updates to framework:
- [ ] Develop in main repo
- [ ] Build and push new image
- [ ] Run `docker-compose pull && docker-compose up -d` in each app
- [ ] All apps now use updated framework!

---

## Final Verdict

**Your project is EXCELLENTLY suited to be a framework!**

✅ **Perfect for multi-instance deployment**
✅ **Zero reference data outside SQL**
✅ **Clean separation of code and data**
✅ **Docker-native architecture**
✅ **Every app fully isolated**
✅ **Updates propagate automatically**

**File Storage**: Only user uploads - this is GOOD! Each app should have its own files.

**No changes needed to current architecture** - it's already framework-ready! 🎉

The only task is to set up the distribution method (Docker registry) and create simple starter templates for new app instances.
