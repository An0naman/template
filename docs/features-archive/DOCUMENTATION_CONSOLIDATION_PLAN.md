# Documentation Consolidation Plan

## Current State
**90 markdown files** in root directory - mostly development notes, feature implementations, and bug fixes

## Proposed Structure

```
template/
├── README.md                    # Main project overview (KEEP & UPDATE)
├── CHANGELOG.md                 # Version history (KEEP & UPDATE)
├── CONTRIBUTING.md              # Contribution guidelines (KEEP)
├── docs/
│   ├── setup/
│   │   ├── INSTALLATION.md      # Quick start, Docker, local setup
│   │   ├── CASAOS.md           # CasaOS-specific deployment
│   │   └── DEPLOYMENT.md       # Production deployment guide
│   ├── features/
│   │   ├── LABEL_PRINTING.md   # Complete label printing guide
│   │   ├── NIIMBOT.md          # Niimbot printer integration
│   │   ├── SENSORS.md          # Sensor data & IoT devices
│   │   ├── NOTIFICATIONS.md    # Notification system
│   │   ├── DASHBOARDS.md       # Dashboard & widgets
│   │   ├── AI_CHATBOT.md       # AI features
│   │   ├── THEMES.md           # Theme system
│   │   └── RELATIONSHIPS.md    # Entry relationships
│   ├── guides/
│   │   ├── USER_GUIDE.md       # End-user documentation
│   │   ├── API_REFERENCE.md    # API documentation
│   │   └── SECURITY.md         # Security implementation
│   ├── development/
│   │   ├── ARCHITECTURE.md     # System architecture
│   │   ├── DATABASE.md         # Database schema
│   │   └── TESTING.md          # Testing guide
│   └── framework/
│       └── FRAMEWORK_USAGE.md  # Using as a framework/template
└── archive/
    └── [All old implementation notes]
```

## Consolidation Categories

### 🗑️ DELETE (Obsolete/Redundant - 40+ files)
**Development Notes** (completed features):
- COLLAPSE_*.md (4 files) → Feature complete
- ENTRY_LAYOUT_*.md (9 files) → Feature complete
- TIMELINE_*.md (7 files) → Feature complete
- V2_*.md (6 files) → Version updates complete
- *_FIX.md, *_DEBUG.md (15+ files) → Bugs fixed
- *_COMPLETE.md, *_STATUS.md (10+ files) → Features done

### 📦 CONSOLIDATE (Merge related topics - 30+ files)

**Label Printing** (7 files → 1):
- A4_LABEL_SHEET_LAYOUT.md
- A4_LABEL_UPDATE_SUMMARY.md
- LABEL_ORIENTATION_GUIDE.md
- LABEL_PRINTER_CONFIGURATION.md
- LABEL_ROTATION_FEATURE.md
- LOGO_ADAPTIVE_LAYOUT_FEATURE.md
- TEXT_WRAPPING_FEATURE.md
→ **docs/features/LABEL_PRINTING.md**

**Niimbot Printers** (5 files → 1):
- NIIMBOT_B1_SUCCESS.md
- NIIMBOT_PAIRING.md
- NIIMBOT_PRINTER_INTEGRATION.md
- NIIMBOT_SUMMARY.md
- INSTALL_NIIMBOT.md
- BLUETOOTH_DOCKER_ISSUES.md
→ **docs/features/NIIMBOT.md**

**Sensors & IoT** (3 files → 1):
- SHARED_SENSOR_DATA_IMPLEMENTATION.md
- SENSOR_TYPE_VALIDATION_FIX.md
- DEVICE_DISCOVERY_FIX.md
→ **docs/features/SENSORS.md**

**Notifications** (3 files → 1):
- NOTIFICATION_FIX_SUMMARY.md
- NTFY_SETUP_GUIDE.md
- OVERDUE_INDICATOR_FEATURE.md
- OVERDUE_VISUALIZATION_FEATURE.md
→ **docs/features/NOTIFICATIONS.md**

**Dashboards** (2 files → 1):
- DASHBOARD_FEATURE.md
- DASHBOARD_IMPLEMENTATION_SUMMARY.md
→ **docs/features/DASHBOARDS.md**

**Themes** (2 files → 1):
- THEME_FIX_SUMMARY.md
- V2_THEME_REVIEW.md
→ **docs/features/THEMES.md**

**Status & Milestones** (4 files → 1):
- STATUS_MILESTONES_FEATURE.md
- STATUS_MILESTONES_IMPLEMENTATION_SUMMARY.md
- MILESTONE_AUTO_END_DATE.md
- MILESTONE_REORDERING_GUIDE.md
- DYNAMIC_STATUS_COLORS.md
- CONFIGURABLE_STATES_SUMMARY.md
→ **docs/features/STATUS_MILESTONES.md**

**Relationships** (2 files → 1):
- RELATIONSHIP_FILTER_GROUPS_IMPLEMENTATION.md
- RELATIONSHIP_SEARCH_FIX.md
→ **docs/features/RELATIONSHIPS.md**

**AI Features** (1 file):
- AI_CHATBOT_FEATURE.md
→ **docs/features/AI_CHATBOT.md**

**Macros** (3 files → 1):
- MACRO_IMPLEMENTATION_GUIDE.md
- MACRO_SYSTEM_STATUS.md
- MACRO_SYSTEM_SUMMARY.md
→ **docs/features/MACROS.md**

**Security** (2 files → 1):
- SECURITY_IMPLEMENTATION.md
- SECURITY_TESTING_GUIDE.md
→ **docs/guides/SECURITY.md**

**Custom SQL** (2 files → 1):
- CUSTOM_SQL_IMPLEMENTATION_SUMMARY.md
- CUSTOM_SQL_QUERY_FEATURE.md
→ **docs/features/CUSTOM_SQL.md**

### ✅ KEEP & UPDATE (Core docs - 5 files)

**Root Level**:
- README.md → Update with new structure reference
- CHANGELOG.md → Keep for version tracking
- CONTRIBUTING.md → Keep for contributors
- FRAMEWORK_ARCHITECTURE_ANALYSIS.md → Move to docs/framework/FRAMEWORK_USAGE.md

**Setup Guides**:
- CASAOS_SETUP.md → docs/setup/CASAOS.md

### 📋 CREATE NEW (Essential missing docs)

**User Documentation**:
- docs/guides/USER_GUIDE.md (new)
- docs/guides/API_REFERENCE.md (new)

**Developer Documentation**:
- docs/development/ARCHITECTURE.md (consolidate from scattered notes)
- docs/development/DATABASE.md (schema documentation)
- docs/development/TESTING.md (consolidate testing docs)

**Setup Documentation**:
- docs/setup/INSTALLATION.md (consolidate quick start)
- docs/setup/DEPLOYMENT.md (production deployment)

## Implementation Steps

### Step 1: Create Directory Structure
```bash
mkdir -p docs/{setup,features,guides,development,framework}
mkdir -p archive
```

### Step 2: Consolidate Features (Priority Order)

1. **Label Printing** (most complex)
2. **Niimbot Integration** (hardware-specific)
3. **Sensors & IoT** (integration guide)
4. **Notifications** (user-facing)
5. **Dashboards** (user-facing)
6. **Other features** (alphabetical)

### Step 3: Move Obsolete Files to Archive
```bash
mv *_FIX.md *_DEBUG.md *_COMPLETE.md *_STATUS.md archive/
```

### Step 4: Update Root README
- Add documentation structure section
- Link to consolidated docs
- Simplify quick start

### Step 5: Update CHANGELOG
- Add note about documentation reorganization
- Reference new docs structure

## Estimated Results

**Before**: 90 markdown files (cluttered, redundant)
**After**: ~20 well-organized files

```
Root: 3 files (README, CHANGELOG, CONTRIBUTING)
docs/setup: 3 files
docs/features: 10 files
docs/guides: 3 files
docs/development: 3 files
docs/framework: 1 file
archive: 60+ files (for reference)
```

## Benefits

✅ **Easier to Navigate**: Clear structure by purpose
✅ **Less Redundancy**: Related content consolidated
✅ **Better Onboarding**: Clear user vs developer docs
✅ **Maintainable**: Fewer files to keep updated
✅ **Professional**: Industry-standard docs layout
✅ **Framework-Ready**: Clear separation of concerns
